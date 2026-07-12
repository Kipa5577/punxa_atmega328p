"""
avr_constants.py
================
Pure data: no FSM logic lives here. Two kinds of things are defined:

  1. MEM_* — the address-source codes that MemoryInterfaceHandler expects
     on its Address_XYZ input (which pointer/register feeds the address bus).

  2. Opcode group sets — every AVR opcode number bucketed by "what shape
     of instruction is this" (e.g. "two register operands, write result
     back" vs "one register operand, no write back"). The FSM (in
     control_box.py) only ever asks "is this opcode in group X?" — it
     never hard-codes a raw opcode number itself. That's the whole point
     of splitting this out: when you want to know what CPSE does, you
     look it up by name here, instead of grepping for the number 37
     through six hundred lines of state logic.

If you ever add a new opcode, this is the ONLY file you should need to
touch (assuming its execution shape already matches one of the existing
groups).
"""

# ---------------------------------------------------------------------------
# Address_XYZ values (must match MemoryInterfaceHandler.Mem_instruction)
# ---------------------------------------------------------------------------
MEM_X        = 1   # X pointer
MEM_X_PLUS   = 2   # X pointer (post-increment variant flag)
MEM_Y        = 3   # Y pointer
MEM_Y_PLUS   = 4
MEM_Z        = 5   # Z pointer
MEM_Z_PLUS   = 6
MEM_SP       = 7   # Stack pointer
MEM_SP_PLUS  = 8
MEM_RAM_ADDR = 9   # Direct address from RomAddress input
MEM_Y_Q      = 10  # Y + q displacement  (LDD/STD Y+q)
MEM_Z_Q      = 11  # Z + q displacement  (LDD/STD Z+q)
MEM_RD       = 12  # Register file: address == Rd (0-31 in SRAM)
MEM_RR       = 13  # Register file: address == Rr (0-31 in SRAM)
MEM_WB_ADDR  = 14  # Register file: address comes from the WB_Addr port
                    # (used for Rd+1, R0, R1, etc. — anything that isn't
                    # plain Rd/Rr)


# ---------------------------------------------------------------------------
# Rd <- op(Rd, Rr)  — two register operands, result written back to Rd
# ---------------------------------------------------------------------------
RD_RR_ALU_WRITE = {
    1,   # ADD
    2,   # ADC
    9,   # AND
    11,  # OR
    13,  # EOR
    23,  # MUL    (result -> R1:R0, handled as 16-bit write)
    24,  # MULS
    25,  # MULSU
    26,  # FMUL
    27,  # FMULS
    28,  # FMULSU
    93,  # MOV    (Rr fetched as source, Rd is destination)
}

# op(Rd, Rr)  — compare / test only, no write-back to the register file
RD_RR_NO_WRITE = {
    38,  # CP
    39,  # CPC
    37,  # CPSE  (also generates a skip if equal — see EXECUTE_ALU_OPP)
    75,  # BST   (stores a bit from Rd into the T flag only)
}

# ---------------------------------------------------------------------------
# Rd <- op(Rd, K)  — one register + 8-bit immediate
# ---------------------------------------------------------------------------
RD_K_ALU_WRITE = {
    4,   # SUB    (SUB is Rd-Rr; opcode 4 is assigned this way in this table)
    5,   # SUBI
    6,   # SBC
    7,   # SBCI
    10,  # ANDI
    12,  # ORI
    16,  # SBR   (= ORI)
    17,  # CBR   (= ANDI with ~K)
    40,  # CPI   (compare, no write-back — also listed in RD_K_NO_WRITE)
    95,  # LDI
}

# op(Rd, K)  — no write-back
RD_K_NO_WRITE = {
    40,  # CPI
}

# ---------------------------------------------------------------------------
# Rd <- op(Rd)  — single register operand
# ---------------------------------------------------------------------------
RD_ONLY_WRITE = {
    14,  # COM
    15,  # NEG
    18,  # INC
    19,  # DEC
    20,  # TST   (= AND Rd,Rd  — flags only, no write)
    21,  # CLR   (= EOR Rd,Rd)
    22,  # SER   (= LDI Rd, 0xFF)
    67,  # LSL   (= ADD Rd,Rd)
    68,  # LSR
    69,  # ROL
    70,  # ROR
    71,  # ASR
    72,  # SWAP
}

# TST: flags only, no Rd write
RD_ONLY_NO_WRITE = {
    20,  # TST
}

# ---------------------------------------------------------------------------
# 16-bit word ALU ops on register pairs (MOVW is NOT here — it's a pure
# copy with its own dedicated state path; see MOVW below)
# ---------------------------------------------------------------------------
WORD_ALU = {
    3,   # ADIW — Rd+1:Rd += K6
    8,   # SBIW — Rd+1:Rd -= K6
}

# MOVW — pure register-pair copy, handled entirely outside the ALU
MOVW = {94}

# ---------------------------------------------------------------------------
# Load from data memory into Rd
# ---------------------------------------------------------------------------
LOAD_MEM = {
    96,  # LDX
    97,  # LDX+
    98,  # LD-X
    99,  # LDY
    100, # LDY+
    101, # LD-Y
    102, # LDDY   (LDD Y+q)
    103, # LDZ
    104, # LDZ+
    105, # LD-Z
    106, # LDDZ   (LDD Z+q)
    107, # LDS    (direct)
    120, # LPM    (load program memory, Z)
    121, # LPMZ   (LPM r,Z)
    122, # LPMZ+  (LPM r,Z+)
    127, # POP    — handled via its own PUSH/POP states, but grouped here too
}

