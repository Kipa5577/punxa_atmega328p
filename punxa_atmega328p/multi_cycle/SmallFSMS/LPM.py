import py4hw

# Supported LPM Opcodes
_LPM_INSTRUCTIONS = {
    120, # LPM   (R0 <- ROM[Z])
    121, # LPMZ  (Rd <- ROM[Z])
    122, # LPMZ+ (Rd <- ROM[Z], Z <- Z+1)
}

STATES = [
    'STOP',
    
    # 1. Fetch Z pointer from SRAM
    'FETCH_ADDRESS_XYZ_BEGIN_L', 'WAIT_FETCH_ADDRESS_XYZ_L', 'LOAD_ADDRESS_XYZ_L_IN_BUFFER',
    'FETCH_ADDRESS_XYZ_BEGIN_H', 'WAIT_FETCH_ADDRESS_XYZ_H', 'LOAD_ADDRESS_XYZ_H_IN_BUFFER',
    
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
                 ):
        super().__init__(parent, name)

        # ── Logic inputs & outputs ───────────────────────────────────────
        self.run                   = self.addIn('Run', run) 
        self.done                  = self.addOut('Done', done) # FSM sets this, must be out
        
        # ── Register inputs ──────────────────────────────────────────────
        self.Instruction           = self.addIn('Instruction',           Instruction)
        self.Resp                  = self.addIn('Resp',                  Resp)
        self.Branch                = self.addIn('Branch',                Branch)
        self.Executed_Jump         = self.addIn('Executed_Jump',         Executed_Jump)
        self.Address_fetched       = self.addIn('Address_fetched',       Address_fetched)

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
        self.debug = 1


    def clock(self):
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
                else:
                    # Failsafe for non-LPM instructions
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