---
name: session-capture
description: Capture a meaningful engineering session as a validated Frontier JSON trace under `.frontier/sessions/`. Use only when the user explicitly asks Codex to capture, record, or save the completed session; never run automatically or for routine work.
---

# Frontier Session Capture

This is a thin Codex adapter. The vendor-neutral contract is `.frontier/session-capture.md`; the machine-readable schema is `.frontier/schema/session-v1.schema.json`. If either conflicts with this skill, follow the canonical contract and correct this adapter later.

## Procedure

1. Read `.frontier/session-capture.md` completely, then read the schema and inspect `.frontier/examples/` for shape only.
2. Observe the repository rather than relying on session memory:

   ```sh
   git rev-parse --show-toplevel
   git rev-parse --abbrev-ref HEAD
   git rev-parse HEAD
   git status --short
   git log --oneline -n 10
   ```

3. Re-read files and command output that the trace will cite. Record facts as `observed`, `inferred`, `hypothesis`, or `unresolved`; retain real model updates, rejected hypotheses, failures, and unresolved questions.
4. Write exactly one trace to `.frontier/sessions/YYYY-MM-DDTHHMMSSZ-short-topic.json` (UTC; the trailing `Z` is required). Its `trace_id` must equal the filename stem.
5. Validate it and fix every error:

   ```sh
   python3 .frontier/validate.py .frontier/sessions/<trace>.json
   ```

6. Report the trace path, validator result, and any claims that remain uncertain or intentionally omitted.

## Constraints

- Run only on explicit user request, never on session exit or as an ordinary-work side effect.
- Do not modify existing committed traces; write a new trace with `supersedes` for substantive corrections.
- Do not commit a trace unless the user asks.
- Do not create a trace if the session does not meet the contract's threshold for meaningful learning or engineering work.
- Do not invent evidence, prior beliefs, hypotheses, model updates, or course material. Prefer omission or an empty array.
- Do not write course material, lessons, or exercises at all, invented or not. Capture pointers in `future_work` only.
- Mark `prior_model_provenance` and `misconceptions[].provenance` as `explicit` only where the user actually stated the belief; otherwise `inferred`.
- Do not silently update `.agent/` files while capturing a trace; those files have their own update workflow.
