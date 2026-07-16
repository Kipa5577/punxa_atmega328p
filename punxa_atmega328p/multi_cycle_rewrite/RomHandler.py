import py4hw

class RomHandler(py4hw.Logic):
    def __init__(self, parent, name,
                 # --- Memory Interface ---
                 RH_mem,  # Type: MemoryInterface
                 
                 # --- Outputs ---
                 RH_instructionOut, # 16-bit Gives the raw instruction code to the instruction decoder (also feeds the IR register's D input directly in Datapath)
                 RH_Address_Out, # 16-bit Gives the address word to the MemoryController
                 RH_Value_Out, # 16-bit Gives the value stored in rom to the memory controller (NOT USED)

                 # --- PC register drive (PC now lives in Datapath as a py4hw.Reg;
                 #     RomHandler is purely the controller that computes what goes
                 #     into it, same relationship it always had with self.PC,
                 #     just externalized) ---
                 RH_PC_ValIn,     # 16-bit IN: current committed PC value (Reg.q)
                 RH_PC_ValueOut,  # 16-bit OUT: next PC value to latch (Reg.d)
                 RH_PC_Load,      # 1-bit OUT: PC register enable -- asserted on
                                  # every cycle RomHandler would previously have
                                  # written self.PC; 0 means "hold"

                # -- StateOutputs -- 
                 RH_Instruction_fetched, # 1-bit Signal to indicate to the Control Box that the instruction has been outputed 
                 RH_Executed_Jump,# 1-bit Signal to indicate to the Control Box component that the jump instruction has been correctly executed

                 # --- Indirect Jumps (IJMP, ICALL) via Z register ---
                 RH_Load_Z, # 1-bit it tels the RomHandler to fetch the value in the rom at address Z  
                 RH_address_ZL, # 8-bit Inputs the low 8 bits of the Zaddress value
                 RH_address_ZH, # 8-bit Input the high 8 bits of the Zaddress value 
                 
                 # --- Branches & Jumps ---
                 RH_Load_K, # 1-bit Tels the RomHandler to use a K value to Jump 
                 RH_K_select, # 2-bit Tels the RomHandler wich K to use 
                 RH_K7, # branch instructions 
                 RH_K12,# RCALL/RJMP 
                 #K16,# LDS/STS SECOND WORD THIS IS TO MEMORY
                 #K22,# JMP/CALL 22-bit absolute
                 RH_K7_22, # JMP/CALL 7 bits comming from the instruction decoder
                 RH_Load_Jump, # 1-bit Tels the RomHandler to jump 
                 RH_relative_Absolute, # 1-bit Tels the RomHandler if the jump is relative or absolute 
                 
                 # --- ROM Writing (SPM and LPM instruction) ---
                 RH_WriteVal, # 8-bit IN this is the value to write to the rom 
                 RH_ReadVal, # 8-bit OUT this is the value of the memory position 

                 RH_SPM_req, # 1-bit this value tells the RomHandler that it should store the R1 high byte and R0 low byte of the instruction
                 RH_LPM_req, # 2-bit this value tells the RomHandler to execute a LPM or LPMZ or LPMZ+ instruction  

                 RH_R0_BUFFER_IN,
                 RH_R1_BUFFER_IN,

                 # 1-bit OUT: pulses for one cycle when an SPM write
                 # (triggered via SPM_req) has been committed to ROM.
                 # Without this the calling FSM (LPM_FSM) has no way to
                 # observe that the SPM_REQ state ever finished -- it's
                 # an internal transition back to STOP with no externally
                 # visible signal otherwise.
                 RH_SPM_Done,

                 RH_PCL_LOAD_VAL,# 8-bit this 
                 RH_PCH_LOAD_VAL,# 

                 # --- CommandInputs --- 
                 RH_Fetch_next_instruction,
                 RH_JumpWidth, # tells the component by how much it has to increment the pc to go to the next instructin 0 = pc +1 | 1 = pc +2 it is connected to the control Box
                 RH_Load_PCL,# This is to control the loading of the pc register
                 RH_Load_PCH,

                 RH_fetch_address, # control imput that tell the component to fetch the next word form the rom memory 
                 RH_Address_fetched,# control values that signals the control box that the address was fetched

                 RH_Load_Byte,

                 RH_reset):     # 1-bit IN: real reset wire (PC's own reset
                                 # value now lives on the PC Reg itself in
                                 # Datapath -- this just resets RomHandler's
                                 # FSM/private state)
        
        super().__init__(parent, name)

        # --- Internal (private to RomHandler, NOT the architectural PC --
        #     see class docstring / spec: these are snapshot/latch state
        #     used to sequence multi-cycle ROM transactions, reset below) ---
        self.PC_BUFFER = 0

        self._pc_restore_pending = False

        # LPM byte-address support: Load_Z asserted together with
        # relative_Absolute=1 means Z is a BYTE address (LPM semantics),
        # so the PC gets Z>>1 (word address) and Z&1 selects which byte
        # of the fetched word is exposed on the next FETCH_ADDR_WAIT
        # completion. Load_Z with relative_Absolute=0 keeps the legacy
        # word-address semantics used by IJMP/ICALL.
        self._lpm_byte_pending = False
        self._lpm_byte_high = 0

        self.FSM = 'STOP'           # State machine initial state
        self.latched_addr_word = 0  # Latches the 2nd-word (low bits) fetched
                                     # during FETCH_ADDR_WAIT, for JMP/CALL
        
        # Memory interface: we are the SOURCE (master/initiator)
        self.mem = self.addInterfaceSource('ins', RH_mem)

        # --- Output Pins ---
        self.instructionOut = self.addOut('instructionOut', RH_instructionOut)
        self.Address_Out = self.addOut('Address_Out', RH_Address_Out)

        self.Value_Out = self.addOut('Value_Out',RH_Value_Out)

        self.Instruction_fetched = self.addOut('Instruction_fetched',RH_Instruction_fetched)
        self.Executed_Jump = self.addOut('Executed_Jump',RH_Executed_Jump)
        
        # --- Input Pins (Control Signals from Decoder/Execute stage) ---
        self.Load_Z = self.addIn('Load_Z', RH_Load_Z)
        self.address_ZL = self.addIn('address_ZL', RH_address_ZL)
        self.address_ZH = self.addIn('address_ZH', RH_address_ZH)
        
        self.Load_K = self.addIn('Load_K', RH_Load_K)
        self.K_select = self.addIn('K_select',RH_K_select)
        self.K7 = self.addIn('K7',RH_K7)
        self.K12 = self.addIn('K12',RH_K12)
        self.K7_22 = self.addIn('K7_22',RH_K7_22)
        
        self.Load_Jump = self.addIn('Load_Jump', RH_Load_Jump)
        self.relative_Absolute = self.addIn('relative_Absolute', RH_relative_Absolute)

        self.Fetch_next_instruction = self.addIn('Fetch_next_instruction',RH_Fetch_next_instruction)

        self.PC_ValIn = self.addIn('PC_ValIn', RH_PC_ValIn)
        self.PC_ValueOut = self.addOut('PC_ValueOut', RH_PC_ValueOut)
        self.PC_Load = self.addOut('PC_Load', RH_PC_Load)

        self.reset = self.addIn('reset', RH_reset)

        self.JumpWidth = self.addIn('JumpWidth',RH_JumpWidth)
        self.Load_PCL  = self.addIn('Load_PCL',RH_Load_PCL)
        self.Load_PCH = self.addIn('Load_PCH',RH_Load_PCH)

        self.PCL_LOAD_VAL = self.addIn('PCL_LOAD_VAL',RH_PCL_LOAD_VAL)
        self.PCH_LOAD_VAL = self.addIn('PCH_LOAD_VAL',RH_PCH_LOAD_VAL) 

        self.fetch_address = self.addIn('fetch_address',RH_fetch_address)
        self.Address_fetched = self.addOut('Address_fetched',RH_Address_fetched)

        self.Load_Byte = self.addIn('RH_Load_Byte',RH_Load_Byte)

        # ---- SPM and LPM instructions -----
        self.WriteVal = self.addIn('WriteVal',RH_WriteVal)
        self.ReadVal = self.addOut('ReadVal',RH_ReadVal)

        self.LPM_req = self.addIn('LPM__req',RH_LPM_req)
        self.SPM_req = self.addIn('SPM_req',RH_SPM_req)

        self.R0_BUFFER_IN = self.addIn('R0_BUFFER_IN',RH_R0_BUFFER_IN)
        self.R1_BUFFER_IN = self.addIn('R1_BUFFER_IN',RH_R1_BUFFER_IN)

        self.SPM_Done = self.addOut('SPM_Done', RH_SPM_Done)


        self.debug = 0

    def _select_K(self):
        """
        Multiplex between the three K sources based on K_select.
        0 = K7   (7-bit signed offset, conditional branches)
        1 = K12  (12-bit signed offset, RJMP/RCALL)
        2 = K7_22 (absolute target, JMP/CALL)
        """
        sel = self.K_select.get()
        if sel == 0:
            return self.K7.get()
        elif sel == 1:
            return self.K12.get()
        elif sel == 2:
            return self.K7_22.get()
        else:
            return self.K7.get()

    def clock(self):
        # Store the current state to detect changes at the end of the clock cycle
        previous_state = self.FSM

        # --- Reset: force FSM + private snapshot state back to their
        #     initial values. The PC register itself resets independently
        #     (its own `reset` pin, wired directly from the same top-level
        #     reset in Datapath) -- this just keeps RomHandler's own FSM in
        #     sync so it doesn't try to resume some in-flight multi-cycle
        #     transaction against a PC that just snapped back to 0. ---
        if self.reset.get():
            self.FSM = 'STOP'
            self.PC_BUFFER = 0
            self._pc_restore_pending = False
            self._lpm_byte_pending = False
            self._lpm_byte_high = 0
            self.latched_addr_word = 0

            self.mem.instype.prepare(0)
            self.mem.read.prepare(0)
            self.mem.write.prepare(0)
            self.instructionOut.prepare(0)
            self.Address_Out.prepare(0)
            self.Value_Out.prepare(0)
            self.Instruction_fetched.prepare(0)
            self.Executed_Jump.prepare(0)
            self.Address_fetched.prepare(0)
            self.ReadVal.prepare(0)
            self.SPM_Done.prepare(0)
            self.PC_ValueOut.prepare(0)
            self.PC_Load.prepare(0)
            return

        # `pc` tracks what self.PC used to be: seeded from the PC register's
        # current committed value, mutated locally exactly like the old
        # `self.PC = ...` assignments did, and driven back out at the end
        # via PC_ValueOut/PC_Load. pc_load mirrors "did this cycle actually
        # assign a new self.PC" from the original code -- it's set to 1
        # right alongside every former `self.PC = ...` site below.
        pc = self.PC_ValIn.get()
        pc_load = 0

        # ---------------------------------------------------------
        # STATE: STOP - Halt Execution until requested
        # ---------------------------------------------------------
        if self.FSM == 'STOP':
            self.mem.instype.prepare(0)
            self.mem.read.prepare(0)
            self.mem.write.prepare(0)
            
            self.Instruction_fetched.prepare(0)
            self.Address_fetched.prepare(0)
            self.SPM_Done.prepare(0)

            load_jump = self.Load_Jump.get()
            load_z    = self.Load_Z.get()
            load_k    = self.Load_K.get()
            load_pcl  = self.Load_PCL.get()
            load_pch  = self.Load_PCH.get()


            if load_jump == 1 or load_z == 1 or load_k == 1 or load_pcl == 1 or load_pch == 1:
                rel_abs = self.relative_Absolute.get()
                jumped = False
                
                if load_z == 1:
                    # FIX: snapshot the PC *before* overwriting it with Z,
                    # and arm the restore flag so the next LOAD_PCL/LOAD_PCH
                    # pulse (LPM's RESTORE_PC step) pulls the real return
                    # address back out of PC_BUFFER instead of the stale
                    # SRAM/stack data bus.
                    self.PC_BUFFER = pc
                    self._pc_restore_pending = True

                    z_val = (self.address_ZH.get() << 8) | self.address_ZL.get()
                    if rel_abs == 1:
                        # LPM semantics: Z is a BYTE address into program
                        # memory. The PC (and the ROM) are WORD addressed,
                        # so the word address is Z>>1, and Z&1 selects the
                        # low (0) or high (1) byte of the fetched word,
                        # applied at the next FETCH_ADDR_WAIT completion.
                        self._lpm_byte_high = z_val & 1
                        self._lpm_byte_pending = True
                        pc = (z_val >> 1) & 0x3FFF
                        pc_load = 1
                    else:
                        # IJMP/ICALL semantics: Z is already a WORD address.
                        pc = z_val & 0x3FFF
                        pc_load = 1
                    jumped = True
                elif load_jump == 1:
                    if rel_abs == 1:
                        # Absolute Jump (JMP/CALL) - target address is split
                        # across two words: K7_22 carries the HIGH bits from
                        # the first instruction word, and the second ROM word
                        # (fetched earlier via FETCH_ADDR_REQ/WAIT and latched
                        # in self.latched_addr_word) carries the LOW 16 bits.
                        # Using K7_22 alone drops the low bits entirely and
                        # sends the PC to a near-zero address (this was the
                        # bug causing JMP/CALL to jump back near reset).
                        k_val = self._select_K()
                        full_addr = (k_val << 16) | self.latched_addr_word
                        pc = full_addr & 0x3FFF
                        pc_load = 1
                    else:
                        # Relative Jump (RJMP/RCALL) - ALWAYS uses K12
                        k_val = self.K12.get()
                        if k_val & 0x800:
                            offset = k_val - 0x1000
                        else:
                            offset = k_val
                        pc = (pc + offset) & 0x3FFF
                        pc_load = 1
                    jumped = True
                elif load_k == 1:
                    # Conditional Branch (BRBS/BRBC) - uses K7 via K_Select
                    k_val = self._select_K()
                    if k_val & 0x40:
                        offset = k_val - 0x80
                    else:
                        offset = k_val
                    pc = (pc + offset) & 0x3FFF
                    pc_load = 1
                    jumped = True
                    
                
                # FIX: decide ONCE per cycle whether this PCL/PCH load is a
                # restore-from-Z-detour (LPM) or a genuine external load
                # (RET/RETI popping the return address off the stack via
                # PCL_LOAD_VAL/PCH_LOAD_VAL). Computed before either branch
                # runs so both bytes agree on the source this cycle.
                restore_from_buffer = self._pc_restore_pending and (load_pch == 1 or load_pcl == 1)

                if load_pch == 1:
                    if restore_from_buffer:
                        pc = (pc & 0x00FF) | (self.PC_BUFFER & 0x3F00)
                        pc_load = 1
                        if self.debug:
                            print(f"[RomHandler] Restored PCH from PC_BUFFER: {(self.PC_BUFFER >> 8) & 0x3F}")
                    else:
                        pc = (pc & 0x00FF) | ((self.PCH_LOAD_VAL.get() & 0x3F) << 8)
                        pc_load = 1
                        if self.debug:
                            print(f"[RomHandler] Loaded PCH: {self.PCH_LOAD_VAL.get()}")
                if load_pcl == 1:
                    if restore_from_buffer:
                        pc = (pc & 0xFF00) | (self.PC_BUFFER & 0x00FF)
                        pc_load = 1
                        if self.debug:
                            print(f"[RomHandler] Restored PCL from PC_BUFFER: {self.PC_BUFFER & 0xFF}")
                    else:
                        pc = (pc & 0xFF00) | (self.PCL_LOAD_VAL.get() & 0xFF)
                        pc_load = 1
                        if self.debug:
                            print(f"[RomHandler] Loaded PCL: {self.PCL_LOAD_VAL.get()}")

                if restore_from_buffer:
                    # Consumed -- clear so a later, unrelated RET/RETI in a
                    # future instruction goes back to using the bus.
                    self._pc_restore_pending = False
                    self._lpm_byte_pending = False

                pc = pc & 0x3FFF
                pc_load = 1
                
                if jumped:
                    self.Executed_Jump.prepare(1)
                    if self.debug:
                        print(f"[RomHandler] Output set: Executed_Jump=1 (New PC: [{pc:04X}])")
                    self.FSM = 'WAIT_Jump_LOW'
                else:
                    self.Executed_Jump.prepare(0)
                    if self.Fetch_next_instruction.get() == 1:

                        self._pc_restore_pending = False
                        self._lpm_byte_pending = False
                        self.FSM = 'FETCH_REQ'
                    elif self.fetch_address.get() == 1:
                        self.FSM = 'FETCH_ADDR_REQ'
            else:
                self.Executed_Jump.prepare(0)
                if self.Fetch_next_instruction.get() == 1:
                    self._pc_restore_pending = False
                    self._lpm_byte_pending = False
                    self.FSM = 'FETCH_REQ'
                elif self.fetch_address.get() == 1:
                    self.FSM = 'FETCH_ADDR_REQ'
                elif self.LPM_req.get() == 1:
                    self.FSM = 'LPM_REG'
                elif self.SPM_req.get() == 1:
                    self.FSM = 'SPM_REQ'

        # ---------------------------------------------------------
        # STATE: WAIT_Jump_LOW - Hold Executed_Jump until control FSM drops request
        # ---------------------------------------------------------
        elif self.FSM == 'WAIT_Jump_LOW':
            self.mem.instype.prepare(0)
            self.mem.read.prepare(0)
            self.mem.write.prepare(0)
            self.Instruction_fetched.prepare(0)
            self.Address_fetched.prepare(0)
            
            if (self.Load_Jump.get() == 0 and self.Load_Z.get() == 0 and 
                self.Load_K.get() == 0 and self.Load_PCL.get() == 0 and self.Load_PCH.get() == 0):
                self.Executed_Jump.prepare(0)
                self.FSM = 'STOP'
            else:
                self.Executed_Jump.prepare(1)

        # ---------------------------------------------------------
        # STATE: FETCH_REQ - Initiate standard instruction fetch
        # ---------------------------------------------------------
        elif self.FSM == 'FETCH_REQ':
            self.Instruction_fetched.prepare(0)
            self.Executed_Jump.prepare(0)
            self.mem.instype.prepare(1)     
            
            if self.Load_Byte.get() == 1:
                # --- SPM WRITE TRANSACTION ---
                self.mem.write.prepare(1)
                self.mem.read.prepare(0)
                self.mem.address.prepare(pc)
                self.mem.write_data.prepare(self.WriteVal.get())
                self.FSM = 'WRITE_WAIT'
            else:
                # --- NORMAL INSTRUCTION FETCH ---
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.address.prepare(pc)
                self.Address_Out.prepare(pc)
                self.FSM = 'FETCH_WAIT'

        # ---------------------------------------------------------
        # STATE: FETCH_WAIT - Complete standard instruction fetch
        # ---------------------------------------------------------
        elif self.FSM == 'FETCH_WAIT':
            if self.mem.resp.get() == 1:
                self.mem.read.prepare(0)
                self.mem.instype.prepare(0)
                
                fetched_instruction = self.mem.read_data.get()
                self.instructionOut.prepare(fetched_instruction)
                self.Value_Out.prepare(fetched_instruction)
                self.Instruction_fetched.prepare(1)
                
                if self.debug:
                    print(f"[RomHandler] Outputs set: instructionOut=[{fetched_instruction:04X}], Instruction_fetched=1")
                
                # --- PC UPDATE LOGIC (Sequential Only) ---
                # ALWAYS increment by 1 here. Two-word instructions will 
                # increment the PC again dynamically during FETCH_ADDR_WAIT.
                pc = (pc + 1) & 0x3FFF
                pc_load = 1

                self.Executed_Jump.prepare(0)
                self.FSM = 'WAIT_Fetch_next_instruction_LOW'

        # ---------------------------------------------------------
        # STATE: FETCH_ADDR_REQ - Initiate secondary address fetch
        # ---------------------------------------------------------
        elif self.FSM == 'FETCH_ADDR_REQ':
            self.Address_fetched.prepare(0)
            self.Executed_Jump.prepare(0)
            
            self.mem.instype.prepare(1)
            self.mem.write.prepare(0)
            self.mem.read.prepare(1)
            self.mem.address.prepare(pc)
            
            self.FSM = 'FETCH_ADDR_WAIT'

        # ---------------------------------------------------------
        # STATE: FETCH_ADDR_WAIT - Complete secondary address fetch
        # ---------------------------------------------------------
        elif self.FSM == 'FETCH_ADDR_WAIT':
            if self.mem.resp.get() == 1:
                self.mem.read.prepare(0)
                self.mem.instype.prepare(0)
                
                fetched_word = self.mem.read_data.get()

                if self._lpm_byte_pending:
                    # LPM: expose only the byte selected by Z&1 (0 = low
                    # byte, 1 = high byte of the 16-bit flash word).
                    out_val = ((fetched_word >> 8) & 0xFF) if self._lpm_byte_high else (fetched_word & 0xFF)
                    self._lpm_byte_pending = False
                    if self.debug:
                        print(f"[RomHandler] LPM byte select: word={fetched_word:04X} byte_high={self._lpm_byte_high} -> {out_val:02X}")
                else:
                    out_val = fetched_word

                self.Address_Out.prepare(out_val)
                self.Value_Out.prepare(out_val)
                self.Address_fetched.prepare(1)
                self.latched_addr_word = fetched_word  # keep for JMP/CALL PC calc
                
                if self.debug:
                    print(f"[RomHandler] Outputs set: Address_Out=[{out_val:04X}], Address_fetched=1")
                
                pc = (pc + 1) & 0x3FFF
                pc_load = 1
                
                self.FSM = 'WAIT_fetch_address_LOW'

        # ---------------------------------------------------------
        # STATE: WRITE_WAIT - Complete SPM write transaction  
        # ---------------------------------------------------------
        elif self.FSM == 'WRITE_WAIT':
            self.mem.write.prepare(0)
            self.mem.instype.prepare(0)
            
            if self.mem.resp.get() == 1:
                pc = (pc + 1) & 0x3FFF
                pc_load = 1
                self.FSM = 'WAIT_Fetch_next_instruction_LOW'

        # ---------------------------------------------------------
        # TRAP STATES: Wait for handshakes to complete
        # ---------------------------------------------------------
        elif self.FSM == 'WAIT_Fetch_next_instruction_LOW':
            if self.Fetch_next_instruction.get() == 0:
                self.Instruction_fetched.prepare(0)
                self.FSM = 'STOP'

        elif self.FSM == 'WAIT_fetch_address_LOW':
            if self.fetch_address.get() == 0:
                self.Address_fetched.prepare(0)
                self.FSM = 'STOP'
            else:
                self.Address_fetched.prepare(1)


        elif self.FSM == 'LPM_REG':
            if self.LPM_req == 1: 
                self.mem.instype.prepare(0)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.address.prepare(self.R0_BUFFER_IN.get())
                val = ((self.R1_BUFFER_IN<<8)|self.R0_BUFFER_IN.get())
                if self.mem.resp.get() == 1: 
                    self.mem.write_data.prepare(self.mem.read_data.get())
            
            elif self.LPM_req == 2:
                self.mem.instype.prepare(0)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                z_address = ((self.address_ZH.get()<<8)|(self.address_ZL.get())) & 0xFFFF
                self.mem.address.prepare(z_address)
                if self.mem.resp.get() == 1:
                    self.VALUE_OUT.prepare(self.mem.read_data.get())

            elif self.LPM_req == 3:
                self.mem.instype.prepare(0)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                z_address = (((self.address_ZH<<8)|(self.address_ZL))+1) & 0xFFFF
                self.mem.address.prepare(z_address)
                if self.mem.resp.get() == 1:
                    self.VALUE_OUT.prepare(self.mem.read_data.get())
            

        elif self.FSM == 'SPM_REQ':
            self.mem.instype.prepare(1)
            self.mem.write.prepare(1)
            self.mem.read.prepare(0)
            # Z is a BYTE address into flash (same convention LPM uses --
            # see the Load_Z/relative_Absolute=1 path above). Program
            # memory is WORD addressed, so the target word is Z>>1; bit 0
            # of Z is reserved/ignored for SPM (a whole word is written
            # at once, unlike LPM's single-byte reads).
            z_address = (((self.address_ZH.get()<<8)|(self.address_ZL.get())) >> 1) & 0x3FFF
            self.mem.address.prepare(z_address)
            val = ((self.R1_BUFFER_IN.get()<<8)|self.R0_BUFFER_IN.get()) & 0xFFFF
            self.mem.write_data.prepare(val)

            self.SPM_Done.prepare(0)
            if self.mem.resp.get() == 1:
                self.mem.write.prepare(0)
                self.SPM_Done.prepare(1)
                self.FSM = 'STOP'
                
        # ---------------------------------------------------------
        # DEFAULT: Safety fallback
        # ---------------------------------------------------------
        else:
            if self.debug:
                print(f"[RomHandler WARNING] Unknown state '{self.FSM}', resetting to STOP")
            self.FSM = 'STOP'

        # Drive the PC register: pc_load=1 exactly on the cycles the old
        # code would have executed a `self.PC = ...` assignment; pc always
        # carries the fully-resolved value for this cycle either way (equal
        # to the unchanged input when pc_load=0, so PC_ValueOut is always
        # well-defined even though the register only latches it when
        # PC_Load=1).
        self.PC_ValueOut.prepare(pc)
        self.PC_Load.prepare(pc_load)

        # --- STATE CHANGE DETECTION ---
        if previous_state != self.FSM:
            if self.debug:
                print(f"[RomHandler] State changed: {previous_state} -> {self.FSM}")

        if self.debug == 1:
            state_log = (
                f"ROM_STATE | "
                f"State: {self.FSM:15} | "
                f"PC: {pc:04X} | "
                f"FetchReq: {self.Fetch_next_instruction.get()} "
                f"Resp: {self.mem.resp.get()} | "
                f"Inst: {self.instructionOut.get():04X} | "
                f"Jump: {self.Executed_Jump.get()}"
            )
            print(state_log)