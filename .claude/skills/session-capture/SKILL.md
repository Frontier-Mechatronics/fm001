---
name: session-capture
description: Capture the current development session as a Frontier session trace — the engineering work, learning progression, evidence, failures, and unresolved questions — written as JSON under .frontier/sessions/. Use when the user explicitly asks to capture, record, or save the session at its end. Never run automatically.
---

# Session capture (Claude adapter)

This skill is a **thin adapter**. The specification lives in the repository and is vendor-neutral;
this file only bridges Claude Code's invocation to it.

**Do not reproduce the specification here.** If guidance in this file ever conflicts with
`.frontier/session-capture.md`, the specification wins and this file should be corrected.

## Procedure

1. **Read the contract.**
   - `.frontier/session-capture.md` — the canonical specification. Read it fully before writing anything.
   - `.frontier/schema/session-v1.schema.json` — the required structure.
   - `.frontier/examples/` — shape reference only. Do not copy its content into a real trace.

2. **Observe repository state.** Do not write it from memory:

   ```sh
   git rev-parse --show-toplevel
   git rev-parse --abbrev-ref HEAD
   git rev-parse HEAD
   git status --short
   git log --oneline -n 10
   ```

   Re-read files the trace will reference. Capture tool versions only where relevant to this session.

3. **Draw the content from this conversation**, applying the specification's rules — particularly:
   - separate `observed` / `inferred` / `hypothesis` / `unresolved` in `claims`;
   - record `prior_model → observation → updated_model` in `learning.model_updates`, keeping prior models
     that turned out to be wrong;
   - keep failures with their rejected hypotheses;
   - keep unresolved questions open;
   - record your own errors in `learning.misconceptions` with `held_by: agent` where they occurred.

4. **Write one trace** to `.frontier/sessions/YYYY-MM-DDTHHMMSS-short-topic.json`, with `trace_id` equal
   to the filename stem.

5. **Validate:**

   ```sh
   python3 .frontier/validate.py .frontier/sessions/<file>.json
   ```

   Fix any reported problems and re-run until clean.

6. **Report** the trace path, the validator result, and — explicitly — anything you were unsure about:
   claims you could not evidence, sections left empty, and anything you inferred rather than observed.
   Do not present an uncertain trace as authoritative.

## Constraints

- Run **only** when the user explicitly asks. Never on session exit, never as a side effect of other work.
- Write exactly one trace per invocation.
- Do not modify existing committed traces. Corrections are new traces using `supersedes`.
- Do not commit the trace unless the user asks. It is meant to be read by a human first.
- Do not write course material, lessons, or exercises. Capture pointers in `future_work` only.
- Prefer an empty array over an invented entry. Fabricated content permanently corrupts the corpus.
- If the session does not warrant a trace under the specification's guidance, say so instead of writing a
  thin one.
