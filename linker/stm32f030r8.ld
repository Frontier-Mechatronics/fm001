/* FM001 — STM32F030R8T6 memory regions.
 *
 * Step 1 of the project-owned linker script: describe the address space only.
 * No ENTRY, no SECTIONS, no symbols yet — those are added deliberately later.
 *
 * Addresses and sizes to be confirmed against:
 *   RM0360 Rev 5, Section 2.2 (Memory organization / memory map)
 *   DS9773 Rev 5, Section 3 (Functional overview) for the 64 KiB / 8 KiB part variant
 */

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 64K
  SRAM  (rwx) : ORIGIN = 0x20000000, LENGTH = 8K
}
