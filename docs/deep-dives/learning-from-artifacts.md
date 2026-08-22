# Learning From Build Artifacts

A guided walkthrough of the FM001 build at the point where `Reset_Handler` exists but the vector
table does not. Every command below was run against the repository state recorded in *Provenance*,
and every block of output is real, pasted unedited.

The purpose is not to document a build procedure. It is to show that each stage of the toolchain
leaves an inspectable artifact, and that reading those artifacts answers questions that reading the
source cannot.

**Read this with a terminal open.** Run each command yourself and compare. Where the document says
"notice X", the point is to find X in your own output.

## Provenance

| | |
|---|---|
| Date | 2026-08-22 |
| Commit | `6dec92c`, plus the then-untracked `src/startup.c` |
| Compiler | Apple clang version 17.0.0 (clang-1700.6.3.2) |
| Linker | Homebrew LLD 20.1.3 |
| Binutils | Homebrew LLVM 20.1.3 (`llvm-readelf`, `llvm-objdump`, `llvm-objcopy`, `llvm-readobj`) |
| Target | `arm-none-eabi`, Cortex-M0, Thumb, freestanding |

Output below is specific to these versions. LLD's defaults in particular are version-dependent, and
one of them is load-bearing here — see *Why the segments do not collide*.

## The state under inspection

Two translation units, one linker script, no vector table and no `ENTRY()`.

`src/main.c` is a placeholder that never returns:

```c
int main(void)
{
    for (;;) {
    }
}
```

`src/startup.c` holds the first project-owned startup code:

```c
extern int main(void);

void Reset_Handler(void)
{
    main();

    for (;;) {
    }
}
```

`Reset_Handler` is currently unreachable. Nothing points the processor at it. That is deliberate:
this step introduces the symbol so it can be inspected before it is wired up.

---

# Stage 1 — Compile

One object per translation unit. `-c` stops the driver before linking.

```sh
clang --target=arm-none-eabi -mcpu=cortex-m0 -mthumb -ffreestanding \
  -c src/main.c -o build/main.o

clang --target=arm-none-eabi -mcpu=cortex-m0 -mthumb -ffreestanding \
  -c src/startup.c -o build/startup.o
```

Both succeed silently. Silence is the expected output of a successful compile; check `$?` rather
than looking for a confirmation message.

What the flags do:

| flag | effect |
|---|---|
| `--target=arm-none-eabi` | Cross-compile. `none` = no OS, `eabi` = the ARM embedded ABI. |
| `-mcpu=cortex-m0` | Selects the Armv6-M instruction subset. Prevents emitting instructions the part cannot execute. |
| `-mthumb` | Thumb encoding. Redundant on Cortex-M0, which has no ARM state, but explicit. |
| `-ffreestanding` | No hosted C library or runtime assumptions. `main` gets no special status. |

```sh
file build/startup.o
```

```
build/startup.o: ELF 32-bit LSB relocatable, ARM, EABI5 version 1 (SYSV), not stripped
```

**Relocatable** is the word that matters. This is not a program. It is a fragment whose addresses
have not been decided.

---

# Stage 2 — Read the object *before* linking

This is the half people skip, and it is the half that explains what linking actually does.

## 2.1 Sections

```sh
llvm-readelf -S build/startup.o
```

```
There are 11 section headers, starting at offset 0x1ac:

Section Headers:
  [Nr] Name              Type            Address  Off    Size   ES Flg Lk Inf Al
  [ 0]                   NULL            00000000 000000 000000 00      0   0  0
  [ 1] .strtab           STRTAB          00000000 000129 000081 00      0   0  1
  [ 2] .text             PROGBITS        00000000 000034 00000c 00  AX  0   0  4
  [ 3] .rel.text         REL             00000000 000118 000008 08   I 10   2  4
  [ 4] .ARM.exidx        ARM_EXIDX       00000000 000040 000008 00  AL  2   0  4
  [ 5] .rel.ARM.exidx    REL             00000000 000120 000008 08   I 10   4  4
  [ 6] .comment          PROGBITS        00000000 000048 00002f 01  MS  0   0  1
  [ 7] .note.GNU-stack   PROGBITS        00000000 000077 000000 00      0   0  1
  [ 8] .ARM.attributes   ARM_ATTRIBUTES  00000000 000077 000041 00      0   0  1
  [ 9] .llvm_addrsig     LLVM_ADDRSIG    00000000 000128 000001 00   E 10   0  1
  [10] .symtab           SYMTAB          00000000 0000b8 000060 10      1   4  4
```

