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
            # SREG storage itself now lives in Datapath as 8 discrete 1-bit
            # flag registers (SREG_C/Z/N/V/S/H/T/I). MIH no longer owns
            # `self.SREG` -- it's purely the controller: SREG_In/eSREG_In
            # are still the ALU's proposed value/write-mask (unchanged
            # meaning), SREG_ReadValue is the composed 8-bit byte read back
            # from those registers (used for the SREG_ADDR 0x5F IN/OUT bus
            # intercept), and SREG_WriteValue/SREG_WriteMask are MIH's
            # resolved write request for this cycle -- combining the ALU's
            # masked update with a possible full-byte SREG_ADDR bus write,
            # with the ALU update taking priority on overlapping bits
            # (matches the original self.SREG ordering: bus write applied
            # first, eSREG mask layered on top). The I flag specifically is
            # excluded from here -- see Datapath's dedicated InterruptFSM
            # override mux in front of SREG_I; MIH is unaware of
            # InterruptFSM entirely now.
            SREG_In, eSREG_In, SREG_ReadValue,
            SREG_WriteValue, SREG_WriteMask,
            # FIX (SREG write race): 1-bit IN, pulses exactly one cycle when
            # the current instruction's leaf FSM retires (see ControlBox's
            # CB_ALU_Commit). eSREG_In/SREG_In are driven combinationally
            # off whatever instruction is currently decoded, but that
            # instruction's actual operand registers (AL/BL/etc, in
            # Datapath) can take several cycles to finish staging -- without
            # this gate, the flag registers got written every one of those
            # cycles off transiently-wrong/stale operands, corrupting any
            # flag a same instruction reads back as its own input (ADC/SBC's
            # carry-in, ROL/ROR's carry-in, BLD's T-in) before the real,
            # settled computation ever got to use it.
            ALU_Commit,
            #---- Bus Address Register (MAR) ----
            # MIH still owns and drives the real `memory` interface's
            # address/read/write/etc pins directly (unchanged, to avoid
            # perturbing cycle-accurate handshake timing) -- MAR_ValueOut is
            # an additional, purely observational output mirroring the same
            # computed address every cycle, which Datapath latches into a
            # real py4hw.Reg (the architectural "bus address register").
            MAR_ValueOut,
            #---- LPM  SPM ---- 
            R0_BUFFER_OUT,R1_BUFFER_OUT,ROM_VAL_IN,ROM_VAL_OUT,
            Bus_Passthrough_Ranges=((0x00FE, 0x00FF),),
            # Tuple of (start, end) INCLUSIVE address tuples, inside
            # [0x0020, 0x00FF], that should be forwarded to the real
            # external bus instead of being swallowed into io_scratch.
            # NOTE: default changed from None+ternary to a plain, always-
            # valid tuple (same single range the old ternary's else-branch
            # produced) so this becomes a bare `self.x = x` assignment --
            # required by the stock transpiler's __init__ parser, which
            # only understands Call/Name/int-literal assignments (see
            # report). Every real caller in this project (the ISA test
            # harness, via MulticycleProcessor/Datapath pass-through)
            # always supplies its own explicit 4-range tuple anyway, so
            # this default is never actually exercised end-to-end -- it
            # only matters for a hypothetical bare/standalone construction.
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

        # Mirror the class-level constants above as instance attributes
        # using their literal values: the stock transpiler's __init__
        # parser only understands self.X = <int literal> / self.X =
        # self.addIn(...) / self.X = <same-named constructor arg> -- a
        # class-level `MEM_X = 1` referenced later as `self.MEM_X` (no
        # assignment in __init__) is invisible to it, and silently
        # synthesizes as an undriven, always-0 top-level wire (see report /
        # py4hw bug report Issue 7 addendum). Values must stay in sync with
        # the class-level declarations above by construction (generated from
        # them).
        self.MEM_X = 1
        self.MEM_X_PLUS = 2
        self.MEM_Y = 3
        self.MEM_Y_PLUS = 4
        self.MEM_Z = 5
        self.MEM_Z_PLUS = 6
        self.MEM_SP = 7
        self.MEM_SP_PLUS = 8
        self.MEM_RAM_ADDR_REG = 9
        self.MEM_Y_Q = 10
        self.MEM_Z_Q = 11
        self.MEM_RD = 12
        self.MEM_RR = 13
        self.MEM_WB_ADDR = 14
        self.MEM_RD_1 = 15
        self.MEM_RR_1 = 16
        self.MEM_A_5bit = 17
        self.MEM_A_6bit = 18
        self.MEM_INT_VECTOR_L = 19
        self.MEM_INT_VECTOR_H = 20
        self.INPUT_DATABUS = 1
        self.INPUT_RESL = 2
        self.INPUT_RESH = 3
        self.INPUT_GENERAL = 4
        self.INPUT_ROM_VALUE = 5
        self.INPUT_XL = 6
        self.INPUT_XH = 7
        self.INPUT_YL = 8
        self.INPUT_YH = 9
        self.INPUT_ZL = 10
        self.INPUT_ZH = 11
        self.INPUT_SPL = 12
        self.INPUT_SPH = 13
        self.INPUT_PCL = 14
        self.INPUT_PCH = 15
        self.INPUT_RD_BUFFER = 16
        self.INPUT_ROM_2 = 17
        self.LOAD_BUS_DATA = 1
        self.LOAD_XL_MINUS = 2
        self.LOAD_XH_MINUS = 3
        self.LOAD_XL_PLUS = 4
        self.LOAD_XH_PLUS = 5
        self.LOAD_YL_MINUS = 6
        self.LOAD_YH_MINUS = 7
        self.LOAD_YL_PLUS = 8
        self.LOAD_YH_PLUS = 9
        self.LOAD_ZL_MINUS = 10
        self.LOAD_ZH_MINUS = 11
        self.LOAD_ZL_PLUS = 12
        self.LOAD_ZH_PLUS = 13
        self.LOAD_XL = 1
        self.LOAD_XH = 2
        self.LOAD_YL = 3
        self.LOAD_YH = 4
        self.LOAD_ZL = 5
        self.LOAD_ZH = 6
        self.LOAD_SPL = 7
        self.LOAD_SPH = 8
        self.LOAD_RD_BUFFER = 14
        self.LOAD_R0_BUFFER = 15
        self.LOAD_R1_BUFFER = 16
        self.INC_NONE = 0
        self.INC_POST_INC = 1
        self.INC_PRE_DEC = 2
        self.INC_POST_DEC = 3
        self.INC_PRE_INC = 4

        # NOTE: was `self.mem = self.addInterfaceSource('memory', memory)`.
        # Replaced with individual flat addOut/addIn calls on the same
        # underlying wires -- see the matching note in RomHandler.py and
        # py4hw_bug_reports.md, Issue 6.
        self.memory_read      = self.addOut('memory_read', memory.read)
        self.memory_write     = self.addOut('memory_write', memory.write)
        self.memory_address   = self.addOut('memory_address', memory.address)
        self.memory_writedata = self.addOut('memory_writedata', memory.write_data)
        self.memory_instype   = self.addOut('memory_instype', memory.instype)
        self.memory_readdata  = self.addIn('memory_readdata', memory.read_data)
        self.memory_resp      = self.addIn('memory_resp', memory.resp)

        self.reset = self.addIn('reset', reset)
        self.WE = self.addIn('WE', WE)
        self.LoadSelectMux = self.addIn('LoadSelectMux', LoadSelectMux)
        self.LoadingMux = self.addIn('LoadingMux', LoadingMux)
        self.IncDec = self.addIn('IncDec', IncDec)
        self.ReadWrite = self.addIn('ReadWrite', ReadWrite)
        self.InputSelectMemory = self.addIn('InputSelectMemory', InputSelectMemory)
        self.Mem_instruction = self.addIn('Mem_instruction', Mem_instruction)
        self.RomAddress = self.addIn('RomAddress', RomAddress) 
        self.RomAddressValue = self.addIn('RomAddressValue',RomAddressValue)

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

        self.R0_BUFFER_out = self.addOut('R0_BUFFER_out',R0_BUFFER_OUT)
        self.R1_BUFFER_out = self.addOut('R1_BUFFER_out',R1_BUFFER_OUT)

        self.ROM_VAL = self.addIn('ROM_VAL',ROM_VAL_IN)


        #---- SREG (relocated -- MIH is controller only, see __init__ docstring) ----
        self.SREG_IN = self.addIn('SREG_IN',SREG_In)
        self.eSREG = self.addIn('eSREG',eSREG_In)
        self.ALU_Commit = self.addIn('ALU_Commit', ALU_Commit)
        self.SREG_ReadValue = self.addIn('SREG_ReadValue', SREG_ReadValue)
        self.SREG_WriteValue = self.addOut('SREG_WriteValue', SREG_WriteValue)
        self.SREG_WriteMask = self.addOut('SREG_WriteMask', SREG_WriteMask)

        # Standard AVR SREG bit ordering used throughout this project
        # (I-T-H-S-V-N-Z-C, see ALU.py): I is bit 7. Kept here since the
        # SREG_ADDR (0x5F) IN/OUT intercept below still needs to know it
        # even though the I flag's storage itself now lives in Datapath.
        self.I_FLAG_BIT = 7

        #---- Bus Address Register (MAR) shadow output ----
        self.MAR_ValueOut = self.addOut('MAR_ValueOut', MAR_ValueOut)

        self.Bus_Passthrough_Ranges = Bus_Passthrough_Ranges


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
        # io_scratch register bank: one discrete register per address in
        # [0x0020, 0x00FF]. Replaces the old Python dict (self.io_scratch = {})
        # -- a dict indexed by a runtime value is a RAM, and the stock
        # transpiler's __init__ parser has no concept of arrays/dicts at all
        # (see report). 224 discrete 8-bit registers + an address-decoded
        # if/elif dispatch (below, in clock()) is the direct translation of
        # 'a byte-addressable RAM with no native array primitive available'.
        self._io_20 = 0
        self._io_21 = 0
        self._io_22 = 0
        self._io_23 = 0
        self._io_24 = 0
        self._io_25 = 0
        self._io_26 = 0
        self._io_27 = 0
        self._io_28 = 0
        self._io_29 = 0
        self._io_2a = 0
        self._io_2b = 0
        self._io_2c = 0
        self._io_2d = 0
        self._io_2e = 0
        self._io_2f = 0
        self._io_30 = 0
        self._io_31 = 0
        self._io_32 = 0
        self._io_33 = 0
        self._io_34 = 0
        self._io_35 = 0
        self._io_36 = 0
        self._io_37 = 0
        self._io_38 = 0
        self._io_39 = 0
        self._io_3a = 0
        self._io_3b = 0
        self._io_3c = 0
        self._io_3d = 0
        self._io_3e = 0
        self._io_3f = 0
        self._io_40 = 0
        self._io_41 = 0
        self._io_42 = 0
        self._io_43 = 0
        self._io_44 = 0
        self._io_45 = 0
        self._io_46 = 0
        self._io_47 = 0
        self._io_48 = 0
        self._io_49 = 0
        self._io_4a = 0
        self._io_4b = 0
        self._io_4c = 0
        self._io_4d = 0
        self._io_4e = 0
        self._io_4f = 0
        self._io_50 = 0
        self._io_51 = 0
        self._io_52 = 0
        self._io_53 = 0
        self._io_54 = 0
        self._io_55 = 0
        self._io_56 = 0
        self._io_57 = 0
        self._io_58 = 0
        self._io_59 = 0
        self._io_5a = 0
        self._io_5b = 0
        self._io_5c = 0
        self._io_5d = 0
        self._io_5e = 0
        self._io_5f = 0
        self._io_60 = 0
        self._io_61 = 0
        self._io_62 = 0
        self._io_63 = 0
        self._io_64 = 0
        self._io_65 = 0
        self._io_66 = 0
        self._io_67 = 0
        self._io_68 = 0
        self._io_69 = 0
        self._io_6a = 0
        self._io_6b = 0
        self._io_6c = 0
        self._io_6d = 0
        self._io_6e = 0
        self._io_6f = 0
        self._io_70 = 0
        self._io_71 = 0
        self._io_72 = 0
        self._io_73 = 0
        self._io_74 = 0
        self._io_75 = 0
        self._io_76 = 0
        self._io_77 = 0
        self._io_78 = 0
        self._io_79 = 0
        self._io_7a = 0
        self._io_7b = 0
        self._io_7c = 0
        self._io_7d = 0
        self._io_7e = 0
        self._io_7f = 0
        self._io_80 = 0
        self._io_81 = 0
        self._io_82 = 0
        self._io_83 = 0
        self._io_84 = 0
        self._io_85 = 0
        self._io_86 = 0
        self._io_87 = 0
        self._io_88 = 0
        self._io_89 = 0
        self._io_8a = 0
        self._io_8b = 0
        self._io_8c = 0
        self._io_8d = 0
        self._io_8e = 0
        self._io_8f = 0
        self._io_90 = 0
        self._io_91 = 0
        self._io_92 = 0
        self._io_93 = 0
        self._io_94 = 0
        self._io_95 = 0
        self._io_96 = 0
        self._io_97 = 0
        self._io_98 = 0
        self._io_99 = 0
        self._io_9a = 0
        self._io_9b = 0
        self._io_9c = 0
        self._io_9d = 0
        self._io_9e = 0
        self._io_9f = 0
        self._io_a0 = 0
        self._io_a1 = 0
        self._io_a2 = 0
        self._io_a3 = 0
        self._io_a4 = 0
        self._io_a5 = 0
        self._io_a6 = 0
        self._io_a7 = 0
        self._io_a8 = 0
        self._io_a9 = 0
        self._io_aa = 0
        self._io_ab = 0
        self._io_ac = 0
        self._io_ad = 0
        self._io_ae = 0
        self._io_af = 0
        self._io_b0 = 0
        self._io_b1 = 0
        self._io_b2 = 0
        self._io_b3 = 0
        self._io_b4 = 0
        self._io_b5 = 0
        self._io_b6 = 0
        self._io_b7 = 0
        self._io_b8 = 0
        self._io_b9 = 0
        self._io_ba = 0
        self._io_bb = 0
        self._io_bc = 0
        self._io_bd = 0
        self._io_be = 0
        self._io_bf = 0
        self._io_c0 = 0
        self._io_c1 = 0
        self._io_c2 = 0
        self._io_c3 = 0
        self._io_c4 = 0
        self._io_c5 = 0
        self._io_c6 = 0
        self._io_c7 = 0
        self._io_c8 = 0
        self._io_c9 = 0
        self._io_ca = 0
        self._io_cb = 0
        self._io_cc = 0
        self._io_cd = 0
        self._io_ce = 0
        self._io_cf = 0
        self._io_d0 = 0
        self._io_d1 = 0
        self._io_d2 = 0
        self._io_d3 = 0
        self._io_d4 = 0
        self._io_d5 = 0
        self._io_d6 = 0
        self._io_d7 = 0
        self._io_d8 = 0
        self._io_d9 = 0
        self._io_da = 0
        self._io_db = 0
        self._io_dc = 0
        self._io_dd = 0
        self._io_de = 0
        self._io_df = 0
        self._io_e0 = 0
        self._io_e1 = 0
        self._io_e2 = 0
        self._io_e3 = 0
        self._io_e4 = 0
        self._io_e5 = 0
        self._io_e6 = 0
        self._io_e7 = 0
        self._io_e8 = 0
        self._io_e9 = 0
        self._io_ea = 0
        self._io_eb = 0
        self._io_ec = 0
        self._io_ed = 0
        self._io_ee = 0
        self._io_ef = 0
        self._io_f0 = 0
        self._io_f1 = 0
        self._io_f2 = 0
        self._io_f3 = 0
        self._io_f4 = 0
        self._io_f5 = 0
        self._io_f6 = 0
        self._io_f7 = 0
        self._io_f8 = 0
        self._io_f9 = 0
        self._io_fa = 0
        self._io_fb = 0
        self._io_fc = 0
        self._io_fd = 0
        self._io_fe = 0
        self._io_ff = 0
        self.XregL = 0
        self.XregH = 0
        self.YregL = 0
        self.YregH = 0
        self.ZregL = 0
        self.ZregH = 0
        self.SPL = 0
        self.SPH = 0
        self.RdBuffer = 0  

        # FIX (test_data_SPM.asm): SPMCR (self-programming control
        # register, real ATmega328P I/O 0x37 / SRAM 0x57) needs to behave
        # as a plain read/write register -- see the SPMCR_ADDR intercept
        # note in clock() below for why it can't just fall through to the
        # generic io_scratch path like most unimplemented registers do.
        self.SPMCR = 0

        self.R0Buffer = 0 
        self.R1Buffer = 0 

        self.BusData = 0
        self.Databuffer = 0
        self.debug = 1

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
            self.SPL = 0
            self.SPH = 0
            self.SPMCR = 0
            self.BusData = 0

            self.RegisterOut.prepare(0)
            self.address_ZL.prepare(0)
            self.address_ZH.prepare(0)
            self.memory_address.prepare(0)
            self.memory_writedata.prepare(0)
            self.memory_instype.prepare(1)
        else:

            # ----------------------------------------------
            # 1. Address generation
            # ----------------------------------------------
            # Inlined from selectAddress()/getX()/getY()/getZ()/getSP() --
            # the stock transpiler does not expand calls to helper methods
            # from clock()/propagate(), so this used to be a hard blocker
            # (see report). getX()/getY()/getZ()/getSP() themselves are
            # inlined too (each was a one-line pure function of instance
            # state, safe to substitute directly wherever called).
            #
            # pointer_name is encoded as an integer instead of a string,
            # matching the fix applied to the FSM current_state variables
            # elsewhere in this project (see report): 0 = no pointer
            # (NONE), 1 = X, 2 = Y, 3 = Z, 4 = SP, 5 = ROM.
            mem_instr = self.Mem_instruction.get()
            address = 0
            pointer_name = 0

            if (mem_instr == self.MEM_X) or (mem_instr == self.MEM_X_PLUS):
                address = (self.XregH << 8) | self.XregL
                pointer_name = 1
            elif (mem_instr == self.MEM_Y) or (mem_instr == self.MEM_Y_PLUS):
                address = (self.YregH << 8) | self.YregL
                pointer_name = 2
            elif (mem_instr == self.MEM_Z) or (mem_instr == self.MEM_Z_PLUS):
                address = (self.ZregH << 8) | self.ZregL
                pointer_name = 3
            elif (mem_instr == self.MEM_SP) or (mem_instr == self.MEM_SP_PLUS):
                address = (self.SPH << 8) | self.SPL
                pointer_name = 4
            elif mem_instr == self.MEM_RAM_ADDR_REG:
                address = self.RomAddressValue.get()
                pointer_name = 5

            elif mem_instr == self.MEM_RD:
                address = self.Rd.get() & 0x1F
                pointer_name = 0

            elif mem_instr == self.MEM_RR:
                address = self.Rr.get() & 0x1F
                pointer_name = 0

            elif mem_instr == self.MEM_WB_ADDR:
                address = self.WbAddr.get() & 0x1F
                pointer_name = 0

            elif mem_instr == self.MEM_Y_Q:
                # q is a 6-bit UNSIGNED displacement (0-63) -- LDD/STD Y+q
                # always indexes forward from Y, never backward. No sign
                # extension here; q_val is used exactly as decoded.
                q_val = self.Q.get() & 0x3F
                address = ((self.YregH << 8) | self.YregL) + q_val

            elif mem_instr == self.MEM_Z_Q:
                # Same as MEM_Y_Q above: q is unsigned, 0-63.
                q_val = self.Q.get() & 0x3F
                address = ((self.ZregH << 8) | self.ZregL) + q_val

            elif mem_instr == self.MEM_RD_1:
                address = (self.Rd.get()+1) & 0x1F
                pointer_name = 0

            elif mem_instr == self.MEM_RR_1:
                address = (self.Rr.get()+1) & 0x1F
                pointer_name = 0

            # --- OUT / IN ADDRESS GENERATION ---
            # AVR I/O space begins at SRAM offset 0x20. By adding 0x20 here,
            # standard LDST_FSM logic handles it identically to standard RAM accesses.
            elif mem_instr == self.MEM_A_5bit:
                address = self.A_5bit.get() + 0x20
                pointer_name = 0

            elif mem_instr == self.MEM_A_6bit:
                address = self.A_6bit.get() + 0x20
                pointer_name = 0

            elif mem_instr == self.MEM_INT_VECTOR_L:
                address = 0x00FE
                pointer_name = 0

            elif mem_instr == self.MEM_INT_VECTOR_H:
                address = 0x00FF
                pointer_name = 0

            # UPDATED: Apply Pre-decrement OR Pre-increment BEFORE accessing memory
            incdec_mode = self.IncDec.get()
            if (pointer_name == 1) or (pointer_name == 2) or (pointer_name == 3) or (pointer_name == 4):
                if incdec_mode == self.INC_PRE_DEC:
                    address -= 1
                elif incdec_mode == self.INC_PRE_INC:
                    address += 1

            address = address & 0xFFFF

            self.memory_address.prepare(address)
            # MAR shadow: mirrors the same address for Datapath's standalone
            # bus-address register. Purely observational -- does not affect
            # the real transaction above.
            self.MAR_ValueOut.prepare(address)

            # FIX (found while building tb_timer_tests.py's real-CPU
            # Timer0/1/2 integration): self.memory_instype was declared as
            # an output bound to memory.instype (see __init__) but never
            # .prepare()'d anywhere in this class -- it silently sat at its
            # default 0 forever. Every address this handler ever puts on
            # the external bus is already absolute/"LS-style" (classic
            # IN/OUT's 6-bit IO address is converted to this same absolute
            # form by adding 0x20 above, in the MEM_A_6bit branch, before
            # it ever leaves this component) -- there is no code path in
            # which this handler emits a raw, un-offset IO address onto
            # the shared bus. So instype should always read 1 on this bus;
            # peripherals that distinguish IO-style (instype=0, the
            # `_addr_IO` constants in GPIO.py/Timers.py/ADC.py) from
            # LDS/STS-style (instype=1, the `_addr_LS` constants) addressing
            # never actually see instype=0 from the real CPU, so their
            # `_addr_IO` branches are effectively unreachable dead code
            # given this CPU's addressing convention -- harmless, but
            # worth knowing if that ever needs revisiting.
            #
            # Without this fix, every peripheral that gates its register
            # decode on `instype.get() == 1` (the real TimerCounter0/1/2,
            # and GPIO's LS-style branches) never asserts `resp`, and the
            # CPU hangs forever waiting for a response that will never
            # come -- confirmed live: `sts TCCR0B, r16` through the real
            # CPU + real TimerCounter0 hung at PC=0x000C with
            # `instype.get()==0`/`resp.get()==0` on TimerCounter0's port
            # every cycle, for as long as this went unfixed. The ISA
            # suite's 111/111 never caught this because its peripherals
            # (VirtualGPIO, SimpleTimer, VirtualUSART) don't check instype
            # at all -- only the *real* GPIO/TimerCounter classes do.
            self.memory_instype.prepare(1)

            # ----------------------------------------------
            # 2. Memory operation & BusData latching (INTERCEPT LOGIC)
            # ----------------------------------------------
            rw = self.ReadWrite.get()

            # ATmega328P SRAM Data Space addresses for SP
            SP_L_ADDR = 0x5D
            SP_H_ADDR = 0x5E

            SREG_ADDR = 0x5F

            # FIX (test_data_SPM.asm "failed in test case 0"): SPMCR's real
            # SRAM address (I/O 0x37 -> SRAM 0x57) lands numerically inside
            # the test harness's Bus_Passthrough_Ranges window for the timer
            # peripheral (0x40-0x6F), even though SPMCR has nothing to do with
            # Timer0 -- that window is just drawn wide enough to cover every
            # extended-I/O timer register in one span. Without this intercept,
            # SPMCR reads/writes were being routed to SimpleTimer (Timers.py),
            # which only recognizes its own five relative sub-addresses and
            # silently no-ops anything else: writes vanish, reads always
            # return 0. Intercepting it here -- same pattern as
            # SP_L_ADDR/SP_H_ADDR/SREG_ADDR above -- makes it a plain
            # read/write register.
            SPMCR_ADDR = 0x57

            # Interrupt vector bytes and any other peripheral windows a
            # testbench has declared via Bus_Passthrough_Ranges (see __init__)
            # fall inside the [0x0020, 0x0100) range that would otherwise be
            # swallowed into the io_scratch register bank a few lines down --
            # carved out here so the peripherals actually mapped there on the
            # real bus (GPIO, a timer, an InterruptUnit, ...) actually see
            # these transactions instead of getting silently intercepted.
            #
            # Inlined from isBusPassthrough(): the stock transpiler does not
            # expand helper-method calls from clock() (see report). Unlike
            # Bus_Passthrough_Ranges (still a real, simulation-configurable
            # constructor parameter -- see __init__), this inlined check is
            # fixed at the four ranges the ISA test harness actually
            # configures (tb_ISA_test_Multicycle_Rewrite.py): GPIO/misc
            # (0x20-0x36), a second peripheral window (0x38-0x3F), the timer
            # (0x40-0x6F), and the interrupt vector bytes (0xFE-0xFF). If
            # Bus_Passthrough_Ranges is ever reconfigured for a different
            # memory map, this inline check must be updated to match.
            # EXTENDED (timer test-harness support): the four ranges above
            # are exactly what tb_ISA_test_Multicycle_Rewrite.py /
            # tb_timers.py (Timer0-only) configure. Bringing TimerCounter1
            # and TimerCounter2 onto the real CPU bus (tb_timer_tests.py)
            # needs their registers passed through too: 0x37 (TIFR2 -- the
            # original four ranges have a gap here, between 0x36 and 0x38,
            # that was never TIFR2-related, just an accident of where the
            # SPMCR intercept below lives), 0x70 (TIMSK2), and 0x80-0x8B
            # (TCCR1A/B/C, TCNT1L/H, ICR1L/H, OCR1AL/H, OCR1BL/H) and
            # 0xB0-0xB4 (TCCR2A/B, TCNT2, OCR2A/B). Purely additive --
            # every address the original four ranges covered is still
            # covered, so this cannot affect the 111-test ISA suite or the
            # existing Timer0-only harness.
            # EXTENDED AGAIN (TWI/I2C test-harness support): TWBR/TWSR/
            # TWAR/TWDR/TWCR at 0xB8-0xBC. Same additive-only guarantee
            # as the timer extension above.
            # EXTENDED AGAIN (USART0 test-harness support): UCSR0A/B/C,
            # UBRR0L/H, UDR0 at 0xC0-0xC6 (0xC7 included for headroom/
            # alignment with tb_usart.py's own window). tb_usart.py's
            # docstring already flagged this exact gap -- its own
            # Bus_Passthrough_Ranges constructor argument included
            # (0xC0, 0xC7), but (as this comment block explains above)
            # that parameter was never actually read at runtime, so the
            # real gate here needed the same fix directly.
            # EXTENDED AGAIN (ADC support): ADCL/ADCH/ADCSRA/ADCSRB/
            # ADMUX/DIDR0 at 0x78-0x7E -- same gap, same fix, same
            # additive-only guarantee. Found the same way as every prior
            # extension in this block: `sts ADCSRA, r16` through the real
            # CPU + real ADC hung with resp stuck at 0 until this range
            # was added.
            is_passthrough = (
                ((address >= 0x20) and (address <= 0x36)) or
                (address == 0x37) or
                ((address >= 0x38) and (address <= 0x3F)) or
                ((address >= 0x40) and (address <= 0x6F)) or
                (address == 0x70) or
                ((address >= 0x78) and (address <= 0x7E)) or
                ((address >= 0x80) and (address <= 0x8B)) or
                ((address >= 0xB0) and (address <= 0xB4)) or
                ((address >= 0xB8) and (address <= 0xBC)) or
                ((address >= 0xC0) and (address <= 0xC7)) or
                ((address >= 0xFE) and (address <= 0xFF))
            )

            resp_val = 0
            sreg_bus_write_pending = 0
            sreg_bus_write_value = 0
            if rw == 1: # WRITE OPERATION
                # Inlined from selectWriteData() -- see report (no call
                # inlining in the stock transpiler).
                sel = self.InputSelectMemory.get()
                write_data = 0

                if sel == self.INPUT_DATABUS:
                    write_data = self.memory_readdata.get()
                elif sel == self.INPUT_RESL:
                    write_data = self.ResL.get()
                elif sel == self.INPUT_RESH:
                    write_data = self.ResH.get()
                elif sel == self.INPUT_GENERAL:
                    write_data = self.K_val_Input.get()
                elif sel == self.INPUT_ROM_VALUE:
                    write_data = self.RomAddressValue.get()
                elif sel == self.INPUT_XL:
                    write_data = self.XregL
                elif sel == self.INPUT_XH:
                    write_data = self.XregH
                elif sel == self.INPUT_YL:
                    write_data = self.YregL
                elif sel == self.INPUT_YH:
                    write_data = self.YregH
                elif sel == self.INPUT_ZL:
                    write_data = self.ZregL
                elif sel == self.INPUT_ZH:
                    write_data = self.ZregH
                elif sel == self.INPUT_SPL:
                    write_data = self.SPL
                elif sel == self.INPUT_SPH:
                    write_data = self.SPH
                elif sel == self.INPUT_PCL:
                    # Add the decoder-provided push offset to the FULL 16-bit PC so
                    # a carry out of the low byte propagates into the high byte
                    # (e.g. PC=0x00FF + 1 must push PCL=0x00, PCH=0x01).
                    pc_full = (((self.PCH_VAL_IN.get() << 8) | self.PCL_VAL_IN.get())
                               + self.PC_Offset.get()) & 0xFFFF
                    write_data = pc_full & 0xFF
                elif sel == self.INPUT_PCH:
                    pc_full = (((self.PCH_VAL_IN.get() << 8) | self.PCL_VAL_IN.get())
                               + self.PC_Offset.get()) & 0xFFFF
                    write_data = (pc_full >> 8) & 0xFF
                elif sel == self.INPUT_RD_BUFFER:
                    write_data = self.RdBuffer
                elif sel == self.INPUT_ROM_2:
                    write_data = self.ROM_VAL.get()

                self.BusData = write_data

                # Intercept SP Writes
                if address == SP_L_ADDR:
                    self.SPL = self.BusData & 0xFF
                    self.memory_write.prepare(0) # Bypass SRAM write
                    resp_val = 1

                elif address == SP_H_ADDR:
                    self.SPH = self.BusData & 0xFF
                    self.memory_write.prepare(0) # Bypass SRAM write
                    resp_val = 1

                elif address == SREG_ADDR:
                    # Full-byte SREG write via IN/OUT/direct-STS. Recorded here
                    # as a pending bus write; folded into SREG_WriteValue/Mask
                    # together with the ALU's masked update at the end of this
                    # method (bus write applies first, eSREG mask wins on any
                    # overlapping bits -- see the __init__ docstring note).
                    sreg_bus_write_pending = 1
                    sreg_bus_write_value = self.BusData & 0xFF
                    self.memory_write.prepare(0)
                    resp_val = 1

                elif address == SPMCR_ADDR:
                    self.SPMCR = self.BusData & 0xFF
                    self.memory_write.prepare(0)  # Bypass the timer peripheral
                    resp_val = 1

                elif ((address >= 0x0020) and (address < 0x0100)) and (not is_passthrough):
                    # Any other memory-mapped I/O / extended I/O register with
                    # no dedicated hardware model yet (EIMSK, EICRA, SMCR, ...).
                    # Real SRAM starts at 0x0100, so anything below that is
                    # either register file or (extended) I/O space -- neither
                    # of which the underlying Memory object backs. Store the
                    # value and ack immediately rather than hanging forever.
                    #
                    # Address-decoded dispatch into the io_scratch register
                    # bank (self._io_XX, one 8-bit register per address --
                    # see __init__) -- inlined replacement for the old
                    # `self.io_scratch[address] = ...` dict write (see
                    # report: the stock transpiler has no array/RAM support).
                    if address == 0x20:
                        self._io_20 = self.BusData & 0xFF
                    elif address == 0x21:
                        self._io_21 = self.BusData & 0xFF
                    elif address == 0x22:
                        self._io_22 = self.BusData & 0xFF
                    elif address == 0x23:
                        self._io_23 = self.BusData & 0xFF
                    elif address == 0x24:
                        self._io_24 = self.BusData & 0xFF
                    elif address == 0x25:
                        self._io_25 = self.BusData & 0xFF
                    elif address == 0x26:
                        self._io_26 = self.BusData & 0xFF
                    elif address == 0x27:
                        self._io_27 = self.BusData & 0xFF
                    elif address == 0x28:
                        self._io_28 = self.BusData & 0xFF
                    elif address == 0x29:
                        self._io_29 = self.BusData & 0xFF
                    elif address == 0x2a:
                        self._io_2a = self.BusData & 0xFF
                    elif address == 0x2b:
                        self._io_2b = self.BusData & 0xFF
                    elif address == 0x2c:
                        self._io_2c = self.BusData & 0xFF
                    elif address == 0x2d:
                        self._io_2d = self.BusData & 0xFF
                    elif address == 0x2e:
                        self._io_2e = self.BusData & 0xFF
                    elif address == 0x2f:
                        self._io_2f = self.BusData & 0xFF
                    elif address == 0x30:
                        self._io_30 = self.BusData & 0xFF
                    elif address == 0x31:
                        self._io_31 = self.BusData & 0xFF
                    elif address == 0x32:
                        self._io_32 = self.BusData & 0xFF
                    elif address == 0x33:
                        self._io_33 = self.BusData & 0xFF
                    elif address == 0x34:
                        self._io_34 = self.BusData & 0xFF
                    elif address == 0x35:
                        self._io_35 = self.BusData & 0xFF
                    elif address == 0x36:
                        self._io_36 = self.BusData & 0xFF
                    elif address == 0x37:
                        self._io_37 = self.BusData & 0xFF
                    elif address == 0x38:
                        self._io_38 = self.BusData & 0xFF
                    elif address == 0x39:
                        self._io_39 = self.BusData & 0xFF
                    elif address == 0x3a:
                        self._io_3a = self.BusData & 0xFF
                    elif address == 0x3b:
                        self._io_3b = self.BusData & 0xFF
                    elif address == 0x3c:
                        self._io_3c = self.BusData & 0xFF
                    elif address == 0x3d:
                        self._io_3d = self.BusData & 0xFF
                    elif address == 0x3e:
                        self._io_3e = self.BusData & 0xFF
                    elif address == 0x3f:
                        self._io_3f = self.BusData & 0xFF
                    elif address == 0x40:
                        self._io_40 = self.BusData & 0xFF
                    elif address == 0x41:
                        self._io_41 = self.BusData & 0xFF
                    elif address == 0x42:
                        self._io_42 = self.BusData & 0xFF
                    elif address == 0x43:
                        self._io_43 = self.BusData & 0xFF
                    elif address == 0x44:
                        self._io_44 = self.BusData & 0xFF
                    elif address == 0x45:
                        self._io_45 = self.BusData & 0xFF
                    elif address == 0x46:
                        self._io_46 = self.BusData & 0xFF
                    elif address == 0x47:
                        self._io_47 = self.BusData & 0xFF
                    elif address == 0x48:
                        self._io_48 = self.BusData & 0xFF
                    elif address == 0x49:
                        self._io_49 = self.BusData & 0xFF
                    elif address == 0x4a:
                        self._io_4a = self.BusData & 0xFF
                    elif address == 0x4b:
                        self._io_4b = self.BusData & 0xFF
                    elif address == 0x4c:
                        self._io_4c = self.BusData & 0xFF
                    elif address == 0x4d:
                        self._io_4d = self.BusData & 0xFF
                    elif address == 0x4e:
                        self._io_4e = self.BusData & 0xFF
                    elif address == 0x4f:
                        self._io_4f = self.BusData & 0xFF
                    elif address == 0x50:
                        self._io_50 = self.BusData & 0xFF
                    elif address == 0x51:
                        self._io_51 = self.BusData & 0xFF
                    elif address == 0x52:
                        self._io_52 = self.BusData & 0xFF
                    elif address == 0x53:
                        self._io_53 = self.BusData & 0xFF
                    elif address == 0x54:
                        self._io_54 = self.BusData & 0xFF
                    elif address == 0x55:
                        self._io_55 = self.BusData & 0xFF
                    elif address == 0x56:
                        self._io_56 = self.BusData & 0xFF
                    elif address == 0x57:
                        self._io_57 = self.BusData & 0xFF
                    elif address == 0x58:
                        self._io_58 = self.BusData & 0xFF
                    elif address == 0x59:
                        self._io_59 = self.BusData & 0xFF
                    elif address == 0x5a:
                        self._io_5a = self.BusData & 0xFF
                    elif address == 0x5b:
                        self._io_5b = self.BusData & 0xFF
                    elif address == 0x5c:
                        self._io_5c = self.BusData & 0xFF
                    elif address == 0x5d:
                        self._io_5d = self.BusData & 0xFF
                    elif address == 0x5e:
                        self._io_5e = self.BusData & 0xFF
                    elif address == 0x5f:
                        self._io_5f = self.BusData & 0xFF
                    elif address == 0x60:
                        self._io_60 = self.BusData & 0xFF
                    elif address == 0x61:
                        self._io_61 = self.BusData & 0xFF
                    elif address == 0x62:
                        self._io_62 = self.BusData & 0xFF
                    elif address == 0x63:
                        self._io_63 = self.BusData & 0xFF
                    elif address == 0x64:
                        self._io_64 = self.BusData & 0xFF
                    elif address == 0x65:
                        self._io_65 = self.BusData & 0xFF
                    elif address == 0x66:
                        self._io_66 = self.BusData & 0xFF
                    elif address == 0x67:
                        self._io_67 = self.BusData & 0xFF
                    elif address == 0x68:
                        self._io_68 = self.BusData & 0xFF
                    elif address == 0x69:
                        self._io_69 = self.BusData & 0xFF
                    elif address == 0x6a:
                        self._io_6a = self.BusData & 0xFF
                    elif address == 0x6b:
                        self._io_6b = self.BusData & 0xFF
                    elif address == 0x6c:
                        self._io_6c = self.BusData & 0xFF
                    elif address == 0x6d:
                        self._io_6d = self.BusData & 0xFF
                    elif address == 0x6e:
                        self._io_6e = self.BusData & 0xFF
                    elif address == 0x6f:
                        self._io_6f = self.BusData & 0xFF
                    elif address == 0x70:
                        self._io_70 = self.BusData & 0xFF
                    elif address == 0x71:
                        self._io_71 = self.BusData & 0xFF
                    elif address == 0x72:
                        self._io_72 = self.BusData & 0xFF
                    elif address == 0x73:
                        self._io_73 = self.BusData & 0xFF
                    elif address == 0x74:
                        self._io_74 = self.BusData & 0xFF
                    elif address == 0x75:
                        self._io_75 = self.BusData & 0xFF
                    elif address == 0x76:
                        self._io_76 = self.BusData & 0xFF
                    elif address == 0x77:
                        self._io_77 = self.BusData & 0xFF
                    elif address == 0x78:
                        self._io_78 = self.BusData & 0xFF
                    elif address == 0x79:
                        self._io_79 = self.BusData & 0xFF
                    elif address == 0x7a:
                        self._io_7a = self.BusData & 0xFF
                    elif address == 0x7b:
                        self._io_7b = self.BusData & 0xFF
                    elif address == 0x7c:
                        self._io_7c = self.BusData & 0xFF
                    elif address == 0x7d:
                        self._io_7d = self.BusData & 0xFF
                    elif address == 0x7e:
                        self._io_7e = self.BusData & 0xFF
                    elif address == 0x7f:
                        self._io_7f = self.BusData & 0xFF
                    elif address == 0x80:
                        self._io_80 = self.BusData & 0xFF
                    elif address == 0x81:
                        self._io_81 = self.BusData & 0xFF
                    elif address == 0x82:
                        self._io_82 = self.BusData & 0xFF
                    elif address == 0x83:
                        self._io_83 = self.BusData & 0xFF
                    elif address == 0x84:
                        self._io_84 = self.BusData & 0xFF
                    elif address == 0x85:
                        self._io_85 = self.BusData & 0xFF
                    elif address == 0x86:
                        self._io_86 = self.BusData & 0xFF
                    elif address == 0x87:
                        self._io_87 = self.BusData & 0xFF
                    elif address == 0x88:
                        self._io_88 = self.BusData & 0xFF
                    elif address == 0x89:
                        self._io_89 = self.BusData & 0xFF
                    elif address == 0x8a:
                        self._io_8a = self.BusData & 0xFF
                    elif address == 0x8b:
                        self._io_8b = self.BusData & 0xFF
                    elif address == 0x8c:
                        self._io_8c = self.BusData & 0xFF
                    elif address == 0x8d:
                        self._io_8d = self.BusData & 0xFF
                    elif address == 0x8e:
                        self._io_8e = self.BusData & 0xFF
                    elif address == 0x8f:
                        self._io_8f = self.BusData & 0xFF
                    elif address == 0x90:
                        self._io_90 = self.BusData & 0xFF
                    elif address == 0x91:
                        self._io_91 = self.BusData & 0xFF
                    elif address == 0x92:
                        self._io_92 = self.BusData & 0xFF
                    elif address == 0x93:
                        self._io_93 = self.BusData & 0xFF
                    elif address == 0x94:
                        self._io_94 = self.BusData & 0xFF
                    elif address == 0x95:
                        self._io_95 = self.BusData & 0xFF
                    elif address == 0x96:
                        self._io_96 = self.BusData & 0xFF
                    elif address == 0x97:
                        self._io_97 = self.BusData & 0xFF
                    elif address == 0x98:
                        self._io_98 = self.BusData & 0xFF
                    elif address == 0x99:
                        self._io_99 = self.BusData & 0xFF
                    elif address == 0x9a:
                        self._io_9a = self.BusData & 0xFF
                    elif address == 0x9b:
                        self._io_9b = self.BusData & 0xFF
                    elif address == 0x9c:
                        self._io_9c = self.BusData & 0xFF
                    elif address == 0x9d:
                        self._io_9d = self.BusData & 0xFF
                    elif address == 0x9e:
                        self._io_9e = self.BusData & 0xFF
                    elif address == 0x9f:
                        self._io_9f = self.BusData & 0xFF
                    elif address == 0xa0:
                        self._io_a0 = self.BusData & 0xFF
                    elif address == 0xa1:
                        self._io_a1 = self.BusData & 0xFF
                    elif address == 0xa2:
                        self._io_a2 = self.BusData & 0xFF
                    elif address == 0xa3:
                        self._io_a3 = self.BusData & 0xFF
                    elif address == 0xa4:
                        self._io_a4 = self.BusData & 0xFF
                    elif address == 0xa5:
                        self._io_a5 = self.BusData & 0xFF
                    elif address == 0xa6:
                        self._io_a6 = self.BusData & 0xFF
                    elif address == 0xa7:
                        self._io_a7 = self.BusData & 0xFF
                    elif address == 0xa8:
                        self._io_a8 = self.BusData & 0xFF
                    elif address == 0xa9:
                        self._io_a9 = self.BusData & 0xFF
                    elif address == 0xaa:
                        self._io_aa = self.BusData & 0xFF
                    elif address == 0xab:
                        self._io_ab = self.BusData & 0xFF
                    elif address == 0xac:
                        self._io_ac = self.BusData & 0xFF
                    elif address == 0xad:
                        self._io_ad = self.BusData & 0xFF
                    elif address == 0xae:
                        self._io_ae = self.BusData & 0xFF
                    elif address == 0xaf:
                        self._io_af = self.BusData & 0xFF
                    elif address == 0xb0:
                        self._io_b0 = self.BusData & 0xFF
                    elif address == 0xb1:
                        self._io_b1 = self.BusData & 0xFF
                    elif address == 0xb2:
                        self._io_b2 = self.BusData & 0xFF
                    elif address == 0xb3:
                        self._io_b3 = self.BusData & 0xFF
                    elif address == 0xb4:
                        self._io_b4 = self.BusData & 0xFF
                    elif address == 0xb5:
                        self._io_b5 = self.BusData & 0xFF
                    elif address == 0xb6:
                        self._io_b6 = self.BusData & 0xFF
                    elif address == 0xb7:
                        self._io_b7 = self.BusData & 0xFF
                    elif address == 0xb8:
                        self._io_b8 = self.BusData & 0xFF
                    elif address == 0xb9:
                        self._io_b9 = self.BusData & 0xFF
                    elif address == 0xba:
                        self._io_ba = self.BusData & 0xFF
                    elif address == 0xbb:
                        self._io_bb = self.BusData & 0xFF
                    elif address == 0xbc:
                        self._io_bc = self.BusData & 0xFF
                    elif address == 0xbd:
                        self._io_bd = self.BusData & 0xFF
                    elif address == 0xbe:
                        self._io_be = self.BusData & 0xFF
                    elif address == 0xbf:
                        self._io_bf = self.BusData & 0xFF
                    elif address == 0xc0:
                        self._io_c0 = self.BusData & 0xFF
                    elif address == 0xc1:
                        self._io_c1 = self.BusData & 0xFF
                    elif address == 0xc2:
                        self._io_c2 = self.BusData & 0xFF
                    elif address == 0xc3:
                        self._io_c3 = self.BusData & 0xFF
                    elif address == 0xc4:
                        self._io_c4 = self.BusData & 0xFF
                    elif address == 0xc5:
                        self._io_c5 = self.BusData & 0xFF
                    elif address == 0xc6:
                        self._io_c6 = self.BusData & 0xFF
                    elif address == 0xc7:
                        self._io_c7 = self.BusData & 0xFF
                    elif address == 0xc8:
                        self._io_c8 = self.BusData & 0xFF
                    elif address == 0xc9:
                        self._io_c9 = self.BusData & 0xFF
                    elif address == 0xca:
                        self._io_ca = self.BusData & 0xFF
                    elif address == 0xcb:
                        self._io_cb = self.BusData & 0xFF
                    elif address == 0xcc:
                        self._io_cc = self.BusData & 0xFF
                    elif address == 0xcd:
                        self._io_cd = self.BusData & 0xFF
                    elif address == 0xce:
                        self._io_ce = self.BusData & 0xFF
                    elif address == 0xcf:
                        self._io_cf = self.BusData & 0xFF
                    elif address == 0xd0:
                        self._io_d0 = self.BusData & 0xFF
                    elif address == 0xd1:
                        self._io_d1 = self.BusData & 0xFF
                    elif address == 0xd2:
                        self._io_d2 = self.BusData & 0xFF
                    elif address == 0xd3:
                        self._io_d3 = self.BusData & 0xFF
                    elif address == 0xd4:
                        self._io_d4 = self.BusData & 0xFF
                    elif address == 0xd5:
                        self._io_d5 = self.BusData & 0xFF
                    elif address == 0xd6:
                        self._io_d6 = self.BusData & 0xFF
                    elif address == 0xd7:
                        self._io_d7 = self.BusData & 0xFF
                    elif address == 0xd8:
                        self._io_d8 = self.BusData & 0xFF
                    elif address == 0xd9:
                        self._io_d9 = self.BusData & 0xFF
                    elif address == 0xda:
                        self._io_da = self.BusData & 0xFF
                    elif address == 0xdb:
                        self._io_db = self.BusData & 0xFF
                    elif address == 0xdc:
                        self._io_dc = self.BusData & 0xFF
                    elif address == 0xdd:
                        self._io_dd = self.BusData & 0xFF
                    elif address == 0xde:
                        self._io_de = self.BusData & 0xFF
                    elif address == 0xdf:
                        self._io_df = self.BusData & 0xFF
                    elif address == 0xe0:
                        self._io_e0 = self.BusData & 0xFF
                    elif address == 0xe1:
                        self._io_e1 = self.BusData & 0xFF
                    elif address == 0xe2:
                        self._io_e2 = self.BusData & 0xFF
                    elif address == 0xe3:
                        self._io_e3 = self.BusData & 0xFF
                    elif address == 0xe4:
                        self._io_e4 = self.BusData & 0xFF
                    elif address == 0xe5:
                        self._io_e5 = self.BusData & 0xFF
                    elif address == 0xe6:
                        self._io_e6 = self.BusData & 0xFF
                    elif address == 0xe7:
                        self._io_e7 = self.BusData & 0xFF
                    elif address == 0xe8:
                        self._io_e8 = self.BusData & 0xFF
                    elif address == 0xe9:
                        self._io_e9 = self.BusData & 0xFF
                    elif address == 0xea:
                        self._io_ea = self.BusData & 0xFF
                    elif address == 0xeb:
                        self._io_eb = self.BusData & 0xFF
                    elif address == 0xec:
                        self._io_ec = self.BusData & 0xFF
                    elif address == 0xed:
                        self._io_ed = self.BusData & 0xFF
                    elif address == 0xee:
                        self._io_ee = self.BusData & 0xFF
                    elif address == 0xef:
                        self._io_ef = self.BusData & 0xFF
                    elif address == 0xf0:
                        self._io_f0 = self.BusData & 0xFF
                    elif address == 0xf1:
                        self._io_f1 = self.BusData & 0xFF
                    elif address == 0xf2:
                        self._io_f2 = self.BusData & 0xFF
                    elif address == 0xf3:
                        self._io_f3 = self.BusData & 0xFF
                    elif address == 0xf4:
                        self._io_f4 = self.BusData & 0xFF
                    elif address == 0xf5:
                        self._io_f5 = self.BusData & 0xFF
                    elif address == 0xf6:
                        self._io_f6 = self.BusData & 0xFF
                    elif address == 0xf7:
                        self._io_f7 = self.BusData & 0xFF
                    elif address == 0xf8:
                        self._io_f8 = self.BusData & 0xFF
                    elif address == 0xf9:
                        self._io_f9 = self.BusData & 0xFF
                    elif address == 0xfa:
                        self._io_fa = self.BusData & 0xFF
                    elif address == 0xfb:
                        self._io_fb = self.BusData & 0xFF
                    elif address == 0xfc:
                        self._io_fc = self.BusData & 0xFF
                    elif address == 0xfd:
                        self._io_fd = self.BusData & 0xFF
                    elif address == 0xfe:
                        self._io_fe = self.BusData & 0xFF
                    elif address == 0xff:
                        self._io_ff = self.BusData & 0xFF
                    self.memory_write.prepare(0)
                    resp_val = 1

                else:
                    # Normal SRAM Write (also used by any Bus_Passthrough_Ranges
                    # address above, which is NOT real SRAM -- it routes to
                    # whatever peripheral a testbench has mapped there on the
                    # real external data bus).
                    self.memory_writedata.prepare(self.BusData)
                    self.memory_write.prepare(1)
                    resp_val = self.memory_resp.get()

                self.memory_read.prepare(0)

            elif rw == 2: # READ OPERATION

                # Intercept SP Reads
                if address == SP_L_ADDR:
                    self.BusData = self.SPL
                    self.memory_read.prepare(0) # Bypass SRAM read
                    resp_val = 1

                elif address == SP_H_ADDR:
                    self.BusData = self.SPH
                    self.memory_read.prepare(0) # Bypass SRAM read
                    resp_val = 1

                elif address == SREG_ADDR:
                    self.BusData = self.SREG_ReadValue.get()
                    resp_val = 1

                elif address == SPMCR_ADDR:
                    self.BusData = self.SPMCR
                    self.memory_read.prepare(0)  # Bypass the timer peripheral
                    resp_val = 1

                elif ((address >= 0x0020) and (address < 0x0100)) and (not is_passthrough):
                    # See matching WRITE branch above. Unwritten registers
                    # default to 0 rather than raising, since real hardware
                    # reset state for these is 0 anyway.
                    #
                    # Address-decoded dispatch into the io_scratch register
                    # bank -- inlined replacement for the old
                    # `self.io_scratch.get(address, 0)` dict read.
                    if address == 0x20:
                        self.BusData = self._io_20
                    elif address == 0x21:
                        self.BusData = self._io_21
                    elif address == 0x22:
                        self.BusData = self._io_22
                    elif address == 0x23:
                        self.BusData = self._io_23
                    elif address == 0x24:
                        self.BusData = self._io_24
                    elif address == 0x25:
                        self.BusData = self._io_25
                    elif address == 0x26:
                        self.BusData = self._io_26
                    elif address == 0x27:
                        self.BusData = self._io_27
                    elif address == 0x28:
                        self.BusData = self._io_28
                    elif address == 0x29:
                        self.BusData = self._io_29
                    elif address == 0x2a:
                        self.BusData = self._io_2a
                    elif address == 0x2b:
                        self.BusData = self._io_2b
                    elif address == 0x2c:
                        self.BusData = self._io_2c
                    elif address == 0x2d:
                        self.BusData = self._io_2d
                    elif address == 0x2e:
                        self.BusData = self._io_2e
                    elif address == 0x2f:
                        self.BusData = self._io_2f
                    elif address == 0x30:
                        self.BusData = self._io_30
                    elif address == 0x31:
                        self.BusData = self._io_31
                    elif address == 0x32:
                        self.BusData = self._io_32
                    elif address == 0x33:
                        self.BusData = self._io_33
                    elif address == 0x34:
                        self.BusData = self._io_34
                    elif address == 0x35:
                        self.BusData = self._io_35
                    elif address == 0x36:
                        self.BusData = self._io_36
                    elif address == 0x37:
                        self.BusData = self._io_37
                    elif address == 0x38:
                        self.BusData = self._io_38
                    elif address == 0x39:
                        self.BusData = self._io_39
                    elif address == 0x3a:
                        self.BusData = self._io_3a
                    elif address == 0x3b:
                        self.BusData = self._io_3b
                    elif address == 0x3c:
                        self.BusData = self._io_3c
                    elif address == 0x3d:
                        self.BusData = self._io_3d
                    elif address == 0x3e:
                        self.BusData = self._io_3e
                    elif address == 0x3f:
                        self.BusData = self._io_3f
                    elif address == 0x40:
                        self.BusData = self._io_40
                    elif address == 0x41:
                        self.BusData = self._io_41
                    elif address == 0x42:
                        self.BusData = self._io_42
                    elif address == 0x43:
                        self.BusData = self._io_43
                    elif address == 0x44:
                        self.BusData = self._io_44
                    elif address == 0x45:
                        self.BusData = self._io_45
                    elif address == 0x46:
                        self.BusData = self._io_46
                    elif address == 0x47:
                        self.BusData = self._io_47
                    elif address == 0x48:
                        self.BusData = self._io_48
                    elif address == 0x49:
                        self.BusData = self._io_49
                    elif address == 0x4a:
                        self.BusData = self._io_4a
                    elif address == 0x4b:
                        self.BusData = self._io_4b
                    elif address == 0x4c:
                        self.BusData = self._io_4c
                    elif address == 0x4d:
                        self.BusData = self._io_4d
                    elif address == 0x4e:
                        self.BusData = self._io_4e
                    elif address == 0x4f:
                        self.BusData = self._io_4f
                    elif address == 0x50:
                        self.BusData = self._io_50
                    elif address == 0x51:
                        self.BusData = self._io_51
                    elif address == 0x52:
                        self.BusData = self._io_52
                    elif address == 0x53:
                        self.BusData = self._io_53
                    elif address == 0x54:
                        self.BusData = self._io_54
                    elif address == 0x55:
                        self.BusData = self._io_55
                    elif address == 0x56:
                        self.BusData = self._io_56
                    elif address == 0x57:
                        self.BusData = self._io_57
                    elif address == 0x58:
                        self.BusData = self._io_58
                    elif address == 0x59:
                        self.BusData = self._io_59
                    elif address == 0x5a:
                        self.BusData = self._io_5a
                    elif address == 0x5b:
                        self.BusData = self._io_5b
                    elif address == 0x5c:
                        self.BusData = self._io_5c
                    elif address == 0x5d:
                        self.BusData = self._io_5d
                    elif address == 0x5e:
                        self.BusData = self._io_5e
                    elif address == 0x5f:
                        self.BusData = self._io_5f
                    elif address == 0x60:
                        self.BusData = self._io_60
                    elif address == 0x61:
                        self.BusData = self._io_61
                    elif address == 0x62:
                        self.BusData = self._io_62
                    elif address == 0x63:
                        self.BusData = self._io_63
                    elif address == 0x64:
                        self.BusData = self._io_64
                    elif address == 0x65:
                        self.BusData = self._io_65
                    elif address == 0x66:
                        self.BusData = self._io_66
                    elif address == 0x67:
                        self.BusData = self._io_67
                    elif address == 0x68:
                        self.BusData = self._io_68
                    elif address == 0x69:
                        self.BusData = self._io_69
                    elif address == 0x6a:
                        self.BusData = self._io_6a
                    elif address == 0x6b:
                        self.BusData = self._io_6b
                    elif address == 0x6c:
                        self.BusData = self._io_6c
                    elif address == 0x6d:
                        self.BusData = self._io_6d
                    elif address == 0x6e:
                        self.BusData = self._io_6e
                    elif address == 0x6f:
                        self.BusData = self._io_6f
                    elif address == 0x70:
                        self.BusData = self._io_70
                    elif address == 0x71:
                        self.BusData = self._io_71
                    elif address == 0x72:
                        self.BusData = self._io_72
                    elif address == 0x73:
                        self.BusData = self._io_73
                    elif address == 0x74:
                        self.BusData = self._io_74
                    elif address == 0x75:
                        self.BusData = self._io_75
                    elif address == 0x76:
                        self.BusData = self._io_76
                    elif address == 0x77:
                        self.BusData = self._io_77
                    elif address == 0x78:
                        self.BusData = self._io_78
                    elif address == 0x79:
                        self.BusData = self._io_79
                    elif address == 0x7a:
                        self.BusData = self._io_7a
                    elif address == 0x7b:
                        self.BusData = self._io_7b
                    elif address == 0x7c:
                        self.BusData = self._io_7c
                    elif address == 0x7d:
                        self.BusData = self._io_7d
                    elif address == 0x7e:
                        self.BusData = self._io_7e
                    elif address == 0x7f:
                        self.BusData = self._io_7f
                    elif address == 0x80:
                        self.BusData = self._io_80
                    elif address == 0x81:
                        self.BusData = self._io_81
                    elif address == 0x82:
                        self.BusData = self._io_82
                    elif address == 0x83:
                        self.BusData = self._io_83
                    elif address == 0x84:
                        self.BusData = self._io_84
                    elif address == 0x85:
                        self.BusData = self._io_85
                    elif address == 0x86:
                        self.BusData = self._io_86
                    elif address == 0x87:
                        self.BusData = self._io_87
                    elif address == 0x88:
                        self.BusData = self._io_88
                    elif address == 0x89:
                        self.BusData = self._io_89
                    elif address == 0x8a:
                        self.BusData = self._io_8a
                    elif address == 0x8b:
                        self.BusData = self._io_8b
                    elif address == 0x8c:
                        self.BusData = self._io_8c
                    elif address == 0x8d:
                        self.BusData = self._io_8d
                    elif address == 0x8e:
                        self.BusData = self._io_8e
                    elif address == 0x8f:
                        self.BusData = self._io_8f
                    elif address == 0x90:
                        self.BusData = self._io_90
                    elif address == 0x91:
                        self.BusData = self._io_91
                    elif address == 0x92:
                        self.BusData = self._io_92
                    elif address == 0x93:
                        self.BusData = self._io_93
                    elif address == 0x94:
                        self.BusData = self._io_94
                    elif address == 0x95:
                        self.BusData = self._io_95
                    elif address == 0x96:
                        self.BusData = self._io_96
                    elif address == 0x97:
                        self.BusData = self._io_97
                    elif address == 0x98:
                        self.BusData = self._io_98
                    elif address == 0x99:
                        self.BusData = self._io_99
                    elif address == 0x9a:
                        self.BusData = self._io_9a
                    elif address == 0x9b:
                        self.BusData = self._io_9b
                    elif address == 0x9c:
                        self.BusData = self._io_9c
                    elif address == 0x9d:
                        self.BusData = self._io_9d
                    elif address == 0x9e:
                        self.BusData = self._io_9e
                    elif address == 0x9f:
                        self.BusData = self._io_9f
                    elif address == 0xa0:
                        self.BusData = self._io_a0
                    elif address == 0xa1:
                        self.BusData = self._io_a1
                    elif address == 0xa2:
                        self.BusData = self._io_a2
                    elif address == 0xa3:
                        self.BusData = self._io_a3
                    elif address == 0xa4:
                        self.BusData = self._io_a4
                    elif address == 0xa5:
                        self.BusData = self._io_a5
                    elif address == 0xa6:
                        self.BusData = self._io_a6
                    elif address == 0xa7:
                        self.BusData = self._io_a7
                    elif address == 0xa8:
                        self.BusData = self._io_a8
                    elif address == 0xa9:
                        self.BusData = self._io_a9
                    elif address == 0xaa:
                        self.BusData = self._io_aa
                    elif address == 0xab:
                        self.BusData = self._io_ab
                    elif address == 0xac:
                        self.BusData = self._io_ac
                    elif address == 0xad:
                        self.BusData = self._io_ad
                    elif address == 0xae:
                        self.BusData = self._io_ae
                    elif address == 0xaf:
                        self.BusData = self._io_af
                    elif address == 0xb0:
                        self.BusData = self._io_b0
                    elif address == 0xb1:
                        self.BusData = self._io_b1
                    elif address == 0xb2:
                        self.BusData = self._io_b2
                    elif address == 0xb3:
                        self.BusData = self._io_b3
                    elif address == 0xb4:
                        self.BusData = self._io_b4
                    elif address == 0xb5:
                        self.BusData = self._io_b5
                    elif address == 0xb6:
                        self.BusData = self._io_b6
                    elif address == 0xb7:
                        self.BusData = self._io_b7
                    elif address == 0xb8:
                        self.BusData = self._io_b8
                    elif address == 0xb9:
                        self.BusData = self._io_b9
                    elif address == 0xba:
                        self.BusData = self._io_ba
                    elif address == 0xbb:
                        self.BusData = self._io_bb
                    elif address == 0xbc:
                        self.BusData = self._io_bc
                    elif address == 0xbd:
                        self.BusData = self._io_bd
                    elif address == 0xbe:
                        self.BusData = self._io_be
                    elif address == 0xbf:
                        self.BusData = self._io_bf
                    elif address == 0xc0:
                        self.BusData = self._io_c0
                    elif address == 0xc1:
                        self.BusData = self._io_c1
                    elif address == 0xc2:
                        self.BusData = self._io_c2
                    elif address == 0xc3:
                        self.BusData = self._io_c3
                    elif address == 0xc4:
                        self.BusData = self._io_c4
                    elif address == 0xc5:
                        self.BusData = self._io_c5
                    elif address == 0xc6:
                        self.BusData = self._io_c6
                    elif address == 0xc7:
                        self.BusData = self._io_c7
                    elif address == 0xc8:
                        self.BusData = self._io_c8
                    elif address == 0xc9:
                        self.BusData = self._io_c9
                    elif address == 0xca:
                        self.BusData = self._io_ca
                    elif address == 0xcb:
                        self.BusData = self._io_cb
                    elif address == 0xcc:
                        self.BusData = self._io_cc
                    elif address == 0xcd:
                        self.BusData = self._io_cd
                    elif address == 0xce:
                        self.BusData = self._io_ce
                    elif address == 0xcf:
                        self.BusData = self._io_cf
                    elif address == 0xd0:
                        self.BusData = self._io_d0
                    elif address == 0xd1:
                        self.BusData = self._io_d1
                    elif address == 0xd2:
                        self.BusData = self._io_d2
                    elif address == 0xd3:
                        self.BusData = self._io_d3
                    elif address == 0xd4:
                        self.BusData = self._io_d4
                    elif address == 0xd5:
                        self.BusData = self._io_d5
                    elif address == 0xd6:
                        self.BusData = self._io_d6
                    elif address == 0xd7:
                        self.BusData = self._io_d7
                    elif address == 0xd8:
                        self.BusData = self._io_d8
                    elif address == 0xd9:
                        self.BusData = self._io_d9
                    elif address == 0xda:
                        self.BusData = self._io_da
                    elif address == 0xdb:
                        self.BusData = self._io_db
                    elif address == 0xdc:
                        self.BusData = self._io_dc
                    elif address == 0xdd:
                        self.BusData = self._io_dd
                    elif address == 0xde:
                        self.BusData = self._io_de
                    elif address == 0xdf:
                        self.BusData = self._io_df
                    elif address == 0xe0:
                        self.BusData = self._io_e0
                    elif address == 0xe1:
                        self.BusData = self._io_e1
                    elif address == 0xe2:
                        self.BusData = self._io_e2
                    elif address == 0xe3:
                        self.BusData = self._io_e3
                    elif address == 0xe4:
                        self.BusData = self._io_e4
                    elif address == 0xe5:
                        self.BusData = self._io_e5
                    elif address == 0xe6:
                        self.BusData = self._io_e6
                    elif address == 0xe7:
                        self.BusData = self._io_e7
                    elif address == 0xe8:
                        self.BusData = self._io_e8
                    elif address == 0xe9:
                        self.BusData = self._io_e9
                    elif address == 0xea:
                        self.BusData = self._io_ea
                    elif address == 0xeb:
                        self.BusData = self._io_eb
                    elif address == 0xec:
                        self.BusData = self._io_ec
                    elif address == 0xed:
                        self.BusData = self._io_ed
                    elif address == 0xee:
                        self.BusData = self._io_ee
                    elif address == 0xef:
                        self.BusData = self._io_ef
                    elif address == 0xf0:
                        self.BusData = self._io_f0
                    elif address == 0xf1:
                        self.BusData = self._io_f1
                    elif address == 0xf2:
                        self.BusData = self._io_f2
                    elif address == 0xf3:
                        self.BusData = self._io_f3
                    elif address == 0xf4:
                        self.BusData = self._io_f4
                    elif address == 0xf5:
                        self.BusData = self._io_f5
                    elif address == 0xf6:
                        self.BusData = self._io_f6
                    elif address == 0xf7:
                        self.BusData = self._io_f7
                    elif address == 0xf8:
                        self.BusData = self._io_f8
                    elif address == 0xf9:
                        self.BusData = self._io_f9
                    elif address == 0xfa:
                        self.BusData = self._io_fa
                    elif address == 0xfb:
                        self.BusData = self._io_fb
                    elif address == 0xfc:
                        self.BusData = self._io_fc
                    elif address == 0xfd:
                        self.BusData = self._io_fd
                    elif address == 0xfe:
                        self.BusData = self._io_fe
                    elif address == 0xff:
                        self.BusData = self._io_ff
                    else:
                        self.BusData = 0
                    self.memory_read.prepare(0)
                    resp_val = 1

                else:
                    # Normal SRAM Read (also used by 0xFE/0xFF, routed to the
                    # external InterruptUnit peripheral -- see WRITE branch).
                    self.BusData = self.memory_readdata.get()
                    self.memory_read.prepare(1)
                    resp_val = self.memory_resp.get()

                # FIX (spurious "wire already prepared" warning spam): this
                # single line is the ONLY place any READ branch above should
                # deassert write -- every branch that also wants write=0
                # (SP_L/SP_H/SPMCR/io_scratch) just falls through to it.
                self.memory_write.prepare(0)

            else: # NO OPERATION
                self.memory_read.prepare(0)
                self.memory_write.prepare(0)
                resp_val = self.memory_resp.get()

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

                if load_sel == self.LOAD_XL:
                    self.XregL = data
                elif load_sel == self.LOAD_XH:
                    self.XregH = data
                elif load_sel == self.LOAD_YL:
                    self.YregL = data
                elif load_sel == self.LOAD_YH:
                    self.YregH = data
                elif load_sel == self.LOAD_ZL:
                    self.ZregL = data
                elif load_sel == self.LOAD_ZH:
                    self.ZregH = data
                elif load_sel == self.LOAD_SPL:
                    self.SPL = data
                elif load_sel == self.LOAD_SPH:
                    self.SPH = data
                elif load_sel == self.LOAD_RD_BUFFER:
                    self.RdBuffer = data
                elif load_sel == self.LOAD_R0_BUFFER:
                    self.R0Buffer = data
                elif load_sel == self.LOAD_R1_BUFFER:
                    self.R1Buffer = data

            # ----------------------------------------------
            # 4. Pointer update
            # ----------------------------------------------
            # Inlined from updatePointer()/getX()../setX().. -- see report
            # (no call inlining in the stock transpiler). pointer_name uses
            # the same integer encoding as section 1 above (0=NONE, 1=X,
            # 2=Y, 3=Z, 4=SP, 5=ROM); ROM (5) intentionally does nothing,
            # same as the original `if ptr_name is None or ptr_name ==
            # "ROM": return` guard.
            if (pointer_name == 1) or (pointer_name == 2) or (pointer_name == 3) or (pointer_name == 4):
                if incdec_mode != self.INC_NONE:
                    ptr_offset = 0
                    if (incdec_mode == self.INC_PRE_DEC) or (incdec_mode == self.INC_POST_DEC):
                        ptr_offset = -1
                    elif (incdec_mode == self.INC_PRE_INC) or (incdec_mode == self.INC_POST_INC):
                        ptr_offset = 1

                    if pointer_name == 1:
                        x_new = (((self.XregH << 8) | self.XregL) + ptr_offset)
                        self.XregL = x_new & 0xFF
                        self.XregH = (x_new >> 8) & 0xFF
                    elif pointer_name == 2:
                        y_new = (((self.YregH << 8) | self.YregL) + ptr_offset)
                        self.YregL = y_new & 0xFF
                        self.YregH = (y_new >> 8) & 0xFF
                    elif pointer_name == 3:
                        z_new = (((self.ZregH << 8) | self.ZregL) + ptr_offset)
                        self.ZregL = z_new & 0xFF
                        self.ZregH = (z_new >> 8) & 0xFF
                    elif pointer_name == 4:
                        sp_new = (((self.SPH << 8) | self.SPL) + ptr_offset)
                        self.SPL = sp_new & 0xFF
                        self.SPH = (sp_new >> 8) & 0xFF

            # --- SREG LOGIC ---
            # Resolve this cycle's write-mask/write-value request for the 8
            # flag registers in Datapath. Priority matches the original
            # self.SREG ordering exactly: a full-byte SREG_ADDR bus write is
            # applied first, then the ALU's eSREG-masked update is layered on
            # top and wins on any overlapping bits. (The I flag's own
            # InterruptFSM override is NOT resolved here -- it bypasses MIH
            # entirely via a dedicated mux in front of SREG_I in Datapath.)
            alu_commit = self.ALU_Commit.get()
            if alu_commit:
                eSREG_mask = self.eSREG.get()
            else:
                eSREG_mask = 0

            if sreg_bus_write_pending:
                sreg_mask_from_bus = 0xFF
            else:
                sreg_mask_from_bus = 0
            write_mask = eSREG_mask | sreg_mask_from_bus
            write_value = (self.SREG_IN.get() & eSREG_mask)
            if sreg_bus_write_pending:
                write_value |= (sreg_bus_write_value & ~eSREG_mask)

            self.SREG_WriteValue.prepare(write_value & 0xFF)
            self.SREG_WriteMask.prepare(write_mask & 0xFF)

            self.R0_BUFFER_out.prepare(self.R0Buffer)
            self.R1_BUFFER_out.prepare(self.R1Buffer)
