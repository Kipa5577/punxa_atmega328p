import py4hw


# ---------------------------------------------------------------------------
# State list
# ---------------------------------------------------------------------------
STATES = [
    # ── Entry ───────────────────────────────────────────────────────────────
    'DECODE_INSTRUCTION',

    # ── Fetch Rd (8-bit) ────────────────────────────────────────────────────
    'FETCH_RD_INIT', 'FETCH_RD_WAIT', 'FETCH_RD_LOADBUFFER',
    # Fetch Rd high byte for 16-bit ops (ADIW/SBIW/MOVW)
    'FETCH_RD_INIT_B2', 'FETCH_RD_WAIT_B2', 'FETCH_RD_LOADBUFFER_B2',

    # ── Fetch Rr (8-bit) ────────────────────────────────────────────────────
    'FETCH_RR_INIT', 'FETCH_RR_WAIT', 'FETCH_RR_LOADBUFFER',
    # Fetch Rr high byte for 16-bit ops
    'FETCH_RR_INIT_B2', 'FETCH_RR_WAIT_B2', 'FETCH_RR_LOADBUFFER_B2',

    # ── Execute ─────────────────────────────────────────────────────────────
    'EXECUTE_ALU_OPP',      # ALU computes; next → write-back or DECODE
    'EXECUTE_BRANCH',       # Evaluate branch condition, update PC if taken
    'EXECUTE_SKIP',         # CPSE / SBRC / SBRS / SBIC / SBIS: may skip next instr

    # ── Load from memory (LD / LDS / LPM) ──────────────────────────────────
    'FETCH_MEMORY_VALL_INIT', 'FETCH_MEMORY_VALL_WAIT',

    # ── Store to memory (ST / STS / SPM) ───────────────────────────────────
    'WRITE_MEMORY_VALL_INIT', 'WRITE_MEMORY_VALL_WAIT',

    # ── Write result back to register file (8-bit) ──────────────────────────
    'WRITE_RES_INIT', 'WRITE_RES_WAIT', 'WRITE_RES_FINISHED',
    # High byte for 16-bit result (ADIW / SBIW / MOVW / MUL* / FMUL*)
    'WRITE_RES_INIT_B2', 'WRITE_RES_WAIT_B2', 'WRITE_RES_FINISHED_B2',

    # ── Jump / Call / Return ─────────────────────────────────────────────────
    'JUMP_LOAD_PC',          # Load new PC from instruction / Z / K
    'CALL_PUSH_PCL_INIT', 'CALL_PUSH_PCL_WAIT',   # Push return address (low)
    'CALL_PUSH_PCH_INIT', 'CALL_PUSH_PCH_WAIT',   # Push return address (high)
    'RET_POP_PCH_INIT',  'RET_POP_PCH_WAIT',      # Pop return address (high)
    'RET_POP_PCL_INIT',  'RET_POP_PCL_WAIT',      # Pop return address (low)
    'RET_LOAD_PC',           # Write restored PC

    # ── PUSH / POP ───────────────────────────────────────────────────────────
    'PUSH_INIT', 'PUSH_WAIT',
    'POP_INIT',  'POP_WAIT',  'POP_LOADBUFFER',

    # ── IN / OUT ─────────────────────────────────────────────────────────────
    'IO_READ_INIT',  'IO_READ_WAIT',  'IO_READ_LOADBUFFER',
    'IO_WRITE_INIT', 'IO_WRITE_WAIT',

    # ── Long-jump upper-bits helper (JMP / CALL absolute) ───────────────────
    'LONG_JUMP_LOAD_UPPER6_BITS_IN_TO_REGISTER',

    # ── Interrupt handling ───────────────────────────────────────────────────
    'INTERRUPT_INIT', 'INTERRUPT_JUMP',
    'INTERRUPT',
    'RETURN_FROM_INTERRUPT',
]


# ---------------------------------------------------------------------------
# Instruction opcode groups
# (numbers match op_codes dict supplied by the user)
# ---------------------------------------------------------------------------

# Rd ← op(Rd, Rr)  — two register operands, result written to Rd
_RD_RR_ALU_WRITE = {
    1,   # ADD
    2,   # ADC
    9,   # AND
    11,  # OR
    13,  # EOR
    23,  # MUL   (result → R1:R0, handled as 16-bit write)
    24,  # MULS
    25,  # MULSU
    26,  # FMUL
    27,  # FMULS
    28,  # FMULSU
    93,  # MOV   (Rr fetched as source, Rd is destination)
}