Three things to notice:

1. **Every `Address` is `00000000`.** Not a placement — an absence of one. Deciding addresses is the
   linker's job.

2. **The section is plain `.text`, not `.text.Reset_Handler`.** Per-function sections require
   `-ffunction-sections`, which this build does not pass. That is fine now, but it forecloses
   `--gc-sections` later: without per-function sections the linker cannot discard individual unused
   functions, only whole sections.

3. **`.ARM.exidx` exists, 8 bytes of it.** Exception-unwind tables, emitted by default even for
   freestanding C with no exceptions in sight. Remember this; it resurfaces in Stage 5 as bytes in
   the final image.

## 2.2 Symbols

```sh
llvm-readelf -s build/startup.o
```

```
Symbol table '.symtab' contains 6 entries:
   Num:    Value  Size Type    Bind   Vis       Ndx Name
     0: 00000000     0 NOTYPE  LOCAL  DEFAULT   UND 
     1: 00000000     0 FILE    LOCAL  DEFAULT   ABS startup.c
     2: 00000000     0 SECTION LOCAL  DEFAULT     2 .text
     3: 00000000     0 NOTYPE  LOCAL  DEFAULT     2 $t
     4: 00000001    12 FUNC    GLOBAL DEFAULT     2 Reset_Handler
     5: 00000000     0 NOTYPE  GLOBAL DEFAULT   UND main
```

- `Reset_Handler` has `Value 00000001` — offset 0 within section 2, **plus the Thumb bit**. See
  *The Thumb bit* below.
- `main` is `UND`: **undefined**. This object references a symbol it does not define. That is a
  promise the linker must keep, and it will fail loudly if it cannot.
- `$t` is a *mapping symbol*, an ARM-specific marker meaning "Thumb code begins here". Note its
  value is `00000000` — **even**, unlike `Reset_Handler` at the same location.

## 2.3 Relocations — the unkept promises

```sh
llvm-readelf -r build/startup.o
```

```
Relocation section '.rel.text' at offset 0x118 contains 1 entries:
 Offset     Info    Type                Sym. Value  Symbol's Name
00000004  0000050a R_ARM_THM_CALL         00000000   main

Relocation section '.rel.ARM.exidx' at offset 0x120 contains 1 entries:
 Offset     Info    Type                Sym. Value  Symbol's Name
00000000  0000022a R_ARM_PREL31           00000000   .text
```

This is a to-do list addressed to the linker. It reads: *at byte offset 4 of `.text` there is a
Thumb call whose target I could not compute; when you know where `main` lives, patch it.*

`R_ARM_THM_CALL` is the relocation type for a Thumb `BL`. `Sym. Value 00000000` is not the answer —
it is the placeholder standing in for the answer.

## 2.4 Disassembly — the placeholder, visible

```sh
llvm-objdump -d build/startup.o
```

```
build/startup.o:	file format elf32-littlearm

Disassembly of section .text:

00000000 <Reset_Handler>:
       0: b580         	push	{r7, lr}
       2: af00         	add	r7, sp, #0x0
       4: f7ff fffe    	bl	0x4 <Reset_Handler+0x4> @ imm = #-0x4
       8: e7ff         	b	0xa <Reset_Handler+0xa> @ imm = #-0x2
       a: e7fe         	b	0xa <Reset_Handler+0xa> @ imm = #-0x4
```

