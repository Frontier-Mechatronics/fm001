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
