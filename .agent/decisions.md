# Engineering Decisions

This is a chronological log. Record decisions when they are made; do not rewrite historical entries to make them appear more certain than they were.

## 2026-08-21 — STM32F030R8 selected for FM001

- Decision: Use the STMicroelectronics NUCLEO-F030R8, containing an STM32F030R8T6, as the FM001 target.
- Rationale: Recorded project direction.
- Alternatives considered: Not recorded.
- Consequences: Firmware targets Arm Cortex-M0 / Armv6-M and board work must use NUCLEO-F030R8-specific documentation.

## 2026-08-21 — HC-SR04 selected as the first external sensor

- Decision: Use an HC-SR04 ultrasonic ranging module.
- Rationale: Recorded project direction.
- Alternatives considered: Not recorded.
- Consequences: FM001 must generate a trigger pulse, measure the Echo pulse, and verify safe electrical interfacing with the 3.3 V MCU.

## 2026-08-21 — Firmware is bare-metal C

- Decision: Write firmware in C for a freestanding bare-metal runtime.
- Rationale: The project is learning-first and explicitly aims to understand startup, memory initialisation, peripheral configuration, and the build process.
- Alternatives considered: Hosted runtime, RTOS, or framework-based firmware are outside the project constraints.
- Consequences: The project owns its startup code, vector table, linker script, and runtime initialisation.

## 2026-08-21 — Avoid high-level firmware frameworks

- Decision: Do not use STM32 HAL, CubeMX-generated application code, Arduino, or an RTOS.
- Rationale: Recorded project constraint.
- Alternatives considered: These tools are deliberately excluded for FM001.
- Consequences: Peripheral configuration is performed and documented at register level.

## 2026-08-21 — Zig toolchain experiment completed

- Decision: Perform an initial Zig-based toolchain/build-system experiment.
- Rationale: Zig was an earlier stated toolchain direction and the experiment informed the project’s toolchain exploration.
- Alternatives considered: Not recorded.
- Consequences: The experiment is historical context; it is not the current FM001 build direction.

## 2026-08-21 — Build direction is Clang/LLVM with GNU Make

- Decision: Use Clang/LLVM with GNU Make for FM001.
- Rationale: Recorded project direction following the initial Zig experiment. No further selection rationale is recorded.
- Alternatives considered: Zig cross-compilation and build orchestration were explored initially.
- Consequences: Build files and linker selection should target this toolchain and remain simple and reproducible.

## 2026-08-21 — Keep vendor/reference PDFs out of Git

- Decision: Exclude local vendor and reference PDFs from Git.
- Rationale: Local engineering PDFs should not be committed; the repository should remain lightweight and record stable document metadata and official URLs.
- Alternatives considered: Committing PDFs is not the selected approach.
- Consequences: `docs/references.md` records the authoritative document title, identifier, revision, date, official URL, and FM001 use.