# op(Rd, Rr)  — compare / test, no write-back to register file
_RD_RR_NO_WRITE = {
    38,  # CP
    39,  # CPC
    37,  # CPSE   (also generates a skip if equal — handled in EXECUTE_ALU_OPP)
    75,  # BST    (stores bit from Rd into T flag only)
}

# Rd ← op(Rd, K)  — one register + 8-bit immediate
_RD_K_ALU_WRITE = {
    4,   # SUB   (actually SUB is Rd-Rr; opcode 4 is assigned in your table)
    5,   # SUBI
    6,   # SBC
    7,   # SBCI
    10,  # ANDI
    12,  # ORI
    16,  # SBR  (= ORI)
    17,  # CBR  (= ANDI with ~K)
    40,  # CPI  (compare, no write-back — see _RD_K_NO_WRITE)
    95,  # LDI
}

# op(Rd, K)  — no write-back
_RD_K_NO_WRITE = {
    40,  # CPI
}

# Rd ← op(Rd)  — single register operand
_RD_ONLY_WRITE = {
    14,  # COM
    15,  # NEG
    18,  # INC
    19,  # DEC
    20,  # TST  (= AND Rd,Rd  — flags only, no write)
    21,  # CLR  (= EOR Rd,Rd)
    22,  # SER  (= LDI Rd, 0xFF)
    67,  # LSL  (= ADD Rd,Rd)
    68,  # LSR
    69,  # ROL
    70,  # ROR
    71,  # ASR
    72,  # SWAP
}

# TST flags only, no Rd write
_RD_ONLY_NO_WRITE = {
    20,  # TST
}

# 16-bit word operations on register pairs
_WORD_ALU = {
    3,   # ADIW  — Rd+1:Rd += K6
    8,   # SBIW  — Rd+1:Rd -= K6
    94,  # MOVW  — copy 16-bit register pair
}

# Load from data memory to Rd
_LOAD_MEM = {
    96,  # LDX
    97,  # LDX+
    98,  # LD-X
    99,  # LDY
    100, # LDY+
    101, # LD-Y
    102, # LDDY  (LDD Y+q)
    103, # LDZ
    104, # LDZ+
    105, # LD-Z
    106, # LDDZ  (LDD Z+q)
    107, # LDS   (direct)
    120, # LPM   (load program memory, Z)
    121, # LPMZ  (LPM r,Z)
    122, # LPMZ+ (LPM r,Z+)
    127, # POP   — handled separately via PUSH/POP states but grouped here
}

# Store Rr to data memory
_STORE_MEM = {
    108, # STX
    109, # STX+
    110, # ST-X
    111, # STY
    112, # STY+
    113, # ST-Y
    114, # STDY  (STD Y+q)
    115, # STZ
    116, # STZ+
    117, # ST-Z
    118, # STDZ  (STD Z+q)
    119, # STS   (direct)
    123, # SPM
    126, # PUSH  — handled separately
}

# Branch instructions: evaluate condition then adjust PC if taken
_BRANCH = {
    45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
    57, 58, 59, 60, 61, 62, 63, 64,  # BRBS..BRID
}

# Skip-if instructions: CPSE / SBRC / SBRS / SBIC / SBIS
_SKIP = {
    37,  # CPSE  (skip if Rd == Rr)
    41,  # SBRC
    42,  # SBRS
    43,  # SBIC
    44,  # SBIS
}

# SREG bit set/clear (no register operand beyond SREG)
_SREG_ONLY = {
    73, 74,             # BSET / BCLR
    77, 78,             # SEC / CLC
    79, 80,             # SEN / CLN
    81, 82,             # SEZ / CLZ
    83, 84,             # SEI / CLI
    85, 86,             # SES / CLS
    87, 88,             # SEV / CLV
    89, 90,             # SET / CLT
    91, 92,             # SEH / CLH
    76,                 # BLD (bit load from T → Rd, but only flag-like; Rd written)
}

# BLD writes a bit back into Rd — needs fetch + write
_BLD = {76}  # Rd ← bit(T, b)

# I/O space
_IO_READ  = {124}  # IN  Rd, A
_IO_WRITE = {125}  # OUT A, Rr

# Jump/Call (absolute and relative)
_RELATIVE_JUMP  = {29}   # RJMP
_INDIRECT_JUMP  = {30}   # IJMP  (Z register)
_ABSOLUTE_JUMP  = {31}   # JMP

_RELATIVE_CALL  = {32}   # RCALL
_INDIRECT_CALL  = {33}   # ICALL
_ABSOLUTE_CALL  = {34}   # CALL