**`bl` at offset 4 branches to itself.** Encoding `f7ff fffe`, displacement −4. It is not a call to
anything; it is a hole shaped like a call. Compare it against the linked version in Stage 4.4 —
that diff is the clearest single illustration of what a linker does.

### The stack, on the first instruction

```
       0: b580         	push	{r7, lr}
```

`Reset_Handler` stores through SP as its very first act. At the default optimisation level the
compiler builds a frame pointer for any function that calls another.

This is the most consequential line in the file, for a reason that has nothing to do with C:
**`Reset_Handler` is the first code to run after reset, and it writes to the stack immediately.**
If MSP does not already hold a valid value when the processor arrives here, the device faults before
reaching `main`.

That is precisely what word 0 of the vector table is for, and it is why `_stack_top` was defined
before this function was written. The lesson order is not arbitrary; the hardware imposes it.

---

# Stage 3 — Link

```sh
ld.lld -T linker/stm32f030r8.ld \
  build/main.o build/startup.o \
  -o build/fm001.elf \
  -Map build/fm001.map
```

```
ld.lld: warning: cannot find entry symbol _start; not setting start address
```

Expected. There is no `ENTRY()` directive in the linker script, so LLD looks for its default entry
symbol `_start`, does not find it, and leaves the ELF entry address at zero. Stage 4.3 shows the
consequence. Adding `ENTRY(Reset_Handler)` is the next intended step and will clear this.

`-T` selects the script. `-Map` writes a placement report — the single most useful linker artifact
and the one most often left unrequested.

---

# Stage 4 — Read the linked executable

## 4.1 Sections now have addresses

```sh
llvm-readelf -S build/fm001.elf
```

```
There are 8 section headers, starting at offset 0x101a8:

Section Headers:
  [Nr] Name              Type            Address  Off    Size   ES Flg Lk Inf Al
  [ 0]                   NULL            00000000 000000 000000 00      0   0  0
  [ 1] .text             PROGBITS        08000000 010000 000010 00  AX  0   0  4
  [ 2] .ARM.exidx        ARM_EXIDX       08000010 010010 000010 00  AL  1   0  4
  [ 3] .comment          PROGBITS        00000000 010020 00004b 01  MS  0   0  1
  [ 4] .ARM.attributes   ARM_ATTRIBUTES  00000000 01006b 000041 00      0   0  1
  [ 5] .symtab           SYMTAB          00000000 0100ac 000080 10      7   5  4
  [ 6] .shstrtab         STRTAB          00000000 01012c 000045 00      0   0  1
  [ 7] .strtab           STRTAB          00000000 010171 000036 00      0   0  1
```

`.text` is now at `0x08000000` — `ORIGIN(FLASH)`, exactly as the `SECTIONS` block demands — and has
grown from 4 bytes to `0x10` = 16 as the second object's code joined it.

Sections with `Address 00000000` (`.comment`, `.symtab`, `.strtab`…) are **not allocated**. They
have no `A` flag, exist only in the file, and never occupy target memory. Only `.text` and
`.ARM.exidx` carry `A`.

## 4.2 Symbols, resolved

```sh
llvm-readelf -s build/fm001.elf
```

```
Symbol table '.symtab' contains 8 entries:
   Num:    Value  Size Type    Bind   Vis       Ndx Name
     0: 00000000     0 NOTYPE  LOCAL  DEFAULT   UND 
     1: 00000000     0 FILE    LOCAL  DEFAULT   ABS main.c
     2: 08000000     0 NOTYPE  LOCAL  DEFAULT     1 $t
     3: 00000000     0 FILE    LOCAL  DEFAULT   ABS startup.c
     4: 08000004     0 NOTYPE  LOCAL  DEFAULT     1 $t
     5: 08000001     4 FUNC    GLOBAL DEFAULT     1 main
     6: 08000005    12 FUNC    GLOBAL DEFAULT     1 Reset_Handler
     7: 20002000     0 NOTYPE  GLOBAL DEFAULT   ABS _stack_top
```

No `UND` entries remain apart from the reserved null symbol at index 0. Every promise kept.

