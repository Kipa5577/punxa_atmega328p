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

                 # --- Flash programming interface (ISP-style), used only
                 # while RH_reset is asserted -- see ROM_FLASHING_DESIGN.md.
                 # Bit-serial SPI slave: MOSI/SCK are inputs driven by an
                 # external "programmer" (a test driver in this project),
                 # MISO is this component's reply.
                 RH_PROG_MOSI,
                 RH_PROG_SCK,
                 RH_PROG_MISO,

                 # Fallback boot address used when the BOOTRST fuse is
                 # unprogrammed (factory default) -- same value that used
                 # to be the *only* reset address (Datapath's PC reset_value).
                 RH_default_reset_address,

                 RH_reset):     # 1-bit IN: real reset wire (PC's own reset
                                 # value now lives on the PC Reg itself in
                                 # Datapath -- this just resets RomHandler's
                                 # FSM/private state)
        
        super().__init__(parent, name)

        # --- Internal (private to RomHandler, NOT the architectural PC --
        #     see class docstring / spec: these are snapshot/latch state
        #     used to sequence multi-cycle ROM transactions, reset below) ---
        self.PC_BUFFER = 0

        # FIX: This flag makes the Load_Z -> LOAD_PCL/LOAD_PCH sequence
        # self-contained inside RomHandler. When something (LPM/LPMZ/LPMZ+)
        # redirects the PC to Z to read a ROM byte, we snapshot the PC into
        # PC_BUFFER at that moment. The very next time LOAD_PCL/LOAD_PCH are
        # asserted, we restore PC from PC_BUFFER instead of from
        # PCL_LOAD_VAL/PCH_LOAD_VAL (which is just MemoryInterfaceHandler's
        # SRAM/stack data bus -- correct for RET/RETI's stack pop, but never
        # driven with anything meaningful for the LPM detour). Previously
        # PC_BUFFER was declared but never used, so LPM's "restore PC" step
        # silently loaded PC from stale bus data (usually 0), sending
        # execution back to address 0 instead of resuming after the LPM
        # instruction.
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

        # --- Flash programming interface ---
        self.PROG_MOSI = self.addIn('PROG_MOSI', RH_PROG_MOSI)
        self.PROG_SCK  = self.addIn('PROG_SCK', RH_PROG_SCK)
        self.PROG_MISO = self.addOut('PROG_MISO', RH_PROG_MISO)

        self.default_reset_address = RH_default_reset_address

        # Programming-mode state. All of this is non-volatile in the same
        # sense ins_mem is -- NOT touched by the `reset` branch below,
        # only by explicit programming instructions or, for the shift
        # register bookkeeping, by naturally idling back to 'IDLE' between
        # instructions. See ROM_FLASHING_DESIGN.md sections 4.1/4.3/4.4.
        self._prog_state = 'IDLE'      # 'IDLE' | 'ERASE_BUSY' | 'WRITE_PAGE_BUSY'
        self._prog_shift_reg = 0       # accumulates up to 32 bits, MSB-first
        self._prog_bit_count = 0       # 0..32 bits shifted in for the current instruction
        self._prog_prev_sck = 0        # for edge detection
        self._prog_enabled = False     # True once Programming Enable has been accepted
        self._prog_page_buffer = [0] * 64  # word buffer for Load Program Memory Page
        self._prog_miso_shift = 0      # byte currently being shifted out on MISO
        self._prog_reply_armed = False # True once _prog_miso_shift holds a real reply
        self._prog_last_miso_bit = 0   # held between edges (SPI mode 0: MISO stable between clocks)
        self._prog_erase_addr = 0      # next word address for the Chip Erase loop
        self._prog_write_page_addr = 0     # base word address of the page being committed
        self._prog_write_page_offset = 0   # 0..63, which word of the page is being written now
        self._prog_saw_resp_low = False    # edge-detect guard for _prog_erase_step/_prog_write_page_step
        self._prog_pending_flash_read = None  # (addr, is_high_byte) between bit 24 and bit 25
        self._prog_pending_reply = None  # reply byte staged between decode bit N and arm bit N+1

        # Fuse bytes. Non-volatile, like ins_mem and the programming state
        # above -- NOT reset by the `reset` wire. Defaults match a
        # factory-fresh ATmega328P (datasheet fuse defaults): only
        # High[0] (BOOTRST) and High[2:1] (BOOTSZ1:0) are ever actually
        # read by this model (see _fuse_boot_address below); the low and
        # extended bytes, and the rest of the high byte, are stored and
        # readable/writable purely so a real fuse-programming tool's
        # read-modify-write sequences don't corrupt BOOTRST/BOOTSZ by
        # writing over bits it doesn't care about -- nothing here models
        # CKSEL/SUT/WDTON/EESAVE/BODLEVEL/RSTDISBL/DWEN/CKDIV8/CKOUT, this
        # simulator has no clock/BOD/EEPROM/debugWIRE to wire them to.
        self._fuse_low = 0x62
        self._fuse_high = 0xD9
        self._fuse_extended = 0xFF

        self._prev_reset = 0           # for the reset *falling*-edge check (§4.6)

        self.debug = 1

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

            # NOTE: mem.instype/read/write are intentionally NOT prepared
            # here (unlike every other output below) -- while reset is
            # asserted, _run_programming_protocol() below owns all three
            # of those wires exclusively, preparing each exactly once per
            # cycle to actually drive the flash reads/writes/erases this
            # mode needs. A second prepare() call here on top of that
            # would be exactly the double-prepare bug already fixed once
            # for SPM_REQ.
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

            # While reset is asserted, RomHandler is the only component in
            # the whole CPU still doing anything (every other component is
            # already held at its own reset value by the same top-level
            # reset wire -- see ROM_FLASHING_DESIGN.md §3.1). Put that idle
            # time to use running the ISP flash-programming protocol
            # against PROG_MOSI/PROG_SCK/PROG_MISO instead of just sitting
            # here. This intentionally runs *after* the normal-FSM state
            # above has already been forced to a safe idle 'STOP' snapshot,
            # and does not touch any of it.
            self._prev_reset = 1
            self._run_programming_protocol()
            return

        # Reset falling-edge check: on the one cycle immediately after
        # reset was last seen asserted, inject the fuse-derived boot
        # address into PC before anything else runs this cycle. See
        # ROM_FLASHING_DESIGN.md §4.6 for why this can't just be PC's own
        # `reset_value` (that's a fixed Python constant baked in at
        # construction time; BOOTRST/BOOTSZ can change at runtime via a
        # Write Fuse High bits instruction, so the boot address has to be
        # injected the same way every other PC update already happens --
        # through PC_ValueOut/PC_Load below).
        just_released = (self._prev_reset == 1)
        self._prev_reset = 0

        # `pc` tracks what self.PC used to be: seeded from the PC register's
        # current committed value, mutated locally exactly like the old
        # `self.PC = ...` assignments did, and driven back out at the end
        # via PC_ValueOut/PC_Load. pc_load mirrors "did this cycle actually
        # assign a new self.PC" from the original code -- it's set to 1
        # right alongside every former `self.PC = ...` site below.
        pc = self.PC_ValIn.get()
        pc_load = 0

        if just_released:
            pc = self._fuse_boot_address()
            pc_load = 1

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
                        # FIX (safety net): a real jump (IJMP/ICALL via Z)
                        # that never gets followed by a LOAD_PCL/LOAD_PCH
                        # restore should not leave _pc_restore_pending
                        # armed for some unrelated later instruction.
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
            self.mem.read.prepare(0)
            # Z is a BYTE address into flash (same convention LPM uses --
            # see the Load_Z/relative_Absolute=1 path above). Program
            # memory is WORD addressed, so the target word is Z>>1; bit 0
            # of Z is reserved/ignored for SPM (a whole word is written
            # at once, unlike LPM's single-byte reads).
            z_address = (((self.address_ZH.get()<<8)|(self.address_ZL.get())) >> 1) & 0x3FFF
            self.mem.address.prepare(z_address)
            # FIX: R1_BUFFER_IN was used without .get() -- shifting the
            # Pin object itself instead of its value.
            val = ((self.R1_BUFFER_IN.get()<<8)|self.R0_BUFFER_IN.get()) & 0xFFFF
            self.mem.write_data.prepare(val)

            # FIX: mem.write and SPM_Done used to be prepare()'d
            # unconditionally above *and then* prepare()'d again inside
            # this if-branch on the completion cycle -- two prepare()
            # calls on the same wire in the same clock() invocation,
            # which is exactly what the "wire already prepared" warning
            # flags. Compute resp first and prepare each wire exactly
            # once based on it, same fix pattern as the SREG read-branch
            # redundant write.prepare(0) removal noted elsewhere in this
            # file's history.
            if self.mem.resp.get() == 1:
                self.mem.write.prepare(0)
                self.SPM_Done.prepare(1)
                # FIX: this used to go straight back to 'STOP'. Every
                # other multi-cycle transaction in this FSM (FETCH_REQ,
                # FETCH_ADDR_REQ, ...) returns through a dedicated
                # "WAIT_..._LOW" trap state that holds until the
                # requesting FSM actually drops its request line -- SPM
                # was missing that. LPM_FSM's SPM_WAIT_DONE state can't
                # drop SPM_req until *it* observes SPM_Done=1, which
                # (like every other cross-component signal here) lags a
                # cycle behind RomHandler's own internal completion. Going
                # straight to STOP meant RomHandler sampled SPM_req still
                # high on that very next cycle and mistook it for a brand
                # new request, re-entering SPM_REQ and performing a second
                # (harmless but spurious) write of the same word -- the
                # source of the "wire already prepared" warnings the very
                # first real SPM test run surfaced. Mirrors
                # WAIT_Fetch_next_instruction_LOW/WAIT_fetch_address_LOW.
                self.FSM = 'WAIT_SPM_req_LOW'
            else:
                self.mem.write.prepare(1)
                self.SPM_Done.prepare(0)

        elif self.FSM == 'WAIT_SPM_req_LOW':
            self.mem.write.prepare(0)
            self.mem.instype.prepare(0)
            if self.SPM_req.get() == 0:
                self.SPM_Done.prepare(0)
                self.FSM = 'STOP'
            else:
                self.SPM_Done.prepare(1)
                
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

    # =================================================================
    # Fuse-derived boot address (ROM_FLASHING_DESIGN.md §1.4 / §4.6)
    # =================================================================
    _BOOTSZ_ADDRESS = {
        0b00: 0x3800,   # 2048-word boot section
        0b01: 0x3C00,   # 1024-word boot section
        0b10: 0x3E00,   # 512-word boot section
        0b11: 0x3F00,   # 256-word boot section (factory-default BOOTSZ,
                         # irrelevant while BOOTRST is also at its
                         # factory-default unprogrammed state)
    }

    def _fuse_boot_address(self):
        bootrst = self._fuse_high & 0x01
        if bootrst == 0:   # programmed -> reset vector is the boot section
            bootsz = (self._fuse_high >> 1) & 0x03
            return self._BOOTSZ_ADDRESS[bootsz]
        return self.default_reset_address   # unprogrammed (factory default)

    # =================================================================
    # ISP flash-programming protocol (ROM_FLASHING_DESIGN.md §4.3-§4.5)
    # =================================================================
    def _run_programming_protocol(self):
        if self._prog_state == 'ERASE_BUSY':
            self._prog_erase_step()
            return
        if self._prog_state == 'WRITE_PAGE_BUSY':
            self._prog_write_page_step()
            return

        # 'IDLE': bit-serial SPI slave, MOSI sampled on the rising edge of
        # SCK, MISO driven on the falling edge (SPI mode 0, matching the
        # real part -- ROM_FLASHING_DESIGN.md §1). Default to no ins_mem
        # traffic; _prog_on_sck_rising may override this exactly once
        # below if this cycle is a Read Program Memory instruction's
        # decode point -- deciding first and calling .prepare() exactly
        # once per wire avoids the double-prepare bug already fixed once
        # in SPM_REQ (see that state's own comment for the story).
        mem_read = 0
        mem_addr = 0

        sck = self.PROG_SCK.get()
        mosi = self.PROG_MOSI.get()
        prev_sck = self._prog_prev_sck
        self._prog_prev_sck = sck

        if sck == 1 and prev_sck == 0:
            mem_read, mem_addr = self._prog_on_sck_rising(mosi)
        elif sck == 0 and prev_sck == 1:
            self._prog_on_sck_falling()
        else:
            # No edge this cycle -- hold MISO at whatever it last drove
            # (SPI mode 0: MISO is stable between clock edges).
            self.PROG_MISO.prepare(self._prog_last_miso_bit)

        self.mem.instype.prepare(1 if mem_read else 0)
        self.mem.read.prepare(mem_read)
        self.mem.write.prepare(0)
        self.mem.address.prepare(mem_addr)

    def _prog_on_sck_rising(self, mosi):
        """Returns (mem_read, mem_addr) for this cycle -- the only two
        ins_mem-facing wires this path ever needs to drive (a plain,
        single-cycle read request); everything else is prepared once by
        the caller. See _run_programming_protocol for why."""
        mem_read = 0
        mem_addr = 0

        self._prog_shift_reg = ((self._prog_shift_reg << 1) | (mosi & 1)) & 0xFFFFFFFF
        self._prog_bit_count += 1

        # Timing note (this took a real bug to find -- see the git log
        # for the story): a reply's first bit must ship on the falling
        # edge of the *first bit of the byte it replies in*, not on the
        # falling edge of the last bit of the *preceding* byte. Arming
        # `_prog_reply_armed`/`_prog_miso_shift` as soon as a decode
        # point is reached (bit 16 for Programming Enable's byte-3 echo,
        # bit 24 for everything else's byte-4 reply) shifts the whole
        # reply one bit early, because that decode bit's *own* falling
        # edge immediately follows and would already start shifting.
        # The fix: decide what to reply at bit N (16 or 24), but only
        # actually set `_prog_reply_armed` on bit N+1's rising edge --
        # its own falling edge, immediately after, is genuinely the
        # first bit of the reply byte. `_prog_pending_reply` carries the
        # decided value across that one-bit gap.
        if self._prog_bit_count == 16:
            b0 = (self._prog_shift_reg >> 8) & 0xFF
            b1 = self._prog_shift_reg & 0xFF
            if b0 == 0xAC and b1 == 0x53:
                self._prog_pending_reply = 0x53

        elif self._prog_bit_count == 17 and self._prog_pending_reply is not None:
            self._prog_miso_shift = self._prog_pending_reply
            self._prog_reply_armed = True
            self._prog_pending_reply = None

        # Generic instructions with a byte-4 reply are fully addressable
        # once bytes 0-2 (24 bits) are in. Poll RDY/BSY and the Read Fuse
        # instructions read plain Python attributes (no wire latency);
        # Read Program Memory has to go through `self.mem`, which --
        # like every other cross-component wire in this design -- only
        # reflects a request one full cycle after it's issued (the same
        # class of bug the SPM Z-sync/R1-settle fixes were for). Issuing
        # the read at bit 24 and sampling its result at bit 25 (rather
        # than deciding the reply value at bit 24 like the others) turns
        # out to satisfy *both* needs at once: it's simultaneously the
        # one-cycle settle the wire read needs, and the one-bit
        # realignment every reply needs per the note above -- so unlike
        # Programming Enable's 16/17 split, there's no separate "pending"
        # step here, bit 25 both decides and arms.
        elif self._prog_bit_count == 24:
            b0 = (self._prog_shift_reg >> 16) & 0xFF
            b1 = (self._prog_shift_reg >> 8) & 0xFF
            b2 = (self._prog_shift_reg >> 0) & 0xFF
            if b0 == 0xF0:
                self._prog_pending_reply = 1 if self._prog_state != 'IDLE' else 0
            elif b0 == 0x50 and b1 == 0x00:
                self._prog_pending_reply = self._fuse_low
            elif b0 == 0x58 and b1 == 0x08:
                self._prog_pending_reply = self._fuse_high
            elif b0 == 0x50 and b1 == 0x08:
                self._prog_pending_reply = self._fuse_extended
            elif b0 in (0x20, 0x28):
                addr = ((b1 << 8) | b2) & 0x3FFF
                mem_read = 1
                mem_addr = addr
                self._prog_pending_flash_read = (addr, b0 == 0x28)

        elif self._prog_bit_count == 25:
            if self._prog_pending_flash_read is not None:
                addr, high = self._prog_pending_flash_read
                self._prog_pending_flash_read = None
                word = self.mem.read_data.get()
                self._prog_miso_shift = (word >> 8) & 0xFF if high else word & 0xFF
                self._prog_reply_armed = True
            elif self._prog_pending_reply is not None:
                self._prog_miso_shift = self._prog_pending_reply
                self._prog_reply_armed = True
                self._prog_pending_reply = None

        if self._prog_bit_count == 32:
            self._prog_execute(self._prog_shift_reg)
            # NOTE: do not reset shift_reg/bit_count here -- the 32nd
            # bit's own falling edge (which drives the last reply bit,
            # if any) still needs _prog_bit_count == 32 to be visible to
            # _prog_on_sck_falling(). Cleared there instead.

        return mem_read, mem_addr

    def _prog_on_sck_falling(self):
        if self._prog_reply_armed:
            bit = (self._prog_miso_shift >> 7) & 1
            self._prog_miso_shift = (self._prog_miso_shift << 1) & 0xFF
        else:
            bit = 0
        self._prog_last_miso_bit = bit
        self.PROG_MISO.prepare(bit)

        if self._prog_bit_count == 32:
            self._prog_shift_reg = 0
            self._prog_bit_count = 0
            self._prog_reply_armed = False

    def _prog_execute(self, instruction):
        b0 = (instruction >> 24) & 0xFF
        b1 = (instruction >> 16) & 0xFF
        b2 = (instruction >> 8) & 0xFF
        b3 = instruction & 0xFF

        if b0 == 0xAC and b1 == 0x53:
            self._prog_enabled = True
            return

        if not self._prog_enabled:
            return  # every instruction below requires Programming Enable first

        if b0 == 0xAC and b1 == 0x80:          # Chip Erase
            self._prog_erase_addr = 0
            self._prog_state = 'ERASE_BUSY'
            self._prog_saw_resp_low = False
            # This instruction never gets its bit-32 falling-edge cleanup
            # (the very next cycle short-circuits straight into
            # _prog_erase_step, bypassing _prog_on_sck_falling entirely),
            # so reset the shift-register bookkeeping here instead --
            # otherwise the next instruction's bit counting would start
            # from a stale bit_count=32. _prog_prev_sck also has to reset
            # to 0 here: it's only ever updated by the IDLE bit-banging
            # path, so it would otherwise sit stuck at whatever it was
            # during bit 32's rising edge (1) for the *entire* busy
            # period and beyond, desyncing rising/falling edge detection
            # for the next instruction the moment SPI traffic resumes
            # (confirmed by tracing the very first multi-page flash test
            # of this loop: every instruction after the first busy
            # operation came out corrupted because of exactly this).
            self._prog_bit_count = 0
            self._prog_shift_reg = 0
            self._prog_reply_armed = False
            self._prog_prev_sck = 0

        elif b0 == 0x40:                       # Load Program Memory Page, low byte
            word_in_page = b2 & 0x3F
            self._prog_page_buffer[word_in_page] = (
                (self._prog_page_buffer[word_in_page] & 0xFF00) | b3)

        elif b0 == 0x48:                       # Load Program Memory Page, high byte
            word_in_page = b2 & 0x3F
            self._prog_page_buffer[word_in_page] = (
                (self._prog_page_buffer[word_in_page] & 0x00FF) | (b3 << 8))

        elif b0 == 0x4C:                       # Write Program Memory Page
            page = ((b1 << 3) | (b2 >> 5)) & 0xFF
            self._prog_write_page_addr = page * 64
            self._prog_write_page_offset = 0
            self._prog_state = 'WRITE_PAGE_BUSY'
            self._prog_saw_resp_low = False
            # Same reasoning as Chip Erase above.
            self._prog_bit_count = 0
            self._prog_shift_reg = 0
            self._prog_reply_armed = False
            self._prog_prev_sck = 0

        elif b0 == 0xAC and b1 == 0xA0:        # Write Fuse bits (Low)
            self._fuse_low = b3

        elif b0 == 0xAC and b1 == 0xA8:        # Write Fuse High bits
            self._fuse_high = b3

        elif b0 == 0xAC and b1 == 0xA4:        # Write Extended Fuse bits
            self._fuse_extended = b3

        # 0x20/0x28/0xF0/0x50.../0x58... (reads) and anything unrecognized
        # need no further action here -- their reply, if any, was already
        # armed by _prog_reply_for at the 24-bit mark.

    def _prog_erase_step(self):
        """One word of Chip Erase per call -- same single-word
        write+resp-handshake pattern SPM_REQ already uses, PLUS the
        resp-edge-detection guard LPM_FSM's back-to-back register reads
        already needed for the identical reason (see its
        _saw_resp_low): looping this same write request repeatedly means
        a stale resp=1 left over from the *previous* word's completion
        can otherwise be mistaken for the *next* word's completion
        before its own write was ever actually issued -- confirmed by
        tracing this exact hazard skipping every other word on the very
        first real multi-word test of this loop. Fills the entire
        16384-word ins_mem with 0xFFFF (erased-flash convention),
        matching the real instruction's scope (whole-chip, not
        page-granular)."""
        addr = self._prog_erase_addr
        self.mem.instype.prepare(1)
        self.mem.read.prepare(0)
        self.mem.address.prepare(addr)
        self.mem.write_data.prepare(0xFFFF)

        resp = self.mem.resp.get()
        if resp == 0:
            self._prog_saw_resp_low = True

        if resp == 1 and self._prog_saw_resp_low:
            self.mem.write.prepare(0)
            self._prog_saw_resp_low = False
            self._prog_erase_addr += 1
            if self._prog_erase_addr >= 16384:
                self._prog_state = 'IDLE'
        else:
            self.mem.write.prepare(1)

        self.PROG_MISO.prepare(0)

    def _prog_write_page_step(self):
        """One word of the buffered page per call, same handshake
        pattern (and same resp-edge-detection guard) as
        _prog_erase_step above."""
        offset = self._prog_write_page_offset
        addr = self._prog_write_page_addr + offset
        self.mem.instype.prepare(1)
        self.mem.read.prepare(0)
        self.mem.address.prepare(addr)
        self.mem.write_data.prepare(self._prog_page_buffer[offset])

        resp = self.mem.resp.get()
        if resp == 0:
            self._prog_saw_resp_low = True

        if resp == 1 and self._prog_saw_resp_low:
            self.mem.write.prepare(0)
            self._prog_saw_resp_low = False
            self._prog_write_page_offset += 1
            if self._prog_write_page_offset >= 64:
                self._prog_state = 'IDLE'
        else:
            self.mem.write.prepare(1)

        self.PROG_MISO.prepare(0)
