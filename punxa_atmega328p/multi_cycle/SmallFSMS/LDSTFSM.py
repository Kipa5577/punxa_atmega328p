import py4hw


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
    #120, # LPM   (load program memory, Z)
    #121, # LPMZ  (LPM r,Z)
    #122, # LPMZ+ (LPM r,Z+)
}



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
    #123, # SPM
}


_X_POINTER = {
    96,  # LDX
    97,  # LDX+
    98,  # LD-X
    108, # STX
    109, # STX+
    110, # ST-X
}

_Y_POINTER = {
    99,  # LDY
    100, # LDY+
    101, # LD-Y
    102, # LDDY  (LDD Y+q)
    111, # STY
    112, # STY+
    113, # ST-Y
    114, # STDY  (STD Y+q)
}

_Z_POINTER = {
    103, # LDZ
    104, # LDZ+
    105, # LD-Z
    106, # LDDZ  (LDD Z+q)
    115, # STZ
    116, # STZ+
    117, # ST-Z
    118, # STDZ  (STD Z+q)
}

# I/O space
_IO_READ  = {124}  # IN  Rd, A
_IO_WRITE = {125}  # OUT A, Rr

# Instructions that access memory/IO directly with NO X/Y/Z pointer at all:
# LDS/STS use a 16-bit address word fetched straight from ROM; IN/OUT use
# the 6-bit I/O address field. None of these touch XregL/H, YregL/H, or
# ZregL/H, so they must skip the entire FETCH_ADDRESS_XYZ_* preamble
# (and its rewrite-back counterpart) entirely rather than walking through
# it with a meaningless WB_Addr of 0.
_NO_POINTER = {107, 119, 124, 125}   # LDS, STS, IN, OUT

# LDI Rd, K — plain immediate load, no X/Y/Z pointer involved at all.
# K arrives on the dedicated K_val_Input / INPUT_GENERAL (4) data path in
# MemoryInterfaceHandler, so no staging buffer is needed: LDI writes K to
# Rd directly in one write state, entered straight from STOP, bypassing
# the FETCH_ADDRESS_XYZ_* preamble entirely since LDI has no pointer.
_LDI = {95}

STATES = [
    'STOP',

    # Getting the address ALWAYS EXECUTED (skipped entirely for LDI)
    'FETCH_ADDRESS_XYZ_BEGIN_L', 'WAIT_FETCH_ADDRESS_XYZ_L', 'LOAD_ADDRESS_XYZ_L_IN_BUFFER',
    'SETTLE_XYZ_H',
    'FETCH_ADDRESS_XYZ_BEGIN_H', 'WAIT_FETCH_ADDRESS_XYZ_H', 'LOAD_ADDRESS_XYZ_H_IN_BUFFER',

    # LDI – Rd <- K (immediate), enters here directly from STOP
    'LOAD_K_TO_RD', 'WAIT_LOAD_K_TO_RD',

    # LOAD 
    'FETCH_ADDRESS_XYZ_POINTER', 'WAIT_ADDRESS_XYZ_POINTER',
    'LOAD_VALUE_TO_RD', 'WAIT_LOAD_VALUE_TO_RD',


    # STORE
    'FETCH_VALUE_OF_RD', 'WAIT_FETCH_VALUE_OF_RD',
    # FIX: dedicated state to latch Rr value into RdBuffer BEFORE fetching ROM address.
    # Previously LoadingMux=14 was incorrectly driven during FETCH/WAIT_ADDRESS_FROM_ROM,
    # where BusData holds ROM-fetch results rather than the register value.
    'LATCH_RD_TO_BUFFER',
    'LOAD_VALUE_TO_MEMORY', 'WAIT_LOAD_VALUE_TO_MEMORY',


    # STORE in case of STS (direct addressing, write side)
    'FETCH_ADDRESS_FROM_ROM', 'WAIT_FETCH_ADDRESS_FROM_ROM', 'LOAD_ADDRESS_TO_MEMORY_HANDLER',

    # LOAD in case of LDS (direct addressing, read side) — mirrors the
    # STS path above but reads SRAM[ROM address] instead of writing it.
    'FETCH_ADDRESS_FROM_ROM_LD', 'WAIT_FETCH_ADDRESS_FROM_ROM_LD',
    'LOAD_FROM_ROM_ADDR_TO_RD', 'WAIT_LOAD_FROM_ROM_ADDR_TO_RD',


    # IO IN
    'FETCH_VALUE_OF_A', 'WAIT_FETCH_VALUE_OF_A',
    # Reuse of these states 'LOAD_VALUE_TO_RD','WAIT_LOAD_VALUE_TO_RD',


    # IO OUT
    # Reuse of these states 'FETCH_VALUE_OF_RD','WAIT_FETCH_VALUE_OF_RD'
    'FETCH_VALUE_TO_A', 'WAIT_FETCH_VALUE_TO_A',


    # Rewriting the address ALWAYS EXECUTED
    'LOAD_ADDRESS_XYZ_BEGIN_L', 'LOAD_ADDRESS_XYZ_WAIT_L',
    'LOAD_ADDRESS_XYZ_BEGIN_H', 'LOAD_ADDRESS_XYZ_WAIT_H',
]


