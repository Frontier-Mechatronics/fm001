# FM001 Agent Guide

## Project Mission

FM001, **Frontier Mechatronics Project 001 — Bare-Metal Ultrasonic Ranging Node**, builds an ultrasonic ranging node with a NUCLEO-F030R8 and HC-SR04 sensor.

It is a learning-first embedded systems project. Its purpose is to develop practical understanding of embedded hardware and firmware foundations that will support future Frontier Mechatronics robots and edge IoT nodes.

## Working Philosophy

- Preserve explicit, low-level implementation and register-level understanding.
- Do not hide hardware behaviour behind unnecessary dependencies or abstractions.
- Do not introduce STM32 HAL, CubeMX-generated application code, Arduino, or an RTOS.
- Keep startup code and the linker script owned and understood by this project.
- Prefer small, reviewable, reproducible changes.
- Explain important toolchain and hardware behaviour when it affects a decision or implementation.
- Consult authoritative documentation before making hardware claims.
- Clearly distinguish verified facts from assumptions, proposals, and unresolved questions.
- Update `.agent/` context files after meaningful decisions or verified discoveries; do not update them merely to create activity.

## Implementation Boundaries

- Firmware language: C.
- Runtime: freestanding bare metal.
- Target: STM32F030R8T6, Arm Cortex-M0, Armv6-M, Thumb.
- Build direction: Clang/LLVM with GNU Make.
- Debug path: OpenOCD through the onboard ST-LINK over SWD.
- Treat compiler warnings seriously; configure them as errors where practical once the build is established.
- Do not create or adopt a generated vendor project structure.

## Context Is Not a Primary Source

The `.agent/` files are concise project summaries, not primary sources.

- Repository code is authoritative for implementation state.
- Datasheets, reference manuals, errata, board manuals, and schematics are authoritative for hardware facts.
- If a context summary conflicts with code or primary documentation, verify the conflict and correct the summary.

## Startup Procedure

Before proposing changes, read these files in order:

1. `AGENTS.md`
2. `.agent/context.md`
3. `.agent/status.md`
4. `.agent/decisions.md`
5. `.agent/discoveries.md`
6. `.agent/open-questions.md`
7. `docs/project-001-spec.md`
8. `docs/references.md`

Then inspect the current repository state, including `git status`, relevant code, and relevant documentation metadata.

## Frontier Session Capture

Only when the user explicitly asks to capture, record, or save a meaningful engineering session, follow the canonical, vendor-neutral contract in `.frontier/session-capture.md`. Each tool has a thin adapter that defers to it: `.claude/skills/session-capture/SKILL.md` for Claude Code, `.codex/skills/session-capture/SKILL.md` for Codex. Where an adapter and the contract disagree, the contract wins.

Never create a session trace automatically or as a side effect of ordinary work. Session traces complement the `.agent/` workflow and must not silently replace or modify it.

## Shutdown and Update Procedure

After meaningful work:

1. Update only the `.agent/` files whose contents actually changed.
2. Record enduring decisions in `decisions.md` and verified technical findings in `discoveries.md`.
3. Remove genuinely resolved items from `open-questions.md` and record their resolution elsewhere.
4. Refresh `status.md` when the current phase, verified state, or next intended step changes.
5. Keep `context.md` stable; change it only when durable project context changes.
