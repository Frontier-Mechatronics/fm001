#!/usr/bin/env python3
"""Validate Frontier session traces against .frontier/schema/session-v1.schema.json.

Uses the `jsonschema` package when available. Without it, falls back to a small
dependency-free structural check: required fields, types, enums, consts, patterns,
length bounds, and additionalProperties, resolving local $ref into $defs.

The fallback is intentionally partial. If validation must be authoritative, install
jsonschema (`pip install jsonschema`) rather than extending this file.

Both paths additionally run semantic checks that JSON Schema cannot express.

Usage:
    python3 .frontier/validate.py [path ...]

With no arguments, validates every trace in .frontier/sessions/ and .frontier/examples/.
Exit status is 0 when everything validates, 1 otherwise.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema" / "session-v1.schema.json"


# ---------------------------------------------------------------- fallback check

def _resolve(node, schema):
    """Resolve a local #/$defs/... reference."""
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return node
        target = schema
        for part in ref[2:].split("/"):
            target = target[part]
        node = target
    return node


TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "number": (int, float),
    "integer": int,
}


def _check(value, node, schema, path, errors):
    node = _resolve(node, schema)
    if not isinstance(node, dict):
        return

    if "const" in node and value != node["const"]:
        errors.append(f"{path}: expected const {node['const']!r}, got {value!r}")
        return

    if "enum" in node and value not in node["enum"]:
        errors.append(f"{path}: {value!r} not one of {node['enum']}")
        return

    expected = node.get("type")
    if expected:
        py = TYPES.get(expected)
        # bool is a subclass of int; keep them distinct
        if py and (not isinstance(value, py) or (expected != "boolean" and isinstance(value, bool))):
            errors.append(f"{path}: expected {expected}, got {type(value).__name__}")
            return

    if isinstance(value, str):
        pattern = node.get("pattern")
        if pattern and not re.search(pattern, value):
            errors.append(f"{path}: {value!r} does not match {pattern}")
        if "minLength" in node and len(value) < node["minLength"]:
            errors.append(f"{path}: shorter than minLength {node['minLength']}")
        if "maxLength" in node and len(value) > node["maxLength"]:
            errors.append(f"{path}: longer than maxLength {node['maxLength']}")

    if isinstance(value, dict):
        props = node.get("properties", {})
        for name in node.get("required", []):
            if name not in value:
                errors.append(f"{path}: missing required field {name!r}")
        if node.get("additionalProperties") is False:
            for name in value:
                if name not in props:
                    errors.append(f"{path}: unexpected field {name!r}")
        for name, sub in value.items():
            if name in props:
                _check(sub, props[name], schema, f"{path}.{name}", errors)

    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            errors.append(f"{path}: needs at least {node['minItems']} item(s)")
        if "maxItems" in node and len(value) > node["maxItems"]:
            errors.append(f"{path}: allows at most {node['maxItems']} item(s)")

    if isinstance(value, list) and "items" in node:
        for i, item in enumerate(value):
            _check(item, node["items"], schema, f"{path}[{i}]", errors)

    # Core applicators needed for the schema's cross-field rules. Deliberately the only
    # combinators supported here; anything beyond this belongs in real jsonschema.
    for sub in node.get("allOf", []):
        _check(value, sub, schema, path, errors)
    if "if" in node:
        probe = []
        _check(value, node["if"], schema, path, probe)
        branch = "then" if not probe else "else"
        if branch in node:
            _check(value, node[branch], schema, path, errors)


def structural_check(trace, schema):
    errors = []
    _check(trace, schema, schema, "$", errors)
    return errors


# ---------------------------------------------------------------- semantic check

def _collect_ids(trace, key, errors):
    """Return the set of ids declared in trace[key], reporting duplicates."""
    seen, dupes = set(), set()
    for item in trace.get(key, []):
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            if item["id"] in seen:
                dupes.add(item["id"])
            seen.add(item["id"])
    for dup in sorted(dupes):
        errors.append(f"{key}: duplicate id {dup!r}")
    return seen


