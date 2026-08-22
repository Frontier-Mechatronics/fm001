/* FM001 — STM32F030R8T6 memory regions.
 *
 * Step 1: describe the address space.
 * Step 2: place .text explicitly at the start of FLASH.
 *
 * Step 2 exists because a MEMORY-only script left every input section orphaned. The linker
 * ordered .ARM.exidx first and then aligned the differently-permissioned .text to its default
 * 0x10000 segment boundary, landing 4 bytes of code at 0x08010010 — past the end of flash.
 * Naming .text here anchors it at ORIGIN(FLASH) and the orphans follow contiguously.
 * No ENTRY and no symbol definitions yet — those are added deliberately later.
 *
 * Addresses and sizes confirmed 2026-08-22 against RM0360 Rev 5, Table 1 "STM32F0x0 memory
 * boundary addresses", STM32F030x8 block, page 39/775:
 *   0x0800 0000 - 0x0800 FFFF   64 KB   Main flash memory
 *   0x2000 0000 - 0x2000 1FFF    8 KB   SRAM
 * DS9773 Rev 5 page 1 confirms STM32F030R8 is an STM32F030x8 device.
 */

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 64K
  SRAM  (rwx) : ORIGIN = 0x20000000, LENGTH = 8K
}

SECTIONS
{
  .text : { *(.text*) } > FLASH
}