Two different kinds of symbol sit in this table, and the `Ndx` column separates them:

- `Ndx 1` — bound to section 1 (`.text`). These move if the section moves.
- `Ndx ABS` — absolute. `_stack_top` is a fixed number the linker computed from
  `ORIGIN(SRAM) + LENGTH(SRAM)`; it is attached to no section, has `Size 0`, and emits no bytes.
  It is an address handed to code, not storage.

### The Thumb bit

```
     2: 08000000     0 NOTYPE  LOCAL  DEFAULT     1 $t              <- even
     4: 08000004     0 NOTYPE  LOCAL  DEFAULT     1 $t              <- even
     5: 08000001     4 FUNC    GLOBAL DEFAULT     1 main            <- odd
     6: 08000005    12 FUNC    GLOBAL DEFAULT     1 Reset_Handler   <- odd
```

`Reset_Handler` reports `0x08000005`, but its first instruction is at `0x08000004` (Stage 4.4
confirms this). **Bit 0 is not part of the address.**

It is the ARM interworking convention: in a value destined for the program counter, bit 0 selects
the instruction set — 1 = Thumb, 0 = ARM — and is loaded into the EPSR T-bit by `BX`, `BLX` and
`POP {PC}`. Cortex-M0 is Thumb-only, so every function symbol carries it set.

This is the same mechanism PM0215 Rev 2 page 7/72 describes for the reset vector:

> On reset, the processor loads the PC with the value of the reset vector, which is at address
> 0x00000004. Bit[0] of the value is loaded into the EPSR T-bit at reset and must be 1.

The `$t` symbols are the proof that this is a property of *function symbols* rather than of the
location. `$t` and `Reset_Handler` describe the same byte, but `$t` is even. A mapping symbol marks
an address; a `FUNC` symbol names a callable entity, so it carries the state bit.

**The practical payoff:** when the vector table is written, taking `&Reset_Handler` in C already
yields `0x08000005`. No manual `| 1` is required. Startup code that writes `| 1` explicitly is
compensating for having written the address as a raw integer.

## 4.3 Segments — what actually gets loaded

```sh
llvm-readelf -l build/fm001.elf
```

```
Elf file type is EXEC (Executable file)
Entry point 0x0
There are 4 program headers, starting at offset 52

Program Headers:
  Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
  LOAD           0x010000 0x08000000 0x08000000 0x00010 0x00010 R E 0x10000
  LOAD           0x010010 0x08000010 0x08000010 0x00010 0x00010 R   0x10000
  GNU_STACK      0x000000 0x00000000 0x00000000 0x00000 0x00000 RW  0x0
  EXIDX          0x010010 0x08000010 0x08000010 0x00010 0x00010 R   0x4

 Section to Segment mapping:
  Segment Sections...
   00     .text 
   01     .ARM.exidx 
   02     
   03     .ARM.exidx 
   None   .comment .ARM.attributes .symtab .shstrtab .strtab 
```

`Entry point 0x0` — the visible consequence of the `_start` warning. Nothing here tells a loader or
debugger where execution begins. Harmless for a device that boots from a vector table, but it is
missing metadata that `ENTRY(Reset_Handler)` supplies.

**Sections are a link-time view; segments are a load-time view.** The `None` row lists everything
that will never reach the target.

### Why the segments do not collide

Two `PT_LOAD` segments, because the permissions differ: `.text` is `R E`, `.ARM.exidx` is `R`. Both
are aligned `0x10000` — LLD's default max-page-size for this target.

This is the same mechanism that produced the earlier `0x08010010` overflow when the linker script
had no `SECTIONS` block. It causes no trouble here because the required congruence already holds:
ELF demands `p_vaddr ≡ p_offset (mod align)`, and

```
0x08000000 mod 0x10000 = 0x0000     0x010000 mod 0x10000 = 0x0000   ✓
0x08000010 mod 0x10000 = 0x0010     0x010010 mod 0x10000 = 0x0010   ✓
```

