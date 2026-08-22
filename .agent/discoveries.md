# Verified Discoveries

Record verified findings here. Include the command, tool output, measurement, or authoritative source needed to distinguish a discovery from an assumption.

## 2026-08-21 — Apple Clang emits Cortex-M0 ARM objects

- Apple Clang version: 17.0.0.
- Tested command:

  ```sh
  clang \
    --target=arm-none-eabi \
    -mcpu=cortex-m0 \
    -mthumb \
    -ffreestanding \
    -c src/main.c \
    -o build/main.o
  ```

- Result: The command successfully produced `build/main.o`.
- `file build/main.o` result: `ELF 32-bit LSB relocatable, ARM, EABI5`.
- LLVM objdump inspection confirmed Thumb code in the generated object.

## 2026-08-21 — OpenOCD communicates with the onboard ST-LINK

- OpenOCD version: 0.12.0.
- Transport: Onboard ST-LINK over SWD.
- Result: OpenOCD connected successfully and detected `Cortex-M0 r0p0`.
- Observed target voltage: approximately 3.25 V.

## 2026-08-21 — Host toolchain inventory for the Clang/Make build

Verified on the development host by running each tool's version/lookup command.

- `clang --version`: `Apple clang version 17.0.0 (clang-1700.6.3.2)`, host target `arm64-apple-darwin25.3.0`.
- `make --version`: `GNU Make 3.81`. This is the macOS-bundled Make, not a current GNU Make; `gmake` is not installed. Makefile syntax must stay within 3.81 features.
- `openocd --version`: `Open On-Chip Debugger 0.12.0`.
- `llvm-objdump --version`: `Homebrew LLVM version 20.1.3`. Note this is Homebrew LLVM, not the Apple Clang toolchain used to compile.
- `which ld.lld`: `/opt/homebrew/bin/ld.lld` is present (Homebrew LLVM 20.1.3).
- `which arm-none-eabi-ld` and `which arm-none-eabi-gcc`: not found. No GNU Arm embedded toolchain is installed on this host.

Scope of this finding: tool presence and versions only. It does not establish that `ld.lld` links a
correct Cortex-M0 image for FM001; that remains an open question to be answered by a linking experiment.

## 2026-08-22 — STM32F030R8T6 Flash and SRAM regions confirmed

- Primary source: RM0360 Rev 5, Table 1 "STM32F0x0 memory boundary addresses", `STM32F030x8` block, page 39/775.
  Rows as printed:

  ```text
  0x2000 0000 - 0x2000 1FFF    8 KB     SRAM
  0x0800 0000 - 0x0800 FFFF   64 KB     Main flash memory
  0x0000 0000 - 0x0000 FFFF   64 KB     Main flash memory, system memory or SRAM
                                        depending on BOOT configuration
  ```

- Part applicability: DS9773 Rev 5 page 1 lists `STM32F030x8` as covering `STM32F030C8, STM32F030R8`, so the
  `STM32F030x8` column applies to the FM001 part. DS9773 Rev 5 Table 2, page 10/93, gives `Flash (Kbytes)` = 64
  in the `STM32F030R8` column.
- Evidence limitation: the `SRAM (Kbytes)` row of DS9773 Table 2 extracts as five values across seven columns
  because of merged cells, so it was not used as evidence. The 8 KB figure rests on RM0360 Table 1, which is
  unambiguous for `STM32F030x8`.
- Also confirmed independently by the project owner reading the same two documents on 2026-08-22.
- Consequence: `linker/stm32f030r8.ld` declares `FLASH (rx)` at ORIGIN `0x08000000` LENGTH `64K`, and
  `SRAM (rwx)` at ORIGIN `0x20000000` LENGTH `8K`.

## 2026-08-22 — Boot aliasing at 0x00000000 is address aliasing, not a second copy

- Primary source: RM0360 Rev 5, boot configuration text, page 44/775. As printed:

  > After this startup delay has elapsed, the CPU fetches the top-of-stack value from address 0x0000 0000, then
  > starts code execution from the boot memory at 0x0000 0004.

  > Boot from main flash memory: the main flash memory is aliased in the boot memory space (0x0000 0000), but
  > still accessible from its original memory space (0x0800 0000). In other words, the flash memory contents can
  > be accessed starting from address 0x0000 0000 or 0x0800 0000.

- Interpretation: one physical flash array reachable through two address windows. The Armv6-M core has no VTOR
  on this device, so the vector table must be visible at `0x0000 0000`; ST satisfies that by aliasing rather than
  by requiring firmware to be linked at zero.
- Consequence for the linker script: no `MEMORY` region is declared for the `0x0000 0000` window. Declaring one
  would tell the linker the device has 128 KiB of flash when it has 64 KiB.
- Runtime remap mechanism exists: RM0360 Rev 5 page 144/775 documents `MEM_MODE[1:0]`, "Memory mapping selection
  bits", in `SYSCFG_CFGR1` (register layout page 142/775). Page 45/775 refers to programming these bits to change
  what appears in the code area. The individual bit encodings have not been transcribed here.
- Not yet verified on hardware: the claim that no copy occurs has not been demonstrated by observation. The
  intended test is to map SRAM to `0x0000 0000` via `MEM_MODE`, write a word at `0x2000 0000`, and read the same
  value back at `0x0000 0000`.

## 2026-08-22 — Local vendor PDFs are present in `docs/references/`

- Seven vendor documents are present locally and excluded from Git by the `/docs/references/` rule in `.gitignore`:
  RM0360, DS_stm32f030r8, PM0215, UM1724, `mb1136-default-c04_schematic`, `DB_nucleo-f030r8`, and the HC-SR04 user guide.
- This supersedes the earlier note that no local copy of the MB1136-DEFAULT-C04 schematic had been confirmed.
- Text extraction works via `pypdf` in the `fm001-3.12.2` pyenv virtualenv (`.python-version` at the repository
  root selects it). Body text, headings, and table rows extract reliably; merged table cells and figures do not.
- Poppler 26.08.0 was installed via Homebrew on 2026-08-22, providing `pdftotext` and `pdftoppm`. Page rendering
  is therefore available, so figures, pinout diagrams, and schematic sheets can now be read directly rather than
  only as extracted text.