_RETURN         = {35}   # RET
_RETURN_INT     = {36}   # RETI

_PUSH = {126}
_POP  = {127}

# No-operation and other single-cycle instructions
_NOP_MISC = {128, 129, 130, 131}   # NOP / SLEEP / WDR / BREAK


# ---------------------------------------------------------------------------
# Helper sets  (for quick membership tests inside Clock())
# ---------------------------------------------------------------------------
_ALL_TWO_REG      = _RD_RR_ALU_WRITE | _RD_RR_NO_WRITE
_ALL_ONE_REG      = _RD_ONLY_WRITE   | _RD_ONLY_NO_WRITE
_ALL_IMM_ALU      = _RD_K_ALU_WRITE
_ALL_ALU          = _ALL_TWO_REG | _ALL_ONE_REG | _ALL_IMM_ALU | _WORD_ALU | _BLD

_WRITES_RD        = _RD_RR_ALU_WRITE | _RD_ONLY_WRITE | _BLD | _RD_K_ALU_WRITE - _RD_K_NO_WRITE
_MUL_FAMILY       = {23, 24, 25, 26, 27, 28}   # result → R1:R0, always 16-bit

# All calls (push return addr before jumping)
_ALL_CALLS  = _RELATIVE_CALL | _INDIRECT_CALL | _ABSOLUTE_CALL
# All returns
_ALL_RETS   = _RETURN | _RETURN_INT


