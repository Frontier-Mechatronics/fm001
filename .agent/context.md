# FM001 Context

## Project Identity

- Project: Frontier Mechatronics Project 001 — Bare-Metal Ultrasonic Ranging Node.
- Purpose: A learning-first foundation project for embedded hardware and firmware skills, future home robotics, and edge IoT work.

## Hardware Target

- Board: STMicroelectronics NUCLEO-F030R8.
- MCU: STM32F030R8T6.
- Core: Arm Cortex-M0.
- Architecture: Armv6-M.
- Sensor: HC-SR04 ultrasonic ranging module.

## Firmware and Toolchain Direction

- Firmware language: C.
- Runtime: Freestanding bare metal.
- Build direction: Clang/LLVM with GNU Make.
- Host: Apple Silicon macOS.
- Debug server: OpenOCD.
- Hardware debug path: Onboard ST-LINK over SWD.
- CI direction: GitHub Actions will eventually enforce build and code-quality checks.

## Constraints

- No RTOS.
- No STM32 HAL.
- No CubeMX-generated application code.
- No Arduino framework.
- Startup code and linker script are project-owned.
- Peripheral work is register-level and should be understood, not hidden.
- Hardware timing and electrical behaviour are verified with bench equipment.

## Learning Goals

Develop working understanding of startup and memory initialisation, vector tables, linker scripts, clocks, GPIO, timers, interrupts, UART, ultrasonic trigger/echo measurement, SWD debugging, and electrical verification.

## Important Paths

- Specification: `docs/project-001-spec.md`
- Reference metadata and official URLs: `docs/references.md`
- Agent context: `.agent/`
- Firmware source: `src/`
- Generated build output: `build/`

## Reference-Document Policy

Local vendor PDFs may be stored in `references/` or `docs/references/` and are excluded from Git. Record document identifiers, revisions, official URLs, and project-use notes in `docs/references.md` instead. Use primary STMicroelectronics and Arm documentation for hardware and core claims.