Both segments satisfy it where they already sit, so the linker never needs to push the second one to
the next 64 KiB boundary. In the orphan case it did, and 4 bytes of code landed past the end of
flash. See `.agent/discoveries.md` for the measurements that pinned this down.

## 4.4 Disassembly — the promise kept

```sh
llvm-objdump -d --section=.text build/fm001.elf
```

```
build/fm001.elf:	file format elf32-littlearm

Disassembly of section .text:

08000000 <main>:
 8000000: e7ff         	b	0x8000002 <main+0x2>    @ imm = #-0x2
 8000002: e7fe         	b	0x8000002 <main+0x2>    @ imm = #-0x4

08000004 <Reset_Handler>:
 8000004: b580         	push	{r7, lr}
 8000006: af00         	add	r7, sp, #0x0
 8000008: f7ff fffa    	bl	0x8000000 <main>        @ imm = #-0xc
 800000c: e7ff         	b	0x800000e <Reset_Handler+0xa> @ imm = #-0x2
 800000e: e7fe         	b	0x800000e <Reset_Handler+0xa> @ imm = #-0x4
```

Compare the call against Stage 2.4:

| | encoding | target |
|---|---|---|
| before link | `f7ff fffe` | `0x4` — itself |
| after link | `f7ff fffa` | `0x08000000` — `main` |

Two bytes changed. That is the relocation being applied.

**Note the target is `0x08000000` — even.** `main`'s symbol value is `0x08000001`, but `BL` does not
change instruction-set state, so no state bit belongs in the encoding. The linker masked bit 0 off
when computing the branch displacement. Bit 0 matters for values loaded into PC (`BX`, `POP {PC}`,
the reset vector); it does not appear in a `BL`.

Header text confirms `08000004 <Reset_Handler>` — the *instruction* address, `0x08000005 & ~1`.

## 4.5 The map file — who contributed what

```sh
cat build/fm001.map
```

```
     VMA      LMA     Size Align Out     In      Symbol
       0        0        0     1 _stack_top = ORIGIN(SRAM) + LENGTH(SRAM)
 8000000  8000000       10     4 .text
 8000000  8000000        4     4         build/main.o:(.text)
 8000000  8000000        0     1                 $t
 8000001  8000001        4     1                 main
 8000004  8000004        c     4         build/startup.o:(.text)
 8000004  8000004        0     1                 $t
 8000005  8000005        c     1                 Reset_Handler
 8000010  8000010       10     4 .ARM.exidx
 8000010  8000010       10     4         <internal>:(.ARM.exidx)
       0        0       4b     1 .comment
       0        0       4b     1         <internal>:(.comment)
       0        0       41     1 .ARM.attributes
       0        0       41     1         build/main.o:(.ARM.attributes)
       0        0       80     4 .symtab
       0        0       80     4         <internal>:(.symtab)
       0        0       45     1 .shstrtab
       0        0       45     1         <internal>:(.shstrtab)
       0        0       36     1 .strtab
       0        0       36     1         <internal>:(.strtab)
```

The three-level indentation is the structure: **output section → contributing input section →
symbols within it.**

Line 2 answers a question posed by this step: **did `*(.text*)` capture the new code automatically?**
Yes. `build/startup.o:(.text)` appears under `.text` with no change to the linker script. The glob
`.text*` matches plain `.text` as well as any `.text.foo`, and `*(...)` matches all input files.

`_stack_top` appears with VMA, LMA and Size all `0`. It is an assignment, not storage.

`<internal>` marks sections the linker synthesised rather than copied from an input file.

---

# Stage 5 — The raw image

```sh
llvm-objcopy -O binary build/fm001.elf build/fm001.bin
wc -c < build/fm001.bin
xxd build/fm001.bin
```

```
      32
```
```
00000000: ffe7 fee7 80b5 00af fff7 faff ffe7 fee7  ................
00000010: f0ff ff7f 0100 0000 f8ff ff7f 0100 0000  ................
```

`objcopy -O binary` strips all ELF structure and emits allocated sections as flat bytes — what a
flash programmer would actually write.

