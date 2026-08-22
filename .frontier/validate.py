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

    if isinstance(value, list) and "items" in node:
        for i, item in enumerate(value):
            _check(item, node["items"], schema, f"{path}[{i}]", errors)


def structural_check(trace, schema):
    errors = []
    _check(trace, schema, schema, "$", errors)
    return errors


# ---------------------------------------------------------------- semantic check

def semantic_check(trace, path):
    """Checks JSON Schema cannot express."""
    errors = []

    stem = path.stem
    if trace.get("trace_id") != stem:
        errors.append(f"trace_id {trace.get('trace_id')!r} does not match filename stem {stem!r}")

    in_sessions = path.parent.name == "sessions"
    if in_sessions and trace.get("example"):
        errors.append("example traces must live in .frontier/examples/, not sessions/")
    if not in_sessions and path.parent.name == "examples" and not trace.get("example"):
        errors.append("traces in examples/ must set \"example\": true")

    declared = {e["id"] for e in trace.get("evidence", []) if isinstance(e, dict) and "id" in e}
    seen = []

    def walk(node, where):
        if isinstance(node, dict):
            for key, val in node.items():
                if key == "evidence" and isinstance(val, list) and all(isinstance(v, str) for v in val):
                    for ref in val:
                        seen.append((ref, where))
                elif key in ("evidence_id", "failure_id") and isinstance(val, str):
                    seen.append((val, where))
                else:
                    walk(val, f"{where}.{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{where}[{i}]")

    for key, val in trace.items():
        if key != "evidence":
            walk(val, key)

    failure_ids = {f["id"] for f in trace.get("failures", []) if isinstance(f, dict) and "id" in f}
    for ref, where in seen:
        if ref not in declared and ref not in failure_ids:
            errors.append(f"{where}: evidence/failure id {ref!r} is not declared")

    unused = declared - {r for r, _ in seen}
    for ref in sorted(unused):
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
