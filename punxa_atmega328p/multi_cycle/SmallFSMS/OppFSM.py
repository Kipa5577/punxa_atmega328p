import py4hw

# Rd ← op(Rd, K)  — one register + 8-bit immediate
_RD_K_ALU_WRITE = {
    5,   # SUBI
    7,   # SBCI
    10,  # ANDI
    12,  # ORI
    16,  # SBR  (= ORI)
    17,  # CBR  (= ANDI with ~K)
    # 6 (SBC) intentionally NOT here -- SBC Rd,Rr is a genuine two-register
    # instruction (Rd <- Rd - Rr - C), not an immediate op like SBCI. It
    # was previously misclassified here (likely a copy/paste from SBCI),
    # which routed it into LOAD_VAL_K_IN_BUFFER instead of FETCH_RR --
    # Rr was never fetched at all, so SBC silently computed Rd - 0 - C.
    # Falling through to the `else: FETCH_RR` branch below is correct.
    # 95 (LDI) removed — LDI is now handled entirely by LDST_FSM.
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
    76,  # BLD moved here — reads Rd, writes Rd
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
    
}

# Conditional branches: BRBS / BRBC and all 18 derived mnemonics
# (BREQ, BRNE, BRCS, ... ). These take no register operand at all —
# they just test a single SREG flag (already resolved into the ALU's
# `Branch` output) and, if true, apply a relative PC offset via the
# RomHandler's K7 path (Load_K + K_select=0). No register fetch and no
# register write-back should ever happen for these opcodes.
_BRANCH = set(range(45, 65))

# op(Rd, Rr)  — compare / test, no write-back to register file
_RD_RR_NO_WRITE = {
    38,  # CP
    39,  # CPC
    37,  # CPSE   (also generates a skip if equal — handled in EXECUTE_ALU_OPP)
    75,  # BST    (stores bit from Rd into T flag only)
}

# I/O Bit Modifications (SBI / CBI)
_IO_BIT_MOD = {
    65,  # SBI
    66,  # CBI
}

