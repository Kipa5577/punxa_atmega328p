# Integer state encoding (was string-based; converted for
# stock py4hw Verilog-transpiler compatibility -- see report):
#   0 = 'STOP'
#   1 = 'WAIT_Jump_LOW'
#   2 = 'FETCH_REQ'
#   3 = 'FETCH_ADDR_REQ'
#   4 = 'WRITE_WAIT'
#   5 = 'FETCH_WAIT'
#   6 = 'LPM_REG'
#   7 = 'WAIT_Fetch_next_instruction_LOW'
#   8 = 'FETCH_ADDR_WAIT'
#   9 = 'SPM_REQ'
#   10 = 'WAIT_fetch_address_LOW'
#   11 = 'WAIT_SPM_req_LOW'

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
                 default_reset_address,

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
        self._pc_restore_pending = 0  # was False; int form required for the stock transpiler's __init__ parser (see report)

        # LPM byte-address support: Load_Z asserted together with
        # relative_Absolute=1 means Z is a BYTE address (LPM semantics),
        # so the PC gets Z>>1 (word address) and Z&1 selects which byte
        # of the fetched word is exposed on the next FETCH_ADDR_WAIT
        # completion. Load_Z with relative_Absolute=0 keeps the legacy
        # word-address semantics used by IJMP/ICALL.
        self._lpm_byte_pending = 0  # was False; int form required for the stock transpiler's __init__ parser (see report)
        self._lpm_byte_high = 0

        self.FSM = 0           # State machine initial state
        self.latched_addr_word = 0  # Latches the 2nd-word (low bits) fetched
                                     # during FETCH_ADDR_WAIT, for JMP/CALL
        
        # Memory interface: we are the SOURCE (master/initiator)
        # NOTE: was `self.mem = self.addInterfaceSource('ins', RH_mem)`,
        # then accessed in clock() as self.ins_instype/.read/.write/
        # .address/.write_data/.read_data/.resp. Replaced with individual
        # flat addOut/addIn calls on the same underlying wires for two
        # reasons (see py4hw_bug_reports.md, Issue 6):
        #   (a) ExtractInitializers' __init__ parser doesn't recognize
        #       addInterfaceSource at all (only addIn/addOut/
        #       addInterfaceSink), so `self.mem = self.addInterfaceSource(...)`
        #       silently registered a single bogus empty-named wire instead
        #       of the interface's real signals.
        #   (b) Even for addInterfaceSink, the transpiler's wire-name
        #       resolution (ReplaceWireCalls/getAstName) only ever uses the
        #       LAST segment of an attribute chain, so `self.ins_instype`
        #       would resolve to a wire named `instype` -- which doesn't
        #       exist; the real port addInterfaceSource actually registers
        #       is named `ins_instype` (prefix + signal name).
        # This form uses only the already-correctly-handled
        # `self.X = self.addOut('X', wire)` pattern, with X matching
        # exactly the real port name, sidestepping both bugs.
        self.ins_read      = self.addOut('ins_read', RH_mem.read)
        self.ins_write     = self.addOut('ins_write', RH_mem.write)
        self.ins_address   = self.addOut('ins_address', RH_mem.address)
        self.ins_writedata = self.addOut('ins_writedata', RH_mem.write_data)
        self.ins_instype   = self.addOut('ins_instype', RH_mem.instype)
        self.ins_readdata  = self.addIn('ins_readdata', RH_mem.read_data)
        self.ins_resp      = self.addIn('ins_resp', RH_mem.resp)

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

        self.Load_Byte = self.addIn('Load_Byte',RH_Load_Byte)

        # ---- SPM and LPM instructions -----
        self.WriteVal = self.addIn('WriteVal',RH_WriteVal)
        self.ReadVal = self.addOut('ReadVal',RH_ReadVal)

        self.LPM_req = self.addIn('LPM_req',RH_LPM_req)
        self.SPM_req = self.addIn('SPM_req',RH_SPM_req)

        self.R0_BUFFER_IN = self.addIn('R0_BUFFER_IN',RH_R0_BUFFER_IN)
        self.R1_BUFFER_IN = self.addIn('R1_BUFFER_IN',RH_R1_BUFFER_IN)

        self.SPM_Done = self.addOut('SPM_Done', RH_SPM_Done)

        # --- Flash programming interface ---
        self.PROG_MOSI = self.addIn('PROG_MOSI', RH_PROG_MOSI)
        self.PROG_SCK  = self.addIn('PROG_SCK', RH_PROG_SCK)
        self.PROG_MISO = self.addOut('PROG_MISO', RH_PROG_MISO)

        self.default_reset_address = default_reset_address

        # Programming-mode state. All of this is non-volatile in the same
        # sense ins_mem is -- NOT touched by the `reset` branch below,
        # only by explicit programming instructions or, for the shift
        # register bookkeeping, by naturally idling back to 'IDLE' between
        # instructions. See ROM_FLASHING_DESIGN.md sections 4.1/4.3/4.4.
        # _prog_state encoding (was string-based; converted for stock
        # py4hw Verilog-transpiler compatibility -- see report):
        #   0 = 'IDLE', 1 = 'ERASE_BUSY', 2 = 'WRITE_PAGE_BUSY'
        self._prog_state = 0
        self._prog_shift_reg = 0
        self._prog_bit_count = 0
        self._prog_prev_sck = 0
        self._prog_enabled = 0
        # Page buffer: one discrete 16-bit register per word (0..63) --
        # replaces the old Python list (self._prog_page_buffer = [0]*64).
        # A list indexed by a runtime value is a RAM; the stock transpiler
        # has no array/RAM support in __init__ (see report).
        self._prog_page_00 = 0
        self._prog_page_01 = 0
        self._prog_page_02 = 0
        self._prog_page_03 = 0
        self._prog_page_04 = 0
        self._prog_page_05 = 0
        self._prog_page_06 = 0
        self._prog_page_07 = 0
        self._prog_page_08 = 0
        self._prog_page_09 = 0
        self._prog_page_10 = 0
        self._prog_page_11 = 0
        self._prog_page_12 = 0
        self._prog_page_13 = 0
        self._prog_page_14 = 0
        self._prog_page_15 = 0
        self._prog_page_16 = 0
        self._prog_page_17 = 0
        self._prog_page_18 = 0
        self._prog_page_19 = 0
        self._prog_page_20 = 0
        self._prog_page_21 = 0
        self._prog_page_22 = 0
        self._prog_page_23 = 0
        self._prog_page_24 = 0
        self._prog_page_25 = 0
        self._prog_page_26 = 0
        self._prog_page_27 = 0
        self._prog_page_28 = 0
        self._prog_page_29 = 0
        self._prog_page_30 = 0
        self._prog_page_31 = 0
        self._prog_page_32 = 0
        self._prog_page_33 = 0
        self._prog_page_34 = 0
        self._prog_page_35 = 0
        self._prog_page_36 = 0
        self._prog_page_37 = 0
        self._prog_page_38 = 0
        self._prog_page_39 = 0
        self._prog_page_40 = 0
        self._prog_page_41 = 0
        self._prog_page_42 = 0
        self._prog_page_43 = 0
        self._prog_page_44 = 0
        self._prog_page_45 = 0
        self._prog_page_46 = 0
        self._prog_page_47 = 0
        self._prog_page_48 = 0
        self._prog_page_49 = 0
        self._prog_page_50 = 0
        self._prog_page_51 = 0
        self._prog_page_52 = 0
        self._prog_page_53 = 0
        self._prog_page_54 = 0
        self._prog_page_55 = 0
        self._prog_page_56 = 0
        self._prog_page_57 = 0
        self._prog_page_58 = 0
        self._prog_page_59 = 0
        self._prog_page_60 = 0
        self._prog_page_61 = 0
        self._prog_page_62 = 0
        self._prog_page_63 = 0
        self._prog_miso_shift = 0
        self._prog_reply_armed = 0
        self._prog_last_miso_bit = 0
        self._prog_erase_addr = 0
        self._prog_write_page_addr = 0
        self._prog_write_page_offset = 0
        self._prog_saw_resp_low = 0
        self._prog_pending_flash_valid = 0
        self._prog_pending_flash_addr = 0
        self._prog_pending_flash_high = 0
        self._prog_pending_reply_valid = 0
        self._prog_pending_reply_value = 0

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
            self.FSM = 0
            self.PC_BUFFER = 0
            self._pc_restore_pending = 0
            self._lpm_byte_pending = 0
            self._lpm_byte_high = 0
            self.latched_addr_word = 0

            # NOTE: mem.instype/read/write are intentionally NOT prepared
            # here (unlike every other output below) -- while reset is
            # asserted, the inlined ISP programming protocol below owns
            # all three of those wires exclusively, preparing each exactly
            # once per cycle to actually drive the flash reads/writes/
            # erases this mode needs.
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
            # reset wire). Put that idle time to use running the ISP
            # flash-programming protocol against PROG_MOSI/PROG_SCK/
            # PROG_MISO instead of just sitting here.
            self._prev_reset = 1

            # ============================================================
            # Inlined ISP flash-programming protocol (was
            # _run_programming_protocol() / _prog_on_sck_rising() /
            # _prog_on_sck_falling() / _prog_execute() -- the stock
            # transpiler does not expand calls to helper methods from
            # clock(), see report). _prog_state encoding: 0 = IDLE,
            # 1 = ERASE_BUSY, 2 = WRITE_PAGE_BUSY.
            # ============================================================
            if self._prog_state == 1:
                # Inlined _prog_erase_step(): one word of Chip Erase per
                # call, filling the whole 16384-word ins_mem with 0xFFFF.
                addr = self._prog_erase_addr
                self.ins_instype.prepare(1)
                self.ins_read.prepare(0)
                self.ins_address.prepare(addr)
                self.ins_writedata.prepare(0xFFFF)

                resp = self.ins_resp.get()
                if resp == 0:
                    self._prog_saw_resp_low = 1

                if (resp == 1) and (self._prog_saw_resp_low):
                    self.ins_write.prepare(0)
                    self._prog_saw_resp_low = 0
                    self._prog_erase_addr += 1
                    if self._prog_erase_addr >= 16384:
                        self._prog_state = 0
                else:
                    self.ins_write.prepare(1)

                self.PROG_MISO.prepare(0)

            elif self._prog_state == 2:
                # Inlined _prog_write_page_step(): one word of the
                # buffered page per call.
                offset = self._prog_write_page_offset
                addr = self._prog_write_page_addr + offset
                self.ins_instype.prepare(1)
                self.ins_read.prepare(0)
                self.ins_address.prepare(addr)

                # Inlined page-buffer read dispatch (was
                # self._prog_page_buffer[offset] -- see report, no
                # array/RAM support in the stock transpiler).
                if offset == 0:
                    page_word = self._prog_page_00
                elif offset == 1:
                    page_word = self._prog_page_01
                elif offset == 2:
                    page_word = self._prog_page_02
                elif offset == 3:
                    page_word = self._prog_page_03
                elif offset == 4:
                    page_word = self._prog_page_04
                elif offset == 5:
                    page_word = self._prog_page_05
                elif offset == 6:
                    page_word = self._prog_page_06
                elif offset == 7:
                    page_word = self._prog_page_07
                elif offset == 8:
                    page_word = self._prog_page_08
                elif offset == 9:
                    page_word = self._prog_page_09
                elif offset == 10:
                    page_word = self._prog_page_10
                elif offset == 11:
                    page_word = self._prog_page_11
                elif offset == 12:
                    page_word = self._prog_page_12
                elif offset == 13:
                    page_word = self._prog_page_13
                elif offset == 14:
                    page_word = self._prog_page_14
                elif offset == 15:
                    page_word = self._prog_page_15
                elif offset == 16:
                    page_word = self._prog_page_16
                elif offset == 17:
                    page_word = self._prog_page_17
                elif offset == 18:
                    page_word = self._prog_page_18
                elif offset == 19:
                    page_word = self._prog_page_19
                elif offset == 20:
                    page_word = self._prog_page_20
                elif offset == 21:
                    page_word = self._prog_page_21
                elif offset == 22:
                    page_word = self._prog_page_22
                elif offset == 23:
                    page_word = self._prog_page_23
                elif offset == 24:
                    page_word = self._prog_page_24
                elif offset == 25:
                    page_word = self._prog_page_25
                elif offset == 26:
                    page_word = self._prog_page_26
                elif offset == 27:
                    page_word = self._prog_page_27
                elif offset == 28:
                    page_word = self._prog_page_28
                elif offset == 29:
                    page_word = self._prog_page_29
                elif offset == 30:
                    page_word = self._prog_page_30
                elif offset == 31:
                    page_word = self._prog_page_31
                elif offset == 32:
                    page_word = self._prog_page_32
                elif offset == 33:
                    page_word = self._prog_page_33
                elif offset == 34:
                    page_word = self._prog_page_34
                elif offset == 35:
                    page_word = self._prog_page_35
                elif offset == 36:
                    page_word = self._prog_page_36
                elif offset == 37:
                    page_word = self._prog_page_37
                elif offset == 38:
                    page_word = self._prog_page_38
                elif offset == 39:
                    page_word = self._prog_page_39
                elif offset == 40:
                    page_word = self._prog_page_40
                elif offset == 41:
                    page_word = self._prog_page_41
                elif offset == 42:
                    page_word = self._prog_page_42
                elif offset == 43:
                    page_word = self._prog_page_43
                elif offset == 44:
                    page_word = self._prog_page_44
                elif offset == 45:
                    page_word = self._prog_page_45
                elif offset == 46:
                    page_word = self._prog_page_46
                elif offset == 47:
                    page_word = self._prog_page_47
                elif offset == 48:
                    page_word = self._prog_page_48
                elif offset == 49:
                    page_word = self._prog_page_49
                elif offset == 50:
                    page_word = self._prog_page_50
                elif offset == 51:
                    page_word = self._prog_page_51
                elif offset == 52:
                    page_word = self._prog_page_52
                elif offset == 53:
                    page_word = self._prog_page_53
                elif offset == 54:
                    page_word = self._prog_page_54
                elif offset == 55:
                    page_word = self._prog_page_55
                elif offset == 56:
                    page_word = self._prog_page_56
                elif offset == 57:
                    page_word = self._prog_page_57
                elif offset == 58:
                    page_word = self._prog_page_58
                elif offset == 59:
                    page_word = self._prog_page_59
                elif offset == 60:
                    page_word = self._prog_page_60
                elif offset == 61:
                    page_word = self._prog_page_61
                elif offset == 62:
                    page_word = self._prog_page_62
                elif offset == 63:
                    page_word = self._prog_page_63
                else:
                    page_word = 0
                self.ins_writedata.prepare(page_word)

                resp = self.ins_resp.get()
                if resp == 0:
                    self._prog_saw_resp_low = 1

                if (resp == 1) and (self._prog_saw_resp_low):
                    self.ins_write.prepare(0)
                    self._prog_saw_resp_low = 0
                    self._prog_write_page_offset += 1
                    if self._prog_write_page_offset >= 64:
                        self._prog_state = 0
                else:
                    self.ins_write.prepare(1)

                self.PROG_MISO.prepare(0)

            else:
                # IDLE: bit-serial SPI slave, MOSI sampled on the rising
                # edge of SCK, MISO driven on the falling edge (SPI mode
                # 0, matching the real part).
                mem_read = 0
                mem_addr = 0

                sck = self.PROG_SCK.get()
                mosi = self.PROG_MOSI.get()
                prev_sck = self._prog_prev_sck
                self._prog_prev_sck = sck

                if (sck == 1) and (prev_sck == 0):
                    # Inlined _prog_on_sck_rising(mosi).
                    self._prog_shift_reg = ((self._prog_shift_reg << 1) | (mosi & 1)) & 0xFFFFFFFF
                    self._prog_bit_count += 1

                    if self._prog_bit_count == 16:
                        b0 = (self._prog_shift_reg >> 8) & 0xFF
                        b1 = self._prog_shift_reg & 0xFF
                        if (b0 == 0xAC) and (b1 == 0x53):
                            self._prog_pending_reply_valid = 1
                            self._prog_pending_reply_value = 0x53

                    elif (self._prog_bit_count == 17) and (self._prog_pending_reply_valid):
                        self._prog_miso_shift = self._prog_pending_reply_value
                        self._prog_reply_armed = 1
                        self._prog_pending_reply_valid = 0

                    elif self._prog_bit_count == 24:
                        b0 = (self._prog_shift_reg >> 16) & 0xFF
                        b1 = (self._prog_shift_reg >> 8) & 0xFF
                        b2 = (self._prog_shift_reg >> 0) & 0xFF
                        if b0 == 0xF0:
                            self._prog_pending_reply_valid = 1
                            if self._prog_state != 0:
                                self._prog_pending_reply_value = 1
                            else:
                                self._prog_pending_reply_value = 0
                        elif (b0 == 0x50) and (b1 == 0x00):
                            self._prog_pending_reply_valid = 1
                            self._prog_pending_reply_value = self._fuse_low
                        elif (b0 == 0x58) and (b1 == 0x08):
                            self._prog_pending_reply_valid = 1
                            self._prog_pending_reply_value = self._fuse_high
                        elif (b0 == 0x50) and (b1 == 0x08):
                            self._prog_pending_reply_valid = 1
                            self._prog_pending_reply_value = self._fuse_extended
                        elif (b0 == 0x20) or (b0 == 0x28):
                            addr = ((b1 << 8) | b2) & 0x3FFF
                            mem_read = 1
                            mem_addr = addr
                            self._prog_pending_flash_valid = 1
                            self._prog_pending_flash_addr = addr
                            self._prog_pending_flash_high = (b0 == 0x28)

                    elif self._prog_bit_count == 25:
                        if self._prog_pending_flash_valid:
                            flash_addr = self._prog_pending_flash_addr
                            flash_high = self._prog_pending_flash_high
                            self._prog_pending_flash_valid = 0
                            word = self.ins_readdata.get()
                            if flash_high:
                                self._prog_miso_shift = (word >> 8) & 0xFF
                            else:
                                self._prog_miso_shift = word & 0xFF
                            self._prog_reply_armed = 1
                        elif self._prog_pending_reply_valid:
                            self._prog_miso_shift = self._prog_pending_reply_value
                            self._prog_reply_armed = 1
                            self._prog_pending_reply_valid = 0

                    if self._prog_bit_count == 32:
                        # Inlined _prog_execute(self._prog_shift_reg).
                        instruction = self._prog_shift_reg
                        ib0 = (instruction >> 24) & 0xFF
                        ib1 = (instruction >> 16) & 0xFF
                        ib2 = (instruction >> 8) & 0xFF
                        ib3 = instruction & 0xFF

                        if (ib0 == 0xAC) and (ib1 == 0x53):
                            self._prog_enabled = 1
                        elif self._prog_enabled and ((ib0 == 0xAC) and (ib1 == 0x80)):
                            # Chip Erase
                            self._prog_erase_addr = 0
                            self._prog_state = 1
                            self._prog_saw_resp_low = 0
                            self._prog_bit_count = 0
                            self._prog_shift_reg = 0
                            self._prog_reply_armed = 0
                            self._prog_prev_sck = 0
                        elif self._prog_enabled and (ib0 == 0x40):
                            # Load Program Memory Page, low byte
                            word_in_page = ib2 & 0x3F
                            if word_in_page == 0:
                                self._prog_page_00 = (self._prog_page_00 & 0xFF00) | ib3
                            elif word_in_page == 1:
                                self._prog_page_01 = (self._prog_page_01 & 0xFF00) | ib3
                            elif word_in_page == 2:
                                self._prog_page_02 = (self._prog_page_02 & 0xFF00) | ib3
                            elif word_in_page == 3:
                                self._prog_page_03 = (self._prog_page_03 & 0xFF00) | ib3
                            elif word_in_page == 4:
                                self._prog_page_04 = (self._prog_page_04 & 0xFF00) | ib3
                            elif word_in_page == 5:
                                self._prog_page_05 = (self._prog_page_05 & 0xFF00) | ib3
                            elif word_in_page == 6:
                                self._prog_page_06 = (self._prog_page_06 & 0xFF00) | ib3
                            elif word_in_page == 7:
                                self._prog_page_07 = (self._prog_page_07 & 0xFF00) | ib3
                            elif word_in_page == 8:
                                self._prog_page_08 = (self._prog_page_08 & 0xFF00) | ib3
                            elif word_in_page == 9:
                                self._prog_page_09 = (self._prog_page_09 & 0xFF00) | ib3
                            elif word_in_page == 10:
                                self._prog_page_10 = (self._prog_page_10 & 0xFF00) | ib3
                            elif word_in_page == 11:
                                self._prog_page_11 = (self._prog_page_11 & 0xFF00) | ib3
                            elif word_in_page == 12:
                                self._prog_page_12 = (self._prog_page_12 & 0xFF00) | ib3
                            elif word_in_page == 13:
                                self._prog_page_13 = (self._prog_page_13 & 0xFF00) | ib3
                            elif word_in_page == 14:
                                self._prog_page_14 = (self._prog_page_14 & 0xFF00) | ib3
                            elif word_in_page == 15:
                                self._prog_page_15 = (self._prog_page_15 & 0xFF00) | ib3
                            elif word_in_page == 16:
                                self._prog_page_16 = (self._prog_page_16 & 0xFF00) | ib3
                            elif word_in_page == 17:
                                self._prog_page_17 = (self._prog_page_17 & 0xFF00) | ib3
                            elif word_in_page == 18:
                                self._prog_page_18 = (self._prog_page_18 & 0xFF00) | ib3
                            elif word_in_page == 19:
                                self._prog_page_19 = (self._prog_page_19 & 0xFF00) | ib3
                            elif word_in_page == 20:
                                self._prog_page_20 = (self._prog_page_20 & 0xFF00) | ib3
                            elif word_in_page == 21:
                                self._prog_page_21 = (self._prog_page_21 & 0xFF00) | ib3
                            elif word_in_page == 22:
                                self._prog_page_22 = (self._prog_page_22 & 0xFF00) | ib3
                            elif word_in_page == 23:
                                self._prog_page_23 = (self._prog_page_23 & 0xFF00) | ib3
                            elif word_in_page == 24:
                                self._prog_page_24 = (self._prog_page_24 & 0xFF00) | ib3
                            elif word_in_page == 25:
                                self._prog_page_25 = (self._prog_page_25 & 0xFF00) | ib3
                            elif word_in_page == 26:
                                self._prog_page_26 = (self._prog_page_26 & 0xFF00) | ib3
                            elif word_in_page == 27:
                                self._prog_page_27 = (self._prog_page_27 & 0xFF00) | ib3
                            elif word_in_page == 28:
                                self._prog_page_28 = (self._prog_page_28 & 0xFF00) | ib3
                            elif word_in_page == 29:
                                self._prog_page_29 = (self._prog_page_29 & 0xFF00) | ib3
                            elif word_in_page == 30:
                                self._prog_page_30 = (self._prog_page_30 & 0xFF00) | ib3
                            elif word_in_page == 31:
                                self._prog_page_31 = (self._prog_page_31 & 0xFF00) | ib3
                            elif word_in_page == 32:
                                self._prog_page_32 = (self._prog_page_32 & 0xFF00) | ib3
                            elif word_in_page == 33:
                                self._prog_page_33 = (self._prog_page_33 & 0xFF00) | ib3
                            elif word_in_page == 34:
                                self._prog_page_34 = (self._prog_page_34 & 0xFF00) | ib3
                            elif word_in_page == 35:
                                self._prog_page_35 = (self._prog_page_35 & 0xFF00) | ib3
                            elif word_in_page == 36:
                                self._prog_page_36 = (self._prog_page_36 & 0xFF00) | ib3
                            elif word_in_page == 37:
                                self._prog_page_37 = (self._prog_page_37 & 0xFF00) | ib3
                            elif word_in_page == 38:
                                self._prog_page_38 = (self._prog_page_38 & 0xFF00) | ib3
                            elif word_in_page == 39:
                                self._prog_page_39 = (self._prog_page_39 & 0xFF00) | ib3
                            elif word_in_page == 40:
                                self._prog_page_40 = (self._prog_page_40 & 0xFF00) | ib3
                            elif word_in_page == 41:
                                self._prog_page_41 = (self._prog_page_41 & 0xFF00) | ib3
                            elif word_in_page == 42:
                                self._prog_page_42 = (self._prog_page_42 & 0xFF00) | ib3
                            elif word_in_page == 43:
                                self._prog_page_43 = (self._prog_page_43 & 0xFF00) | ib3
                            elif word_in_page == 44:
                                self._prog_page_44 = (self._prog_page_44 & 0xFF00) | ib3
                            elif word_in_page == 45:
                                self._prog_page_45 = (self._prog_page_45 & 0xFF00) | ib3
                            elif word_in_page == 46:
                                self._prog_page_46 = (self._prog_page_46 & 0xFF00) | ib3
                            elif word_in_page == 47:
                                self._prog_page_47 = (self._prog_page_47 & 0xFF00) | ib3
                            elif word_in_page == 48:
                                self._prog_page_48 = (self._prog_page_48 & 0xFF00) | ib3
                            elif word_in_page == 49:
                                self._prog_page_49 = (self._prog_page_49 & 0xFF00) | ib3
                            elif word_in_page == 50:
                                self._prog_page_50 = (self._prog_page_50 & 0xFF00) | ib3
                            elif word_in_page == 51:
                                self._prog_page_51 = (self._prog_page_51 & 0xFF00) | ib3
                            elif word_in_page == 52:
                                self._prog_page_52 = (self._prog_page_52 & 0xFF00) | ib3
                            elif word_in_page == 53:
                                self._prog_page_53 = (self._prog_page_53 & 0xFF00) | ib3
                            elif word_in_page == 54:
                                self._prog_page_54 = (self._prog_page_54 & 0xFF00) | ib3
                            elif word_in_page == 55:
                                self._prog_page_55 = (self._prog_page_55 & 0xFF00) | ib3
                            elif word_in_page == 56:
                                self._prog_page_56 = (self._prog_page_56 & 0xFF00) | ib3
                            elif word_in_page == 57:
                                self._prog_page_57 = (self._prog_page_57 & 0xFF00) | ib3
                            elif word_in_page == 58:
                                self._prog_page_58 = (self._prog_page_58 & 0xFF00) | ib3
                            elif word_in_page == 59:
                                self._prog_page_59 = (self._prog_page_59 & 0xFF00) | ib3
                            elif word_in_page == 60:
                                self._prog_page_60 = (self._prog_page_60 & 0xFF00) | ib3
                            elif word_in_page == 61:
                                self._prog_page_61 = (self._prog_page_61 & 0xFF00) | ib3
                            elif word_in_page == 62:
                                self._prog_page_62 = (self._prog_page_62 & 0xFF00) | ib3
                            elif word_in_page == 63:
                                self._prog_page_63 = (self._prog_page_63 & 0xFF00) | ib3
                        elif self._prog_enabled and (ib0 == 0x48):
                            # Load Program Memory Page, high byte
                            word_in_page = ib2 & 0x3F
                            if word_in_page == 0:
                                self._prog_page_00 = (self._prog_page_00 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 1:
                                self._prog_page_01 = (self._prog_page_01 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 2:
                                self._prog_page_02 = (self._prog_page_02 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 3:
                                self._prog_page_03 = (self._prog_page_03 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 4:
                                self._prog_page_04 = (self._prog_page_04 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 5:
                                self._prog_page_05 = (self._prog_page_05 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 6:
                                self._prog_page_06 = (self._prog_page_06 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 7:
                                self._prog_page_07 = (self._prog_page_07 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 8:
                                self._prog_page_08 = (self._prog_page_08 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 9:
                                self._prog_page_09 = (self._prog_page_09 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 10:
                                self._prog_page_10 = (self._prog_page_10 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 11:
                                self._prog_page_11 = (self._prog_page_11 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 12:
                                self._prog_page_12 = (self._prog_page_12 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 13:
                                self._prog_page_13 = (self._prog_page_13 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 14:
                                self._prog_page_14 = (self._prog_page_14 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 15:
                                self._prog_page_15 = (self._prog_page_15 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 16:
                                self._prog_page_16 = (self._prog_page_16 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 17:
                                self._prog_page_17 = (self._prog_page_17 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 18:
                                self._prog_page_18 = (self._prog_page_18 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 19:
                                self._prog_page_19 = (self._prog_page_19 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 20:
                                self._prog_page_20 = (self._prog_page_20 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 21:
                                self._prog_page_21 = (self._prog_page_21 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 22:
                                self._prog_page_22 = (self._prog_page_22 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 23:
                                self._prog_page_23 = (self._prog_page_23 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 24:
                                self._prog_page_24 = (self._prog_page_24 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 25:
                                self._prog_page_25 = (self._prog_page_25 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 26:
                                self._prog_page_26 = (self._prog_page_26 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 27:
                                self._prog_page_27 = (self._prog_page_27 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 28:
                                self._prog_page_28 = (self._prog_page_28 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 29:
                                self._prog_page_29 = (self._prog_page_29 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 30:
                                self._prog_page_30 = (self._prog_page_30 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 31:
                                self._prog_page_31 = (self._prog_page_31 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 32:
                                self._prog_page_32 = (self._prog_page_32 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 33:
                                self._prog_page_33 = (self._prog_page_33 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 34:
                                self._prog_page_34 = (self._prog_page_34 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 35:
                                self._prog_page_35 = (self._prog_page_35 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 36:
                                self._prog_page_36 = (self._prog_page_36 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 37:
                                self._prog_page_37 = (self._prog_page_37 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 38:
                                self._prog_page_38 = (self._prog_page_38 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 39:
                                self._prog_page_39 = (self._prog_page_39 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 40:
                                self._prog_page_40 = (self._prog_page_40 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 41:
                                self._prog_page_41 = (self._prog_page_41 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 42:
                                self._prog_page_42 = (self._prog_page_42 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 43:
                                self._prog_page_43 = (self._prog_page_43 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 44:
                                self._prog_page_44 = (self._prog_page_44 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 45:
                                self._prog_page_45 = (self._prog_page_45 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 46:
                                self._prog_page_46 = (self._prog_page_46 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 47:
                                self._prog_page_47 = (self._prog_page_47 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 48:
                                self._prog_page_48 = (self._prog_page_48 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 49:
                                self._prog_page_49 = (self._prog_page_49 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 50:
                                self._prog_page_50 = (self._prog_page_50 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 51:
                                self._prog_page_51 = (self._prog_page_51 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 52:
                                self._prog_page_52 = (self._prog_page_52 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 53:
                                self._prog_page_53 = (self._prog_page_53 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 54:
                                self._prog_page_54 = (self._prog_page_54 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 55:
                                self._prog_page_55 = (self._prog_page_55 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 56:
                                self._prog_page_56 = (self._prog_page_56 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 57:
                                self._prog_page_57 = (self._prog_page_57 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 58:
                                self._prog_page_58 = (self._prog_page_58 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 59:
                                self._prog_page_59 = (self._prog_page_59 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 60:
                                self._prog_page_60 = (self._prog_page_60 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 61:
                                self._prog_page_61 = (self._prog_page_61 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 62:
                                self._prog_page_62 = (self._prog_page_62 & 0x00FF) | (ib3 << 8)
                            elif word_in_page == 63:
                                self._prog_page_63 = (self._prog_page_63 & 0x00FF) | (ib3 << 8)
                        elif self._prog_enabled and (ib0 == 0x4C):
                            # Write Program Memory Page
                            page = ((ib1 << 3) | (ib2 >> 5)) & 0xFF
                            self._prog_write_page_addr = page * 64
                            self._prog_write_page_offset = 0
                            self._prog_state = 2
                            self._prog_saw_resp_low = 0
                            self._prog_bit_count = 0
                            self._prog_shift_reg = 0
                            self._prog_reply_armed = 0
                            self._prog_prev_sck = 0
                        elif self._prog_enabled and ((ib0 == 0xAC) and (ib1 == 0xA0)):
                            self._fuse_low = ib3
                        elif self._prog_enabled and ((ib0 == 0xAC) and (ib1 == 0xA8)):
                            self._fuse_high = ib3
                        elif self._prog_enabled and ((ib0 == 0xAC) and (ib1 == 0xA4)):
                            self._fuse_extended = ib3

                elif (sck == 0) and (prev_sck == 1):
                    # Inlined _prog_on_sck_falling().
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
                        self._prog_reply_armed = 0
                else:
                    # No edge this cycle -- hold MISO at whatever it last
                    # drove (SPI mode 0: MISO is stable between edges).
                    self.PROG_MISO.prepare(self._prog_last_miso_bit)

                if mem_read:
                    self.ins_instype.prepare(1)
                else:
                    self.ins_instype.prepare(0)
                self.ins_read.prepare(mem_read)
                self.ins_write.prepare(0)
                self.ins_address.prepare(mem_addr)

        else:

            # Reset falling-edge check: on the one cycle immediately after
            # reset was last seen asserted, inject the fuse-derived boot
            # address into PC before anything else runs this cycle.
            just_released = (self._prev_reset == 1)
            self._prev_reset = 0

            # `pc` tracks what self.PC used to be: seeded from the PC
            # register's current committed value, mutated locally exactly
            # like the old `self.PC = ...` assignments did, and driven back
            # out at the end via PC_ValueOut/PC_Load.
            pc = self.PC_ValIn.get()
            pc_load = 0

            if just_released:
                # Inlined _fuse_boot_address() -- see report (no call
                # inlining, and no dict/array support, in the stock
                # transpiler; _BOOTSZ_ADDRESS above is kept for
                # documentation/external callers only).
                bootrst = self._fuse_high & 0x01
                if bootrst == 0:
                    bootsz = (self._fuse_high >> 1) & 0x03
                    if bootsz == 0:
                        pc = 0x3800
                    elif bootsz == 1:
                        pc = 0x3C00
                    elif bootsz == 2:
                        pc = 0x3E00
                    else:
                        pc = 0x3F00
                else:
                    pc = self.default_reset_address
                pc_load = 1

            # ---------------------------------------------------------
            # STATE: STOP - Halt Execution until requested
            # ---------------------------------------------------------
            if self.FSM == 0:
                self.ins_instype.prepare(0)
                self.ins_read.prepare(0)
                self.ins_write.prepare(0)

                self.Instruction_fetched.prepare(0)
                self.Address_fetched.prepare(0)
                self.SPM_Done.prepare(0)

                load_jump = self.Load_Jump.get()
                load_z    = self.Load_Z.get()
                load_k    = self.Load_K.get()
                load_pcl  = self.Load_PCL.get()
                load_pch  = self.Load_PCH.get()


                if ((load_jump == 1) or ((load_z == 1) or ((load_k == 1) or ((load_pcl == 1) or (load_pch == 1))))):
                    rel_abs = self.relative_Absolute.get()
                    jumped = 0

                    if load_z == 1:
                        # FIX: snapshot the PC *before* overwriting it with Z,
                        # and arm the restore flag so the next LOAD_PCL/LOAD_PCH
                        # pulse (LPM's RESTORE_PC step) pulls the real return
                        # address back out of PC_BUFFER instead of the stale
                        # SRAM/stack data bus.
                        self.PC_BUFFER = pc
                        self._pc_restore_pending = 1

                        z_val = (self.address_ZH.get() << 8) | self.address_ZL.get()
                        if rel_abs == 1:
                            # LPM semantics: Z is a BYTE address into program
                            # memory. The PC (and the ROM) are WORD addressed,
                            # so the word address is Z>>1, and Z&1 selects the
                            # low (0) or high (1) byte of the fetched word,
                            # applied at the next FETCH_ADDR_WAIT completion.
                            self._lpm_byte_high = z_val & 1
                            self._lpm_byte_pending = 1
                            pc = (z_val >> 1) & 0x3FFF
                            pc_load = 1
                        else:
                            # IJMP/ICALL semantics: Z is already a WORD address.
                            pc = z_val & 0x3FFF
                            pc_load = 1
                        jumped = 1
                    elif load_jump == 1:
                        if rel_abs == 1:
                            # Absolute Jump (JMP/CALL) - target address is split
                            # across two words: K7_22 carries the HIGH bits from
                            # the first instruction word, and the second ROM word
                            # (fetched earlier via FETCH_ADDR_REQ/WAIT and latched
                            # in self.latched_addr_word) carries the LOW 16 bits.
                            # Inlined _select_K() -- see report.
                            k_select_sel = self.K_select.get()
                            if k_select_sel == 0:
                                k_val = self.K7.get()
                            elif k_select_sel == 1:
                                k_val = self.K12.get()
                            elif k_select_sel == 2:
                                k_val = self.K7_22.get()
                            else:
                                k_val = self.K7.get()
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
                        jumped = 1
                    elif load_k == 1:
                        # Conditional Branch (BRBS/BRBC) - uses K7 via K_Select
                        # Inlined _select_K() -- see report.
                        k_select_sel = self.K_select.get()
                        if k_select_sel == 0:
                            k_val = self.K7.get()
                        elif k_select_sel == 1:
                            k_val = self.K12.get()
                        elif k_select_sel == 2:
                            k_val = self.K7_22.get()
                        else:
                            k_val = self.K7.get()
                        if k_val & 0x40:
                            offset = k_val - 0x80
                        else:
                            offset = k_val
                        pc = (pc + offset) & 0x3FFF
                        pc_load = 1
                        jumped = 1

                    # FIX: decide ONCE per cycle whether this PCL/PCH load is a
                    # restore-from-Z-detour (LPM) or a genuine external load
                    # (RET/RETI popping the return address off the stack via
                    # PCL_LOAD_VAL/PCH_LOAD_VAL). Computed before either branch
                    # runs so both bytes agree on the source this cycle.
                    restore_from_buffer = self._pc_restore_pending and ((load_pch == 1) or (load_pcl == 1))

                    if load_pch == 1:
                        if restore_from_buffer:
                            pc = (pc & 0x00FF) | (self.PC_BUFFER & 0x3F00)
                            pc_load = 1
                        else:
                            pc = (pc & 0x00FF) | ((self.PCH_LOAD_VAL.get() & 0x3F) << 8)
                            pc_load = 1
                    if load_pcl == 1:
                        if restore_from_buffer:
                            pc = (pc & 0xFF00) | (self.PC_BUFFER & 0x00FF)
                            pc_load = 1
                        else:
                            pc = (pc & 0xFF00) | (self.PCL_LOAD_VAL.get() & 0xFF)
                            pc_load = 1

                    if restore_from_buffer:
                        # Consumed -- clear so a later, unrelated RET/RETI in a
                        # future instruction goes back to using the bus.
                        self._pc_restore_pending = 0
                        self._lpm_byte_pending = 0

                    pc = pc & 0x3FFF
                    pc_load = 1

                    if jumped:
                        self.Executed_Jump.prepare(1)
                        self.FSM = 1
                    else:
                        self.Executed_Jump.prepare(0)
                        if self.Fetch_next_instruction.get() == 1:
                            # FIX (safety net): a real jump (IJMP/ICALL via Z)
                            # that never gets followed by a LOAD_PCL/LOAD_PCH
                            # restore should not leave _pc_restore_pending
                            # armed for some unrelated later instruction.
                            self._pc_restore_pending = 0
                            self._lpm_byte_pending = 0
                            self.FSM = 2
                        elif self.fetch_address.get() == 1:
                            self.FSM = 3
                else:
                    self.Executed_Jump.prepare(0)
                    if self.Fetch_next_instruction.get() == 1:
                        self._pc_restore_pending = 0
                        self._lpm_byte_pending = 0
                        self.FSM = 2
                    elif self.fetch_address.get() == 1:
                        self.FSM = 3
                    elif self.LPM_req.get() == 1:
                        self.FSM = 6
                    elif self.SPM_req.get() == 1:
                        self.FSM = 9

            # ---------------------------------------------------------
            # STATE: WAIT_Jump_LOW - Hold Executed_Jump until control FSM drops request
            # ---------------------------------------------------------
            elif self.FSM == 1:
                self.ins_instype.prepare(0)
                self.ins_read.prepare(0)
                self.ins_write.prepare(0)
                self.Instruction_fetched.prepare(0)
                self.Address_fetched.prepare(0)

                if ((self.Load_Jump.get() == 0) and ((self.Load_Z.get() == 0) and ((self.Load_K.get() == 0) and ((self.Load_PCL.get() == 0) and (self.Load_PCH.get() == 0))))):
                    self.Executed_Jump.prepare(0)
                    self.FSM = 0
                else:
                    self.Executed_Jump.prepare(1)

            # ---------------------------------------------------------
            # STATE: FETCH_REQ - Initiate standard instruction fetch
            # ---------------------------------------------------------
            elif self.FSM == 2:
                self.Instruction_fetched.prepare(0)
                self.Executed_Jump.prepare(0)
                self.ins_instype.prepare(1)

                if self.Load_Byte.get() == 1:
                    # --- SPM WRITE TRANSACTION ---
                    self.ins_write.prepare(1)
                    self.ins_read.prepare(0)
                    self.ins_address.prepare(pc)
                    self.ins_writedata.prepare(self.WriteVal.get())
                    self.FSM = 4
                else:
                    # --- NORMAL INSTRUCTION FETCH ---
                    self.ins_write.prepare(0)
                    self.ins_read.prepare(1)
                    self.ins_address.prepare(pc)
                    self.Address_Out.prepare(pc)
                    self.FSM = 5

            # ---------------------------------------------------------
            # STATE: FETCH_WAIT - Complete standard instruction fetch
            # ---------------------------------------------------------
            elif self.FSM == 5:
                if self.ins_resp.get() == 1:
                    self.ins_read.prepare(0)
                    self.ins_instype.prepare(0)

                    fetched_instruction = self.ins_readdata.get()
                    self.instructionOut.prepare(fetched_instruction)
                    self.Value_Out.prepare(fetched_instruction)
                    self.Instruction_fetched.prepare(1)

                    # --- PC UPDATE LOGIC (Sequential Only) ---
                    # ALWAYS increment by 1 here. Two-word instructions will
                    # increment the PC again dynamically during FETCH_ADDR_WAIT.
                    pc = (pc + 1) & 0x3FFF
                    pc_load = 1

                    self.Executed_Jump.prepare(0)
                    self.FSM = 7

            # ---------------------------------------------------------
            # STATE: FETCH_ADDR_REQ - Initiate secondary address fetch
            # ---------------------------------------------------------
            elif self.FSM == 3:
                self.Address_fetched.prepare(0)
                self.Executed_Jump.prepare(0)

                self.ins_instype.prepare(1)
                self.ins_write.prepare(0)
                self.ins_read.prepare(1)
                self.ins_address.prepare(pc)

                self.FSM = 8

            # ---------------------------------------------------------
            # STATE: FETCH_ADDR_WAIT - Complete secondary address fetch
            # ---------------------------------------------------------
            elif self.FSM == 8:
                if self.ins_resp.get() == 1:
                    self.ins_read.prepare(0)
                    self.ins_instype.prepare(0)

                    fetched_word = self.ins_readdata.get()

                    if self._lpm_byte_pending:
                        # LPM: expose only the byte selected by Z&1 (0 = low
                        # byte, 1 = high byte of the 16-bit flash word).
                        if self._lpm_byte_high:
                            out_val = (fetched_word >> 8) & 0xFF
                        else:
                            out_val = fetched_word & 0xFF
                        self._lpm_byte_pending = 0
                    else:
                        out_val = fetched_word

                    self.Address_Out.prepare(out_val)
                    self.Value_Out.prepare(out_val)
                    self.Address_fetched.prepare(1)
                    self.latched_addr_word = fetched_word  # keep for JMP/CALL PC calc

                    pc = (pc + 1) & 0x3FFF
                    pc_load = 1

                    self.FSM = 10

            # ---------------------------------------------------------
            # STATE: WRITE_WAIT - Complete SPM write transaction
            # ---------------------------------------------------------
            elif self.FSM == 4:
                self.ins_write.prepare(0)
                self.ins_instype.prepare(0)

                if self.ins_resp.get() == 1:
                    pc = (pc + 1) & 0x3FFF
                    pc_load = 1
                    self.FSM = 7

            # ---------------------------------------------------------
            # TRAP STATES: Wait for handshakes to complete
            # ---------------------------------------------------------
            elif self.FSM == 7:
                if self.Fetch_next_instruction.get() == 0:
                    self.Instruction_fetched.prepare(0)
                    self.FSM = 0

            elif self.FSM == 10:
                if self.fetch_address.get() == 0:
                    self.Address_fetched.prepare(0)
                    self.FSM = 0
                else:
                    self.Address_fetched.prepare(1)


            elif self.FSM == 6:
                if self.LPM_req == 1:
                    self.ins_instype.prepare(0)
                    self.ins_write.prepare(0)
                    self.ins_read.prepare(1)
                    self.ins_address.prepare(self.R0_BUFFER_IN.get())
                    val = ((self.R1_BUFFER_IN<<8)|self.R0_BUFFER_IN.get())
                    if self.ins_resp.get() == 1:
                        self.ins_writedata.prepare(self.ins_readdata.get())

                elif self.LPM_req == 2:
                    self.ins_instype.prepare(0)
                    self.ins_write.prepare(0)
                    self.ins_read.prepare(1)
                    z_address = ((self.address_ZH.get()<<8)|(self.address_ZL.get())) & 0xFFFF
                    self.ins_address.prepare(z_address)
                    if self.ins_resp.get() == 1:
                        self.Value_Out.prepare(self.ins_readdata.get())

                elif self.LPM_req == 3:
                    self.ins_instype.prepare(0)
                    self.ins_write.prepare(0)
                    self.ins_read.prepare(1)
                    z_address = (((self.address_ZH<<8)|(self.address_ZL))+1) & 0xFFFF
                    self.ins_address.prepare(z_address)
                    if self.ins_resp.get() == 1:
                        self.Value_Out.prepare(self.ins_readdata.get())


            elif self.FSM == 9:
                self.ins_instype.prepare(1)
                self.ins_read.prepare(0)
                # Z is a BYTE address into flash (same convention LPM uses --
                # see the Load_Z/relative_Absolute=1 path above). Program
                # memory is WORD addressed, so the target word is Z>>1; bit 0
                # of Z is reserved/ignored for SPM (a whole word is written
                # at once, unlike LPM's single-byte reads).
                z_address = (((self.address_ZH.get()<<8)|(self.address_ZL.get())) >> 1) & 0x3FFF
                self.ins_address.prepare(z_address)
                # FIX: R1_BUFFER_IN was used without .get() -- shifting the
                # Pin object itself instead of its value.
                val = ((self.R1_BUFFER_IN.get()<<8)|self.R0_BUFFER_IN.get()) & 0xFFFF
                self.ins_writedata.prepare(val)

                if self.ins_resp.get() == 1:
                    self.ins_write.prepare(0)
                    self.SPM_Done.prepare(1)
                    self.FSM = 11
                else:
                    self.ins_write.prepare(1)
                    self.SPM_Done.prepare(0)

            elif self.FSM == 11:
                self.ins_write.prepare(0)
                self.ins_instype.prepare(0)
                if self.SPM_req.get() == 0:
                    self.SPM_Done.prepare(0)
                    self.FSM = 0
                else:
                    self.SPM_Done.prepare(1)

            # ---------------------------------------------------------
            # DEFAULT: Safety fallback
            # ---------------------------------------------------------
            else:
                self.FSM = 0

            # Drive the PC register: pc_load=1 exactly on the cycles the old
            # code would have executed a `self.PC = ...` assignment; pc always
            # carries the fully-resolved value for this cycle either way.
            self.PC_ValueOut.prepare(pc)
            self.PC_Load.prepare(pc_load)

    def _fuse_boot_address(self):
        bootrst = self._fuse_high & 0x01
        if bootrst == 0:   # programmed -> reset vector is the boot section
            bootsz = (self._fuse_high >> 1) & 0x03
            return self._BOOTSZ_ADDRESS[bootsz]
        return self.default_reset_address   # unprogrammed (factory default)

    # =================================================================
