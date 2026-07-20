import py4hw

STATES = [
    'STOP',

    # NOTE: SP lives permanently inside MemoryInterfaceHandler (self.SPL/self.SPH),
    # the same way CallRetFSM's CALL/RCALL/RET paths use it. Mem_Instruction=7
    # (MEM_SP) reads/writes through the resident SP register directly and
    # updatePointer() adjusts it in the same cycle the access is issued - there
    # is no separate SRAM-mapped copy at 0x5D/0x5E to fetch into a buffer or
    # write back afterwards. The old FETCH_STACK_POINTER_*/LOAD_STACK_POINTER_*
    # dance has been removed (it was reading/writing the wrong address anyway -
    # MEM_WB_ADDR masks its address to 5 bits, so 0x5D/0x5E aliased onto
    # unrelated register cells 0x1D/0x1E and clobbered SP with garbage).

    # Pop part
    'FETCH_FROM_STACK_POINTER','WAIT_FETCH_FROM_STACK_POINTER',
    'LOAD_VALUE_TO_RD','WAIT_LOAD_VALUE_TO_RD',

    # Push Part
    'FETCH_RD','WAIT_FETCH_RD',
    'LOAD_VALUE_TO_STACK','WAIT_LOAD_VALUE_TO_STACK',
]


class PopPush_FSM(py4hw.Logic):
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
                 LOAD_PCL,
                 LOAD_PCH,
                 # Fethc_next_instruction is also used to rest the outputs of the instruction decoder and to tell it to expect a new instruction
                 # The instruction decoder also recives the instruction_fetched signal form the romHandler to tell it that it has a new instrucion in its entrance.

                 # ── Write-back address ───────────────────────────────────
                 WB_Addr,            # 5-bit explicit write-back address (for Rd+1, R0, R1 in MUL, etc.)
                                  reset=None,
             ):
        super().__init__(parent, name)
        self.reset = self.addIn('reset', reset) if reset is not None else None


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
        self._wb_addr_val = 0

        # Remember whether the pointer used a post-increment / pre-decrement
        # addressing mode and therefore needs the updated value written
        # back to its SRAM-mapped register (R26-R31) once the access
        # sequence completes.
        self._pointer_update_pending = False
        self.debug = 1


    def clock(self):
        if self.reset is not None and self.reset.get():
            self.current_state = 'STOP'
            self.done.prepare(0)
            self.LoadSelectMux.prepare(0)
            self.LoadingMux.prepare(0)
            self.InputSelectMemory.prepare(0)
            self.WEMEMORY.prepare(0)
            self.Read_Write.prepare(0)
            self.Mem_Instruction.prepare(0)
            self.IncDec.prepare(0)
            self.InputSelectBuffer.prepare(0)
            self.WEBUFFER.prepare(0)
            self.Load_Z.prepare(0)
            self.Load_K.prepare(0)
            self.Load_Jump.prepare(0)
            self.relative_Absolute.prepare(0)
            self.Load_Byte.prepare(0)
            self.Fetch_next_instruction.prepare(0)
            self.WB_Addr.prepare(0)
            self.Fetch_Address.prepare(0)
            self.LOAD_PCL.prepare(0)
            self.LOAD_PCH.prepare(0)
            return

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

        if state == 'STOP' and run:
            self._latched_inst = inst
            i = self._latched_inst

        # ================================================================
        # STATE MACHINE
        # ================================================================

        if state == 'STOP':
            if run:
                if i == 127:                 # POP
                    next_state = 'FETCH_FROM_STACK_POINTER'
                else:                         # PUSH
                    next_state = 'FETCH_RD'


        # ------------------------------------------------
        # POP  (SP++ then read [SP] - matches RET's pre-increment convention)
        # ------------------------------------------------

        elif state == 'FETCH_FROM_STACK_POINTER':
            Mem_Instruction = 7              # MEM_SP (resident SPL/SPH)
            Read_Write = 2                   # read SRAM
            IncDec = 4                       # pre-increment, issued ONCE
            next_state = 'WAIT_FETCH_FROM_STACK_POINTER'

        elif state == 'WAIT_FETCH_FROM_STACK_POINTER':
            Mem_Instruction = 7
            Read_Write = 2
            IncDec = 0                       # hold steady while waiting for resp

            if resp:
                WE_Memory = 1                # Latch data from SRAM into RdBuffer
                LoadingMux = 14              # LOAD_RD_BUFFER
                next_state = 'LOAD_VALUE_TO_RD'

        elif state == 'LOAD_VALUE_TO_RD':
            Mem_Instruction = 12             # MEM_RD
            Read_Write = 1                   # Write to Rd
            InputSelect_Memory = 16          # INPUT_RD_BUFFER
            next_state = 'WAIT_LOAD_VALUE_TO_RD'

        elif state == 'WAIT_LOAD_VALUE_TO_RD':
            Mem_Instruction = 12
            Read_Write = 1
            InputSelect_Memory = 16
            if resp:
                done = 1
                next_state = 'STOP'


        # ------------------------------------------------
        # PUSH  (write [SP] then SP-- - matches RCALL/CALL's post-decrement convention)
        # ------------------------------------------------

        elif state == 'FETCH_RD':
            Mem_Instruction = 12             # MEM_RD
            Read_Write = 2                   # read Rd
            next_state = 'WAIT_FETCH_RD'

        elif state == 'WAIT_FETCH_RD':
            Mem_Instruction = 12
            Read_Write = 2

            if resp:
                WE_Memory = 1                # Latch Rd value into RdBuffer
                LoadingMux = 14              # LOAD_RD_BUFFER
                next_state = 'LOAD_VALUE_TO_STACK'

        elif state == 'LOAD_VALUE_TO_STACK':
            Mem_Instruction = 7              # MEM_SP (resident SPL/SPH)
            Read_Write = 1                   # write SRAM
            IncDec = 3                       # post-decrement, issued ONCE
            InputSelect_Memory = 16          # INPUT_RD_BUFFER
            next_state = 'WAIT_LOAD_VALUE_TO_STACK'

        elif state == 'WAIT_LOAD_VALUE_TO_STACK':
            Mem_Instruction = 7
            Read_Write = 1
            IncDec = 0                       # hold steady while waiting for resp
            InputSelect_Memory = 16
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
        # Drive the explicit write-back address (used by MEM_WB_ADDR mode)
        self.WB_Addr.prepare(self._wb_addr_val)

        # --- AI-Friendly State & I/O Trace ---
        if self.debug and (self.current_state != 'STOP'):
            state_log = (
                f"POPPUSH_TRACE | "
                f"State: {self.current_state} -> {next_state} | "
                f"Run: {run} Resp: {resp} | "
                f"MemInstr: {Mem_Instruction} RW: {Read_Write} IncDec: {IncDec} | "
                f"Done: {done}"
            )
            print(state_log)
        
        # Advance state
        self.current_state = next_state