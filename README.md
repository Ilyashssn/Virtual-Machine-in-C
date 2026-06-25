# 16-Bit Virtual Machine — Architecture Reference

Byte-oriented virtual processor with a 16-bit address space, 8-bit registers, and a Python assembler. This document describes the **current implementation** as defined in `VM.c` and `assembler.py`.

---

## 1. Overview

The system consists of two components:

| Component | File | Role |
|-----------|------|------|
| **Virtual machine** | `VM.c` | Loads a binary program into main memory and executes it via a fetch-decode-execute loop. |
| **Assembler** | `assembler.py` | Translates assembly source (`.txt` / `.asm`) into raw bytecode. |

### Toolchain

```text
source.asm  ──►  assembler.py  ──►  program.bin  ──►  VM
```

```bash
python assembler.py program.asm program.bin
gcc -o vm VM.c
./vm program.bin
```

On `STOP`, the VM prints register and flag state via `print_state()`.

---

## 2. Architectural Parameters

| Parameter | Value |
|-----------|-------|
| Main memory size | 65 536 bytes (64 KiB) |
| RAM size | 256 bytes |
| Register width | 8 bits |
| Address width | 16 bits |
| Endianness (jump addresses) | Big-endian |
| Integer literals in assembler | Decimal or hex (`0x` prefix) |

---

## 3. Memory Organization

### 3.1 Main memory (`memory[65536]`)

Single unified space used for **program code** and **stack**. Both share the same array.

```text
Address
0x0000  ┌─────────────────────┐
        │                     │
        │   Program / code    │
        │                     │
        ├─────────────────────┤
        │                     │
        │   Stack (↓ grows)   │
        │                     │
0xFFFF  └─────────────────────┘
```

| Symbol | Initial value | Description |
|--------|---------------|-------------|
| `PC` | `0x0000` | Program counter — address of next byte to fetch |
| `SP` | `0xFFFF` | Stack pointer — address of top stack element |

**Stack behavior:**
- `PUSH`: decrement `SP`, then write register value to `memory[SP]`
- `POP`: read from `memory[SP]`, increment `SP`, write into register
- Stack grows toward **lower** addresses

**Stack fault detection:**
- Overflow: after `PUSH`, if `SP <= PC` → halt with `STACK OVERFLOW`
- Underflow: before `POP`, if `SP >= 65535` → halt with `STACK UNDERFLOW`

### 3.2 Data RAM (`RAM[256]`)

Separate 256-byte storage, indexed `0x00`–`0xFF`. Accessed only through load/store addressing modes and the `STORE` instruction. Not used for code or stack.

---

## 4. Register File

Six general-purpose 8-bit registers:

| Name | Index | Purpose |
|------|-------|---------|
| `R0` | 0 | General purpose; implicit operand for `MUL` |
| `R1` | 1 | General purpose |
| `R2` | 2 | General purpose |
| `R3` | 3 | General purpose |
| `LR` | 4 | Loop counter; used by `LOOP` |
| `AR` | 5 | Holds high byte of `MUL` result |

All registers reset to `0` at startup. The VM does not bounds-check register indices in bytecode; invalid indices read/write outside `registers[6]` (undefined behavior).

---

## 5. Status Flags

Two flags, stored as integers (`0` or `1`):

| Flag | Name | Meaning |
|------|------|---------|
| `CF` | Carry | Set by arithmetic/compare as defined per instruction |
| `ZF` | Zero | Set when result equals zero (or operands equal for `CMP`) |

Initial state: `CF = 0`, `ZF = 0`.

---

## 6. Execution Cycle

Each iteration:

1. Read `opcode = memory[PC]`; increment `PC`
2. Decode and execute via `switch(opcode)`
3. Instruction handler reads operands from `memory[PC]` and updates `PC` accordingly
4. Update flags where applicable
5. Repeat until `running = 0` (`STOP`, fault, or invalid opcode)

Invalid opcode → print `BUG HAPPENED`, halt.

---

## 7. Encoding Conventions

### 7.1 Jump addresses (big-endian)

Used by `JMP`, all conditional jumps, and `LOOP`.

```text
Byte 1 (at PC):   address_high = (target >> 8) & 0xFF
Byte 2 (at PC+1): address_low  = target & 0xFF

target = address_low | (address_high << 8)
```

### 7.2 Three-operand descriptor (LOAD, ADD, SUB, AND)

```text
Byte 1 (at PC): descriptor
  bits 7–6 : addressing mode (0–3)
  bits 5–0 : destination register index

Byte 2 (at PC+1): source operand (encoding depends on mode)
```

```text
  7   6   5   4   3   2   1   0
┌───────┬───────────────────────┐
│  M    │   destination reg     │
└───────┴───────────────────────┘
```

