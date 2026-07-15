import py4hw

# Core blocks from your project
from .ControlBox import *
from .Instruction_decoder import *
from .RomHandler import *
from .MemoryInterfaceHandler import *
from .ALU import *
from .OperandBuffer import *
from .SmallFSMS.INSTRUCTION_FSM_BOX import *

class multicycleProcessor(py4hw.Logic):

    def __init__(self, parent, name, Interrupt, Interrupt_Enable, ins_mem, memory, reset, reset_address=0,
                 Bus_Passthrough_Ranges=None):
        super().__init__(parent, name)

        # -------------------------
        # External inputs / outputs
        # -------------------------
        
        self.reset = self.addIn('reset', reset)

        # Interrupt request line, driven by an external InterruptUnit
        # peripheral once it has both seen I == 1 (via Interrupt_Enable
        # below) and observed one of its own configured interrupt sources
        # fire. MainFSM samples this at instruction boundaries only (see
        # MainFSM.INTERRUPT_ENTRY). Always wired, not optional — every
        # instantiation of this CPU must supply a real InterruptUnit wire.
        self.Interrupt = self.addIn('interrupt', Interrupt)

        # Global Interrupt Enable (I flag of SREG) pin, driven OUT to the
        # external InterruptUnit. Always wired, not optional. Driven
        # directly by MemoryInterfaceHandler.I_Flag_Out below — it already
        # owns the committed SREG register, so it's the natural source.
        self.Interrupt_Enable = self.addOut('Interrupt_Enable', Interrupt_Enable)

        self.ins_mem = self.addInterfaceSource('ins_mem', ins_mem)
        self.memory = self.addInterfaceSource('memory', memory)

        #RH = RomHandler
        #ID =  InstructionDecoder
        #MIH = MemoryInstructionHandler
        #CB = ControlBox
        #ALU = arithmetic logic unit
        #OB = OperandBuffer
        #SL = SREG (now handled inside MemoryInterfaceHandler, wire names kept for continuity)
        # -------------------------
        # Shared wires
        # -------------------------
        W_Instruction_RH_ID = self.wire('W_Instruction_RH_ID', 16)
        W_Resp_MIH_CB = self.wire( 'W_Resp_MIH', 1)
        W_Branch_ALU_CB = self.wire('W_Branch_ALU_CB', 1)
        W_Skip_ALU_CB = self.wire( 'W_Skip_ALU_CB', 1)

        # Decoder outputs
        W_CODE_ID_CB = self.wire( 'W_CODE_ID_CB', 16)
        W_RD_ID_MIH = self.wire( 'W_RD_ID_MIH', 5)
        W_RR_ID_MIH = self.wire( 'W_RR_ID_MIH', 5)
        W_K8_ID_OB = self.wire('W_K8_ID_OB',8)
        #self.W_K7_ID_MIH = py4hw.Wire(self,'W_K7_ID_MIH',7)
        W_K6_ID_OB =  self.wire('W_K6_ID_OB',6)
        W_K4_ID_ = self.wire('W_K4_ID_',4)
        W_k7_ID_RH = py4hw.Wire(self, 'W_k7_ID_RH', 7)
        W_k12_ID_RH = py4hw.Wire(self,'W_k12_ID_RH',12)
        W_k7_22_ID_RH = py4hw.Wire(self,'W_k7_22_ID_RH',7)
        W_b_ID_ALU = py4hw.Wire(self, 'W_b_ID_RH', 3)
        W_s_ID_ALU = py4hw.Wire(self,'W_s_ID_MIH',3)
        W_A5_ID_MIH = py4hw.Wire(self,'W_A5_ID_MIH',5)
        W_A6_ID_MIH = py4hw.Wire(self,'W_A6_ID_MIH',6)
        W_q6_ID_MIH = py4hw.Wire(self, 'W_q6_ID_MIH', 6)
        W_Instruction_decoded_ID_CB = py4hw.Wire(self,'W_Instruction_decoded_ID_CB',1)
        #self.W_address_xyz = py4hw.Wire(self, 'W_address_xyz', 16)

        # ALU / SREG
        W_ImputRegA0_OB_ALU = py4hw.Wire(self, 'W_ImputRegA0_OB_ALU', 8)
        W_ImputRegA1_OB_ALU = py4hw.Wire(self, 'W_ImputRegA1_OB_ALU', 8)
        W_ImputRegB0_OB_ALU = py4hw.Wire(self, 'W_ImputRegB0_OB_ALU', 8)
        W_ImputRegB1_OB_ALU = py4hw.Wire(self, 'W_ImputRegB1_OB_ALU', 8)
        W_OUTPUTByte0_ALU_MIH = py4hw.Wire(self, 'W_OUTPUTByte0_ALU_MIH', 8)
        W_OUTPUTByte1_ALU_MIH = py4hw.Wire(self, 'W_OUTPUTByte1_ALU_MIH', 8)
        W_SREG_SL_ALU = py4hw.Wire(self, 'W_SREG_SL_ALU', 8)
        W_eSREG_ALU_SL = py4hw.Wire(self, 'W_eSREG_ALU_SL', 8)
        W_SREG_ALU_SL = py4hw.Wire(self, 'W_SREG_ALU_SL', 8)

        # Operand buffer interface
        W_DataInput_MIH_OB = py4hw.Wire(self, 'W_DataInput_MIH_OB', 8)
        W_BufferWe_CB_OB = py4hw.Wire(self, 'W_BufferWe_CB_OB', 4)  # 1=A0, 2=A1, 3=B0, 4=B1 ,5=IOBuffer
        W_IOBuffer_MIH_OB = py4hw.Wire(self, 'W_IOBuffer_MIH_OB',8)
        W_Input_Select_CB_OB =  py4hw.Wire(self,'W_Input_Select_CB_OB',1)


        # ControlBox wires
        W_NotExecute_CB_MIH = py4hw.Wire(self, 'NotExecute', 1)
        W_LoadSelect_MUX_CB_MIH = py4hw.Wire(self, 'W_LoadSelect_MUX', 3)
        W_Loading_MUX_CB_MIH = py4hw.Wire(self, 'W_Loading_MUX', 5)
        W_Input_Select_CB_MIH = py4hw.Wire(self, 'W_Input_Select', 5)
        W_WE_OpBuf_CB_MIH = py4hw.Wire(self, 'W_WE_OpBuf_CB_MIH', 6)
        W_read_write = py4hw.Wire(self, 'W_read_write', 2)
        #self.W_Mem_instruction = py4hw.Wire(self, 'W_Mem_instruction', 3)
        W_LOAD_Z_CB_RH = py4hw.Wire(self, 'W_LOAD_Z', 1)
        W_LOAD_K_CB_RH = py4hw.Wire(self, 'W_LOAD_K', 1)
        W_LOAD_JUMP_CB_RH = py4hw.Wire(self, 'W_LOAD_JUMP', 1)
        W_Relative_Absolute_CB_RH = py4hw.Wire(self, 'W_Relative_Absolute', 1)
        W_Load_byte_CB = py4hw.Wire(self, 'w_load_byte', 1)
        W_LoadL_CB_ = py4hw.Wire(self,'W_LoadL',1)
        W_LoadH_CB_ = py4hw.Wire(self,'W_LoadH',1)
        W_JumpWidth_CB_RH = py4hw.Wire(self,'W_JumpWidth',1)
        W_LOAD_PCL_CB_RH = py4hw.Wire(self,'W_LOAD_PCL_CB_RH',1)
        W_LOAD_PCH_CB_RH = py4hw.Wire(self,'W_LOAD_PCH_CB_RH',1)
        W_Instruction_fetched_RH_CB = py4hw.Wire(self,'W_Instruction_fetched',1)
        W_Executed_Jump_CB = py4hw.Wire(self,'W_Executed_Jump',1)
        W_Fetch_next_instruction_CB_RH = py4hw.Wire(self,'W_Fetch_next_instruction_CB_RH',1)
        W_Select_K_CB_RH = py4hw.Wire(self,'W_Select_K_CB_RH',2)

        W_WriteVal_RH_MIH = py4hw.Wire(self,'W_WriteVal_RH_MIH',8)
        W_ReadVal_RH_MIH = py4hw.Wire(self,'W_ReadVal_RH_MIH',8)
        W_LPM_req_CB_RH = py4hw.Wire(self,'W_LPM_req_CB_RH',1)
        W_SPM_req_CB_RH = py4hw.Wire(self,'W_SPM_req_CB_RH',2)

        self.W_R0_BUFFER_IN_MIH_RH = py4hw.Wire(self,'W_R0_BUFFER_IN_MIH_RH',8)
        self.W_R1_BUFFER_IN_MIH_RH = py4hw.Wire(self,'W_R1_BUFFER_IN_MIH_RH',8)
        self.W_SPM_Done_RH_CB = py4hw.Wire(self,'W_SPM_Done_RH_CB',1)
        W_R0_BUFFER_IN_MIH_RH = py4hw.Wire(self,'W_R0_BUFFER_IN_MIH_RH',8)
        W_R1_BUFFER_IN_MIH_RH = py4hw.Wire(self,'W_R1_BUFFER_IN_MIH_RH',8)

        W_VALUE_OUT = py4hw.Wire(self,'W_VALUE_OUT',8)
        


        # MemoryInterfaceHandler wires
        #self.w_mem_register_out = py4hw.Wire(self, 'w_mem_register_out', 8)
        w_mem_incdec_MIH_CB = py4hw.Wire(self, 'w_mem_incdec_MIH_CB', 3)
        w_mem_instr_MIH_CB = py4hw.Wire(self, 'w_mem_instr_MIH_CB', 5)
        #self.w_general_input = py4hw.Wire(self, 'w_general_input', 8)
        w_address_ZL_MIH_RH = py4hw.Wire(self,'w_address_ZL_MIH_RH',8)
        w_address_ZH_MIH_RH = py4hw.Wire(self,'w_address_ZH_MIH_RH',8)
        W_Pc_valL_RH_MIH = py4hw.Wire(self,'W_Pc_valL_RH_MIH',8)
        W_Pc_valH_RH_MIH = py4hw.Wire(self,'W_Pc_valH_RH_MIH',8)

        # Write-back address: explicit register address driven by ControlBox
        W_WB_addr_CB_MIH = py4hw.Wire(self, 'w_wb_addr', 8)

        # ROM handler wires
        W_Rom_address_RH_MIH = py4hw.Wire(self, 'W_Rom_address_RH_MIH', 16)
        W_Rom_value_RH_MIH = py4hw.Wire(self, 'W_Rom_value_RH_MIH', 16)
        W_PCL_LOAD_VAL_CB_RH = py4hw.Wire(self,'W_PCL_LOAD_VAL_CB_RH',8)
        W_PCH_LOAD_VAL_CB_RH = py4hw.Wire(self,'W_PCH_LOAD_VAL_CB_RH',8)
        W_Fetch_Address_CB_RH = py4hw.Wire(self,'W_Fetch_Address_CB_RH',1)
        W_Address_fetched_RH_CB = py4hw.Wire(self,'W_Address_fetched_RH_CB',1)

        # No use 

        W_Write_Enable_CB_OB = py4hw.Wire(self,'W_Write_Enable_CB_OB',1)

        # -------------------------
        # Interrupt wires
        # -------------------------
        # Entrance signal: MainFSM pulses this to hand off to InterruptFSM
        # (see ControlBox — InterruptFSM.Interrupt_Done now really is wired
        # back to MainFSM internally, no external stub needed anymore).
        self.W_Interrupt_Entrance_CB = py4hw.Wire(self, 'W_Interrupt_Entrance_CB', 1)

        # InterruptFSM's direct SREG-I-flag override, to MemoryInterfaceHandler.
        self.W_I_Force_WE_CB_MIH = py4hw.Wire(self, 'W_I_Force_WE_CB_MIH', 1)
        self.W_I_Force_Value_CB_MIH = py4hw.Wire(self, 'W_I_Force_Value_CB_MIH', 1)


        # -------------------------
        # Sub-components
        # -------------------------
        RomHandler(self, 'RomHandler',
            RH_mem= ins_mem,
            RH_instructionOut= W_Instruction_RH_ID,
            RH_Address_Out= W_Rom_address_RH_MIH,
            RH_Value_Out= W_Rom_value_RH_MIH, 
            RH_Pc_valL=W_Pc_valL_RH_MIH,
            RH_Pc_valH=W_Pc_valH_RH_MIH,
            RH_Instruction_fetched=W_Instruction_fetched_RH_CB,
            RH_Executed_Jump=W_Executed_Jump_CB,
            RH_Load_Z=W_LOAD_Z_CB_RH,
            RH_address_ZL=w_address_ZL_MIH_RH,
            RH_address_ZH=w_address_ZH_MIH_RH,
            RH_Load_K=W_LOAD_K_CB_RH,
            RH_K_select=W_Select_K_CB_RH,
            RH_K7=W_k7_ID_RH,
            RH_K12=W_k12_ID_RH,
            RH_K7_22=W_k7_22_ID_RH,
            RH_Load_Jump=W_LOAD_JUMP_CB_RH,
            RH_relative_Absolute=W_Relative_Absolute_CB_RH,
            RH_Load_Byte=W_Load_byte_CB,
            RH_PCL_LOAD_VAL=W_PCL_LOAD_VAL_CB_RH,
            RH_PCH_LOAD_VAL=W_PCH_LOAD_VAL_CB_RH,
            RH_Fetch_next_instruction=W_Fetch_next_instruction_CB_RH,
            RH_JumpWidth=W_JumpWidth_CB_RH,
            RH_Load_PCL=W_LOAD_PCL_CB_RH,
            RH_Load_PCH=W_LOAD_PCH_CB_RH,
            RH_fetch_address=W_Fetch_Address_CB_RH,
            RH_Address_fetched=W_Address_fetched_RH_CB,
            RH_reset_address=reset_address,
            #--- SPM and LPM ---
            RH_WriteVal=W_WriteVal_RH_MIH,
            RH_ReadVal=W_ReadVal_RH_MIH,
            RH_LPM_req=W_LPM_req_CB_RH,
            RH_SPM_req=W_SPM_req_CB_RH,
            RH_R0_BUFFER_IN=W_R0_BUFFER_IN_MIH_RH,
            RH_R1_BUFFER_IN=W_R1_BUFFER_IN_MIH_RH,
        )

        Instruction_decoder(self, 'InstructionDecoder',
            ID_Instruction=W_Instruction_RH_ID,
            ID_Instruction_fetched=W_Instruction_fetched_RH_CB,
            ID_InstructionCode=W_CODE_ID_CB,
            ID_Rd=W_RD_ID_MIH,
            ID_Rr=W_RR_ID_MIH,
            ID_K8=W_K8_ID_OB,
            ID_k12=W_k12_ID_RH,
            ID_K6=W_K6_ID_OB,
            ID_K4=W_K4_ID_,
            ID_k16=W_k12_ID_RH,
            ID_k7= W_k7_ID_RH,
            ID_k7_22=W_k7_22_ID_RH,
            ID_b=W_b_ID_ALU,
            ID_s=W_s_ID_ALU,
            ID_A5=W_A5_ID_MIH,
            ID_A6=W_A6_ID_MIH,
            ID_q=W_q6_ID_MIH,
            ID_Instruction_decoded=W_Instruction_decoded_ID_CB
        )

        control_Box(self, 'ControlBox',
            CB_Instruction=W_CODE_ID_CB,              
            CB_Resp=W_Resp_MIH_CB,                     
            CB_Branch=W_Branch_ALU_CB,                 
            CB_Skip=W_Skip_ALU_CB,                     
            CB_Interrupt=Interrupt,                    
            CB_Instruction_fetched=W_Instruction_fetched_RH_CB,   
            CB_Instruction_decoded=W_Instruction_decoded_ID_CB,   
            CB_Executed_Jump=W_Executed_Jump_CB,       
            CB_Address_fetched=W_Address_fetched_RH_CB,
            CB_LoadSelectMux=W_LoadSelect_MUX_CB_MIH,  
            CB_LoadingMux=W_Loading_MUX_CB_MIH,        
            CB_Input_Select=W_Input_Select_CB_MIH,     
            CB_WE_MEMORY=W_WE_OpBuf_CB_MIH,                  
            CB_Read_Write=W_read_write,                
            CB_mem_instr=w_mem_instr_MIH_CB,           
            CB_IncDec=w_mem_incdec_MIH_CB,             
            CB_InputSelect=W_Input_Select_CB_OB,       
            CB_WE_Buffer=W_BufferWe_CB_OB,            
            CB_Load_Z=W_LOAD_Z_CB_RH,                  
            CB_Load_K=W_LOAD_K_CB_RH,
            CB_K_Select = W_Select_K_CB_RH,                  
            CB_Load_Jump=W_LOAD_JUMP_CB_RH,            
            CB_relative_Absolute=W_Relative_Absolute_CB_RH,  
            CB_Load_Byte=W_Load_byte_CB,               
            CB_Fetch_next_instruction=W_Fetch_next_instruction_CB_RH,  
            CB_Fetch_Address=W_Fetch_Address_CB_RH,    
            CB_WB_Addr=W_WB_addr_CB_MIH,               
            CB_JumpWidth=W_JumpWidth_CB_RH,            
            CB_LOAD_PCL=W_LOAD_PCL_CB_RH,              
            CB_LOAD_PCH=W_LOAD_PCH_CB_RH,      
            CB_LPM_req=W_LPM_req_CB_RH,
            CB_SPM_req=W_SPM_req_CB_RH,
        )

        OperandBuffer(
            self, 'OperandBuffer',
            OB_DATA_IN=W_DataInput_MIH_OB,
            OB_K=W_K8_ID_OB,
            OB_WE=W_BufferWe_CB_OB,
            OB_Reset=reset,
            OB_InputSelectBuffer=W_Input_Select_CB_OB,
            OB_A0=W_ImputRegA0_OB_ALU,
            OB_A1=W_ImputRegA1_OB_ALU,
            OB_B0=W_ImputRegB0_OB_ALU,
            OB_B1=W_ImputRegB1_OB_ALU,
            OB_IOout=W_IOBuffer_MIH_OB
        )

        ALU(
            self, 'ALU',
            A0=W_ImputRegA0_OB_ALU,
            A1=W_ImputRegA1_OB_ALU,
            B0=W_ImputRegB0_OB_ALU,
            B1=W_ImputRegB1_OB_ALU,
            op=W_CODE_ID_CB,
            SREG_STATE=W_SREG_SL_ALU,
            BitPos=W_b_ID_ALU,
            IOreg=W_IOBuffer_MIH_OB,
            R0=W_OUTPUTByte0_ALU_MIH,
            R1=W_OUTPUTByte1_ALU_MIH,
            SREG_VAL=W_SREG_ALU_SL,
            eSREG_VAL=W_eSREG_ALU_SL,
            BRANCH=W_Branch_ALU_CB,
            SKIP=W_Skip_ALU_CB
        )

        MemoryInterfaceHandler(
            self, 'MemoryInterfaceHandler',
            reset=reset,
            WE=W_WE_OpBuf_CB_MIH,
            LoadSelectMux=W_LoadSelect_MUX_CB_MIH,
            LoadingMux=W_Loading_MUX_CB_MIH,
            IncDec=w_mem_incdec_MIH_CB,
            RomAddressValue=W_Rom_value_RH_MIH,
            ReadWrite=W_read_write,
            InputSelectMemory=W_Input_Select_CB_MIH,
            Mem_instruction=w_mem_instr_MIH_CB,
            RomAddress=W_Rom_address_RH_MIH,
            ResL=W_OUTPUTByte0_ALU_MIH,
            ResH=W_OUTPUTByte1_ALU_MIH,
            K_val_Input=W_K8_ID_OB,
            PCL_VAL_IN=W_Pc_valL_RH_MIH,
            PCH_VAL_IN=W_Pc_valH_RH_MIH,
            # Reuse the existing JumpWidth wire (MainFSM -> ControlBox ->
            # RomHandler, where it is received but never read) as the PC
            # push offset: 1 exactly when the current opcode is a 2-word
            # instruction, which is precisely the correction the pushed
            # return address needs for CALL (see MemoryInterfaceHandler).
            PC_Offset=W_JumpWidth_CB_RH,
            Rd=W_RD_ID_MIH,
            Rr=W_RR_ID_MIH,
            WbAddr=W_WB_addr_CB_MIH,
            memory=memory,
            RegisterOut=W_DataInput_MIH_OB,
            Resp=W_Resp_MIH_CB,
            address_ZL=w_address_ZL_MIH_RH,
            address_ZH=w_address_ZH_MIH_RH,
            Q=W_q6_ID_MIH,
            A_5bit=W_A5_ID_MIH,
            A_6bit=W_A6_ID_MIH,
            MIH_PCL_LOAD_VAL = W_PCL_LOAD_VAL_CB_RH,
            MIH_PCH_LOAD_VAL = W_PCH_LOAD_VAL_CB_RH,
            #---- SREG ----
            # ALU's flag update (SREG_VAL/eSREG_VAL) is merged directly into
            # MemoryInterfaceHandler's internal SREG register — the same
            # register that services IN/OUT accesses to I/O address 0x5F.
            # This keeps flag-updates and IN/OUT-visible SREG in sync
            # (previously they were two separate, unsynchronized registers).
            SREG_In=W_SREG_ALU_SL,
            eSREG_In=W_eSREG_ALU_SL,
            SREG_Reset=reset,
            SREG_Out=W_SREG_SL_ALU,
            # ---- LPM SPM ----
            R0_BUFFER_OUT= self.W_R0_BUFFER_IN_MIH_RH,
            R1_BUFFER_OUT= self.W_R1_BUFFER_IN_MIH_RH,
            ROM_VAL_IN=self.W_WriteVal_RH_MIH,
            ROM_VAL_OUT=self.W_ReadVal_RH_MIH,
            #---- Interrupts ----
            # Drive the CPU's external Interrupt_Enable pin straight from
            # MemoryInterfaceHandler's own SREG bit 7 — it already owns the
            # committed SREG register, so it's the natural source for this
            # instead of a separate tap elsewhere.
            I_Flag_Out=self.Interrupt_Enable,
            I_Force_WE=self.W_I_Force_WE_CB_MIH,
            I_Force_Value=self.W_I_Force_Value_CB_MIH,
            Bus_Passthrough_Ranges=Bus_Passthrough_Ranges,
            R0_BUFFER_OUT= W_R0_BUFFER_IN_MIH_RH,
            R1_BUFFER_OUT= W_R1_BUFFER_IN_MIH_RH,
            ROM_VAL_IN=W_WriteVal_RH_MIH,
            ROM_VAL_OUT=W_ReadVal_RH_MIH,
        )