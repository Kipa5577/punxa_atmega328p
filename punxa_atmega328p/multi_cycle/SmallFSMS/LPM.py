import py4hw


STATES = [
    'STOP',
    'FETCH_RD','WAIT_FETCH_RD',
    'LOAD_IN_RR','WAIT_LOAD_IN_RR',
]


class MOV_FSM(py4hw.Logic):
    def __init__(self, parent, name,
                 # ── Logic imputs─────────────────────────────────────────
                 run, # 1-Bit The main FSM pulls this to high to trigger this FSM
                 done, # 1-Bit The main FSM recives this to high to indicate that this FSM has finished
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
                 Mem_Instruction,    # pointer selection for Mem_instruction in MemoryInterface
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
                 Fetch_Address, # In the case of STS instruction to fetch the instruction address
                 # Fethc_next_instruction is also used to rest the outputs of the instruction decoder and to tell it to expect a new instruction
                 # The instruction decoder also recives the instruction_fetched signal form the romHandler to tell it that it has a new instrucion in its entrance.

                 # ── Write-back address ───────────────────────────────────
                 WB_Addr,            # 5-bit explicit write-back address (for Rd+1, R0, R1 in MUL, etc.)
                 ):
        super().__init__(parent, name)


        # ── Logic imputs─────────────────────────────────────────
        self.run                   = self.addIn('Run',run) 
        self.done                  = self.addIn('Done',done)
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
        self.Mem_Instruction      = self.addOut('Mem_Instruction',      Mem_Instruction)
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
        self.Fetch_Address    = self.addOut('Fetch_Address',Fetch_Address)

        # ── FSM state ────────────────────────────────────────────────────
        self.current_state = 'DECODE_INSTRUCTION'
        # Remember the instruction across multi-cycle sequences
        self._latched_inst = 0
        # Explicit write-back address used when Address_XYZ == MEM_WB_ADDR
        self._wb_addr_val = 0


    def clock(self):
        inst              = self.Instruction.get()
        resp              = self.Resp.get()
        branch            = self.Branch.get()
        skip              = self.Skip.get()
        irq               = self.Interrupt.get()
        instr_fetched     = self.Instruction_fetched.get()
        instr_decoded     = self.Instruction_decoded.get()
        executed_jump     = self.Executed_Jump.get()
        run               = self.run.get()

        InputSelect_Memory=0
        InputSelect_Buffer=0
        NotExecute=0
        LoadSelectMux=0
        LoadingMux=0
        Input_Select=0
        WE=0
        Read_Write=0   
        Mem_Instruction=0
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
        Fetch_Address=0
        WB_Addr=self._wb_addr_val
        done = 0 

        state = self.current_state
        i     = self._latched_inst   # use latched opcode during multi-cycle seqs
        next_state = state           # default: stay

        # ================================================================
        # STATE MACHINE
        # ================================================================

        if state == 'STOP':
            if run == 1: 
                state = 'FETCH_RD'
                
        elif state == 'FETCH_RD':
            Mem_Instruction = 12 # RD pointer
            Read_Write  = 0 # read opp 
            Input_Select= 1 # Fetching value form dataBus
            state = 'WAIT_FETCH_RD'

        elif state == 'WAIT_FETCH_RD':
            if resp == 1:
                state = 'LOAD_IN_RR'

        elif state == 'LOAD_IN_RR':
            Mem_Instruction = 13 # RR pointer
            Read_Write  = 1 # Write opp

        elif state == 'WAIT_LOAD_IN_RR':
            if resp == 1:
                state = 'STOP'
                done = 1

        # ================================================================
        # Drive all outputs
        # ================================================================
        self.NotExecute.prepare(NotExecute)
        self.LoadSelectMux.prepare(LoadSelectMux)
        self.LoadingMux.prepare(LoadingMux)
        self.Input_Select.prepare(Input_Select)
        self.WE.prepare(WE)
        self.Read_Write.prepare(Read_Write)
        self.Mem_Instruction.prepare(Mem_Instruction)
        self.IncDec.prepare(IncDec)

        if write_RdL_Buffer:
            self.write_Opperand_Buffer.prepare(1)   # 1=A0
        elif write_RdH_Buffer:
            self.write_Opperand_Buffer.prepare(2)   # 2=A1
        elif write_RrL_Buffer:
            self.write_Opperand_Buffer.prepare(3)   # 3=B0
        elif write_RrH_Buffer:
            self.write_Opperand_Buffer.prepare(4)   # 4=B1
        else:
            self.write_Opperand_Buffer.prepare(0)

        self.InputSelect.prepare(InputSelect)
        self.Write_Enable.prepare(Write_Enable)

        self.Load_Z.prepare(Load_Z)
        self.Load_K.prepare(Load_K)
        self.Load_Jump.prepare(Load_Jump)
        self.relative_Absolute.prepare(relative_Absolute)
        self.Load_Byte.prepare(Load_Byte)
        self.Fetch_next_instruction.prepare(Fetch_next_instruction)
        self.Fetch_Address.prepare(Fetch_Address)

        self.done.prepare(done)
        # Drive the explicit write-back address (used by MEM_WB_ADDR mode)
        self.WB_Addr.prepare(WB_Addr)

        # Advance state
        self.current_state = next_state

