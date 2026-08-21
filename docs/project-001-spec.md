
# Frontier Mechatronics Project 001

## Project Title

Bare-Metal Ultrasonic Ranging Node

## Purpose

Briefly describe what this project is intended to build and why it is the first Frontier Mechatronics project.

Keep this focused on both:

- the physical system being built
- the embedded systems concepts the project is intended to teach

## Primary Learning Objectives

List the concepts that should be understood by the end of the project.

Suggested areas:

- Cortex-M0 reset and startup behaviour
- STM32 memory map
- vector table
- linker script
- stack and runtime initialization
- memory-mapped I/O
- RCC / clock configuration
- GPIO
- hardware timers
- interrupts
- UART
- pulse generation and pulse-width measurement
- SWD debugging
- ELF / binary inspection
- oscilloscope-based verification
- embedded C build and cross-compilation
- Zig build system
- CI for embedded firmware

## Hardware

### Target MCU Board

- Board: STMicroelectronics NUCLEO-F030R8
- MCU: STM32F030R8T6
- CPU core: 32-bit ARM Cortex-M0 running at up to 48 MHz
- Flash: 64KiB
- SRAM: 8 KiB
- Board revision: MB1136-F030R8-C04 

### Sensor

- Device: HC-SR04 Ultrasonic Ranging Module
- Interface: Custom 4-pin hardware control interface: VCC, Trig (Trigger Input), Echo (Pulse Output), and GND
- Supply voltage: 5V DC
- Logic voltage: 5V TTL logic level
- Important electrical constraints:
  - Working Current: Consumes up to 15mA during active sonic transmission.
  - 3.3V System Incompatibility: Because the Echo pin outputs a full 5V logic signal, connecting it directly
    to a 3.3V microcontroller (like your STM32 Nucleo board) will cause permanent over-voltage damage to the
    MCU pin. You must use a series resistor voltage divider or a logic-level shifter on the Echo line to drop it safely to 3.3V.
  - Triggering Pulse Requirement: The Trig pin requires a precise high-level TTL pulse lasting at least 10 microseconds
    to initialize a measurement cycle.

### Debug / Communications

- Debug probe:
- Debug interface:
- UART adapter:

### Bench Equipment

- Oscilloscope:
- Multimeter:
- Bench power supply:
- Other:

## Software and Toolchain

### Host

- Development machine:
- Host OS:
- Architecture:

### Firmware

- Language: C
- Target architecture:
- Runtime:
- RTOS: None

### Build System

- Zig version:
- Zig build system:
- C compiler frontend:
- Linker:

### Debug / Flash Tools

- Debug server:
- Debugger:
- Flash mechanism:

### CI

- Platform: GitHub Actions
- Required CI checks:

## Project Constraints

Record the deliberate constraints for the project.

For example:

- no STM32 HAL for firmware functionality
- no CubeMX-generated application code
- no RTOS
- no Arduino framework
- no hidden peripheral abstraction
- peripheral configuration should be understood at register level
- startup process should be understood and owned by the project
- linker behaviour should be understood and owned by the project
- external libraries should only be introduced deliberately
- compiler warnings treated as errors where practical

## System Overview

Describe the intended final data/control path.

```text
HC-SR04
   │
   │ echo
   ▼
STM32F030R8
   │
   ├── timer measures pulse width
   ├── firmware calculates distance
   │
   └── UART
         │
         ▼
      MacBook Pro
```

Also document the trigger path:

```text
STM32 timer/GPIO
      │
      ▼
HC-SR04 TRIG
```

## Electrical Interface

Document the intended connections between the STM32 and HC-SR04.

Include:

- MCU pin
- board header pin
- sensor pin
- signal direction
- voltage level
- any resistor divider or level-shifting requirement

Do not finalize values until they have been checked against the authoritative datasheets.

## Firmware Architecture

Describe the intended software structure at a high level.

Initial structure may be approximately:

```text
reset
  ↓
vector table
  ↓
Reset_Handler
  ↓
runtime initialization
  ↓
main
  ↓
peripheral initialization
  ↓
measurement loop
```

Record intended modules only as they become justified. Avoid designing a large abstraction hierarchy before the hardware is working.

## Memory Model

Document:

- Flash start address
- Flash size
- SRAM start address
- SRAM size
- vector table location
- `.text`
- `.rodata`
- `.data`
- `.bss`
- stack
- heap policy

Include a simple memory-map diagram once verified from the datasheet/reference manual.

## Milestones

### Phase 0 — Toolchain and Bring-Up

Goal:

Produce, inspect, flash and debug the smallest firmware image that executes our own code.

Exit criteria:

- Zig toolchain configured for the target
- C source cross-compiles
- custom linker script is used
- vector table exists
- reset handler executes
- `main()` executes
- GPIO output can be observed
- firmware can be flashed via SWD
- debugger can halt and inspect the MCU
- GitHub Actions can reproduce the build

