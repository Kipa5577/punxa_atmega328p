import py4hw

# Supported LPM Opcodes
_LPM_INSTRUCTIONS = {
    120, # LPM   (R0 <- ROM[Z])
    121, # LPMZ  (Rd <- ROM[Z])
    122, # LPMZ+ (Rd <- ROM[Z], Z <- Z+1)
}

# Supported SPM Opcodes -- this FSM's SPM_req/R0_BUFFER/R1_BUFFER outputs
# were already scaffolded in RomHandler/MemoryInterfaceHandler but never
# actually driven by any instruction; this class now drives them for real.
_SPM_INSTRUCTIONS = {
    123, # SPM (ROM[Z] <- R1:R0)
}

STATES = [
    'STOP',
    
    # 1. Fetch Z pointer from SRAM
    'FETCH_ADDRESS_XYZ_BEGIN_L', 'WAIT_FETCH_ADDRESS_XYZ_L', 'LOAD_ADDRESS_XYZ_L_IN_BUFFER',
    'FETCH_ADDRESS_XYZ_BEGIN_H', 'WAIT_FETCH_ADDRESS_XYZ_H', 'LOAD_ADDRESS_XYZ_H_IN_BUFFER',
    'SETTLE_Z',
    
    # 2. Point RomHandler PC to Z
    'JUMP_TO_Z', 'WAIT_JUMP_TO_Z',
    
    # 3. Read ROM Data
    'FETCH_ROM_DATA', 'WAIT_FETCH_ROM_DATA',
    
    # 4. Write ROM Data to Destination Register
    'LOAD_ROM_TO_RD', 'WAIT_LOAD_ROM_TO_RD',
    
    # 5. Restore original PC
    'RESTORE_PC', 'WAIT_RESTORE_PC',
    
    # 6. Post-increment Z (Only for LPMZ+)
    'INCREMENT_Z',
    
    # 7. Write updated Z pointer back to SRAM
    'LOAD_ADDRESS_XYZ_BEGIN_L', 'LOAD_ADDRESS_XYZ_WAIT_L',
    'LOAD_ADDRESS_XYZ_BEGIN_H', 'LOAD_ADDRESS_XYZ_WAIT_H',

    # SPM: fetch R0 and R1 (the fixed operand pair SPM always writes,
    # regardless of decoded Rd/Rr -- the decoder leaves both at 0 for
    # opcode 123), latch them into MemoryInterfaceHandler's dedicated
    # R0Buffer/R1Buffer, then trigger RomHandler's SPM_req path, which
    # writes R1:R0 to ROM[Z] directly (Z is read continuously via
    # address_ZL/address_ZH -- no PC detour needed, unlike LPM).
    #
    # FIX: RomHandler's address_ZL/address_ZH inputs are driven by
    # MemoryInterfaceHandler's *own* ZregL/ZregH shadow registers (see
    # MIH.address_ZL/address_ZH.prepare(self.ZregL/self.ZregH)), not
    # directly by the r30/r31 GP registers. That shadow is only ever
    # updated when something explicitly loads it via LOAD_ZL/LOAD_ZH
    # (LoadingMux 5/6) -- which is exactly what the LPM path's own
    # FETCH_ADDRESS_XYZ_BEGIN_L/H states do before touching ROM. The SPM
    # path used to skip straight to SPM_FETCH_R0_BEGIN and trigger the
    # ROM write against whatever stale ZregL/ZregH happened to be left
    # over from the last LPM/LD Z/ST Z instruction (0 if none had ever
    # run), silently writing to the wrong Flash address regardless of
    # what the program had just loaded into r30/r31. These six states
    # mirror the LPM Z-fetch/settle sequence (read r30 -> ZregL, read
    # r31 -> ZregH, wait one extra cycle for the shadow write to actually
    # propagate) before falling into the existing R0/R1 fetch + trigger
    # states, so SPM ends up targeting the Z the program actually set.
    'SPM_FETCH_Z_L_BEGIN', 'SPM_WAIT_Z_L', 'SPM_LOAD_Z_L_IN_BUFFER',
    'SPM_FETCH_Z_H_BEGIN', 'SPM_WAIT_Z_H', 'SPM_LOAD_Z_H_IN_BUFFER',
    'SPM_SETTLE_Z',

    'SPM_FETCH_R0_BEGIN', 'SPM_WAIT_R0', 'SPM_LOAD_R0',
    'SPM_FETCH_R1_BEGIN', 'SPM_WAIT_R1', 'SPM_LOAD_R1',
    # FIX: SPM_LOAD_R1 used to fall straight into SPM_TRIGGER. R0 gets
    # away without an equivalent settle state only because the
    # FETCH_R1_BEGIN/WAIT_R1 x4/LOAD_R1 states in between give its
    # buffer write several cycles to become visible; R1's own write (in
    # SPM_LOAD_R1) has no such runway before SPM_TRIGGER reads it, so
    # RomHandler was committing R1Buffer's still-stale value (0) into
    # the high byte of every SPM write. One settle cycle here, same
    # reasoning as SPM_SETTLE_Z above.
    'SPM_SETTLE_R1',
    'SPM_TRIGGER', 'SPM_WAIT_DONE',
]