## The defect, visible as bytes

The first eight bytes are `ff e7 fe e7 80 b5 00 af`. Read as instructions those are `b`, `b`,
`push {r7, lr}`, `add r7, sp, #0`.

**Those are instructions sitting where the initial stack pointer and reset vector must go.** Per
PM0215 the processor will load MSP from the first word and PC from the second. Programmed to a
device as-is, this image sets MSP to `0xe7fee7ff` and PC to `0xaf00b580` — both nonsense. It cannot
boot. That is the whole point of the next step, and here it is as hex.

## The image is bigger than the code

`.text` is 16 bytes, but the file is 32. The second sixteen are `.ARM.exidx` — the exception-unwind
tables from Stage 2.1, carried all the way through because they are an allocated section.

```sh
llvm-readobj --unwind build/fm001.elf
```

```
UnwindInformation {
  UnwindIndexTable {
    SectionIndex: 2
    SectionName: .ARM.exidx
    SectionOffset: 0x10010
    Entries [
      Entry {
        FunctionAddress: 0x8000000
        Model: CantUnwind
      }
      Entry {
        FunctionAddress: 0x8000010
        Model: CantUnwind
      }
    ]
  }
}
```

Two entries, but note the second `FunctionAddress` is `0x8000010` — **not** `Reset_Handler` at
`0x08000004`. `0x08000010` is one past the end of `.text`. That entry is a **sentinel** marking
where coverage ends.

So two functions produced **one** real entry plus a terminator. The adjacent identical `CantUnwind`
entries were coalesced.

Linking `main.o` alone makes this unambiguous:

```sh
ld.lld -T linker/stm32f030r8.ld build/main.o -o /tmp/one.elf
llvm-readelf -S /tmp/one.elf | grep exidx
llvm-readobj --unwind /tmp/one.elf | grep -E 'FunctionAddress|Model'
```

```
  [ 2] .ARM.exidx        ARM_EXIDX       08000004 010004 000010 00  AL  1   0  4
        FunctionAddress: 0x8000000
        Model: CantUnwind
        FunctionAddress: 0x8000004
        Model: CantUnwind
```

| | functions | `.ARM.exidx` size | real entries | sentinel at | end of `.text` |
|---|---|---|---|---|---|
| `main.o` only | 1 | `0x10` | 1 | `0x08000004` | `0x08000004` |
| both objects | 2 | `0x10` | 1 | `0x08000010` | `0x08000010` |

Three things line up. The size does not grow when a function is added. There is exactly one real
entry in both cases. And the trailing entry tracks the end of `.text` precisely in each — which is
what a sentinel does and what a real function entry could not do, since no function begins there.

Half of this image is metadata for a C++ feature that is not in use. Worth removing later
(`-fno-unwind-tables`, or `/DISCARD/` in the linker script); noted here rather than fixed, because
this step changes nothing but `Reset_Handler`.

---

# Stage 6 — Two experiments

## 6.1 Placement inside `.text` is command-line order

```sh
ld.lld -T linker/stm32f030r8.ld build/startup.o build/main.o \
  -o /tmp/flip.elf -Map /tmp/flip.map
grep -E 'main|Reset_Handler|\.text' /tmp/flip.map
```

```
 8000000  8000000       10     4 .text
 8000000  8000000        c     4         build/startup.o:(.text)
 8000001  8000001        c     1                 Reset_Handler
 800000c  800000c        4     4         build/main.o:(.text)
 800000d  800000d        4     1                 main
```

```sh
llvm-readelf -s /tmp/flip.elf | grep FUNC
```

```
     5: 08000001    12 FUNC    GLOBAL DEFAULT     1 Reset_Handler
     6: 0800000d     4 FUNC    GLOBAL DEFAULT     1 main
```

Swapping two arguments swapped the layout. `*(.text*)` contributes input sections in the order the
files appear on the command line; nothing marks the reset handler as special or deserving of a low
address.

