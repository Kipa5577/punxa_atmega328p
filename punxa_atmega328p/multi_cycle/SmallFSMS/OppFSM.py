import py4hw

# Rd ← op(Rd, K)  — one register + 8-bit immediate
_RD_K_ALU_WRITE = {
    5,   # SUBI
    6,   # SBC
    7,   # SBCI
    10,  # ANDI
    12,  # ORI
    16,  # SBR  (= ORI)
    17,  # CBR  (= ANDI with ~K)
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

# op(Rd, Rr)  — compare / test, no write-back to register file
_RD_RR_NO_WRITE = {
    38,  # CP
    39,  # CPC
    37,  # CPSE   (also generates a skip if equal — handled in EXECUTE_ALU_OPP)
    75,  # BST    (stores bit from Rd into T flag only)
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
        self.debug = 1

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
                elif i in {41, 42}:          # SBRC / SBRS — operand decodes into Rr, not Rd
                    next_state = 'FETCH_RR'
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
                # 41, 42 removed — SBRC/SBRS no longer routed through here
                elif i in {43, 44}:               # SBIC / SBIS
                    next_state = 'FETCH_IO_REG_VAL'
                else:
                    next_state = 'FETCH_RR'

        # ================================================================
        # FETCH RD BYTE 1
        # ================================================================

        elif state == 'FETCH_RD_B2':
            Mem_Instruction = 15 # RD+1 pointer
            Read_Write  = 2 # read opp 
            InputSelect_Memory = 1 # FIX: Matched variable name
            next_state = 'WAIT_FETCH_RD_B2'

        elif state == 'WAIT_FETCH_RD_B2':
            if resp:
                next_state = 'LOAD_VAL_RD_IN_BUFFER_B2'

        elif state == 'LOAD_VAL_RD_IN_BUFFER_B2':
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
            WE_Buffer = 5     # write DATA into IOBuffer

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

            # Everything else writes a single byte
            else:
                next_state = 'LOAD_RESULT'

        # ================================================================
        # WRITE RESULT BYTE 0
        # ================================================================

        elif state == 'LOAD_RESULT':
            Mem_Instruction = 12 # RD pointer
            Read_Write = 1 # Write 
            InputSelect_Memory = 2 
            next_state = 'WAIT_LOAD_RESULT'

        elif state == 'WAIT_LOAD_RESULT':
            Mem_Instruction = 12
            Read_Write = 1
            InputSelect_Memory = 2
            if resp:
                if i in {23,24,25,26,27,28}:
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
            Mem_Instruction = 15 # RD+1 pointer
            Read_Write = 1 # Write 
            InputSelect_Memory = 2 
            next_state = 'WAIT_LOAD_RESULT_B2'

        elif state == 'WAIT_LOAD_RESULT_B2':
            Mem_Instruction = 15 
            Read_Write = 1       # Write 
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

        self.done.prepare(done)
        self.WB_Addr.prepare(WB_Addr)


        # --- AI-Friendly State & I/O Trace ---
        if self.debug == 1:
            state_log = (
                f"OPP_TRACE | "
                f"State: {self.current_state} -> {next_state} | "
                f"Inst: {i:03} | "
                f"MemInstr: {Mem_Instruction} WE_Buf: {WE_Buffer} | "
                f"Resp: {resp} Done: {done}"
            )
            print(state_log)

        # Advance state
        self.current_state = next_state