import py4hw




STATES = [
    'STOP',
    # READ STACK POINTER
    'FETCH_STACK_POINTER_BEGIN_L','FETCH_STACK_POINTER_BEGIN_L','LOAD_STACK_POINTER_L_IN_BUFFER' 
    'FETCH_STACK_POINTER_BEGIN_H','FETCH_STACK_POINTER_BEGIN_H','LOAD_STACK_POINTER_H_IN_BUFFER'

    # HANDLE PC RETURN VALUE INCREMENTATION
    'INCREMENT_STORED_PC'

    #LOAD_PC TO MEMORY
    'READ_L_BYTE_OF_PC','LOAD_L_BYTE_OF_PC_TO_STACK',
    'READ_H_BYTE_OF_PC','LOAD_H_BYTE_OF_PC_TO_STACK',

    # JUMP_PART RCALL
    'FETCH_K_OFFSET','WAIT_K_OFFSET',
    'JUMP_R',

    #JUMP_PART ICALL
    'FETCH_ADDRESS_Z_L','WAIT_FETCH_ADDRESS_Z_L',
    'FETCH_ADDRESS_Z_H','WAIT_FETCH_ADDRESS_Z_H',
    'JUMP_I',

    #JUMP_PART CALL
    'FETCH_ADDRESS_BYTE','WAIT_ADDRESS_RECONSTRUCTION',
    'JUMP'

    #JUMP BACK RET
    'FETCH_L_BYTE_OF_PC','WAIT_FETCH_L_BYTE_OF_PC','STORE_L_BYTE_OF_PC'
    'FETCH_L_BYTE_OF_PC','WAIT_FETCH_L_BYTE_OF_PC','STORE_L_BYTE_OF_PC'

    # 
    'LOAD_STACK_POINTER_BEGIN_L','LOAD_STACK_POINTER_WAIT_L',
    'LOAD_STACK_POINTER_BEGIN_H','LOAD_STACK_POINTER_WAIT_H',
]


class CallRet_FSM(py4hw.Logic):
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
                 Fetch_Address, # In the case of STS instruction to fetch the instruction address
                 JumpWidth,
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

        self.JumpWidth = self.addOut('JumpWidth',JumpWidth)
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

        # --- MemoryInterfeceHandler ---
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
        i     = self._latched_inst   # use latched opcode during multi-cycle seqs
        next_state = state           # default: stay

        # ================================================================
        # STATE MACHINE
        # ================================================================

        if state == 'STOP':
            if run == 1: 
                next_state = 'FETCH_RD'
                
        elif state == 'FETCH_RD':
            Mem_Instruction = 12 # RD pointer
            Read_Write  = 0 # read opp 
            Input_Select= 1 # Fetching value form dataBus
            next_state = 'WAIT_FETCH_RD'

        elif state == 'WAIT_FETCH_RD':
            if resp == 1:
                next_state = 'LOAD_IN_RR'

        elif state == 'LOAD_IN_RR':
            Mem_Instruction = 13 # RR pointer
            Input_Select= 1 # Fetching value form dataBus
            Read_Write  = 1 # Write opp

        elif state == 'WAIT_LOAD_IN_RR':
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
        # Drive the explicit write-back address (used by MEM_WB_ADDR mode)
        self.WB_Addr.prepare(WB_Addr)

        # Advance state
        print(f"CallRet_FSM_STATE:{self.current_state} -> {next_state}")
        self.current_state = next_state