# ---------------------------------------------------------------------------
# Store Rr to data memory
# ---------------------------------------------------------------------------
STORE_MEM = {
    108, # STX
    109, # STX+
    110, # ST-X
    111, # STY
    112, # STY+
    113, # ST-Y
    114, # STDY   (STD Y+q)
    115, # STZ
    116, # STZ+
    117, # ST-Z
    118, # STDZ   (STD Z+q)
    119, # STS    (direct)
    123, # SPM
    126, # PUSH   — handled via its own PUSH/POP states, but grouped here too
}

# STS is the only STORE_MEM member whose address comes from the *next
# instruction word* rather than from an X/Y/Z pointer register.
STORE_DIRECT = {119}  # STS

# opcode -> Address_XYZ pointer code, for the X/Y/Z-pointer store variants
STORE_ADDR_XYZ = {
    108: MEM_X,      109: MEM_X_PLUS, 110: MEM_X_PLUS,  # ST X, ST X+, ST -X
    111: MEM_Y,      112: MEM_Y_PLUS, 113: MEM_Y_PLUS,  # ST Y, ST Y+, ST -Y
    114: MEM_Y_Q,                                       # STD Y+q
    115: MEM_Z,      116: MEM_Z_PLUS, 117: MEM_Z_PLUS,  # ST Z, ST Z+, ST -Z
    118: MEM_Z_Q,                                       # STD Z+q
    123: MEM_Z,                                         # SPM (via Z)
}

# ---------------------------------------------------------------------------
# Branches: evaluate condition, then adjust PC if taken
# ---------------------------------------------------------------------------
BRANCH = {
    45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
    57, 58, 59, 60, 61, 62, 63, 64,  # BRBS..BRID
}

# Skip-if instructions: CPSE / SBRC / SBRS / SBIC / SBIS
SKIP = {
    37,  # CPSE  (skip if Rd == Rr)
    41,  # SBRC
    42,  # SBRS
    43,  # SBIC
    44,  # SBIS
}

# Of the SKIP group, these two test an I/O bit directly and never need Rr.
SKIP_NO_RR = {43, 44}  # SBIC, SBIS

# ---------------------------------------------------------------------------
# SREG bit set/clear (no register operand beyond SREG itself)
# ---------------------------------------------------------------------------
SREG_ONLY = {
    73, 74,  # BSET / BCLR
    77, 78,  # SEC  / CLC
    79, 80,  # SEN  / CLN
    81, 82,  # SEZ  / CLZ
    83, 84,  # SEI  / CLI
    85, 86,  # SES  / CLS
    87, 88,  # SEV  / CLV
    89, 90,  # SET  / CLT
    91, 92,  # SEH  / CLH
    76,      # BLD (bit load from T -> Rd — Rd IS written, see BLD below)
}

# BLD writes a bit back into Rd, so it needs the fetch+write sequence even
# though it's grouped with the SREG instructions above.
BLD = {76}

# ---------------------------------------------------------------------------
# I/O space
# ---------------------------------------------------------------------------
IO_READ  = {124}  # IN  Rd, A
IO_WRITE = {125}  # OUT A, Rr

# ---------------------------------------------------------------------------
# Jump / Call / Return
# ---------------------------------------------------------------------------
RELATIVE_JUMP = {29}   # RJMP
INDIRECT_JUMP = {30}   # IJMP (via Z register)
ABSOLUTE_JUMP = {31}   # JMP

RELATIVE_CALL = {32}   # RCALL
INDIRECT_CALL = {33}   # ICALL
ABSOLUTE_CALL = {34}   # CALL

RETURN     = {35}   # RET
RETURN_INT = {36}   # RETI

PUSH = {126}
POP  = {127}

# No-operation and other single-cycle instructions
NOP_MISC = {128, 129, 130, 131}   # NOP / SLEEP / WDR / BREAK


# ---------------------------------------------------------------------------
# Composite groups — built from the primitives above so the FSM can ask
# one clean question ("is this a two-register ALU op?") instead of
# repeating unions everywhere.
# ---------------------------------------------------------------------------
ALL_TWO_REG = RD_RR_ALU_WRITE | RD_RR_NO_WRITE
ALL_ONE_REG = RD_ONLY_WRITE | RD_ONLY_NO_WRITE
ALL_IMM_ALU = RD_K_ALU_WRITE
ALL_ALU     = ALL_TWO_REG | ALL_ONE_REG | ALL_IMM_ALU | WORD_ALU | BLD

WRITES_RD = RD_RR_ALU_WRITE | RD_ONLY_WRITE | BLD | (RD_K_ALU_WRITE - RD_K_NO_WRITE)

# Every MUL-family opcode always produces a 16-bit result in R1:R0,
# regardless of the fact that its operands are two 8-bit registers.
MUL_FAMILY = {23, 24, 25, 26, 27, 28}

ALL_CALLS = RELATIVE_CALL | INDIRECT_CALL | ABSOLUTE_CALL
ALL_RETS  = RETURN | RETURN_INT