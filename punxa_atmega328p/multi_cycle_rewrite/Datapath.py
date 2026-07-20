import py4hw

from .RomHandler import *
from .Instruction_decoder import *
from .ALU import *
from .MemoryInterfaceHandler import *

"""
=============================================================================
Datapath
=============================================================================
Everything that stores state, plus the units that compute what goes into
that state:

    RomHandler            -- drives PC and IR
    Instruction_decoder    -- reads IR, feeds ALU/MIH/RomHandler internally
    ALU_STRUC               -- reads AL/AH/BL/BH/IO, drives SREG write bus
    MemoryInterfaceHandler -- drives MAR (shadow) and SREG write bus, owns
                              X/Y/Z/SP pointer registers internally

    Registers (py4hw.Reg): PC, IR, MAR, AL, AH, BL, BH, IO,
                            SREG_C/Z/N/V/S/H/T/I

ControlBox is NOT inside this component -- it's Datapath's sole peer at the
multicycleProcessor top level, talking to Datapath purely through control
signals in / status signals out (see the D_* port list below).
=============================================================================
"""

class Datapath(py4hw.Logic):
    def __init__(self, parent, name,
                 # ---- External passthrough (same as multicycleProcessor's
                 #      own external ports) ----
                 reset, ins_mem, memory, reset_address, Interrupt_Enable,
                 Bus_Passthrough_Ranges=None,

                 # ---- Flash programming interface passthrough (see
                 #      ROM_FLASHING_DESIGN.md) -- straight through to
                 #      RomHandler, same pattern as `reset` above ----
                 PROG_MOSI=None, PROG_SCK=None, PROG_MISO=None,

                 # ==============================================================
                 # Boundary to ControlBox
                 # ==============================================================
                 # ---- Datapath -> ControlBox (status / handshakes) ----
                 D_Resp=None, D_Branch=None, D_Skip=None, D_Instruction=None,
                 D_Instruction_fetched=None, D_Instruction_decoded=None,
                 D_Executed_Jump=None, D_Address_fetched=None, D_SPM_Done=None,

                 # ---- ControlBox -> Datapath (control signals) ----
                 D_LoadSelectMux=None, D_LoadingMux=None, D_Input_Select=None,
                 D_WE_MEMORY=None, D_Read_Write=None, D_mem_instr=None, D_IncDec=None,
                 D_InputSelect=None, D_WE_Buffer=None,
                 D_Load_Z=None, D_Load_K=None, D_K_Select=None, D_Load_Jump=None,
                 D_relative_Absolute=None, D_Load_Byte=None,
                 D_Fetch_next_instruction=None, D_Fetch_Address=None,
                 D_WB_Addr=None, D_JumpWidth=None,
                 D_LOAD_PCL=None, D_LOAD_PCH=None,
                 D_LPM_req=None, D_SPM_req=None,
                 D_I_Force_WE=None, D_I_Force_Value=None, D_ALU_Commit=None,
                 ):
        super().__init__(parent, name)

        self.reset = self.addIn('reset', reset)
        self.ins_mem = self.addInterfaceSource('ins_mem', ins_mem)
        self.memory = self.addInterfaceSource('memory', memory)
        self.Interrupt_Enable = self.addOut('Interrupt_Enable', Interrupt_Enable)

        self.PROG_MOSI = self.addIn('PROG_MOSI', PROG_MOSI)
        self.PROG_SCK = self.addIn('PROG_SCK', PROG_SCK)
        self.PROG_MISO = self.addOut('PROG_MISO', PROG_MISO)
        self.reset_address = reset_address

        # ---- Boundary pins (mirrored for hierarchy/visualization; the
        #      actual driving happens in the leaf sub-components/registers
        #      wired to these exact same wire objects below) ----
        self.D_Resp = self.addOut('D_Resp', D_Resp)
        self.D_Branch = self.addOut('D_Branch', D_Branch)
        self.D_Skip = self.addOut('D_Skip', D_Skip)
        self.D_Instruction = self.addOut('D_Instruction', D_Instruction)
        self.D_Instruction_fetched = self.addOut('D_Instruction_fetched', D_Instruction_fetched)
        self.D_Instruction_decoded = self.addOut('D_Instruction_decoded', D_Instruction_decoded)
        self.D_Executed_Jump = self.addOut('D_Executed_Jump', D_Executed_Jump)
        self.D_Address_fetched = self.addOut('D_Address_fetched', D_Address_fetched)
        self.D_SPM_Done = self.addOut('D_SPM_Done', D_SPM_Done)

        self.D_LoadSelectMux = self.addIn('D_LoadSelectMux', D_LoadSelectMux)
        self.D_LoadingMux = self.addIn('D_LoadingMux', D_LoadingMux)
        self.D_Input_Select = self.addIn('D_Input_Select', D_Input_Select)
        self.D_WE_MEMORY = self.addIn('D_WE_MEMORY', D_WE_MEMORY)
        self.D_Read_Write = self.addIn('D_Read_Write', D_Read_Write)
        self.D_mem_instr = self.addIn('D_mem_instr', D_mem_instr)
        self.D_IncDec = self.addIn('D_IncDec', D_IncDec)
        self.D_InputSelect = self.addIn('D_InputSelect', D_InputSelect)
        self.D_WE_Buffer = self.addIn('D_WE_Buffer', D_WE_Buffer)
        self.D_Load_Z = self.addIn('D_Load_Z', D_Load_Z)
        self.D_Load_K = self.addIn('D_Load_K', D_Load_K)
        self.D_K_Select = self.addIn('D_K_Select', D_K_Select)
        self.D_Load_Jump = self.addIn('D_Load_Jump', D_Load_Jump)
        self.D_relative_Absolute = self.addIn('D_relative_Absolute', D_relative_Absolute)
        self.D_Load_Byte = self.addIn('D_Load_Byte', D_Load_Byte)
        self.D_Fetch_next_instruction = self.addIn('D_Fetch_next_instruction', D_Fetch_next_instruction)
        self.D_Fetch_Address = self.addIn('D_Fetch_Address', D_Fetch_Address)
        self.D_WB_Addr = self.addIn('D_WB_Addr', D_WB_Addr)
        self.D_JumpWidth = self.addIn('D_JumpWidth', D_JumpWidth)
        self.D_LOAD_PCL = self.addIn('D_LOAD_PCL', D_LOAD_PCL)
        self.D_LOAD_PCH = self.addIn('D_LOAD_PCH', D_LOAD_PCH)
        self.D_LPM_req = self.addIn('D_LPM_req', D_LPM_req)
        self.D_SPM_req = self.addIn('D_SPM_req', D_SPM_req)
        self.D_I_Force_WE = self.addIn('D_I_Force_WE', D_I_Force_WE)
        self.D_I_Force_Value = self.addIn('D_I_Force_Value', D_I_Force_Value)
        self.D_ALU_Commit = self.addIn('D_ALU_Commit', D_ALU_Commit)

        # ==============================================================
        # Internal wires (RomHandler <-> Instruction_decoder <-> ALU <->
        # MemoryInterfaceHandler -- everything that used to be top-level
        # wiring inside multicycleProcessor.py is now fully internal here)
        # ==============================================================
        W_Instruction_RH_ID   = self.wire('W_Instruction_RH_ID', 16)
        W_CODE_ID              = self.wire('W_CODE_ID', 16)
        W_RD_ID_MIH             = self.wire('W_RD_ID_MIH', 5)
        W_RR_ID_MIH             = self.wire('W_RR_ID_MIH', 5)
        W_K8_ID                = self.wire('W_K8_ID', 8)
        W_K6_ID                = self.wire('W_K6_ID', 6)
        W_K4_ID                = self.wire('W_K4_ID', 4)
        W_k7_ID_RH              = self.wire('W_k7_ID_RH', 7)
        W_k12_ID_RH             = self.wire('W_k12_ID_RH', 12)
        W_k7_22_ID_RH           = self.wire('W_k7_22_ID_RH', 7)
        W_b_ID_ALU              = self.wire('W_b_ID_ALU', 3)
        W_s_ID                  = self.wire('W_s_ID', 3)
        W_A5_ID_MIH              = self.wire('W_A5_ID_MIH', 5)
        W_A6_ID_MIH              = self.wire('W_A6_ID_MIH', 6)
        W_q6_ID_MIH              = self.wire('W_q6_ID_MIH', 6)

        W_OUTPUTByte0_ALU_MIH   = self.wire('W_OUTPUTByte0_ALU_MIH', 8)
        W_OUTPUTByte1_ALU_MIH   = self.wire('W_OUTPUTByte1_ALU_MIH', 8)
        W_SREG_ALU_VAL          = self.wire('W_SREG_ALU_VAL', 8)
        W_eSREG_ALU_VAL         = self.wire('W_eSREG_ALU_VAL', 8)

        W_DataInput_MIH_REGS    = self.wire('W_DataInput_MIH_REGS', 8)

        W_Rom_address_RH_MIH    = self.wire('W_Rom_address_RH_MIH', 16)
        W_Rom_value_RH_MIH      = self.wire('W_Rom_value_RH_MIH', 16)
        w_address_ZL_MIH_RH     = self.wire('w_address_ZL_MIH_RH', 8)
        w_address_ZH_MIH_RH     = self.wire('w_address_ZH_MIH_RH', 8)
        W_PCL_LOAD_VAL_CB_RH    = self.wire('W_PCL_LOAD_VAL_CB_RH', 8)
        W_PCH_LOAD_VAL_CB_RH    = self.wire('W_PCH_LOAD_VAL_CB_RH', 8)
        W_WriteVal_RH_MIH       = self.wire('W_WriteVal_RH_MIH', 8)
        W_ReadVal_RH_MIH        = self.wire('W_ReadVal_RH_MIH', 8)
        W_R0_BUFFER_IN_MIH_RH   = self.wire('W_R0_BUFFER_IN_MIH_RH', 8)
        W_R1_BUFFER_IN_MIH_RH   = self.wire('W_R1_BUFFER_IN_MIH_RH', 8)
        W_SPM_Done_RH           = self.wire('W_SPM_Done_RH', 1)

        # ---- New register-drive wires ----
        W_PC_ValueOut = self.wire('W_PC_ValueOut', 16)
        W_PC_Load    = self.wire('W_PC_Load', 1)
        W_PC_Q       = self.wire('W_PC_Q', 16)
        W_PCL_VAL_IN = self.wire('W_PCL_VAL_IN', 8)
        W_PCH_VAL_IN = self.wire('W_PCH_VAL_IN', 8)

        W_IR_Q       = self.wire('W_IR_Q', 16)

        W_MAR_ValueOut = self.wire('W_MAR_ValueOut', 16)
        W_MAR_Q        = self.wire('W_MAR_Q', 16)
        W_Const1       = self.wire('W_Const1', 1)

        W_AL_Q, W_AH_Q, W_BL_Q, W_BH_Q, W_IO_Q = (
            self.wire('W_AL_Q', 8), self.wire('W_AH_Q', 8), self.wire('W_BL_Q', 8),
            self.wire('W_BH_Q', 8), self.wire('W_IO_Q', 8),
        )
        W_en_AL, W_en_AH, W_en_BL, W_en_BH, W_en_IO = (
            self.wire('W_en_AL', 1), self.wire('W_en_AH', 1), self.wire('W_en_BL', 1),
            self.wire('W_en_BH', 1), self.wire('W_en_IO', 1),
        )
        W_BL_d = self.wire('W_BL_d', 8)

        # ---- SREG write bus (from MIH) and per-flag drive wires ----
        W_SREG_WriteValue = self.wire('W_SREG_WriteValue', 8)
        W_SREG_WriteMask  = self.wire('W_SREG_WriteMask', 8)
        W_SREG_ReadValue  = self.wire('W_SREG_ReadValue', 8)

        # One 1-bit d/enable pair per flag, bit position matches standard
        # AVR SREG ordering (I=7,T=6,H=5,S=4,V=3,N=2,Z=1,C=0 -- see
        # MemoryInterfaceHandler's docstring / ALU.py).
        flag_bits = {'C': 0, 'Z': 1, 'N': 2, 'V': 3, 'S': 4, 'H': 5, 'T': 6, 'I': 7}
        w_flag_d = {'I': self.wire('W_SREG_I_d', 1)}
        w_flag_en = {'I': self.wire('W_SREG_I_en', 1)}
        w_flag_q = {f: (self.Interrupt_Enable if f == 'I' else self.wire(f'W_SREG_{f}_q', 1))
                    for f in flag_bits}
        w_mask_bit = {f: self.wire(f'W_SREG_{f}_maskbit', 1) for f in flag_bits}
        w_value_bit = {f: self.wire(f'W_SREG_{f}_valuebit', 1) for f in flag_bits}

        # ==============================================================
        # Sub-components
        # ==============================================================
        RomHandler(self, 'RomHandler',
            RH_mem=ins_mem,
            RH_instructionOut=W_Instruction_RH_ID,
            RH_Address_Out=W_Rom_address_RH_MIH,
            RH_Value_Out=W_Rom_value_RH_MIH,
            RH_PC_ValIn=W_PC_Q,
            RH_PC_ValueOut=W_PC_ValueOut,
            RH_PC_Load=W_PC_Load,
            RH_Instruction_fetched=self.D_Instruction_fetched,
            RH_Executed_Jump=self.D_Executed_Jump,
            RH_Load_Z=self.D_Load_Z,
            RH_address_ZL=w_address_ZL_MIH_RH,
            RH_address_ZH=w_address_ZH_MIH_RH,
            RH_Load_K=self.D_Load_K,
            RH_K_select=self.D_K_Select,
            RH_K7=W_k7_ID_RH,
            RH_K12=W_k12_ID_RH,
            RH_K7_22=W_k7_22_ID_RH,
            RH_Load_Jump=self.D_Load_Jump,
            RH_relative_Absolute=self.D_relative_Absolute,
            RH_WriteVal=W_WriteVal_RH_MIH,
            RH_ReadVal=W_ReadVal_RH_MIH,
            RH_SPM_req=self.D_SPM_req,
            RH_LPM_req=self.D_LPM_req,
            RH_R0_BUFFER_IN=W_R0_BUFFER_IN_MIH_RH,
            RH_R1_BUFFER_IN=W_R1_BUFFER_IN_MIH_RH,
            RH_SPM_Done=self.D_SPM_Done,
            RH_PCL_LOAD_VAL=W_PCL_LOAD_VAL_CB_RH,
            RH_PCH_LOAD_VAL=W_PCH_LOAD_VAL_CB_RH,
            RH_Fetch_next_instruction=self.D_Fetch_next_instruction,
            RH_JumpWidth=self.D_JumpWidth,
            RH_Load_PCL=self.D_LOAD_PCL,
            RH_Load_PCH=self.D_LOAD_PCH,
            RH_fetch_address=self.D_Fetch_Address,
            RH_Address_fetched=self.D_Address_fetched,
            RH_Load_Byte=self.D_Load_Byte,
            RH_PROG_MOSI=self.PROG_MOSI,
            RH_PROG_SCK=self.PROG_SCK,
            RH_PROG_MISO=self.PROG_MISO,
            RH_default_reset_address=self.reset_address,
            RH_reset=self.reset,
        )

        Instruction_decoder(self, 'InstructionDecoder',
            ID_Instruction=W_IR_Q,
            ID_Instruction_fetched=self.D_Instruction_fetched,
            ID_InstructionCode=self.D_Instruction,
            ID_Rd=W_RD_ID_MIH,
            ID_Rr=W_RR_ID_MIH,
            ID_K8=W_K8_ID,
            ID_k12=W_k12_ID_RH,
            ID_K6=W_K6_ID,
            ID_K4=W_K4_ID,
            ID_k16=W_k12_ID_RH,
            ID_k7=W_k7_ID_RH,
            ID_k7_22=W_k7_22_ID_RH,
            ID_b=W_b_ID_ALU,
            ID_s=W_s_ID,
            ID_A5=W_A5_ID_MIH,
            ID_A6=W_A6_ID_MIH,
            ID_q=W_q6_ID_MIH,
            ID_Instruction_decoded=self.D_Instruction_decoded,
            ID_Reset=self.reset,
        )

        ALU_STRUC(
            self, 'ALU',
            A0=W_AL_Q, A1=W_AH_Q, B0=W_BL_Q, B1=W_BH_Q,
            op=self.D_Instruction,
            SREG_STATE=W_SREG_ReadValue,
            BitPos=W_b_ID_ALU,
            IOreg=W_IO_Q,
            R0=W_OUTPUTByte0_ALU_MIH,
            R1=W_OUTPUTByte1_ALU_MIH,
            SREG_VAL=W_SREG_ALU_VAL,
            eSREG_VAL=W_eSREG_ALU_VAL,
            BRANCH=self.D_Branch,
            SKIP=self.D_Skip,
            reset=self.reset,
        )

        MemoryInterfaceHandler(
            self, 'MemoryInterfaceHandler',
            reset=self.reset,
            ALU_Commit=self.D_ALU_Commit,
            WE=self.D_WE_MEMORY,
            LoadSelectMux=self.D_LoadSelectMux,
            LoadingMux=self.D_LoadingMux,
            IncDec=self.D_IncDec,
            RomAddressValue=W_Rom_value_RH_MIH,
            ReadWrite=self.D_Read_Write,
            InputSelectMemory=self.D_Input_Select,
            Mem_instruction=self.D_mem_instr,
            RomAddress=W_Rom_address_RH_MIH,
            ResL=W_OUTPUTByte0_ALU_MIH,
            ResH=W_OUTPUTByte1_ALU_MIH,
            K_val_Input=W_K8_ID,
            PCL_VAL_IN=W_PCL_VAL_IN,
            PCH_VAL_IN=W_PCH_VAL_IN,
            PC_Offset=self.D_JumpWidth,
            Rd=W_RD_ID_MIH,
            Rr=W_RR_ID_MIH,
            WbAddr=self.D_WB_Addr,
            memory=memory,
            RegisterOut=W_DataInput_MIH_REGS,
            Resp=self.D_Resp,
            address_ZL=w_address_ZL_MIH_RH,
            address_ZH=w_address_ZH_MIH_RH,
            Q=W_q6_ID_MIH,
            A_5bit=W_A5_ID_MIH,
            A_6bit=W_A6_ID_MIH,
            MIH_PCL_LOAD_VAL=W_PCL_LOAD_VAL_CB_RH,
            MIH_PCH_LOAD_VAL=W_PCH_LOAD_VAL_CB_RH,
            SREG_In=W_SREG_ALU_VAL,
            eSREG_In=W_eSREG_ALU_VAL,
            SREG_ReadValue=W_SREG_ReadValue,
            SREG_WriteValue=W_SREG_WriteValue,
            SREG_WriteMask=W_SREG_WriteMask,
            MAR_ValueOut=W_MAR_ValueOut,
            R0_BUFFER_OUT=W_R0_BUFFER_IN_MIH_RH,
            R1_BUFFER_OUT=W_R1_BUFFER_IN_MIH_RH,
            ROM_VAL_IN=W_WriteVal_RH_MIH,
            ROM_VAL_OUT=W_ReadVal_RH_MIH,
            Bus_Passthrough_Ranges=Bus_Passthrough_Ranges,
        )

        # (w_mem_incdec_MIH/w_mem_instr_MIH removed -- D_IncDec/D_mem_instr
        # are wired directly into MIH above; no indirection needed.)

        # ==============================================================
        # Registers
        # ==============================================================

        # ---- PC ----
        py4hw.Reg(self, 'PC', d=W_PC_ValueOut, q=W_PC_Q,
                  enable=W_PC_Load, reset=self.reset, reset_value=reset_address)
        py4hw.Range(self, 'PC_split_L', W_PC_Q, 7, 0, W_PCL_VAL_IN)
        py4hw.Range(self, 'PC_split_H', W_PC_Q, 15, 8, W_PCH_VAL_IN)

        # ---- IR ---- (d = RomHandler's fetched word, enable = fetch pulse,
        #     exactly the same value/timing RomHandler always exposed via
        #     instructionOut/Instruction_fetched -- no new RomHandler ports
        #     needed for this one)
        py4hw.Reg(self, 'IR', d=W_Instruction_RH_ID, q=W_IR_Q,
                  enable=self.D_Instruction_fetched, reset=self.reset, reset_value=0)

        # ---- MAR (bus address register, shadow of MIH's live address) ----
        py4hw.Constant(self, 'const1', 1, W_Const1)
        py4hw.Reg(self, 'MAR', d=W_MAR_ValueOut, q=W_MAR_Q,
                  enable=W_Const1, reset=self.reset, reset_value=0)

        # ---- AL/AH/BL/BH/IO (replaces OperandBuffer) ----
        # WE_Buffer one-hot decode via Eq-against-Constant, matching the
        # Eq(a, b, r) + Constant(value, r) pattern already used throughout
        # this codebase (see HandleC_STRUC/HandleV_STRUC/HandleZ_STRUC/
        # LU_STRUC) rather than an EqualConstant convenience primitive.
        W_const_1 = self.wire('W_const_1', 4)
        W_const_2 = self.wire('W_const_2', 4)
        W_const_3 = self.wire('W_const_3', 4)
        W_const_4 = self.wire('W_const_4', 4)
        W_const_5 = self.wire('W_const_5', 4)
        py4hw.Constant(self, 'const_1', 1, W_const_1)
        py4hw.Constant(self, 'const_2', 2, W_const_2)
        py4hw.Constant(self, 'const_3', 3, W_const_3)
        py4hw.Constant(self, 'const_4', 4, W_const_4)
        py4hw.Constant(self, 'const_5', 5, W_const_5)
        py4hw.Equal(self, 'eq_AL', self.D_WE_Buffer, W_const_1, W_en_AL)
        py4hw.Equal(self, 'eq_AH', self.D_WE_Buffer, W_const_2, W_en_AH)
        py4hw.Equal(self, 'eq_BL', self.D_WE_Buffer, W_const_3, W_en_BL)
        py4hw.Equal(self, 'eq_BH', self.D_WE_Buffer, W_const_4, W_en_BH)
        py4hw.Equal(self, 'eq_IO', self.D_WE_Buffer, W_const_5, W_en_IO)

        # BL loads from the data bus when InputSelect==1, else from the
        # decoded K8 constant -- same as OperandBuffer's original
        # `valueRr0 = DATA if InputSelectBuffer==1 else K`.
        py4hw.Mux(self, 'mux_BL_d', sel=self.D_InputSelect, ins=[W_K8_ID, W_DataInput_MIH_REGS], r=W_BL_d)

        py4hw.Reg(self, 'AL', d=W_DataInput_MIH_REGS, q=W_AL_Q, enable=W_en_AL, reset=self.reset, reset_value=0)
        py4hw.Reg(self, 'AH', d=W_DataInput_MIH_REGS, q=W_AH_Q, enable=W_en_AH, reset=self.reset, reset_value=0)
        py4hw.Reg(self, 'BL', d=W_BL_d,               q=W_BL_Q, enable=W_en_BL, reset=self.reset, reset_value=0)
        py4hw.Reg(self, 'BH', d=W_DataInput_MIH_REGS, q=W_BH_Q, enable=W_en_BH, reset=self.reset, reset_value=0)
        py4hw.Reg(self, 'IO', d=W_DataInput_MIH_REGS, q=W_IO_Q, enable=W_en_IO, reset=self.reset, reset_value=0)

        # ---- SREG: 8 discrete 1-bit flag registers ----
        for f, bit in flag_bits.items():
            py4hw.Range(self, f'SREG_{f}_maskbit', W_SREG_WriteMask, bit, bit, w_mask_bit[f])
            py4hw.Range(self, f'SREG_{f}_valuebit', W_SREG_WriteValue, bit, bit, w_value_bit[f])

            if f == 'I':
                # InterruptFSM's override bypasses MIH entirely and drives
                # this register directly via its own mux -- I_Force_WE=1
                # always wins over whatever MIH/ALU proposed this cycle
                # (matches the original priority: InterruptFSM's write
                # applied AFTER the normal ALU/eSREG update).
                py4hw.Or2(self, 'SREG_I_en_or', w_mask_bit['I'], self.D_I_Force_WE, w_flag_en['I'])
                py4hw.Mux(self, 'SREG_I_d_mux', sel=self.D_I_Force_WE,
                          ins=[w_value_bit['I'], self.D_I_Force_Value], r=w_flag_d['I'])
                d_wire, en_wire = w_flag_d['I'], w_flag_en['I']
            else:
                # No override for the other 7 flags -- their Reg's d/enable
                # are just the decomposed write-value/write-mask bits
                # directly, no extra glue needed.
                d_wire, en_wire = w_value_bit[f], w_mask_bit[f]

            py4hw.Reg(self, f'SREG_{f}', d=d_wire, q=w_flag_q[f],
                      enable=en_wire, reset=self.reset, reset_value=0)

        # Compose the 8 flags back into one byte for MIH's SREG_ADDR (0x5F)
        # IN/OUT intercept and for the ALU's SREG_STATE input. LSBF order:
        # index0 = bit0 = C, ... index7 = bit7 = I.
        py4hw.ConcatenateLSBF(
            self, 'SREG_compose',
            ins=[w_flag_q['C'], w_flag_q['Z'], w_flag_q['N'], w_flag_q['V'],
                 w_flag_q['S'], w_flag_q['H'], w_flag_q['T'], w_flag_q['I']],
            r=W_SREG_ReadValue,
        )