def _collect_refs(trace):
    """Walk the trace collecting (id, kind, location) for every id reference.

    Kind is determined by the field name, so an evidence reference can never be
    satisfied by a failure id and vice versa.
    """
    refs = []

    def walk(node, where):
        if isinstance(node, dict):
            for key, val in node.items():
                if key == "evidence" and isinstance(val, list):
                    for ref in val:
                        if isinstance(ref, str):
                            refs.append((ref, "evidence", where))
                elif key == "evidence_id" and isinstance(val, str):
                    refs.append((val, "evidence", where))
                elif key == "failure_id" and isinstance(val, str):
                    refs.append((val, "failure", where))
                else:
                    walk(val, f"{where}.{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{where}[{i}]")

    for key, val in trace.items():
        if key != "evidence":  # the registry declares, it does not reference
            walk(val, key)
    return refs


# Path prefixes whose contents are conventionally build output rather than tracked files.
# Used only to warn about an evidence item claiming to be recoverable when it probably is not.
_LIKELY_UNTRACKED = ("build/", "dist/", "target/", "node_modules/", "__pycache__/")


def semantic_check(trace, path):
    """Checks JSON Schema cannot express."""
    errors = []

    if not isinstance(trace, dict):
        return [f"top-level value is {type(trace).__name__}, expected an object"]

    stem = path.stem
    if trace.get("trace_id") != stem:
        errors.append(f"trace_id {trace.get('trace_id')!r} does not match filename stem {stem!r}")

    in_sessions = path.parent.name == "sessions"
    if in_sessions and trace.get("example"):
        errors.append("example traces must live in .frontier/examples/, not sessions/")
    if path.parent.name == "examples" and not trace.get("example"):
        errors.append('traces in examples/ must set "example": true')

    # Declared ids, each namespace checked for duplicates independently.
    declared = {
        "evidence": _collect_ids(trace, "evidence", errors),
        "failure": _collect_ids(trace, "failures", errors),
    }
    _collect_ids(trace, "experiments", errors)
    _collect_ids(trace, "claims", errors)

    overlap = declared["evidence"] & declared["failure"]
    for dup in sorted(overlap):
        errors.append(f"note: id {dup!r} is used by both an evidence entry and a failure; legal but confusing")

    refs = _collect_refs(trace)
    for ref, kind, where in refs:
        if ref not in declared[kind]:
            errors.append(f"{where}: {kind} id {ref!r} is not declared")

    for item in trace.get("evidence", []):
        if not isinstance(item, dict):
            continue
        ref, persistence = item.get("ref", ""), item.get("persistence")
        if persistence == "committed" and isinstance(ref, str) and ref.startswith(_LIKELY_UNTRACKED):
            errors.append(
                f"note: evidence {item.get('id')!r} claims persistence 'committed' but {ref!r} "
                "looks like build output; 'ephemeral' or 'reproducible' is probably correct"
            )

    used = {r for r, kind, _ in refs if kind == "evidence"}
    for ref in sorted(declared["evidence"] - used):
        errors.append(f"note: evidence {ref!r} is declared but never referenced")

    return errors


# ---------------------------------------------------------------- driver

def validate(path, schema):
    try:
        trace = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"], "parse"

    try:
        import jsonschema
    except ImportError:
        errors = structural_check(trace, schema)
        mode = "fallback"
    else:
        from importlib.metadata import version as _pkg_version
        validator = jsonschema.Draft202012Validator(schema)
        errors = [
            f"$.{'.'.join(str(p) for p in e.absolute_path)}: {e.message}"
            for e in sorted(validator.iter_errors(trace), key=lambda e: list(e.absolute_path))
        ]
        mode = f"jsonschema {_pkg_version('jsonschema')}"

    return errors + semantic_check(trace, path), mode


def main(argv):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    if argv:
        paths = [Path(a) for a in argv]
    else:
        paths = sorted(
            list((ROOT / "sessions").glob("*.json")) + list((ROOT / "examples").glob("*.json"))
        )

    if not paths:
        print("no traces found")
        return 0

    failed = 0
    for path in paths:
        errors, mode = validate(path, schema)
        hard = [e for e in errors if not e.startswith("note:")]
        status = "FAIL" if hard else "ok"
        print(f"[{status}] {path}  ({mode})")
        for err in errors:
            print(f"       {err}")
        if hard:
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
