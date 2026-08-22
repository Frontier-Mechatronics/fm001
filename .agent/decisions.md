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

## 2026-08-22 — Stack-top symbol is `_stack_top`, defined by the linker script

- Decision: The initial Main Stack Pointer value is defined in `linker/stm32f030r8.ld` as
  `_stack_top = ORIGIN(SRAM) + LENGTH(SRAM);`, a plain assignment at top level, outside `SECTIONS`.
- Rationale:
  - Derived, not hard-coded. The address exists in exactly one place — the `MEMORY` block. Changing part
    or region size cannot leave a stale stack pointer behind.
  - Outside `SECTIONS` makes it an absolute (`ABS`) symbol rather than one bound to an output section. It
    is an address handed to other code, not storage, and it emits no bytes into the image.
  - Plain `=` rather than `PROVIDE()`. `PROVIDE` defines a symbol only when something references it and
    nothing else defines it; a plain assignment always defines it, so the value is inspectable with
    `llvm-readelf -s` before any code refers to it — which is the point of introducing it as its own step.
  - The name is project-owned rather than adopted from a vendor template (ST/CubeMX uses `_estack`, GNU
    newlib startup uses `__stack`). The leading underscore keeps it in the identifier space reserved to the
    implementation, so it cannot collide with an application identifier.
- Alternatives considered: `ORIGIN(SRAM) + LENGTH(SRAM)` is the whole of SRAM. Reserving a fixed stack
  region and pointing the symbol at its top is the usual next refinement, and was deliberately deferred —
  there is no `.data`, `.bss`, or heap to collide with yet, so a reservation now would encode a guess.
- Consequences:
  - The symbol alone does not make the image bootable. The core reads its MSP from a word at
    `0x00000000`; nothing yet writes `_stack_top` into that word. Storing it is the vector-table step.
  - Stack overflow on this part is silent. Cortex-M0 has no MPU and no stack-limit register, so growth
    past `0x20000000` wraps out of SRAM rather than faulting. Detection, if wanted, must be built.

## 2026-08-22 — Startup code lives in `src/startup.c`; the reset entry point is `Reset_Handler`

- Decision: Project-owned startup code goes in `src/startup.c`, separate from `src/main.c`. The reset entry
  point is named `Reset_Handler`.
- Rationale:
  - Separate file: startup code and application code have different lifetimes and different review needs.
    Startup runs before the C environment is fully established and will grow `.data`/`.bss` initialisation;
    `main.c` should stay ordinary C.
  - `Reset_Handler` is the near-universal name across Cortex-M toolchains, vendor documentation and
    published startup code, so it aids recognition when reading reference material.
- Known inconsistency, accepted deliberately: `Reset_Handler` is the CMSIS/ST convention, whereas
  `_stack_top` was chosen specifically to avoid the vendor name `_estack`. The distinction drawn is that
  `Reset_Handler` is a widely shared convention across the whole Cortex-M ecosystem, while `_estack` is
  tied to ST's generated linker scripts. This is a judgement call, not a principle, and is recorded so it
  is not mistaken for an oversight.
- Consequences:
  - `Reset_Handler` must not return. LR is `0xFFFFFFFF` at reset (PM0215 Rev 2 page 7/72), so it is entered
    by the reset sequence rather than by a call and has no valid return address. It ends in a trap loop.
  - The handler uses the stack on its first instruction, so a valid MSP is a precondition for it running at
    all. Word 0 of the vector table must be in place before this code can execute.
