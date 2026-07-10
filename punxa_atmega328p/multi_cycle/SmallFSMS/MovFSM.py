import py4hw

# Add the specific opcode(s) for MOVW to this set if your decoder uses them.
_MOVW = { 45 } 

STATES = [
    'STOP',
    
    # FOR MOV (and Byte 1 of MOVW)
    'FETCH_RR', 'WAIT_FETCH_RR',
    'LOAD_IN_RD', 'WAIT_LOAD_IN_RD',

    # FOR MOVW (Byte 2)
    'FETCH_RR_B2', 'WAIT_FETCH_RR_B2',
    'LOAD_IN_RD_B2', 'WAIT_LOAD_IN_RD_B2',
]


class MOV_FSM(py4hw.Logic):
    def __init__(self, parent, name,
                 # ── Logic inputs ────────────────────────────────────────
                 run, # 1-Bit The main FSM pulls this to high to trigger this FSM
                 done, # 1-Bit The main FSM recives this to high to indicate that this FSM has finished
                 # ── Inputs ──────────────────────────────────────────────
                 Instruction,        # 8-bit opcode from instruction decoder
                 Resp,               # 1-bit: memory operation Finished
                 Branch,             # 1-bit: ALU branch condition met
                 Executed_Jump,      # This tell the controll box that the romHandler has successfully executed the jump instrution and it is ready to load the next instruction

                 # ── Memory Interface Outputs ─────────────────────────────
                 LoadSelectMux,      # address mux for memory reads
                 LoadingMux,         # selects which pointer reg is loaded
                 InputSelectMemory,  # data source mux for memory writes
                 WEMEMORY,           # write enable for pointer registers
                 Read_Write,         # 0=read, 1=write
                 Mem_Instruction,    # pointer selection for Mem_instruction in MemoryInterface
                 IncDec,             # This icrement or Decrements address

                 # ── ALU Buffer Outputs ───────────────────────────────────
                 InputSelectBuffer,  # 1 = Load Data in to Rr0 , 0 = Load K in to Rr0
                 WEBUFFER,           # 1 = Rd0, 2 = Rd1, 3 = Rr0, 4 = Rr1, 5 = IOBuffer

                 # ── ROM Handler Outputs ──────────────────────────────────
                 Load_Z,             # load Z pointer from program memory
                 Load_K,             # load immediate K to rom loader for relative or absolute jump
                 Load_Jump,          # trigger PC jump
                 relative_Absolute,  # 0=relative, 1=absolute jump
                 Load_Byte,          # 0 = fetches form rom  1 = writes to rom
                 Fetch_next_instruction, # If set to 1 fetches the next instruction it has to be set back to 0 and then to one for the next instruction to be fetched
                 Fetch_Address,      # In the case of STS instruction to fetch the instruction address
                 LOAD_PCL,
                 LOAD_PCH,

                 # ── Write-back address ───────────────────────────────────
                 WB_Addr,            # 5-bit explicit write-back address (for Rd+1, R0, R1 in MUL, etc.)
                 ):
        super().__init__(parent, name)


        # ── Logic inputs ────────────────────────────────────────
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
        self.InputSelectMemory= self.addOut('InputSelectMemory',InputSelectMemory)
        self.WEMEMORY         = self.addOut('WEMEMORY',         WEMEMORY)
        self.Read_Write       = self.addOut('Read_Write',       Read_Write)
        self.Mem_Instruction  = self.addOut('Mem_Instruction',  Mem_Instruction)
        self.IncDec           = self.addOut('IncDec',           IncDec)

        self.InputSelectBuffer= self.addOut('InputSelectBuffer',InputSelectBuffer)
        self.WEBUFFER         = self.addOut('WEBUFFER',         WEBUFFER)

        self.Load_Z           = self.addOut('Load_Z',           Load_Z)
        self.Load_K           = self.addOut('Load_K',           Load_K)
        self.Load_Jump        = self.addOut('Load_Jump',        Load_Jump)
        self.relative_Absolute= self.addOut('relative_Absolute',relative_Absolute)
        self.Load_Byte        = self.addOut('Load_Byte',        Load_Byte)
        self.Fetch_next_instruction = self.addOut('Fetch_next_instruction', Fetch_next_instruction)
        self.WB_Addr          = self.addOut('WB_Addr',          WB_Addr)
        self.Fetch_Address    = self.addOut('Fetch_Address',    Fetch_Address)

        self.LOAD_PCL = self.addOut('LOAD_PCL',LOAD_PCL)
        self.LOAD_PCH = self.addOut('LOAD_PCH',LOAD_PCH)


        # ── FSM state ────────────────────────────────────────────────────
        self.current_state = 'STOP'
        # Remember the instruction across multi-cycle sequences
        self._latched_inst = 0
        self.debug = 0


    def clock(self):
        inst              = self.Instruction.get()
        resp              = self.Resp.get()
        branch            = self.Branch.get()
        executed_jump     = self.Executed_Jump.get()
        run               = self.run.get()

        #--- Instruction Buffers ----
        InputSelect_Buffer=0       
        WE_Buffer=0
        LoadSelectMux=0 
        LoadingMux=0

        # --- MemoryInterfaceHandler ---
        Read_Write=0
        Mem_Instruction=0
        IncDec=0
        InputSelect_Memory=0
        WE_Memory=0
        WB_Addr=0

        # --- RomHandler ---
        Load_Z=0
        Load_K=0
        Load_Jump=0
        relative_Absolute=0
        Load_Byte=0
        Fetch_Address=0

        # --- FSM_Control ---
        done = 0

        state = self.current_state
        next_state = state           # default: stay

        if state == 'STOP' and run:
            self._latched_inst = inst

        i = self._latched_inst       # use latched opcode during multi-cycle seqs

        # ================================================================
        # STATE MACHINE
        # ================================================================

        if state == 'STOP':
            if run == 1: 
                next_state = 'FETCH_RR'
                
        # ------------------------------------------------
        # READ FROM SOURCE REGISTER (Rr)
        # ------------------------------------------------
        elif state == 'FETCH_RR':
            Mem_Instruction = 13     # MEM_RR pointer[cite: 3]
            Read_Write  = 2          # 2 = Read operation[cite: 1]
            InputSelect_Memory = 1   # Fetching value from DataBus[cite: 3]
            next_state = 'WAIT_FETCH_RR'

        elif state == 'WAIT_FETCH_RR':
            Mem_Instruction = 13
            Read_Write  = 2
            InputSelect_Memory = 1
            if resp == 1:
                # Value fetched from Rr is ready on the DataBus.
                WE_Memory = 1        # Latch data into memory handler[cite: 1]
                LoadingMux = 14      # Select LOAD_RD_BUFFER to store it safely[cite: 1, 3]
                next_state = 'LOAD_IN_RD'

        # ------------------------------------------------
        # WRITE TO DESTINATION REGISTER (Rd)
        # ------------------------------------------------
        elif state == 'LOAD_IN_RD':
            Mem_Instruction = 12     # MEM_RD pointer[cite: 3]
            Read_Write  = 1          # 1 = Write operation[cite: 1]
            InputSelect_Memory = 16  # Use INPUT_RD_BUFFER as data source[cite: 1, 3]
            next_state = 'WAIT_LOAD_IN_RD'

        elif state == 'WAIT_LOAD_IN_RD':
            Mem_Instruction = 12
            Read_Write  = 1
            InputSelect_Memory = 16
            if resp == 1:
                # If the instruction is MOVW, move to the second byte logic
                if i in _MOVW:
                    next_state = 'FETCH_RR_B2'
                else:
                    next_state = 'STOP'
                    done = 1

        # ------------------------------------------------
        # MOVW: READ SECOND BYTE FROM SOURCE (Rr+1)
        # ------------------------------------------------
        elif state == 'FETCH_RR_B2':
            Mem_Instruction = 16     # MEM_RR_1 pointer (Rr+1)[cite: 3]
            Read_Write  = 2          
            InputSelect_Memory = 1   
            next_state = 'WAIT_FETCH_RR_B2'

        elif state == 'WAIT_FETCH_RR_B2':
            Mem_Instruction = 16
            Read_Write  = 2
            InputSelect_Memory = 1
            if resp == 1:
                WE_Memory = 1        
                LoadingMux = 14      # Latch the second byte into LOAD_RD_BUFFER[cite: 3]
                next_state = 'LOAD_IN_RD_B2'

        # ------------------------------------------------
        # MOVW: WRITE SECOND BYTE TO DESTINATION (Rd+1)
        # ------------------------------------------------
        elif state == 'LOAD_IN_RD_B2':
            Mem_Instruction = 15     # MEM_RD_1 pointer (Rd+1)[cite: 3]
            Read_Write  = 1          
            InputSelect_Memory = 16  
            next_state = 'WAIT_LOAD_IN_RD_B2'

        elif state == 'WAIT_LOAD_IN_RD_B2':
            Mem_Instruction = 15
            Read_Write  = 1
            InputSelect_Memory = 16
            if resp == 1:
                next_state = 'STOP'
                done = 1


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
        if self.debug and (self.current_state != 'STOP'):
            state_log = (
                f"MOV_TRACE  | "
                f"State: {self.current_state:18} -> {next_state:18} | "
                f"MemInstr: {Mem_Instruction:<2} RW: {Read_Write} | "
                f"Resp: {resp} Done: {done}"
            )
            print(state_log)

        # Advance state
        self.current_state = next_state