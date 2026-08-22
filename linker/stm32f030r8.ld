/* FM001 — STM32F030R8T6 memory regions.
 *
 * Step 1: describe the address space.
 * Step 2: place .text explicitly at the start of FLASH.
 * Step 3: define the initial stack-pointer value as a linker symbol.
 *
 * Step 2 exists because a MEMORY-only script left every input section orphaned. The linker
 * ordered .ARM.exidx first and then aligned the differently-permissioned .text to its default
 * 0x10000 segment boundary, landing 4 bytes of code at 0x08010010 — past the end of flash.
 * Naming .text here anchors it at ORIGIN(FLASH) and the orphans follow contiguously.
 *
 * Step 3 defines _stack_top only. It emits no bytes: an assignment outside SECTIONS creates an
 * absolute symbol, which is an address the linker hands to other code, not storage in the image.
 * Nothing references it yet, so build/fm001.bin is unchanged by this step. The vector table that
 * will store this value at ORIGIN(FLASH) is deliberately still absent.
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

/* Initial Main Stack Pointer value.
 *
 * PM0215 Rev 2, section 2.1.3 "Core registers", page 6/72: "On reset, the processor loads the
 * MSP with the value from address 0x00000000." The core loads MSP with the word *stored* at
 * that address, so this symbol is the value that word must eventually contain.
 *
 * PM0215 Rev 2, section 2.1.2 "Stacks", page 5/72: the processor uses a full descending stack —
 * a push decrements SP first, then writes. So the correct initial value is one past the last
 * usable byte, not the address of the last usable word. ORIGIN + LENGTH = 0x20002000, which is
 * the first address *outside* SRAM; the first push writes to 0x20001FFC, the last word inside it.
 *
 * 0x20002000 is 8-byte aligned, which AAPCS requires of SP at a public interface.
 */
_stack_top = ORIGIN(SRAM) + LENGTH(SRAM);

SECTIONS
{
  .text : { *(.text*) } > FLASH
}