### Phase 1 — GPIO

Goal:

Understand and control STM32 GPIO directly.

Exit criteria:

- peripheral clock enabled explicitly
- GPIO mode configured through registers
- output toggled
- output measured with oscilloscope
- expected and measured behaviour documented

### Phase 2 — Clock and Timer

Goal:

Understand the relevant STM32 clock tree and configure a hardware timer.

Exit criteria:

- timer clock source understood
- prescaler calculated manually
- timer period calculated manually
- timer-generated signal measured on oscilloscope
- calculated and measured timing agree within expected tolerance

### Phase 3 — Interrupts

Goal:

Handle a hardware-generated interrupt.

Exit criteria:

- relevant vector-table entry understood
- NVIC configuration understood
- ISR executes
- interrupt behaviour verified

### Phase 4 — UART

Goal:

Transmit runtime diagnostics independently of the debugger.

Exit criteria:

- UART configured from registers
- baud-rate divisor calculated
- text/data received on Mac through USB-TTL adapter
- UART waveform examined on oscilloscope

### Phase 5 — Ultrasonic Trigger

Goal:

Generate the HC-SR04 trigger pulse.

Exit criteria:

- trigger timing generated using MCU hardware
- pulse width verified on oscilloscope
- electrical interface verified safe

### Phase 6 — Echo Measurement

Goal:

Measure the HC-SR04 echo pulse accurately.

Exit criteria:

- rising/falling edge behaviour understood
- pulse width measured using timer hardware
- timeout/error condition handled
- measured waveform compared with MCU measurement

### Phase 7 — Distance Calculation

Goal:

Convert measured pulse duration into a usable range measurement.

Exit criteria:

- conversion calculation documented
- result transmitted over UART
- several known-distance measurements performed
- error/variation recorded

### Phase 8 — Engineering Cleanup

Goal:

Turn the working experiment into a maintainable embedded project.

Exit criteria:

- firmware structure reviewed
- unnecessary abstractions removed
- useful abstractions introduced where justified
- warnings clean
- tests added where host-side testing is meaningful
- CI clean
- documentation current
- build artifacts reproducible

## Verification Strategy

For every major feature, identify how it will be verified.

Preferred hierarchy:

1. understand expected behaviour from documentation
2. calculate expected values
3. observe MCU/software state through debugger
4. measure electrical behaviour
5. compare expected versus observed behaviour
6. document discrepancies

Examples:

| Feature | Expected | Verification |
|---|---|---|
| GPIO output | Defined high/low voltage | Oscilloscope / DMM |
| Timer | Calculated frequency | Oscilloscope |
| UART | Calculated baud rate | Terminal + oscilloscope |
| HC-SR04 trigger | Required pulse width | Oscilloscope |
| Echo | Pulse proportional to range | Timer + oscilloscope |

## Testing Strategy

Document which behaviour can reasonably be tested without hardware.

Potential host-side tests:

- distance conversion
- timer calculation helpers
- baud-rate calculations
- parsing/formatting
- state-machine behaviour if introduced

Hardware-dependent behaviour should be verified separately rather than mocked excessively.

## CI Quality Gates

Initial CI should eventually check:

- clean firmware build
- host tests
- compiler warnings
- formatting
- ELF generation
- binary generation
- firmware size

Possible later checks:

- static analysis
- stack usage
- section sizes
- forbidden dependencies
- multiple optimization modes
- reproducible build checks

## Definition of Done

Project 001 is complete when:

- the firmware starts through project-owned startup code
- memory placement is understood
- GPIO works through direct peripheral configuration
- hardware timing is understood and measured
- at least one interrupt is used
- UART diagnostics work
- HC-SR04 ranging works reliably
- important timing has been independently verified with the oscilloscope
- firmware can be built from a clean checkout using Zig
- CI builds and tests the project successfully
- the project can be flashed and debugged through SWD
- the repository contains sufficient documentation for the system to be reproduced later

## References

Authoritative references should be listed in `docs/references.md`.

For each reference record:

- title
- vendor / publisher
- document identifier
- revision
- publication date if available
- official URL
- date accessed

## Open Questions

Track decisions that have not yet been made.

Initial examples:

- exact STM32 pins for TRIG/ECHO
- whether HC-SR04 ECHO requires external level shifting on the selected pin
- exact system clock configuration
- whether SysTick or a general-purpose timer is used for early timing exercises
- whether the onboard or standalone ST-LINK is used initially
- exact debug software stack on macOS
- exact Zig version to pin for the project

## Engineering Log

Use this section only for major findings or point to a separate development log.

Useful things to record:

- unexpected hardware behaviour
- incorrect assumptions
- timing measurements
- debugger discoveries
- datasheet/reference-manual ambiguities
- toolchain issues
- design decisions worth preserving