This is worth knowing before it becomes a debugging surprise. Once the vector table exists it will
hold an explicit pointer, so ordering stays a layout preference rather than a correctness
requirement — but a build system that reorders its inputs will silently reshuffle the image.

## 6.2 The Thumb bit lives in the symbol, not the section

```sh
llvm-readelf -s build/fm001.elf | grep -E '\$t|FUNC'
```

```
     2: 08000000     0 NOTYPE  LOCAL  DEFAULT     1 $t
     4: 08000004     0 NOTYPE  LOCAL  DEFAULT     1 $t
     5: 08000001     4 FUNC    GLOBAL DEFAULT     1 main
     6: 08000005    12 FUNC    GLOBAL DEFAULT     1 Reset_Handler
```

Same locations, different values, because the two symbol kinds mean different things.

---

# What this image still cannot do

| | |
|---|---|
| No vector table | Words 0 and 1 of flash are instructions, not MSP and the reset vector. Cannot boot. |
| No `ENTRY()` | `Entry point 0x0`; the `_start` warning stands. |
| `Reset_Handler` unreachable | Nothing references it. Only the (currently absent) vector table will. |
| No `.data` / `.bss` handling | No such sections exist yet. Initialised and zeroed statics are unsupported. |
| Unwind tables shipped | Half the binary is `.ARM.exidx` metadata for unused C++ exception support. |
| Stack unbounded | `_stack_top` is all of SRAM. Cortex-M0 has no MPU and no stack-limit register, so overflow is silent. |

Next intended step: `ENTRY(Reset_Handler)`, which fixes row 2 without changing the image layout.

---

# Command reference

```sh
# compile
clang --target=arm-none-eabi -mcpu=cortex-m0 -mthumb -ffreestanding -c src/main.c    -o build/main.o
clang --target=arm-none-eabi -mcpu=cortex-m0 -mthumb -ffreestanding -c src/startup.c -o build/startup.o

# link
ld.lld -T linker/stm32f030r8.ld build/main.o build/startup.o -o build/fm001.elf -Map build/fm001.map

# flatten
llvm-objcopy -O binary build/fm001.elf build/fm001.bin
```

| command | answers |
|---|---|
| `file X.o` | Is this a relocatable object or an executable? |
| `llvm-readelf -S X` | What sections exist, how big, what permissions, placed where? |
| `llvm-readelf -s X` | What symbols, at what values, defined or undefined? |
| `llvm-readelf -r X.o` | What could the compiler not resolve on its own? |
| `llvm-readelf -l X.elf` | What actually gets loaded, and at what alignment? |
| `llvm-objdump -d X` | What instructions, at what addresses? |
| `llvm-objdump -s --section=N X` | Raw bytes of one section. |
| `llvm-readobj --unwind X.elf` | Decode `.ARM.exidx` instead of reading it as hex. |
| `xxd X.bin` | What will actually be written to flash? |
| `cat X.map` | Which input file contributed which bytes, in what order? |

Flags deliberately **not** used yet, listed because they change the output above:

- `-ffunction-sections` — emits `.text.Reset_Handler` instead of `.text`; prerequisite for `--gc-sections`.
- `-O2` — the `push {r7, lr}` frame in `Reset_Handler` likely collapses to a tail call. Useful for
  distinguishing `-O0` scaffolding from necessity.
- `-fno-unwind-tables` — would remove `.ARM.exidx`, halving the image.

---

# Unverified

Kept separate per `AGENTS.md`: everything above is observed tool output; the following are
explanations that have not been independently tested.

- For `.ARM.exidx`, the *observations* in Stage 5 are solid: one real entry for two functions, a
  trailing entry that tracks the end of `.text`, and no size growth when a function is added. The
  word "coalesced" is the inferred mechanism. It has not been checked against LLD source or the ARM
  EHABI specification, and no test was constructed with functions of differing unwind models to force
  the non-merging case.
- No claim here is hardware-verified. Nothing in this document has been programmed to a device.
  The assertion that this image "cannot boot" is derived from PM0215 and the byte content, not from
  observation.