| Mode `M` | Name | Source operand byte |
|----------|------|---------------------|
| 0 | Immediate | 8-bit value `0–255` |
| 1 | Register | Source register index |
| 2 | Direct RAM | RAM address `0–255`; read `RAM[addr]` |
| 3 | Indirect RAM | Register index; read `RAM[registers[idx]]` |

**Assembly syntax:**

```text
LOAD R0, 42          ; mode 0
ADD  R1, R2          ; mode 1
SUB  R2, [0x10]      ; mode 2
AND  R0, [R1]        ; mode 3
```

### 7.3 STORE operand byte

```text
Byte 1: RAM address (0–255)
Byte 2: source descriptor
  bit 7    : 0 = immediate, 1 = register
  bits 6–0 : immediate value (0–127) or register index
```

```text
STORE 0x20, 42       ; immediate 42 → RAM[0x20]
STORE 0x20, R1       ; registers[R1] → RAM[0x20]
```

---

## 8. Instruction Set Reference

### Summary table

| Opcode | Mnemonic | Size (bytes) | Flags updated |
|--------|----------|:------------:|:-------------:|
| `0x01` | `LOAD` | 3 | — |
| `0x02` | `ADD` | 3 | CF, ZF |
| `0x03` | `SUB` | 3 | CF, ZF |
| `0x04` | `JMP` | 3 | — |
| `0x05` | `MUL` | 2 | — |
| `0x06` | `PUSH` | 2 | — |
| `0x07` | `POP` | 2 | — |
| `0x08` | `JZ` | 3 | — |
| `0x09` | `JNZ` | 3 | — |
| `0x0A` | `JC` | 3 | — |
| `0x0B` | `JNC` | 3 | — |
| `0x0C` | `CMP` | 3 | CF, ZF |
| `0x0D` | `JE` | 3 | — |
| `0x0E` | `JL` | 3 | — |
| `0x0F` | `JG` | 3 | — |
| `0x10` | `STORE` | 3 | — |
| `0x11` | `LOOP` | 3 | — |
| `0x12` | `AND` | 3 | CF, ZF |
| `0xFF` | `STOP` | 1 | — |

---

### `LOAD` — `0x01`

**Syntax:** `LOAD dest, source`  
**Encoding:** `[0x01] [mode<<6 | dest] [operand]`

Load source into destination register. Source resolved by addressing mode (§7.2).

**Flags:** unchanged  
**Operation:** `dest ← source`

---

### `ADD` — `0x02`

**Syntax:** `ADD dest, source`  
**Encoding:** `[0x02] [mode<<6 | dest] [operand]`

**Operation:** `dest ← dest + source` (8-bit wrap)  
**Flags:**
- `CF = 1` if sum exceeds 255 (computed on 16-bit intermediate before truncation)
- `ZF = 1` if result is 0

---

### `SUB` — `0x03`

**Syntax:** `SUB dest, source`  
**Encoding:** `[0x03] [mode<<6 | dest] [operand]`

**Operation:** `dest ← dest - source`  
**Flags:**
- `CF = 1` if `dest < source` (unsigned borrow), evaluated **before** subtraction
- `ZF = 1` if result is 0

---

### `AND` — `0x12`

**Syntax:** `AND dest, source`  
**Encoding:** `[0x12] [mode<<6 | dest] [operand]`

**Operation:** `dest ← dest & source`  
**Flags:**
- `CF = 0`
- `ZF = 1` if result is 0

---

### `MUL` — `0x05`

**Syntax:** `MUL Rn`  
**Encoding:** `[0x05] [n]`

**Operation:** 16-bit product of `R0 × Rn`:
- `R0 ← product & 0xFF` (low byte)
- `AR ← (product >> 8) & 0xFF` (high byte)

**Flags:** unchanged

---

### `CMP` — `0x0C`

**Syntax:** `CMP Ra, Rb`  
**Encoding:** `[0x0C] [a] [b]`

Compare `registers[a]` to `registers[b]` (no register write).

| Condition | CF | ZF |
|-----------|:--:|:--:|
| equal | 0 | 1 |
| `a > b` (unsigned) | 0 | 0 |
| `a < b` (unsigned) | 1 | 0 |

---

### `STORE` — `0x10`

**Syntax:** `STORE addr, source`  
**Encoding:** `[0x10] [addr] [source_byte]`

Write to `RAM[addr]`. Source is immediate (0–127) or register per §7.3.

**Flags:** unchanged

---

### `PUSH` — `0x06`

**Syntax:** `PUSH Rn`  
**Encoding:** `[0x06] [n]`

`SP ← SP - 1`; `memory[SP] ← registers[n]`

---

### `POP` — `0x07`

**Syntax:** `POP Rn`  
**Encoding:** `[0x07] [n]`

`registers[n] ← memory[SP]`; `SP ← SP + 1`

---

### Jump instructions

All jumps: **3 bytes** — `[opcode] [addr_high] [addr_low]`

