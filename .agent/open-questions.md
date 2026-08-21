# Open Questions

Keep only unresolved questions here. When one is resolved, remove it and record the resulting decision or verified discovery in the appropriate file.

## Toolchain and Runtime

- Which linker will be used with the Clang/LLVM + Make build, and what is its exact invocation?
- What is the project’s initial startup implementation, including vector-table definitions and `.data` / `.bss` initialisation?

## Memory and Clocking

- What exact Flash and SRAM regions should the first linker script define, as verified from the applicable STM32 documentation?
- What initial system-clock configuration will the firmware use?

## Debugging

- Which debugger client will be used interactively through OpenOCD?

## Ultrasonic Interface

- Which MCU pins will be assigned to HC-SR04 TRIG and ECHO?
- Which target pin is safe for the HC-SR04 Echo signal after checking its exact STM32 voltage tolerance and electrical limits?
- What electrical level shifting or divider implementation will be used for Echo?
- Which timer and capture channel will measure the Echo pulse?

## CI

- Which build and code-quality checks will be required in the initial GitHub Actions workflow?