_RD_RR_ALU_WRITE = {
    1,   # ADD
    2,   # ADC
    4,   # SUB   
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

STATES = [
    'STOP',

    # FOR 1 WORD INSTRUCTIONS
    'FETCH_RD','WAIT_FETCH_RD','LOAD_VAL_RD_IN_BUFFER',
    'FETCH_RR','WAIT_FETCH_RR','LOAD_VAL_RR_IN_BUFFER',
    'WAIT_RR_RESP_LOW',

    # FOR 2 WORD INSTRUCTIONS 
    'FETCH_RD_B2','WAIT_FETCH_RD_B2','LOAD_VAL_RD_IN_BUFFER_B2',
    'FETCH_RR_B2','WAIT_FETCH_RR_B2','LOAD_VAL_RR_IN_BUFFER_B2',

    # SBRC – Skip if Bit in Register is Cleared (or SBRS)
    # EVALUATED AFTER RD IS LOADED 

    # SBIC – Skip if Bit in I/O Register is Cleared (or SBIS)
    'FETCH_IO_REG_VAL','WAIT_FETCH_IO_REG_VAL','LOAD_FETCH_IO_REG_TO_BUFFER',

    # BSET - BLIR
    # JUST JUMP TO THE DETERMINE OUTPUT FAISE

    'LOAD_VAL_K_IN_BUFFER',
    'DETERMINE_OUTPUT',

    # BRBS / BRBC and derived conditional branches
    'BRANCH_DECIDE','BRANCH_JUMP',

    # WRITE BACK I/O FOR SBI / CBI
    'WRITE_IO_REG_VAL', 'WAIT_WRITE_IO_REG_VAL',

    #
    'LOAD_RESULT','WAIT_LOAD_RESULT',
    'WAIT_WRITE_RESP_LOW',
    
    # THESE ARE FOR 2 BYRE RESULT INSTRUCTIONS 
    'LOAD_RESULT_B2','WAIT_LOAD_RESULT_B2',
]

class OPP_FSM(py4hw.Logic):
    def __init__(self, parent, name,
                 # ── Logic imputs─────────────────────────────────────────
                 run, # 1-Bit The main FSM pulls this to high to trigger this FSM
                 done, # 1-Bit The main FSM recives this to high to indicate that this FSM has finished
                 # ── Inputs ──────────────────────────────────────────────
                 Instruction,        # 8-bit opcode from instruction decoder
                 Resp,               # 1-bit: memory operation Finished
                 Branch,             # 1-bit: ALU branch condition met
                 Executed_Jump, # This tell the controll box that the romHandler has successfully executed the jump instrution and it is ready to load the next instruction

                 # ── Memory Interface Outputs ─────────────────────────────
                 LoadSelectMux,      # address mux for memory reads
                 LoadingMux,         # selects which pointer reg is loaded
                 InputSelectMemory,       # data source mux for memory writes
                 WEMEMORY,           # write enable for pointer registers
                 Read_Write,         # 0=read, 1=write
                 Mem_Instruction,    # pointer selection for Mem_instruction in MemoryInterface
                 IncDec,             # This icrement or Decrements address

                 # ── ALU Buffer Outputs ───────────────────────────────────
                 InputSelectBuffer, # 1 = Load Data in to Rr0 , 0 = Load K in to Rr0
                 WEBUFFER, # 1 = Rd0, 2 = Rd1, 3 = Rr0, 4 = Rr1, 5 = IOBuffer

                 # ── ROM Handler Outputs ──────────────────────────────────
                 Load_Z,             # load Z pointer from program memory
                 Load_K,             # load immediate K to rom loader for relative or absolute jump
                 Load_Jump,          # trigger PC jump
                 relative_Absolute,  # 0=relative, 1=absolute jump
                 Load_Byte,          # 0 = fetches form rom  1 = writes to rom
                 Fetch_next_instruction, # If set to 1 fetches the next instruction it has to be set back to 0 and then to one for the next instruction to be fetched
                 Fetch_Address, # In the case of STS instruction to fetch the instruction 
                 LOAD_PCL,
                 LOAD_PCH,
                 K_Select,           # 2-bit: selects K7/K12/K7_22 in RomHandler (K7 for conditional branches)
                 # Fethc_next_instruction is also used to rest the outputs of the instruction decoder and to tell it to expect a new instruction
                 # The instruction decoder also recives the instruction_fetched signal form the romHandler to tell it that it has a new instrucion in its entrance.

                 # ── Write-back address ───────────────────────────────────
                 WB_Addr,            # 5-bit explicit write-back address (for Rd+1, R0, R1 in MUL, etc.)
                 ):
        super().__init__(parent, name)


        # ── Logic imputs─────────────────────────────────────────
        self.run                   = self.addIn('Run',run)
        self.done                  = self.addOut('Done',done)
        # ── Register inputs ──────────────────────────────────────────────
        self.Instruction           = self.addIn('Instruction',           Instruction)
        self.Resp                  = self.addIn('Resp',                  Resp)
        self.Branch                = self.addIn('Branch',                Branch)
        self.Executed_Jump         = self.addIn('Executed_Jump',         Executed_Jump)

        # ── Register outputs ─────────────────────────────────────────────
        self.LoadSelectMux    = self.addOut('LoadSelectMux',    LoadSelectMux)
        self.LoadingMux       = self.addOut('LoadingMux',       LoadingMux)
        self.InputSelectMemory     = self.addOut('InputSelectMemory',     InputSelectMemory)
        self.WEMEMORY         = self.addOut('WEMEMORY',         WEMEMORY)
        self.Read_Write       = self.addOut('Read_Write',       Read_Write)
        self.Mem_Instruction      = self.addOut('Mem_Instruction',      Mem_Instruction)
        self.IncDec           = self.addOut('IncDec',           IncDec)

        self.InputSelectBuffer =  self.addOut('InputSelectBuffer', InputSelectBuffer)
        self.WEBUFFER         = self.addOut('WEBUFFER',         WEBUFFER)

        self.Load_Z           = self.addOut('Load_Z',           Load_Z)
        self.Load_K           = self.addOut('Load_K',           Load_K)
        self.Load_Jump        = self.addOut('Load_Jump',        Load_Jump)
        self.relative_Absolute= self.addOut('relative_Absolute',relative_Absolute)
        self.Load_Byte        = self.addOut('Load_Byte',        Load_Byte)
        self.Fetch_next_instruction           = self.addOut('Fetch_next_instruction',           Fetch_next_instruction)
        self.WB_Addr          = self.addOut('WB_Addr',          WB_Addr)
        self.Fetch_Address    = self.addOut('Fetch_Address',Fetch_Address)

        self.LOAD_PCL = self.addOut('LOAD_PCL',LOAD_PCL)
        self.LOAD_PCH = self.addOut('LOAD_PCH',LOAD_PCH)
        self.K_Select = self.addOut('K_Select',K_Select)

        # ── FSM state ────────────────────────────────────────────────────
        self.current_state = 'STOP'
        # Remember the instruction across multi-cycle sequences
        self._latched_inst = 0
        # Explicit selected address used when Mem_instruction == MEM_WB_ADDR

        # Remember whether the pointer used a post-increment / pre-decrement
        # addressing mode and therefore needs the updated value written
        # back to its SRAM-mapped register (R26-R31) once the access
        # sequence completes.
        self._pointer_update_pending = False
        self.debug = 0

    def clock(self):
        inst              = self.Instruction.get()
        resp              = self.Resp.get()
        branch            = self.Branch.get()
        executed_jump     = self.Executed_Jump.get()
        run               = self.run.get()

        # --- Instruction Buffers ----
        InputSelect_Buffer = 0       
        WE_Buffer = 0
        LoadSelectMux = 0 
        LoadingMux = 0

        # --- MemoryInterfaceHandler ---
        Read_Write = 0
        Mem_Instruction = 0
        IncDec = 0
        InputSelect_Memory = 0
        WE_Memory = 0
        WB_Addr = 0

        # --- RomHandler ---
        Load_Z = 0
        Load_K = 0
        Load_Jump = 0
        relative_Absolute = 0
        Load_Byte = 0
        Fetch_Address = 0
        K_select = 0

        # --- FSM_Control ---
        done = 0

        state = self.current_state
        i     = self._latched_inst   # use latched opcode during multi-cycle seqs
        next_state = state           # default: stay

        # ================================================================
        # STATE MACHINE
        # ================================================================

        if state == 'STOP':
            if run:
                self._latched_inst = inst
                i = inst
                if i in _SREG_ONLY:
                    next_state = 'DETERMINE_OUTPUT'
                elif i in _BRANCH:
                    next_state = 'BRANCH_DECIDE'
                elif i in {41, 42}:          
                    next_state = 'FETCH_RR'
                elif i in _IO_BIT_MOD:
                    next_state = 'FETCH_IO_REG_VAL'
                else:
                    next_state = 'FETCH_RD'

        # ================================================================
        # FETCH RD BYTE 0
        # ================================================================

        elif state == 'FETCH_RD':
            Mem_Instruction = 12 # RD pointer
            Read_Write  = 2 # read opp 
            InputSelect_Memory = 1 
            next_state = 'WAIT_FETCH_RD'

        elif state == 'WAIT_FETCH_RD':
            Read_Write  = 2 # read opp
            Mem_Instruction = 12 # RD pointer
            if resp:
                next_state = 'LOAD_VAL_RD_IN_BUFFER'

        elif state == 'LOAD_VAL_RD_IN_BUFFER':
            Mem_Instruction = 12
            InputSelect_Memory = 1
            WE_Buffer = 1          
            InputSelect_Buffer = 1 

            if resp == 1:
                next_state = 'LOAD_VAL_RD_IN_BUFFER'
            else:
                if i in _RD_ONLY_WRITE:
                    next_state = 'DETERMINE_OUTPUT'
                elif i in _RD_K_ALU_WRITE or i in _RD_K_NO_WRITE:
                    next_state = 'LOAD_VAL_K_IN_BUFFER'
                elif i in {43, 44}:               # SBIC / SBIS
                    next_state = 'FETCH_IO_REG_VAL'
                elif i in {3, 8}:                 # ADIW / SBIW: word Rd, need Rd+1 too
                    next_state = 'FETCH_RD_B2'
                else:
                    next_state = 'FETCH_RR'

        # ================================================================
        # FETCH RD BYTE 1
        # ================================================================

        elif state == 'FETCH_RD_B2':
            Mem_Instruction = 15 # RD+1 pointer
            Read_Write  = 2 # read opp 
            InputSelect_Memory = 1 
            next_state = 'WAIT_FETCH_RD_B2'

        elif state == 'WAIT_FETCH_RD_B2':
            # FIX: this state previously asserted nothing while waiting, so
            # the read request (Mem_Instruction=15, Read_Write=2) was
            # dropped the instant FETCH_RD_B2 finished its one cycle.
            # `resp` would then fire (if at all) disconnected from this
            # specific request, and LOAD_VAL_RD_IN_BUFFER_B2 would latch
            # whatever stale value happened to be on the bus instead of
            # Rd+1's real content -- exactly mirrors WAIT_FETCH_RD's own
            # structure for the low byte.
            Mem_Instruction = 15   # RD+1 pointer
            Read_Write = 2         # read opp
            InputSelect_Memory = 1
            if resp:
                next_state = 'LOAD_VAL_RD_IN_BUFFER_B2'

        elif state == 'LOAD_VAL_RD_IN_BUFFER_B2':
            # FIX: this state previously only set next_state and nothing
            # else -- it never asserted WE_Buffer, so the just-fetched high
            # byte of Rd was silently discarded instead of being latched
            # into the buffer's Rd1 slot. Mirrors LOAD_VAL_RD_IN_BUFFER's
            # own byte-0 latch structure.
            Mem_Instruction = 15   # RD+1 pointer (keep address/bus stable)
            InputSelect_Memory = 1
            WE_Buffer = 2          # latch into Rd1
            InputSelect_Buffer = 1
            if i in {3, 8}:        # ADIW / SBIW: no Rr to fetch, load K instead
                next_state = 'LOAD_VAL_K_IN_BUFFER'
            else:
                next_state = 'FETCH_RR_B2'

        # ================================================================
        # FETCH RR BYTE 0
        # ================================================================

        elif state == 'FETCH_RR':
            Mem_Instruction = 13 # RR pointer
            Read_Write  = 2 # read opp 
            InputSelect_Memory = 1 
            next_state = 'WAIT_FETCH_RR'

        elif state == 'WAIT_FETCH_RR':
            Mem_Instruction = 13
            Read_Write = 2
            InputSelect_Memory = 1
            if resp:
                next_state = 'LOAD_VAL_RR_IN_BUFFER'

        elif state == 'LOAD_VAL_RR_IN_BUFFER':
            Mem_Instruction = 13
            InputSelect_Memory = 1

            if i in {41, 42}:          # SBRC / SBRS
                WE_Buffer = 1
            else:
                WE_Buffer = 3
            InputSelect_Buffer = 1

            # capture happens this single cycle, then drop the request
            next_state = 'WAIT_RR_RESP_LOW'

        elif state == 'WAIT_RR_RESP_LOW':
            # Read_Write defaults to 0 here — this is what actually lets resp fall
            if resp == 0:
                next_state = 'DETERMINE_OUTPUT'

        # ================================================================
        # FETCH RR BYTE 1
        # ================================================================

        elif state == 'FETCH_RR_B2':
            Mem_Instruction = 16 # RR+1 pointer
            Read_Write  = 2 # read opp 
            InputSelect_Memory = 1 
            next_state = 'WAIT_FETCH_RR_B2'

        elif state == 'WAIT_FETCH_RR_B2':
            # Same fix as WAIT_FETCH_RD_B2: hold the read request stable
            # while waiting for resp, instead of letting it drop to IDLE.
            Mem_Instruction = 16   # RR+1 pointer
            Read_Write = 2         # read opp
            InputSelect_Memory = 1
            if resp:
                next_state = 'LOAD_VAL_RR_IN_BUFFER_B2'

        elif state == 'LOAD_VAL_RR_IN_BUFFER_B2':
            WE_Buffer = 4         
            InputSelect_Buffer = 1
            next_state = 'DETERMINE_OUTPUT'

        # ================================================================
        # FETCH IO REGISTER VALUE
        # ================================================================

        elif state == 'FETCH_IO_REG_VAL':
            Mem_Instruction = 17   # MEM_A_5bit
            Read_Write = 2         # read
            InputSelect_Memory = 1
            next_state = 'WAIT_FETCH_IO_REG_VAL'

        elif state == 'WAIT_FETCH_IO_REG_VAL':
            Mem_Instruction = 17
            Read_Write = 2
            InputSelect_Memory = 1
            if resp:
                next_state = 'LOAD_FETCH_IO_REG_TO_BUFFER'

        elif state == 'LOAD_FETCH_IO_REG_TO_BUFFER':
            # FIX: SBI/CBI (65/66) need the fetched I/O value to reach AU's
            # RegAL input, which is hard-wired to ImputRegA0 (buffer slot
            # WE=1) -- not IOBuffer (WE=5). IOBuffer only feeds BranchUnit,
            # which is used exclusively by SBIC/SBIS's skip evaluation.
            # Previously this state always used WE=5 regardless of which
            # instruction got here, so SBI/CBI's AU computation silently
            # read stale/zero data from ImputRegA0 instead of the real I/O
            # register value (e.g. CBI on 0xFF, bit 0 produced 0x00 instead
            # of 0xFE, because AU saw RegAL=0 and 0 & ~1 == 0).
            WE_Buffer = 1 if i in {65, 66} else 5     # write DATA into A0 (SBI/CBI) or IOBuffer (SBIC/SBIS)
            InputSelect_Buffer = 1

            # 4-Phase Handshake: Wait for memory to acknowledge request drop
            if resp == 1:
                next_state = 'LOAD_FETCH_IO_REG_TO_BUFFER'
            else:
                next_state = 'DETERMINE_OUTPUT'

        # ================================================================
        # LOAD IMMEDIATE K
        # ================================================================

        elif state == 'LOAD_VAL_K_IN_BUFFER':
            WE_Buffer = 3
            InputSelect_Buffer = 0   # select K, not DATA
            next_state = 'DETERMINE_OUTPUT'

        # ================================================================
        # ALU / SKIP / FLAG DECISION POINT
        # ================================================================

        elif state == 'DETERMINE_OUTPUT':

            # No register write instructions
            if i in _RD_K_NO_WRITE:
                done = 1
                next_state = 'STOP'

            elif i in _RD_RR_NO_WRITE:
                done = 1
                next_state = 'STOP'

            elif i in _SKIP:
                done = 1
                next_state = 'STOP'

            elif i in _SREG_ONLY:
                done = 1
                next_state = 'STOP'

            # MUL-family => 16-bit result
            elif i in {23,24,25,26,27,28}:
                next_state = 'LOAD_RESULT'

            # Conditional branches never reach here in normal operation
            elif i in _BRANCH:
                done = 1
                next_state = 'STOP'

            # Route SBI and CBI to dedicated write-back path
            elif i in _IO_BIT_MOD:
                next_state = 'WRITE_IO_REG_VAL'

            # Everything else writes a single byte
            else:
                next_state = 'LOAD_RESULT'

        # ================================================================
        # BRBS / BRBC / DERIVED CONDITIONAL BRANCHES
        # ================================================================

        elif state == 'BRANCH_DECIDE':
            # `branch` is the ALU's resolved condition (correct SREG bit
            # already selected via BitPos). No register/memory access
            # of any kind is involved for a branch.
            if branch == 1:
                next_state = 'BRANCH_JUMP'
            else:
                done = 1
                next_state = 'STOP'

        elif state == 'BRANCH_JUMP':
            # Pulse Load_K for one cycle with K_select=0 (K7 = 7-bit
            # signed relative offset) so RomHandler applies PC += k7.
            Load_K = 1
            K_select = 0
            if executed_jump == 1:
                done = 1
                next_state = 'STOP'

        # ================================================================
        # WRITE RESULT BYTE 0
        # ================================================================

        elif state == 'LOAD_RESULT':
            if i in {23, 24, 25, 26, 27, 28}:
                # FIX: MUL/MULS/MULSU/FMUL/FMULS/FMULSU always write their
                # result to the FIXED register pair R1:R0, regardless of
                # what Rd/Rr the instruction encoded. Mem_Instruction=12
                # (MEM_RD) addresses *Rd itself* -- so this was silently
                # overwriting one of the instruction's own operand
                # registers (e.g. `fmul r16, r17` was clobbering r16)
                # instead of writing to r0. Mem_Instruction=14
                # (MEM_WB_ADDR) with an explicit WB_Addr is the path meant
                # for exactly this case (see WB_Addr's own doc comment:
                # "R0/R1 for MUL").
                Mem_Instruction = 14  # MEM_WB_ADDR
                WB_Addr = 0           # R0
            else:
                Mem_Instruction = 12  # RD pointer
                WB_Addr = 0
            Read_Write = 1 # Write 
            InputSelect_Memory = 2 
            next_state = 'WAIT_LOAD_RESULT'

        elif state == 'WAIT_LOAD_RESULT':
            if i in {23, 24, 25, 26, 27, 28}:
                Mem_Instruction = 14
                WB_Addr = 0
            else:
                Mem_Instruction = 12
                WB_Addr = 0
            Read_Write = 1
            InputSelect_Memory = 2
            if resp:
                if i in {23,24,25,26,27,28,3,8}:
                    next_state = 'WAIT_WRITE_RESP_LOW'
                else:
                    done = 1
                    next_state = 'STOP'

        elif state == 'WAIT_WRITE_RESP_LOW':
            # By default Read_Write = 0 here, safely dropping the write request
            if resp == 0:
                next_state = 'LOAD_RESULT_B2'

        # ================================================================
        # WRITE RESULT BYTE 1
        # ================================================================

        elif state == 'LOAD_RESULT_B2':
            if i in {23, 24, 25, 26, 27, 28}:
                # FIX: same reasoning as LOAD_RESULT above -- the high
                # byte of a MUL-family result always goes to the fixed
                # R1, not to "Rd+1" (Mem_Instruction=15 / MEM_RD_1),
                # which was clobbering the register right after Rd
                # (e.g. `fmul r16, r17` was overwriting r17 instead of r1).
                Mem_Instruction = 14  # MEM_WB_ADDR
                WB_Addr = 1           # R1
            else:
                Mem_Instruction = 15  # RD+1 pointer
                WB_Addr = 0
            Read_Write = 1 # Write 
            # FIX: this is the HIGH byte of the result. InputSelect_Memory=2
            # is INPUT_RESL (ResL) -- the same source LOAD_RESULT just used
            # for the low byte. Writing ResL here again means R1 ends up
            # with the same value as R0 instead of the high byte, no matter
            # how correct the destination address (WB_Addr) is.
            # INPUT_RESH (3) reads AU's ResH output instead.
            InputSelect_Memory = 3
            next_state = 'WAIT_LOAD_RESULT_B2'

        elif state == 'WAIT_LOAD_RESULT_B2':
            if i in {23, 24, 25, 26, 27, 28}:
                Mem_Instruction = 14
                WB_Addr = 1
            else:
                Mem_Instruction = 15
                WB_Addr = 0
            Read_Write = 1       # Write 
            InputSelect_Memory = 3  # FIX: INPUT_RESH, see LOAD_RESULT_B2 above
            if resp:
                done = 1
                next_state = 'STOP'

        # ================================================================
        # WRITE I/O REGISTER VALUE (SBI / CBI)
        # ================================================================

        elif state == 'WRITE_IO_REG_VAL':
            Mem_Instruction = 17   # MEM_A_5bit maps directly to SRAM I/O space
            Read_Write = 1         # write opp
            InputSelect_Memory = 2 # 2 = INPUT_RESL (Latched ALU Result)
            next_state = 'WAIT_WRITE_IO_REG_VAL'

        elif state == 'WAIT_WRITE_IO_REG_VAL':
            Mem_Instruction = 17
            Read_Write = 1
            InputSelect_Memory = 2
            if resp:
                done = 1
                next_state = 'STOP'

        # ================================================================
        # Drive all outputs
        # ================================================================
        self.LoadSelectMux.prepare(LoadSelectMux)
        self.LoadingMux.prepare(LoadingMux)
        self.InputSelectMemory.prepare(InputSelect_Memory)
        self.WEMEMORY.prepare(WE_Memory)
        self.Read_Write.prepare(Read_Write)
        self.Mem_Instruction.prepare(Mem_Instruction)
        self.IncDec.prepare(IncDec)
        
        self.InputSelectBuffer.prepare(InputSelect_Buffer)
        self.WEBUFFER.prepare(WE_Buffer)

        self.Load_Z.prepare(Load_Z)
        self.Load_K.prepare(Load_K)
        self.Load_Jump.prepare(Load_Jump)
        self.relative_Absolute.prepare(relative_Absolute)
        self.Load_Byte.prepare(Load_Byte)
        self.Fetch_Address.prepare(Fetch_Address)
        self.K_Select.prepare(K_select)

        self.done.prepare(done)
        self.WB_Addr.prepare(WB_Addr)


        # --- AI-Friendly State & I/O Trace ---
        if self.debug == 1:
            state_log = (
                f"OPP_TRACE | State: {self.current_state:30} -> {next_state:30} | Inst: {i:03}\n"
                f"  [Memory]   MemInstr: {Mem_Instruction:<2} | RW: {Read_Write} | InputSel: {InputSelect_Memory:<2} | WE: {WE_Memory} | LoadMux: {LoadingMux:<2} | IncDec: {IncDec} | WB_Addr: {WB_Addr:<2}\n"
                f"  [Buffer]   InputSel: {InputSelect_Buffer}  | WE: {WE_Buffer}\n"
                f"  [ROM/Ctrl] FetchAddr: {Fetch_Address} | LoadZ: {Load_Z} | LoadK: {Load_K} | LoadJmp: {Load_Jump} | RelAbs: {relative_Absolute} | LoadByte: {Load_Byte}\n"
                f"  [Status]   Resp: {resp} | Done: {done}"
            )
            print(state_log)

        # Advance state
        self.current_state = next_state