| Opcode | Mnemonic | Branch condition |
|--------|----------|------------------|
| `0x04` | `JMP` | unconditional |
| `0x08` | `JZ` | `ZF == 1` |
| `0x09` | `JNZ` | `ZF == 0` |
| `0x0A` | `JC` | `CF == 1` |
| `0x0B` | `JNC` | `CF == 0` |
| `0x0D` | `JE` | `ZF == 1` (same condition as `JZ`) |
| `0x0E` | `JL` | `CF == 1` |
| `0x0F` | `JG` | `CF == 0` and `ZF == 0` |

If condition false: `PC ← PC + 2` (skip address bytes).  
If condition true: `PC ← target`.

**Syntax:** `JMP label` or `JMP 0x0010`

---

### `LOOP` — `0x11`

**Syntax:** `LOOP label`  
**Encoding:** `[0x11] [addr_high] [addr_low]`

Uses **LR (`registers[4]`)** as counter:

| Condition | Action |
|-----------|--------|
| `LR == 0` | `PC ← PC + 2` (fall through) |
| `LR != 0` | `PC ← target`; `LR ← LR - 1` |

Equivalent to: decrement loop counter and jump if non-zero, without explicit `SUB`/`JNZ`.

---

### `STOP` — `0xFF`

**Syntax:** `STOP`  
**Encoding:** `[0xFF]`

Halts execution, prints `RAN SUCCESFULLY`, dumps CPU state.

---

## 9. Assembler Reference

### 9.1 Invocation

```bash
python assembler.py <source> <output>
```

Two-pass assembly: pass 1 resolves label addresses, pass 2 emits bytecode.

### 9.2 Source format

- One instruction per line
- `#`-style comments via `;` (text after `;` ignored)
- Commas optional: `LOAD R0, 1` = `LOAD R0 1`
- Case insensitive
- Labels: `name:` at start of line; address = byte offset of next instruction

```assembly
START:
    LOAD R0, 0
    JMP START
```

### 9.3 Supported mnemonics

All opcodes in §8. Register names: `R0`, `R1`, `R2`, `R3`, `LR`, `AR`.

### 9.4 Assembler limits

- Immediate values: `0–255` (LOAD/ADD/SUB/AND)
- STORE immediates: `0–127`
- RAM addresses: `0–255`
- Jump targets: `0–65535` or label
- No macros, includes, or equates

---

## 10. VM Interface

```bash
vm <program.bin>
```

Requires exactly one argument. Loads up to 65536 bytes from the file into `memory[]` starting at address 0.

**Output on success (`STOP`):**

```text
[VM] N bytes succesfully loaded
RAN SUCCESFULLY
R0=... R1=... R2=... R3=... LR=... AR=...
CF=... ZF=... PC=... SP=...
```

**Error exits:**
- No argument → `ERROR: No input file provided`
- File not found → `BUG HAPPENED`
- Invalid opcode / invalid addressing mode → `BUG HAPPENED`
- Stack overflow / underflow → message then halt (no register dump)

---

## 11. Worked Example — Fibonacci (N = 7)

**Source** (`assembly_code_example1.txt`):

```assembly
LOAD LR, 7
LOAD R0, 0
LOAD R1, 1
WHILE:
LOAD R2, R1
ADD R1, R0
LOAD R0, R2
SUB LR, 1
JNZ WHILE
STOP
```

**Generated bytecode:**

| Addr | Bytes | Instruction |
|------|-------|-------------|
| 0 | `01 04 07` | `LOAD LR, 7` |
| 3 | `01 00 00` | `LOAD R0, 0` |
| 6 | `01 01 01` | `LOAD R1, 1` |
| 9 | `01 42 01` | `LOAD R2, R1` |
| 12 | `02 41 00` | `ADD R1, R0` |
| 15 | `01 40 02` | `LOAD R0, R2` |
| 18 | `03 04 01` | `SUB LR, 1` |
| 21 | `09 00 09` | `JNZ WHILE` |
| 24 | `FF` | `STOP` |

**Expected final state:** `R0 = 13`, `R1 = 21`, `LR = 0`, `ZF = 1`

---

## 12. File Layout

```text
VM/
├── VM.c                      # Virtual machine
├── assembler.py              # Assembler
├── assembly_code_example1.txt
├── assembly_code_example2.txt
├── binary_code_example       # Prebuilt bytecode (optional)
└── README.md                 # This document
```

---

## 13. Implementation Notes

- **Unified memory:** No hardware separation between code and stack; collision possible if stack grows into active code region.
- **Separate RAM:** Data RAM is not mapped into main memory address space.
- **MUL operand:** Always uses `R0`; only multiplier register is encoded.
- **LOOP / LR:** `LOOP` hard-wires counter to register index 4 (`LR`).
- **JE vs JZ:** Identical branch condition; both test `ZF == 1`.
- **JG semantics:** "Greater" means unsigned greater (`CF=0` and `ZF=0` after `CMP`).
