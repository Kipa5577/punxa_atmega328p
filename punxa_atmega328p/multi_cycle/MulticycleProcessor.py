import py4hw

# Core blocks from your project
from .ControlBox import *
from .Instruction_decoder import *
from .RomHandler import *
from .MemoryInterfaceHandler import *
from .ALU import *
from .SREG_Logic import *
from .OperandBuffer import *

# Reuse the opcode groupings from ControlBox so the assembly stays in sync.
from . import ControlBox as cb


class multicycleProcessor(py4hw.Logic):

    def __init__(self, parent, name, Interrupt, ins_mem, memory, reset, reset_address=0):
        super().__init__(parent, name)

        # -------------------------
        # External inputs / outputs
        # -------------------------
        
        self.reset = self.addIn('reset', reset)
        self.Interrupt = self.addIn('interrupt', Interrupt)

        self.ins_mem = self.addInterfaceSource('ins_mem', ins_mem)
        self.memory = self.addInterfaceSource('memory', memory)

        # -------------------------
        # Shared wires
        # -------------------------
        self.w_instruction = py4hw.Wire(self, 'w_instruction', 16)
        self.w_resp = py4hw.Wire(self, 'w_resp', 1)
        self.w_branch = py4hw.Wire(self, 'w_branch', 1)
        self.w_skip = py4hw.Wire(self, 'w_skip', 1)
        #self.w_interrupt = py4hw.Wire(self, 'w_interrupt', 1)

        # Decoder outputs
        self.W_CODE = py4hw.Wire(self, 'w_code', 16)
        self.W_Rd = py4hw.Wire(self, 'w_rd', 5)
        self.W_Rr = py4hw.Wire(self, 'w_rr', 5)
        self.W_K = py4hw.Wire(self, 'w_k', 8)
        self.W_K_ADDR = py4hw.Wire(self, 'w_k_addr', 22)
        self.W_b = py4hw.Wire(self, 'w_b', 7)
        self.W_A = py4hw.Wire(self, 'w_A', 5)
        self.W_q = py4hw.Wire(self, 'w_q', 6)
        #self.W_address_xyz = py4hw.Wire(self, 'W_address_xyz', 16)

        # ALU / SREG
        self.W_ALU_ImputRegA0 = py4hw.Wire(self, 'ImputRegA0', 8)
        self.W_ALU_ImputRegA1 = py4hw.Wire(self, 'ImputRegA1', 8)
        self.W_ALU_ImputRegB0 = py4hw.Wire(self, 'ImputRegB0', 8)
        self.W_ALU_ImputRegB1 = py4hw.Wire(self, 'ImputRegB1', 8)
        self.W_OUTPUTByte0 = py4hw.Wire(self, 'OUTPUTByte0', 8)
        self.W_OUTPUTByte1 = py4hw.Wire(self, 'OUTPUTByte1', 8)
        self.W_ALU_SREG_IN = py4hw.Wire(self, 'ALU_SREG_IN', 8)
        self.W_ALU_ESREG_OUT = py4hw.Wire(self, 'ALU_ESREG_OUT', 8)
        self.W_ALU_SREG_OUT = py4hw.Wire(self, 'ALU_SREG_OUT', 8)

        # Operand buffer interface
        self.w_operand_data = py4hw.Wire(self, 'w_operand_data', 8)
        self.w_operand_we = py4hw.Wire(self, 'w_operand_we', 3)  # 1=A0, 2=A1, 3=B0, 4=B1
        self.W_ALU_IO = py4hw.Wire(self, 'W_ALU_IO',8)
        self.w_input_select =  py4hw.Wire(self,'w_input_select',1)
        self.w_write_enbale = py4hw.Wire(self,'w_write_enbale',3)

        # ControlBox wires
        self.W_NotExecute = py4hw.Wire(self, 'NotExecute', 1)
        self.W_LoadSelect_MUX = py4hw.Wire(self, 'W_LoadSelect_MUX', 3)
        self.W_Loading_MUX = py4hw.Wire(self, 'W_Loading_MUX', 3)
        self.W_Input_Select = py4hw.Wire(self, 'W_Input_Select', 3)
        self.W_WE = py4hw.Wire(self, 'W_WE', 6)
        self.W_read_write = py4hw.Wire(self, 'W_read_write', 2)
        #self.W_Mem_instruction = py4hw.Wire(self, 'W_Mem_instruction', 3)
        self.W_LOAD_Z = py4hw.Wire(self, 'W_LOAD_Z', 1)
        self.W_LOAD_K = py4hw.Wire(self, 'W_LOAD_K', 1)
        self.W_LOAD_JUMP = py4hw.Wire(self, 'W_LOAD_JUMP', 1)
        self.W_Relative_Absolute = py4hw.Wire(self, 'W_Relative_Absolute', 1)
        self.W_Load_byte = py4hw.Wire(self, 'w_load_byte', 1)
        self.w_EnableRead = py4hw.Wire(self,'w_EnableRead',1)

        # MemoryInterfaceHandler wires
        #self.w_mem_register_out = py4hw.Wire(self, 'w_mem_register_out', 8)
        self.w_mem_incdec = py4hw.Wire(self, 'w_mem_incdec', 2)
        self.w_mem_instr = py4hw.Wire(self, 'w_mem_instr', 4)
        #self.w_general_input = py4hw.Wire(self, 'w_general_input', 8)
        self.w_address_ZL = py4hw.Wire(self,'w_address_ZL',8)
        self.w_address_ZH = py4hw.Wire(self,'w_address_ZH',8)

        # ROM handler wires
        self.w_rom_address = py4hw.Wire(self, 'w_rom_address', 4)

        # -------------------------
        # Sub-components
        # -------------------------
        self.rom = RomHandler(
            self, 'RomHandler',
            mem=self.ins_mem,
            instructionOut=self.w_instruction,
            Address_Out=self.w_rom_address,
            Load_Z=self.W_LOAD_Z,
            address_ZL=self.w_address_ZL,
            address_ZH=self.w_address_ZH,
            Load_K=self.W_LOAD_K,
            K=self.W_K_ADDR,
            Load_Jump=self.W_LOAD_JUMP,
            relative_Absolute=self.W_Relative_Absolute,
            Load_Byte=self.W_Load_byte,
            WriteVal=self.W_K,
            reset_address=reset_address,
            Enable=self.w_EnableRead,
        )

        self.decoder = Instruction_decoder(
            self, 'InstructionDecoder',
            Instruction=self.w_instruction,
            InstructionCode=self.W_CODE,
            Rd=self.W_Rd,
            Rr=self.W_Rr,
            K=self.W_K,
            k_addr=self.W_K_ADDR,
            b=self.W_b,
            A=self.W_A,
            q=self.W_q,
        )

        self.control = control_Box(
            self, 'ControlBox',
            Instruction=self.W_CODE,
            Resp=self.w_resp,
            Branch=self.w_branch,
            Skip=self.w_skip,
            Interrupt=self.Interrupt,
            NotExecute=self.W_NotExecute,
            LoadSelectMux=self.W_LoadSelect_MUX,
            LoadingMux=self.W_Loading_MUX,
            Input_Select=self.W_Input_Select,
            WE=self.W_WE,
            Read_Write=self.W_read_write,
            Address_XYZ=self.w_mem_instr,
            write_Opperand_Buffer = self.w_operand_we,
            Load_Z=self.W_LOAD_Z,
            Load_K=self.W_LOAD_K,
            Load_Jump=self.W_LOAD_JUMP,
            relative_Absolute=self.W_Relative_Absolute,
            Load_Byte=self.W_Load_byte,
            IncDec = self.w_mem_incdec,
            InputSelect= self.w_input_select,
            Write_Enable= self.w_write_enbale,
            Enable=self.w_EnableRead,
        )

        self.sreg = SREG_Logic(
            self, 'SREG',
            SREG_In=self.W_ALU_SREG_IN,
            eSREG_In=self.W_ALU_ESREG_OUT,
            Reset=self.reset,
            SREG_Out=self.W_ALU_SREG_OUT,
        )

        self.operand_buffer = OperandBuffer(
            self, 'OperandBuffer',
            DATAInterface=self.w_operand_data,
            K=self.W_K,
            WE=self.w_operand_we,
            Reset=self.reset,
            A0=self.W_ALU_ImputRegA0,
            A1=self.W_ALU_ImputRegA1,
            B0=self.W_ALU_ImputRegB0,
            B1=self.W_ALU_ImputRegB1,
            IOout=self.W_ALU_IO,
            InputSelect=self.w_input_select,
        )

        self.alu = ALU(
            self, 'ALU',
            ImputRegA0=self.W_ALU_ImputRegA0,
            ImputRegA1=self.W_ALU_ImputRegA1,
            ImputRegB0=self.W_ALU_ImputRegB0,
            ImputRegB1=self.W_ALU_ImputRegB1,
            ALUInstruction=self.W_CODE,
            SREG_STATE=self.W_ALU_SREG_OUT,
            BitPos=self.W_b,
            IOreg=self.W_ALU_IO,
            ALUOUTPUTByte0=self.W_OUTPUTByte0,
            ALUOUTPUTByte1=self.W_OUTPUTByte1,
            SREG_VAL=self.W_ALU_SREG_IN,
            eSREG_VAL=self.W_ALU_ESREG_OUT,
            BRANCH=self.w_branch,
            SKIP=self.w_skip,
        )

        self.mem_if = MemoryInterfaceHandler(
            self, 'MemoryInterfaceHandler',
            reset=self.reset,
            WE=self.W_WE,
            LoadSelectMux=self.W_LoadSelect_MUX,
            LoadingMux=self.W_Loading_MUX,
            IncDec=self.w_mem_incdec,
            ReadWrite=self.W_read_write,
            InputSelect=self.W_Input_Select,
            Mem_instruction=self.w_mem_instr,
            RomAddress=self.w_rom_address,
            ResL=self.W_OUTPUTByte0,
            ResH=self.W_OUTPUTByte1,
            Param_Rd=self.W_Rd,
            Param_Rr=self.W_Rr,
            GeneralInput=self.W_K,
            memory=self.memory,
            RegisterOut=self.w_operand_data,
            Resp=self.w_resp,
            address_ZL=self.w_address_ZL,
            address_ZH=self.w_address_ZH,
            Q=self.W_q,
        )
