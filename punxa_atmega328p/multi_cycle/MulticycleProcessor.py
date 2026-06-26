import py4hw

# Core blocks from your project
from .ControlBox import *
from .Instruction_decoder import *
from .RomHandler import *
from .MemoryInterfaceHandler import *
from .ALU import *
from .SREG_Logic import *
from .OperandBuffer import *
from .SmallFSMS.INSTRUCTION_FSM_BOX import *

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

        #RH = RomHandler
        #ID =  InstructionDecoder
        #MIH = MemoryInstructionHandler
        #CB = ControlBox
        #ALU = arithmetic logic unit
        #OB = OperandBuffer
        #SL = SREG_Logic
        # -------------------------
        # Shared wires
        # -------------------------
        self.W_Instruction_RH_ID = py4hw.Wire(self, 'W_Instruction_RH_ID', 16)
        self.W_Resp_MIH_CB = py4hw.Wire(self, 'W_Resp_MIH', 1)
        self.W_Branch_ALU_CB = py4hw.Wire(self, 'W_Branch_ALU_CB', 1)
        self.W_Skip_ALU_CB = py4hw.Wire(self, 'W_Skip_ALU_CB', 1)

        # Decoder outputs
        self.W_CODE_ID_CB = py4hw.Wire(self, 'W_CODE_ID_CB', 16)
        self.W_RD_ID_MIH = py4hw.Wire(self, 'W_RD_ID_MIH', 5)
        self.W_RR_ID_MIH = py4hw.Wire(self, 'W_RR_ID_MIH', 5)
        self.W_K8_ID_OB = py4hw.Wire(self,'W_K8_ID_OB',8)
        #self.W_K7_ID_MIH = py4hw.Wire(self,'W_K7_ID_MIH',7)
        self.W_K6_ID_OB =  py4hw.Wire(self,'W_K6_ID_OB',6)
        self.W_K4_ID_ = py4hw.Wire(self,'W_K4_ID_',4)
        self.W_k7_ID_RH = py4hw.Wire(self, 'W_k7_ID_RH', 7)
        self.W_k12_ID_RH = py4hw.Wire(self,'W_k12_ID_RH',12)
        self.W_k7_22_ID_RH = py4hw.Wire(self,'W_k7_22_ID_RH',7)
        self.W_b_ID_ALU = py4hw.Wire(self, 'W_b_ID_RH', 3)
        self.W_s_ID_ALU = py4hw.Wire(self,'W_s_ID_MIH',3)
        self.W_A5_ID_MIH = py4hw.Wire(self,'W_A5_ID_MIH',5)
        self.W_A6_ID_MIH = py4hw.Wire(self,'W_A6_ID_MIH',6)
        self.W_q6_ID_MIH = py4hw.Wire(self, 'W_q6_ID_MIH', 6)
        self.W_Instruction_decoded_ID_CB = py4hw.Wire(self,'W_Instruction_decoded_ID_CB',1)
        #self.W_address_xyz = py4hw.Wire(self, 'W_address_xyz', 16)

        # ALU / SREG
        self.W_ImputRegA0_OB_ALU = py4hw.Wire(self, 'W_ImputRegA0_OB_ALU', 8)
        self.W_ImputRegA1_OB_ALU = py4hw.Wire(self, 'W_ImputRegA1_OB_ALU', 8)
        self.W_ImputRegB0_OB_ALU = py4hw.Wire(self, 'W_ImputRegB0_OB_ALU', 8)
        self.W_ImputRegB1_OB_ALU = py4hw.Wire(self, 'W_ImputRegB1_OB_ALU', 8)
        self.W_OUTPUTByte0_ALU_MIH = py4hw.Wire(self, 'W_OUTPUTByte0_ALU_MIH', 8)
        self.W_OUTPUTByte1_ALU_MIH = py4hw.Wire(self, 'W_OUTPUTByte1_ALU_MIH', 8)
        self.W_SREG_SL_ALU = py4hw.Wire(self, 'W_SREG_SL_ALU', 8)
        self.W_eSREG_ALU_SL = py4hw.Wire(self, 'W_eSREG_ALU_SL', 8)
        self.W_SREG_ALU_SL = py4hw.Wire(self, 'W_SREG_ALU_SL', 8)

        # Operand buffer interface
        self.W_DataInput_MIH_OB = py4hw.Wire(self, 'W_DataInput_MIH_OB', 8)
        self.W_BufferWe_CB_OB = py4hw.Wire(self, 'W_BufferWe_CB_OB', 4)  # 1=A0, 2=A1, 3=B0, 4=B1 ,5=IOBuffer
        self.W_IOBuffer_MIH_OB = py4hw.Wire(self, 'W_IOBuffer_MIH_OB',8)
        self.W_Input_Select_CB_OB =  py4hw.Wire(self,'W_Input_Select_CB_OB',1)


        # ControlBox wires
        self.W_NotExecute_CB_MIH = py4hw.Wire(self, 'NotExecute', 1)
        self.W_LoadSelect_MUX_CB_MIH = py4hw.Wire(self, 'W_LoadSelect_MUX', 3)
        self.W_Loading_MUX_CB_MIH = py4hw.Wire(self, 'W_Loading_MUX', 3)
        self.W_Input_Select_CB_MIH = py4hw.Wire(self, 'W_Input_Select', 3)
        self.W_WE_OpBuf_CB_MIH = py4hw.Wire(self, 'W_WE_OpBuf_CB_MIH', 6)
        self.W_read_write = py4hw.Wire(self, 'W_read_write', 2)
        #self.W_Mem_instruction = py4hw.Wire(self, 'W_Mem_instruction', 3)
        self.W_LOAD_Z_CB_RH = py4hw.Wire(self, 'W_LOAD_Z', 1)
        self.W_LOAD_K_CB_RH = py4hw.Wire(self, 'W_LOAD_K', 1)
        self.W_LOAD_JUMP_CB_RH = py4hw.Wire(self, 'W_LOAD_JUMP', 1)
        self.W_Relative_Absolute_CB_RH = py4hw.Wire(self, 'W_Relative_Absolute', 1)
        self.W_Load_byte_CB = py4hw.Wire(self, 'w_load_byte', 1)
        self.W_LoadL_CB_ = py4hw.Wire(self,'W_LoadL',1)
        self.W_LoadH_CB_ = py4hw.Wire(self,'W_LoadH',1)
        self.W_JumpWidth_CB_RH = py4hw.Wire(self,'W_JumpWidth',1)
        self.W_LOAD_PCL_CB_RH = py4hw.Wire(self,'W_LOAD_PCL_CB_RH',1)
        self.W_LOAD_PCH_CB_RH = py4hw.Wire(self,'W_LOAD_PCH_CB_RH',1)
        self.W_Instruction_fetched_RH_CB = py4hw.Wire(self,'W_Instruction_fetched',1)
        self.W_Executed_Jump_CB = py4hw.Wire(self,'W_Executed_Jump',1)
        self.W_Fetch_next_instruction_CB_RH = py4hw.Wire(self,'W_Fetch_next_instruction_CB_RH',1)
        


        # MemoryInterfaceHandler wires
        #self.w_mem_register_out = py4hw.Wire(self, 'w_mem_register_out', 8)
        self.w_mem_incdec_MIH_CB = py4hw.Wire(self, 'w_mem_incdec_MIH_CB', 2)
        self.w_mem_instr_MIH_CB = py4hw.Wire(self, 'w_mem_instr_MIH_CB', 5)
        #self.w_general_input = py4hw.Wire(self, 'w_general_input', 8)
        self.w_address_ZL_MIH_RH = py4hw.Wire(self,'w_address_ZL_MIH_RH',8)
        self.w_address_ZH_MIH_RH = py4hw.Wire(self,'w_address_ZH_MIH_RH',8)
        self.W_Pc_valL_RH_MIH = py4hw.Wire(self,'W_Pc_valL_RH_MIH',8)
        self.W_Pc_valH_RH_MIH = py4hw.Wire(self,'W_Pc_valH_RH_MIH',8)

        # Write-back address: explicit register address driven by ControlBox
        self.W_WB_addr_CB_MIH = py4hw.Wire(self, 'w_wb_addr', 5)

        # ROM handler wires
        self.W_Rom_address_RH_MIH = py4hw.Wire(self, 'W_Rom_address_RH_MIH', 16)
        self.W_Rom_value_RH_MIH = py4hw.Wire(self, 'W_Rom_value_RH_MIH', 16)
        self.W_PCL_LOAD_VAL_CB_RH = py4hw.Wire(self,'W_PCL_LOAD_VAL_CB_RH',8)
        self.W_PCH_LOAD_VAL_CB_RH = py4hw.Wire(self,'W_PCH_LOAD_VAL_CB_RH',8)
        self.W_Fetch_Address_CB_RH = py4hw.Wire(self,'W_Fetch_Address_CB_RH',1)
        self.W_Address_fetched_RH_CB = py4hw.Wire(self,'W_Address_fetched_RH_CB',1)

        # No use 

        self.W_Write_Enable_CB_OB = py4hw.Wire(self,'W_Write_Enable_CB_OB',1)


        # -------------------------
        # Sub-components
        # -------------------------
        self.rom = RomHandler(
            self, 'RomHandler',
            RH_mem=self.ins_mem,
            RH_instructionOut=self.W_Instruction_RH_ID,
            RH_Address_Out=self.W_Rom_address_RH_MIH,
            RH_Value_Out=self.W_Rom_value_RH_MIH, 
            RH_Pc_valL=self.W_Pc_valL_RH_MIH,
            RH_Pc_valH=self.W_Pc_valH_RH_MIH,
            RH_Instruction_fetched=self.W_Instruction_fetched_RH_CB,
            RH_Executed_Jump=self.W_Executed_Jump_CB,
            RH_Load_Z=self.W_LOAD_Z_CB_RH,
            RH_address_ZL=self.w_address_ZL_MIH_RH,
            RH_address_ZH=self.w_address_ZH_MIH_RH,
            RH_Load_K=self.W_LOAD_K_CB_RH,
            RH_K_select=self.W_Relative_Absolute_CB_RH,
            RH_K7=self.W_k7_ID_RH,
            RH_K12=self.W_k12_ID_RH,
            RH_K7_22=self.W_k7_22_ID_RH,
            RH_Load_Jump=self.W_LOAD_JUMP_CB_RH,
            RH_relative_Absolute=self.W_Relative_Absolute_CB_RH,
            RH_Load_Byte=self.W_Load_byte_CB,
            RH_WriteVal=self.W_OUTPUTByte0_ALU_MIH,
            RH_PCL_LOAD_VAL=self.W_PCL_LOAD_VAL_CB_RH,
            RH_PCH_LOAD_VAL=self.W_PCH_LOAD_VAL_CB_RH,
            RH_Fetch_next_instruction=self.W_Fetch_next_instruction_CB_RH,
            RH_JumpWidth=self.W_JumpWidth_CB_RH,
            RH_Load_PCL=self.W_LOAD_PCL_CB_RH,
            RH_Load_PCH=self.W_LOAD_PCH_CB_RH,
            RH_fetch_address=self.W_Fetch_Address_CB_RH,
            RH_Address_fetched=self.W_Address_fetched_RH_CB,
            RH_reset_address=reset_address
        )

        self.decoder = Instruction_decoder(
            self, 'InstructionDecoder',
            ID_Instruction=self.W_Instruction_RH_ID,
            ID_Instruction_fetched=self.W_Instruction_fetched_RH_CB,
            ID_InstructionCode=self.W_CODE_ID_CB,
            ID_Rd=self.W_RD_ID_MIH,
            ID_Rr=self.W_RR_ID_MIH,
            ID_K8=self.W_K8_ID_OB,
            ID_k12=self.W_k12_ID_RH,
            ID_K6=self.W_K6_ID_OB,
            ID_K4=self.W_K4_ID_,
            ID_k16=self.W_k12_ID_RH,
            ID_k7= self.W_k7_ID_RH,
            ID_k7_22=self.W_k7_22_ID_RH,
            ID_b=self.W_b_ID_ALU,
            ID_s=self.W_s_ID_ALU,
            ID_A5=self.W_A5_ID_MIH,
            ID_A6=self.W_A6_ID_MIH,
            ID_q=self.W_q6_ID_MIH,
            ID_Instruction_decoded=self.W_Instruction_decoded_ID_CB
        )

        self.control = control_Box(
            self, 'ControlBox',
            CB_Instruction=self.W_CODE_ID_CB,              # Decoded instruction opcode/code from Instruction_decoder, used to drive the FSM's control decisions
            CB_Resp=self.W_Resp_MIH_CB,                     # Memory handshake response from MemoryInterfaceHandler, tells ControlBox the SRAM access has completed
            CB_Branch=self.W_Branch_ALU_CB,                 # Branch condition result from the ALU (e.g. zero/carry flag check), tells ControlBox whether a conditional branch should be taken
            CB_Skip=self.W_Skip_ALU_CB,                     # Skip condition result from the ALU, tells ControlBox whether a skip instruction (SBRC/SBRS/SBIC/SBIS) should skip the next instruction
            CB_Interrupt=self.Interrupt,                    # Interrupt request line, signals ControlBox that an interrupt needs to be serviced
            CB_Instruction_fetched=self.W_Instruction_fetched_RH_CB,   # Handshake from RomHandler indicating a new instruction word has been fetched and is ready to decode
            CB_Instruction_decoded=self.W_Instruction_decoded_ID_CB,   # Handshake from Instruction_decoder indicating the decoded fields for the current instruction are valid/stable
            CB_Executed_Jump=self.W_Executed_Jump_CB,       # Handshake from RomHandler confirming a jump/branch/call target has been committed to the PC this cycle
            CB_LoadSelectMux=self.W_LoadSelect_MUX_CB_MIH,  # Output to MemoryInterfaceHandler: selects which displacement/offset source feeds the address-generation MUX
            CB_LoadingMux=self.W_Loading_MUX_CB_MIH,        # Output to MemoryInterfaceHandler: selects which internal pointer byte (XL/XH/YL/YH/ZL/ZH/SPL/SPH) gets loaded when WE is asserted
            CB_Input_Select=self.W_Input_Select_CB_MIH,     # Output to MemoryInterfaceHandler: selects the data source MUX for writes to memory (ALU result, K constant, ROM value, pointer byte, etc.)
            CB_WE_MEMORY=self.W_WE_OpBuf_CB_MIH,                  # Output to MemoryInterfaceHandler: write-enable for loading data into the internal X/Y/Z/SP pointer registers
            CB_Read_Write=self.W_read_write,                # Output to MemoryInterfaceHandler: selects memory read (0) vs memory write (1) for the current SRAM access
            CB_mem_instr=self.w_mem_instr_MIH_CB,           # Output to MemoryInterfaceHandler: selects which addressing mode/pointer (X, Y, Z, SP, Rd, Rr, A5/A6, etc.) generates the SRAM address
            CB_IncDec=self.w_mem_incdec_MIH_CB,             # Output to MemoryInterfaceHandler: controls pointer auto-increment/pre-decrement behavior (none / post-increment / pre-decrement)
            CB_InputSelect=self.W_Input_Select_CB_OB,       # Output to OperandBuffer: selects whether the Rr0 latch loads from the data bus or from the decoded K constant
            CB_WE_Buffer=self.W_BufferWe_CB_OB,            # Output to OperandBuffer: write-enable selecting which operand latch (Rd0/Rd1/Rr0/Rr1/IO) is updated this cycle
            CB_Load_Z=self.W_LOAD_Z_CB_RH,                  # Output to RomHandler: triggers an indirect jump/call (IJMP/ICALL) using the Z register as the new PC
            CB_Load_K=self.W_LOAD_K_CB_RH,                  # Output to RomHandler: triggers a conditional branch (BRxx/SBxx) using the K7 offset
            CB_Load_Jump=self.W_LOAD_JUMP_CB_RH,            # Output to RomHandler: triggers an unconditional jump/call (RJMP/RCALL/JMP/CALL) using the K12/K7_22 offset/address
            CB_relative_Absolute=self.W_Relative_Absolute_CB_RH,  # Output to RomHandler: selects whether the pending jump is relative (PC += K) or absolute (PC = K)
            CB_Load_Byte=self.W_Load_byte_CB,               # Output to RomHandler: triggers a Store Program Memory (SPM) write of WriteVal into instruction ROM
            CB_Fetch_next_instruction=self.W_Fetch_next_instruction_CB_RH,  # Output to RomHandler: releases the FSM from STOP/single-step trap to fetch the next instruction
            CB_Fetch_Address=self.W_Fetch_Address_CB_RH,    # Output to RomHandler: requests fetching the next ROM word as a raw address/data value (e.g. second word of LDS/STS/JMP/CALL)
            CB_WB_Addr=self.W_WB_addr_CB_MIH,               # Output to MemoryInterfaceHandler: explicit write-back register address (e.g. Rd+1 for ADIW/MOVW, R0/R1 for MUL) overriding Rd/Rr
            CB_JumpWidth=self.W_JumpWidth_CB_RH,            # Output to RomHandler: tells it how much to advance the PC for the next instruction (0 = PC+1, 1 = PC+2 for two-word instructions)
            CB_LOAD_PCL=self.W_LOAD_PCL_CB_RH,              # Output to RomHandler: enables loading the low byte of the Program Counter from PCL_LOAD_VAL (e.g. POP PC during RET)
            CB_LOAD_PCH=self.W_LOAD_PCH_CB_RH,              # Output to RomHandler: enables loading the high byte of the Program Counter from PCH_LOAD_VAL (e.g. POP PC during RET)
        )

        self.sreg = SREG_Logic(
            self, 'SREG_Reset',
            SREG_In=self.W_SREG_ALU_SL,
            eSREG_In=self.W_eSREG_ALU_SL,
            SREG_Reset=self.reset,
            SREG_Out=self.W_SREG_SL_ALU
        )

        self.operand_buffer = OperandBuffer(
            self, 'OperandBuffer',
            OB_DATA_IN=self.W_DataInput_MIH_OB,
            OB_K=self.W_K8_ID_OB,
            OB_WE=self.W_BufferWe_CB_OB,
            OB_Reset=self.reset,
            OB_InputSelectBuffer=self.W_Input_Select_CB_OB,
            OB_A0=self.W_ImputRegA0_OB_ALU,
            OB_A1=self.W_ImputRegA1_OB_ALU,
            OB_B0=self.W_ImputRegB0_OB_ALU,
            OB_B1=self.W_ImputRegB1_OB_ALU,
            OB_IOout=self.W_IOBuffer_MIH_OB
        )

        self.alu = ALU(
            self, 'ALU',
            ImputRegA0=self.W_ImputRegA0_OB_ALU,
            ImputRegA1=self.W_ImputRegA1_OB_ALU,
            ImputRegB0=self.W_ImputRegB0_OB_ALU,
            ImputRegB1=self.W_ImputRegB1_OB_ALU,
            ALUInstruction=self.W_CODE_ID_CB,
            SREG_STATE=self.W_SREG_SL_ALU,
            BitPos=self.W_b_ID_ALU,
            IOreg=self.W_IOBuffer_MIH_OB,
            ALUOUTPUTByte0=self.W_OUTPUTByte0_ALU_MIH,
            ALUOUTPUTByte1=self.W_OUTPUTByte1_ALU_MIH,
            SREG_VAL=self.W_SREG_ALU_SL,
            eSREG_VAL=self.W_eSREG_ALU_SL,
            BRANCH=self.W_Branch_ALU_CB,
            SKIP=self.W_Skip_ALU_CB
        )

        self.mem_if = MemoryInterfaceHandler(
            self, 'MemoryInterfaceHandler',
            reset=self.reset,
            WE=self.W_WE_OpBuf_CB_MIH,
            LoadSelectMux=self.W_LoadSelect_MUX_CB_MIH,
            LoadingMux=self.W_Loading_MUX_CB_MIH,
            IncDec=self.w_mem_incdec_MIH_CB,
            RomAddressValue=self.W_Rom_value_RH_MIH,
            ReadWrite=self.W_read_write,
            InputSelectMemory=self.W_Input_Select_CB_MIH,
            Mem_instruction=self.w_mem_instr_MIH_CB,
            RomAddress=self.W_Rom_address_RH_MIH,
            ResL=self.W_OUTPUTByte0_ALU_MIH,
            ResH=self.W_OUTPUTByte1_ALU_MIH,
            K_val_Input=self.W_K8_ID_OB,
            PCL_VAL_IN=self.W_Pc_valL_RH_MIH,
            PCH_VAL_IN=self.W_Pc_valH_RH_MIH,
            Rd=self.W_RD_ID_MIH,
            Rr=self.W_RR_ID_MIH,
            WbAddr=self.W_WB_addr_CB_MIH,
            memory=self.memory,
            RegisterOut=self.W_DataInput_MIH_OB,
            Resp=self.W_Resp_MIH_CB,
            address_ZL=self.w_address_ZL_MIH_RH,
            address_ZH=self.w_address_ZH_MIH_RH,
            Q=self.W_q6_ID_MIH,
            A_5bit=self.W_A5_ID_MIH,
            A_6bit=self.W_A6_ID_MIH,
            MIH_PCL_LOAD_VAL = self.W_PCL_LOAD_VAL_CB_RH,
            MIH_PCH_LOAD_VAL = self.W_PCH_LOAD_VAL_CB_RH,
        )