class LPM_FSM(py4hw.Logic):
    def __init__(self, parent, name,
                 # ── Logic inputs ─────────────────────────────────────────
                 run, 
                 done, 
                 # ── Inputs ──────────────────────────────────────────────
                 Instruction,        
                 Resp,               
                 Branch,             
                 Executed_Jump, 
                 Address_fetched,    # Added: Needed to ack RomHandler fetch completion

                 # ── Memory Interface Outputs ─────────────────────────────
                 NotExecute,         
                 LoadSelectMux,      
                 LoadingMux,         
                 Input_Select,       
                 WE,                 
                 Read_Write,         
                 Mem_Instruction,    
                 IncDec,             

                 # ── ALU Buffer Outputs ───────────────────────────────────
                 write_Opperand_Buffer, 
                 InputSelect, 
                 Write_Enable, 

                 # ── ROM Handler Outputs ──────────────────────────────────
                 Load_Z,             
                 Load_K,             
                 Load_Jump,          
                 relative_Absolute,  
                 Load_Byte,          
                 Fetch_next_instruction, 
                 Fetch_Address, 
                 LOAD_PCL,           # Added: Needed to restore PC
                 LOAD_PCH,           # Added: Needed to restore PC

                 # ── Write-back address ───────────────────────────────────
                 WB_Addr,            

                 LPM_req,
                 SPM_req,
                 SPM_Done,          # 1-bit IN: pulses when RomHandler's SPM_req write has committed
                                  reset=None,
             ):
        super().__init__(parent, name)
        self.reset = self.addIn('reset', reset) if reset is not None else None

        # ── Logic inputs & outputs ───────────────────────────────────────
        self.run                   = self.addIn('Run', run) 
        self.done                  = self.addOut('Done', done) # FSM sets this, must be out
        
        # ── Register inputs ──────────────────────────────────────────────
        self.Instruction           = self.addIn('Instruction',           Instruction)
        self.Resp                  = self.addIn('Resp',                  Resp)
        self.Branch                = self.addIn('Branch',                Branch)
        self.Executed_Jump         = self.addIn('Executed_Jump',         Executed_Jump)
        self.Address_fetched       = self.addIn('Address_fetched',       Address_fetched)
        self.SPM_Done              = self.addIn('SPM_Done',              SPM_Done)

        # ── Register outputs ─────────────────────────────────────────────
        self.NotExecute            = self.addOut('NotExecute',       NotExecute)
        self.LoadSelectMux         = self.addOut('LoadSelectMux',    LoadSelectMux)
        self.LoadingMux            = self.addOut('LoadingMux',       LoadingMux)
        self.Input_Select          = self.addOut('Input_Select',     Input_Select)
        self.WE                    = self.addOut('WE',               WE)
        self.Read_Write            = self.addOut('Read_Write',       Read_Write)
        self.Mem_Instruction       = self.addOut('Mem_Instruction',  Mem_Instruction)
        self.IncDec                = self.addOut('IncDec',           IncDec)

        self.write_Opperand_Buffer = self.addOut('write_Opperand_Buffer',write_Opperand_Buffer)
        self.InputSelect           = self.addOut('InputSelect',      InputSelect)
        self.Write_Enable          = self.addOut('Write_Enable',     Write_Enable)

        self.Load_Z                = self.addOut('Load_Z',           Load_Z)
        self.Load_K                = self.addOut('Load_K',           Load_K)
        self.Load_Jump             = self.addOut('Load_Jump',        Load_Jump)
        self.relative_Absolute     = self.addOut('relative_Absolute',relative_Absolute)
        self.Load_Byte             = self.addOut('Load_Byte',        Load_Byte)
        self.Fetch_next_instruction= self.addOut('Fetch_next_instruction',Fetch_next_instruction)
        self.Fetch_Address         = self.addOut('Fetch_Address',    Fetch_Address)
        self.LOAD_PCL              = self.addOut('LOAD_PCL',         LOAD_PCL)
        self.LOAD_PCH              = self.addOut('LOAD_PCH',         LOAD_PCH)
        
        self.WB_Addr               = self.addOut('WB_Addr',          WB_Addr)

        self.LPM_req               = self.addOut('LPM_req',          LPM_req)
        self.SPM_req               = self.addOut('SPM_req',          SPM_req)

        # ── FSM state ────────────────────────────────────────────────────
        self.current_state = 'STOP'
        self._latched_inst = 0
        self._wb_addr_val = 0
        self._pointer_update_pending = False
        # Edge-detect flag: set once Resp has genuinely been observed low
        # during the current memory read, so a subsequent Resp=1 can be
        # trusted as THIS read's completion rather than a registered
        # Resp=1 left over from the previous memory operation (this is
        # the same hazard that corrupted the ZH read in LDST_FSM).
        self._saw_resp_low = False
        self.debug = 0


    def clock(self):
        if self.reset is not None and self.reset.get():
            self.current_state = 'STOP'
            self.done.prepare(0)
            self.NotExecute.prepare(0)
            self.LoadSelectMux.prepare(0)
            self.LoadingMux.prepare(0)
            self.Input_Select.prepare(0)
            self.WE.prepare(0)
            self.Read_Write.prepare(0)
            self.Mem_Instruction.prepare(0)
            self.IncDec.prepare(0)
            self.write_Opperand_Buffer.prepare(0)
            self.InputSelect.prepare(0)
            self.Write_Enable.prepare(0)
            self.Load_Z.prepare(0)
            self.Load_K.prepare(0)
            self.Load_Jump.prepare(0)
            self.relative_Absolute.prepare(0)
            self.Load_Byte.prepare(0)
            self.Fetch_next_instruction.prepare(0)
            self.Fetch_Address.prepare(0)
            self.LOAD_PCL.prepare(0)
            self.LOAD_PCH.prepare(0)
            self.WB_Addr.prepare(0)
            self.LPM_req.prepare(0)
            self.SPM_req.prepare(0)
            return

        inst              = self.Instruction.get()
        resp              = self.Resp.get()
        executed_jump     = self.Executed_Jump.get()
        address_fetched   = self.Address_fetched.get()
        run               = self.run.get()

        # Zero out default drives
        InputSelect_Buffer = 0
        NotExecute = 0
        LoadSelectMux = 0
        LoadingMux = 0
        Input_Select = 0
        WE = 0
        Read_Write = 0   
        Mem_Instruction = 0
        IncDec = 0
        write_Opperand_Buffer = 0
        InputSelect = 0
        Write_Enable = 0
        Load_Z = 0
        Load_K = 0
        Load_Jump = 0
        relative_Absolute = 0
        Load_Byte = 0
        Fetch_next_instruction = 0
        Fetch_Address = 0
        LOAD_PCL = 0
        LOAD_PCH = 0
        WB_Addr = self._wb_addr_val
        SPM_req = 0
        done = 0 

        state = self.current_state
        next_state = state           

        if state == 'STOP' and run:
            self._latched_inst = inst
            # Only LPMZ+ (122) updates the Z pointer
            self._pointer_update_pending = (inst == 122)

        i = self._latched_inst  

        # ================================================================
        # STATE MACHINE
        # ================================================================

        if state == 'STOP':
            if run:
                if inst in _LPM_INSTRUCTIONS:
                    next_state = 'FETCH_ADDRESS_XYZ_BEGIN_L'
                elif inst in _SPM_INSTRUCTIONS:
                    next_state = 'SPM_FETCH_Z_L_BEGIN'
                else:
                    # Failsafe for non-LPM/SPM instructions
                    done = 1 

        # ------------------------------------------------
        # 1. FETCH ADDRESS XYZ LOW (Z Pointer)
        # ------------------------------------------------
        elif state == 'FETCH_ADDRESS_XYZ_BEGIN_L':
            self._wb_addr_val = 30   # R30 (ZL)
            WB_Addr = 30
            Mem_Instruction = 14     # MEM_WB_ADDR
            Read_Write = 2           # Read
            Input_Select = 1         # Receive from DataBus
            # New read: discard any Resp=1 sampled before Resp has gone
            # low — it belongs to the previous memory operation.
            self._saw_resp_low = False
            next_state = 'WAIT_FETCH_ADDRESS_XYZ_L'

        elif state == 'WAIT_FETCH_ADDRESS_XYZ_L':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 2 
            Input_Select = 1 
            if not resp:
                self._saw_resp_low = True
            elif self._saw_resp_low:
                next_state = 'LOAD_ADDRESS_XYZ_L_IN_BUFFER'

        elif state == 'LOAD_ADDRESS_XYZ_L_IN_BUFFER':
            WE = 1
            LoadingMux = 5           # LOAD_ZL
            next_state = 'FETCH_ADDRESS_XYZ_BEGIN_H'

        # ------------------------------------------------
        # 1. FETCH ADDRESS XYZ HIGH (Z Pointer)
        # ------------------------------------------------
        elif state == 'FETCH_ADDRESS_XYZ_BEGIN_H':
            self._wb_addr_val = 31   # R31 (ZH)
            WB_Addr = 31
            Mem_Instruction = 14     
            Read_Write = 2 
            Input_Select = 1 
            # CRITICAL edge-detect reset: this read starts one cycle after
            # the ZL read completed with Resp=1. Without waiting for a
            # genuine Resp low->high transition, the stale Resp=1 from the
            # ZL read is accepted immediately and ZL's value gets latched
            # into ZH — sending LPM to a garbage ROM address.
            self._saw_resp_low = False
            next_state = 'WAIT_FETCH_ADDRESS_XYZ_H'

        elif state == 'WAIT_FETCH_ADDRESS_XYZ_H':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 2 
            Input_Select = 1 
            if not resp:
                self._saw_resp_low = True
            elif self._saw_resp_low:
                next_state = 'LOAD_ADDRESS_XYZ_H_IN_BUFFER'

        elif state == 'LOAD_ADDRESS_XYZ_H_IN_BUFFER':
            WE = 1
            LoadingMux = 6           # LOAD_ZH
            next_state = 'SETTLE_Z'

        # One idle cycle between writing ZH and reading Z back out via
        # Load_Z. MemoryInterfaceHandler prepares its address_ZL/address_ZH
        # outputs from self.ZregL/self.ZregH BEFORE it applies the current
        # cycle's register write (see its clock() -- the address_ZL/ZH
        # .prepare() calls run ahead of the "Register loading" section).
        # Without this settle cycle, JUMP_TO_Z reads Z one cycle too early
        # and RomHandler computes its jump target from the OLD Z value
        # (confirmed via trace: writing Z=0x0200 then immediately asserting
        # Load_Z produced New PC=0x0000 instead of 0x0100 -- exactly what
        # you'd get from a stale, not-yet-updated ZH).
        elif state == 'SETTLE_Z':
            next_state = 'JUMP_TO_Z'

        # ------------------------------------------------
        # 2. OVERWRITE ROM HANDLER PC WITH Z
        # ------------------------------------------------
        elif state == 'JUMP_TO_Z':
            Load_Z = 1
            # relative_Absolute=1 alongside Load_Z tells RomHandler that Z
            # is a BYTE address (LPM semantics): PC <- Z>>1 and Z&1 selects
            # the byte of the fetched flash word. (IJMP/ICALL assert Load_Z
            # with relative_Absolute=0 and keep word-address semantics.)
            relative_Absolute = 1
            next_state = 'WAIT_JUMP_TO_Z'

        elif state == 'WAIT_JUMP_TO_Z':
            Load_Z = 1               # Hold request
            relative_Absolute = 1
            if executed_jump:
                next_state = 'FETCH_ROM_DATA'

        # ------------------------------------------------
        # 3. READ DATA FROM ROM
        # ------------------------------------------------
        elif state == 'FETCH_ROM_DATA':
            Fetch_Address = 1        # Trigger FETCH_ADDR_REQ at new PC
            next_state = 'WAIT_FETCH_ROM_DATA'

        elif state == 'WAIT_FETCH_ROM_DATA':
            Fetch_Address = 1        # Hold request
            if address_fetched:
                next_state = 'LOAD_ROM_TO_RD'

        # ------------------------------------------------
        # 4. WRITE ROM DATA TO DESTINATION
        # ------------------------------------------------
        elif state == 'LOAD_ROM_TO_RD':
            if i == 120:             # Base LPM hardcodes destination to R0
                Mem_Instruction = 14 # MEM_WB_ADDR
                self._wb_addr_val = 0
                WB_Addr = 0
            else:                    # LPM Rd, Z or LPM Rd, Z+ uses instruction Rd
                Mem_Instruction = 12 # MEM_RD

            Read_Write = 1           # Write operation
            Input_Select = 5         # INPUT_ROM_VALUE — the byte RomHandler just fetched (RomAddressValue), not the raw SRAM data bus
            next_state = 'WAIT_LOAD_ROM_TO_RD'

        elif state == 'WAIT_LOAD_ROM_TO_RD':
            if i == 120:
                Mem_Instruction = 14
                WB_Addr = 0
            else:
                Mem_Instruction = 12
                
            Read_Write = 1
            Input_Select = 5
            if resp:
                next_state = 'RESTORE_PC'

        # ------------------------------------------------
        # 5. RESTORE ORIGINAL PC 
        # ------------------------------------------------
        elif state == 'RESTORE_PC':
            # Load_Jump must accompany LOAD_PCL/LOAD_PCH: RomHandler only
            # sets its internal `jumped` flag (and therefore asserts
            # Executed_Jump) inside the Load_Z/Load_Jump/Load_K branches.
            # LOAD_PCL/LOAD_PCH alone still overwrite the PC bytes, but
            # `jumped` stays False, so Executed_Jump never pulses and this
            # FSM would hang forever waiting for it. Load_Jump's own PC
            # arithmetic (relative_Absolute/K12) is harmless here — it gets
            # fully overwritten afterward by RomHandler's unconditional
            # LOAD_PCL/LOAD_PCH byte assignments.
            Load_Jump = 1
            relative_Absolute = 0
            LOAD_PCL = 1
            LOAD_PCH = 1
            next_state = 'WAIT_RESTORE_PC'

        elif state == 'WAIT_RESTORE_PC':
            Load_Jump = 1
            relative_Absolute = 0
            LOAD_PCL = 1
            LOAD_PCH = 1
            if executed_jump:
                if self._pointer_update_pending:
                    next_state = 'INCREMENT_Z'
                else:
                    done = 1
                    next_state = 'STOP'

        # ------------------------------------------------
        # 6. POST-INCREMENT Z (LPMZ+ Only)
        # ------------------------------------------------
        elif state == 'INCREMENT_Z':
            Mem_Instruction = 6      # Z pointer mapping
            IncDec = 1               # Post-increment internally in MIH
            Read_Write = 0           # No memory read/write this cycle
            next_state = 'LOAD_ADDRESS_XYZ_BEGIN_L'

        # ------------------------------------------------
        # 7. REWRITE UPDATED Z POINTER TO SRAM
        # ------------------------------------------------
        elif state == 'LOAD_ADDRESS_XYZ_BEGIN_L':
            self._wb_addr_val = 30   # ZL
            WB_Addr = 30
            Mem_Instruction = 14     # MEM_WB_ADDR
            Read_Write = 1           # Write updated value
            Input_Select = 10        # INPUT_ZL
            next_state = 'LOAD_ADDRESS_XYZ_WAIT_L'

        elif state == 'LOAD_ADDRESS_XYZ_WAIT_L':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 1
            Input_Select = 10  
            if resp:
                next_state = 'LOAD_ADDRESS_XYZ_BEGIN_H'

        elif state == 'LOAD_ADDRESS_XYZ_BEGIN_H':
            self._wb_addr_val = 31   # ZH
            WB_Addr = 31
            Mem_Instruction = 14    
            Read_Write = 1
            Input_Select = 11        # INPUT_ZH
            next_state = 'LOAD_ADDRESS_XYZ_WAIT_H'

        elif state == 'LOAD_ADDRESS_XYZ_WAIT_H':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 1
            Input_Select = 11  
            if resp:
                done = 1
                next_state = 'STOP'

        # ================================================================
        # SPM: sync MemoryInterfaceHandler's ZregL/ZregH shadow from the
        # r30/r31 GP registers before touching ROM (see the STATES-list
        # comment above for why this is needed). Mirrors the LPM path's
        # own FETCH_ADDRESS_XYZ_BEGIN_L/H + settle sequence exactly.
        # ================================================================
        elif state == 'SPM_FETCH_Z_L_BEGIN':
            self._wb_addr_val = 30   # R30 (ZL)
            WB_Addr = 30
            Mem_Instruction = 14     # MEM_WB_ADDR
            Read_Write = 2           # Read
            Input_Select = 1         # Receive from DataBus
            self._saw_resp_low = False
            next_state = 'SPM_WAIT_Z_L'

        elif state == 'SPM_WAIT_Z_L':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 2
            Input_Select = 1
            if not resp:
                self._saw_resp_low = True
            elif self._saw_resp_low:
                next_state = 'SPM_LOAD_Z_L_IN_BUFFER'

        elif state == 'SPM_LOAD_Z_L_IN_BUFFER':
            WE = 1
            LoadingMux = 5           # LOAD_ZL
            next_state = 'SPM_FETCH_Z_H_BEGIN'

        elif state == 'SPM_FETCH_Z_H_BEGIN':
            self._wb_addr_val = 31   # R31 (ZH)
            WB_Addr = 31
            Mem_Instruction = 14
            Read_Write = 2
            Input_Select = 1
            # Same hazard as every other back-to-back register read in
            # this FSM: reset the edge-detect flag so a stale Resp=1 left
            # over from the ZL read can't be mistaken for the ZH read's
            # own completion.
            self._saw_resp_low = False
            next_state = 'SPM_WAIT_Z_H'

        elif state == 'SPM_WAIT_Z_H':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 2
            Input_Select = 1
            if not resp:
                self._saw_resp_low = True
            elif self._saw_resp_low:
                next_state = 'SPM_LOAD_Z_H_IN_BUFFER'

        elif state == 'SPM_LOAD_Z_H_IN_BUFFER':
            WE = 1
            LoadingMux = 6           # LOAD_ZH
            next_state = 'SPM_SETTLE_Z'

        elif state == 'SPM_SETTLE_Z':
            # MIH's address_ZL/address_ZH outputs are prepared from
            # self.ZregL/self.ZregH *before* this cycle's register-load
            # section runs (see MemoryInterfaceHandler.clock()), so the
            # ZH write just latched won't be visible on address_ZH until
            # the next cycle. Burn one cycle so RomHandler's SPM_REQ
            # state reads a fully-settled Z, same reason LPM's own
            # SETTLE_Z state exists.
            next_state = 'SPM_FETCH_R0_BEGIN'

        # ================================================================
        # SPM: fetch R0
        # ================================================================
        elif state == 'SPM_FETCH_R0_BEGIN':
            self._wb_addr_val = 0    # R0
            WB_Addr = 0
            Mem_Instruction = 14     # MEM_WB_ADDR
            Read_Write = 2           # Read
            Input_Select = 1
            self._saw_resp_low = False
            next_state = 'SPM_WAIT_R0'

        elif state == 'SPM_WAIT_R0':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 2
            Input_Select = 1
            if not resp:
                self._saw_resp_low = True
            elif self._saw_resp_low:
                next_state = 'SPM_LOAD_R0'

        elif state == 'SPM_LOAD_R0':
            WE = 1
            LoadingMux = 15          # LOAD_R0_BUFFER
            next_state = 'SPM_FETCH_R1_BEGIN'

        # ================================================================
        # SPM: fetch R1
        # ================================================================
        elif state == 'SPM_FETCH_R1_BEGIN':
            self._wb_addr_val = 1    # R1
            WB_Addr = 1
            Mem_Instruction = 14
            Read_Write = 2
            Input_Select = 1
            # Same hazard as the ZL->ZH transition above: this read starts
            # one cycle after R0's completed with Resp=1, so the
            # edge-detect flag must be reset before trusting a new Resp=1.
            self._saw_resp_low = False
            next_state = 'SPM_WAIT_R1'

        elif state == 'SPM_WAIT_R1':
            WB_Addr = self._wb_addr_val
            Mem_Instruction = 14
            Read_Write = 2
            Input_Select = 1
            if not resp:
                self._saw_resp_low = True
            elif self._saw_resp_low:
                next_state = 'SPM_LOAD_R1'

        elif state == 'SPM_LOAD_R1':
            WE = 1
            LoadingMux = 16          # LOAD_R1_BUFFER
            next_state = 'SPM_SETTLE_R1'

        elif state == 'SPM_SETTLE_R1':
            next_state = 'SPM_TRIGGER'

        # ================================================================
        # SPM: trigger the write and wait for RomHandler to commit it
        # ================================================================
        elif state == 'SPM_TRIGGER':
            SPM_req = 1
            next_state = 'SPM_WAIT_DONE'

        elif state == 'SPM_WAIT_DONE':
            SPM_req = 1              # hold the request asserted
            if self.SPM_Done.get() == 1:
                done = 1
                next_state = 'STOP'

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

        self.write_Opperand_Buffer.prepare(write_Opperand_Buffer)
        self.InputSelect.prepare(InputSelect) 
        self.Write_Enable.prepare(Write_Enable) 

        self.Load_Z.prepare(Load_Z)
        self.Load_K.prepare(Load_K)
        self.Load_Jump.prepare(Load_Jump)
        self.relative_Absolute.prepare(relative_Absolute)
        self.Load_Byte.prepare(Load_Byte)
        self.Fetch_next_instruction.prepare(Fetch_next_instruction)
        self.Fetch_Address.prepare(Fetch_Address)
        self.LOAD_PCL.prepare(LOAD_PCL)
        self.LOAD_PCH.prepare(LOAD_PCH)

        self.done.prepare(done)
        self.WB_Addr.prepare(WB_Addr)
        self.SPM_req.prepare(SPM_req)

        # --- AI-Friendly State & I/O Trace ---
        # Only trace while this FSM is actually doing something: either
        # mid-sequence (state != 'STOP') or on the cycle it's first kicked
        # off (state == 'STOP' and run == 1). This mirrors the intent noted
        # in LDST_FSM's debug guard, so idle cycles between instructions
        # (state == 'STOP', run == 0) stay silent instead of spamming a
        # print every single clock tick.
        if self.debug == 1 and (state != 'STOP' or run):
            state_log = (
                f"LPM_TRACE | State: {state:30} -> {next_state:30} | Inst: {i:03}\n"
                f"  [Memory]   MemInstr: {Mem_Instruction:<2} | RW: {Read_Write} | InputSel: {Input_Select:<2} | WE: {WE} | LoadMux: {LoadingMux:<2} | IncDec: {IncDec} | WB_Addr: {WB_Addr:<2}\n"
                f"  [Buffer]   InputSel: {InputSelect}  | WE: {write_Opperand_Buffer} | WriteEn: {Write_Enable}\n"
                f"  [ROM/Ctrl] FetchAddr: {Fetch_Address} | LoadZ: {Load_Z} | LoadK: {Load_K} | LoadJmp: {Load_Jump} | RelAbs: {relative_Absolute} | LoadByte: {Load_Byte} | LoadPCL: {LOAD_PCL} | LoadPCH: {LOAD_PCH}\n"
                f"  [Status]   Resp: {resp} | AddrFetched: {address_fetched} | ExecJump: {executed_jump} | PtrUpdatePending: {self._pointer_update_pending} | Done: {done}"
            )
            print(state_log)

        self.current_state = next_state