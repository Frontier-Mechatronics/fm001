# Current Status

## Current Phase

Foundation and bring-up preparation.

## Current Objective

Build up the first project-owned linker script one deliberate step at a time, then produce a linked executable ELF and inspect its layout.

## Last Verified State

- `src/main.c` exists and is a minimal freestanding entry-point experiment.
- Apple Clang 17.0.0 produced `build/main.o` for Cortex-M0 using the command recorded below.
- `build/main.o` was identified as `ELF 32-bit LSB relocatable, ARM, EABI5`.
- LLVM objdump confirmed Thumb code in the generated object.
- OpenOCD 0.12.0 connected through the onboard ST-LINK over SWD and detected `Cortex-M0 r0p0`.
- The ST-LINK target-voltage reading during that test was approximately 3.25 V.
- STM32F030R8T6 Flash and SRAM base addresses and sizes were confirmed against RM0360 Rev 5 and DS9773 Rev 5.
  See `discoveries.md` for the evidence and its limitations.
- `linker/stm32f030r8.ld` exists and declares only a `MEMORY` block. It has not yet been used in a link,
  so nothing about its effect on section placement has been observed.

## Next Intended Step

Link `build/main.o` using `ld.lld -T linker/stm32f030r8.ld` and inspect the resulting ELF with `llvm-readelf -S -l`.

The specific question this answers: with a script that supplies `MEMORY` but no `SECTIONS`, does the linker place
`.text` into the FLASH region by orphan-section attribute matching, place it elsewhere, or refuse to link? This is
also the first real evidence toward the open question of which linker FM001 uses. Record the observed behaviour
rather than assuming it.

## Current Toolchain

- Host: Apple Silicon macOS.
- C compiler: Apple Clang 17.0.0.
- Target: `arm-none-eabi`, `cortex-m0`, Thumb, freestanding.
- Build direction: GNU Make; no Makefile is currently present. The host's `make` is GNU Make 3.81 (macOS-bundled) and `gmake` is not installed.
- Linker: Not yet selected or verified. `ld.lld` is installed; no GNU Arm embedded toolchain (`arm-none-eabi-*`) is present on this host. See `discoveries.md`.
- Debug server: OpenOCD 0.12.0.
- Debug transport: Onboard ST-LINK over SWD.
- Documentation tooling: pyenv virtualenv `fm001-3.12.2` (selected by `.python-version`) with `pypdf` for text
  extraction, and Homebrew poppler 26.08.0 (`pdftotext`, `pdftoppm`) for text and page rendering of the vendor
  PDFs in `docs/references/`.

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
- `linker/stm32f030r8.ld`: project-owned linker script. Currently declares only the `MEMORY` block, with `FLASH (rx)`
  at `0x08000000` for 64K and `SRAM (rwx)` at `0x20000000` for 8K. No `ENTRY`, no `SECTIONS`, no symbol definitions yet.
- `docs/references/`: local vendor PDFs; excluded from Git.
- `build.zig` is no longer present at the repository root.
- No project-owned startup source, executable ELF, Makefile, or CI configuration has been observed.
- Tracked by Git: `.agent/`, `AGENTS.md`, `.gitignore`, `LICENSE`, `README.md`, `docs/notes/20260821.md`,
  `docs/project-001-spec.md`, `docs/references.md`, and `src/main.c`. `linker/` is untracked.

## Known Documentation Discrepancies

Current, unresolved inconsistencies between documents. Resolve and remove these rather than working around them.

None currently recorded.
