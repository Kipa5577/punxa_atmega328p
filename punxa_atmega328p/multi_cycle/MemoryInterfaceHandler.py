import py4hw
import punxa_atmega328p.Memory 

"""
=============================================================================
AI Agent Component Reference: MemoryInterfaceHandler
=============================================================================

Description:
This class manages the Data Memory (SRAM) interface for an AVR-like architecture 
in py4hw. It internally houses and maintains the 16-bit indirect addressing 
pointers (X, Y, Z, and Stack Pointer SP). It handles complex address generation 
including direct addressing, indirect addressing, pointer auto-increment/decrement, 
and displacement addressing (Y+q, Z+q). 
=============================================================================
"""

class MemoryInterfaceHandler(py4hw.Logic):

    # ----------------------------------------------------------
    # Memory instruction encodings
    # ----------------------------------------------------------
    MEM_X = 1
    MEM_X_PLUS = 2
    MEM_Y = 3
    MEM_Y_PLUS = 4
    MEM_Z = 5
    MEM_Z_PLUS = 6
    MEM_SP = 7
    MEM_SP_PLUS = 8
    MEM_RAM_ADDR_REG = 9
    MEM_Y_Q = 10
    MEM_Z_Q = 11
    MEM_RD  = 12   
    MEM_RR  = 13   
    MEM_WB_ADDR = 14  
    MEM_RD_1 = 15
    MEM_RR_1 = 16
    MEM_A_5bit = 17
    MEM_A_6bit = 18

    # Fixed-address reads for the interrupt vector bytes written by the
    # external InterruptUnit peripheral (see MEM_A_5bit/A_6bit for the
    # precedent of a "constant, no pointer-register" addressing mode).
    # Used exclusively by InterruptFSM's entrance sequence.
    MEM_INT_VECTOR_L = 19   # fixed address 0x00FE
    MEM_INT_VECTOR_H = 20   # fixed address 0x00FF

    # --- Input select ---
    INPUT_DATABUS = 1
    INPUT_RESL = 2
    INPUT_RESH = 3
    INPUT_GENERAL = 4
    INPUT_ROM_VALUE = 5
    INPUT_XL = 6
    INPUT_XH = 7
    INPUT_YL = 8
    INPUT_YH = 9
    INPUT_ZL = 10
    INPUT_ZH = 11
    INPUT_SPL = 12
    INPUT_SPH = 13
    INPUT_PCL = 14
    INPUT_PCH = 15
    INPUT_RD_BUFFER = 16
    INPUT_ROM_2 = 17

    # --- LoadSelectMux ---
    LOAD_BUS_DATA = 1
    LOAD_XL_MINUS = 2
    LOAD_XH_MINUS = 3
    LOAD_XL_PLUS = 4
    LOAD_XH_PLUS = 5
    LOAD_YL_MINUS = 6
    LOAD_YH_MINUS = 7
    LOAD_YL_PLUS = 8
    LOAD_YH_PLUS = 9
    LOAD_ZL_MINUS = 10
    LOAD_ZH_MINUS = 11
    LOAD_ZL_PLUS = 12
    LOAD_ZH_PLUS = 13

    # --- LoadingMux ---
    LOAD_XL = 1
    LOAD_XH = 2
    LOAD_YL = 3
    LOAD_YH = 4
    LOAD_ZL = 5
    LOAD_ZH = 6
    LOAD_SPL = 7
    LOAD_SPH = 8
    LOAD_RD_BUFFER = 14  
    LOAD_R0_BUFFER = 15 
    LOAD_R1_BUFFER = 16

    # --- Increment/Decrement Control ---
    INC_NONE = 0
    INC_POST_INC = 1
    INC_PRE_DEC = 2
    INC_POST_DEC = 3  
    INC_PRE_INC = 4   


    def __init__(self, parent, name: str,
            reset, WE, LoadSelectMux, LoadingMux, IncDec, ReadWrite, InputSelectMemory, 
            Mem_instruction, RomAddress, ResL, ResH, K_val_Input, RomAddressValue,
            PCL_VAL_IN, PCH_VAL_IN, PC_Offset, Q, Rd, Rr, A_5bit, A_6bit, WbAddr, memory,
            RegisterOut, Resp, address_ZL, address_ZH, MIH_PCL_LOAD_VAL, MIH_PCH_LOAD_VAL,
            #---- SREG ----
            SREG_In,eSREG_In,SREG_Reset,SREG_Out,
            #---- LPM  SPM ---- 
            R0_BUFFER_OUT,R1_BUFFER_OUT,ROM_VAL_IN,ROM_VAL_OUT,
            #---- Interrupts ----
            I_Flag_Out,   # 1-bit OUT: bit 7 of SREG (Global Interrupt Enable),
                          # broken out as its own wire for an external
                          # InterruptUnit peripheral to gate on.
            I_Force_WE,      # 1-bit IN: InterruptFSM asserts this for one
                             # cycle to directly overwrite the I flag,
                             # bypassing the normal ALU/eSREG (SEI/CLI) path.
            I_Force_Value,   # 1-bit IN: value to force I to when I_Force_WE=1
                             # (0 = interrupt entrance clearing I, 1 = RETI
                             # re-enabling it).
            Bus_Passthrough_Ranges=None,
            # List of (start, end) INCLUSIVE address tuples, inside
            # [0x0020, 0x00FF], that should be forwarded to the real
            # external bus instead of being swallowed into io_scratch.
            # Without this, ANY peripheral a testbench maps in that range
            # (GPIO, a timer, an InterruptUnit, ...) would silently never
            # be reached — MemoryInterfaceHandler would answer for it
            # itself out of io_scratch. Defaults to just the interrupt
            # vector bytes (0x00FE-0x00FF) so InterruptFSM keeps working
            # even if a testbench doesn't pass anything here; add more
            # ranges to match whatever else your bus layout maps in
            # [0x0020, 0x00FF] (e.g. GPIO at 0x20-0x3F, a timer at
            # 0x40-0x6F — see tb_MultiCycle.py).
        ):
        super().__init__(parent, name)

        self.mem = self.addInterfaceSource('memory', memory)

        self.reset = self.addIn('reset', reset)
        self.WE = self.addIn('WE', WE)
        self.LoadSelectMux = self.addIn('LoadSelectMux', LoadSelectMux)
        self.LoadingMux = self.addIn('LoadingMux', LoadingMux)
        self.IncDec = self.addIn('IncDec', IncDec)
        self.ReadWrite = self.addIn('ReadWrite', ReadWrite)
        self.InputSelectMemory = self.addIn('InputSelectMemory', InputSelectMemory)
        self.Mem_instruction = self.addIn('Mem_instruction', Mem_instruction)
        self.RomAddress = self.addIn('RomAddress', RomAddress) 
        self.RomAddressValue = self.addIn('RomHandlerValueRead',RomAddressValue)

        self.PCL_VAL_IN = self.addIn('PCL_VAL_IN',PCL_VAL_IN)
        self.PCH_VAL_IN = self.addIn('PCH_VAL_IN',PCH_VAL_IN)
        # PC push offset — driven by the EXISTING JumpWidth signal (computed
        # in MainFSM from TWO_WORD_INS and exported via CB_JumpWidth; note
        # RomHandler receives but never reads it). Semantics here: number of
        # instruction words the RomHandler has NOT yet consumed at the moment
        # CallRet_FSM pushes the return address. RomHandler auto-advances PC
        # past the opcode word only, so for 2-word CALL the exported
        # Pc_valL/Pc_valH still points at CALL's own address word at push
        # time; adding JumpWidth (=1) lands the pushed return address on the
        # instruction AFTER the full encoding. Valid because the push states
        # run BEFORE Fetch_Address consumes the second word — if the CALL
        # sequence is ever reordered to fetch the address first, this offset
        # must become 0 for that path.
        self.PC_Offset = self.addIn('PC_Offset', PC_Offset)
        self.ResL = self.addIn('ResL', ResL)
        self.ResH = self.addIn('ResH', ResH)
        self.K_val_Input = self.addIn('K_val_Input', K_val_Input)
        self.Q = self.addIn('Q', Q)

        self.Rd = self.addIn('Rd', Rd)
        self.Rr = self.addIn('Rr', Rr)
        self.A_5bit = self.addIn('A_5bit',A_5bit)
        self.A_6bit = self.addIn('A_6bit',A_6bit)
        self.WbAddr = self.addIn('WbAddr', WbAddr)

        self.RegisterOut = self.addOut('RegisterOut', RegisterOut)
        self.Resp = self.addOut('Resp',Resp)
        self.address_ZL = self.addOut('address_ZL',address_ZL)
        self.address_ZH = self.addOut('address_ZH',address_ZH)
        self.MIH_PCL_LOAD_VAL = self.addOut('MIH_PCL_LOAD_VAL',MIH_PCL_LOAD_VAL)
        self.MIH_PCH_LOAD_VAL = self.addOut('MIH_PCH_LOAD_VAL',MIH_PCH_LOAD_VAL)

        self.R0_BUFFER_out = self.addOut('R0_BUFFER_OUT',R0_BUFFER_OUT)
        self.R1_BUFFER_out = self.addOut('R1_BUFFER_out',R1_BUFFER_OUT)

        self.ROM_VAL = self.addIn('ROM_VAL_IN',ROM_VAL_IN)


        #---- SREG ----
        self.SREG_IN = self.addIn('SREG_In',SREG_In)
        self.eSREG = self.addIn('eSREG_In',eSREG_In)
        self.SREG_Reset = self.addIn('SREG_Reset',SREG_Reset)
        self.SREG_OUT = self.addOut('SREG_OUT',SREG_Out)

        #---- Interrupts ----
        # Standard AVR SREG bit ordering used throughout this project
        # (I-T-H-S-V-N-Z-C, see ALU.py): I is bit 7.
        self.I_FLAG_BIT = 7
        self.I_Flag_Out = self.addOut('I_Flag_Out', I_Flag_Out)
        self.I_Force_WE = self.addIn('I_Force_WE', I_Force_WE)
        self.I_Force_Value = self.addIn('I_Force_Value', I_Force_Value)

        self.Bus_Passthrough_Ranges = (
            list(Bus_Passthrough_Ranges) if Bus_Passthrough_Ranges
            else [(0x00FE, 0x00FF)]
        )


        self.SREG = 0 
        # Generic placeholder storage for memory-mapped I/O / extended I/O
        # registers (0x0020-0x00FF in the real AVR address map) that don't
        # have dedicated hardware behavior implemented yet (EIMSK, EICRA,
        # SMCR, TIMSKx, etc.). Without this, STS/LDS/IN/OUT to any such
        # register falls through to the "normal SRAM" path, which depends
        # on the underlying Memory object acknowledging an address it
        # doesn't actually back (true SRAM only starts at 0x0100) -- the
        # write is issued, resp never asserts, and the calling FSM retries
        # forever. This makes those registers behave as plain read/write
        # scratch cells (store the value, no side effects) so instructions
        # touching them complete immediately, matching "not implemented
        # yet, treat as inert" for anything peripheral-related (including
        # the interrupt-wake path SLEEP would eventually need).
        self.io_scratch = {}
        self.XregL = 0
        self.XregH = 0
        self.YregL = 0
        self.YregH = 0
        self.ZregL = 0
        self.ZregH = 0
        self.SPL = 0
        self.SPH = 0
        self.RdBuffer = 0  

        self.R0Buffer = 0 
        self.R1Buffer = 0 

        self.BusData = 0
        self.Databuffer = 0
        self.debug = 1

    # ==========================================================
    # Helpers
    # ==========================================================

    def getX(self): return (self.XregH << 8) | self.XregL
    def getY(self): return (self.YregH << 8) | self.YregL
    def getZ(self): return (self.ZregH << 8) | self.ZregL
    def getSP(self): return (self.SPH << 8) | self.SPL

    def setX(self, value):
        self.XregL = value & 0xFF
        self.XregH = (value >> 8) & 0xFF

    def setY(self, value):
        self.YregL = value & 0xFF
        self.YregH = (value >> 8) & 0xFF

    def setZ(self, value):
        self.ZregL = value & 0xFF
        self.ZregH = (value >> 8) & 0xFF

    def setSP(self, value):
        self.SPL = value & 0xFF
        self.SPH = (value >> 8) & 0xFF

    # ==========================================================
    # Address generation
    # ==========================================================

    def isBusPassthrough(self, address):
        for start, end in self.Bus_Passthrough_Ranges:
            if start <= address <= end:
                return True
        return False

    def selectAddress(self):
        mem_instr = self.Mem_instruction.get()
        base_address = 0
        pointer_name = None

        if mem_instr in (self.MEM_X, self.MEM_X_PLUS):
            base_address = self.getX()
            pointer_name = "X"
        elif mem_instr in (self.MEM_Y, self.MEM_Y_PLUS):
            base_address = self.getY()
            pointer_name = "Y"
        elif mem_instr in (self.MEM_Z, self.MEM_Z_PLUS):
            base_address = self.getZ()
            pointer_name = "Z"
        elif mem_instr in (self.MEM_SP, self.MEM_SP_PLUS):
            base_address = self.getSP()
            pointer_name = "SP"
        elif mem_instr == self.MEM_RAM_ADDR_REG:
            base_address = self.RomAddressValue.get()
            pointer_name = "ROM"

        elif mem_instr == self.MEM_RD:
            base_address = self.Rd.get() & 0x1F
            pointer_name = None   

        elif mem_instr == self.MEM_RR:
            base_address = self.Rr.get() & 0x1F
            pointer_name = None

        elif mem_instr == self.MEM_WB_ADDR:
            base_address = self.WbAddr.get() & 0x1F
            pointer_name = None

        elif mem_instr == self.MEM_Y_Q:
            # q is a 6-bit UNSIGNED displacement (0-63) -- LDD/STD Y+q
            # always indexes forward from Y, never backward. No sign
            # extension here; q_val is used exactly as decoded.
            q_val = self.Q.get() & 0x3F
            base_address = self.getY() + q_val

        elif mem_instr == self.MEM_Z_Q:
            # Same as MEM_Y_Q above: q is unsigned, 0-63.
            q_val = self.Q.get() & 0x3F
            base_address = self.getZ() + q_val

        elif mem_instr == self.MEM_RD_1:
            base_address = (self.Rd.get()+1) & 0x1F
            pointer_name = None   

        elif mem_instr == self.MEM_RR_1:
            base_address = (self.Rr.get()+1) & 0x1F
            pointer_name = None   

        # --- OUT / IN ADDRESS GENERATION ---
        # AVR I/O space begins at SRAM offset 0x20. By adding 0x20 here, 
        # standard LDST_FSM logic handles it identically to standard RAM accesses.
        elif mem_instr == self.MEM_A_5bit:
            base_address = self.A_5bit.get() + 0x20
            pointer_name = None   

        elif mem_instr == self.MEM_A_6bit:
            base_address = self.A_6bit.get() + 0x20
            pointer_name = None

        elif mem_instr == self.MEM_INT_VECTOR_L:
            base_address = 0x00FE
            pointer_name = None

        elif mem_instr == self.MEM_INT_VECTOR_H:
            base_address = 0x00FF
            pointer_name = None   
            
        # UPDATED: Apply Pre-decrement OR Pre-increment BEFORE accessing memory 
        mode = self.IncDec.get()
        if pointer_name in ("X", "Y", "Z", "SP"):
            if mode == self.INC_PRE_DEC:
                base_address -= 1
            elif mode == self.INC_PRE_INC:
                base_address += 1

        if self.debug:
            print(f"{pointer_name}Address:[{base_address}]")
        return base_address & 0xFFFF, pointer_name

    # ==========================================================
    # Address update logic
    # ==========================================================

    def updatePointer(self, ptr_name):
        if ptr_name is None or ptr_name == "ROM":
            return

        mode = self.IncDec.get()
        if mode == self.INC_NONE:
            return

        # Calculate the offset to apply to the pointer based on the mode
        offset = 0
        if mode in (self.INC_PRE_DEC, self.INC_POST_DEC):
            offset = -1
        elif mode in (self.INC_PRE_INC, self.INC_POST_INC):
            offset = 1

        if ptr_name == "X":
            self.setX(self.getX() + offset)
        elif ptr_name == "Y":
            self.setY(self.getY() + offset)
        elif ptr_name == "Z":
            self.setZ(self.getZ() + offset)
        elif ptr_name == "SP":
            self.setSP(self.getSP() + offset)

    # ==========================================================
    # Data source selection
    # ==========================================================

    def selectWriteData(self):
        sel = self.InputSelectMemory.get()
        write_data = 0
        source_name = "DEFAULT"

        if sel == self.INPUT_DATABUS:
            write_data = self.mem.read_data.get()
            source_name = "DATABUS"
        elif sel == self.INPUT_RESL:
            write_data = self.ResL.get()
            source_name = "RESL"
        elif sel == self.INPUT_RESH:
            write_data = self.ResH.get()
            source_name = "RESH"
        elif sel == self.INPUT_GENERAL:
            write_data = self.K_val_Input.get()
            source_name = "GENERAL"
        elif sel == self.INPUT_ROM_VALUE:
            write_data = self.RomAddressValue.get()
            source_name = "ROM_VALUE"
            
        elif sel == self.INPUT_XL: 
            write_data = self.XregL
            source_name = "XL"
        elif sel == self.INPUT_XH: 
            write_data = self.XregH
            source_name = "XH"
        elif sel == self.INPUT_YL: 
            write_data = self.YregL
            source_name = "YL"
        elif sel == self.INPUT_YH: 
            write_data = self.YregH
            source_name = "YH"
        elif sel == self.INPUT_ZL: 
            write_data = self.ZregL
            source_name = "ZL"
        elif sel == self.INPUT_ZH: 
            write_data = self.ZregH
            source_name = "ZH"
        elif sel == self.INPUT_SPL: 
            write_data = self.SPL
            source_name = "SPL"
        elif sel == self.INPUT_SPH: 
            write_data = self.SPH
            source_name = "SPH"
            
        elif sel == self.INPUT_PCL: 
            # Add the decoder-provided push offset to the FULL 16-bit PC so
            # a carry out of the low byte propagates into the high byte
            # (e.g. PC=0x00FF + 1 must push PCL=0x00, PCH=0x01).
            pc_full = (((self.PCH_VAL_IN.get() << 8) | self.PCL_VAL_IN.get())
                       + self.PC_Offset.get()) & 0xFFFF
            write_data = pc_full & 0xFF
            source_name = "PCL"
        elif sel == self.INPUT_PCH: 
            pc_full = (((self.PCH_VAL_IN.get() << 8) | self.PCL_VAL_IN.get())
                       + self.PC_Offset.get()) & 0xFFFF
            write_data = (pc_full >> 8) & 0xFF
            source_name = "PCH"
            
        elif sel == self.INPUT_RD_BUFFER: 
            write_data = self.RdBuffer
            source_name = "RD_BUFFER"

        elif sel == self.INPUT_ROM_2:
            write_data = self.ROM_VAL.get()
            source_name = "ROM_VAL"
            

        if source_name:
            if self.debug:
                print(f"{source_name}_WriteData:[{write_data}]")
        
        return write_data

    # ==========================================================
    # Main clocked behavior
    # ==========================================================

    def clock(self):
        # ----------------------------------------------
        # 0. Reset
        # ----------------------------------------------
        if self.reset.get():
            self.XregL = 0
            self.XregH = 0
            self.YregL = 0
            self.YregH = 0
            self.ZregL = 0
            self.ZregH = 0
            self.SPL = self.SPH = 0
            self.BusData = 0
            
            self.RegisterOut.prepare(0)
            self.address_ZL.prepare(0)
            self.address_ZH.prepare(0)
            self.mem.address.prepare(0)
            self.mem.write_data.prepare(0)
            return

        # ----------------------------------------------
        # 1. Address generation
        # ----------------------------------------------
        address, pointer_name = self.selectAddress()
        self.mem.address.prepare(address)

        # ----------------------------------------------
        # 2. Memory operation & BusData latching (INTERCEPT LOGIC)
        # ----------------------------------------------
        rw = self.ReadWrite.get()
        
        # ATmega328P SRAM Data Space addresses for SP
        SP_L_ADDR = 0x5D
        SP_H_ADDR = 0x5E

        SREG_ADDR = 0x5F

        # Interrupt vector bytes and any other peripheral windows a
        # testbench has declared via Bus_Passthrough_Ranges (see __init__)
        # fall inside the [0x0020, 0x0100) range that would otherwise be
        # swallowed into io_scratch a few lines down — carved out here so
        # the peripherals actually mapped there on the real bus (GPIO, a
        # timer, an InterruptUnit, ...) actually see these transactions
        # instead of getting silently intercepted.

        resp_val = 0
        if rw == 1: # WRITE OPERATION
            self.BusData = self.selectWriteData()
            
            # Intercept SP Writes
            if address == SP_L_ADDR:
                self.SPL = self.BusData & 0xFF
                self.mem.write.prepare(0) # Bypass SRAM write
                resp_val = 1
                if self.debug:
                    print(f"Intercepted WRITE to SPL: {self.SPL:02X}")

            elif address == SP_H_ADDR:
                self.SPH = self.BusData & 0xFF
                self.mem.write.prepare(0) # Bypass SRAM write
                resp_val = 1
                if self.debug:
                    print(f"Intercepted WRITE to SPH: {self.SPH:02X}")

            elif address == SREG_ADDR:
                self.SREG = self.BusData & 0xFF
                self.mem.write.prepare(0)
                resp_val = 1
                if self.debug:
                    print(f"Intercepted WRITE to SREG: {self.SREG:02X}")

            elif (0x0020 <= address < 0x0100
                  and not self.isBusPassthrough(address)):
                # Any other memory-mapped I/O / extended I/O register with
                # no dedicated hardware model yet (EIMSK, EICRA, SMCR, ...).
                # Real SRAM starts at 0x0100, so anything below that is
                # either register file or (extended) I/O space -- neither
                # of which the underlying Memory object backs. Store the
                # value and ack immediately rather than hanging forever.
                self.io_scratch[address] = self.BusData & 0xFF
                self.mem.write.prepare(0)
                resp_val = 1
                if self.debug:
                    print(f"Intercepted WRITE to I/O[{address:02X}]: {self.BusData:02X}")

            else:
                # Normal SRAM Write (also used by any Bus_Passthrough_Ranges
                # address above, which is NOT real SRAM -- it routes to
                # whatever peripheral a testbench has mapped there on the
                # real external data bus).
                self.mem.write_data.prepare(self.BusData)
                self.mem.write.prepare(1)
                resp_val = self.mem.resp.get()

            self.mem.read.prepare(0)

        elif rw == 2: # READ OPERATION
            
            # Intercept SP Reads
            if address == SP_L_ADDR:
                self.BusData = self.SPL
                self.mem.read.prepare(0) # Bypass SRAM read
                resp_val = 1
                if self.debug:
                    print(f"Intercepted READ from SPL: {self.BusData:02X}")

            elif address == SP_H_ADDR:
                self.BusData = self.SPH
                self.mem.read.prepare(0) # Bypass SRAM read
                resp_val = 1
                if self.debug:
                    print(f"Intercepted READ from SPH: {self.BusData:02X}")

            elif address == SREG_ADDR:
                self.BusData = self.SREG
                self.mem.write.prepare(0)
                resp_val = 1
                if self.debug:
                    print(f"Intercepted READ from SREG: {self.SREG:02X}")

            elif (0x0020 <= address < 0x0100
                  and not self.isBusPassthrough(address)):
                # See matching WRITE branch above. Unwritten registers
                # default to 0 rather than raising, since real hardware
                # reset state for these is 0 anyway.
                self.BusData = self.io_scratch.get(address, 0)
                self.mem.read.prepare(0)
                resp_val = 1
                if self.debug:
                    print(f"Intercepted READ from I/O[{address:02X}]: {self.BusData:02X}")

            else:
                # Normal SRAM Read (also used by 0xFE/0xFF, routed to the
                # external InterruptUnit peripheral -- see WRITE branch).
                self.BusData = self.mem.read_data.get()
                self.mem.read.prepare(1)
                resp_val = self.mem.resp.get()
                
            self.mem.write.prepare(0)
            
        else: # NO OPERATION
            self.mem.read.prepare(0)
            self.mem.write.prepare(0)
            resp_val = self.mem.resp.get()
            
        self.Resp.prepare(resp_val)
        self.RegisterOut.prepare(self.BusData)

        self.address_ZL.prepare(self.ZregL)
        self.address_ZH.prepare(self.ZregH)
        self.MIH_PCL_LOAD_VAL.prepare(self.BusData)
        self.MIH_PCH_LOAD_VAL.prepare(self.BusData)

        # ----------------------------------------------
        # 3. Register loading
        # ----------------------------------------------
        if self.WE.get():
            load_sel = self.LoadingMux.get()
            data = self.BusData & 0xFF
            target_name = None
            
            if load_sel == self.LOAD_XL: 
                self.XregL = data
                target_name = "XL"
            elif load_sel == self.LOAD_XH: 
                self.XregH = data
                target_name = "XH"
            elif load_sel == self.LOAD_YL: 
                self.YregL = data
                target_name = "YL"
            elif load_sel == self.LOAD_YH: 
                self.YregH = data
                target_name = "YH"
            elif load_sel == self.LOAD_ZL: 
                self.ZregL = data
                target_name = "ZL"
            elif load_sel == self.LOAD_ZH: 
                self.ZregH = data
                target_name = "ZH"
            elif load_sel == self.LOAD_SPL: 
                self.SPL = data
                target_name = "SPL"
            elif load_sel == self.LOAD_SPH: 
                self.SPH = data
                target_name = "SPH"
            elif load_sel == self.LOAD_RD_BUFFER: 
                self.RdBuffer = data
                target_name = "RD_BUFFER"
            elif load_sel == self.LOAD_R0_BUFFER:
                self.R0Buffer = data
                target_name = "R0_BUFFER"
            elif load_sel == self.LOAD_R1_BUFFER:
                self.R1Buffer = data
                target_name = "R1_BUFFER"

            if target_name:
                if self.debug:
                    print(f"{target_name}_Loaded:[{data}]")

        # ----------------------------------------------
        # 4. Pointer update
        # ----------------------------------------------
        self.updatePointer(pointer_name)

        if self.debug == 1:
            state_log = (
                f"MIH_STATE | "
                f"PC: {self.PCH_VAL_IN.get():02X}{self.PCL_VAL_IN.get():02X} | "
                f"X: {self.getX():04X} Y: {self.getY():04X} Z: {self.getZ():04X} SP: {self.getSP():04X} | "
                f"Addr: {address:04X} Bus: {self.BusData:02X} | "
                f"RD_BUFFER: {self.RdBuffer} |"
                f"WE: {self.WE.get()} RW: {rw} Resp: {self.mem.resp.get()}"
            )
            print(state_log)

        # --- SREG LOGIC ---

        if self.SREG_Reset.get():
            self.SREG = 0

        if self.eSREG.get() > 0:
            self.SREG = (self.SREG & ~self.eSREG.get()) | (self.SREG_IN.get() & self.eSREG.get()) 

        # InterruptFSM's direct override — always applied AFTER the normal
        # ALU/eSREG (SEI/CLI) update, so it wins regardless of whatever
        # stale instruction context the ALU/decoder happen to be holding
        # at the moment of interrupt entry or RETI (there's no "current
        # instruction" driving eSREG during INTERRUPT_ENTRY).
        if self.I_Force_WE.get() == 1:
            if self.I_Force_Value.get() == 1:
                self.SREG |= (1 << self.I_FLAG_BIT)
            else:
                self.SREG &= ~(1 << self.I_FLAG_BIT)

        self.SREG_OUT.prepare(self.SREG)

        # Global Interrupt Enable (I flag) out to the external InterruptUnit.
        # Always reflects the same committed SREG value as SREG_OUT above,
        # including changes made this very cycle by SEI/CLI/IN/OUT.
        self.I_Flag_Out.prepare((self.SREG >> self.I_FLAG_BIT) & 1)

        # FIX: these two outputs were declared via addOut but never
        # prepared anywhere in this class, so RomHandler's R0_BUFFER_IN/
        # R1_BUFFER_IN (SPM's register operands) permanently read 0
        # regardless of what LOAD_R0_BUFFER/LOAD_R1_BUFFER had latched
        # into self.R0Buffer/self.R1Buffer above.
        self.R0_BUFFER_out.prepare(self.R0Buffer)
        self.R1_BUFFER_out.prepare(self.R1Buffer)