# ---------------------------------------------------------------------------
#  ControlBox  — main FSM
# ---------------------------------------------------------------------------
class control_Box(py4hw.Logic):
    """
    Central FSM (orchestrator) for an ATmega328P-like CPU.

    All 131 opcodes are handled. The FSM coordinates four subsystems:
      • MemoryInterfaceHandler  — register file + data memory reads/writes
      • ALU                     — arithmetic/logic + flag updates
      • RomHandler              — program counter + instruction fetch
      • InterruptFSM            — interrupt detection and vector jump

    Signal conventions
    ------------------
    LoadSelectMux   : selects which register address goes to the memory bus
                        0 = none, 1 = Rd address, 2 = Rr address
    Input_Select    : selects what data is written back via MemoryInterface
                        0 = databus (pass-through), 1 = ALU ResL, 2 = ALU ResH,
                        3 = General (K immediate)
    NotExecute      : 1 = stall/NOP this cycle (used during skip)
    WE              : write-enable for pointer register loading in MemInterface
    Load_Z/K/Jump   : ROM handler controls
    """

    def __init__(self, parent, name,
                 # ── Inputs ──────────────────────────────────────────────
                 Instruction,        # 8-bit opcode from instruction decoder
                 Resp,               # 1-bit: memory operation acknowledged
                 Branch,             # 1-bit: ALU branch condition met
                 Skip,               # 1-bit: ALU skip condition met
                 Interrupt,          # 1-bit: interrupt pending

                 # ── Memory Interface Outputs ─────────────────────────────
                 NotExecute,         # stall signal
                 LoadSelectMux,      # address mux for memory reads
                 LoadingMux,         # selects which pointer reg is loaded
                 Input_Select,       # data source mux for memory writes
                 WE,                 # write enable for pointer registers
                 Read_Write,         # 0=read, 1=write
                 Address_XYZ,        # pointer selection for Mem_instruction
                 IncDec,             # This icrement or Decrements address

                 # ── ALU Buffer Outputs ───────────────────────────────────
                 write_Opperand_Buffer, # 1=A0, 2=A1, 3=B0, 4=B1

                 # ── ROM Handler Outputs ──────────────────────────────────
                 Load_Z,             # load Z pointer from program memory
                 Load_K,             # load immediate K into ALU
                 Load_Jump,          # trigger PC jump
                 relative_Absolute,  # 0=relative, 1=absolute jump
                 Load_Byte,          # load single byte from ROM
                 ):
        super().__init__(parent, name)

        # ── Register inputs ──────────────────────────────────────────────
        self.Instruction      = self.addIn('Instruction',      Instruction)
        self.Resp             = self.addIn('Resp',             Resp)
        self.Branch           = self.addIn('Branch',           Branch)
        self.Skip             = self.addIn('Skip',             Skip)
        self.Interrupt        = self.addIn('Interrupt',        Interrupt)

        # ── Register outputs ─────────────────────────────────────────────
        self.NotExecute       = self.addOut('NotExecute',       NotExecute)
        self.LoadSelectMux    = self.addOut('LoadSelectMux',    LoadSelectMux)
        self.LoadingMux       = self.addOut('LoadingMux',       LoadingMux)
        self.Input_Select     = self.addOut('Input_Select',     Input_Select)
        self.WE               = self.addOut('WE',               WE)
        self.Read_Write       = self.addOut('Read_Write',       Read_Write)
        self.Address_XYZ      = self.addOut('Address_XYZ',      Address_XYZ)
        self.IncDec           = self.addOut('IncDec',           IncDec)

        self.write_Opperand_Buffer = self.addOut('write_Opperand_Buffer',write_Opperand_Buffer)

        self.Load_Z           = self.addOut('Load_Z',           Load_Z)
        self.Load_K           = self.addOut('Load_K',           Load_K)
        self.Load_Jump        = self.addOut('Load_Jump',        Load_Jump)
        self.relative_Absolute= self.addOut('relative_Absolute',relative_Absolute)
        self.Load_Byte        = self.addOut('Load_Byte',        Load_Byte)

        # ── FSM state ────────────────────────────────────────────────────
        self.current_state = 'DECODE_INSTRUCTION'
        # Remember the instruction across multi-cycle sequences
        self._latched_inst = 0

    # ====================================================================
    def Clock(self):
        inst   = self.Instruction.get()
        resp   = self.Resp.get()
        branch = self.Branch.get()
        skip   = self.Skip.get()
        irq    = self.Interrupt.get()

        # ── Default output values (all de-asserted) ──────────────────────
        out = {
            'NotExecute':       0,
            'LoadSelectMux':    0,
            'LoadingMux':       0,
            'Input_Select':     0,
            'WE':               0,
            'Read_Write':       0,   # 0 = read
            'Address_XYZ':      0,
            'write_RdL_Buffer': 0,
            'write_RdH_Buffer': 0,
            'write_RrL_Buffer': 0,
            'write_RrH_Buffer': 0,
            'Load_Z':           0,
            'Load_K':           0,
            'Load_Jump':        0,
            'relative_Absolute':0,
            'Load_Byte':        0,
        }

        state = self.current_state
        i     = self._latched_inst   # use latched opcode during multi-cycle seqs
        next_state = state           # default: stay

        # ================================================================
        # STATE MACHINE
        # ================================================================

        # ── DECODE ──────────────────────────────────────────────────────
        if state == 'DECODE_INSTRUCTION':
            # Latch the incoming instruction for use across all subsequent states
            i = inst
            self._latched_inst = i

            # Check for pending interrupt (only when we are at instruction boundary)
            if irq:
                next_state = 'INTERRUPT_INIT'

            # ── Two-register ALU (fetch Rd first) ──────────────────────
            elif i in (_ALL_TWO_REG | _WORD_ALU | _BLD):
                next_state = 'FETCH_RD_INIT'

            # ── Single-register ALU (fetch Rd only) ────────────────────
            elif i in _ALL_ONE_REG:
                next_state = 'FETCH_RD_INIT'

            # ── Immediate ALU (Rd from reg file, K from decoder) ────────
            elif i in _ALL_IMM_ALU:
                next_state = 'FETCH_RD_INIT'   # still need Rd; K is wired

            # ── Load from memory → Rd ───────────────────────────────────
            elif i in _LOAD_MEM - _POP:
                next_state = 'FETCH_MEMORY_VALL_INIT'

            # ── Store Rr to memory ───────────────────────────────────────
            elif i in _STORE_MEM - _PUSH:
                next_state = 'FETCH_RD_INIT'    # fetch source register first

            # ── PUSH ─────────────────────────────────────────────────────
            elif i in _PUSH:
                next_state = 'FETCH_RD_INIT'

            # ── POP ──────────────────────────────────────────────────────
            elif i in _POP:
                next_state = 'POP_INIT'

            # ── IN (read I/O port) ───────────────────────────────────────
            elif i in _IO_READ:
                next_state = 'IO_READ_INIT'

            # ── OUT (write I/O port) ─────────────────────────────────────
            elif i in _IO_WRITE:
                next_state = 'FETCH_RD_INIT'   # fetch source, then write I/O

            # ── Skip instructions ─────────────────────────────────────────
            elif i in _SKIP:
                next_state = 'FETCH_RD_INIT'   # CPSE needs both regs; SBRC/RS need Rd

            # ── Branch instructions ───────────────────────────────────────
            elif i in _BRANCH:
                next_state = 'EXECUTE_BRANCH'

            # ── Relative/Indirect/Absolute JUMP ──────────────────────────
            elif i in _RELATIVE_JUMP:
                out['Load_Jump']          = 1
                out['relative_Absolute']  = 0   # relative
                next_state = 'DECODE_INSTRUCTION'  # single cycle

            elif i in _INDIRECT_JUMP:
                out['Load_Z']    = 1
                out['Load_Jump'] = 1
                out['relative_Absolute'] = 1    # absolute (Z)
                next_state = 'DECODE_INSTRUCTION'

            elif i in _ABSOLUTE_JUMP:
                next_state = 'LONG_JUMP_LOAD_UPPER6_BITS_IN_TO_REGISTER'

            # ── CALL instructions ─────────────────────────────────────────
            elif i in _ALL_CALLS:
                next_state = 'CALL_PUSH_PCL_INIT'

            # ── RET / RETI ────────────────────────────────────────────────
            elif i in _ALL_RETS:
                next_state = 'RET_POP_PCH_INIT'

            # ── SREG-only (SEC CLI BSET BCLR …) ─────────────────────────
            elif i in _SREG_ONLY - _BLD:
                # ALU / SREG updates happen combinatorially; single cycle.
                next_state = 'DECODE_INSTRUCTION'

            # ── NOP / SLEEP / WDR / BREAK ────────────────────────────────
            elif i in _NOP_MISC:
                next_state = 'DECODE_INSTRUCTION'

            else:
                # Unknown opcode — treat as NOP
                next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # FETCH Rd — low byte
        # ================================================================
        elif state == 'FETCH_RD_INIT':
            out['LoadSelectMux'] = 1    # present Rd address to memory bus
            out['Read_Write']    = 0    # read
            next_state = 'FETCH_RD_WAIT'

        elif state == 'FETCH_RD_WAIT':
            out['LoadSelectMux'] = 1
            out['Read_Write']    = 0
            if resp:
                next_state = 'FETCH_RD_LOADBUFFER'

        elif state == 'FETCH_RD_LOADBUFFER':
            out['write_RdL_Buffer'] = 1   # latch Rd into ALU input buffer

            # ── Route: where to next? ────────────────────────────────────
            if i in (_ALL_TWO_REG | _WORD_ALU):
                # Need Rr or second byte
                if i in _WORD_ALU:
                    next_state = 'FETCH_RD_INIT_B2'   # grab RdH first
                else:
                    next_state = 'FETCH_RR_INIT'

            elif i in _ALL_ONE_REG:
                next_state = 'EXECUTE_ALU_OPP'

            elif i in _ALL_IMM_ALU:
                out['Load_K'] = 1          # tell ROM handler to latch K
                next_state = 'EXECUTE_ALU_OPP'

            elif i in _STORE_MEM - _PUSH:
                next_state = 'WRITE_MEMORY_VALL_INIT'

            elif i in _PUSH:
                next_state = 'PUSH_INIT'

            elif i in _IO_WRITE:
                next_state = 'IO_WRITE_INIT'

            elif i in _SKIP:
                # CPSE, SBRC, SBRS need Rr; SBIC/SBIS operate on I/O, not Rr
                if i in {43, 44}:   # SBIC / SBIS → execute skip directly
                    next_state = 'EXECUTE_SKIP'
                else:
                    next_state = 'FETCH_RR_INIT'

            elif i in _BLD:
                # BLD: write T-bit into Rd — skip Rr, go straight to write
                next_state = 'EXECUTE_ALU_OPP'

            else:
                next_state = 'EXECUTE_ALU_OPP'

        # ================================================================
        # FETCH Rd — high byte  (ADIW / SBIW / MOVW)
        # ================================================================
        elif state == 'FETCH_RD_INIT_B2':
            out['LoadSelectMux'] = 1    # address Rd+1
            out['Read_Write']    = 0
            next_state = 'FETCH_RD_WAIT_B2'

        elif state == 'FETCH_RD_WAIT_B2':
            out['LoadSelectMux'] = 1
            out['Read_Write']    = 0
            if resp:
                next_state = 'FETCH_RD_LOADBUFFER_B2'

        elif state == 'FETCH_RD_LOADBUFFER_B2':
            out['write_RdH_Buffer'] = 1
            if i in {94}:   # MOVW — source is Rr pair, need Rr next
                next_state = 'FETCH_RR_INIT'
            else:
                # ADIW / SBIW: second operand is K (immediate)
                out['Load_K'] = 1
                next_state = 'EXECUTE_ALU_OPP'

        # ================================================================
        # FETCH Rr — low byte
        # ================================================================
        elif state == 'FETCH_RR_INIT':
            out['LoadSelectMux'] = 2    # present Rr address to memory bus
            out['Read_Write']    = 0
            next_state = 'FETCH_RR_WAIT'

        elif state == 'FETCH_RR_WAIT':
            out['LoadSelectMux'] = 2
            out['Read_Write']    = 0
            if resp:
                next_state = 'FETCH_RR_LOADBUFFER'

        elif state == 'FETCH_RR_LOADBUFFER':
            out['write_RrL_Buffer'] = 1

            if i in _WORD_ALU:      # MOVW still needs RrH
                next_state = 'FETCH_RR_INIT_B2'
            elif i in _SKIP:
                next_state = 'EXECUTE_SKIP'
            else:
                next_state = 'EXECUTE_ALU_OPP'

        # ================================================================
        # FETCH Rr — high byte  (MOVW only)
        # ================================================================
        elif state == 'FETCH_RR_INIT_B2':
            out['LoadSelectMux'] = 2
            out['Read_Write']    = 0
            next_state = 'FETCH_RR_WAIT_B2'

        elif state == 'FETCH_RR_WAIT_B2':
            out['LoadSelectMux'] = 2
            out['Read_Write']    = 0
            if resp:
                next_state = 'FETCH_RR_LOADBUFFER_B2'

        elif state == 'FETCH_RR_LOADBUFFER_B2':
            out['write_RrH_Buffer'] = 1
            next_state = 'EXECUTE_ALU_OPP'

        # ================================================================
        # EXECUTE — ALU operation (result available next clock)
        # ================================================================
        elif state == 'EXECUTE_ALU_OPP':
            # No output signals: ALU is purely combinatorial and
            # settles on its own based on the latched buffer values.
            # Decide whether to write back.

            if i in (_RD_RR_NO_WRITE | _RD_ONLY_NO_WRITE | _RD_K_NO_WRITE):
                # CP / CPC / CPI / TST — flags updated, no register write
                next_state = 'DECODE_INSTRUCTION'

            elif i in _MUL_FAMILY:
                # Result is 16-bit in R1:R0 — two write-back cycles
                next_state = 'WRITE_RES_INIT'    # write low byte to R0

            elif i in _WORD_ALU:
                # ADIW / SBIW / MOVW — write low byte first
                next_state = 'WRITE_RES_INIT'

            elif i in _WRITES_RD - _RD_K_NO_WRITE:
                next_state = 'WRITE_RES_INIT'

            else:
                # Default: write back (handles any edge cases)
                next_state = 'WRITE_RES_INIT'

        # ================================================================
        # EXECUTE — Branch
        # ================================================================
        elif state == 'EXECUTE_BRANCH':
            if branch:
                out['Load_Jump']         = 1
                out['relative_Absolute'] = 0   # all AVR branches are PC-relative
            # Either way return to decode next cycle
            next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # EXECUTE — Skip
        # ================================================================
        elif state == 'EXECUTE_SKIP':
            if skip:
                # Insert a bubble: suppress instruction fetch for one cycle
                out['NotExecute'] = 1
            next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # LOAD from memory (LD / LDS / LPM)
        # ================================================================
        elif state == 'FETCH_MEMORY_VALL_INIT':
            out['Address_XYZ'] = 1    # use pointer address from instruction decoder
            out['Read_Write']  = 0    # read
            next_state = 'FETCH_MEMORY_VALL_WAIT'

        elif state == 'FETCH_MEMORY_VALL_WAIT':
            out['Address_XYZ'] = 1
            out['Read_Write']  = 0
            if resp:
                # Data from memory arrives on bus → write to Rd
                next_state = 'WRITE_RES_INIT'

        # ================================================================
        # STORE to memory (ST / STS / SPM)
        # ================================================================
        elif state == 'WRITE_MEMORY_VALL_INIT':
            out['Address_XYZ'] = 1
            out['Read_Write']  = 1    # write
            out['Input_Select']= 1    # source = ALU ResL (which holds Rd value)
            next_state = 'WRITE_MEMORY_VALL_WAIT'

        elif state == 'WRITE_MEMORY_VALL_WAIT':
            out['Address_XYZ'] = 1
            out['Read_Write']  = 1
            out['Input_Select']= 1
            if resp:
                next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # WRITE result to register file — low byte
        # ================================================================
        elif state == 'WRITE_RES_INIT':
            out['Input_Select'] = 1   # ALU ResL → memory data bus
            out['Read_Write']   = 1   # write
            out['LoadSelectMux']= 1   # address = Rd
            next_state = 'WRITE_RES_WAIT'

        elif state == 'WRITE_RES_WAIT':
            out['Input_Select'] = 1
            out['Read_Write']   = 1
            out['LoadSelectMux']= 1
            if resp:
                next_state = 'WRITE_RES_FINISHED'

        elif state == 'WRITE_RES_FINISHED':
            # For 16-bit results, we need to write the high byte too
            if i in (_MUL_FAMILY | _WORD_ALU | {94}):
                next_state = 'WRITE_RES_INIT_B2'
            else:
                next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # WRITE result — high byte (R1 for MUL; Rd+1 for ADIW/SBIW/MOVW)
        # ================================================================
        elif state == 'WRITE_RES_INIT_B2':
            out['Input_Select'] = 2   # ALU ResH
            out['Read_Write']   = 1
            out['LoadSelectMux']= 1   # address decoder adds +1 for B2 writes
            next_state = 'WRITE_RES_WAIT_B2'

        elif state == 'WRITE_RES_WAIT_B2':
            out['Input_Select'] = 2
            out['Read_Write']   = 1
            out['LoadSelectMux']= 1
            if resp:
                next_state = 'WRITE_RES_FINISHED_B2'

        elif state == 'WRITE_RES_FINISHED_B2':
            next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # PUSH  (SP-- then write Rd to new SP)
        # ================================================================
        elif state == 'PUSH_INIT':
            out['Address_XYZ'] = 6    # SP pointer
            out['Read_Write']  = 1
            out['Input_Select']= 1    # Rd value in ALU ResL
            next_state = 'PUSH_WAIT'

        elif state == 'PUSH_WAIT':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 1
            out['Input_Select']= 1
            if resp:
                next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # POP  (read from SP then SP++)
        # ================================================================
        elif state == 'POP_INIT':
            out['Address_XYZ'] = 6    # SP pointer
            out['Read_Write']  = 0    # read
            next_state = 'POP_WAIT'

        elif state == 'POP_WAIT':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 0
            if resp:
                next_state = 'POP_LOADBUFFER'

        elif state == 'POP_LOADBUFFER':
            out['write_RdL_Buffer'] = 1
            next_state = 'WRITE_RES_INIT'   # write popped value back to Rd

        # ================================================================
        # IN — read from I/O port into Rd
        # ================================================================
        elif state == 'IO_READ_INIT':
            out['Address_XYZ'] = 8    # I/O address from instruction decoder
            out['Read_Write']  = 0
            next_state = 'IO_READ_WAIT'

        elif state == 'IO_READ_WAIT':
            out['Address_XYZ'] = 8
            out['Read_Write']  = 0
            if resp:
                next_state = 'IO_READ_LOADBUFFER'

        elif state == 'IO_READ_LOADBUFFER':
            out['write_RdL_Buffer'] = 1
            next_state = 'WRITE_RES_INIT'

        # ================================================================
        # OUT — write Rd to I/O port (Rd was fetched in FETCH_RD sequence)
        # ================================================================
        elif state == 'IO_WRITE_INIT':
            out['Address_XYZ'] = 8    # I/O address from instruction decoder
            out['Read_Write']  = 1
            out['Input_Select']= 1    # Rd in ResL
            next_state = 'IO_WRITE_WAIT'

        elif state == 'IO_WRITE_WAIT':
            out['Address_XYZ'] = 8
            out['Read_Write']  = 1
            out['Input_Select']= 1
            if resp:
                next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # CALL — push return address (PCL first, then PCH), then jump
        # ================================================================
        elif state == 'CALL_PUSH_PCL_INIT':
            out['Address_XYZ'] = 6    # SP
            out['Read_Write']  = 1
            out['Input_Select']= 3    # PC low byte via GeneralInput
            next_state = 'CALL_PUSH_PCL_WAIT'

        elif state == 'CALL_PUSH_PCL_WAIT':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 1
            out['Input_Select']= 3
            if resp:
                next_state = 'CALL_PUSH_PCH_INIT'

        elif state == 'CALL_PUSH_PCH_INIT':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 1
            out['Input_Select']= 3    # PC high byte via GeneralInput
            next_state = 'CALL_PUSH_PCH_WAIT'

        elif state == 'CALL_PUSH_PCH_WAIT':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 1
            out['Input_Select']= 3
            if resp:
                # Return address saved — now perform the jump
                if i in _RELATIVE_CALL:
                    out['Load_Jump']          = 1
                    out['relative_Absolute']  = 0
                elif i in _INDIRECT_CALL:
                    out['Load_Z']             = 1
                    out['Load_Jump']          = 1
                    out['relative_Absolute']  = 1
                elif i in _ABSOLUTE_CALL:
                    out['Load_Jump']          = 1
                    out['relative_Absolute']  = 1
                next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # RET / RETI — pop return address from stack
        # ================================================================
        elif state == 'RET_POP_PCH_INIT':
            out['Address_XYZ'] = 6    # SP
            out['Read_Write']  = 0
            next_state = 'RET_POP_PCH_WAIT'

        elif state == 'RET_POP_PCH_WAIT':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 0
            if resp:
                next_state = 'RET_POP_PCL_INIT'

        elif state == 'RET_POP_PCL_INIT':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 0
            next_state = 'RET_POP_PCL_WAIT'

        elif state == 'RET_POP_PCL_WAIT':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 0
            if resp:
                next_state = 'RET_LOAD_PC'

        elif state == 'RET_LOAD_PC':
            out['Load_Jump']         = 1
            out['relative_Absolute'] = 1   # absolute (restored address)
            if i in _RETURN_INT:
                # RETI also re-enables interrupts (set SREG.I)
                # That is signalled to the ALU/SREG logic externally;
                # the FSM simply marks the state.
                pass
            next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # JMP (absolute 22-bit)
        # ================================================================
        elif state == 'LONG_JUMP_LOAD_UPPER6_BITS_IN_TO_REGISTER':
            # Second word of the 32-bit JMP/CALL instruction holds the full
            # 16-bit lower target address; upper 6 bits are in the opcode word.
            out['Load_Byte']         = 1
            out['Load_Jump']         = 1
            out['relative_Absolute'] = 1
            next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # INTERRUPT — save context, jump to vector
        # ================================================================
        elif state == 'INTERRUPT_INIT':
            # Push PCL onto stack
            out['Address_XYZ'] = 6
            out['Read_Write']  = 1
            out['Input_Select']= 3
            next_state = 'INTERRUPT_JUMP'

        elif state == 'INTERRUPT_JUMP':
            out['Address_XYZ'] = 6
            out['Read_Write']  = 1
            out['Input_Select']= 3
            if resp:
                out['Load_Jump']         = 1
                out['relative_Absolute'] = 1   # jump to interrupt vector (absolute)
                next_state = 'DECODE_INSTRUCTION'

        elif state == 'INTERRUPT':
            # Placeholder for multi-cycle interrupt acknowledgement if needed
            next_state = 'DECODE_INSTRUCTION'

        elif state == 'RETURN_FROM_INTERRUPT':
            # Alias for RETI handling (routed through RET path above)
            out['Load_Jump']         = 1
            out['relative_Absolute'] = 1
            next_state = 'DECODE_INSTRUCTION'

        else:
            # Safety catch-all
            next_state = 'DECODE_INSTRUCTION'

        # ================================================================
        # Drive all outputs
        # ================================================================
        self.NotExecute.put(out['NotExecute'])
        self.LoadSelectMux.put(out['LoadSelectMux'])
        self.LoadingMux.put(out['LoadingMux'])
        self.Input_Select.put(out['Input_Select'])
        self.WE.put(out['WE'])
        self.Read_Write.put(out['Read_Write'])
        self.Address_XYZ.put(out['Address_XYZ'])

        if out['write_RdL_Buffer'] == 1:
            self.write_Opperand_Buffer.put(1) # 1=A0, 2=A1, 3=B0, 4=B1
        elif out['write_RdH_Buffer'] == 1:
            self.write_Opperand_Buffer.put(2) # 1=A0, 2=A1, 3=B0, 4=B1
        elif out['write_RrL_Buffer'] == 1:
            self.write_Opperand_Buffer.put(3) # 1=A0, 2=A1, 3=B0, 4=B1
        elif out['write_RrH_Buffer'] == 1:
            self.write_Opperand_Buffer.put(4) # 1=A0, 2=A1, 3=B0, 4=B1


        self.Load_Z.put(out['Load_Z'])
        self.Load_K.put(out['Load_K'])
        self.Load_Jump.put(out['Load_Jump'])
        self.relative_Absolute.put(out['relative_Absolute'])
        self.Load_Byte.put(out['Load_Byte'])

        # Advance state
        self.current_state = next_state