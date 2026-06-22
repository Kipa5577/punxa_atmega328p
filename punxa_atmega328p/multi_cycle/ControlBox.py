import py4hw


# ---------------------------------------------------------------------------
# Address_XYZ values (must match MemoryInterfaceHandler.Mem_instruction)
# ---------------------------------------------------------------------------
MEM_X          = 1   # X pointer
MEM_X_PLUS     = 2   # X pointer (post-increment variant flag)
MEM_Y          = 3   # Y pointer
MEM_Y_PLUS     = 4
MEM_Z          = 5   # Z pointer
MEM_Z_PLUS     = 6
MEM_SP         = 7   # Stack pointer
MEM_SP_PLUS    = 8
MEM_RAM_ADDR   = 9   # Direct address from RomAddress input
MEM_Y_Q        = 10  # Y + q displacement  (LDD/STD Y+q)
MEM_Z_Q        = 11  # Z + q displacement  (LDD/STD Z+q)
MEM_RD         = 12  # Register file: address == Rd (0-31 in SRAM)
MEM_RR         = 13  # Register file: address == Rr (0-31 in SRAM)
MEM_WB_ADDR    = 14  # Register file: address comes from the WB_Addr port (for Rd+1, R0, R1 etc.)


# ---------------------------------------------------------------------------
# State list
# ---------------------------------------------------------------------------
STATES = [
    # ── Entry ───────────────────────────────────────────────────────────────

    'FETCH_INSTRUION', # Tells the RomHandler to Fetch the next instruction
    'DECODE_INSTRUCTION', # Waits for the Instruction decoder to send a decoded instruction signa
    'EXECUTE_INSTRUCTION' # The control box is deciding what to do with the new instruction code it recived 
    'FINISED_INSTRUCTION_EXECUTION' # This tells the RomLoader to fetch a new instruction and sends a signal to the instruction decoder that the current instruction has finished exeution so it should wait for a new one and tell the control box wen it has recived it.

    # ── Fetch Rd (8-bit) ────────────────────────────────────────────────────
    'FETCH_RD_INIT', # Tells the MemoryInterface handler to load to the bus the rd address and that it is a read operation
    'FETCH_RD_WAIT', # Waits for the Memory interface to rend back the resp signal
    'FETCH_RD_LOADBUFFER', # Writes the value of the RD register in the value buffer before the ALU
    # Fetch Rd high byte for 16-bit ops (ADIW/SBIW/MOVW)
    'FETCH_RD_INIT_B2', # Tells the MemoryInterface handler to load to the bus the rd address and that it is a read operation
    'FETCH_RD_WAIT_B2', # Waits for the Memory interface to rend back the resp signal
    'FETCH_RD_LOADBUFFER_B2', # Writes the value of the RD register in the value buffer before the ALU
    # ── Fetch Rr (8-bit) ────────────────────────────────────────────────────
    'FETCH_RR_INIT',# Tells the MemoryInterface handler to load to the bus the rd address and that it is a read operation
    'FETCH_RR_WAIT',# Waits for the Memory interface to rend back the resp signal
    'FETCH_RR_LOADBUFFER',# Writes the value of the RE register in the value buffer before the ALU
    # Fetch Rr high byte for 16-bit ops
    'FETCH_RR_INIT_B2',# Tells the MemoryInterface handler to load to the bus the rd address and that it is a read operation
    'FETCH_RR_WAIT_B2',# Waits for the Memory interface to rend back the resp signal
    'FETCH_RR_LOADBUFFER_B2', # Writes the value of the RD register in the value buffer before the ALU

    # ── Execute ─────────────────────────────────────────────────────────────
    'EXECUTE_ALU_OPP',      # ALU computes; next → write-back or DECODE
    'EXECUTE_BRANCH',       # Evaluate branch condition, update PC if taken
    'EXECUTE_SKIP',         # CPSE / SBRC / SBRS / SBIC / SBIS: may skip next instr
    
    'SKIP'

    # ── Load from memory (LD / LDS / LPM) ──────────────────────────────────
    'FETCH_MEMORY_VALL_INIT', 'FETCH_MEMORY_VALL_WAIT', #Before loading from memory the control box shoudl store the values (based ont the instruction) : 
    # R26:R27 intor the X register of the MemoryHandlerInterface
    # R28:R29 intor the Y register of the MemoryHandlerInterface
    # R30:R31 intor the Z register of the MemoryHandlerInterface

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
    'POP_INIT',  'POP_WAIT',  
    # 'POP_LOADBUFFER', There is no need for a load buffer fecause after a pop the controlbox is going to directly load the value to a register in memory

    # ── IN / OUT ─────────────────────────────────────────────────────────────
    'IO_READ_INIT',  'IO_READ_WAIT',  'IO_READ_LOADBUFFER',
    'IO_WRITE_INIT', 'IO_WRITE_WAIT',

    # ── Long-jump upper-bits helper (JMP / CALL absolute) ───────────────────
    'LONG_JUMP_LOAD_UPPER6_BITS_IN_TO_REGISTER',

    # ── Interrupt handling ───────────────────────────────────────────────────
    'INTERRUPT_INIT', 'INTERRUPT_JUMP',
    #'INTERRUPT',# this in terrupt state  is not neaded as we have jumped to the interup and we are going to return once the reti instruction is called 
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
# Helper sets  (for quick membership tests inside clock())
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
    All 131 opcodes are handled. The FSM coordinates four subsystems:
      • MemoryInterfaceHandler  — register file + data memory reads/writes
      • ALU                     — arithmetic/logic + flag updates
      • RomHandler              — program counter + instruction fetch + jump handeling

    Signal conventions
    ------------------
    LoadingMux   : selects which register address is written to 
                        0 = none, 1 = LOAD_XL , 2 = LOAD_XH , 3 = LOAD_YL , 4 = LOAD_YH , 5 = LOAD_ZL , 6 = LOAD_ZH , 7 = LOAD_SPL, 8 = LOAD_SPH
  
    Input_Select    : selects what data is written back via MemoryInterface
                        0 = none, 1 = databus, 2 = ALU_ResL, 3 = ALU_ResH,4 = General (K immediate)

    NotExecute      : 1 = stall/NOP this cycle (used during skip)
    WE              : write-enable for pointer register loading in MemInterface

    Increment/Decrement Control : Select wether to decrement/increment the values stored in registers X/Y/Z/SP or NOT
                    0 = INC_NONE, 1 = INC_POST_INC , 2 = INC_PRE_DEC,
    
    LoadSelectMux : Selects the imput for the loadingMux
                    0 = NONE, 1 = LOAD_BUS_DATA, 2 = LOAD_XL_MINUS, 3 = LOAD_XH_MINUS, 4 = LOAD_XL_PLUS, 5 = LOAD_XH_PLUS, 6 = LOAD_YL_MINUS, 7 = LOAD_YH_MINUS, 8 = LOAD_YL_PLUS, 9 = LOAD_YH_PLUS, 10 = LOAD_ZL_MINUS, 11 =  LOAD_ZH_MINUS, 12 = LOAD_ZL_PLUS, 13 = LOAD_ZH_PLUS

    Mem_instruction: Selects the address source (X/Y/Z/SP) to put on the address bus
                    0 = none, 1 = MEM_X , 2 = MEM_X_PLUS, 3 = MEM_Y , 4 = MEM_Y_PLUS, 5 = MEM_Z, 6 = MEM_Z_PLUS, 7 = MEM_SP, 8 = MEM_SP_PLUS, 9 = MEM_RAM_ADDR_REG 


    
    Load_Z/K/Jump   : ROM handler controls
    """

    def __init__(self, parent, name,
                 # ── Inputs ──────────────────────────────────────────────
                 Instruction,        # 8-bit opcode from instruction decoder
                 Resp,               # 1-bit: memory operation Finished 
                 Branch,             # 1-bit: ALU branch condition met
                 Skip,               # 1-bit: ALU skip condition met
                 Interrupt,          # 1-bit: interrupt pending
                 Instruction_fetched, # 1-bit This signal is sent by the romHandler to tell the controll box that it has fetched the next instruction and has sent it to the instruction decoder
                 Instruction_decoded, # 1-bit This signak is sent by the Instruction_decoder to thell the controll box that the instruction decoder has updated ist outputs based on the new instruction 
                 Executed_Jump, # This tell the controll box that the romHandler has successfully executed the jump instrution and it is ready to load the next instruction

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
                 write_Opperand_Buffer, # 1=A0, 2=A1, 3=B0, 4=B1, 5=IOBuffer 
                 InputSelect, # 1 = Load Data in to Rr0 , 0 = Load K in to Rr0
                 Write_Enable, # 1 = Rd0, 2 = Rd1, 3 = Rr0, 4 = Rr1, 5 = IOBuffer 

                 # ── ROM Handler Outputs ──────────────────────────────────
                 Load_Z,             # load Z pointer from program memory
                 Load_K,             # load immediate K to rom loader for relative or absolute jump
                 Load_Jump,          # trigger PC jump
                 relative_Absolute,  # 0=relative, 1=absolute jump
                 Load_Byte,          # 0 = fetches form rom  1 = writes to rom 
                 Fetch_next_instruction, # If set to 1 fetches the next instruction it has to be set back to 0 and then to one for the next instruction to be fetched
                 # Fethc_next_instruction is also used to rest the outputs of the instruction decoder and to tell it to expect a new instruction
                 # The instruction decoder also recives the instruction_fetched signal form the romHandler to tell it that it has a new instrucion in its entrance.



                 # ── Write-back address ───────────────────────────────────
                 WB_Addr,            # 5-bit explicit write-back address (for Rd+1, R0, R1 in MUL, etc.)
                 ):
        super().__init__(parent, name)

        # ── Register inputs ──────────────────────────────────────────────
        self.Instruction           = self.addIn('Instruction',           Instruction)
        self.Resp                  = self.addIn('Resp',                  Resp)
        self.Branch                = self.addIn('Branch',                Branch)
        self.Skip                  = self.addIn('Skip',                  Skip)
        self.Interrupt             = self.addIn('Interrupt',             Interrupt)
        self.Instruction_fetched   = self.addIn('Instruction_fetched',   Instruction_fetched)
        self.Instruction_decoded   = self.addIn('Instruction_decoded',   Instruction_decoded)
        self.Executed_Jump         = self.addIn('Executed_Jump',         Executed_Jump)

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
        self.InputSelect =  self.addOut('InputSelect', InputSelect)
        self.Write_Enable = self.addOut('Write_Enable',Write_Enable)

        self.Load_Z           = self.addOut('Load_Z',           Load_Z)
        self.Load_K           = self.addOut('Load_K',           Load_K)
        self.Load_Jump        = self.addOut('Load_Jump',        Load_Jump)
        self.relative_Absolute= self.addOut('relative_Absolute',relative_Absolute)
        self.Load_Byte        = self.addOut('Load_Byte',        Load_Byte)
        self.Fetch_next_instruction           = self.addOut('Fetch_next_instruction',           Fetch_next_instruction)
        self.WB_Addr          = self.addOut('WB_Addr',          WB_Addr)

        # ── FSM state ────────────────────────────────────────────────────
        self.current_state = 'DECODE_INSTRUCTION'
        # Remember the instruction across multi-cycle sequences
        self._latched_inst = 0
        # Explicit write-back address used when Address_XYZ == MEM_WB_ADDR
        self._wb_addr_val = 0

    # ====================================================================
    def clock(self):
        inst              = self.Instruction.get()
        resp              = self.Resp.get()
        branch            = self.Branch.get()
        skip              = self.Skip.get()
        irq               = self.Interrupt.get()
        instr_fetched     = self.Instruction_fetched.get()
        instr_decoded     = self.Instruction_decoded.get()
        executed_jump     = self.Executed_Jump.get()

        # ── Default output values (all de-asserted) ──────────────────────
        # output variables

        NotExecute=0
        LoadSelectMux=0
        LoadingMux=0
        Input_Select=0
        WE=0
        Read_Write=0   
        Address_XYZ=0
        IncDec=0
        write_RdL_Buffer=0
        write_RdH_Buffer=0
        write_RrL_Buffer=0
        write_RrH_Buffer=0
        InputSelect=0
        Write_Enable=0
        Load_Z=0
        Load_K=0
        Load_Jump=0
        relative_Absolute=0
        Load_Byte=0
        Fetch_next_instruction=0
        WB_Addr=self._wb_addr_val

        state = self.current_state
        i     = self._latched_inst   # use latched opcode during multi-cycle seqs
        next_state = state           # default: stay

        # ================================================================
        # STATE MACHINE
        # ================================================================

        # ── FETCH_INSTRUION: trigger fetch, wait for RomHandler ─────────
        if state == 'FETCH_INSTRUION':
            Fetch_next_instruction = 1
            if instr_fetched:                     # RomHandler signals fetch done
                next_state = 'DECODE_INSTRUCTION'

        # ── DECODE_INSTRUCTION: wait for decoder, then latch & route ────
        elif state == 'DECODE_INSTRUCTION':
            if not instr_decoded:
                # Decoder hasn't signalled ready yet — hold here
                pass
            else:
                # Latch the incoming instruction for use across all subsequent states
                i = inst
                self._latched_inst = i

                # For MUL instructions the result always goes to R1:R0. Pre-set
                # _wb_addr_val = 0 (R0) here so WRITE_RES_INIT can use MEM_WB_ADDR.
                if i in _MUL_FAMILY:
                    self._wb_addr_val = 0

                # Check for pending interrupt (only when we are at instruction boundary)
                if irq:
                    next_state = 'INTERRUPT_INIT'

                # ── Two-register ALU (fetch Rd first) ──────────────────────
                elif i in (_ALL_TWO_REG | _WORD_ALU | _BLD):
                    next_state = 'FETCH_RD_INIT'

                # ── Single-register ALU (fetch Rd only) ────────────────────
                elif i in _ALL_ONE_REG:
                    next_state = 'FETCH_RD_INIT'

                # ── Immediate ALU (fetch Rd only, K is directly wired to the ALU) ────────
                elif i in _ALL_IMM_ALU:
                    next_state = 'FETCH_RD_INIT'

                # ── Load from memory → Load to Rd that is in memory ────────
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
                    Load_Jump         = 1
                    relative_Absolute = 0            # relative
                    next_state = 'FINISED_INSTRUCTION_EXECUTION'

                elif i in _INDIRECT_JUMP:
                    Load_Z            = 1
                    Load_Jump         = 1
                    relative_Absolute = 1            # absolute (Z)
                    next_state = 'FINISED_INSTRUCTION_EXECUTION'

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
                    next_state = 'FETCH_INSTRUION'

                # ── NOP / SLEEP / WDR / BREAK ────────────────────────────────
                elif i in _NOP_MISC:
                    next_state = 'FETCH_INSTRUION'

                else:
                    # Unknown opcode — treat as NOP
                    next_state = 'FETCH_INSTRUION'

        # ================================================================
        # FETCH Rd — low byte
        # ================================================================
        elif state == 'FETCH_RD_INIT':
            Address_XYZ = MEM_RD    # drive Rd (0-31) onto address bus
            Read_Write  = 0         # read
            next_state = 'FETCH_RD_WAIT'

        elif state == 'FETCH_RD_WAIT':
            Address_XYZ = MEM_RD
            Read_Write  = 0
            if resp:
                next_state = 'FETCH_RD_LOADBUFFER'

        elif state == 'FETCH_RD_LOADBUFFER':
            write_RdL_Buffer = 1    # latch Rd into ALU input buffer

            # ── Route: where to next? ────────────────────────────────────
            if i in (_ALL_TWO_REG | _WORD_ALU):
                # Need Rr or second byte
                if i in _WORD_ALU:
                    # Pre-compute Rd+1 so B2 fetch/write states can use MEM_WB_ADDR.
                    ins_word = self._latched_inst
                    if i in {3, 8}:     # ADIW, SBIW: Rd = 24 + 2*(bits[5:4])
                        rd_base = 24 + (((ins_word >> 4) & 0x03) << 1)
                    elif i == 94:       # MOVW: Rd = bits[7:4] * 2
                        rd_base = ((ins_word >> 4) & 0x0F) * 2
                    else:
                        rd_base = (ins_word >> 4) & 0x1F
                    self._wb_addr_val = (rd_base + 1) & 0x1F
                    WB_Addr = self._wb_addr_val
                    next_state = 'FETCH_RD_INIT_B2'   # grab RdH first
                else:
                    next_state = 'FETCH_RR_INIT'

            elif i in _ALL_ONE_REG:
                next_state = 'EXECUTE_ALU_OPP'

            elif i in _ALL_IMM_ALU:
                Load_K = 1              # tell ROM handler to latch K
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
        # FETCH Rd — high byte  (ADIW / SBIW / MOVW — need Rd+1)
        # The ControlBox sets WB_Addr = Rd+1 so MemoryInterfaceHandler can
        # address it via MEM_WB_ADDR mode.
        # ================================================================
        elif state == 'FETCH_RD_INIT_B2':
            Address_XYZ = MEM_WB_ADDR   # address comes from WB_Addr port
            WB_Addr     = self._wb_addr_val
            Read_Write  = 0
            next_state = 'FETCH_RD_WAIT_B2'

        elif state == 'FETCH_RD_WAIT_B2':
            Address_XYZ = MEM_WB_ADDR
            WB_Addr     = self._wb_addr_val
            Read_Write  = 0
            if resp:
                next_state = 'FETCH_RD_LOADBUFFER_B2'

        elif state == 'FETCH_RD_LOADBUFFER_B2':
            write_RdH_Buffer = 1
            if i in {94}:   # MOVW — source is Rr pair, need Rr next
                next_state = 'FETCH_RR_INIT'
            else:
                # ADIW / SBIW: second operand is K (immediate)
                Load_K = 1
                next_state = 'EXECUTE_ALU_OPP'

        # ================================================================
        # FETCH Rr — low byte
        # ================================================================
        elif state == 'FETCH_RR_INIT':
            Address_XYZ = MEM_RR    # drive Rr (0-31) onto address bus
            Read_Write  = 0
            next_state = 'FETCH_RR_WAIT'

        elif state == 'FETCH_RR_WAIT':
            Address_XYZ = MEM_RR
            Read_Write  = 0
            if resp:
                next_state = 'FETCH_RR_LOADBUFFER'

        elif state == 'FETCH_RR_LOADBUFFER':
            write_RrL_Buffer = 1

            if i in _WORD_ALU:      # MOVW still needs RrH
                # Pre-compute Rr+1 for the B2 fetch (MOVW only).
                ins_word = self._latched_inst
                rr_base = (ins_word & 0x0F) * 2
                self._wb_addr_val = (rr_base + 1) & 0x1F
                WB_Addr = self._wb_addr_val
                next_state = 'FETCH_RR_INIT_B2'
            elif i in _SKIP:
                next_state = 'EXECUTE_SKIP'
            else:
                next_state = 'EXECUTE_ALU_OPP'

        # ================================================================
        # FETCH Rr — high byte  (MOVW only — need Rr+1)
        # ================================================================
        elif state == 'FETCH_RR_INIT_B2':
            Address_XYZ = MEM_WB_ADDR   # WB_Addr holds Rr+1
            WB_Addr     = self._wb_addr_val
            Read_Write  = 0
            next_state = 'FETCH_RR_WAIT_B2'

        elif state == 'FETCH_RR_WAIT_B2':
            Address_XYZ = MEM_WB_ADDR
            WB_Addr     = self._wb_addr_val
            Read_Write  = 0
            if resp:
                next_state = 'FETCH_RR_LOADBUFFER_B2'

        elif state == 'FETCH_RR_LOADBUFFER_B2':
            write_RrH_Buffer = 1
            next_state = 'EXECUTE_ALU_OPP'

        # ================================================================
        # EXECUTE — ALU operation (result available next clock)
        # ================================================================
        elif state == 'EXECUTE_ALU_OPP':
            # ALU is purely combinatorial; no output signals needed here.
            # Route to the correct write-back path based on result width.

            if i in (_RD_RR_NO_WRITE | _RD_ONLY_NO_WRITE | _RD_K_NO_WRITE):
                # CP / CPC / CPSE / CPI / TST / BST — flags only, no register write
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

            elif i in (_MUL_FAMILY | _WORD_ALU):
                # 16-bit result instructions:
                #   MUL family  → R1:R0
                #   ADIW / SBIW / MOVW → Rd+1:Rd
                # Write low byte first; WRITE_RES_FINISHED will chain to B2.
                next_state = 'WRITE_RES_INIT'

            else:
                # All remaining 8-bit write-back ops:
                # ADD, ADC, SUB, SUBI, SBC, SBCI, AND, ANDI, OR, ORI, EOR,
                # MOV, LDI, COM, NEG, INC, DEC, CLR, SER, LSL, LSR, ROL,
                # ROR, ASR, SWAP, BLD, CBR, SBR — single byte to Rd.
                next_state = 'WRITE_RES_INIT'

        # ================================================================
        # EXECUTE — Branch
        # ================================================================
        elif state == 'EXECUTE_BRANCH':
            if branch:
                Load_Jump         = 1
                relative_Absolute = 0   # all AVR branches are PC-relative
                next_state = 'FINISED_INSTRUCTION_EXECUTION'
            else:
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # EXECUTE — Skip
        # ================================================================
        elif state == 'EXECUTE_SKIP':
            if skip:
                # SKIP state will suppress the next fetched instruction
                next_state = 'SKIP'
            else:
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # SKIP — hold NotExecute for one cycle to swallow the next instr
        # ================================================================
        elif state == 'SKIP':
            NotExecute = 1
            next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # LOAD from memory (LD / LDS / LPM)
        # ================================================================
        elif state == 'FETCH_MEMORY_VALL_INIT':
            Address_XYZ = 1     # use pointer address from instruction decoder
            Read_Write  = 0     # read
            next_state = 'FETCH_MEMORY_VALL_WAIT'

        elif state == 'FETCH_MEMORY_VALL_WAIT':
            Address_XYZ = 1
            Read_Write  = 0
            if resp:
                # Data from memory arrives on bus → write to Rd
                next_state = 'WRITE_RES_INIT'

        # ================================================================
        # STORE to memory (ST / STS / SPM)
        # ================================================================
        elif state == 'WRITE_MEMORY_VALL_INIT':
            Address_XYZ = 1
            Read_Write  = 1     # write
            Input_Select= 1     # source = ALU ResL (which holds Rd value)
            next_state = 'WRITE_MEMORY_VALL_WAIT'

        elif state == 'WRITE_MEMORY_VALL_WAIT':
            Address_XYZ = 1
            Read_Write  = 1
            Input_Select= 1
            if resp:
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # WRITE result to register file — low byte  (Rd ← ResL)
        # For MUL family: result → R0 (address 0), driven via MEM_WB_ADDR.
        # For all other ops: result → Rd, driven via MEM_RD.
        # ================================================================
        elif state == 'WRITE_RES_INIT':
            Input_Select = 2            # ALU ResL → write data
            Read_Write   = 1            # write
            if i in _MUL_FAMILY:
                Address_XYZ = MEM_WB_ADDR   # WB_Addr = 0 (R0), set at DECODE
                WB_Addr     = self._wb_addr_val
            else:
                Address_XYZ = MEM_RD        # address = Rd
            next_state = 'WRITE_RES_WAIT'

        elif state == 'WRITE_RES_WAIT':
            Input_Select = 2
            Read_Write   = 1
            if i in _MUL_FAMILY:
                Address_XYZ = MEM_WB_ADDR
                WB_Addr     = self._wb_addr_val
            else:
                Address_XYZ = MEM_RD
            if resp:
                next_state = 'WRITE_RES_FINISHED'

        elif state == 'WRITE_RES_FINISHED':
            # Only 16-bit-result instructions chain to a second write-back:
            #   _MUL_FAMILY  (23-28)  → high byte goes to R1  (WB_Addr=1)
            #   _WORD_ALU    (3,8,94) → high byte goes to Rd+1 (WB_Addr=rd+1)
            # Every other instruction (8-bit ALU, LD, POP, IN ...) stops here.
            if i in (_MUL_FAMILY | _WORD_ALU):
                if i in _MUL_FAMILY:
                    self._wb_addr_val = 1   # R1 (high byte of MUL result)
                else:
                    # ADIW (3) / SBIW (8) / MOVW (94): high byte → Rd+1
                    ins_word = self._latched_inst
                    if i in {3, 8}:     # ADIW, SBIW: Rd = 24 + 2*(bits[5:4])
                        rd_base = 24 + (((ins_word >> 4) & 0x03) << 1)
                    else:               # MOVW (94): Rd = bits[7:4] * 2
                        rd_base = ((ins_word >> 4) & 0x0F) * 2
                    self._wb_addr_val = (rd_base + 1) & 0x1F
                WB_Addr = self._wb_addr_val
                next_state = 'WRITE_RES_INIT_B2'
            else:
                # 8-bit result — single write-back is complete.
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # WRITE result — high byte (R1 for MUL; Rd+1 for ADIW/SBIW/MOVW)
        # ================================================================
        elif state == 'WRITE_RES_INIT_B2':
            Input_Select = 3            # ALU ResH → write data
            Read_Write   = 1
            Address_XYZ  = MEM_WB_ADDR
            WB_Addr      = self._wb_addr_val
            next_state = 'WRITE_RES_WAIT_B2'

        elif state == 'WRITE_RES_WAIT_B2':
            Input_Select = 3
            Read_Write   = 1
            Address_XYZ  = MEM_WB_ADDR
            WB_Addr      = self._wb_addr_val
            if resp:
                next_state = 'WRITE_RES_FINISHED_B2'

        elif state == 'WRITE_RES_FINISHED_B2':
            next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # PUSH  (SP-- then write Rd to new SP)
        # ================================================================
        elif state == 'PUSH_INIT':
            Address_XYZ = MEM_SP        # SP pointer
            Read_Write  = 1
            Input_Select= 1             # Rd value in ALU ResL
            next_state = 'PUSH_WAIT'

        elif state == 'PUSH_WAIT':
            Address_XYZ = MEM_SP
            Read_Write  = 1
            Input_Select= 1
            if resp:
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # POP  (read from SP then SP++)
        # ================================================================
        elif state == 'POP_INIT':
            Address_XYZ = MEM_SP        # SP pointer
            Read_Write  = 0             # read
            next_state = 'POP_WAIT'

        elif state == 'POP_WAIT':
            Address_XYZ = MEM_SP
            Read_Write  = 0
            if resp:
                # Data is on the bus — latch it then write back to Rd
                write_RdL_Buffer = 1
                next_state = 'WRITE_RES_INIT'

        # ================================================================
        # IN — read from I/O port into Rd
        # ================================================================
        elif state == 'IO_READ_INIT':
            Address_XYZ = MEM_RAM_ADDR  # I/O address from instruction decoder
            Read_Write  = 0
            next_state = 'IO_READ_WAIT'

        elif state == 'IO_READ_WAIT':
            Address_XYZ = MEM_RAM_ADDR
            Read_Write  = 0
            if resp:
                next_state = 'IO_READ_LOADBUFFER'

        elif state == 'IO_READ_LOADBUFFER':
            write_RdL_Buffer = 1
            next_state = 'WRITE_RES_INIT'

        # ================================================================
        # OUT — write Rd to I/O port (Rd was fetched in FETCH_RD sequence)
        # ================================================================
        elif state == 'IO_WRITE_INIT':
            Address_XYZ = MEM_RAM_ADDR  # I/O address from instruction decoder
            Read_Write  = 1
            Input_Select= 1             # Rd in ResL
            next_state = 'IO_WRITE_WAIT'

        elif state == 'IO_WRITE_WAIT':
            Address_XYZ = MEM_RAM_ADDR
            Read_Write  = 1
            Input_Select= 1
            if resp:
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # CALL — push return address (PCL first, then PCH), then jump
        # ================================================================
        elif state == 'CALL_PUSH_PCL_INIT':
            Address_XYZ = MEM_SP        # SP
            Read_Write  = 1
            Input_Select= 3             # PC low byte via GeneralInput
            next_state = 'CALL_PUSH_PCL_WAIT'

        elif state == 'CALL_PUSH_PCL_WAIT':
            Address_XYZ = MEM_SP
            Read_Write  = 1
            Input_Select= 3
            if resp:
                next_state = 'CALL_PUSH_PCH_INIT'

        elif state == 'CALL_PUSH_PCH_INIT':
            Address_XYZ = MEM_SP
            Read_Write  = 1
            Input_Select= 3             # PC high byte via GeneralInput
            next_state = 'CALL_PUSH_PCH_WAIT'

        elif state == 'CALL_PUSH_PCH_WAIT':
            Address_XYZ = MEM_SP
            Read_Write  = 1
            Input_Select= 3
            if resp:
                # Return address saved — now perform the jump
                if i in _RELATIVE_CALL:
                    Load_Jump         = 1
                    relative_Absolute = 0
                elif i in _INDIRECT_CALL:
                    Load_Z            = 1
                    Load_Jump         = 1
                    relative_Absolute = 1
                elif i in _ABSOLUTE_CALL:
                    Load_Jump         = 1
                    relative_Absolute = 1
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # RET / RETI — pop return address from stack
        # ================================================================
        elif state == 'RET_POP_PCH_INIT':
            Address_XYZ = MEM_SP        # SP
            Read_Write  = 0
            next_state = 'RET_POP_PCH_WAIT'

        elif state == 'RET_POP_PCH_WAIT':
            Address_XYZ = MEM_SP
            Read_Write  = 0
            if resp:
                next_state = 'RET_POP_PCL_INIT'

        elif state == 'RET_POP_PCL_INIT':
            Address_XYZ = MEM_SP
            Read_Write  = 0
            next_state = 'RET_POP_PCL_WAIT'

        elif state == 'RET_POP_PCL_WAIT':
            Address_XYZ = MEM_SP
            Read_Write  = 0
            if resp:
                next_state = 'RET_LOAD_PC'

        elif state == 'RET_LOAD_PC':
            Load_Jump         = 1
            relative_Absolute = 1       # absolute (restored address)
            if i in _RETURN_INT:
                # RETI also re-enables interrupts (set SREG.I) —
                # signalled externally; FSM just marks the state.
                pass
            next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # JMP (absolute 22-bit)
        # ================================================================
        elif state == 'LONG_JUMP_LOAD_UPPER6_BITS_IN_TO_REGISTER':
            # Second word of 32-bit JMP/CALL instruction holds full 16-bit
            # lower target address; upper 6 bits are in the opcode word.
            Load_Byte         = 1
            Load_Jump         = 1
            relative_Absolute = 1
            next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # INTERRUPT — save context, jump to vector
        # ================================================================
        elif state == 'INTERRUPT_INIT':
            # Push PCL onto stack
            Address_XYZ = MEM_SP
            Read_Write  = 1
            Input_Select= 3
            next_state = 'INTERRUPT_JUMP'

        elif state == 'INTERRUPT_JUMP':
            Address_XYZ = MEM_SP
            Read_Write  = 1
            Input_Select= 3
            if resp:
                Load_Jump         = 1
                relative_Absolute = 1   # jump to interrupt vector (absolute)
                next_state = 'FINISED_INSTRUCTION_EXECUTION'

        elif state == 'RETURN_FROM_INTERRUPT':
            # Alias for RETI handling (routed through RET path above)
            Load_Jump         = 1
            relative_Absolute = 1
            next_state = 'FINISED_INSTRUCTION_EXECUTION'

        # ================================================================
        # FINISED_INSTRUCTION_EXECUTION — signal fetch of next instruction
        # ================================================================
        elif state == 'FINISED_INSTRUCTION_EXECUTION':
            # Assert Fetch_next_instruction to tell RomHandler + decoder
            # that execution is complete and the pipeline should advance.
            Fetch_next_instruction = 1
            # Wait for RomHandler to confirm the jump/fetch is done before
            # allowing the decoder to accept a new instruction.
            if executed_jump:
                next_state = 'FETCH_INSTRUION'

        else:
            # Safety catch-all
            next_state = 'FETCH_INSTRUION'

        # ================================================================
        # Drive all outputs
        # ================================================================
        self.NotExecute.put(NotExecute)
        self.LoadSelectMux.put(LoadSelectMux)
        self.LoadingMux.put(LoadingMux)
        self.Input_Select.put(Input_Select)
        self.WE.put(WE)
        self.Read_Write.put(Read_Write)
        self.Address_XYZ.put(Address_XYZ)
        self.IncDec.put(IncDec)

        if write_RdL_Buffer:
            self.write_Opperand_Buffer.put(1)   # 1=A0
        elif write_RdH_Buffer:
            self.write_Opperand_Buffer.put(2)   # 2=A1
        elif write_RrL_Buffer:
            self.write_Opperand_Buffer.put(3)   # 3=B0
        elif write_RrH_Buffer:
            self.write_Opperand_Buffer.put(4)   # 4=B1
        else:
            self.write_Opperand_Buffer.put(0)

        self.InputSelect.put(InputSelect)
        self.Write_Enable.put(Write_Enable)

        self.Load_Z.put(Load_Z)
        self.Load_K.put(Load_K)
        self.Load_Jump.put(Load_Jump)
        self.relative_Absolute.put(relative_Absolute)
        self.Load_Byte.put(Load_Byte)
        self.Fetch_next_instruction.put(Fetch_next_instruction)

        # Drive the explicit write-back address (used by MEM_WB_ADDR mode)
        self.WB_Addr.put(WB_Addr)

        # Advance state
        self.current_state = next_state