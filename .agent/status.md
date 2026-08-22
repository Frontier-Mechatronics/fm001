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
- `linker/stm32f030r8.ld` declares `MEMORY` plus a minimal `SECTIONS` block placing `.text` in FLASH.
- `ld.lld` links `build/main.o` against that script and produces `build/fm001.elf` with `.text` at `0x08000000`.
  The link emits one expected warning: no `_start` entry symbol. See `discoveries.md` for the orphan-placement
  failure that made the `SECTIONS` block necessary.
- The linker script defines `_stack_top = ORIGIN(SRAM) + LENGTH(SRAM);`. `llvm-readelf -s build/fm001.elf`
  reports it as `20002000  0  NOTYPE  GLOBAL  DEFAULT  ABS _stack_top`. Nothing references it yet and it emits
  no bytes: `build/fm001.bin` is byte-identical before and after the change (20 bytes, MD5
  `90c7062801e841ad5c604058eeec8e09`). PM0215 Rev 2 page 6/72 is the authority for what that value is for.
- `src/startup.c` defines `Reset_Handler`, the first project-owned startup source. It calls `main()` and traps.
  Nothing points the core at it yet.
- `ld.lld -T linker/stm32f030r8.ld build/main.o build/startup.o` links both objects. `*(.text*)` captured the new
  code with no linker-script change. `.text` is 16 bytes: `main` at `0x08000000`, `Reset_Handler` at `0x08000004`.
- `Reset_Handler`'s symbol value is `0x08000005` while its first instruction is at `0x08000004`. Bit 0 is the ARM
  Thumb-state bit, not an address bit. See `discoveries.md`.

## Next Intended Step

Give the image a vector table. `build/fm001.elf` still has `main` at the base of flash, so the first words of the
boot memory are instructions rather than the initial stack pointer and reset vector. The device cannot start
from it. `_stack_top` now names the correct value but nothing stores it at offset 0.

`_stack_top` names the correct initial MSP value and `Reset_Handler` exists, but nothing stores either at
`ORIGIN(FLASH)`, so the first words of boot memory are still instructions. The device cannot start from this image.

Next, smallest first: add `ENTRY(Reset_Handler)`, which sets the ELF entry address and clears the standing
`_start` warning without changing the image layout. Then emit a vector table whose first word is `_stack_top` and
whose second is `Reset_Handler`, and place it at `ORIGIN(FLASH)` ahead of `.text`. Confirm the required table
layout and the minimum entry count from PM0215 and RM0360 rather than from an example script.

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

clang \
  --target=arm-none-eabi \
  -mcpu=cortex-m0 \
  -mthumb \
  -ffreestanding \
  -c src/startup.c \
  -o build/startup.o

ld.lld -T linker/stm32f030r8.ld build/main.o build/startup.o -o build/fm001.elf -Map build/fm001.map

llvm-objcopy -O binary build/fm001.elf build/fm001.bin
```

Inspection commands used to check placement and symbols:

```sh
llvm-readelf -S build/fm001.elf   # section addresses and sizes
llvm-readelf -s build/fm001.elf   # symbol table, including ABS linker-script symbols
```

## Current Repository Shape

- `src/main.c`: minimal C entry-point experiment.
- `src/startup.c`: project-owned startup source. Currently defines `Reset_Handler` only — no vector table, no
  `.data`/`.bss` initialisation.
- `build/`: generated local objects; ignored by Git.
- `docs/project-001-spec.md`: project specification.
- `docs/references.md`: authoritative-reference metadata.
- `linker/stm32f030r8.ld`: project-owned linker script. Declares `MEMORY` with `FLASH (rx)` at `0x08000000` for 64K
  and `SRAM (rwx)` at `0x20000000` for 8K; one absolute symbol assignment, `_stack_top`; and a `SECTIONS` block
  placing `.text` in FLASH. No `ENTRY` and no vector-table output section yet.
- `docs/references/`: local vendor PDFs; excluded from Git.
- `.frontier/`: session-capture contract, schema, validator, and captured session traces.
- `build.zig` is no longer present at the repository root.
- No Makefile or CI configuration exists. `build/fm001.elf` is produced by hand with the commands above and is
  not tracked.
- Tracked by Git: `.agent/`, `.claude/`, `.codex/`, `.frontier/`, `AGENTS.md`, `.gitignore`, `.python-version`,
  `LICENSE`, `README.md`, `docs/` (excluding `docs/references/`), `linker/`, and `src/`.

## Known Documentation Discrepancies

Current, unresolved inconsistencies between documents. Resolve and remove these rather than working around them.

None currently recorded.
