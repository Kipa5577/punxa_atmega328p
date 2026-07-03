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
        self.W_Loading_MUX_CB_MIH = py4hw.Wire(self, 'W_Loading_MUX', 5)
        self.W_Input_Select_CB_MIH = py4hw.Wire(self, 'W_Input_Select', 5)
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
        self.W_Select_K_CB_RH = py4hw.Wire(self,'W_Select_K_CB_RH',2)
        


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
        self.W_WB_addr_CB_MIH = py4hw.Wire(self, 'w_wb_addr', 8)

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
            RH_K_select=self.W_Select_K_CB_RH,
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
            CB_Instruction=self.W_CODE_ID_CB,              
            CB_Resp=self.W_Resp_MIH_CB,                     
            CB_Branch=self.W_Branch_ALU_CB,                 
            CB_Skip=self.W_Skip_ALU_CB,                     
            CB_Interrupt=self.Interrupt,                    
            CB_Instruction_fetched=self.W_Instruction_fetched_RH_CB,   
            CB_Instruction_decoded=self.W_Instruction_decoded_ID_CB,   
            CB_Executed_Jump=self.W_Executed_Jump_CB,       
            CB_Address_fetched=self.W_Address_fetched_RH_CB,
            CB_LoadSelectMux=self.W_LoadSelect_MUX_CB_MIH,  
            CB_LoadingMux=self.W_Loading_MUX_CB_MIH,        
            CB_Input_Select=self.W_Input_Select_CB_MIH,     
            CB_WE_MEMORY=self.W_WE_OpBuf_CB_MIH,                  
            CB_Read_Write=self.W_read_write,                
            CB_mem_instr=self.w_mem_instr_MIH_CB,           
            CB_IncDec=self.w_mem_incdec_MIH_CB,             
            CB_InputSelect=self.W_Input_Select_CB_OB,       
            CB_WE_Buffer=self.W_BufferWe_CB_OB,            
            CB_Load_Z=self.W_LOAD_Z_CB_RH,                  
            CB_Load_K=self.W_LOAD_K_CB_RH,
            CB_K_Select = self.W_Select_K_CB_RH,                  
            CB_Load_Jump=self.W_LOAD_JUMP_CB_RH,            
            CB_relative_Absolute=self.W_Relative_Absolute_CB_RH,  
            CB_Load_Byte=self.W_Load_byte_CB,               
            CB_Fetch_next_instruction=self.W_Fetch_next_instruction_CB_RH,  
            CB_Fetch_Address=self.W_Fetch_Address_CB_RH,    
            CB_WB_Addr=self.W_WB_addr_CB_MIH,               
            CB_JumpWidth=self.W_JumpWidth_CB_RH,            
            CB_LOAD_PCL=self.W_LOAD_PCL_CB_RH,              
            CB_LOAD_PCH=self.W_LOAD_PCH_CB_RH,              
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