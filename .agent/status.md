# Current Status

## Current Phase

Foundation and bring-up preparation.

## Current Objective

Verify the STM32F030R8 memory layout from authoritative documentation, then create the first project-owned linker script and linked executable ELF.

## Last Verified State

- `src/main.c` exists and is a minimal freestanding entry-point experiment.
- Apple Clang 17.0.0 produced `build/main.o` for Cortex-M0 using the command recorded below.
- `build/main.o` was identified as `ELF 32-bit LSB relocatable, ARM, EABI5`.
- LLVM objdump confirmed Thumb code in the generated object.
- OpenOCD 0.12.0 connected through the onboard ST-LINK over SWD and detected `Cortex-M0 r0p0`.
- The ST-LINK target-voltage reading during that test was approximately 3.25 V.

## Next Intended Step

Read the applicable STM32 datasheet and RM0360 memory-map, boot, and vector information; define the Flash and SRAM regions for the first linker script; then link a minimal executable ELF. Do not implement this step without separately reviewing the relevant primary documentation.

## Current Toolchain

- Host: Apple Silicon macOS.
- C compiler: Apple Clang 17.0.0.
- Target: `arm-none-eabi`, `cortex-m0`, Thumb, freestanding.
- Build direction: GNU Make; no Makefile is currently present. The host's `make` is GNU Make 3.81 (macOS-bundled) and `gmake` is not installed.
- Linker: Not yet selected or verified. `ld.lld` is installed; no GNU Arm embedded toolchain (`arm-none-eabi-*`) is present on this host. See `discoveries.md`.
- Debug server: OpenOCD 0.12.0.
- Debug transport: Onboard ST-LINK over SWD.

## Known Working Commands

```sh
clang \
  --target=arm-none-eabi \
  -mcpu=cortex-m0 \
  -mthumb \
  -ffreestanding \
  -c src/main.c \
  -o build/main.o
```

## Current Repository Shape

- `src/main.c`: minimal C entry-point experiment.
- `build/`: generated local objects; ignored by Git.
- `docs/project-001-spec.md`: project specification.
- `docs/references.md`: authoritative-reference metadata.
- `linker/`: present but empty; intended home for the first project-owned linker script.
- `build.zig`: present at the repository root but empty (0 bytes). It is a leftover of the completed Zig experiment, not current build direction.
- No project-owned startup source, linker script, executable ELF, Makefile, or CI configuration has been observed.
- Only `.gitignore`, `LICENSE`, `README.md`, and `docs/project-001-spec.md` are tracked by Git. `AGENTS.md`, `.agent/`, `src/`, `docs/references.md`, and `docs/notes/` are untracked working-tree files.

## Known Documentation Discrepancies

Current, unresolved inconsistencies between documents. Resolve and remove these rather than working around them.

- The `MB1136-DEFAULT-C04` board schematic is listed in `docs/references.md`, but no local copy has been confirmed. Obtain it before making board-net claims about headers, LED, UART routing, ST-LINK, power, or solder bridges.