class LDST_FSM(py4hw.Logic):
    def __init__(self, parent, name,
                 # ── Logic imputs─────────────────────────────────────────
                 run, # 1-Bit The main FSM pulls this to high to trigger this FSM
                 done, # 1-Bit The main FSM recives this to high to indicate that this FSM has finished
                 # ── Inputs ──────────────────────────────────────────────
                 Instruction,        # 8-bit opcode from instruction decoder
                 Resp,               # 1-bit: memory operation Finished
                 Address_fetched,    # 1-bit: romHandler Fetched address
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
                 ):
        super().__init__(parent, name)


        # ── Logic imputs─────────────────────────────────────────
        self.run                   = self.addIn('Run',run)
        self.done                  = self.addOut('Done',done)
        # ── Register inputs ──────────────────────────────────────────────
        self.Instruction           = self.addIn('Instruction', Instruction)
        self.Resp                  = self.addIn('Resp', Resp)
        self.Branch                = self.addIn('Branch', Branch)
        self.Executed_Jump         = self.addIn('Executed_Jump', Executed_Jump)

        # ── Register outputs ─────────────────────────────────────────────
        self.LoadSelectMux    = self.addOut('LoadSelectMux', LoadSelectMux)
        self.LoadingMux       = self.addOut('LoadingMux', LoadingMux)
        self.InputSelectMemory     = self.addOut('InputSelectMemory', InputSelectMemory)
        self.WEMEMORY         = self.addOut('WEMEMORY', WEMEMORY)
        self.Read_Write       = self.addOut('Read_Write', Read_Write)
        self.Mem_Instruction      = self.addOut('Mem_Instruction', Mem_Instruction)
        self.IncDec           = self.addOut('IncDec', IncDec)

        self.InputSelectBuffer =  self.addOut('InputSelectBuffer', InputSelectBuffer)
        self.WEBUFFER         = self.addOut('WEBUFFER', WEBUFFER)

        self.Load_Z           = self.addOut('Load_Z', Load_Z)
        self.Load_K           = self.addOut('Load_K', Load_K)
        self.Load_Jump        = self.addOut('Load_Jump', Load_Jump)
        self.relative_Absolute= self.addOut('relative_Absolute',relative_Absolute)
        self.Load_Byte        = self.addOut('Load_Byte', Load_Byte)
        self.Fetch_next_instruction= self.addOut('Fetch_next_instruction', Fetch_next_instruction)
        self.WB_Addr          = self.addOut('WB_Addr', WB_Addr)
        self.Fetch_Address    = self.addOut('Fetch_Address',Fetch_Address)

        self.LOAD_PCL = self.addOut('LOAD_PCL',LOAD_PCL)
        self.LOAD_PCH = self.addOut('LOAD_PCH',LOAD_PCH)
        self.Address_fetched  = self.addIn('Address_fetched', Address_fetched)


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
        # Edge-detect flag for the high-byte pointer read (FETCH/WAIT_
        # ADDRESS_XYZ_H): set once we've genuinely observed Resp go low
        # during THIS read, so a subsequent Resp=1 can be trusted as this
        # read's real completion rather than a stale Resp=1 left over
        # from the low-byte read that ran immediately beforehand.
        self._h_saw_resp_low = False
        # Deferred post-increment flag for LD X+/Y+/Z+ (applied only once
        # the pointer read completes, so the address stays stable during
        # the access), and the Mem_Instruction held during that read.
        self._deferred_post_inc = False
        self._ptr_mem_instruction = 0
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
        next_state = state           # default: stay

        # Latch the instruction the moment we leave STOP, so the rest of
        # the (multi-cycle) sequence keeps working on the same opcode even
        # if `Instruction` changes underneath us mid-sequence.
        if state == 'STOP' and run:
            self._latched_inst = inst

        i = self._latched_inst   # use latched opcode during multi-cycle seqs

        # ================================================================
        # STATE MACHINE
        # ================================================================


        if state == 'STOP':
            if run:
                if inst in _LDI:
                    next_state = 'LOAD_K_TO_RD'
                elif inst in _NO_POINTER:
                    # LDS / STS / IN / OUT have no X/Y/Z pointer at all —
                    # skip the FETCH_ADDRESS_XYZ_* preamble entirely and
                    # go straight to the right entry point for each.
                    if inst == 107:        # LDS (direct read)
                        next_state = 'FETCH_ADDRESS_FROM_ROM_LD'
                    elif inst == 119:       # STS (direct write)
                        next_state = 'FETCH_VALUE_OF_RD'
                    elif inst in _IO_READ:  # IN
                        next_state = 'FETCH_VALUE_OF_A'
                    elif inst in _IO_WRITE: # OUT
                        next_state = 'FETCH_VALUE_OF_RD'
                else:
                    next_state = 'FETCH_ADDRESS_XYZ_BEGIN_L'


        # ------------------------------------------------
        # FETCH ADDRESS XYZ LOW
        # ------------------------------------------------
        # X/Y/Z are register-file pointers mapped into SRAM at the
        # standard AVR addresses (X=R26:R27, Y=R28:R29, Z=R30:R31), so
        # their bytes are read/written through MEM_WB_ADDR + WB_Addr,
        # exactly like any other general-purpose register.

        elif state == 'FETCH_ADDRESS_XYZ_BEGIN_L':

            if inst in _X_POINTER:
                self._wb_addr_val = 26
                WB_Addr = 26
            elif inst in _Y_POINTER:
                self._wb_addr_val = 28
                WB_Addr = 28
            elif inst in _Z_POINTER:
                self._wb_addr_val = 30
                WB_Addr = 30

            Mem_Instruction = 14     # MEM_WB_ADDR
            Read_Write = 2 # Read
            InputSelect_Memory = 1   # RECIVE VALUE FROM MEMORY
            next_state = 'WAIT_FETCH_ADDRESS_XYZ_L'

        elif state == 'WAIT_FETCH_ADDRESS_XYZ_L':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 2 # Read
            InputSelect_Memory = 1 # RECIVE VALUE FROM MEMORY
            if resp:
                next_state = 'LOAD_ADDRESS_XYZ_L_IN_BUFFER'

        elif state == 'LOAD_ADDRESS_XYZ_L_IN_BUFFER':
            # Latch the fetched low byte into the internal pointer
            # register inside MemoryInterfaceHandler (XL/YL/ZL) so the
            # handler's own X/Y/Z view stays in sync with the SRAM-mapped
            # register-file copy we just read.
            WE_Memory = 1
            if inst in _X_POINTER:
                LoadingMux = 1   # LOAD_XL
            elif inst in _Y_POINTER:
                LoadingMux = 3   # LOAD_YL
            elif inst in _Z_POINTER:
                LoadingMux = 5   # LOAD_ZL
            next_state = 'SETTLE_XYZ_H'

        # One idle cycle between the low-byte pointer read and the
        # high-byte pointer read. MemoryInterfaceHandler's Resp/bus data
        # for the just-completed low-byte read (WAIT_FETCH_ADDRESS_XYZ_L)
        # is still settling when LOAD_ADDRESS_XYZ_L_IN_BUFFER runs, so
        # starting the new high-byte read (a different WB_Addr) right on
        # its heels would sample stale Resp/bus data left over from the
        # low-byte read instead of waiting for the real high-byte value
        # (e.g. reading ZH would silently latch ZL's value again).
        elif state == 'SETTLE_XYZ_H':
            Mem_Instruction = 0
            Read_Write = 0
            InputSelect_Memory = 0
            next_state = 'FETCH_ADDRESS_XYZ_BEGIN_H'

        # ------------------------------------------------
        # FETCH ADDRESS XYZ HIGH
        # ------------------------------------------------

        elif state == 'FETCH_ADDRESS_XYZ_BEGIN_H':

            if inst in _X_POINTER:
                self._wb_addr_val = 27
                WB_Addr = 27
            elif inst in _Y_POINTER:
                self._wb_addr_val = 29
                WB_Addr = 29
            elif inst in _Z_POINTER:
                self._wb_addr_val = 31
                WB_Addr = 31

            Mem_Instruction = 14     # MEM_WB_ADDR
            Read_Write = 2 # Read
            InputSelect_Memory = 1 # RECIVE VALUE FROM MEMORY
            # Reset the edge-detect flag: this is a brand new read, so any
            # Resp=1 sampled before we've seen Resp go low again must be
            # discarded as a holdover from the low-byte read.
            self._h_saw_resp_low = False
            next_state = 'WAIT_FETCH_ADDRESS_XYZ_H'

        elif state == 'WAIT_FETCH_ADDRESS_XYZ_H':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 2 # Read
            InputSelect_Memory = 1 # RECIVE VALUE FROM MEMORY
            if not resp:
                # Genuinely see Resp deassert for THIS read before trusting
                # a later Resp=1 as its real completion. Without this, a
                # Resp=1 left over from the low-byte read that immediately
                # precedes this high-byte read can look like this read
                # finishing on its very first cycle, latching the low
                # byte's stale bus data as the high byte (e.g. ZH reading
                # back ZL's value).
                self._h_saw_resp_low = True
            elif self._h_saw_resp_low:
                next_state = 'LOAD_ADDRESS_XYZ_H_IN_BUFFER'

        elif state == 'LOAD_ADDRESS_XYZ_H_IN_BUFFER':
            WE_Memory = 1
            if inst in _X_POINTER:
                LoadingMux = 2   # LOAD_XH
            elif inst in _Y_POINTER:
                LoadingMux = 4   # LOAD_YH
            elif inst in _Z_POINTER:
                LoadingMux = 6   # LOAD_ZH

            if i in _LOAD_MEM:
                next_state = 'FETCH_ADDRESS_XYZ_POINTER'

            elif i in _STORE_MEM:
                next_state = 'FETCH_VALUE_OF_RD'

            elif i in _IO_READ:
                next_state = 'FETCH_VALUE_OF_A'

            elif i in _IO_WRITE:
                next_state = 'FETCH_VALUE_OF_RD'

            else:
                next_state = 'STOP'

        # ------------------------------------------------
        # LDI – LOAD IMMEDIATE K INTO Rd
        # ------------------------------------------------
        # No X/Y/Z pointer is involved and no staging buffer is needed:
        # MemoryInterfaceHandler exposes K directly via K_val_Input, selected
        # by InputSelect_Memory = 4 (INPUT_GENERAL). We just point the
        # write at Rd (Mem_Instruction = 12 / MEM_RD) and let that data
        # source flow straight through.

        elif state == 'LOAD_K_TO_RD':
            # Defensively clear any pointer-update flag left over from a
            # prior pointer-based instruction — LDI never uses X/Y/Z and
            # must always fall straight through to done/STOP afterward.
            self._pointer_update_pending = False
            Mem_Instruction = 12     # MEM_RD: address = Rd
            Read_Write = 1           # write opp: SRAM[Rd] <- K
            InputSelect_Memory = 4   # INPUT_GENERAL: K_val_Input
            next_state = 'WAIT_LOAD_K_TO_RD'

        elif state == 'WAIT_LOAD_K_TO_RD':
            Mem_Instruction = 12
            Read_Write = 1
            InputSelect_Memory = 4   # INPUT_GENERAL: K_val_Input
            if resp:
                done = 1
                next_state = 'STOP'

        # ------------------------------------------------
        # LOAD FROM MEMORY
        # ------------------------------------------------

        elif state == 'FETCH_ADDRESS_XYZ_POINTER':

            self._pointer_update_pending = False
            # Post-increment must NOT be applied while the read is still in
            # flight: updatePointer fires the first cycle IncDec is seen,
            # which would change X/Y/Z (and therefore the driven address)
            # mid-read. Defer it to the completion cycle instead.
            self._deferred_post_inc = False
            # Edge-detect reset: this state is entered one cycle after the
            # high-pointer-byte read completed (Resp may still be 1 from
            # it), so any Resp=1 sampled before Resp has gone low again
            # belongs to that previous read and must be ignored.
            self._h_saw_resp_low = False

            if i in _X_POINTER:
                if i == 96:   # LDX
                    Mem_Instruction = 1  # X pointer
                elif i == 97:  # LDX+
                    Mem_Instruction = 1  # X pointer (post-inc deferred)
                    self._deferred_post_inc = True
                    self._pointer_update_pending = True
                elif i == 98:  # LD-X
                    Mem_Instruction = 1  # X pointer
                    IncDec = 2            # PRE DECREMENT (applies once here)
                    self._pointer_update_pending = True

            elif i in _Y_POINTER:
                if i == 99:    # LDY
                    Mem_Instruction = 3  # Y pointer
                elif i == 100:  # LDY+
                    Mem_Instruction = 3  # Y pointer (post-inc deferred)
                    self._deferred_post_inc = True
                    self._pointer_update_pending = True
                elif i == 101:  # LD-Y
                    Mem_Instruction = 3  # Y pointer
                    IncDec = 2            # PRE DECREMENT (applies once here)
                    self._pointer_update_pending = True
                elif i == 102:  # LDDY (LDD Y+q)
                    Mem_Instruction = 10  # MEM_Y_Q

            elif i in _Z_POINTER:
                if i == 103:    # LDZ
                    Mem_Instruction = 5  # Z pointer
                elif i == 104:  # LDZ+
                    Mem_Instruction = 5  # Z pointer (post-inc deferred)
                    self._deferred_post_inc = True
                    self._pointer_update_pending = True
                elif i == 105:  # LD-Z
                    Mem_Instruction = 5  # Z pointer
                    IncDec = 2            # PRE DECREMENT (applies once here)
                    self._pointer_update_pending = True
                elif i == 106:  # LDDZ (LDD Z+q)
                    Mem_Instruction = 11  # MEM_Z_Q

            # Remember which Mem_Instruction to keep driving during the
            # wait so the read address stays stable for the whole access.
            # NOTE: pre-decrement already updated the pointer this cycle,
            # so holding the plain pointer instruction (IncDec=0) during
            # the wait resolves to the same (decremented) address.
            self._ptr_mem_instruction = Mem_Instruction

            Read_Write = 2 # Read
            InputSelect_Memory = 1  # Fetching value from dataBus

            next_state = 'WAIT_ADDRESS_XYZ_POINTER'


        elif state == 'WAIT_ADDRESS_XYZ_POINTER':
            # HOLD the read: keep driving the same pointer address for the
            # entire access. Previously Mem_Instruction fell back to 0
            # here, so the memory interface was actually addressing
            # location 0 while "waiting" — the genuine data at Y+q/Z+q
            # could never arrive.
            Mem_Instruction = self._ptr_mem_instruction
            Read_Write = 2 
            InputSelect_Memory = 1  

            if not resp:
                # Resp genuinely deasserted for THIS read: any later
                # Resp=1 is really ours (see edge-detect note above).
                self._h_saw_resp_low = True
            elif self._h_saw_resp_low:
                WE_Memory = 1            # [FIX]: Latch data into RdBuffer
                LoadingMux = 14          # [FIX]: Select LOAD_RD_BUFFER
                if self._deferred_post_inc:
                    # Apply the post-increment exactly once, now that the
                    # read has completed at the ORIGINAL address.
                    IncDec = 1
                    self._deferred_post_inc = False
                next_state = 'LOAD_VALUE_TO_RD'

        elif state == 'LOAD_VALUE_TO_RD':
            Mem_Instruction = 12 
            Read_Write  = 1 
            InputSelect_Memory = 16      # [FIX]: Use latched RdBuffer (16) instead of DataBus (1)
            next_state = 'WAIT_LOAD_VALUE_TO_RD'

        elif state == 'WAIT_LOAD_VALUE_TO_RD':
            Mem_Instruction = 12     
            Read_Write = 1
            InputSelect_Memory = 16      # [FIX]: Use latched RdBuffer (16)

            if resp:
                if self._pointer_update_pending:
                    next_state = 'LOAD_ADDRESS_XYZ_BEGIN_L'
                else:
                    done = 1
                    next_state = 'STOP'

        # ------------------------------------------------
        # STORE TO MEMORY
        # ------------------------------------------------

        elif state == 'FETCH_VALUE_OF_RD':
            # Reset here (not just in LOAD_VALUE_TO_MEMORY) because STS and
            # OUT enter via this same state directly from STOP, skipping
            # LOAD_VALUE_TO_MEMORY's own reset entirely — without this,
            # a stale True left by a prior post-inc/pre-dec store could
            # incorrectly send STS/OUT into the XYZ rewrite path.
            self._pointer_update_pending = False
            Mem_Instruction = 12     # RD pointer: read the source register
            Read_Write = 2           # read the source register value
            InputSelect_Memory = 1
            # Edge-detect reset: for X/Y/Z pointer stores this state is
            # entered right after the high-pointer-byte read completed
            # (LOAD_ADDRESS_XYZ_H_IN_BUFFER is a single cycle), so the
            # memory interface's registered Resp may still be 1 from that
            # read. Any Resp=1 sampled before we've seen Resp go low again
            # belongs to the previous read and must be ignored, or we'd
            # latch the pointer high byte into RD_BUFFER as the "source
            # register value" and store it to memory.
            self._h_saw_resp_low = False

            next_state = 'WAIT_FETCH_VALUE_OF_RD'

        elif state == 'WAIT_FETCH_VALUE_OF_RD':
            Mem_Instruction = 12
            Read_Write = 2  # Read
            InputSelect_Memory = 1
            if not resp:
                # Resp deasserted: any later Resp=1 is genuinely ours.
                self._h_saw_resp_low = True
            elif self._h_saw_resp_low:
                # FIX: Send both STS (119) and OUT (_IO_WRITE) to the latch state
                if i == 119 or i in _IO_WRITE: 
                    next_state = 'LATCH_RD_TO_BUFFER'
                elif i in _STORE_MEM:
                    # Latch the fetched Rd/Rr value into RD_BUFFER right
                    # now, while Bus data is valid (resp==1 this cycle).
                    # Without this, LOAD_VALUE_TO_MEMORY has nothing but
                    # stale ALU ResL data to write, since this path (unlike
                    # STS/OUT above) never visits LATCH_RD_TO_BUFFER.
                    WE_Memory = 1
                    LoadingMux = 14
                    next_state = 'LOAD_VALUE_TO_MEMORY'


        elif state == 'LATCH_RD_TO_BUFFER':
            Mem_Instruction = 12     # FIX: hold the SAME read (source register)
                                     # stable -- this was defaulting to 0
                                     # (register r0) since Mem_Instruction
                                     # was never set here, silently
                                     # redirecting the address away from
                                     # the real source register mid-wait.
            Read_Write = 2           # Request Memory Read
            WE_Memory = 0            # DON'T latch yet!
            LoadingMux = 14          
            next_state = 'WAIT_LATCH_RD_TO_BUFFER'

        elif state == 'WAIT_LATCH_RD_TO_BUFFER':
            Mem_Instruction = 12     # FIX: same as above -- keep addressing
                                     # the source register, not r0.
            Read_Write = 2 # Keep holding the read request
            LoadingMux = 14
            if resp:
                # Memory data is now valid!
                WE_Memory = 1 # Latch it this cycle
                
                
                if i == 119: # If STS
                    next_state = 'FETCH_ADDRESS_FROM_ROM'
                elif i in _IO_WRITE: # If OUT
                    next_state = 'FETCH_VALUE_TO_A'
            else:
                WE_Memory = 0

        elif state == 'LOAD_VALUE_TO_MEMORY':

            self._pointer_update_pending = False
            # Post-increment must be applied exactly ONCE per instruction.
            # updatePointer() in MemoryInterfaceHandler fires every cycle
            # IncDec is asserted, and this state's signals are held for
            # LOAD + WAIT cycles — driving IncDec continuously bumps the
            # pointer multiple times per store (st X+ was advancing X by 2+)
            # and shifts the write address mid-transaction. Defer the
            # post-increment to the completion cycle instead.
            self._deferred_post_inc = False

            if i in _X_POINTER:
                Mem_Instruction = 1
                if i == 109:    # STX+ (post-inc deferred)
                    self._deferred_post_inc = True
                    self._pointer_update_pending = True
                elif i == 110:  # ST-X
                    IncDec = 2  # PRE DECREMENT (applies once, this cycle only)
                    self._pointer_update_pending = True
            elif i in _Y_POINTER:
                Mem_Instruction = 10 if i == 114 else 3  # STDY uses MEM_Y_Q
                if i == 112:    # STY+ (post-inc deferred)
                    self._deferred_post_inc = True
                    self._pointer_update_pending = True
                elif i == 113:  # ST-Y
                    IncDec = 2  # PRE DECREMENT (applies once, this cycle only)
                    self._pointer_update_pending = True
            elif i in _Z_POINTER:
                Mem_Instruction = 11 if i == 118 else 5  # STDZ uses MEM_Z_Q
                if i == 116:    # STZ+ (post-inc deferred)
                    self._deferred_post_inc = True
                    self._pointer_update_pending = True
                elif i == 117:  # ST-Z
                    IncDec = 2  # PRE DECREMENT (applies once, this cycle only)
                    self._pointer_update_pending = True

            Read_Write = 1            # write opp
            InputSelect_Memory = 16   # data sourced from RD_BUFFER (the Rd/Rr value latched in WAIT_FETCH_VALUE_OF_RD)

            next_state = 'WAIT_LOAD_VALUE_TO_MEMORY'

        elif state == 'WAIT_LOAD_VALUE_TO_MEMORY':

            # Hold the write (same address selection) but with IncDec=0:
            # pre-decrement already updated the pointer in the previous
            # cycle (so the plain pointer now resolves to the same,
            # decremented address), and post-increment is deferred until
            # the write completes below.
            if i == 119:
                Mem_Instruction = 9
                InputSelect_Memory = 16 
            elif i in _X_POINTER:
                Mem_Instruction = 1
                InputSelect_Memory = 16
            elif i in _Y_POINTER:
                Mem_Instruction = 10 if i == 114 else 3
                InputSelect_Memory = 16
            elif i in _Z_POINTER:
                Mem_Instruction = 11 if i == 118 else 5
                InputSelect_Memory = 16

            Read_Write = 1
            
            if resp:
                if self._deferred_post_inc:
                    # Apply the post-increment exactly once, now that the
                    # write has completed at the ORIGINAL address.
                    IncDec = 1
                    self._deferred_post_inc = False
                if self._pointer_update_pending:
                    next_state = 'LOAD_ADDRESS_XYZ_BEGIN_L'
                else:
                    done = 1
                    next_state = 'STOP'


        # ------------------------------------------------
        # IO READ (IN)
        # ------------------------------------------------

        elif state == 'FETCH_VALUE_OF_A':
            # Defensively clear — IN has no X/Y/Z pointer either, and it
            # also lands in LOAD_VALUE_TO_RD/WAIT_LOAD_VALUE_TO_RD, which
            # checks this flag to decide whether to detour into the XYZ
            # rewrite path.
            self._pointer_update_pending = False
            Mem_Instruction = 18     # MEM_A_6bit: I/O port address
            Read_Write = 2           # read opp
            InputSelect_Memory = 1   # Fetching value from dataBus
            next_state = 'WAIT_FETCH_VALUE_OF_A'

        elif state == 'WAIT_FETCH_VALUE_OF_A':
            Mem_Instruction = 18
            Read_Write = 2
            InputSelect_Memory = 1
            
            if resp:
                WE_Memory = 1            # [FIX]: Latch data into RdBuffer
                LoadingMux = 14          # [FIX]: Select LOAD_RD_BUFFER
                next_state = 'LOAD_VALUE_TO_RD'


        # ------------------------------------------------
        # IO WRITE (OUT)
        # ------------------------------------------------

        elif state == 'FETCH_VALUE_TO_A':
            Mem_Instruction = 18     # MEM_A_6bit: I/O port address
            Read_Write = 1           # write opp
            InputSelect_Memory = 16  # INPUT_RD_BUFFER: latched Rd value (matches STS's use of 16)
            next_state = 'WAIT_FETCH_VALUE_TO_A'

        elif state == 'WAIT_FETCH_VALUE_TO_A':
            Mem_Instruction = 18
            Read_Write = 1           # write opp
            InputSelect_Memory = 16
            if resp:
                done = 1
                next_state = 'STOP'


        # ------------------------------------------------
        # REWRITE ADDRESS XYZ LOW
        # ------------------------------------------------

        elif state == 'LOAD_ADDRESS_XYZ_BEGIN_L':

            if i in _X_POINTER :
                self._wb_addr_val = 26
                WB_Addr = 26
            elif i in _Y_POINTER :
                self._wb_addr_val = 28
                WB_Addr = 28
            elif i in _Z_POINTER :
                self._wb_addr_val = 30
                WB_Addr = 30

            Mem_Instruction = 14      # MEM_WB_ADDR
            Read_Write = 1            # write opp: source is updated pointer value
            if i in _X_POINTER :
                InputSelect_Memory = 6   # INPUT_XL
            elif i in _Y_POINTER :
                InputSelect_Memory = 8   # INPUT_YL
            elif i in _Z_POINTER :
                InputSelect_Memory = 10  # INPUT_ZL

            next_state = 'LOAD_ADDRESS_XYZ_WAIT_L'

        elif state == 'LOAD_ADDRESS_XYZ_WAIT_L':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 1
            if i in _X_POINTER:
                InputSelect_Memory = 6   # INPUT_XL
            elif i in _Y_POINTER:
                InputSelect_Memory = 8   # INPUT_YL
            elif i in _Z_POINTER:
                InputSelect_Memory = 10  # INPUT_ZL

            if resp:
                next_state = 'LOAD_ADDRESS_XYZ_BEGIN_H'


        # ------------------------------------------------
        # REWRITE ADDRESS XYZ HIGH
        # ------------------------------------------------

        elif state == 'LOAD_ADDRESS_XYZ_BEGIN_H':

            if i in _X_POINTER:
                self._wb_addr_val = 27
                WB_Addr = 27
                InputSelect_Memory = 7   # INPUT_XH
            elif i in _Y_POINTER:
                self._wb_addr_val = 29
                WB_Addr = 29
                InputSelect_Memory = 9   # INPUT_YH
            elif i in _Z_POINTER:
                self._wb_addr_val = 31
                WB_Addr = 31
                InputSelect_Memory = 11  # INPUT_ZH

            Mem_Instruction = 14    # MEM_WB_ADDR
            Read_Write = 1

            next_state = 'LOAD_ADDRESS_XYZ_WAIT_H'

        elif state == 'LOAD_ADDRESS_XYZ_WAIT_H':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 1
            if i in _X_POINTER:
                InputSelect_Memory = 7   # INPUT_XH
            elif i in _Y_POINTER:
                InputSelect_Memory = 9   # INPUT_YH
            elif i in _Z_POINTER:
                InputSelect_Memory = 11  # INPUT_ZH

            if resp:
                done = 1
                next_state = 'STOP'

        # ------------------------------------------------
        # STORE in case of STS (Direct Addressing)
        # ------------------------------------------------

        elif state == 'FETCH_ADDRESS_FROM_ROM':
            # Trigger the RomHandler to fetch the 16-bit address word.
            # FIX: LoadingMux=14 / WE_Memory=1 have been removed from here.
            # The register value is now safely latched in the dedicated
            # LATCH_RD_TO_BUFFER state that precedes this one.
            Fetch_Address = 1
            next_state = 'WAIT_FETCH_ADDRESS_FROM_ROM'

        elif state == 'WAIT_FETCH_ADDRESS_FROM_ROM':
            # Hold the fetch signal high while we wait for the RomHandler.
            # FIX: LoadingMux=14 / WE_Memory=1 have been removed from here
            # for the same reason as FETCH_ADDRESS_FROM_ROM above.
            Fetch_Address = 1
            if self.Address_fetched.get() == 1:
                next_state = 'LOAD_ADDRESS_TO_MEMORY_HANDLER'

        elif state == 'LOAD_ADDRESS_TO_MEMORY_HANDLER':
            # The RomHandler is now outputting the 16-bit address.
            # Tell the MemoryInterfaceHandler to use it (MEM_RAM_ADDR_REG = 9)
            # and write the value stored in RdBuffer to SRAM.
            Fetch_Address = 1
            Mem_Instruction = 9         # 9 = MEM_RAM_ADDR_REG
            Read_Write = 1              # 1 = Memory Write
            InputSelect_Memory = 16     # 16 = INPUT_RD_BUFFER (correctly latched)
            
            # Move to the existing memory wait state to finish the transaction
            next_state = 'WAIT_LOAD_VALUE_TO_MEMORY'


        # ------------------------------------------------
        # LOAD in case of LDS (Direct Addressing)
        # ------------------------------------------------
        # Mirrors the STS path above: LDS has no X/Y/Z pointer at all, so
        # the 16-bit address word is fetched straight from ROM, then used
        # to read SRAM directly (MEM_RAM_ADDR_REG), then written into Rd.

        elif state == 'FETCH_ADDRESS_FROM_ROM_LD':
            # Defensively clear any pointer-update flag left over from a
            # prior pointer-based instruction — LDS never uses X/Y/Z and
            # must always fall straight through to done/STOP afterward.
            self._pointer_update_pending = False
            # Trigger the RomHandler to fetch the 16-bit address word
            Fetch_Address = 1
            next_state = 'WAIT_FETCH_ADDRESS_FROM_ROM_LD'

        elif state == 'WAIT_FETCH_ADDRESS_FROM_ROM_LD':
            # Hold the fetch signal high while we wait for the RomHandler
            Fetch_Address = 1

            # Transition once the RomHandler acks the fetch
            if self.Address_fetched.get() == 1:
                next_state = 'LOAD_FROM_ROM_ADDR_TO_RD'

        elif state == 'LOAD_FROM_ROM_ADDR_TO_RD':
            # The RomHandler is now outputting the 16-bit address.
            # Read SRAM[that address] (MEM_RAM_ADDR_REG = 9) onto the
            # data bus, then latch it into Rd. 
            Fetch_Address = 1           # [FIX]: Keep handshake high so RomHandler holds the address
            Mem_Instruction = 9         # 9 = MEM_RAM_ADDR_REG
            Read_Write = 2              # 2 = Memory Read
            InputSelect_Memory = 1      # [FIX]: Changed from 16 to 1 (Fetch value from dataBus)
            next_state = 'WAIT_LOAD_FROM_ROM_ADDR_TO_RD'

        elif state == 'WAIT_LOAD_FROM_ROM_ADDR_TO_RD':
            Fetch_Address = 1
            Mem_Instruction = 9
            Read_Write = 2
            InputSelect_Memory = 1

            if resp:
                WE_Memory = 1            # [FIX]: Latch data into RdBuffer
                LoadingMux = 14          # [FIX]: Select LOAD_RD_BUFFER
                next_state = 'LOAD_VALUE_TO_RD'



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

        # --- AI-Friendly State & I/O Trace ---
        if self.debug: #and (self.current_state != 'STOP'):
            state_log = (
                f"LDST_TRACE | State: {self.current_state:30} -> {next_state:30} | Inst: {i:03}\n"
                f"  [Memory]   MemInstr: {Mem_Instruction:<2} | RW: {Read_Write} | InputSel: {InputSelect_Memory:<2} | WE: {WE_Memory} | LoadMux: {LoadingMux:<2} | IncDec: {IncDec} | WB_Addr: {WB_Addr:<2}\n"
                f"  [Buffer]   InputSel: {InputSelect_Buffer}  | WE: {WE_Buffer}\n"
                f"  [ROM/Ctrl] FetchAddr: {Fetch_Address} | LoadZ: {Load_Z} | LoadK: {Load_K} | LoadJmp: {Load_Jump} | RelAbs: {relative_Absolute} | LoadByte: {Load_Byte}\n"
                f"  [Status]   Resp: {resp} | Done: {done}"
            )
            print(state_log)
            
        # Advance state
        self.current_state = next_state