// This file was automatically created by py4hw Verilog generator
module multicycleProcessor (
	input clk,
	input  reset,
	input  Interrupt,
	input [15:0] ins_mem_readdata,
	input  ins_mem_resp,
	input [7:0] memory_readdata,
	input  memory_resp,
	input  PROG_MOSI,
	input  PROG_SCK,
	output  Interrupt_Enable,
	output  ins_mem_read,
	output  ins_mem_write,
	output [15:0] ins_mem_writedata,
	output [13:0] ins_mem_address,
	output  ins_mem_instype,
	output  memory_read,
	output  memory_write,
	output [7:0] memory_writedata,
	output [15:0] memory_address,
	output  memory_instype,
	output  PROG_MISO);
wire [2:0] w_W_IncDec;
wire w_W_InputSelect;
wire [3:0] w_W_WE_Buffer;
wire w_W_Load_Z;
wire w_W_Load_K;
wire [1:0] w_W_K_Select;
wire w_W_Load_Jump;
wire w_W_relative_Absolute;
wire w_W_Load_Byte;
wire w_W_Fetch_next_instruction;
wire w_W_Fetch_Address;
wire [7:0] w_W_WB_Addr;
wire w_W_JumpWidth;
wire w_W_LOAD_PCL;
wire w_W_LOAD_PCH;
wire [1:0] w_W_LPM_req;
wire [1:0] w_W_SPM_req;
wire w_W_Interrupt_Entrance;
wire w_W_I_Force_WE;
wire w_W_I_Force_Value;
wire w_W_Resp;
wire w_W_ALU_Commit;
wire w_W_Branch;
wire w_W_Skip;
wire [15:0] w_W_Instruction;
wire w_W_Instruction_fetched;
wire w_W_Instruction_decoded;
wire w_W_Executed_Jump;
wire w_W_Address_fetched;
wire w_W_SPM_Done;
wire [2:0] w_W_LoadSelectMux;
wire [4:0] w_W_LoadingMux;
wire [4:0] w_W_Input_Select;
wire [5:0] w_W_WE_MEMORY;
wire [1:0] w_W_Read_Write;
wire [4:0] w_W_mem_instr;

Datapath_7f9e3ee8bce0 i_Datapath(.clk(clk),.reset(reset),.ins_mem_readdata(ins_mem_readdata),.ins_mem_resp(ins_mem_resp),.memory_readdata(memory_readdata),.memory_resp(memory_resp),.PROG_MOSI(PROG_MOSI),.PROG_SCK(PROG_SCK),.D_LoadSelectMux(w_W_LoadSelectMux),.D_LoadingMux(w_W_LoadingMux),.D_Input_Select(w_W_Input_Select),.D_WE_MEMORY(w_W_WE_MEMORY),.D_Read_Write(w_W_Read_Write),.D_mem_instr(w_W_mem_instr),.D_IncDec(w_W_IncDec),.D_InputSelect(w_W_InputSelect),.D_WE_Buffer(w_W_WE_Buffer),.D_Load_Z(w_W_Load_Z),.D_Load_K(w_W_Load_K),.D_K_Select(w_W_K_Select),.D_Load_Jump(w_W_Load_Jump),.D_relative_Absolute(w_W_relative_Absolute),.D_Load_Byte(w_W_Load_Byte),.D_Fetch_next_instruction(w_W_Fetch_next_instruction),.D_Fetch_Address(w_W_Fetch_Address),.D_WB_Addr(w_W_WB_Addr),.D_JumpWidth(w_W_JumpWidth),.D_LOAD_PCL(w_W_LOAD_PCL),.D_LOAD_PCH(w_W_LOAD_PCH),.D_LPM_req(w_W_LPM_req),.D_SPM_req(w_W_SPM_req),.D_I_Force_WE(w_W_I_Force_WE),.D_I_Force_Value(w_W_I_Force_Value),.D_ALU_Commit(w_W_ALU_Commit),.ins_mem_read(ins_mem_read),.ins_mem_write(ins_mem_write),.ins_mem_writedata(ins_mem_writedata),.ins_mem_address(ins_mem_address),.ins_mem_instype(ins_mem_instype),.memory_read(memory_read),.memory_write(memory_write),.memory_writedata(memory_writedata),.memory_address(memory_address),.memory_instype(memory_instype),.Interrupt_Enable(Interrupt_Enable),.PROG_MISO(PROG_MISO),.D_Resp(w_W_Resp),.D_Branch(w_W_Branch),.D_Skip(w_W_Skip),.D_Instruction(w_W_Instruction),.D_Instruction_fetched(w_W_Instruction_fetched),.D_Instruction_decoded(w_W_Instruction_decoded),.D_Executed_Jump(w_W_Executed_Jump),.D_Address_fetched(w_W_Address_fetched),.D_SPM_Done(w_W_SPM_Done));
control_Box_7f9e35be6900 i_ControlBox(.clk(clk),.CB_Instruction(w_W_Instruction),.CB_Resp(w_W_Resp),.CB_Branch(w_W_Branch),.CB_Skip(w_W_Skip),.CB_Interrupt(Interrupt),.CB_Instruction_fetched(w_W_Instruction_fetched),.CB_Instruction_decoded(w_W_Instruction_decoded),.CB_Executed_Jump(w_W_Executed_Jump),.CB_Address_fetched(w_W_Address_fetched),.CB_SPM_Done(w_W_SPM_Done),.CB_Reset(reset),.CB_LoadSelectMux(w_W_LoadSelectMux),.CB_LoadingMux(w_W_LoadingMux),.CB_Input_Select(w_W_Input_Select),.CB_WE_MEMORY(w_W_WE_MEMORY),.CB_Read_Write(w_W_Read_Write),.CB_mem_instr(w_W_mem_instr),.CB_IncDec(w_W_IncDec),.CB_InputSelect(w_W_InputSelect),.CB_WE_Buffer(w_W_WE_Buffer),.CB_Load_Z(w_W_Load_Z),.CB_Load_K(w_W_Load_K),.CB_Load_Jump(w_W_Load_Jump),.CB_relative_Absolute(w_W_relative_Absolute),.CB_Load_Byte(w_W_Load_Byte),.CB_Fetch_next_instruction(w_W_Fetch_next_instruction),.CB_Fetch_Address(w_W_Fetch_Address),.CB_WB_Addr(w_W_WB_Addr),.CB_JumpWidth(w_W_JumpWidth),.CB_LOAD_PCL(w_W_LOAD_PCL),.CB_LOAD_PCH(w_W_LOAD_PCH),.CB_K_Select(w_W_K_Select),.CB_LPM_req(w_W_LPM_req),.CB_SPM_req(w_W_SPM_req),.CB_Interrupt_Entrance(w_W_Interrupt_Entrance),.CB_I_Force_WE(w_W_I_Force_WE),.CB_I_Force_Value(w_W_I_Force_Value),.CB_ALU_Commit(w_W_ALU_Commit));
endmodule

// This file was automatically created by py4hw Verilog generator
module Datapath_7f9e3ee8bce0 (
	input clk,
	input  reset,
	input [15:0] ins_mem_readdata,
	input  ins_mem_resp,
	input [7:0] memory_readdata,
	input  memory_resp,
	input  PROG_MOSI,
	input  PROG_SCK,
	input [2:0] D_LoadSelectMux,
	input [4:0] D_LoadingMux,
	input [4:0] D_Input_Select,
	input [5:0] D_WE_MEMORY,
	input [1:0] D_Read_Write,
	input [4:0] D_mem_instr,
	input [2:0] D_IncDec,
	input  D_InputSelect,
	input [3:0] D_WE_Buffer,
	input  D_Load_Z,
	input  D_Load_K,
	input [1:0] D_K_Select,
	input  D_Load_Jump,
	input  D_relative_Absolute,
	input  D_Load_Byte,
	input  D_Fetch_next_instruction,
	input  D_Fetch_Address,
	input [7:0] D_WB_Addr,
	input  D_JumpWidth,
	input  D_LOAD_PCL,
	input  D_LOAD_PCH,
	input [1:0] D_LPM_req,
	input [1:0] D_SPM_req,
	input  D_I_Force_WE,
	input  D_I_Force_Value,
	input  D_ALU_Commit,
	output  ins_mem_read,
	output  ins_mem_write,
	output [15:0] ins_mem_writedata,
	output [13:0] ins_mem_address,
	output  ins_mem_instype,
	output  memory_read,
	output  memory_write,
	output [7:0] memory_writedata,
	output [15:0] memory_address,
	output  memory_instype,
	output  Interrupt_Enable,
	output  PROG_MISO,
	output  D_Resp,
	output  D_Branch,
	output  D_Skip,
	output [15:0] D_Instruction,
	output  D_Instruction_fetched,
	output  D_Instruction_decoded,
	output  D_Executed_Jump,
	output  D_Address_fetched,
	output  D_SPM_Done);
wire w_W_SREG_N_maskbit;
wire w_W_SREG_V_maskbit;
wire w_W_SREG_S_maskbit;
wire w_W_SREG_H_maskbit;
wire w_W_SREG_T_maskbit;
wire w_W_SREG_I_maskbit;
wire w_W_SREG_C_valuebit;
wire w_W_SREG_Z_valuebit;
wire w_W_SREG_N_valuebit;
wire w_W_SREG_V_valuebit;
wire w_W_SREG_S_valuebit;
wire w_W_SREG_H_valuebit;
wire w_W_SREG_T_valuebit;
wire w_W_SREG_I_valuebit;
wire [3:0] w_W_const_1;
wire [3:0] w_W_const_2;
wire [3:0] w_W_const_3;
wire [3:0] w_W_const_4;
wire [3:0] w_W_const_5;
wire [15:0] w_W_Instruction_RH_ID;
wire [4:0] w_W_RD_ID_MIH;
wire [4:0] w_W_RR_ID_MIH;
wire [7:0] w_W_K8_ID;
wire [5:0] w_W_K6_ID;
wire [3:0] w_W_K4_ID;
wire [6:0] w_W_k7_ID_RH;
wire [11:0] w_W_k12_ID_RH;
wire [6:0] w_W_k7_22_ID_RH;
wire [2:0] w_W_b_ID_ALU;
wire [2:0] w_W_s_ID;
wire [4:0] w_W_A5_ID_MIH;
wire [5:0] w_W_A6_ID_MIH;
wire [5:0] w_W_q6_ID_MIH;
wire [7:0] w_W_OUTPUTByte0_ALU_MIH;
wire [7:0] w_W_OUTPUTByte1_ALU_MIH;
wire [7:0] w_W_SREG_ALU_VAL;
wire [7:0] w_W_eSREG_ALU_VAL;
wire [7:0] w_W_DataInput_MIH_REGS;
wire [15:0] w_W_Rom_address_RH_MIH;
wire [15:0] w_W_Rom_value_RH_MIH;
wire [7:0] w_w_address_ZL_MIH_RH;
wire [7:0] w_w_address_ZH_MIH_RH;
wire [7:0] w_W_PCL_LOAD_VAL_CB_RH;
wire [7:0] w_W_PCH_LOAD_VAL_CB_RH;
wire [7:0] w_W_WriteVal_RH_MIH;
wire [7:0] w_W_ReadVal_RH_MIH;
wire [7:0] w_W_R0_BUFFER_IN_MIH_RH;
wire [7:0] w_W_R1_BUFFER_IN_MIH_RH;
wire [15:0] w_W_PC_ValueOut;
wire w_W_PC_Load;
wire [15:0] w_W_PC_Q;
wire [7:0] w_W_PCL_VAL_IN;
wire [7:0] w_W_PCH_VAL_IN;
wire [15:0] w_W_IR_Q;
wire [15:0] w_W_MAR_ValueOut;
wire [15:0] w_W_MAR_Q;
wire w_W_Const1;
wire [7:0] w_W_AL_Q;
wire [7:0] w_W_AH_Q;
wire [7:0] w_W_BL_Q;
wire [7:0] w_W_BH_Q;
wire [7:0] w_W_IO_Q;
wire w_W_en_AL;
wire w_W_en_AH;
wire w_W_en_BL;
wire w_W_en_BH;
wire w_W_en_IO;
wire [7:0] w_W_BL_d;
wire [7:0] w_W_SREG_WriteValue;
wire [7:0] w_W_SREG_WriteMask;
wire [7:0] w_W_SREG_ReadValue;
wire w_W_SREG_I_d;
wire w_W_SREG_I_en;
wire w_W_SREG_C_q;
wire w_W_SREG_Z_q;
wire w_W_SREG_N_q;
wire w_W_SREG_V_q;
wire w_W_SREG_S_q;
wire w_W_SREG_H_q;
wire w_W_SREG_T_q;
wire w_W_SREG_C_maskbit;
wire w_W_SREG_Z_maskbit;

RomHandler_7f9e3eea6300 i_RomHandler(.clk(clk),.ins_readdata(ins_mem_readdata),.ins_resp(ins_mem_resp),.Load_Z(D_Load_Z),.address_ZL(w_w_address_ZL_MIH_RH),.address_ZH(w_w_address_ZH_MIH_RH),.Load_K(D_Load_K),.K_select(D_K_Select),.K7(w_W_k7_ID_RH),.K12(w_W_k12_ID_RH),.K7_22(w_W_k7_22_ID_RH),.Load_Jump(D_Load_Jump),.relative_Absolute(D_relative_Absolute),.Fetch_next_instruction(D_Fetch_next_instruction),.PC_ValIn(w_W_PC_Q),.reset(reset),.JumpWidth(D_JumpWidth),.Load_PCL(D_LOAD_PCL),.Load_PCH(D_LOAD_PCH),.PCL_LOAD_VAL(w_W_PCL_LOAD_VAL_CB_RH),.PCH_LOAD_VAL(w_W_PCH_LOAD_VAL_CB_RH),.fetch_address(D_Fetch_Address),.Load_Byte(D_Load_Byte),.WriteVal(w_W_WriteVal_RH_MIH),.LPM_req(D_LPM_req),.SPM_req(D_SPM_req),.R0_BUFFER_IN(w_W_R0_BUFFER_IN_MIH_RH),.R1_BUFFER_IN(w_W_R1_BUFFER_IN_MIH_RH),.PROG_MOSI(PROG_MOSI),.PROG_SCK(PROG_SCK),.ins_read(ins_mem_read),.ins_write(ins_mem_write),.ins_address(ins_mem_address),.ins_writedata(ins_mem_writedata),.ins_instype(ins_mem_instype),.instructionOut(w_W_Instruction_RH_ID),.Address_Out(w_W_Rom_address_RH_MIH),.Value_Out(w_W_Rom_value_RH_MIH),.Instruction_fetched(D_Instruction_fetched),.Executed_Jump(D_Executed_Jump),.PC_ValueOut(w_W_PC_ValueOut),.PC_Load(w_W_PC_Load),.Address_fetched(D_Address_fetched),.ReadVal(w_W_ReadVal_RH_MIH),.SPM_Done(D_SPM_Done),.PROG_MISO(PROG_MISO));
Instruction_decoder_7f9e35c19580 i_InstructionDecoder(.clk(clk),.Instruction(w_W_IR_Q),.Instruction_fetched(D_Instruction_fetched),.reset(reset),.InstructionCode(D_Instruction),.Rd(w_W_RD_ID_MIH),.Rr(w_W_RR_ID_MIH),.K8(w_W_K8_ID),.K6(w_W_K6_ID),.K4(w_W_K4_ID),.k7(w_W_k7_ID_RH),.k12(w_W_k12_ID_RH),.k7_22(w_W_k7_22_ID_RH),.b(w_W_b_ID_ALU),.s(w_W_s_ID),.A5(w_W_A5_ID_MIH),.A6(w_W_A6_ID_MIH),.q(w_W_q6_ID_MIH),.Instruction_decoded(D_Instruction_decoded));
ALU_STRUC_7f9e3eea7c50 i_ALU(.reset(reset),.A0(w_W_AL_Q),.A1(w_W_AH_Q),.B0(w_W_BL_Q),.B1(w_W_BH_Q),.op(D_Instruction),.SREG_STATE(w_W_SREG_ReadValue),.BitPos(w_W_b_ID_ALU),.IOreg(w_W_IO_Q),.R0(w_W_OUTPUTByte0_ALU_MIH),.R1(w_W_OUTPUTByte1_ALU_MIH),.SREG_VAL(w_W_SREG_ALU_VAL),.eSREG_VAL(w_W_eSREG_ALU_VAL),.BRANCH(D_Branch),.SKIP(D_Skip));
MemoryInterfaceHandler_7f9e35bbad50 i_MemoryInterfaceHandler(.clk(clk),.memory_readdata(memory_readdata),.memory_resp(memory_resp),.reset(reset),.WE(D_WE_MEMORY),.LoadSelectMux(D_LoadSelectMux),.LoadingMux(D_LoadingMux),.IncDec(D_IncDec),.ReadWrite(D_Read_Write),.InputSelectMemory(D_Input_Select),.Mem_instruction(D_mem_instr),.RomAddress(w_W_Rom_address_RH_MIH),.RomAddressValue(w_W_Rom_value_RH_MIH),.PCL_VAL_IN(w_W_PCL_VAL_IN),.PCH_VAL_IN(w_W_PCH_VAL_IN),.PC_Offset(D_JumpWidth),.ResL(w_W_OUTPUTByte0_ALU_MIH),.ResH(w_W_OUTPUTByte1_ALU_MIH),.K_val_Input(w_W_K8_ID),.Q(w_W_q6_ID_MIH),.Rd(w_W_RD_ID_MIH),.Rr(w_W_RR_ID_MIH),.A_5bit(w_W_A5_ID_MIH),.A_6bit(w_W_A6_ID_MIH),.WbAddr(D_WB_Addr),.ROM_VAL(w_W_WriteVal_RH_MIH),.SREG_IN(w_W_SREG_ALU_VAL),.eSREG(w_W_eSREG_ALU_VAL),.ALU_Commit(D_ALU_Commit),.SREG_ReadValue(w_W_SREG_ReadValue),.memory_read(memory_read),.memory_write(memory_write),.memory_address(memory_address),.memory_writedata(memory_writedata),.memory_instype(memory_instype),.RegisterOut(w_W_DataInput_MIH_REGS),.Resp(D_Resp),.address_ZL(w_w_address_ZL_MIH_RH),.address_ZH(w_w_address_ZH_MIH_RH),.MIH_PCL_LOAD_VAL(w_W_PCL_LOAD_VAL_CB_RH),.MIH_PCH_LOAD_VAL(w_W_PCH_LOAD_VAL_CB_RH),.R0_BUFFER_out(w_W_R0_BUFFER_IN_MIH_RH),.R1_BUFFER_out(w_W_R1_BUFFER_IN_MIH_RH),.SREG_WriteValue(w_W_SREG_WriteValue),.SREG_WriteMask(w_W_SREG_WriteMask),.MAR_ValueOut(w_W_MAR_ValueOut));
Reg16RE i_PC(.clk(clk),.d(w_W_PC_ValueOut),.e(w_W_PC_Load),.r(reset),.q(w_W_PC_Q));
assign w_W_PCL_VAL_IN = w_W_PC_Q[7:0];
assign w_W_PCH_VAL_IN = w_W_PC_Q[15:8];
Reg16RE i_IR(.clk(clk),.d(w_W_Instruction_RH_ID),.e(D_Instruction_fetched),.r(reset),.q(w_W_IR_Q));
assign w_W_Const1 = 1;
Reg16RE i_MAR(.clk(clk),.d(w_W_MAR_ValueOut),.e(w_W_Const1),.r(reset),.q(w_W_MAR_Q));
assign w_W_const_1[3:0] = 1;
assign w_W_const_2[3:0] = 2;
assign w_W_const_3[3:0] = 3;
assign w_W_const_4[3:0] = 4;
assign w_W_const_5[3:0] = 5;
assign w_W_en_AL = (D_WE_Buffer == w_W_const_1)? 1:0;
assign w_W_en_AH = (D_WE_Buffer == w_W_const_2)? 1:0;
assign w_W_en_BL = (D_WE_Buffer == w_W_const_3)? 1:0;
assign w_W_en_BH = (D_WE_Buffer == w_W_const_4)? 1:0;
assign w_W_en_IO = (D_WE_Buffer == w_W_const_5)? 1:0;
Mux_7f9e35bd9670 i_mux_BL_d(.sel(D_InputSelect),.in0(w_W_K8_ID),.in1(w_W_DataInput_MIH_REGS),.r(w_W_BL_d));
Reg8RE i_AL(.clk(clk),.d(w_W_DataInput_MIH_REGS),.e(w_W_en_AL),.r(reset),.q(w_W_AL_Q));
Reg8RE i_AH(.clk(clk),.d(w_W_DataInput_MIH_REGS),.e(w_W_en_AH),.r(reset),.q(w_W_AH_Q));
Reg8RE i_BL(.clk(clk),.d(w_W_BL_d),.e(w_W_en_BL),.r(reset),.q(w_W_BL_Q));
Reg8RE i_BH(.clk(clk),.d(w_W_DataInput_MIH_REGS),.e(w_W_en_BH),.r(reset),.q(w_W_BH_Q));
Reg8RE i_IO(.clk(clk),.d(w_W_DataInput_MIH_REGS),.e(w_W_en_IO),.r(reset),.q(w_W_IO_Q));
assign w_W_SREG_C_maskbit = w_W_SREG_WriteMask[0:0];
assign w_W_SREG_C_valuebit = w_W_SREG_WriteValue[0:0];
Reg1RE i_SREG_C(.clk(clk),.d(w_W_SREG_C_valuebit),.e(w_W_SREG_C_maskbit),.r(reset),.q(w_W_SREG_C_q));
assign w_W_SREG_Z_maskbit = w_W_SREG_WriteMask[1:1];
assign w_W_SREG_Z_valuebit = w_W_SREG_WriteValue[1:1];
Reg1RE i_SREG_Z(.clk(clk),.d(w_W_SREG_Z_valuebit),.e(w_W_SREG_Z_maskbit),.r(reset),.q(w_W_SREG_Z_q));
assign w_W_SREG_N_maskbit = w_W_SREG_WriteMask[2:2];
assign w_W_SREG_N_valuebit = w_W_SREG_WriteValue[2:2];
Reg1RE i_SREG_N(.clk(clk),.d(w_W_SREG_N_valuebit),.e(w_W_SREG_N_maskbit),.r(reset),.q(w_W_SREG_N_q));
assign w_W_SREG_V_maskbit = w_W_SREG_WriteMask[3:3];
assign w_W_SREG_V_valuebit = w_W_SREG_WriteValue[3:3];
Reg1RE i_SREG_V(.clk(clk),.d(w_W_SREG_V_valuebit),.e(w_W_SREG_V_maskbit),.r(reset),.q(w_W_SREG_V_q));
assign w_W_SREG_S_maskbit = w_W_SREG_WriteMask[4:4];
assign w_W_SREG_S_valuebit = w_W_SREG_WriteValue[4:4];
Reg1RE i_SREG_S(.clk(clk),.d(w_W_SREG_S_valuebit),.e(w_W_SREG_S_maskbit),.r(reset),.q(w_W_SREG_S_q));
assign w_W_SREG_H_maskbit = w_W_SREG_WriteMask[5:5];
assign w_W_SREG_H_valuebit = w_W_SREG_WriteValue[5:5];
Reg1RE i_SREG_H(.clk(clk),.d(w_W_SREG_H_valuebit),.e(w_W_SREG_H_maskbit),.r(reset),.q(w_W_SREG_H_q));
assign w_W_SREG_T_maskbit = w_W_SREG_WriteMask[6:6];
assign w_W_SREG_T_valuebit = w_W_SREG_WriteValue[6:6];
Reg1RE i_SREG_T(.clk(clk),.d(w_W_SREG_T_valuebit),.e(w_W_SREG_T_maskbit),.r(reset),.q(w_W_SREG_T_q));
assign w_W_SREG_I_maskbit = w_W_SREG_WriteMask[7:7];
assign w_W_SREG_I_valuebit = w_W_SREG_WriteValue[7:7];
assign w_W_SREG_I_en = w_W_SREG_I_maskbit | D_I_Force_WE;
Mux_7f9e35be6210 i_SREG_I_d_mux(.sel(D_I_Force_WE),.in0(w_W_SREG_I_valuebit),.in1(D_I_Force_Value),.r(w_W_SREG_I_d));
Reg1RE i_SREG_I(.clk(clk),.d(w_W_SREG_I_d),.e(w_W_SREG_I_en),.r(reset),.q(Interrupt_Enable));
assign w_W_SREG_ReadValue ={Interrupt_Enable,w_W_SREG_T_q,w_W_SREG_H_q,w_W_SREG_S_q,w_W_SREG_V_q,w_W_SREG_N_q,w_W_SREG_Z_q,w_W_SREG_C_q};
endmodule

// This file was automatically created by py4hw Verilog generator
module RomHandler_7f9e3eea6300 (
	input clk,
	input [15:0] ins_readdata,
	input  ins_resp,
	input  Load_Z,
	input [7:0] address_ZL,
	input [7:0] address_ZH,
	input  Load_K,
	input [1:0] K_select,
	input [6:0] K7,
	input [11:0] K12,
	input [6:0] K7_22,
	input  Load_Jump,
	input  relative_Absolute,
	input  Fetch_next_instruction,
	input [15:0] PC_ValIn,
	input  reset,
	input  JumpWidth,
	input  Load_PCL,
	input  Load_PCH,
	input [7:0] PCL_LOAD_VAL,
	input [7:0] PCH_LOAD_VAL,
	input  fetch_address,
	input  Load_Byte,
	input [7:0] WriteVal,
	input [1:0] LPM_req,
	input [1:0] SPM_req,
	input [7:0] R0_BUFFER_IN,
	input [7:0] R1_BUFFER_IN,
	input  PROG_MOSI,
	input  PROG_SCK,
	output  reg  ins_read,
	output  reg  ins_write,
	output  reg [13:0] ins_address,
	output  reg [15:0] ins_writedata,
	output  reg  ins_instype,
	output  reg [15:0] instructionOut,
	output  reg [15:0] Address_Out,
	output  reg [15:0] Value_Out,
	output  reg  Instruction_fetched,
	output  reg  Executed_Jump,
	output  reg [15:0] PC_ValueOut,
	output  reg  PC_Load,
	output  reg  Address_fetched,
	output  reg [7:0] ReadVal,
	output  reg  SPM_Done,
	output  reg  PROG_MISO);
// Code generated from clock method
// wire/variable declaration
integer PC_BUFFER;
integer _pc_restore_pending;
integer _lpm_byte_pending;
integer _lpm_byte_high;
integer FSM;
integer latched_addr_word;
integer _prog_state;
integer _prog_shift_reg;
reg [5:0] _prog_bit_count;
reg [0:0] _prog_prev_sck;
reg [0:0] _prog_enabled;
reg [15:0] _prog_page_00;
reg [15:0] _prog_page_01;
reg [15:0] _prog_page_02;
reg [15:0] _prog_page_03;
reg [15:0] _prog_page_04;
reg [15:0] _prog_page_05;
reg [15:0] _prog_page_06;
reg [15:0] _prog_page_07;
reg [15:0] _prog_page_08;
reg [15:0] _prog_page_09;
reg [15:0] _prog_page_10;
reg [15:0] _prog_page_11;
reg [15:0] _prog_page_12;
reg [15:0] _prog_page_13;
reg [15:0] _prog_page_14;
reg [15:0] _prog_page_15;
reg [15:0] _prog_page_16;
reg [15:0] _prog_page_17;
reg [15:0] _prog_page_18;
reg [15:0] _prog_page_19;
reg [15:0] _prog_page_20;
reg [15:0] _prog_page_21;
reg [15:0] _prog_page_22;
reg [15:0] _prog_page_23;
reg [15:0] _prog_page_24;
reg [15:0] _prog_page_25;
reg [15:0] _prog_page_26;
reg [15:0] _prog_page_27;
reg [15:0] _prog_page_28;
reg [15:0] _prog_page_29;
reg [15:0] _prog_page_30;
reg [15:0] _prog_page_31;
reg [15:0] _prog_page_32;
reg [15:0] _prog_page_33;
reg [15:0] _prog_page_34;
reg [15:0] _prog_page_35;
reg [15:0] _prog_page_36;
reg [15:0] _prog_page_37;
reg [15:0] _prog_page_38;
reg [15:0] _prog_page_39;
reg [15:0] _prog_page_40;
reg [15:0] _prog_page_41;
reg [15:0] _prog_page_42;
reg [15:0] _prog_page_43;
reg [15:0] _prog_page_44;
reg [15:0] _prog_page_45;
reg [15:0] _prog_page_46;
reg [15:0] _prog_page_47;
reg [15:0] _prog_page_48;
reg [15:0] _prog_page_49;
reg [15:0] _prog_page_50;
reg [15:0] _prog_page_51;
reg [15:0] _prog_page_52;
reg [15:0] _prog_page_53;
reg [15:0] _prog_page_54;
reg [15:0] _prog_page_55;
reg [15:0] _prog_page_56;
reg [15:0] _prog_page_57;
reg [15:0] _prog_page_58;
reg [15:0] _prog_page_59;
reg [15:0] _prog_page_60;
reg [15:0] _prog_page_61;
reg [15:0] _prog_page_62;
reg [15:0] _prog_page_63;
integer _prog_miso_shift;
reg [0:0] _prog_reply_armed;
reg [0:0] _prog_last_miso_bit;
integer _prog_erase_addr;
integer _prog_write_page_addr;
reg [6:0] _prog_write_page_offset;
reg [0:0] _prog_saw_resp_low;
reg [0:0] _prog_pending_flash_valid;
integer _prog_pending_flash_addr;
reg [0:0] _prog_pending_flash_high;
reg [0:0] _prog_pending_reply_valid;
integer _prog_pending_reply_value;
integer _fuse_low;
integer _fuse_high;
integer _fuse_extended;
integer _prev_reset;
integer debug;
integer previous_state;
integer addr;
integer resp;
integer offset;
integer page_word;
integer mem_read;
integer mem_addr;
integer sck;
integer mosi;
integer prev_sck;
integer b0;
integer b1;
integer b2;
integer flash_addr;
integer flash_high;
integer word;
integer instruction;
integer ib0;
integer ib1;
integer ib2;
integer ib3;
integer word_in_page;
integer page;
integer bit;
integer just_released;
integer pc;
integer pc_load;
integer bootrst;
integer bootsz;
integer load_jump;
integer load_z;
integer load_k;
integer load_pcl;
integer load_pch;
integer rel_abs;
integer jumped;
integer z_val;
integer k_select_sel;
integer k_val;
integer full_addr;
integer restore_from_buffer;
integer fetched_instruction;
integer fetched_word;
integer out_val;
integer val;
integer z_address;
// initial
initial
begin
    PC_BUFFER=0;
    _pc_restore_pending=0;
    _lpm_byte_pending=0;
    _lpm_byte_high=0;
    FSM=0;
    latched_addr_word=0;
    _prog_state=0;
    _prog_shift_reg=0;
    _prog_bit_count=0;
    _prog_prev_sck=0;
    _prog_enabled=0;
    _prog_page_00=0;
    _prog_page_01=0;
    _prog_page_02=0;
    _prog_page_03=0;
    _prog_page_04=0;
    _prog_page_05=0;
    _prog_page_06=0;
    _prog_page_07=0;
    _prog_page_08=0;
    _prog_page_09=0;
    _prog_page_10=0;
    _prog_page_11=0;
    _prog_page_12=0;
    _prog_page_13=0;
    _prog_page_14=0;
    _prog_page_15=0;
    _prog_page_16=0;
    _prog_page_17=0;
    _prog_page_18=0;
    _prog_page_19=0;
    _prog_page_20=0;
    _prog_page_21=0;
    _prog_page_22=0;
    _prog_page_23=0;
    _prog_page_24=0;
    _prog_page_25=0;
    _prog_page_26=0;
    _prog_page_27=0;
    _prog_page_28=0;
    _prog_page_29=0;
    _prog_page_30=0;
    _prog_page_31=0;
    _prog_page_32=0;
    _prog_page_33=0;
    _prog_page_34=0;
    _prog_page_35=0;
    _prog_page_36=0;
    _prog_page_37=0;
    _prog_page_38=0;
    _prog_page_39=0;
    _prog_page_40=0;
    _prog_page_41=0;
    _prog_page_42=0;
    _prog_page_43=0;
    _prog_page_44=0;
    _prog_page_45=0;
    _prog_page_46=0;
    _prog_page_47=0;
    _prog_page_48=0;
    _prog_page_49=0;
    _prog_page_50=0;
    _prog_page_51=0;
    _prog_page_52=0;
    _prog_page_53=0;
    _prog_page_54=0;
    _prog_page_55=0;
    _prog_page_56=0;
    _prog_page_57=0;
    _prog_page_58=0;
    _prog_page_59=0;
    _prog_page_60=0;
    _prog_page_61=0;
    _prog_page_62=0;
    _prog_page_63=0;
    _prog_miso_shift=0;
    _prog_reply_armed=0;
    _prog_last_miso_bit=0;
    _prog_erase_addr=0;
    _prog_write_page_addr=0;
    _prog_write_page_offset=0;
    _prog_saw_resp_low=0;
    _prog_pending_flash_valid=0;
    _prog_pending_flash_addr=0;
    _prog_pending_flash_high=0;
    _prog_pending_reply_valid=0;
    _prog_pending_reply_value=0;
    _fuse_low=98;
    _fuse_high=217;
    _fuse_extended=255;
    _prev_reset=0;
    debug=1;
end
// process
always @(posedge clk)
begin
    previous_state=FSM;
    if (reset)
    begin
        FSM=0;
        PC_BUFFER=0;
        _pc_restore_pending=0;
        _lpm_byte_pending=0;
        _lpm_byte_high=0;
        latched_addr_word=0;
        instructionOut<=0;
        Address_Out<=0;
        Value_Out<=0;
        Instruction_fetched<=0;
        Executed_Jump<=0;
        Address_fetched<=0;
        ReadVal<=0;
        SPM_Done<=0;
        PC_ValueOut<=0;
        PC_Load<=0;
        _prev_reset=1;
        case (_prog_state)
        1: begin
        addr=_prog_erase_addr;
        ins_instype<=1;
        ins_read<=0;
        ins_address<=addr;
        ins_writedata<=65535;
        resp=ins_resp;
        if (resp==0)
        begin
            _prog_saw_resp_low=1;
        end
        if ((resp==1)&&_prog_saw_resp_low)
        begin
            ins_write<=0;
            _prog_saw_resp_low=0;
            _prog_erase_addr=_prog_erase_addr+1;
            if (_prog_erase_addr>=16384)
            begin
                _prog_state=0;
            end
        end
        else
        begin
            ins_write<=1;
        end
        PROG_MISO<=0;
    end
    2: begin
    offset=_prog_write_page_offset;
    addr=_prog_write_page_addr+offset;
    ins_instype<=1;
    ins_read<=0;
    ins_address<=addr;
    case (offset)
    0: page_word=_prog_page_00;
    1: page_word=_prog_page_01;
    2: page_word=_prog_page_02;
    3: page_word=_prog_page_03;
    4: page_word=_prog_page_04;
    5: page_word=_prog_page_05;
    6: page_word=_prog_page_06;
    7: page_word=_prog_page_07;
    8: page_word=_prog_page_08;
    9: page_word=_prog_page_09;
    10: page_word=_prog_page_10;
    11: page_word=_prog_page_11;
    12: page_word=_prog_page_12;
    13: page_word=_prog_page_13;
    14: page_word=_prog_page_14;
    15: page_word=_prog_page_15;
    16: page_word=_prog_page_16;
    17: page_word=_prog_page_17;
    18: page_word=_prog_page_18;
    19: page_word=_prog_page_19;
    20: page_word=_prog_page_20;
    21: page_word=_prog_page_21;
    22: page_word=_prog_page_22;
    23: page_word=_prog_page_23;
    24: page_word=_prog_page_24;
    25: page_word=_prog_page_25;
    26: page_word=_prog_page_26;
    27: page_word=_prog_page_27;
    28: page_word=_prog_page_28;
    29: page_word=_prog_page_29;
    30: page_word=_prog_page_30;
    31: page_word=_prog_page_31;
    32: page_word=_prog_page_32;
    33: page_word=_prog_page_33;
    34: page_word=_prog_page_34;
    35: page_word=_prog_page_35;
    36: page_word=_prog_page_36;
    37: page_word=_prog_page_37;
    38: page_word=_prog_page_38;
    39: page_word=_prog_page_39;
    40: page_word=_prog_page_40;
    41: page_word=_prog_page_41;
    42: page_word=_prog_page_42;
    43: page_word=_prog_page_43;
    44: page_word=_prog_page_44;
    45: page_word=_prog_page_45;
    46: page_word=_prog_page_46;
    47: page_word=_prog_page_47;
    48: page_word=_prog_page_48;
    49: page_word=_prog_page_49;
    50: page_word=_prog_page_50;
    51: page_word=_prog_page_51;
    52: page_word=_prog_page_52;
    53: page_word=_prog_page_53;
    54: page_word=_prog_page_54;
    55: page_word=_prog_page_55;
    56: page_word=_prog_page_56;
    57: page_word=_prog_page_57;
    58: page_word=_prog_page_58;
    59: page_word=_prog_page_59;
    60: page_word=_prog_page_60;
    61: page_word=_prog_page_61;
    62: page_word=_prog_page_62;
    63: page_word=_prog_page_63;
    default:page_word=0;
endcase
ins_writedata<=page_word;
resp=ins_resp;
if (resp==0)
begin
    _prog_saw_resp_low=1;
end
if ((resp==1)&&_prog_saw_resp_low)
begin
    ins_write<=0;
    _prog_saw_resp_low=0;
    _prog_write_page_offset=_prog_write_page_offset+1;
    if (_prog_write_page_offset>=64)
    begin
        _prog_state=0;
    end
end
else
begin
    ins_write<=1;
end
PROG_MISO<=0;
end
default:begin
mem_read=0;
mem_addr=0;
sck=PROG_SCK;
mosi=PROG_MOSI;
prev_sck=_prog_prev_sck;
_prog_prev_sck=sck;
if ((sck==1)&&(prev_sck==0))
begin
_prog_shift_reg=((_prog_shift_reg<<1)|(mosi&1))&4294967295;
_prog_bit_count=_prog_bit_count+1;
if (_prog_bit_count==16)
begin
    b0=(_prog_shift_reg>>8)&255;
    b1=_prog_shift_reg&255;
    if ((b0==172)&&(b1==83))
    begin
        _prog_pending_reply_valid=1;
        _prog_pending_reply_value=83;
    end
end
else
begin
    if ((_prog_bit_count==17)&&_prog_pending_reply_valid)
    begin
        _prog_miso_shift=_prog_pending_reply_value;
        _prog_reply_armed=1;
        _prog_pending_reply_valid=0;
    end
    else
    begin
        case (_prog_bit_count)
        24: begin
        b0=(_prog_shift_reg>>16)&255;
        b1=(_prog_shift_reg>>8)&255;
        b2=(_prog_shift_reg>>0)&255;
        if (b0==240)
        begin
            _prog_pending_reply_valid=1;
            if (_prog_state!=0)
            begin
                _prog_pending_reply_value=1;
            end
            else
            begin
                _prog_pending_reply_value=0;
            end
        end
        else
        begin
            if ((b0==80)&&(b1==0))
            begin
                _prog_pending_reply_valid=1;
                _prog_pending_reply_value=_fuse_low;
            end
            else
            begin
                if ((b0==88)&&(b1==8))
                begin
                    _prog_pending_reply_valid=1;
                    _prog_pending_reply_value=_fuse_high;
                end
                else
                begin
                    if ((b0==80)&&(b1==8))
                    begin
                        _prog_pending_reply_valid=1;
                        _prog_pending_reply_value=_fuse_extended;
                    end
                    else
                    begin
                        if ((b0==32)||(b0==40))
                        begin
                            addr=((b1<<8)|b2)&16383;
                            mem_read=1;
                            mem_addr=addr;
                            _prog_pending_flash_valid=1;
                            _prog_pending_flash_addr=addr;
                            _prog_pending_flash_high=b0==40;
                        end
                    end
                end
            end
        end
    end
    25: if (_prog_pending_flash_valid)
    begin
        flash_addr=_prog_pending_flash_addr;
        flash_high=_prog_pending_flash_high;
        _prog_pending_flash_valid=0;
        word=ins_readdata;
        if (flash_high)
        begin
            _prog_miso_shift=(word>>8)&255;
        end
        else
        begin
            _prog_miso_shift=word&255;
        end
        _prog_reply_armed=1;
    end
    else
    begin
        if (_prog_pending_reply_valid)
        begin
            _prog_miso_shift=_prog_pending_reply_value;
            _prog_reply_armed=1;
            _prog_pending_reply_valid=0;
        end
    end
    default:;
endcase
end
end
if (_prog_bit_count==32)
begin
instruction=_prog_shift_reg;
ib0=(instruction>>24)&255;
ib1=(instruction>>16)&255;
ib2=(instruction>>8)&255;
ib3=instruction&255;
if ((ib0==172)&&(ib1==83))
begin
_prog_enabled=1;
end
else
begin
if (_prog_enabled&&((ib0==172)&&(ib1==128)))
begin
    _prog_erase_addr=0;
    _prog_state=1;
    _prog_saw_resp_low=0;
    _prog_bit_count=0;
    _prog_shift_reg=0;
    _prog_reply_armed=0;
    _prog_prev_sck=0;
end
else
begin
    if (_prog_enabled&&(ib0==64))
    begin
        word_in_page=ib2&63;
        case (word_in_page)
        0: _prog_page_00=(_prog_page_00&65280)|ib3;
        1: _prog_page_01=(_prog_page_01&65280)|ib3;
        2: _prog_page_02=(_prog_page_02&65280)|ib3;
        3: _prog_page_03=(_prog_page_03&65280)|ib3;
        4: _prog_page_04=(_prog_page_04&65280)|ib3;
        5: _prog_page_05=(_prog_page_05&65280)|ib3;
        6: _prog_page_06=(_prog_page_06&65280)|ib3;
        7: _prog_page_07=(_prog_page_07&65280)|ib3;
        8: _prog_page_08=(_prog_page_08&65280)|ib3;
        9: _prog_page_09=(_prog_page_09&65280)|ib3;
        10: _prog_page_10=(_prog_page_10&65280)|ib3;
        11: _prog_page_11=(_prog_page_11&65280)|ib3;
        12: _prog_page_12=(_prog_page_12&65280)|ib3;
        13: _prog_page_13=(_prog_page_13&65280)|ib3;
        14: _prog_page_14=(_prog_page_14&65280)|ib3;
        15: _prog_page_15=(_prog_page_15&65280)|ib3;
        16: _prog_page_16=(_prog_page_16&65280)|ib3;
        17: _prog_page_17=(_prog_page_17&65280)|ib3;
        18: _prog_page_18=(_prog_page_18&65280)|ib3;
        19: _prog_page_19=(_prog_page_19&65280)|ib3;
        20: _prog_page_20=(_prog_page_20&65280)|ib3;
        21: _prog_page_21=(_prog_page_21&65280)|ib3;
        22: _prog_page_22=(_prog_page_22&65280)|ib3;
        23: _prog_page_23=(_prog_page_23&65280)|ib3;
        24: _prog_page_24=(_prog_page_24&65280)|ib3;
        25: _prog_page_25=(_prog_page_25&65280)|ib3;
        26: _prog_page_26=(_prog_page_26&65280)|ib3;
        27: _prog_page_27=(_prog_page_27&65280)|ib3;
        28: _prog_page_28=(_prog_page_28&65280)|ib3;
        29: _prog_page_29=(_prog_page_29&65280)|ib3;
        30: _prog_page_30=(_prog_page_30&65280)|ib3;
        31: _prog_page_31=(_prog_page_31&65280)|ib3;
        32: _prog_page_32=(_prog_page_32&65280)|ib3;
        33: _prog_page_33=(_prog_page_33&65280)|ib3;
        34: _prog_page_34=(_prog_page_34&65280)|ib3;
        35: _prog_page_35=(_prog_page_35&65280)|ib3;
        36: _prog_page_36=(_prog_page_36&65280)|ib3;
        37: _prog_page_37=(_prog_page_37&65280)|ib3;
        38: _prog_page_38=(_prog_page_38&65280)|ib3;
        39: _prog_page_39=(_prog_page_39&65280)|ib3;
        40: _prog_page_40=(_prog_page_40&65280)|ib3;
        41: _prog_page_41=(_prog_page_41&65280)|ib3;
        42: _prog_page_42=(_prog_page_42&65280)|ib3;
        43: _prog_page_43=(_prog_page_43&65280)|ib3;
        44: _prog_page_44=(_prog_page_44&65280)|ib3;
        45: _prog_page_45=(_prog_page_45&65280)|ib3;
        46: _prog_page_46=(_prog_page_46&65280)|ib3;
        47: _prog_page_47=(_prog_page_47&65280)|ib3;
        48: _prog_page_48=(_prog_page_48&65280)|ib3;
        49: _prog_page_49=(_prog_page_49&65280)|ib3;
        50: _prog_page_50=(_prog_page_50&65280)|ib3;
        51: _prog_page_51=(_prog_page_51&65280)|ib3;
        52: _prog_page_52=(_prog_page_52&65280)|ib3;
        53: _prog_page_53=(_prog_page_53&65280)|ib3;
        54: _prog_page_54=(_prog_page_54&65280)|ib3;
        55: _prog_page_55=(_prog_page_55&65280)|ib3;
        56: _prog_page_56=(_prog_page_56&65280)|ib3;
        57: _prog_page_57=(_prog_page_57&65280)|ib3;
        58: _prog_page_58=(_prog_page_58&65280)|ib3;
        59: _prog_page_59=(_prog_page_59&65280)|ib3;
        60: _prog_page_60=(_prog_page_60&65280)|ib3;
        61: _prog_page_61=(_prog_page_61&65280)|ib3;
        62: _prog_page_62=(_prog_page_62&65280)|ib3;
        63: _prog_page_63=(_prog_page_63&65280)|ib3;
        default:;
    endcase
end
else
begin
    if (_prog_enabled&&(ib0==72))
    begin
        word_in_page=ib2&63;
        case (word_in_page)
        0: _prog_page_00=(_prog_page_00&255)|(ib3<<8);
        1: _prog_page_01=(_prog_page_01&255)|(ib3<<8);
        2: _prog_page_02=(_prog_page_02&255)|(ib3<<8);
        3: _prog_page_03=(_prog_page_03&255)|(ib3<<8);
        4: _prog_page_04=(_prog_page_04&255)|(ib3<<8);
        5: _prog_page_05=(_prog_page_05&255)|(ib3<<8);
        6: _prog_page_06=(_prog_page_06&255)|(ib3<<8);
        7: _prog_page_07=(_prog_page_07&255)|(ib3<<8);
        8: _prog_page_08=(_prog_page_08&255)|(ib3<<8);
        9: _prog_page_09=(_prog_page_09&255)|(ib3<<8);
        10: _prog_page_10=(_prog_page_10&255)|(ib3<<8);
        11: _prog_page_11=(_prog_page_11&255)|(ib3<<8);
        12: _prog_page_12=(_prog_page_12&255)|(ib3<<8);
        13: _prog_page_13=(_prog_page_13&255)|(ib3<<8);
        14: _prog_page_14=(_prog_page_14&255)|(ib3<<8);
        15: _prog_page_15=(_prog_page_15&255)|(ib3<<8);
        16: _prog_page_16=(_prog_page_16&255)|(ib3<<8);
        17: _prog_page_17=(_prog_page_17&255)|(ib3<<8);
        18: _prog_page_18=(_prog_page_18&255)|(ib3<<8);
        19: _prog_page_19=(_prog_page_19&255)|(ib3<<8);
        20: _prog_page_20=(_prog_page_20&255)|(ib3<<8);
        21: _prog_page_21=(_prog_page_21&255)|(ib3<<8);
        22: _prog_page_22=(_prog_page_22&255)|(ib3<<8);
        23: _prog_page_23=(_prog_page_23&255)|(ib3<<8);
        24: _prog_page_24=(_prog_page_24&255)|(ib3<<8);
        25: _prog_page_25=(_prog_page_25&255)|(ib3<<8);
        26: _prog_page_26=(_prog_page_26&255)|(ib3<<8);
        27: _prog_page_27=(_prog_page_27&255)|(ib3<<8);
        28: _prog_page_28=(_prog_page_28&255)|(ib3<<8);
        29: _prog_page_29=(_prog_page_29&255)|(ib3<<8);
        30: _prog_page_30=(_prog_page_30&255)|(ib3<<8);
        31: _prog_page_31=(_prog_page_31&255)|(ib3<<8);
        32: _prog_page_32=(_prog_page_32&255)|(ib3<<8);
        33: _prog_page_33=(_prog_page_33&255)|(ib3<<8);
        34: _prog_page_34=(_prog_page_34&255)|(ib3<<8);
        35: _prog_page_35=(_prog_page_35&255)|(ib3<<8);
        36: _prog_page_36=(_prog_page_36&255)|(ib3<<8);
        37: _prog_page_37=(_prog_page_37&255)|(ib3<<8);
        38: _prog_page_38=(_prog_page_38&255)|(ib3<<8);
        39: _prog_page_39=(_prog_page_39&255)|(ib3<<8);
        40: _prog_page_40=(_prog_page_40&255)|(ib3<<8);
        41: _prog_page_41=(_prog_page_41&255)|(ib3<<8);
        42: _prog_page_42=(_prog_page_42&255)|(ib3<<8);
        43: _prog_page_43=(_prog_page_43&255)|(ib3<<8);
        44: _prog_page_44=(_prog_page_44&255)|(ib3<<8);
        45: _prog_page_45=(_prog_page_45&255)|(ib3<<8);
        46: _prog_page_46=(_prog_page_46&255)|(ib3<<8);
        47: _prog_page_47=(_prog_page_47&255)|(ib3<<8);
        48: _prog_page_48=(_prog_page_48&255)|(ib3<<8);
        49: _prog_page_49=(_prog_page_49&255)|(ib3<<8);
        50: _prog_page_50=(_prog_page_50&255)|(ib3<<8);
        51: _prog_page_51=(_prog_page_51&255)|(ib3<<8);
        52: _prog_page_52=(_prog_page_52&255)|(ib3<<8);
        53: _prog_page_53=(_prog_page_53&255)|(ib3<<8);
        54: _prog_page_54=(_prog_page_54&255)|(ib3<<8);
        55: _prog_page_55=(_prog_page_55&255)|(ib3<<8);
        56: _prog_page_56=(_prog_page_56&255)|(ib3<<8);
        57: _prog_page_57=(_prog_page_57&255)|(ib3<<8);
        58: _prog_page_58=(_prog_page_58&255)|(ib3<<8);
        59: _prog_page_59=(_prog_page_59&255)|(ib3<<8);
        60: _prog_page_60=(_prog_page_60&255)|(ib3<<8);
        61: _prog_page_61=(_prog_page_61&255)|(ib3<<8);
        62: _prog_page_62=(_prog_page_62&255)|(ib3<<8);
        63: _prog_page_63=(_prog_page_63&255)|(ib3<<8);
        default:;
    endcase
end
else
begin
    if (_prog_enabled&&(ib0==76))
    begin
        page=((ib1<<3)|(ib2>>5))&255;
        _prog_write_page_addr=page*64;
        _prog_write_page_offset=0;
        _prog_state=2;
        _prog_saw_resp_low=0;
        _prog_bit_count=0;
        _prog_shift_reg=0;
        _prog_reply_armed=0;
        _prog_prev_sck=0;
    end
    else
    begin
        if (_prog_enabled&&((ib0==172)&&(ib1==160)))
        begin
            _fuse_low=ib3;
        end
        else
        begin
            if (_prog_enabled&&((ib0==172)&&(ib1==168)))
            begin
                _fuse_high=ib3;
            end
            else
            begin
                if (_prog_enabled&&((ib0==172)&&(ib1==164)))
                begin
                    _fuse_extended=ib3;
                end
            end
        end
    end
end
end
end
end
end
end
else
begin
if ((sck==0)&&(prev_sck==1))
begin
if (_prog_reply_armed)
begin
bit=(_prog_miso_shift>>7)&1;
_prog_miso_shift=(_prog_miso_shift<<1)&255;
end
else
begin
bit=0;
end
_prog_last_miso_bit=bit;
PROG_MISO<=bit;
if (_prog_bit_count==32)
begin
_prog_shift_reg=0;
_prog_bit_count=0;
_prog_reply_armed=0;
end
end
else
begin
PROG_MISO<=_prog_last_miso_bit;
end
end
if (mem_read)
begin
ins_instype<=1;
end
else
begin
ins_instype<=0;
end
ins_read<=mem_read;
ins_write<=0;
ins_address<=mem_addr;
end
endcase
end
else
begin
just_released=_prev_reset==1;
_prev_reset=0;
pc=PC_ValIn;
pc_load=0;
if (just_released)
begin
bootrst=_fuse_high&1;
if (bootrst==0)
begin
bootsz=(_fuse_high>>1)&3;
case (bootsz)
0: pc=14336;
1: pc=15360;
2: pc=15872;
default:pc=16128;
endcase
end
else
begin
pc=0;
end
pc_load=1;
end
case (FSM)
0: begin
ins_instype<=0;
ins_read<=0;
ins_write<=0;
Instruction_fetched<=0;
Address_fetched<=0;
SPM_Done<=0;
load_jump=Load_Jump;
load_z=Load_Z;
load_k=Load_K;
load_pcl=Load_PCL;
load_pch=Load_PCH;
if ((load_jump==1)||((load_z==1)||((load_k==1)||((load_pcl==1)||(load_pch==1)))))
begin
rel_abs=relative_Absolute;
jumped=0;
if (load_z==1)
begin
PC_BUFFER=pc;
_pc_restore_pending=1;
z_val=(address_ZH<<8)|address_ZL;
if (rel_abs==1)
begin
_lpm_byte_high=z_val&1;
_lpm_byte_pending=1;
pc=(z_val>>1)&16383;
pc_load=1;
end
else
begin
pc=z_val&16383;
pc_load=1;
end
jumped=1;
end
else
begin
if (load_jump==1)
begin
if (rel_abs==1)
begin
k_select_sel=K_select;
case (k_select_sel)
0: k_val=K7;
1: k_val=K12;
2: k_val=K7_22;
default:k_val=K7;
endcase
full_addr=(k_val<<16)|latched_addr_word;
pc=full_addr&16383;
pc_load=1;
end
else
begin
k_val=K12;
if (k_val&2048)
begin
offset=k_val-4096;
end
else
begin
offset=k_val;
end
pc=(pc+offset)&16383;
pc_load=1;
end
jumped=1;
end
else
begin
if (load_k==1)
begin
k_select_sel=K_select;
case (k_select_sel)
0: k_val=K7;
1: k_val=K12;
2: k_val=K7_22;
default:k_val=K7;
endcase
if (k_val&64)
begin
offset=k_val-128;
end
else
begin
offset=k_val;
end
pc=(pc+offset)&16383;
pc_load=1;
jumped=1;
end
end
end
restore_from_buffer=_pc_restore_pending&&((load_pch==1)||(load_pcl==1));
if (load_pch==1)
begin
if (restore_from_buffer)
begin
pc=(pc&255)|(PC_BUFFER&16128);
pc_load=1;
end
else
begin
pc=(pc&255)|((PCH_LOAD_VAL&63)<<8);
pc_load=1;
end
end
if (load_pcl==1)
begin
if (restore_from_buffer)
begin
pc=(pc&65280)|(PC_BUFFER&255);
pc_load=1;
end
else
begin
pc=(pc&65280)|(PCL_LOAD_VAL&255);
pc_load=1;
end
end
if (restore_from_buffer)
begin
_pc_restore_pending=0;
_lpm_byte_pending=0;
end
pc=pc&16383;
pc_load=1;
if (jumped)
begin
Executed_Jump<=1;
FSM=1;
end
else
begin
Executed_Jump<=0;
if (Fetch_next_instruction==1)
begin
_pc_restore_pending=0;
_lpm_byte_pending=0;
FSM=2;
end
else
begin
if (fetch_address==1)
begin
FSM=3;
end
end
end
end
else
begin
Executed_Jump<=0;
if (Fetch_next_instruction==1)
begin
_pc_restore_pending=0;
_lpm_byte_pending=0;
FSM=2;
end
else
begin
if (fetch_address==1)
begin
FSM=3;
end
else
begin
if (LPM_req==1)
begin
FSM=6;
end
else
begin
if (SPM_req==1)
begin
FSM=9;
end
end
end
end
end
end
1: begin
ins_instype<=0;
ins_read<=0;
ins_write<=0;
Instruction_fetched<=0;
Address_fetched<=0;
if ((Load_Jump==0)&&((Load_Z==0)&&((Load_K==0)&&((Load_PCL==0)&&(Load_PCH==0)))))
begin
Executed_Jump<=0;
FSM=0;
end
else
begin
Executed_Jump<=1;
end
end
2: begin
Instruction_fetched<=0;
Executed_Jump<=0;
ins_instype<=1;
if (Load_Byte==1)
begin
ins_write<=1;
ins_read<=0;
ins_address<=pc;
ins_writedata<=WriteVal;
FSM=4;
end
else
begin
ins_write<=0;
ins_read<=1;
ins_address<=pc;
Address_Out<=pc;
FSM=5;
end
end
5: if (ins_resp==1)
begin
ins_read<=0;
ins_instype<=0;
fetched_instruction=ins_readdata;
instructionOut<=fetched_instruction;
Value_Out<=fetched_instruction;
Instruction_fetched<=1;
pc=(pc+1)&16383;
pc_load=1;
Executed_Jump<=0;
FSM=7;
end
3: begin
Address_fetched<=0;
Executed_Jump<=0;
ins_instype<=1;
ins_write<=0;
ins_read<=1;
ins_address<=pc;
FSM=8;
end
8: if (ins_resp==1)
begin
ins_read<=0;
ins_instype<=0;
fetched_word=ins_readdata;
if (_lpm_byte_pending)
begin
if (_lpm_byte_high)
begin
out_val=(fetched_word>>8)&255;
end
else
begin
out_val=fetched_word&255;
end
_lpm_byte_pending=0;
end
else
begin
out_val=fetched_word;
end
Address_Out<=out_val;
Value_Out<=out_val;
Address_fetched<=1;
latched_addr_word=fetched_word;
pc=(pc+1)&16383;
pc_load=1;
FSM=10;
end
4: begin
ins_write<=0;
ins_instype<=0;
if (ins_resp==1)
begin
pc=(pc+1)&16383;
pc_load=1;
FSM=7;
end
end
7: if (Fetch_next_instruction==0)
begin
Instruction_fetched<=0;
FSM=0;
end
10: if (fetch_address==0)
begin
Address_fetched<=0;
FSM=0;
end
else
begin
Address_fetched<=1;
end
6: case (LPM_req)
1: begin
ins_instype<=0;
ins_write<=0;
ins_read<=1;
ins_address<=R0_BUFFER_IN;
val=(R1_BUFFER_IN<<8)|R0_BUFFER_IN;
if (ins_resp==1)
begin
ins_writedata<=ins_readdata;
end
end
2: begin
ins_instype<=0;
ins_write<=0;
ins_read<=1;
z_address=((address_ZH<<8)|address_ZL)&65535;
ins_address<=z_address;
if (ins_resp==1)
begin
Value_Out<=ins_readdata;
end
end
3: begin
ins_instype<=0;
ins_write<=0;
ins_read<=1;
z_address=(((address_ZH<<8)|address_ZL)+1)&65535;
ins_address<=z_address;
if (ins_resp==1)
begin
Value_Out<=ins_readdata;
end
end
default:;
endcase
9: begin
ins_instype<=1;
ins_read<=0;
z_address=(((address_ZH<<8)|address_ZL)>>1)&16383;
ins_address<=z_address;
val=((R1_BUFFER_IN<<8)|R0_BUFFER_IN)&65535;
ins_writedata<=val;
if (ins_resp==1)
begin
ins_write<=0;
SPM_Done<=1;
FSM=11;
end
else
begin
ins_write<=1;
SPM_Done<=0;
end
end
11: begin
ins_write<=0;
ins_instype<=0;
if (SPM_req==0)
begin
SPM_Done<=0;
FSM=0;
end
else
begin
SPM_Done<=1;
end
end
default:FSM=0;
endcase
PC_ValueOut<=pc;
PC_Load<=pc_load;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module Instruction_decoder_7f9e35c19580 (
	input clk,
	input [15:0] Instruction,
	input  Instruction_fetched,
	input  reset,
	output  reg [15:0] InstructionCode,
	output  reg [4:0] Rd,
	output  reg [4:0] Rr,
	output  reg [7:0] K8,
	output  reg [5:0] K6,
	output  reg [3:0] K4,
	output  reg [6:0] k7,
	output  reg [11:0] k12,
	output  reg [6:0] k7_22,
	output  reg [2:0] b,
	output  reg [2:0] s,
	output  reg [4:0] A5,
	output  reg [5:0] A6,
	output  reg [5:0] q,
	output  reg  Instruction_decoded);
// Code generated from clock method
// wire/variable declaration
integer ins;
integer code;
integer mask_4;
integer mask_6;
integer mask_8;
integer mask_8b;
integer mask_10;
integer mask_10b;
integer mask_11;
integer mask_13;
integer OP17;
integer OP16;
integer OP5A6A12;
integer OP7;
integer OP4;
integer OP2A10;
integer OP1A8A13;
integer OP14;
integer rd_d5;
integer rd_d4;
integer rd_d3;
integer rd_d2;
integer rr_r5;
integer rr_r4;
integer rr_r3;
integer K_8bit;
integer K_7bit;
integer K_6bit;
integer K_4bit;
integer k_7bit;
integer k_12bit;
integer k_22bit;
integer b_bit;
integer s_bit;
integer a5_local;
integer a6_local;
integer q_disp;
integer out_rd;
integer out_rr;
integer out_K8;
integer out_K6;
integer out_K4;
integer out_k7;
integer out_k12;
integer out_k7_22;
integer out_b;
integer out_s;
integer out_A5;
integer out_A6;
integer out_q;
// initial
initial
begin
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        InstructionCode<=0;
        Rd<=0;
        Rr<=0;
        K8<=0;
        K6<=0;
        K4<=0;
        k7<=0;
        k12<=0;
        k7_22<=0;
        b<=0;
        s<=0;
        A5<=0;
        A6<=0;
        q<=0;
        Instruction_decoded<=0;
    end
    else
    begin
        ins=Instruction;
        code=0;
        mask_4=ins&61440;
        mask_6=ins&64512;
        mask_8=ins&65032;
        mask_8b=ins&65280;
        mask_10=ins&65038;
        mask_10b=ins&65416;
        mask_11=ins&65039;
        mask_13=ins&65423;
        OP17=((((ins>>3)&1)|(((ins>>9)&1)<<1))|(((ins>>12)&1)<<2))|((ins>>14)<<3);
        OP16=ins>>11;
        OP5A6A12=ins>>8;
        OP7=((ins>>9)<<4)|(ins&15);
        OP4=((ins>>7)<<1)|((ins>>3)&1);
        OP2A10=ins>>12;
        OP1A8A13=ins>>10;
        OP14=((ins>>10)<<3)|(ins&7);
        if (ins==38169)
        begin
            code=33;
        end
        else
        begin
            if (ins==37913)
            begin
                code=30;
            end
            else
            begin
                if (mask_4==28672)
                begin
                    code=10;
                end
                else
                begin
                    if (mask_4==57344)
                    begin
                        code=95;
                    end
                    else
                    begin
                        if (mask_4==49152)
                        begin
                            code=29;
                        end
                        else
                        begin
                            if (mask_6==3072)
                            begin
                                code=1;
                            end
                            else
                            begin
                                if (mask_8==64000)
                                begin
                                    code=75;
                                end
                                else
                                begin
                                    if (mask_8==63488)
                                    begin
                                        code=76;
                                    end
                                    else
                                    begin
                                        if (mask_8==64512)
                                        begin
                                            code=41;
                                        end
                                        else
                                        begin
                                            if (mask_8==65024)
                                            begin
                                                code=42;
                                            end
                                            else
                                            begin
                                                if (mask_8b==512)
                                                begin
                                                    code=24;
                                                end
                                                else
                                                begin
                                                    if (mask_10==37900)
                                                    begin
                                                        code=31;
                                                    end
                                                    else
                                                    begin
                                                        if (mask_10==37902)
                                                        begin
                                                            code=34;
                                                        end
                                                        else
                                                        begin
                                                            if (mask_10b==768)
                                                            begin
                                                                code=25;
                                                            end
                                                            else
                                                            begin
                                                                if (mask_10b==896)
                                                                begin
                                                                    code=27;
                                                                end
                                                                else
                                                                begin
                                                                    if (mask_10b==904)
                                                                    begin
                                                                        code=28;
                                                                    end
                                                                    else
                                                                    begin
                                                                        if (mask_11==36864)
                                                                        begin
                                                                            code=107;
                                                                        end
                                                                        else
                                                                        begin
                                                                            if (mask_11==37376)
                                                                            begin
                                                                                code=119;
                                                                            end
                                                                            else
                                                                            begin
                                                                                if (mask_11==37898)
                                                                                begin
                                                                                    code=19;
                                                                                end
                                                                                else
                                                                                begin
                                                                                    if (mask_11==33280)
                                                                                    begin
                                                                                        code=115;
                                                                                    end
                                                                                    else
                                                                                    begin
                                                                                        if (mask_13==37896)
                                                                                        begin
                                                                                            code=73;
                                                                                        end
                                                                                        else
                                                                                        begin
                                                                                            if (mask_13==38024)
                                                                                            begin
                                                                                                code=74;
                                                                                            end
                                                                                            else
                                                                                            begin
                                                                                                if (OP17==19)
                                                                                                begin
                                                                                                    code=114;
                                                                                                end
                                                                                                else
                                                                                                begin
                                                                                                    if (OP17==18)
                                                                                                    begin
                                                                                                        code=118;
                                                                                                    end
                                                                                                    else
                                                                                                    begin
                                                                                                        if (OP17==16)
                                                                                                        begin
                                                                                                            code=106;
                                                                                                        end
                                                                                                        else
                                                                                                        begin
                                                                                                            if (OP17==17)
                                                                                                            begin
                                                                                                                code=102;
                                                                                                            end
                                                                                                            else
                                                                                                            begin
                                                                                                                if (OP16==22)
                                                                                                                begin
                                                                                                                    code=124;
                                                                                                                end
                                                                                                                else
                                                                                                                begin
                                                                                                                    if (OP16==23)
                                                                                                                    begin
                                                                                                                        code=125;
                                                                                                                    end
                                                                                                                    else
                                                                                                                    begin
                                                                                                                        if (OP5A6A12==1)
                                                                                                                        begin
                                                                                                                            code=94;
                                                                                                                        end
                                                                                                                        else
                                                                                                                        begin
                                                                                                                            if (OP5A6A12==150)
                                                                                                                            begin
                                                                                                                                code=3;
                                                                                                                            end
                                                                                                                            else
                                                                                                                            begin
                                                                                                                                if (OP5A6A12==151)
                                                                                                                                begin
                                                                                                                                    code=8;
                                                                                                                                end
                                                                                                                                else
                                                                                                                                begin
                                                                                                                                    if (OP5A6A12==153)
                                                                                                                                    begin
                                                                                                                                        code=43;
                                                                                                                                    end
                                                                                                                                    else
                                                                                                                                    begin
                                                                                                                                        if (OP5A6A12==154)
                                                                                                                                        begin
                                                                                                                                            code=65;
                                                                                                                                        end
                                                                                                                                        else
                                                                                                                                        begin
                                                                                                                                            if (OP5A6A12==152)
                                                                                                                                            begin
                                                                                                                                                code=66;
                                                                                                                                            end
                                                                                                                                            else
                                                                                                                                            begin
                                                                                                                                                if (OP5A6A12==155)
                                                                                                                                                begin
                                                                                                                                                    code=44;
                                                                                                                                                end
                                                                                                                                                else
                                                                                                                                                begin
                                                                                                                                                    if (OP7==1185)
                                                                                                                                                    begin
                                                                                                                                                        code=15;
                                                                                                                                                    end
                                                                                                                                                    else
                                                                                                                                                    begin
                                                                                                                                                        if (OP7==1184)
                                                                                                                                                        begin
                                                                                                                                                            code=14;
                                                                                                                                                        end
                                                                                                                                                        else
                                                                                                                                                        begin
                                                                                                                                                            if (OP7==1187)
                                                                                                                                                            begin
                                                                                                                                                                code=18;
                                                                                                                                                            end
                                                                                                                                                            else
                                                                                                                                                            begin
                                                                                                                                                                if (OP7==1194)
                                                                                                                                                                begin
                                                                                                                                                                    code=19;
                                                                                                                                                                end
                                                                                                                                                                else
                                                                                                                                                                begin
                                                                                                                                                                    if (OP7==1190)
                                                                                                                                                                    begin
                                                                                                                                                                        code=68;
                                                                                                                                                                    end
                                                                                                                                                                    else
                                                                                                                                                                    begin
                                                                                                                                                                        if (OP7==1191)
                                                                                                                                                                        begin
                                                                                                                                                                            code=70;
                                                                                                                                                                        end
                                                                                                                                                                        else
                                                                                                                                                                        begin
                                                                                                                                                                            if (OP7==1189)
                                                                                                                                                                            begin
                                                                                                                                                                                code=71;
                                                                                                                                                                            end
                                                                                                                                                                            else
                                                                                                                                                                            begin
                                                                                                                                                                                if (OP7==1186)
                                                                                                                                                                                begin
                                                                                                                                                                                    code=72;
                                                                                                                                                                                end
                                                                                                                                                                                else
                                                                                                                                                                                begin
                                                                                                                                                                                    if (OP7==1167)
                                                                                                                                                                                    begin
                                                                                                                                                                                        code=127;
                                                                                                                                                                                    end
                                                                                                                                                                                    else
                                                                                                                                                                                    begin
                                                                                                                                                                                        if (OP7==1183)
                                                                                                                                                                                        begin
                                                                                                                                                                                            code=126;
                                                                                                                                                                                        end
                                                                                                                                                                                        else
                                                                                                                                                                                        begin
                                                                                                                                                                                            if (OP7==1164)
                                                                                                                                                                                            begin
                                                                                                                                                                                                code=96;
                                                                                                                                                                                            end
                                                                                                                                                                                            else
                                                                                                                                                                                            begin
                                                                                                                                                                                                if (OP7==1165)
                                                                                                                                                                                                begin
                                                                                                                                                                                                    code=97;
                                                                                                                                                                                                end
                                                                                                                                                                                                else
                                                                                                                                                                                                begin
                                                                                                                                                                                                    if (OP7==1166)
                                                                                                                                                                                                    begin
                                                                                                                                                                                                        code=98;
                                                                                                                                                                                                    end
                                                                                                                                                                                                    else
                                                                                                                                                                                                    begin
                                                                                                                                                                                                        if (OP7==1032)
                                                                                                                                                                                                        begin
                                                                                                                                                                                                            code=99;
                                                                                                                                                                                                        end
                                                                                                                                                                                                        else
                                                                                                                                                                                                        begin
                                                                                                                                                                                                            if (OP7==1161)
                                                                                                                                                                                                            begin
                                                                                                                                                                                                                code=100;
                                                                                                                                                                                                            end
                                                                                                                                                                                                            else
                                                                                                                                                                                                            begin
                                                                                                                                                                                                                if (OP7==1162)
                                                                                                                                                                                                                begin
                                                                                                                                                                                                                    code=101;
                                                                                                                                                                                                                end
                                                                                                                                                                                                                else
                                                                                                                                                                                                                begin
                                                                                                                                                                                                                    if (OP7==1024)
                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                        code=103;
                                                                                                                                                                                                                    end
                                                                                                                                                                                                                    else
                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                        if (OP7==1153)
                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                            code=104;
                                                                                                                                                                                                                        end
                                                                                                                                                                                                                        else
                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                            if (OP7==1154)
                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                code=105;
                                                                                                                                                                                                                            end
                                                                                                                                                                                                                            else
                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                if (OP7==1180)
                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                    code=108;
                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                    if (OP7==1181)
                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                        code=109;
                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                        if (OP7==1182)
                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                            code=110;
                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                            if (OP7==1048)
                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                code=111;
                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                if (OP7==1177)
                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                    code=112;
                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                    if (OP7==1178)
                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                        code=113;
                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                        if (OP7==1040)
                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                            code=115;
                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                            if (OP7==1169)
                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                code=116;
                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                if (OP7==1170)
                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                    code=117;
                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                    if (OP7==1156)
                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                        code=121;
                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                        if (OP7==1157)
                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                            code=122;
                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                            if (OP4==13)
                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                code=26;
                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                if (OP2A10==4)
                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                    code=7;
                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                    if (OP2A10==5)
                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                        code=5;
                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                        if (OP2A10==6)
                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                            code=12;
                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                            if (OP2A10==3)
                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                code=40;
                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                if (OP2A10==13)
                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                    code=32;
                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                    if (OP1A8A13==2)
                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                        code=6;
                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                        if (OP1A8A13==3)
                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                            code=1;
                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                            if (OP1A8A13==5)
                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                code=38;
                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                if (OP1A8A13==7)
                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                    code=2;
                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                    if (OP1A8A13==6)
                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                        code=4;
                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                        if (OP1A8A13==8)
                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                            code=9;
                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                            if (OP1A8A13==9)
                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                code=13;
                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                if (OP1A8A13==10)
                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                    code=11;
                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                    if (OP1A8A13==39)
                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                        code=23;
                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                        if (OP1A8A13==1)
                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                            code=39;
                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                            if (OP1A8A13==11)
                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                code=93;
                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                if (OP1A8A13==60)
                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                    code=45;
                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                    if (OP1A8A13==61)
                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                        code=46;
                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                        if (OP1A8A13==4)
                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                            code=37;
                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                            if (OP14==481)
                                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                                code=47;
                                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                                if (OP14==489)
                                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                                    code=48;
                                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                                    if (OP14==480)
                                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                                        code=49;
                                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                                        if (OP14==488)
                                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                                            code=51;
                                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                                            if (OP14==482)
                                                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                                                code=53;
                                                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                                                if (OP14==490)
                                                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                                                    code=54;
                                                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                                                    if (OP14==492)
                                                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                                                        code=55;
                                                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                                                        if (OP14==484)
                                                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                                                            code=56;
                                                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                                                            if (OP14==485)
                                                                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                                                                code=57;
                                                                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                                                                if (OP14==493)
                                                                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                                                                    code=58;
                                                                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                                                                    if (OP14==486)
                                                                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                                                                        code=59;
                                                                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                                                                        if (OP14==494)
                                                                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                                                                            code=60;
                                                                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                                                                            if (OP14==483)
                                                                                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                                                                                code=61;
                                                                                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                                                                                            else
                                                                                                                                                                                                                                                                                                                                                                                                            begin
                                                                                                                                                                                                                                                                                                                                                                                                                if (OP14==491)
                                                                                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                                                                                    code=62;
                                                                                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                                                                                else
                                                                                                                                                                                                                                                                                                                                                                                                                begin
                                                                                                                                                                                                                                                                                                                                                                                                                    if (OP14==487)
                                                                                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                                                                                        code=63;
                                                                                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                                                                                    else
                                                                                                                                                                                                                                                                                                                                                                                                                    begin
                                                                                                                                                                                                                                                                                                                                                                                                                        if (OP14==495)
                                                                                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                                                                                            code=64;
                                                                                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                                                                                        else
                                                                                                                                                                                                                                                                                                                                                                                                                        begin
                                                                                                                                                                                                                                                                                                                                                                                                                            case (ins)
                                                                                                                                                                                                                                                                                                                                                                                                                            0: code=128;
                                                                                                                                                                                                                                                                                                                                                                                                                            38280: code=129;
                                                                                                                                                                                                                                                                                                                                                                                                                            38312: code=130;
                                                                                                                                                                                                                                                                                                                                                                                                                            38296: code=131;
                                                                                                                                                                                                                                                                                                                                                                                                                            38152: code=35;
                                                                                                                                                                                                                                                                                                                                                                                                                            38168: code=36;
                                                                                                                                                                                                                                                                                                                                                                                                                            38376: code=123;
                                                                                                                                                                                                                                                                                                                                                                                                                            38392: code=123;
                                                                                                                                                                                                                                                                                                                                                                                                                            36868: code=120;
                                                                                                                                                                                                                                                                                                                                                                                                                            default:;
                                                                                                                                                                                                                                                                                                                                                                                                                        endcase
                                                                                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                                end
                                                                                                                                                                                                                                            end
                                                                                                                                                                                                                                        end
                                                                                                                                                                                                                                    end
                                                                                                                                                                                                                                end
                                                                                                                                                                                                                            end
                                                                                                                                                                                                                        end
                                                                                                                                                                                                                    end
                                                                                                                                                                                                                end
                                                                                                                                                                                                            end
                                                                                                                                                                                                        end
                                                                                                                                                                                                    end
                                                                                                                                                                                                end
                                                                                                                                                                                            end
                                                                                                                                                                                        end
                                                                                                                                                                                    end
                                                                                                                                                                                end
                                                                                                                                                                            end
                                                                                                                                                                        end
                                                                                                                                                                    end
                                                                                                                                                                end
                                                                                                                                                            end
                                                                                                                                                        end
                                                                                                                                                    end
                                                                                                                                                end
                                                                                                                                            end
                                                                                                                                        end
                                                                                                                                    end
                                                                                                                                end
                                                                                                                            end
                                                                                                                        end
                                                                                                                    end
                                                                                                                end
                                                                                                            end
                                                                                                        end
                                                                                                    end
                                                                                                end
                                                                                            end
                                                                                        end
                                                                                    end
                                                                                end
                                                                            end
                                                                        end
                                                                    end
                                                                end
                                                            end
                                                        end
                                                    end
                                                end
                                            end
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    rd_d5=(ins>>4)&31;
    rd_d4=16+((ins>>4)&15);
    rd_d3=16+((ins>>4)&7);
    rd_d2=24+(((ins>>4)&3)<<1);
    rr_r5=((ins>>5)&16)|(ins&15);
    rr_r4=16+(ins&15);
    rr_r3=16+(ins&7);
    K_8bit=((ins>>4)&240)|(ins&15);
    K_7bit=(ins>>2)&127;
    K_6bit=((ins>>2)&48)|(ins&15);
    K_4bit=(ins>>4)&15;
    k_7bit=(ins>>3)&127;
    if (k_7bit&64)
    begin
        k_7bit=k_7bit-128;
    end
    k_12bit=ins&4095;
    if (k_12bit&2048)
    begin
        k_12bit=k_12bit-4096;
    end
    k_22bit=(((ins>>3)&62)|(ins&1))<<16;
    b_bit=ins&7;
    s_bit=(ins>>4)&7;
    a5_local=(ins>>3)&31;
    a6_local=((ins>>5)&48)|(ins&15);
    q_disp=(((ins>>8)&32)|((ins>>7)&24))|(ins&7);
    out_rd=0;
    out_rr=0;
    out_K8=0;
    out_K6=0;
    out_K4=0;
    out_k7=0;
    out_k12=0;
    out_k7_22=0;
    out_b=0;
    out_s=0;
    out_A5=0;
    out_A6=0;
    out_q=0;
    if ((code==1)||((code==2)||((code==4)||((code==6)||((code==9)||((code==11)||((code==13)||((code==20)||((code==23)||((code==37)||((code==38)||((code==39)||(code==93)))))))))))))
    begin
        out_rd=rd_d5;
        out_rr=rr_r5;
    end
    else
    begin
        if (code==24)
        begin
            out_rd=rd_d4;
            out_rr=rr_r4;
        end
        else
        begin
            if ((code==25)||((code==26)||((code==27)||(code==28))))
            begin
                out_rd=rd_d3;
                out_rr=rr_r3;
            end
            else
            begin
                if (code==94)
                begin
                    out_rd=((ins>>4)&15)*2;
                    out_rr=(ins&15)*2;
                end
                else
                begin
                    if ((code==5)||((code==7)||((code==10)||((code==12)||((code==16)||((code==17)||((code==40)||(code==95))))))))
                    begin
                        out_rd=rd_d4;
                        out_K8=K_8bit;
                    end
                    else
                    begin
                        if ((code==3)||(code==8))
                        begin
                            out_rd=rd_d2;
                            out_K6=K_6bit;
                            out_K8=K_6bit;
                        end
                        else
                        begin
                            if ((code==14)||((code==15)||((code==18)||((code==19)||((code==21)||((code==22)||((code==67)||((code==68)||((code==69)||((code==70)||((code==71)||((code==72)||((code==126)||(code==127))))))))))))))
                            begin
                                out_rd=rd_d5;
                            end
                            else
                            begin
                                if ((code==29)||(code==32))
                                begin
                                    out_k12=k_12bit;
                                end
                                else
                                begin
                                    if ((45<=code)&&(code<=64))
                                    begin
                                        out_k7=k_7bit;
                                        out_b=b_bit;
                                    end
                                    else
                                    begin
                                        if ((code==31)||(code==34))
                                        begin
                                            out_k7_22=(k_22bit>>16)&127;
                                        end
                                        else
                                        begin
                                            if ((code==41)||((code==42)||(code==75)))
                                            begin
                                                out_rr=rd_d5;
                                                out_b=b_bit;
                                            end
                                            else
                                            begin
                                                if (code==76)
                                                begin
                                                    out_rd=rd_d5;
                                                    out_b=b_bit;
                                                end
                                                else
                                                begin
                                                    if ((code==43)||((code==44)||((code==65)||(code==66))))
                                                    begin
                                                        out_A5=a5_local;
                                                        out_b=b_bit;
                                                    end
                                                    else
                                                    begin
                                                        if (((code==73)||(code==74))||((77<=code)&&(code<=92)))
                                                        begin
                                                            out_s=s_bit;
                                                            out_b=s_bit;
                                                        end
                                                        else
                                                        begin
                                                            if ((code==124)||(code==125))
                                                            begin
                                                                out_rd=rd_d5;
                                                                out_A6=a6_local;
                                                            end
                                                            else
                                                            begin
                                                                if ((code==102)||((code==106)||((code==114)||(code==118))))
                                                                begin
                                                                    out_rd=rd_d5;
                                                                    out_q=q_disp;
                                                                end
                                                                else
                                                                begin
                                                                    if (((96<=code)&&(code<=101))||(((103<=code)&&(code<=105))||(((108<=code)&&(code<=113))||(((115<=code)&&(code<=117))||((code==107)||((code==119)||((code==121)||(code==122))))))))
                                                                    begin
                                                                        out_rd=rd_d5;
                                                                    end
                                                                end
                                                            end
                                                        end
                                                    end
                                                end
                                            end
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    InstructionCode<=code;
    Rd<=out_rd;
    Rr<=out_rr;
    K8<=out_K8;
    K6<=out_K6;
    K4<=out_K4;
    k7<=out_k7;
    k12<=out_k12;
    k7_22<=out_k7_22;
    b<=out_b;
    s<=out_s;
    A5<=out_A5;
    A6<=out_A6;
    q<=out_q;
    Instruction_decoded<=Instruction_fetched;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module ALU_STRUC_7f9e3eea7c50 (
	input  reset,
	input [7:0] A0,
	input [7:0] A1,
	input [7:0] B0,
	input [7:0] B1,
	input [15:0] op,
	input [7:0] SREG_STATE,
	input [2:0] BitPos,
	input [7:0] IOreg,
	output [7:0] R0,
	output [7:0] R1,
	output [7:0] SREG_VAL,
	output [7:0] eSREG_VAL,
	output  BRANCH,
	output  SKIP);
wire [7:0] w_w_arith_ctrl;
wire [3:0] w_w_copp;
wire [2:0] w_w_zopp;
wire [2:0] w_w_nopp;
wire [3:0] w_w_vopp;
wire [2:0] w_w_sopp;
wire [2:0] w_w_hopp;
wire [1:0] w_w_topp;
wire w_w_iopp;
wire [2:0] w_w_branchOpp;
wire w_w_mul_carry;
wire w_w_cin;
wire w_w_zin;
wire w_w_nin;
wire w_w_vin;
wire w_w_tin_sink;
wire w_w_cout;
wire w_w_zout;
wire w_w_nout;
wire w_w_vout;
wire w_w_sout;
wire w_w_hout;
wire w_w_tout;
wire w_w_iout;
wire [15:0] w_w_regA_16;
wire [15:0] w_w_regB_16;
wire [15:0] w_w_res_16;

SREG_Splitter_7f9e3eebc7a0 i_SREGSplitter(.SREG_STATE(SREG_STATE),.w_cin(w_w_cin),.w_zin(w_w_zin),.w_nin(w_w_nin),.w_vin(w_w_vin),.w_tin(w_w_tin_sink));
assign w_w_regA_16 ={A1,A0};
assign w_w_regB_16 ={B1,B0};
assign w_w_res_16 ={R1,R0};
ALU_ConfCodeCalc_7f9e3eebcf80 i_ConfCodeCalc(.ins(op),.bit_pos(BitPos),.ArithmCode(w_w_arith_ctrl),.Copp(w_w_copp),.Zopp(w_w_zopp),.Nopp(w_w_nopp),.Vopp(w_w_vopp),.Sopp(w_w_sopp),.Hopp(w_w_hopp),.Topp(w_w_topp),.Iopp(w_w_iopp),.eSREG(eSREG_VAL),.BranchOpp(w_w_branchOpp));
AU_STRUC_7f9e3eebd4c0 i_AU(.Cval(w_w_cin),.Tval(w_w_tin_sink),.RegAL(A0),.RegAH(A1),.RegBL(B0),.RegBH(B1),.Operation(w_w_arith_ctrl),.BitPos(BitPos),.ResL(R0),.ResH(R1),.MulCarryOut(w_w_mul_carry));
BranchUnit_STRUC_7f9e35cb7590 i_LU(.SREG(SREG_STATE),.RegisterToTest(A0),.RegisterB(B0),.IORegisterToTest(IOreg),.Bit(BitPos),.Operation(w_w_branchOpp),.Skip(SKIP),.Branch(BRANCH));
HandleC_STRUC_7f9e35b39f40 i_HC(.Rr(w_w_regB_16),.Rd(w_w_regA_16),.Res(w_w_res_16),.Mode(w_w_copp),.MulCarry(w_w_mul_carry),.Cout(w_w_cout));
HandleZ_STRUC_7f9e35b59d00 i_HZ(.Res(w_w_res_16),.Mode(w_w_zopp),.Zprev(w_w_zin),.Zout(w_w_zout));
HandleN_STRUC_7f9e35b71970 i_HN(.Res(w_w_res_16),.Mode(w_w_nopp),.Nout(w_w_nout));
HandleV_STRUC_7f9e35b72210 i_HV(.Rr(w_w_regB_16),.Rd(w_w_regA_16),.Res(w_w_res_16),.N(w_w_nout),.C(w_w_cout),.Mode(w_w_vopp),.Vout(w_w_vout));
HandleH_STRUC_7f9e35b9e630 i_HH(.Rr(w_w_regB_16),.Rd(w_w_regA_16),.Res(w_w_res_16),.Mode(w_w_hopp),.Hout(w_w_hout));
HandleT_STRUC_7f9e35ba7290 i_HT(.Rr(B0),.BitPos(BitPos),.Mode(w_w_topp),.Tout(w_w_tout));
HandleI_STRUC_7f9e35bb1d00 i_HI(.Mode(w_w_iopp),.Iout(w_w_iout));
HandleS_STRUC_7f9e35bb3a10 i_HS(.N(w_w_nout),.V(w_w_vout),.Mode(w_w_sopp),.Sout(w_w_sout));
ALU_MergerAndLogic_7f9e35bb8ec0 i_ALUMerger(.w_cout(w_w_cout),.w_zout(w_w_zout),.w_nout(w_w_nout),.w_vout(w_w_vout),.w_sout(w_w_sout),.w_hout(w_w_hout),.w_tout(w_w_tout),.w_iout(w_w_iout),.sreg_val(SREG_VAL));
endmodule

// This file was automatically created by py4hw Verilog generator
module SREG_Splitter_7f9e3eebc7a0 (
	input [7:0] SREG_STATE,
	output  reg  w_cin,
	output  reg  w_zin,
	output  reg  w_nin,
	output  reg  w_vin,
	output  reg  w_tin);
// Code generated from propagate method
// wire/variable declaration
integer sreg;
// initial
initial
begin
end
// process
always @(*)
begin
    sreg=SREG_STATE;
    w_cin<=sreg&1;
    w_zin<=(sreg>>1)&1;
    w_nin<=(sreg>>2)&1;
    w_vin<=(sreg>>3)&1;
    w_tin<=(sreg>>6)&1;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module ALU_ConfCodeCalc_7f9e3eebcf80 (
	input [15:0] ins,
	input [2:0] bit_pos,
	output  reg [7:0] ArithmCode,
	output  reg [3:0] Copp,
	output  reg [2:0] Zopp,
	output  reg [2:0] Nopp,
	output  reg [3:0] Vopp,
	output  reg [2:0] Sopp,
	output  reg [2:0] Hopp,
	output  reg [1:0] Topp,
	output  reg  Iopp,
	output  reg [7:0] eSREG,
	output  reg [2:0] BranchOpp);
// Code generated from propagate method
// wire/variable declaration
integer ins_sel;
integer bp;
integer arith_code;
integer branch_val;
integer esreg_val;
integer copp_val;
integer zopp_val;
integer nopp_val;
integer vopp_val;
integer sopp_val;
integer hopp_val;
integer topp_val;
integer iopp_val;
// initial
initial
begin
end
// process
always @(*)
begin
    ins_sel=ins&255;
    bp=bit_pos;
    if ((((((ins_sel==37)||(ins_sel==41))||((ins_sel==42)||(ins_sel==43)))||(((ins_sel==44)||(ins_sel==45))||((ins_sel==46)||(ins_sel==47))))||((((ins_sel==48)||(ins_sel==49))||((ins_sel==50)||(ins_sel==51)))||(((ins_sel==52)||(ins_sel==53))||((ins_sel==54)||(ins_sel==55)))))||(((((ins_sel==56)||(ins_sel==57))||((ins_sel==58)||(ins_sel==59)))||(((ins_sel==60)||(ins_sel==61))||((ins_sel==62)||(ins_sel==63))))||(ins_sel==64)))
    begin
        arith_code=0;
    end
    else
    begin
        arith_code=ins_sel;
    end
    branch_val=0;
    esreg_val=0;
    copp_val=0;
    zopp_val=0;
    nopp_val=0;
    vopp_val=0;
    sopp_val=0;
    hopp_val=0;
    topp_val=0;
    iopp_val=0;
    case (ins_sel)
    1: begin
    esreg_val=63;
    copp_val=2;
    zopp_val=2;
    nopp_val=2;
    vopp_val=2;
    sopp_val=2;
    hopp_val=2;
end
2: begin
esreg_val=63;
copp_val=2;
zopp_val=2;
nopp_val=2;
vopp_val=2;
sopp_val=2;
hopp_val=2;
end
3: begin
esreg_val=31;
copp_val=4;
zopp_val=3;
nopp_val=3;
vopp_val=4;
sopp_val=2;
end
4: begin
esreg_val=63;
copp_val=3;
zopp_val=2;
nopp_val=2;
vopp_val=3;
sopp_val=2;
hopp_val=3;
end
5: begin
esreg_val=63;
copp_val=3;
zopp_val=2;
nopp_val=2;
vopp_val=3;
sopp_val=2;
hopp_val=3;
end
6: begin
esreg_val=63;
copp_val=3;
zopp_val=5;
nopp_val=2;
vopp_val=3;
sopp_val=2;
hopp_val=3;
end
7: begin
esreg_val=63;
copp_val=3;
zopp_val=5;
nopp_val=2;
vopp_val=3;
sopp_val=2;
hopp_val=3;
end
8: begin
esreg_val=31;
copp_val=5;
zopp_val=3;
nopp_val=3;
vopp_val=5;
sopp_val=2;
end
9: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
10: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
11: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
12: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
13: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
14: begin
esreg_val=31;
copp_val=6;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
15: begin
esreg_val=63;
copp_val=7;
zopp_val=2;
nopp_val=2;
vopp_val=6;
sopp_val=2;
hopp_val=4;
end
16: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
17: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
18: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
vopp_val=6;
sopp_val=2;
end
19: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
vopp_val=7;
sopp_val=2;
end
20: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
21: begin
esreg_val=30;
zopp_val=2;
nopp_val=2;
sopp_val=2;
end
23: begin
esreg_val=3;
copp_val=8;
zopp_val=3;
end
24: begin
esreg_val=3;
copp_val=8;
zopp_val=3;
end
25: begin
esreg_val=3;
copp_val=8;
zopp_val=3;
end
26: begin
esreg_val=3;
copp_val=8;
zopp_val=3;
end
27: begin
esreg_val=3;
copp_val=8;
zopp_val=3;
end
28: begin
esreg_val=3;
copp_val=8;
zopp_val=3;
end
37: branch_val=7;
38: begin
esreg_val=63;
copp_val=3;
zopp_val=2;
nopp_val=2;
vopp_val=3;
sopp_val=2;
hopp_val=3;
end
39: begin
esreg_val=63;
copp_val=3;
zopp_val=5;
nopp_val=2;
vopp_val=3;
sopp_val=2;
hopp_val=3;
end
40: begin
esreg_val=63;
copp_val=3;
zopp_val=2;
nopp_val=2;
vopp_val=3;
sopp_val=2;
hopp_val=3;
end
41: branch_val=3;
42: branch_val=4;
43: branch_val=5;
44: branch_val=6;
45: branch_val=1;
46: branch_val=2;
47: branch_val=1;
48: branch_val=2;
49: branch_val=1;
50: branch_val=2;
51: branch_val=2;
52: branch_val=2;
53: branch_val=1;
54: branch_val=2;
55: branch_val=1;
56: branch_val=2;
57: branch_val=1;
58: branch_val=2;
59: branch_val=1;
60: branch_val=2;
61: branch_val=1;
62: branch_val=2;
63: branch_val=1;
64: branch_val=2;
67: begin
esreg_val=31;
copp_val=10;
zopp_val=2;
nopp_val=2;
vopp_val=9;
sopp_val=2;
end
68: begin
esreg_val=31;
copp_val=9;
zopp_val=2;
vopp_val=9;
sopp_val=2;
end
69: begin
esreg_val=31;
copp_val=10;
zopp_val=2;
nopp_val=2;
vopp_val=9;
sopp_val=2;
end
70: begin
esreg_val=31;
copp_val=9;
zopp_val=2;
nopp_val=2;
vopp_val=9;
sopp_val=2;
end
71: begin
esreg_val=31;
copp_val=9;
zopp_val=2;
nopp_val=2;
vopp_val=9;
sopp_val=2;
end
73: begin
esreg_val=(1<<bp)&255;
copp_val=1;
zopp_val=1;
nopp_val=1;
vopp_val=1;
sopp_val=1;
hopp_val=1;
topp_val=1;
iopp_val=1;
end
74: esreg_val=(1<<bp)&255;
75: begin
esreg_val=64;
topp_val=2;
end
77: begin
esreg_val=1;
copp_val=1;
end
78: esreg_val=1;
79: begin
esreg_val=4;
nopp_val=1;
end
80: esreg_val=4;
81: begin
esreg_val=2;
zopp_val=1;
end
82: esreg_val=2;
83: begin
esreg_val=128;
iopp_val=1;
end
84: esreg_val=128;
85: begin
esreg_val=16;
sopp_val=1;
end
86: esreg_val=16;
87: begin
esreg_val=8;
vopp_val=1;
end
88: esreg_val=8;
89: begin
esreg_val=64;
topp_val=1;
end
90: esreg_val=64;
91: begin
esreg_val=32;
hopp_val=1;
end
92: esreg_val=32;
default:;
endcase
ArithmCode<=arith_code;
BranchOpp<=branch_val;
eSREG<=esreg_val;
Copp<=copp_val;
Zopp<=zopp_val;
Nopp<=nopp_val;
Vopp<=vopp_val;
Sopp<=sopp_val;
Hopp<=hopp_val;
Topp<=topp_val;
Iopp<=iopp_val;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module AU_STRUC_7f9e3eebd4c0 (
	input  Cval,
	input  Tval,
	input [7:0] RegAL,
	input [7:0] RegAH,
	input [7:0] RegBL,
	input [7:0] RegBH,
	input [7:0] Operation,
	input [2:0] BitPos,
	output [7:0] ResL,
	output [7:0] ResH,
	output  MulCarryOut);
wire [7:0] w_w_add;
wire [7:0] w_w_inc;
wire [7:0] w_w_com;
wire [7:0] w_w_adc_temp;
wire [7:0] w_w_mul_h;
wire [7:0] w_w_muls_h;
wire [7:0] w_w_zero8;
wire [7:0] w_w_asr;
wire [15:0] w_w_zero16;
wire [15:0] w_w_sbiw16;
wire [7:0] w_w_sub;
wire w_w_zero1;
wire [7:0] w_w_lsl;
wire [7:0] w_w_cbi;
wire [7:0] w_w_one8;
wire [7:0] w_w_sbiw_l;
wire [15:0] w_w_mulsu16;
wire [7:0] w_w_dec;
wire [7:0] w_w_ff;
wire [7:0] w_w_bld;
wire [7:0] w_w_Cval8;
wire [7:0] w_w_neg;
wire [7:0] w_w_mulsu_l;
wire [6:0] w_w_op_sel7;
wire [7:0] w_w_notB;
wire [15:0] w_w_fmul16;
wire [15:0] w_w_adiw16;
wire w_w_muls_carry;
wire [7:0] w_w_sbiw_h;
wire [3:0] w_w_A_3_0;
wire [7:0] w_w_fmul_l;
wire [3:0] w_w_A_7_4;
wire [7:0] w_w_lsr;
wire [15:0] w_w_mul16;
wire [7:0] w_w_adiw_l;
wire [8:0] w_w_regB_9u;
wire [7:0] w_w_mulsu_h;
wire [7:0] w_w_fmul_h;
wire [15:0] w_w_fmuls16;
wire [7:0] w_w_fmuls_l;
wire [7:0] w_w_cbr;
wire [7:0] w_w_adc;
wire [6:0] w_w_zero7;
wire [7:0] w_w_and;
wire [6:0] w_w_A_6_0;
wire [7:0] w_w_rol;
wire [7:0] w_w_swap;
wire [7:0] w_w_sbc_temp;
wire [7:0] w_w_or;
wire [7:0] w_w_fmuls_h;
wire w_w_mulsu_carry;
wire [15:0] w_w_wordA;
wire w_w_mul_carry;
wire [6:0] w_w_A_7_1;
wire w_w_A_7;
wire [15:0] w_w_fmulsu16;
wire [7:0] w_w_sbc;
wire [7:0] w_w_xor;
wire [7:0] w_w_ror;
wire [7:0] w_w_fmulsu_l;
wire [15:0] w_w_wordB;
wire [7:0] w_w_bit_mask;
wire [7:0] w_w_adiw_h;
wire [7:0] w_w_not_mask;
wire [7:0] w_w_mul_l;
wire [15:0] w_w_muls16;
wire [7:0] w_w_sbi;
wire [7:0] w_w_muls_l;
wire [8:0] w_w_regA_9s;
wire [7:0] w_w_fmulsu_h;

assign w_w_zero8[7:0] = 0;
assign w_w_zero16[15:0] = 0;
assign w_w_zero1 = 0;
assign w_w_one8[7:0] = 1;
assign w_w_ff[7:0] = 255;
assign w_w_zero7[6:0] = 0;
assign w_w_Cval8 ={w_w_zero7,Cval};
Add8 i_ADD_Unit(.a(RegAL),.b(RegBL),.r(w_w_add));
Add8 i_ADC_Add1(.a(RegAL),.b(RegBL),.r(w_w_adc_temp));
Add8 i_ADC_Add2(.a(w_w_adc_temp),.b(w_w_Cval8),.r(w_w_adc));
assign w_w_sub = RegAL - RegBL;
assign w_w_sbc_temp = RegAL - RegBL;
assign w_w_sbc = w_w_sbc_temp - w_w_Cval8;
Add8 i_INC_Unit(.a(RegAL),.b(w_w_one8),.r(w_w_inc));
assign w_w_dec = RegAL - w_w_one8;
assign w_w_wordA ={RegAH,RegAL};
assign w_w_wordB ={RegBH,RegBL};
Add16 i_ADIW_Unit(.a(w_w_wordA),.b(w_w_wordB),.r(w_w_adiw16));
assign w_w_adiw_l = w_w_adiw16[7:0];
assign w_w_adiw_h = w_w_adiw16[15:8];
assign w_w_sbiw16 = w_w_wordA - w_w_wordB;
assign w_w_sbiw_l = w_w_sbiw16[7:0];
assign w_w_sbiw_h = w_w_sbiw16[15:8];
assign w_w_and = RegAL & RegBL;
assign w_w_or = RegAL | RegBL;
assign w_w_xor = RegAL ^ RegBL;
assign w_w_com = ~RegAL;
assign w_w_neg = w_w_zero8 - RegAL;
assign w_w_notB = ~RegBL;
assign w_w_cbr = RegAL & w_w_notB;
assign w_w_A_6_0 = RegAL[6:0];
assign w_w_A_7_1 = RegAL[7:1];
assign w_w_A_7 = RegAL[7:7];
assign w_w_lsl ={w_w_A_6_0,w_w_zero1};
assign w_w_lsr ={w_w_zero1,w_w_A_7_1};
assign w_w_rol ={w_w_A_6_0,Cval};
assign w_w_ror ={Cval,w_w_A_7_1};
assign w_w_asr ={w_w_A_7,w_w_A_7_1};
assign w_w_A_3_0 = RegAL[3:0];
assign w_w_A_7_4 = RegAL[7:4];
assign w_w_swap ={w_w_A_3_0,w_w_A_7_4};
ShiftLeft_7f9e35c78740 i_Shl_Mask(.a(w_w_one8),.b(BitPos),.r(w_w_bit_mask));
assign w_w_sbi = RegAL | w_w_bit_mask;
assign w_w_not_mask = ~w_w_bit_mask;
assign w_w_cbi = RegAL & w_w_not_mask;
Mux_7f9e35c79b20 i_BLD_Mux(.sel(Tval),.in0(w_w_cbi),.in1(w_w_sbi),.r(w_w_bld));
assign w_w_mul16 = RegAL * RegBL;
assign w_w_mul_l = w_w_mul16[7:0];
assign w_w_mul_h = w_w_mul16[15:8];
assign w_w_fmul16 = w_w_mul16 << 1;
assign w_w_fmul_l = w_w_fmul16[7:0];
assign w_w_fmul_h = w_w_fmul16[15:8];
assign w_w_mul_carry = w_w_mul16[15:15];
assign w_w_muls16 = $signed(RegAL) * $signed(RegBL);
assign w_w_muls_l = w_w_muls16[7:0];
assign w_w_muls_h = w_w_muls16[15:8];
assign w_w_muls_carry = w_w_muls16[15:15];
assign w_w_fmuls16 = w_w_muls16 << 1;
assign w_w_fmuls_l = w_w_fmuls16[7:0];
assign w_w_fmuls_h = w_w_fmuls16[15:8];
assign w_w_regA_9s = { { 1 { RegAL[7] } }, RegAL };
assign w_w_regB_9u = RegBL;
assign w_w_mulsu16 = $signed(w_w_regA_9s) * $signed(w_w_regB_9u);
assign w_w_mulsu_l = w_w_mulsu16[7:0];
assign w_w_mulsu_h = w_w_mulsu16[15:8];
assign w_w_mulsu_carry = w_w_mulsu16[15:15];
assign w_w_fmulsu16 = w_w_mulsu16 << 1;
assign w_w_fmulsu_l = w_w_fmulsu16[7:0];
assign w_w_fmulsu_h = w_w_fmulsu16[15:8];
assign w_w_op_sel7 = Operation[6:0];
Mux_7f9e35c7bb00 i_Main_Mux_ResL(.sel(w_w_op_sel7),.in0(w_w_zero8),.in1(w_w_add),.in2(w_w_adc),.in3(w_w_adiw_l),.in4(w_w_sub),.in5(w_w_sub),.in6(w_w_sbc),.in7(w_w_sbc),.in8(w_w_sbiw_l),.in9(w_w_and),.in10(w_w_and),.in11(w_w_or),.in12(w_w_or),.in13(w_w_xor),.in14(w_w_com),.in15(w_w_neg),.in16(w_w_or),.in17(w_w_cbr),.in18(w_w_inc),.in19(w_w_dec),.in20(w_w_and),.in21(w_w_xor),.in22(w_w_ff),.in23(w_w_mul_l),.in24(w_w_muls_l),.in25(w_w_mulsu_l),.in26(w_w_fmul_l),.in27(w_w_fmuls_l),.in28(w_w_fmulsu_l),.in29(w_w_zero8),.in30(w_w_zero8),.in31(w_w_zero8),.in32(w_w_zero8),.in33(w_w_zero8),.in34(w_w_zero8),.in35(w_w_zero8),.in36(w_w_zero8),.in37(w_w_zero8),.in38(w_w_sub),.in39(w_w_sbc),.in40(w_w_sub),.in41(w_w_zero8),.in42(w_w_zero8),.in43(w_w_zero8),.in44(w_w_zero8),.in45(w_w_zero8),.in46(w_w_zero8),.in47(w_w_zero8),.in48(w_w_zero8),.in49(w_w_zero8),.in50(w_w_zero8),.in51(w_w_zero8),.in52(w_w_zero8),.in53(w_w_zero8),.in54(w_w_zero8),.in55(w_w_zero8),.in56(w_w_zero8),.in57(w_w_zero8),.in58(w_w_zero8),.in59(w_w_zero8),.in60(w_w_zero8),.in61(w_w_zero8),.in62(w_w_zero8),.in63(w_w_zero8),.in64(w_w_zero8),.in65(w_w_sbi),.in66(w_w_cbi),.in67(w_w_lsl),.in68(w_w_lsr),.in69(w_w_rol),.in70(w_w_ror),.in71(w_w_asr),.in72(w_w_swap),.in73(w_w_zero8),.in74(w_w_zero8),.in75(w_w_zero8),.in76(w_w_bld),.in77(w_w_zero8),.in78(w_w_zero8),.in79(w_w_zero8),.in80(w_w_zero8),.in81(w_w_zero8),.in82(w_w_zero8),.in83(w_w_zero8),.in84(w_w_zero8),.in85(w_w_zero8),.in86(w_w_zero8),.in87(w_w_zero8),.in88(w_w_zero8),.in89(w_w_zero8),.in90(w_w_zero8),.in91(w_w_zero8),.in92(w_w_zero8),.in93(RegBL),.in94(w_w_zero8),.in95(w_w_zero8),.in96(w_w_zero8),.in97(w_w_zero8),.in98(w_w_zero8),.in99(w_w_zero8),.in100(w_w_zero8),.in101(w_w_zero8),.in102(w_w_zero8),.in103(w_w_zero8),.in104(w_w_zero8),.in105(w_w_zero8),.in106(w_w_zero8),.in107(w_w_zero8),.in108(w_w_zero8),.in109(w_w_zero8),.in110(w_w_zero8),.in111(w_w_zero8),.in112(w_w_zero8),.in113(w_w_zero8),.in114(w_w_zero8),.in115(w_w_zero8),.in116(w_w_zero8),.in117(w_w_zero8),.in118(w_w_zero8),.in119(w_w_zero8),.in120(w_w_zero8),.in121(w_w_zero8),.in122(w_w_zero8),.in123(w_w_zero8),.in124(w_w_zero8),.in125(w_w_zero8),.in126(w_w_zero8),.in127(w_w_zero8),.r(ResL));
Mux_7f9e35c7bb30 i_Main_Mux_ResH(.sel(w_w_op_sel7),.in0(w_w_zero8),.in1(w_w_zero8),.in2(w_w_zero8),.in3(w_w_adiw_h),.in4(w_w_zero8),.in5(w_w_zero8),.in6(w_w_zero8),.in7(w_w_zero8),.in8(w_w_sbiw_h),.in9(w_w_zero8),.in10(w_w_zero8),.in11(w_w_zero8),.in12(w_w_zero8),.in13(w_w_zero8),.in14(w_w_zero8),.in15(w_w_zero8),.in16(w_w_zero8),.in17(w_w_zero8),.in18(w_w_zero8),.in19(w_w_zero8),.in20(w_w_zero8),.in21(w_w_zero8),.in22(w_w_zero8),.in23(w_w_mul_h),.in24(w_w_muls_h),.in25(w_w_mulsu_h),.in26(w_w_fmul_h),.in27(w_w_fmuls_h),.in28(w_w_fmulsu_h),.in29(w_w_zero8),.in30(w_w_zero8),.in31(w_w_zero8),.in32(w_w_zero8),.in33(w_w_zero8),.in34(w_w_zero8),.in35(w_w_zero8),.in36(w_w_zero8),.in37(w_w_zero8),.in38(w_w_zero8),.in39(w_w_zero8),.in40(w_w_zero8),.in41(w_w_zero8),.in42(w_w_zero8),.in43(w_w_zero8),.in44(w_w_zero8),.in45(w_w_zero8),.in46(w_w_zero8),.in47(w_w_zero8),.in48(w_w_zero8),.in49(w_w_zero8),.in50(w_w_zero8),.in51(w_w_zero8),.in52(w_w_zero8),.in53(w_w_zero8),.in54(w_w_zero8),.in55(w_w_zero8),.in56(w_w_zero8),.in57(w_w_zero8),.in58(w_w_zero8),.in59(w_w_zero8),.in60(w_w_zero8),.in61(w_w_zero8),.in62(w_w_zero8),.in63(w_w_zero8),.in64(w_w_zero8),.in65(w_w_zero8),.in66(w_w_zero8),.in67(w_w_zero8),.in68(w_w_zero8),.in69(w_w_zero8),.in70(w_w_zero8),.in71(w_w_zero8),.in72(w_w_zero8),.in73(w_w_zero8),.in74(w_w_zero8),.in75(w_w_zero8),.in76(w_w_zero8),.in77(w_w_zero8),.in78(w_w_zero8),.in79(w_w_zero8),.in80(w_w_zero8),.in81(w_w_zero8),.in82(w_w_zero8),.in83(w_w_zero8),.in84(w_w_zero8),.in85(w_w_zero8),.in86(w_w_zero8),.in87(w_w_zero8),.in88(w_w_zero8),.in89(w_w_zero8),.in90(w_w_zero8),.in91(w_w_zero8),.in92(w_w_zero8),.in93(w_w_zero8),.in94(w_w_zero8),.in95(w_w_zero8),.in96(w_w_zero8),.in97(w_w_zero8),.in98(w_w_zero8),.in99(w_w_zero8),.in100(w_w_zero8),.in101(w_w_zero8),.in102(w_w_zero8),.in103(w_w_zero8),.in104(w_w_zero8),.in105(w_w_zero8),.in106(w_w_zero8),.in107(w_w_zero8),.in108(w_w_zero8),.in109(w_w_zero8),.in110(w_w_zero8),.in111(w_w_zero8),.in112(w_w_zero8),.in113(w_w_zero8),.in114(w_w_zero8),.in115(w_w_zero8),.in116(w_w_zero8),.in117(w_w_zero8),.in118(w_w_zero8),.in119(w_w_zero8),.in120(w_w_zero8),.in121(w_w_zero8),.in122(w_w_zero8),.in123(w_w_zero8),.in124(w_w_zero8),.in125(w_w_zero8),.in126(w_w_zero8),.in127(w_w_zero8),.r(ResH));
Mux_7f9e35c94ad0 i_Main_Mux_MulC(.sel(w_w_op_sel7),.in0(w_w_zero1),.in1(w_w_zero1),.in2(w_w_zero1),.in3(w_w_zero1),.in4(w_w_zero1),.in5(w_w_zero1),.in6(w_w_zero1),.in7(w_w_zero1),.in8(w_w_zero1),.in9(w_w_zero1),.in10(w_w_zero1),.in11(w_w_zero1),.in12(w_w_zero1),.in13(w_w_zero1),.in14(w_w_zero1),.in15(w_w_zero1),.in16(w_w_zero1),.in17(w_w_zero1),.in18(w_w_zero1),.in19(w_w_zero1),.in20(w_w_zero1),.in21(w_w_zero1),.in22(w_w_zero1),.in23(w_w_mul_carry),.in24(w_w_muls_carry),.in25(w_w_mulsu_carry),.in26(w_w_mul_carry),.in27(w_w_muls_carry),.in28(w_w_mulsu_carry),.in29(w_w_zero1),.in30(w_w_zero1),.in31(w_w_zero1),.in32(w_w_zero1),.in33(w_w_zero1),.in34(w_w_zero1),.in35(w_w_zero1),.in36(w_w_zero1),.in37(w_w_zero1),.in38(w_w_zero1),.in39(w_w_zero1),.in40(w_w_zero1),.in41(w_w_zero1),.in42(w_w_zero1),.in43(w_w_zero1),.in44(w_w_zero1),.in45(w_w_zero1),.in46(w_w_zero1),.in47(w_w_zero1),.in48(w_w_zero1),.in49(w_w_zero1),.in50(w_w_zero1),.in51(w_w_zero1),.in52(w_w_zero1),.in53(w_w_zero1),.in54(w_w_zero1),.in55(w_w_zero1),.in56(w_w_zero1),.in57(w_w_zero1),.in58(w_w_zero1),.in59(w_w_zero1),.in60(w_w_zero1),.in61(w_w_zero1),.in62(w_w_zero1),.in63(w_w_zero1),.in64(w_w_zero1),.in65(w_w_zero1),.in66(w_w_zero1),.in67(w_w_zero1),.in68(w_w_zero1),.in69(w_w_zero1),.in70(w_w_zero1),.in71(w_w_zero1),.in72(w_w_zero1),.in73(w_w_zero1),.in74(w_w_zero1),.in75(w_w_zero1),.in76(w_w_zero1),.in77(w_w_zero1),.in78(w_w_zero1),.in79(w_w_zero1),.in80(w_w_zero1),.in81(w_w_zero1),.in82(w_w_zero1),.in83(w_w_zero1),.in84(w_w_zero1),.in85(w_w_zero1),.in86(w_w_zero1),.in87(w_w_zero1),.in88(w_w_zero1),.in89(w_w_zero1),.in90(w_w_zero1),.in91(w_w_zero1),.in92(w_w_zero1),.in93(w_w_zero1),.in94(w_w_zero1),.in95(w_w_zero1),.in96(w_w_zero1),.in97(w_w_zero1),.in98(w_w_zero1),.in99(w_w_zero1),.in100(w_w_zero1),.in101(w_w_zero1),.in102(w_w_zero1),.in103(w_w_zero1),.in104(w_w_zero1),.in105(w_w_zero1),.in106(w_w_zero1),.in107(w_w_zero1),.in108(w_w_zero1),.in109(w_w_zero1),.in110(w_w_zero1),.in111(w_w_zero1),.in112(w_w_zero1),.in113(w_w_zero1),.in114(w_w_zero1),.in115(w_w_zero1),.in116(w_w_zero1),.in117(w_w_zero1),.in118(w_w_zero1),.in119(w_w_zero1),.in120(w_w_zero1),.in121(w_w_zero1),.in122(w_w_zero1),.in123(w_w_zero1),.in124(w_w_zero1),.in125(w_w_zero1),.in126(w_w_zero1),.in127(w_w_zero1),.r(MulCarryOut));
endmodule

// This file was automatically created by py4hw Verilog generator
module Add8 (
	input [7:0] a,
	input [7:0] b,
	output [7:0] r);
wire w_ci;

assign w_ci = 0;
assign r = a + b + w_ci;
endmodule

// This file was automatically created by py4hw Verilog generator
module Add16 (
	input [15:0] a,
	input [15:0] b,
	output [15:0] r);
wire w_ci;

assign w_ci = 0;
assign r = a + b + w_ci;
endmodule

// This file was automatically created by py4hw Verilog generator
module ShiftLeft_7f9e35c78740 (
	input [7:0] a,
	input [2:0] b,
	output [7:0] r);
wire w_doShift2;
wire [7:0] w_shift_0;
wire [7:0] w_shifted0;
wire [7:0] w_shift_1;
wire [7:0] w_shifted1;
wire w_doShift0;
wire [7:0] w_shift_2;
wire w_doShift1;
wire [7:0] w_shifted2;

assign w_shifted0 = a << 1;
assign w_doShift0 = b[0];
assign w_shift_0 = (w_doShift0)? w_shifted0 : a;
assign w_shifted1 = w_shift_0 << 2;
assign w_doShift1 = b[1];
assign w_shift_1 = (w_doShift1)? w_shifted1 : w_shift_0;
assign w_shifted2 = w_shift_1 << 4;
assign w_doShift2 = b[2];
assign w_shift_2 = (w_doShift2)? w_shifted2 : w_shift_1;
assign r = w_shift_2;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35c79b20 (
	input  sel,
	input [7:0] in0,
	input [7:0] in1,
	output [7:0] r);

assign r = (sel)? in1 : in0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35c7bb00 (
	input [6:0] sel,
	input [7:0] in0,
	input [7:0] in1,
	input [7:0] in2,
	input [7:0] in3,
	input [7:0] in4,
	input [7:0] in5,
	input [7:0] in6,
	input [7:0] in7,
	input [7:0] in8,
	input [7:0] in9,
	input [7:0] in10,
	input [7:0] in11,
	input [7:0] in12,
	input [7:0] in13,
	input [7:0] in14,
	input [7:0] in15,
	input [7:0] in16,
	input [7:0] in17,
	input [7:0] in18,
	input [7:0] in19,
	input [7:0] in20,
	input [7:0] in21,
	input [7:0] in22,
	input [7:0] in23,
	input [7:0] in24,
	input [7:0] in25,
	input [7:0] in26,
	input [7:0] in27,
	input [7:0] in28,
	input [7:0] in29,
	input [7:0] in30,
	input [7:0] in31,
	input [7:0] in32,
	input [7:0] in33,
	input [7:0] in34,
	input [7:0] in35,
	input [7:0] in36,
	input [7:0] in37,
	input [7:0] in38,
	input [7:0] in39,
	input [7:0] in40,
	input [7:0] in41,
	input [7:0] in42,
	input [7:0] in43,
	input [7:0] in44,
	input [7:0] in45,
	input [7:0] in46,
	input [7:0] in47,
	input [7:0] in48,
	input [7:0] in49,
	input [7:0] in50,
	input [7:0] in51,
	input [7:0] in52,
	input [7:0] in53,
	input [7:0] in54,
	input [7:0] in55,
	input [7:0] in56,
	input [7:0] in57,
	input [7:0] in58,
	input [7:0] in59,
	input [7:0] in60,
	input [7:0] in61,
	input [7:0] in62,
	input [7:0] in63,
	input [7:0] in64,
	input [7:0] in65,
	input [7:0] in66,
	input [7:0] in67,
	input [7:0] in68,
	input [7:0] in69,
	input [7:0] in70,
	input [7:0] in71,
	input [7:0] in72,
	input [7:0] in73,
	input [7:0] in74,
	input [7:0] in75,
	input [7:0] in76,
	input [7:0] in77,
	input [7:0] in78,
	input [7:0] in79,
	input [7:0] in80,
	input [7:0] in81,
	input [7:0] in82,
	input [7:0] in83,
	input [7:0] in84,
	input [7:0] in85,
	input [7:0] in86,
	input [7:0] in87,
	input [7:0] in88,
	input [7:0] in89,
	input [7:0] in90,
	input [7:0] in91,
	input [7:0] in92,
	input [7:0] in93,
	input [7:0] in94,
	input [7:0] in95,
	input [7:0] in96,
	input [7:0] in97,
	input [7:0] in98,
	input [7:0] in99,
	input [7:0] in100,
	input [7:0] in101,
	input [7:0] in102,
	input [7:0] in103,
	input [7:0] in104,
	input [7:0] in105,
	input [7:0] in106,
	input [7:0] in107,
	input [7:0] in108,
	input [7:0] in109,
	input [7:0] in110,
	input [7:0] in111,
	input [7:0] in112,
	input [7:0] in113,
	input [7:0] in114,
	input [7:0] in115,
	input [7:0] in116,
	input [7:0] in117,
	input [7:0] in118,
	input [7:0] in119,
	input [7:0] in120,
	input [7:0] in121,
	input [7:0] in122,
	input [7:0] in123,
	input [7:0] in124,
	input [7:0] in125,
	input [7:0] in126,
	input [7:0] in127,
	output [7:0] r);
wire [7:0] w_l0_56;
wire [7:0] w_l1_15;
wire [7:0] w_l0_57;
wire [7:0] w_l1_16;
wire [7:0] w_l5_0;
wire [7:0] w_l0_58;
wire [7:0] w_l1_17;
wire [7:0] w_l5_1;
wire [7:0] w_l0_59;
wire [7:0] w_l1_18;
wire [7:0] w_l2_0;
wire [7:0] w_l0_60;
wire [7:0] w_l1_19;
wire [7:0] w_l2_1;
wire [7:0] w_l0_61;
wire [7:0] w_l1_20;
wire [7:0] w_l2_2;
wire [7:0] w_l0_62;
wire [7:0] w_l1_21;
wire [7:0] w_l2_3;
wire [7:0] w_l0_63;
wire [7:0] w_l1_22;
wire [7:0] w_l2_4;
wire [7:0] w_l1_23;
wire [7:0] w_l2_5;
wire [7:0] w_l1_24;
wire [7:0] w_l2_6;
wire [7:0] w_l1_25;
wire [7:0] w_l2_7;
wire [7:0] w_l1_26;
wire [7:0] w_l2_8;
wire [7:0] w_l1_27;
wire [7:0] w_l2_9;
wire [7:0] w_l1_28;
wire w_sel_bits_1;
wire [7:0] w_l2_10;
wire w_sel_bits_2;
wire [7:0] w_l1_29;
wire w_sel_bits_3;
wire [7:0] w_l2_11;
wire w_sel_bits_4;
wire [7:0] w_l1_30;
wire [7:0] w_l3_0;
wire w_sel_bits_5;
wire [7:0] w_l2_12;
wire w_sel_bits_6;
wire [7:0] w_l1_31;
wire [7:0] w_l3_1;
wire [7:0] w_l2_13;
wire [7:0] w_l3_2;
wire [7:0] w_l2_14;
wire [7:0] w_l3_3;
wire [7:0] w_l2_15;
wire [7:0] w_l3_4;
wire [7:0] w_l3_5;
wire [7:0] w_l3_6;
wire [7:0] w_l3_7;
wire [7:0] w_l0_0;
wire [7:0] w_l0_1;
wire [7:0] w_l0_2;
wire [7:0] w_l0_3;
wire [7:0] w_l0_4;
wire [7:0] w_l0_5;
wire [7:0] w_l0_6;
wire [7:0] w_l0_7;
wire [7:0] w_l0_8;
wire [7:0] w_l0_9;
wire [7:0] w_l0_10;
wire [7:0] w_l0_11;
wire [7:0] w_l0_12;
wire [7:0] w_l0_13;
wire [7:0] w_l0_14;
wire [7:0] w_l0_15;
wire [7:0] w_l0_16;
wire [7:0] w_l1_14;
wire [7:0] w_l0_17;
wire [7:0] w_l0_18;
wire [7:0] w_l0_19;
wire [7:0] w_l0_20;
wire [7:0] w_l0_21;
wire [7:0] w_l0_22;
wire [7:0] w_l0_23;
wire [7:0] w_l0_24;
wire [7:0] w_l0_25;
wire [7:0] w_l0_26;
wire [7:0] w_l0_27;
wire [7:0] w_l0_28;
wire [7:0] w_l0_29;
wire [7:0] w_l0_30;
wire [7:0] w_l0_31;
wire [7:0] w_l0_32;
wire [7:0] w_l0_33;
wire [7:0] w_l4_0;
wire [7:0] w_l0_34;
wire [7:0] w_l4_1;
wire [7:0] w_l0_35;
wire [7:0] w_l4_2;
wire [7:0] w_l0_36;
wire [7:0] w_l4_3;
wire [7:0] w_l0_37;
wire [7:0] w_l0_38;
wire [7:0] w_l0_39;
wire [7:0] w_l0_40;
wire [7:0] w_l0_41;
wire [7:0] w_l1_0;
wire [7:0] w_l0_42;
wire [7:0] w_l1_1;
wire [7:0] w_l0_43;
wire [7:0] w_l1_2;
wire [7:0] w_l0_44;
wire [7:0] w_l1_3;
wire [7:0] w_l0_45;
wire [7:0] w_l1_4;
wire w_sel_bits_0;
wire [7:0] w_l0_46;
wire [7:0] w_l1_5;
wire [7:0] w_l0_47;
wire [7:0] w_l1_6;
wire [7:0] w_l0_48;
wire [7:0] w_l1_7;
wire [7:0] w_l0_49;
wire [7:0] w_l1_8;
wire [7:0] w_l0_50;
wire [7:0] w_l1_9;
wire [7:0] w_l0_51;
wire [7:0] w_l1_10;
wire [7:0] w_l0_52;
wire [7:0] w_l1_11;
wire [7:0] w_l0_53;
wire [7:0] w_l1_12;
wire [7:0] w_l0_54;
wire [7:0] w_l1_13;
wire [7:0] w_l0_55;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_sel_bits_3 = sel[3];
assign w_sel_bits_4 = sel[4];
assign w_sel_bits_5 = sel[5];
assign w_sel_bits_6 = sel[6];
assign w_l0_0 = (w_sel_bits_0)? in1 : in127;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in40 : in40;
assign w_l0_3 = (w_sel_bits_0)? in39 : in39;
assign w_l0_4 = (w_sel_bits_0)? in20 : in8;
assign w_l0_5 = (w_sel_bits_0)? in16 : in20;
assign w_l0_6 = (w_sel_bits_0)? in21 : in16;
assign w_l0_7 = (w_sel_bits_0)? in15 : in14;
assign w_l0_8 = (w_sel_bits_0)? in17 : in16;
assign w_l0_9 = (w_sel_bits_0)? in19 : in18;
assign w_l0_10 = (w_sel_bits_0)? in21 : in20;
assign w_l0_11 = (w_sel_bits_0)? in23 : in22;
assign w_l0_12 = (w_sel_bits_0)? in25 : in24;
assign w_l0_13 = (w_sel_bits_0)? in27 : in26;
assign w_l0_14 = (w_sel_bits_0)? in127 : in28;
assign w_l0_15 = (w_sel_bits_0)? in127 : in127;
assign w_l0_16 = (w_sel_bits_0)? in127 : in127;
assign w_l0_17 = (w_sel_bits_0)? in127 : in127;
assign w_l0_18 = (w_sel_bits_0)? in127 : in127;
assign w_l0_19 = (w_sel_bits_0)? in39 : in40;
assign w_l0_20 = (w_sel_bits_0)? in127 : in40;
assign w_l0_21 = (w_sel_bits_0)? in127 : in127;
assign w_l0_22 = (w_sel_bits_0)? in127 : in127;
assign w_l0_23 = (w_sel_bits_0)? in127 : in127;
assign w_l0_24 = (w_sel_bits_0)? in127 : in127;
assign w_l0_25 = (w_sel_bits_0)? in127 : in127;
assign w_l0_26 = (w_sel_bits_0)? in127 : in127;
assign w_l0_27 = (w_sel_bits_0)? in127 : in127;
assign w_l0_28 = (w_sel_bits_0)? in127 : in127;
assign w_l0_29 = (w_sel_bits_0)? in127 : in127;
assign w_l0_30 = (w_sel_bits_0)? in127 : in127;
assign w_l0_31 = (w_sel_bits_0)? in127 : in127;
assign w_l0_32 = (w_sel_bits_0)? in65 : in127;
assign w_l0_33 = (w_sel_bits_0)? in67 : in66;
assign w_l0_34 = (w_sel_bits_0)? in69 : in68;
assign w_l0_35 = (w_sel_bits_0)? in71 : in70;
assign w_l0_36 = (w_sel_bits_0)? in127 : in72;
assign w_l0_37 = (w_sel_bits_0)? in127 : in127;
assign w_l0_38 = (w_sel_bits_0)? in127 : in76;
assign w_l0_39 = (w_sel_bits_0)? in127 : in127;
assign w_l0_40 = (w_sel_bits_0)? in127 : in127;
assign w_l0_41 = (w_sel_bits_0)? in127 : in127;
assign w_l0_42 = (w_sel_bits_0)? in127 : in127;
assign w_l0_43 = (w_sel_bits_0)? in127 : in127;
assign w_l0_44 = (w_sel_bits_0)? in127 : in127;
assign w_l0_45 = (w_sel_bits_0)? in127 : in127;
assign w_l0_46 = (w_sel_bits_0)? in93 : in127;
assign w_l0_47 = (w_sel_bits_0)? in127 : in127;
assign w_l0_48 = (w_sel_bits_0)? in127 : in127;
assign w_l0_49 = (w_sel_bits_0)? in127 : in127;
assign w_l0_50 = (w_sel_bits_0)? in127 : in127;
assign w_l0_51 = (w_sel_bits_0)? in127 : in127;
assign w_l0_52 = (w_sel_bits_0)? in127 : in127;
assign w_l0_53 = (w_sel_bits_0)? in127 : in127;
assign w_l0_54 = (w_sel_bits_0)? in127 : in127;
assign w_l0_55 = (w_sel_bits_0)? in127 : in127;
assign w_l0_56 = (w_sel_bits_0)? in127 : in127;
assign w_l0_57 = (w_sel_bits_0)? in127 : in127;
assign w_l0_58 = (w_sel_bits_0)? in127 : in127;
assign w_l0_59 = (w_sel_bits_0)? in127 : in127;
assign w_l0_60 = (w_sel_bits_0)? in127 : in127;
assign w_l0_61 = (w_sel_bits_0)? in127 : in127;
assign w_l0_62 = (w_sel_bits_0)? in127 : in127;
assign w_l0_63 = (w_sel_bits_0)? in127 : in127;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign w_l1_2 = (w_sel_bits_1)? w_l0_5 : w_l0_4;
assign w_l1_3 = (w_sel_bits_1)? w_l0_7 : w_l0_6;
assign w_l1_4 = (w_sel_bits_1)? w_l0_9 : w_l0_8;
assign w_l1_5 = (w_sel_bits_1)? w_l0_11 : w_l0_10;
assign w_l1_6 = (w_sel_bits_1)? w_l0_13 : w_l0_12;
assign w_l1_7 = (w_sel_bits_1)? w_l0_15 : w_l0_14;
assign w_l1_8 = (w_sel_bits_1)? w_l0_17 : w_l0_16;
assign w_l1_9 = (w_sel_bits_1)? w_l0_19 : w_l0_18;
assign w_l1_10 = (w_sel_bits_1)? w_l0_21 : w_l0_20;
assign w_l1_11 = (w_sel_bits_1)? w_l0_23 : w_l0_22;
assign w_l1_12 = (w_sel_bits_1)? w_l0_25 : w_l0_24;
assign w_l1_13 = (w_sel_bits_1)? w_l0_27 : w_l0_26;
assign w_l1_14 = (w_sel_bits_1)? w_l0_29 : w_l0_28;
assign w_l1_15 = (w_sel_bits_1)? w_l0_31 : w_l0_30;
assign w_l1_16 = (w_sel_bits_1)? w_l0_33 : w_l0_32;
assign w_l1_17 = (w_sel_bits_1)? w_l0_35 : w_l0_34;
assign w_l1_18 = (w_sel_bits_1)? w_l0_37 : w_l0_36;
assign w_l1_19 = (w_sel_bits_1)? w_l0_39 : w_l0_38;
assign w_l1_20 = (w_sel_bits_1)? w_l0_41 : w_l0_40;
assign w_l1_21 = (w_sel_bits_1)? w_l0_43 : w_l0_42;
assign w_l1_22 = (w_sel_bits_1)? w_l0_45 : w_l0_44;
assign w_l1_23 = (w_sel_bits_1)? w_l0_47 : w_l0_46;
assign w_l1_24 = (w_sel_bits_1)? w_l0_49 : w_l0_48;
assign w_l1_25 = (w_sel_bits_1)? w_l0_51 : w_l0_50;
assign w_l1_26 = (w_sel_bits_1)? w_l0_53 : w_l0_52;
assign w_l1_27 = (w_sel_bits_1)? w_l0_55 : w_l0_54;
assign w_l1_28 = (w_sel_bits_1)? w_l0_57 : w_l0_56;
assign w_l1_29 = (w_sel_bits_1)? w_l0_59 : w_l0_58;
assign w_l1_30 = (w_sel_bits_1)? w_l0_61 : w_l0_60;
assign w_l1_31 = (w_sel_bits_1)? w_l0_63 : w_l0_62;
assign w_l2_0 = (w_sel_bits_2)? w_l1_1 : w_l1_0;
assign w_l2_1 = (w_sel_bits_2)? w_l1_3 : w_l1_2;
assign w_l2_2 = (w_sel_bits_2)? w_l1_5 : w_l1_4;
assign w_l2_3 = (w_sel_bits_2)? w_l1_7 : w_l1_6;
assign w_l2_4 = (w_sel_bits_2)? w_l1_9 : w_l1_8;
assign w_l2_5 = (w_sel_bits_2)? w_l1_11 : w_l1_10;
assign w_l2_6 = (w_sel_bits_2)? w_l1_13 : w_l1_12;
assign w_l2_7 = (w_sel_bits_2)? w_l1_15 : w_l1_14;
assign w_l2_8 = (w_sel_bits_2)? w_l1_17 : w_l1_16;
assign w_l2_9 = (w_sel_bits_2)? w_l1_19 : w_l1_18;
assign w_l2_10 = (w_sel_bits_2)? w_l1_21 : w_l1_20;
assign w_l2_11 = (w_sel_bits_2)? w_l1_23 : w_l1_22;
assign w_l2_12 = (w_sel_bits_2)? w_l1_25 : w_l1_24;
assign w_l2_13 = (w_sel_bits_2)? w_l1_27 : w_l1_26;
assign w_l2_14 = (w_sel_bits_2)? w_l1_29 : w_l1_28;
assign w_l2_15 = (w_sel_bits_2)? w_l1_31 : w_l1_30;
assign w_l3_0 = (w_sel_bits_3)? w_l2_1 : w_l2_0;
assign w_l3_1 = (w_sel_bits_3)? w_l2_3 : w_l2_2;
assign w_l3_2 = (w_sel_bits_3)? w_l2_5 : w_l2_4;
assign w_l3_3 = (w_sel_bits_3)? w_l2_7 : w_l2_6;
assign w_l3_4 = (w_sel_bits_3)? w_l2_9 : w_l2_8;
assign w_l3_5 = (w_sel_bits_3)? w_l2_11 : w_l2_10;
assign w_l3_6 = (w_sel_bits_3)? w_l2_13 : w_l2_12;
assign w_l3_7 = (w_sel_bits_3)? w_l2_15 : w_l2_14;
assign w_l4_0 = (w_sel_bits_4)? w_l3_1 : w_l3_0;
assign w_l4_1 = (w_sel_bits_4)? w_l3_3 : w_l3_2;
assign w_l4_2 = (w_sel_bits_4)? w_l3_5 : w_l3_4;
assign w_l4_3 = (w_sel_bits_4)? w_l3_7 : w_l3_6;
assign w_l5_0 = (w_sel_bits_5)? w_l4_1 : w_l4_0;
assign w_l5_1 = (w_sel_bits_5)? w_l4_3 : w_l4_2;
assign r = (w_sel_bits_6)? w_l5_1 : w_l5_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35c7bb30 (
	input [6:0] sel,
	input [7:0] in0,
	input [7:0] in1,
	input [7:0] in2,
	input [7:0] in3,
	input [7:0] in4,
	input [7:0] in5,
	input [7:0] in6,
	input [7:0] in7,
	input [7:0] in8,
	input [7:0] in9,
	input [7:0] in10,
	input [7:0] in11,
	input [7:0] in12,
	input [7:0] in13,
	input [7:0] in14,
	input [7:0] in15,
	input [7:0] in16,
	input [7:0] in17,
	input [7:0] in18,
	input [7:0] in19,
	input [7:0] in20,
	input [7:0] in21,
	input [7:0] in22,
	input [7:0] in23,
	input [7:0] in24,
	input [7:0] in25,
	input [7:0] in26,
	input [7:0] in27,
	input [7:0] in28,
	input [7:0] in29,
	input [7:0] in30,
	input [7:0] in31,
	input [7:0] in32,
	input [7:0] in33,
	input [7:0] in34,
	input [7:0] in35,
	input [7:0] in36,
	input [7:0] in37,
	input [7:0] in38,
	input [7:0] in39,
	input [7:0] in40,
	input [7:0] in41,
	input [7:0] in42,
	input [7:0] in43,
	input [7:0] in44,
	input [7:0] in45,
	input [7:0] in46,
	input [7:0] in47,
	input [7:0] in48,
	input [7:0] in49,
	input [7:0] in50,
	input [7:0] in51,
	input [7:0] in52,
	input [7:0] in53,
	input [7:0] in54,
	input [7:0] in55,
	input [7:0] in56,
	input [7:0] in57,
	input [7:0] in58,
	input [7:0] in59,
	input [7:0] in60,
	input [7:0] in61,
	input [7:0] in62,
	input [7:0] in63,
	input [7:0] in64,
	input [7:0] in65,
	input [7:0] in66,
	input [7:0] in67,
	input [7:0] in68,
	input [7:0] in69,
	input [7:0] in70,
	input [7:0] in71,
	input [7:0] in72,
	input [7:0] in73,
	input [7:0] in74,
	input [7:0] in75,
	input [7:0] in76,
	input [7:0] in77,
	input [7:0] in78,
	input [7:0] in79,
	input [7:0] in80,
	input [7:0] in81,
	input [7:0] in82,
	input [7:0] in83,
	input [7:0] in84,
	input [7:0] in85,
	input [7:0] in86,
	input [7:0] in87,
	input [7:0] in88,
	input [7:0] in89,
	input [7:0] in90,
	input [7:0] in91,
	input [7:0] in92,
	input [7:0] in93,
	input [7:0] in94,
	input [7:0] in95,
	input [7:0] in96,
	input [7:0] in97,
	input [7:0] in98,
	input [7:0] in99,
	input [7:0] in100,
	input [7:0] in101,
	input [7:0] in102,
	input [7:0] in103,
	input [7:0] in104,
	input [7:0] in105,
	input [7:0] in106,
	input [7:0] in107,
	input [7:0] in108,
	input [7:0] in109,
	input [7:0] in110,
	input [7:0] in111,
	input [7:0] in112,
	input [7:0] in113,
	input [7:0] in114,
	input [7:0] in115,
	input [7:0] in116,
	input [7:0] in117,
	input [7:0] in118,
	input [7:0] in119,
	input [7:0] in120,
	input [7:0] in121,
	input [7:0] in122,
	input [7:0] in123,
	input [7:0] in124,
	input [7:0] in125,
	input [7:0] in126,
	input [7:0] in127,
	output [7:0] r);
wire [7:0] w_l0_28;
wire [7:0] w_l0_29;
wire [7:0] w_l0_30;
wire [7:0] w_l0_31;
wire [7:0] w_l0_32;
wire [7:0] w_l0_33;
wire [7:0] w_l0_34;
wire [7:0] w_l0_35;
wire [7:0] w_l0_36;
wire [7:0] w_l0_37;
wire [7:0] w_l0_38;
wire [7:0] w_l0_39;
wire [7:0] w_l0_40;
wire [7:0] w_l4_0;
wire [7:0] w_l0_41;
wire [7:0] w_l4_1;
wire [7:0] w_l0_42;
wire [7:0] w_l4_2;
wire [7:0] w_l0_43;
wire [7:0] w_l4_3;
wire [7:0] w_l0_44;
wire [7:0] w_l1_0;
wire [7:0] w_l0_45;
wire [7:0] w_l1_1;
wire w_sel_bits_0;
wire [7:0] w_l0_46;
wire [7:0] w_l1_2;
wire [7:0] w_l0_47;
wire [7:0] w_l1_3;
wire [7:0] w_l0_48;
wire [7:0] w_l1_4;
wire [7:0] w_l0_49;
wire [7:0] w_l1_5;
wire [7:0] w_l0_50;
wire [7:0] w_l1_6;
wire [7:0] w_l0_51;
wire [7:0] w_l1_7;
wire [7:0] w_l0_52;
wire [7:0] w_l1_8;
wire [7:0] w_l0_53;
wire [7:0] w_l1_9;
wire [7:0] w_l0_54;
wire [7:0] w_l1_10;
wire [7:0] w_l0_55;
wire [7:0] w_l1_11;
wire [7:0] w_l0_56;
wire [7:0] w_l1_12;
wire [7:0] w_l0_57;
wire [7:0] w_l1_13;
wire [7:0] w_l0_58;
wire [7:0] w_l1_14;
wire [7:0] w_l0_59;
wire [7:0] w_l1_15;
wire [7:0] w_l0_60;
wire [7:0] w_l1_16;
wire [7:0] w_l0_61;
wire [7:0] w_l1_17;
wire [7:0] w_l0_62;
wire [7:0] w_l1_18;
wire [7:0] w_l0_63;
wire [7:0] w_l1_19;
wire [7:0] w_l1_20;
wire [7:0] w_l5_0;
wire [7:0] w_l1_21;
wire [7:0] w_l5_1;
wire [7:0] w_l1_22;
wire [7:0] w_l2_0;
wire [7:0] w_l1_23;
wire [7:0] w_l2_1;
wire [7:0] w_l1_24;
wire w_sel_bits_1;
wire [7:0] w_l2_2;
wire w_sel_bits_2;
wire [7:0] w_l1_25;
wire w_sel_bits_3;
wire [7:0] w_l2_3;
wire w_sel_bits_4;
wire [7:0] w_l1_26;
wire w_sel_bits_5;
wire [7:0] w_l2_4;
wire w_sel_bits_6;
wire [7:0] w_l1_27;
wire [7:0] w_l2_5;
wire [7:0] w_l1_28;
wire [7:0] w_l2_6;
wire [7:0] w_l1_29;
wire [7:0] w_l2_7;
wire [7:0] w_l1_30;
wire [7:0] w_l2_8;
wire [7:0] w_l1_31;
wire [7:0] w_l2_9;
wire [7:0] w_l2_10;
wire [7:0] w_l3_0;
wire [7:0] w_l2_11;
wire [7:0] w_l3_1;
wire [7:0] w_l2_12;
wire [7:0] w_l3_2;
wire [7:0] w_l2_13;
wire [7:0] w_l3_3;
wire [7:0] w_l2_14;
wire [7:0] w_l3_4;
wire [7:0] w_l2_15;
wire [7:0] w_l3_5;
wire [7:0] w_l3_6;
wire [7:0] w_l3_7;
wire [7:0] w_l0_0;
wire [7:0] w_l0_1;
wire [7:0] w_l0_2;
wire [7:0] w_l0_3;
wire [7:0] w_l0_4;
wire [7:0] w_l0_5;
wire [7:0] w_l0_6;
wire [7:0] w_l0_7;
wire [7:0] w_l0_8;
wire [7:0] w_l0_9;
wire [7:0] w_l0_10;
wire [7:0] w_l0_11;
wire [7:0] w_l0_12;
wire [7:0] w_l0_13;
wire [7:0] w_l0_14;
wire [7:0] w_l0_15;
wire [7:0] w_l0_16;
wire [7:0] w_l0_17;
wire [7:0] w_l0_18;
wire [7:0] w_l0_19;
wire [7:0] w_l0_20;
wire [7:0] w_l0_21;
wire [7:0] w_l0_22;
wire [7:0] w_l0_23;
wire [7:0] w_l0_24;
wire [7:0] w_l0_25;
wire [7:0] w_l0_26;
wire [7:0] w_l0_27;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_sel_bits_3 = sel[3];
assign w_sel_bits_4 = sel[4];
assign w_sel_bits_5 = sel[5];
assign w_sel_bits_6 = sel[6];
assign w_l0_0 = (w_sel_bits_0)? in127 : in127;
assign w_l0_1 = (w_sel_bits_0)? in3 : in127;
assign w_l0_2 = (w_sel_bits_0)? in127 : in127;
assign w_l0_3 = (w_sel_bits_0)? in127 : in127;
assign w_l0_4 = (w_sel_bits_0)? in127 : in8;
assign w_l0_5 = (w_sel_bits_0)? in127 : in127;
assign w_l0_6 = (w_sel_bits_0)? in127 : in127;
assign w_l0_7 = (w_sel_bits_0)? in127 : in127;
assign w_l0_8 = (w_sel_bits_0)? in127 : in127;
assign w_l0_9 = (w_sel_bits_0)? in127 : in127;
assign w_l0_10 = (w_sel_bits_0)? in127 : in127;
assign w_l0_11 = (w_sel_bits_0)? in23 : in127;
assign w_l0_12 = (w_sel_bits_0)? in25 : in24;
assign w_l0_13 = (w_sel_bits_0)? in27 : in26;
assign w_l0_14 = (w_sel_bits_0)? in127 : in28;
assign w_l0_15 = (w_sel_bits_0)? in127 : in127;
assign w_l0_16 = (w_sel_bits_0)? in127 : in127;
assign w_l0_17 = (w_sel_bits_0)? in127 : in127;
assign w_l0_18 = (w_sel_bits_0)? in127 : in127;
assign w_l0_19 = (w_sel_bits_0)? in127 : in127;
assign w_l0_20 = (w_sel_bits_0)? in127 : in127;
assign w_l0_21 = (w_sel_bits_0)? in127 : in127;
assign w_l0_22 = (w_sel_bits_0)? in127 : in127;
assign w_l0_23 = (w_sel_bits_0)? in127 : in127;
assign w_l0_24 = (w_sel_bits_0)? in127 : in127;
assign w_l0_25 = (w_sel_bits_0)? in127 : in127;
assign w_l0_26 = (w_sel_bits_0)? in127 : in127;
assign w_l0_27 = (w_sel_bits_0)? in127 : in127;
assign w_l0_28 = (w_sel_bits_0)? in127 : in127;
assign w_l0_29 = (w_sel_bits_0)? in127 : in127;
assign w_l0_30 = (w_sel_bits_0)? in127 : in127;
assign w_l0_31 = (w_sel_bits_0)? in127 : in127;
assign w_l0_32 = (w_sel_bits_0)? in127 : in127;
assign w_l0_33 = (w_sel_bits_0)? in127 : in127;
assign w_l0_34 = (w_sel_bits_0)? in127 : in127;
assign w_l0_35 = (w_sel_bits_0)? in127 : in127;
assign w_l0_36 = (w_sel_bits_0)? in127 : in127;
assign w_l0_37 = (w_sel_bits_0)? in127 : in127;
assign w_l0_38 = (w_sel_bits_0)? in127 : in127;
assign w_l0_39 = (w_sel_bits_0)? in127 : in127;
assign w_l0_40 = (w_sel_bits_0)? in127 : in127;
assign w_l0_41 = (w_sel_bits_0)? in127 : in127;
assign w_l0_42 = (w_sel_bits_0)? in127 : in127;
assign w_l0_43 = (w_sel_bits_0)? in127 : in127;
assign w_l0_44 = (w_sel_bits_0)? in127 : in127;
assign w_l0_45 = (w_sel_bits_0)? in127 : in127;
assign w_l0_46 = (w_sel_bits_0)? in127 : in127;
assign w_l0_47 = (w_sel_bits_0)? in127 : in127;
assign w_l0_48 = (w_sel_bits_0)? in127 : in127;
assign w_l0_49 = (w_sel_bits_0)? in127 : in127;
assign w_l0_50 = (w_sel_bits_0)? in127 : in127;
assign w_l0_51 = (w_sel_bits_0)? in127 : in127;
assign w_l0_52 = (w_sel_bits_0)? in127 : in127;
assign w_l0_53 = (w_sel_bits_0)? in127 : in127;
assign w_l0_54 = (w_sel_bits_0)? in127 : in127;
assign w_l0_55 = (w_sel_bits_0)? in127 : in127;
assign w_l0_56 = (w_sel_bits_0)? in127 : in127;
assign w_l0_57 = (w_sel_bits_0)? in127 : in127;
assign w_l0_58 = (w_sel_bits_0)? in127 : in127;
assign w_l0_59 = (w_sel_bits_0)? in127 : in127;
assign w_l0_60 = (w_sel_bits_0)? in127 : in127;
assign w_l0_61 = (w_sel_bits_0)? in127 : in127;
assign w_l0_62 = (w_sel_bits_0)? in127 : in127;
assign w_l0_63 = (w_sel_bits_0)? in127 : in127;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign w_l1_2 = (w_sel_bits_1)? w_l0_5 : w_l0_4;
assign w_l1_3 = (w_sel_bits_1)? w_l0_7 : w_l0_6;
assign w_l1_4 = (w_sel_bits_1)? w_l0_9 : w_l0_8;
assign w_l1_5 = (w_sel_bits_1)? w_l0_11 : w_l0_10;
assign w_l1_6 = (w_sel_bits_1)? w_l0_13 : w_l0_12;
assign w_l1_7 = (w_sel_bits_1)? w_l0_15 : w_l0_14;
assign w_l1_8 = (w_sel_bits_1)? w_l0_17 : w_l0_16;
assign w_l1_9 = (w_sel_bits_1)? w_l0_19 : w_l0_18;
assign w_l1_10 = (w_sel_bits_1)? w_l0_21 : w_l0_20;
assign w_l1_11 = (w_sel_bits_1)? w_l0_23 : w_l0_22;
assign w_l1_12 = (w_sel_bits_1)? w_l0_25 : w_l0_24;
assign w_l1_13 = (w_sel_bits_1)? w_l0_27 : w_l0_26;
assign w_l1_14 = (w_sel_bits_1)? w_l0_29 : w_l0_28;
assign w_l1_15 = (w_sel_bits_1)? w_l0_31 : w_l0_30;
assign w_l1_16 = (w_sel_bits_1)? w_l0_33 : w_l0_32;
assign w_l1_17 = (w_sel_bits_1)? w_l0_35 : w_l0_34;
assign w_l1_18 = (w_sel_bits_1)? w_l0_37 : w_l0_36;
assign w_l1_19 = (w_sel_bits_1)? w_l0_39 : w_l0_38;
assign w_l1_20 = (w_sel_bits_1)? w_l0_41 : w_l0_40;
assign w_l1_21 = (w_sel_bits_1)? w_l0_43 : w_l0_42;
assign w_l1_22 = (w_sel_bits_1)? w_l0_45 : w_l0_44;
assign w_l1_23 = (w_sel_bits_1)? w_l0_47 : w_l0_46;
assign w_l1_24 = (w_sel_bits_1)? w_l0_49 : w_l0_48;
assign w_l1_25 = (w_sel_bits_1)? w_l0_51 : w_l0_50;
assign w_l1_26 = (w_sel_bits_1)? w_l0_53 : w_l0_52;
assign w_l1_27 = (w_sel_bits_1)? w_l0_55 : w_l0_54;
assign w_l1_28 = (w_sel_bits_1)? w_l0_57 : w_l0_56;
assign w_l1_29 = (w_sel_bits_1)? w_l0_59 : w_l0_58;
assign w_l1_30 = (w_sel_bits_1)? w_l0_61 : w_l0_60;
assign w_l1_31 = (w_sel_bits_1)? w_l0_63 : w_l0_62;
assign w_l2_0 = (w_sel_bits_2)? w_l1_1 : w_l1_0;
assign w_l2_1 = (w_sel_bits_2)? w_l1_3 : w_l1_2;
assign w_l2_2 = (w_sel_bits_2)? w_l1_5 : w_l1_4;
assign w_l2_3 = (w_sel_bits_2)? w_l1_7 : w_l1_6;
assign w_l2_4 = (w_sel_bits_2)? w_l1_9 : w_l1_8;
assign w_l2_5 = (w_sel_bits_2)? w_l1_11 : w_l1_10;
assign w_l2_6 = (w_sel_bits_2)? w_l1_13 : w_l1_12;
assign w_l2_7 = (w_sel_bits_2)? w_l1_15 : w_l1_14;
assign w_l2_8 = (w_sel_bits_2)? w_l1_17 : w_l1_16;
assign w_l2_9 = (w_sel_bits_2)? w_l1_19 : w_l1_18;
assign w_l2_10 = (w_sel_bits_2)? w_l1_21 : w_l1_20;
assign w_l2_11 = (w_sel_bits_2)? w_l1_23 : w_l1_22;
assign w_l2_12 = (w_sel_bits_2)? w_l1_25 : w_l1_24;
assign w_l2_13 = (w_sel_bits_2)? w_l1_27 : w_l1_26;
assign w_l2_14 = (w_sel_bits_2)? w_l1_29 : w_l1_28;
assign w_l2_15 = (w_sel_bits_2)? w_l1_31 : w_l1_30;
assign w_l3_0 = (w_sel_bits_3)? w_l2_1 : w_l2_0;
assign w_l3_1 = (w_sel_bits_3)? w_l2_3 : w_l2_2;
assign w_l3_2 = (w_sel_bits_3)? w_l2_5 : w_l2_4;
assign w_l3_3 = (w_sel_bits_3)? w_l2_7 : w_l2_6;
assign w_l3_4 = (w_sel_bits_3)? w_l2_9 : w_l2_8;
assign w_l3_5 = (w_sel_bits_3)? w_l2_11 : w_l2_10;
assign w_l3_6 = (w_sel_bits_3)? w_l2_13 : w_l2_12;
assign w_l3_7 = (w_sel_bits_3)? w_l2_15 : w_l2_14;
assign w_l4_0 = (w_sel_bits_4)? w_l3_1 : w_l3_0;
assign w_l4_1 = (w_sel_bits_4)? w_l3_3 : w_l3_2;
assign w_l4_2 = (w_sel_bits_4)? w_l3_5 : w_l3_4;
assign w_l4_3 = (w_sel_bits_4)? w_l3_7 : w_l3_6;
assign w_l5_0 = (w_sel_bits_5)? w_l4_1 : w_l4_0;
assign w_l5_1 = (w_sel_bits_5)? w_l4_3 : w_l4_2;
assign r = (w_sel_bits_6)? w_l5_1 : w_l5_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35c94ad0 (
	input [6:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	input  in8,
	input  in9,
	input  in10,
	input  in11,
	input  in12,
	input  in13,
	input  in14,
	input  in15,
	input  in16,
	input  in17,
	input  in18,
	input  in19,
	input  in20,
	input  in21,
	input  in22,
	input  in23,
	input  in24,
	input  in25,
	input  in26,
	input  in27,
	input  in28,
	input  in29,
	input  in30,
	input  in31,
	input  in32,
	input  in33,
	input  in34,
	input  in35,
	input  in36,
	input  in37,
	input  in38,
	input  in39,
	input  in40,
	input  in41,
	input  in42,
	input  in43,
	input  in44,
	input  in45,
	input  in46,
	input  in47,
	input  in48,
	input  in49,
	input  in50,
	input  in51,
	input  in52,
	input  in53,
	input  in54,
	input  in55,
	input  in56,
	input  in57,
	input  in58,
	input  in59,
	input  in60,
	input  in61,
	input  in62,
	input  in63,
	input  in64,
	input  in65,
	input  in66,
	input  in67,
	input  in68,
	input  in69,
	input  in70,
	input  in71,
	input  in72,
	input  in73,
	input  in74,
	input  in75,
	input  in76,
	input  in77,
	input  in78,
	input  in79,
	input  in80,
	input  in81,
	input  in82,
	input  in83,
	input  in84,
	input  in85,
	input  in86,
	input  in87,
	input  in88,
	input  in89,
	input  in90,
	input  in91,
	input  in92,
	input  in93,
	input  in94,
	input  in95,
	input  in96,
	input  in97,
	input  in98,
	input  in99,
	input  in100,
	input  in101,
	input  in102,
	input  in103,
	input  in104,
	input  in105,
	input  in106,
	input  in107,
	input  in108,
	input  in109,
	input  in110,
	input  in111,
	input  in112,
	input  in113,
	input  in114,
	input  in115,
	input  in116,
	input  in117,
	input  in118,
	input  in119,
	input  in120,
	input  in121,
	input  in122,
	input  in123,
	input  in124,
	input  in125,
	input  in126,
	input  in127,
	output  r);
wire w_l2_10;
wire w_l3_0;
wire w_l2_11;
wire w_l3_1;
wire w_l2_12;
wire w_l3_2;
wire w_l2_13;
wire w_l3_3;
wire w_l2_14;
wire w_l3_4;
wire w_l2_15;
wire w_l2_9;
wire w_l3_5;
wire w_l3_6;
wire w_l3_7;
wire w_l0_0;
wire w_l0_1;
wire w_l0_2;
wire w_l0_3;
wire w_l0_4;
wire w_l0_5;
wire w_l0_6;
wire w_l0_7;
wire w_l0_8;
wire w_l0_9;
wire w_l0_10;
wire w_l0_11;
wire w_l0_12;
wire w_l0_13;
wire w_l0_14;
wire w_l0_15;
wire w_l0_16;
wire w_l0_17;
wire w_l0_18;
wire w_l0_19;
wire w_l0_20;
wire w_l0_21;
wire w_l0_22;
wire w_l0_23;
wire w_l0_24;
wire w_l0_25;
wire w_l0_26;
wire w_l0_27;
wire w_l0_28;
wire w_l0_29;
wire w_l0_30;
wire w_l0_31;
wire w_l0_32;
wire w_l0_33;
wire w_l0_34;
wire w_l0_35;
wire w_l0_36;
wire w_l0_37;
wire w_l0_38;
wire w_l0_39;
wire w_l0_40;
wire w_l4_0;
wire w_l0_41;
wire w_l4_1;
wire w_l0_42;
wire w_l4_2;
wire w_l0_43;
wire w_l4_3;
wire w_l0_44;
wire w_l1_0;
wire w_l0_45;
wire w_l1_1;
wire w_l0_46;
wire w_sel_bits_0;
wire w_l1_2;
wire w_l0_47;
wire w_l1_3;
wire w_l0_48;
wire w_l1_4;
wire w_l0_49;
wire w_l1_5;
wire w_l0_50;
wire w_l1_6;
wire w_l0_51;
wire w_l1_7;
wire w_l0_52;
wire w_l1_8;
wire w_l0_53;
wire w_l1_9;
wire w_l0_54;
wire w_l1_10;
wire w_l0_55;
wire w_l1_11;
wire w_l0_56;
wire w_l1_12;
wire w_l0_57;
wire w_l1_13;
wire w_l0_58;
wire w_l1_14;
wire w_l0_59;
wire w_l1_15;
wire w_l0_60;
wire w_l1_16;
wire w_l0_61;
wire w_l1_17;
wire w_l0_62;
wire w_l1_18;
wire w_l0_63;
wire w_l1_19;
wire w_l1_20;
wire w_l5_0;
wire w_l1_21;
wire w_l5_1;
wire w_l1_22;
wire w_l2_0;
wire w_l1_23;
wire w_l2_1;
wire w_l1_24;
wire w_l2_2;
wire w_sel_bits_1;
wire w_l1_25;
wire w_l2_3;
wire w_sel_bits_2;
wire w_sel_bits_3;
wire w_l1_26;
wire w_l2_4;
wire w_sel_bits_4;
wire w_sel_bits_5;
wire w_l1_27;
wire w_l2_5;
wire w_sel_bits_6;
wire w_l1_28;
wire w_l2_6;
wire w_l1_29;
wire w_l2_7;
wire w_l1_30;
wire w_l2_8;
wire w_l1_31;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_sel_bits_3 = sel[3];
assign w_sel_bits_4 = sel[4];
assign w_sel_bits_5 = sel[5];
assign w_sel_bits_6 = sel[6];
assign w_l0_0 = (w_sel_bits_0)? in127 : in127;
assign w_l0_1 = (w_sel_bits_0)? in127 : in127;
assign w_l0_2 = (w_sel_bits_0)? in127 : in127;
assign w_l0_3 = (w_sel_bits_0)? in127 : in127;
assign w_l0_4 = (w_sel_bits_0)? in127 : in127;
assign w_l0_5 = (w_sel_bits_0)? in127 : in127;
assign w_l0_6 = (w_sel_bits_0)? in127 : in127;
assign w_l0_7 = (w_sel_bits_0)? in127 : in127;
assign w_l0_8 = (w_sel_bits_0)? in127 : in127;
assign w_l0_9 = (w_sel_bits_0)? in127 : in127;
assign w_l0_10 = (w_sel_bits_0)? in127 : in127;
assign w_l0_11 = (w_sel_bits_0)? in26 : in127;
assign w_l0_12 = (w_sel_bits_0)? in28 : in27;
assign w_l0_13 = (w_sel_bits_0)? in27 : in26;
assign w_l0_14 = (w_sel_bits_0)? in127 : in28;
assign w_l0_15 = (w_sel_bits_0)? in127 : in127;
assign w_l0_16 = (w_sel_bits_0)? in127 : in127;
assign w_l0_17 = (w_sel_bits_0)? in127 : in127;
assign w_l0_18 = (w_sel_bits_0)? in127 : in127;
assign w_l0_19 = (w_sel_bits_0)? in127 : in127;
assign w_l0_20 = (w_sel_bits_0)? in127 : in127;
assign w_l0_21 = (w_sel_bits_0)? in127 : in127;
assign w_l0_22 = (w_sel_bits_0)? in127 : in127;
assign w_l0_23 = (w_sel_bits_0)? in127 : in127;
assign w_l0_24 = (w_sel_bits_0)? in127 : in127;
assign w_l0_25 = (w_sel_bits_0)? in127 : in127;
assign w_l0_26 = (w_sel_bits_0)? in127 : in127;
assign w_l0_27 = (w_sel_bits_0)? in127 : in127;
assign w_l0_28 = (w_sel_bits_0)? in127 : in127;
assign w_l0_29 = (w_sel_bits_0)? in127 : in127;
assign w_l0_30 = (w_sel_bits_0)? in127 : in127;
assign w_l0_31 = (w_sel_bits_0)? in127 : in127;
assign w_l0_32 = (w_sel_bits_0)? in127 : in127;
assign w_l0_33 = (w_sel_bits_0)? in127 : in127;
assign w_l0_34 = (w_sel_bits_0)? in127 : in127;
assign w_l0_35 = (w_sel_bits_0)? in127 : in127;
assign w_l0_36 = (w_sel_bits_0)? in127 : in127;
assign w_l0_37 = (w_sel_bits_0)? in127 : in127;
assign w_l0_38 = (w_sel_bits_0)? in127 : in127;
assign w_l0_39 = (w_sel_bits_0)? in127 : in127;
assign w_l0_40 = (w_sel_bits_0)? in127 : in127;
assign w_l0_41 = (w_sel_bits_0)? in127 : in127;
assign w_l0_42 = (w_sel_bits_0)? in127 : in127;
assign w_l0_43 = (w_sel_bits_0)? in127 : in127;
assign w_l0_44 = (w_sel_bits_0)? in127 : in127;
assign w_l0_45 = (w_sel_bits_0)? in127 : in127;
assign w_l0_46 = (w_sel_bits_0)? in127 : in127;
assign w_l0_47 = (w_sel_bits_0)? in127 : in127;
assign w_l0_48 = (w_sel_bits_0)? in127 : in127;
assign w_l0_49 = (w_sel_bits_0)? in127 : in127;
assign w_l0_50 = (w_sel_bits_0)? in127 : in127;
assign w_l0_51 = (w_sel_bits_0)? in127 : in127;
assign w_l0_52 = (w_sel_bits_0)? in127 : in127;
assign w_l0_53 = (w_sel_bits_0)? in127 : in127;
assign w_l0_54 = (w_sel_bits_0)? in127 : in127;
assign w_l0_55 = (w_sel_bits_0)? in127 : in127;
assign w_l0_56 = (w_sel_bits_0)? in127 : in127;
assign w_l0_57 = (w_sel_bits_0)? in127 : in127;
assign w_l0_58 = (w_sel_bits_0)? in127 : in127;
assign w_l0_59 = (w_sel_bits_0)? in127 : in127;
assign w_l0_60 = (w_sel_bits_0)? in127 : in127;
assign w_l0_61 = (w_sel_bits_0)? in127 : in127;
assign w_l0_62 = (w_sel_bits_0)? in127 : in127;
assign w_l0_63 = (w_sel_bits_0)? in127 : in127;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign w_l1_2 = (w_sel_bits_1)? w_l0_5 : w_l0_4;
assign w_l1_3 = (w_sel_bits_1)? w_l0_7 : w_l0_6;
assign w_l1_4 = (w_sel_bits_1)? w_l0_9 : w_l0_8;
assign w_l1_5 = (w_sel_bits_1)? w_l0_11 : w_l0_10;
assign w_l1_6 = (w_sel_bits_1)? w_l0_13 : w_l0_12;
assign w_l1_7 = (w_sel_bits_1)? w_l0_15 : w_l0_14;
assign w_l1_8 = (w_sel_bits_1)? w_l0_17 : w_l0_16;
assign w_l1_9 = (w_sel_bits_1)? w_l0_19 : w_l0_18;
assign w_l1_10 = (w_sel_bits_1)? w_l0_21 : w_l0_20;
assign w_l1_11 = (w_sel_bits_1)? w_l0_23 : w_l0_22;
assign w_l1_12 = (w_sel_bits_1)? w_l0_25 : w_l0_24;
assign w_l1_13 = (w_sel_bits_1)? w_l0_27 : w_l0_26;
assign w_l1_14 = (w_sel_bits_1)? w_l0_29 : w_l0_28;
assign w_l1_15 = (w_sel_bits_1)? w_l0_31 : w_l0_30;
assign w_l1_16 = (w_sel_bits_1)? w_l0_33 : w_l0_32;
assign w_l1_17 = (w_sel_bits_1)? w_l0_35 : w_l0_34;
assign w_l1_18 = (w_sel_bits_1)? w_l0_37 : w_l0_36;
assign w_l1_19 = (w_sel_bits_1)? w_l0_39 : w_l0_38;
assign w_l1_20 = (w_sel_bits_1)? w_l0_41 : w_l0_40;
assign w_l1_21 = (w_sel_bits_1)? w_l0_43 : w_l0_42;
assign w_l1_22 = (w_sel_bits_1)? w_l0_45 : w_l0_44;
assign w_l1_23 = (w_sel_bits_1)? w_l0_47 : w_l0_46;
assign w_l1_24 = (w_sel_bits_1)? w_l0_49 : w_l0_48;
assign w_l1_25 = (w_sel_bits_1)? w_l0_51 : w_l0_50;
assign w_l1_26 = (w_sel_bits_1)? w_l0_53 : w_l0_52;
assign w_l1_27 = (w_sel_bits_1)? w_l0_55 : w_l0_54;
assign w_l1_28 = (w_sel_bits_1)? w_l0_57 : w_l0_56;
assign w_l1_29 = (w_sel_bits_1)? w_l0_59 : w_l0_58;
assign w_l1_30 = (w_sel_bits_1)? w_l0_61 : w_l0_60;
assign w_l1_31 = (w_sel_bits_1)? w_l0_63 : w_l0_62;
assign w_l2_0 = (w_sel_bits_2)? w_l1_1 : w_l1_0;
assign w_l2_1 = (w_sel_bits_2)? w_l1_3 : w_l1_2;
assign w_l2_2 = (w_sel_bits_2)? w_l1_5 : w_l1_4;
assign w_l2_3 = (w_sel_bits_2)? w_l1_7 : w_l1_6;
assign w_l2_4 = (w_sel_bits_2)? w_l1_9 : w_l1_8;
assign w_l2_5 = (w_sel_bits_2)? w_l1_11 : w_l1_10;
assign w_l2_6 = (w_sel_bits_2)? w_l1_13 : w_l1_12;
assign w_l2_7 = (w_sel_bits_2)? w_l1_15 : w_l1_14;
assign w_l2_8 = (w_sel_bits_2)? w_l1_17 : w_l1_16;
assign w_l2_9 = (w_sel_bits_2)? w_l1_19 : w_l1_18;
assign w_l2_10 = (w_sel_bits_2)? w_l1_21 : w_l1_20;
assign w_l2_11 = (w_sel_bits_2)? w_l1_23 : w_l1_22;
assign w_l2_12 = (w_sel_bits_2)? w_l1_25 : w_l1_24;
assign w_l2_13 = (w_sel_bits_2)? w_l1_27 : w_l1_26;
assign w_l2_14 = (w_sel_bits_2)? w_l1_29 : w_l1_28;
assign w_l2_15 = (w_sel_bits_2)? w_l1_31 : w_l1_30;
assign w_l3_0 = (w_sel_bits_3)? w_l2_1 : w_l2_0;
assign w_l3_1 = (w_sel_bits_3)? w_l2_3 : w_l2_2;
assign w_l3_2 = (w_sel_bits_3)? w_l2_5 : w_l2_4;
assign w_l3_3 = (w_sel_bits_3)? w_l2_7 : w_l2_6;
assign w_l3_4 = (w_sel_bits_3)? w_l2_9 : w_l2_8;
assign w_l3_5 = (w_sel_bits_3)? w_l2_11 : w_l2_10;
assign w_l3_6 = (w_sel_bits_3)? w_l2_13 : w_l2_12;
assign w_l3_7 = (w_sel_bits_3)? w_l2_15 : w_l2_14;
assign w_l4_0 = (w_sel_bits_4)? w_l3_1 : w_l3_0;
assign w_l4_1 = (w_sel_bits_4)? w_l3_3 : w_l3_2;
assign w_l4_2 = (w_sel_bits_4)? w_l3_5 : w_l3_4;
assign w_l4_3 = (w_sel_bits_4)? w_l3_7 : w_l3_6;
assign w_l5_0 = (w_sel_bits_5)? w_l4_1 : w_l4_0;
assign w_l5_1 = (w_sel_bits_5)? w_l4_3 : w_l4_2;
assign r = (w_sel_bits_6)? w_l5_1 : w_l5_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module BranchUnit_STRUC_7f9e35cb7590 (
	input [7:0] SREG,
	input [7:0] RegisterToTest,
	input [7:0] RegisterB,
	input [7:0] IORegisterToTest,
	input [2:0] Bit,
	input [2:0] Operation,
	output  Skip,
	output  Branch);
wire w_w_io_bit_1;
wire w_w_not_sreg_bit;
wire w_w_not_reg_bit;
wire w_w_reg_bit_1;
wire w_w_io_bit_0;
wire w_w_not_io_bit;
wire w_w_io_bit_3;
wire w_w_io_bit_2;
wire w_w_io_bit_4;
wire w_w_io_bit_5;
wire w_w_io_bit_6;
wire w_w_io_bit_7;
wire w_w_cpse_skip;
wire w_w_reg_bit_0;
wire w_w_reg_bit_3;
wire w_w_reg_bit_2;
wire w_w_zero1;
wire w_w_reg_bit_4;
wire w_w_io_bit;
wire w_w_reg_bit_5;
wire w_w_reg_bit_6;
wire w_w_reg_bit_7;
wire w_w_sreg_bit_0;
wire w_w_sreg_bit_1;
wire w_w_sreg_bit_2;
wire w_w_reg_bit;
wire w_w_sreg_bit_3;
wire w_w_sreg_bit_4;
wire w_w_sreg_bit_5;
wire w_w_sreg_bit_6;
wire w_w_sreg_bit_7;
wire w_w_sreg_bit;

assign w_w_zero1 = 0;
assign w_w_sreg_bit_0 = SREG[0];
assign w_w_sreg_bit_1 = SREG[1];
assign w_w_sreg_bit_2 = SREG[2];
assign w_w_sreg_bit_3 = SREG[3];
assign w_w_sreg_bit_4 = SREG[4];
assign w_w_sreg_bit_5 = SREG[5];
assign w_w_sreg_bit_6 = SREG[6];
assign w_w_sreg_bit_7 = SREG[7];
Mux_7f9e35b1cbc0 i_Mux_SREG_Bit(.sel(Bit),.in0(w_w_sreg_bit_0),.in1(w_w_sreg_bit_1),.in2(w_w_sreg_bit_2),.in3(w_w_sreg_bit_3),.in4(w_w_sreg_bit_4),.in5(w_w_sreg_bit_5),.in6(w_w_sreg_bit_6),.in7(w_w_sreg_bit_7),.r(w_w_sreg_bit));
assign w_w_reg_bit_0 = RegisterToTest[0];
assign w_w_reg_bit_1 = RegisterToTest[1];
assign w_w_reg_bit_2 = RegisterToTest[2];
assign w_w_reg_bit_3 = RegisterToTest[3];
assign w_w_reg_bit_4 = RegisterToTest[4];
assign w_w_reg_bit_5 = RegisterToTest[5];
assign w_w_reg_bit_6 = RegisterToTest[6];
assign w_w_reg_bit_7 = RegisterToTest[7];
Mux_7f9e35b1ea20 i_Mux_Reg_Bit(.sel(Bit),.in0(w_w_reg_bit_0),.in1(w_w_reg_bit_1),.in2(w_w_reg_bit_2),.in3(w_w_reg_bit_3),.in4(w_w_reg_bit_4),.in5(w_w_reg_bit_5),.in6(w_w_reg_bit_6),.in7(w_w_reg_bit_7),.r(w_w_reg_bit));
assign w_w_io_bit_0 = IORegisterToTest[0];
assign w_w_io_bit_1 = IORegisterToTest[1];
assign w_w_io_bit_2 = IORegisterToTest[2];
assign w_w_io_bit_3 = IORegisterToTest[3];
assign w_w_io_bit_4 = IORegisterToTest[4];
assign w_w_io_bit_5 = IORegisterToTest[5];
assign w_w_io_bit_6 = IORegisterToTest[6];
assign w_w_io_bit_7 = IORegisterToTest[7];
Mux_7f9e35b248c0 i_Mux_IO_Bit(.sel(Bit),.in0(w_w_io_bit_0),.in1(w_w_io_bit_1),.in2(w_w_io_bit_2),.in3(w_w_io_bit_3),.in4(w_w_io_bit_4),.in5(w_w_io_bit_5),.in6(w_w_io_bit_6),.in7(w_w_io_bit_7),.r(w_w_io_bit));
assign w_w_not_sreg_bit = ~w_w_sreg_bit;
assign w_w_not_reg_bit = ~w_w_reg_bit;
assign w_w_not_io_bit = ~w_w_io_bit;
assign w_w_cpse_skip = (RegisterToTest == RegisterB)? 1:0;
Mux_7f9e35b263f0 i_Mux_Skip(.sel(Operation),.in0(w_w_zero1),.in1(w_w_zero1),.in2(w_w_zero1),.in3(w_w_not_reg_bit),.in4(w_w_reg_bit),.in5(w_w_not_io_bit),.in6(w_w_io_bit),.in7(w_w_cpse_skip),.r(Skip));
Mux_7f9e35b396a0 i_Mux_Branch(.sel(Operation),.in0(w_w_zero1),.in1(w_w_sreg_bit),.in2(w_w_not_sreg_bit),.in3(w_w_zero1),.in4(w_w_zero1),.in5(w_w_zero1),.in6(w_w_zero1),.in7(w_w_zero1),.r(Branch));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b1cbc0 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_l1_1;
wire w_l1_0;
wire w_l0_0;
wire w_sel_bits_0;
wire w_l0_1;
wire w_l0_2;
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in0;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in5 : in4;
assign w_l0_3 = (w_sel_bits_0)? in7 : in6;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b1ea20 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;
wire w_l1_0;
wire w_l1_1;
wire w_l0_0;
wire w_sel_bits_0;
wire w_l0_1;
wire w_l0_2;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in0;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in5 : in4;
assign w_l0_3 = (w_sel_bits_0)? in7 : in6;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b248c0 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_l0_1;
wire w_l0_2;
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;
wire w_l1_0;
wire w_l1_1;
wire w_l0_0;
wire w_sel_bits_0;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in0;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in5 : in4;
assign w_l0_3 = (w_sel_bits_0)? in7 : in6;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b263f0 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_l0_2;
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;
wire w_l1_0;
wire w_l1_1;
wire w_l0_0;
wire w_sel_bits_0;
wire w_l0_1;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in2 : in2;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in5 : in4;
assign w_l0_3 = (w_sel_bits_0)? in7 : in6;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b396a0 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;
wire w_l1_0;
wire w_l1_1;
wire w_l0_0;
wire w_sel_bits_0;
wire w_l0_1;
wire w_l0_2;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in7;
assign w_l0_1 = (w_sel_bits_0)? in7 : in2;
assign w_l0_2 = (w_sel_bits_0)? in7 : in7;
assign w_l0_3 = (w_sel_bits_0)? in7 : in7;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleC_STRUC_7f9e35b39f40 (
	input [15:0] Rr,
	input [15:0] Rd,
	input [15:0] Res,
	input [3:0] Mode,
	input  MulCarry,
	output  Cout);
wire w_w_zero1;
wire w_w_one1;
wire [7:0] w_w_zero8;
wire w_w_c_neg;
wire w_w_sub_or_temp;
wire w_w_c_add;
wire w_w_add_or_temp;
wire w_w_not_r7;
wire w_w_not_rd7;
wire w_w_rd7;
wire w_w_not_r15;
wire w_w_rr7;
wire w_w_not_rd15;
wire w_w_c_sub;
wire w_w_r7;
wire w_w_rd15;
wire w_w_r15;
wire [7:0] w_w_res_l;
wire w_w_c_adiw;
wire w_w_rd0;
wire w_w_sub_t1;
wire w_w_c_sbiw;
wire w_w_sub_t2;
wire w_w_sub_t3;
wire w_w_add_t1;
wire w_w_add_t2;
wire w_w_add_t3;
wire w_w_res_is_zero;

assign w_w_zero1 = 0;
assign w_w_one1 = 1;
assign w_w_zero8[7:0] = 0;
assign w_w_rd7 = Rd[7:7];
assign w_w_rr7 = Rr[7:7];
assign w_w_r7 = Res[7:7];
assign w_w_rd0 = Rd[0:0];
assign w_w_rd15 = Rd[15:15];
assign w_w_r15 = Res[15:15];
assign w_w_res_l = Res[7:0];
assign w_w_not_r7 = ~w_w_r7;
assign w_w_not_rd7 = ~w_w_rd7;
assign w_w_not_r15 = ~w_w_r15;
assign w_w_not_rd15 = ~w_w_rd15;
assign w_w_add_t1 = w_w_rd7 & w_w_rr7;
assign w_w_add_t2 = w_w_rr7 & w_w_not_r7;
assign w_w_add_t3 = w_w_not_r7 & w_w_rd7;
assign w_w_add_or_temp = w_w_add_t1 | w_w_add_t2;
assign w_w_c_add = w_w_add_or_temp | w_w_add_t3;
assign w_w_sub_t1 = w_w_not_rd7 & w_w_rr7;
assign w_w_sub_t2 = w_w_rr7 & w_w_r7;
assign w_w_sub_t3 = w_w_r7 & w_w_not_rd7;
assign w_w_sub_or_temp = w_w_sub_t1 | w_w_sub_t2;
assign w_w_c_sub = w_w_sub_or_temp | w_w_sub_t3;
assign w_w_c_adiw = w_w_not_r15 & w_w_rd15;
assign w_w_c_sbiw = w_w_r15 & w_w_not_rd15;
assign w_w_res_is_zero = (w_w_res_l == w_w_zero8)? 1:0;
assign w_w_c_neg = ~w_w_res_is_zero;
Mux_7f9e35b59cd0 i_Mux_Cout(.sel(Mode),.in0(w_w_zero1),.in1(w_w_one1),.in2(w_w_c_add),.in3(w_w_c_sub),.in4(w_w_c_adiw),.in5(w_w_c_sbiw),.in6(w_w_one1),.in7(w_w_c_neg),.in8(MulCarry),.in9(w_w_rd0),.in10(w_w_rd7),.in11(w_w_zero1),.in12(w_w_zero1),.in13(w_w_zero1),.in14(w_w_zero1),.in15(w_w_zero1),.r(Cout));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b59cd0 (
	input [3:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	input  in8,
	input  in9,
	input  in10,
	input  in11,
	input  in12,
	input  in13,
	input  in14,
	input  in15,
	output  r);
wire w_l1_2;
wire w_l0_3;
wire w_l1_3;
wire w_l2_0;
wire w_l0_4;
wire w_l2_1;
wire w_l0_5;
wire w_l0_0;
wire w_l1_0;
wire w_sel_bits_1;
wire w_l0_6;
wire w_l0_1;
wire w_sel_bits_2;
wire w_l1_1;
wire w_sel_bits_3;
wire w_l0_2;
wire w_l0_7;
wire w_sel_bits_0;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_sel_bits_3 = sel[3];
assign w_l0_0 = (w_sel_bits_0)? in6 : in15;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in5 : in4;
assign w_l0_3 = (w_sel_bits_0)? in7 : in6;
assign w_l0_4 = (w_sel_bits_0)? in9 : in8;
assign w_l0_5 = (w_sel_bits_0)? in15 : in10;
assign w_l0_6 = (w_sel_bits_0)? in15 : in15;
assign w_l0_7 = (w_sel_bits_0)? in15 : in15;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign w_l1_2 = (w_sel_bits_1)? w_l0_5 : w_l0_4;
assign w_l1_3 = (w_sel_bits_1)? w_l0_7 : w_l0_6;
assign w_l2_0 = (w_sel_bits_2)? w_l1_1 : w_l1_0;
assign w_l2_1 = (w_sel_bits_2)? w_l1_3 : w_l1_2;
assign r = (w_sel_bits_3)? w_l2_1 : w_l2_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleZ_STRUC_7f9e35b59d00 (
	input [15:0] Res,
	input [2:0] Mode,
	input  Zprev,
	output  Zout);
wire [7:0] w_w_zero8;
wire w_w_z_16;
wire [15:0] w_w_zero16;
wire [7:0] w_w_res_l;
wire w_w_z_chained;
wire w_w_zero1;
wire w_w_z_8;
wire w_w_one1;

assign w_w_zero1 = 0;
assign w_w_one1 = 1;
assign w_w_zero8[7:0] = 0;
assign w_w_zero16[15:0] = 0;
assign w_w_res_l = Res[7:0];
assign w_w_z_8 = (w_w_res_l == w_w_zero8)? 1:0;
assign w_w_z_16 = (Res == w_w_zero16)? 1:0;
assign w_w_z_chained = Zprev & w_w_z_8;
Mux_7f9e35b71820 i_Mux_Zout(.sel(Mode),.in0(w_w_zero1),.in1(w_w_one1),.in2(w_w_z_8),.in3(w_w_z_16),.in4(w_w_z_chained),.in5(w_w_z_chained),.in6(w_w_zero1),.in7(w_w_zero1),.r(Zout));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b71820 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_l0_0;
wire w_sel_bits_0;
wire w_l1_0;
wire w_l0_1;
wire w_l0_2;
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;
wire w_l1_1;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in7;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in5 : in5;
assign w_l0_3 = (w_sel_bits_0)? in7 : in7;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleN_STRUC_7f9e35b71970 (
	input [15:0] Res,
	input [2:0] Mode,
	output  Nout);
wire w_w_n8;
wire w_w_one1;
wire w_w_n16;
wire w_w_zero1;

assign w_w_zero1 = 0;
assign w_w_one1 = 1;
assign w_w_n8 = Res[7:7];
assign w_w_n16 = Res[15:15];
Mux_7f9e35b73620 i_Mux_Nout(.sel(Mode),.in0(w_w_zero1),.in1(w_w_one1),.in2(w_w_n8),.in3(w_w_n16),.in4(w_w_zero1),.in5(w_w_zero1),.in6(w_w_zero1),.in7(w_w_zero1),.r(Nout));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b73620 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_sel_bits_1;
wire w_sel_bits_2;
wire w_l0_3;
wire w_l1_0;
wire w_l1_1;
wire w_l0_0;
wire w_sel_bits_0;
wire w_l0_1;
wire w_l0_2;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in7;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in7 : in7;
assign w_l0_3 = (w_sel_bits_0)? in7 : in7;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleV_STRUC_7f9e35b72210 (
	input [15:0] Rr,
	input [15:0] Rd,
	input [15:0] Res,
	input  N,
	input  C,
	input [3:0] Mode,
	output  Vout);
wire w_w_m2_t1_temp;
wire w_w_m2_t1;
wire w_w_zero1;
wire w_w_one1;
wire w_w_mode6;
wire [7:0] w_w_0x80;
wire [7:0] w_w_0x7F;
wire w_w_m3_t2_temp;
wire w_w_m2_t2_temp;
wire w_w_not_rd7;
wire w_w_mode7;
wire w_w_not_rr7;
wire w_w_m3_t2;
wire w_w_not_r7;
wire w_w_not_rd15;
wire w_w_not_r15;
wire w_w_m2_t2;
wire w_w_rd7;
wire w_w_rr7;
wire w_w_r7;
wire w_w_rd15;
wire w_w_r15;
wire w_w_mode3;
wire [7:0] w_w_res_l;
wire w_w_mode2;
wire w_w_mode9;
wire w_w_mode4;
wire w_w_m3_t1_temp;
wire w_w_mode5;
wire w_w_m3_t1;

assign w_w_zero1 = 0;
assign w_w_one1 = 1;
assign w_w_0x80[7:0] = 128;
assign w_w_0x7F[7:0] = 127;
assign w_w_rd7 = Rd[7:7];
assign w_w_rr7 = Rr[7:7];
assign w_w_r7 = Res[7:7];
assign w_w_rd15 = Rd[15:15];
assign w_w_r15 = Res[15:15];
assign w_w_res_l = Res[7:0];
assign w_w_not_rd7 = ~w_w_rd7;
assign w_w_not_rr7 = ~w_w_rr7;
assign w_w_not_r7 = ~w_w_r7;
assign w_w_not_rd15 = ~w_w_rd15;
assign w_w_not_r15 = ~w_w_r15;
assign w_w_m2_t1_temp = w_w_rd7 & w_w_rr7;
assign w_w_m2_t1 = w_w_m2_t1_temp & w_w_not_r7;
assign w_w_m2_t2_temp = w_w_not_rd7 & w_w_not_rr7;
assign w_w_m2_t2 = w_w_m2_t2_temp & w_w_r7;
assign w_w_mode2 = w_w_m2_t1 | w_w_m2_t2;
assign w_w_m3_t1_temp = w_w_rd7 & w_w_not_rr7;
assign w_w_m3_t1 = w_w_m3_t1_temp & w_w_not_r7;
assign w_w_m3_t2_temp = w_w_not_rd7 & w_w_rr7;
assign w_w_m3_t2 = w_w_m3_t2_temp & w_w_r7;
assign w_w_mode3 = w_w_m3_t1 | w_w_m3_t2;
assign w_w_mode4 = w_w_not_rd15 & w_w_r15;
assign w_w_mode5 = w_w_rd15 & w_w_not_r15;
assign w_w_mode6 = (w_w_res_l == w_w_0x80)? 1:0;
assign w_w_mode7 = (w_w_res_l == w_w_0x7F)? 1:0;
assign w_w_mode9 = N ^ C;
Mux_7f9e35b9d8e0 i_Mux_Vout(.sel(Mode),.in0(w_w_zero1),.in1(w_w_one1),.in2(w_w_mode2),.in3(w_w_mode3),.in4(w_w_mode4),.in5(w_w_mode5),.in6(w_w_mode6),.in7(w_w_mode7),.in8(w_w_zero1),.in9(w_w_mode9),.in10(w_w_zero1),.in11(w_w_zero1),.in12(w_w_zero1),.in13(w_w_zero1),.in14(w_w_zero1),.in15(w_w_zero1),.r(Vout));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35b9d8e0 (
	input [3:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	input  in8,
	input  in9,
	input  in10,
	input  in11,
	input  in12,
	input  in13,
	input  in14,
	input  in15,
	output  r);
wire w_sel_bits_1;
wire w_l0_6;
wire w_l0_1;
wire w_sel_bits_2;
wire w_l1_0;
wire w_sel_bits_3;
wire w_l0_7;
wire w_l0_2;
wire w_l1_1;
wire w_sel_bits_0;
wire w_l0_3;
wire w_l1_2;
wire w_l2_0;
wire w_l0_4;
wire w_l1_3;
wire w_l2_1;
wire w_l0_5;
wire w_l0_0;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_sel_bits_3 = sel[3];
assign w_l0_0 = (w_sel_bits_0)? in1 : in15;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in5 : in4;
assign w_l0_3 = (w_sel_bits_0)? in7 : in6;
assign w_l0_4 = (w_sel_bits_0)? in9 : in15;
assign w_l0_5 = (w_sel_bits_0)? in15 : in15;
assign w_l0_6 = (w_sel_bits_0)? in15 : in15;
assign w_l0_7 = (w_sel_bits_0)? in15 : in15;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign w_l1_2 = (w_sel_bits_1)? w_l0_5 : w_l0_4;
assign w_l1_3 = (w_sel_bits_1)? w_l0_7 : w_l0_6;
assign w_l2_0 = (w_sel_bits_2)? w_l1_1 : w_l1_0;
assign w_l2_1 = (w_sel_bits_2)? w_l1_3 : w_l1_2;
assign r = (w_sel_bits_3)? w_l2_1 : w_l2_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleH_STRUC_7f9e35b9e630 (
	input [15:0] Rr,
	input [15:0] Rd,
	input [15:0] Res,
	input [2:0] Mode,
	output  Hout);
wire w_w_add_t2;
wire w_w_h_sub;
wire w_w_rd3;
wire w_w_add_t3;
wire w_w_sub_t1;
wire w_w_rr3;
wire w_w_h_neg;
wire w_w_h_add;
wire w_w_r3;
wire w_w_zero1;
wire w_w_sub_or_temp;
wire w_w_one1;
wire w_w_add_or_temp;
wire w_w_sub_t2;
wire w_w_not_rd3;
wire w_w_sub_t3;
wire w_w_not_r3;
wire w_w_add_t1;

assign w_w_zero1 = 0;
assign w_w_one1 = 1;
assign w_w_rd3 = Rd[3:3];
assign w_w_rr3 = Rr[3:3];
assign w_w_r3 = Res[3:3];
assign w_w_not_rd3 = ~w_w_rd3;
assign w_w_not_r3 = ~w_w_r3;
assign w_w_add_t1 = w_w_rd3 & w_w_rr3;
assign w_w_add_t2 = w_w_rr3 & w_w_not_r3;
assign w_w_add_t3 = w_w_not_r3 & w_w_rd3;
assign w_w_add_or_temp = w_w_add_t1 | w_w_add_t2;
assign w_w_h_add = w_w_add_or_temp | w_w_add_t3;
assign w_w_sub_t1 = w_w_not_rd3 & w_w_rr3;
assign w_w_sub_t2 = w_w_rr3 & w_w_r3;
assign w_w_sub_t3 = w_w_r3 & w_w_not_rd3;
assign w_w_sub_or_temp = w_w_sub_t1 | w_w_sub_t2;
assign w_w_h_sub = w_w_sub_or_temp | w_w_sub_t3;
assign w_w_h_neg = w_w_r3 | w_w_rd3;
Mux_7f9e35ba7140 i_Mux_Hout(.sel(Mode),.in0(w_w_zero1),.in1(w_w_one1),.in2(w_w_h_add),.in3(w_w_h_sub),.in4(w_w_h_neg),.in5(w_w_zero1),.in6(w_w_zero1),.in7(w_w_zero1),.r(Hout));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35ba7140 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_l0_2;
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;
wire w_l1_0;
wire w_l1_1;
wire w_l0_0;
wire w_sel_bits_0;
wire w_l0_1;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in7;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in7 : in4;
assign w_l0_3 = (w_sel_bits_0)? in7 : in7;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleT_STRUC_7f9e35ba7290 (
	input [7:0] Rr,
	input [2:0] BitPos,
	input [1:0] Mode,
	output  Tout);
wire w_w_rr_bit_2;
wire w_w_one1;
wire w_w_rr_bit_3;
wire w_w_rr_bit_4;
wire w_w_rr_bit_5;
wire w_w_rr_bit_6;
wire w_w_rr_bit_7;
wire w_w_rr_bit_0;
wire w_w_bst;
wire w_w_rr_bit_1;
wire w_w_zero1;

assign w_w_zero1 = 0;
assign w_w_one1 = 1;
assign w_w_rr_bit_0 = Rr[0];
assign w_w_rr_bit_1 = Rr[1];
assign w_w_rr_bit_2 = Rr[2];
assign w_w_rr_bit_3 = Rr[3];
assign w_w_rr_bit_4 = Rr[4];
assign w_w_rr_bit_5 = Rr[5];
assign w_w_rr_bit_6 = Rr[6];
assign w_w_rr_bit_7 = Rr[7];
Mux_7f9e35bb1430 i_Mux_BST_BitSelect(.sel(BitPos),.in0(w_w_rr_bit_0),.in1(w_w_rr_bit_1),.in2(w_w_rr_bit_2),.in3(w_w_rr_bit_3),.in4(w_w_rr_bit_4),.in5(w_w_rr_bit_5),.in6(w_w_rr_bit_6),.in7(w_w_rr_bit_7),.r(w_w_bst));
Mux_7f9e35bb1460 i_Mux_Tout(.sel(Mode),.in0(w_w_zero1),.in1(w_w_one1),.in2(w_w_bst),.in3(w_w_zero1),.r(Tout));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35bb1430 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;
wire w_l1_0;
wire w_l1_1;
wire w_l0_0;
wire w_sel_bits_0;
wire w_l0_1;
wire w_l0_2;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in0;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign w_l0_2 = (w_sel_bits_0)? in5 : in4;
assign w_l0_3 = (w_sel_bits_0)? in7 : in6;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35bb1460 (
	input [1:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	output  r);
wire w_sel_bits_1;
wire w_l0_1;
wire w_l0_0;
wire w_sel_bits_0;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_l0_0 = (w_sel_bits_0)? in1 : in3;
assign w_l0_1 = (w_sel_bits_0)? in3 : in2;
assign r = (w_sel_bits_1)? w_l0_1 : w_l0_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleI_STRUC_7f9e35bb1d00 (
	input  Mode,
	output  Iout);
wire w_w_one1;
wire w_w_zero1;

assign w_w_zero1 = 0;
assign w_w_one1 = 1;
Mux_7f9e35bb39e0 i_Mux_Iout(.sel(Mode),.in0(w_w_zero1),.in1(w_w_one1),.r(Iout));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35bb39e0 (
	input  sel,
	input  in0,
	input  in1,
	output  r);

assign r = (sel)? in1 : in0;
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleS_STRUC_7f9e35bb3a10 (
	input  N,
	input  V,
	input [2:0] Mode,
	output  Sout);
wire w_zero;
wire w_one;
wire w_sign;

assign w_one = 1;
assign w_zero = 0;
assign w_sign = N ^ V;
Mux_7f9e35bb8170 i_mux(.sel(Mode),.in0(w_zero),.in1(w_one),.in2(w_sign),.in3(w_sign),.in4(w_sign),.in5(w_sign),.in6(w_sign),.in7(w_sign),.r(Sout));
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35bb8170 (
	input [2:0] sel,
	input  in0,
	input  in1,
	input  in2,
	input  in3,
	input  in4,
	input  in5,
	input  in6,
	input  in7,
	output  r);
wire w_sel_bits_1;
wire w_l0_3;
wire w_sel_bits_2;
wire w_l1_0;
wire w_l1_1;
wire w_l0_0;
wire w_sel_bits_0;
wire w_l0_1;
wire w_l0_2;

assign w_sel_bits_0 = sel[0];
assign w_sel_bits_1 = sel[1];
assign w_sel_bits_2 = sel[2];
assign w_l0_0 = (w_sel_bits_0)? in1 : in0;
assign w_l0_1 = (w_sel_bits_0)? in7 : in7;
assign w_l0_2 = (w_sel_bits_0)? in7 : in7;
assign w_l0_3 = (w_sel_bits_0)? in7 : in7;
assign w_l1_0 = (w_sel_bits_1)? w_l0_1 : w_l0_0;
assign w_l1_1 = (w_sel_bits_1)? w_l0_3 : w_l0_2;
assign r = (w_sel_bits_2)? w_l1_1 : w_l1_0;
endmodule

// This file was automatically created by py4hw Verilog generator
module ALU_MergerAndLogic_7f9e35bb8ec0 (
	input  w_cout,
	input  w_zout,
	input  w_nout,
	input  w_vout,
	input  w_sout,
	input  w_hout,
	input  w_tout,
	input  w_iout,
	output  reg [7:0] sreg_val);
// Code generated from propagate method
// wire/variable declaration
integer new_sreg;
// initial
initial
begin
end
// process
always @(*)
begin
    new_sreg=((((((((w_iout&1)<<7)|((w_tout&1)<<6))|((w_hout&1)<<5))|((w_sout&1)<<4))|((w_vout&1)<<3))|((w_nout&1)<<2))|((w_zout&1)<<1))|(w_cout&1);
    sreg_val<=new_sreg;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module MemoryInterfaceHandler_7f9e35bbad50 (
	input clk,
	input [7:0] memory_readdata,
	input  memory_resp,
	input  reset,
	input [5:0] WE,
	input [2:0] LoadSelectMux,
	input [4:0] LoadingMux,
	input [2:0] IncDec,
	input [1:0] ReadWrite,
	input [4:0] InputSelectMemory,
	input [4:0] Mem_instruction,
	input [15:0] RomAddress,
	input [15:0] RomAddressValue,
	input [7:0] PCL_VAL_IN,
	input [7:0] PCH_VAL_IN,
	input  PC_Offset,
	input [7:0] ResL,
	input [7:0] ResH,
	input [7:0] K_val_Input,
	input [5:0] Q,
	input [4:0] Rd,
	input [4:0] Rr,
	input [4:0] A_5bit,
	input [5:0] A_6bit,
	input [7:0] WbAddr,
	input [7:0] ROM_VAL,
	input [7:0] SREG_IN,
	input [7:0] eSREG,
	input  ALU_Commit,
	input [7:0] SREG_ReadValue,
	output  reg  memory_read,
	output  reg  memory_write,
	output  reg [15:0] memory_address,
	output  reg [7:0] memory_writedata,
	output  reg  memory_instype,
	output  reg [7:0] RegisterOut,
	output  reg  Resp,
	output  reg [7:0] address_ZL,
	output  reg [7:0] address_ZH,
	output  reg [7:0] MIH_PCL_LOAD_VAL,
	output  reg [7:0] MIH_PCH_LOAD_VAL,
	output  reg [7:0] R0_BUFFER_out,
	output  reg [7:0] R1_BUFFER_out,
	output  reg [7:0] SREG_WriteValue,
	output  reg [7:0] SREG_WriteMask,
	output  reg [15:0] MAR_ValueOut);
// Code generated from clock method
// wire/variable declaration
integer MEM_X;
integer MEM_X_PLUS;
integer MEM_Y;
integer MEM_Y_PLUS;
integer MEM_Z;
integer MEM_Z_PLUS;
integer MEM_SP;
integer MEM_SP_PLUS;
integer MEM_RAM_ADDR_REG;
integer MEM_Y_Q;
integer MEM_Z_Q;
integer MEM_RD;
integer MEM_RR;
integer MEM_WB_ADDR;
integer MEM_RD_1;
integer MEM_RR_1;
integer MEM_A_5bit;
integer MEM_A_6bit;
integer MEM_INT_VECTOR_L;
integer MEM_INT_VECTOR_H;
integer INPUT_DATABUS;
integer INPUT_RESL;
integer INPUT_RESH;
integer INPUT_GENERAL;
integer INPUT_ROM_VALUE;
integer INPUT_XL;
integer INPUT_XH;
integer INPUT_YL;
integer INPUT_YH;
integer INPUT_ZL;
integer INPUT_ZH;
integer INPUT_SPL;
integer INPUT_SPH;
integer INPUT_PCL;
integer INPUT_PCH;
integer INPUT_RD_BUFFER;
integer INPUT_ROM_2;
integer LOAD_BUS_DATA;
integer LOAD_XL_MINUS;
integer LOAD_XH_MINUS;
integer LOAD_XL_PLUS;
integer LOAD_XH_PLUS;
integer LOAD_YL_MINUS;
integer LOAD_YH_MINUS;
integer LOAD_YL_PLUS;
integer LOAD_YH_PLUS;
integer LOAD_ZL_MINUS;
integer LOAD_ZH_MINUS;
integer LOAD_ZL_PLUS;
integer LOAD_ZH_PLUS;
integer LOAD_XL;
integer LOAD_XH;
integer LOAD_YL;
integer LOAD_YH;
integer LOAD_ZL;
integer LOAD_ZH;
integer LOAD_SPL;
integer LOAD_SPH;
integer LOAD_RD_BUFFER;
integer LOAD_R0_BUFFER;
integer LOAD_R1_BUFFER;
integer INC_NONE;
integer INC_POST_INC;
integer INC_PRE_DEC;
integer INC_POST_DEC;
integer INC_PRE_INC;
integer I_FLAG_BIT;
integer _io_20;
integer _io_21;
integer _io_22;
integer _io_23;
integer _io_24;
integer _io_25;
integer _io_26;
integer _io_27;
integer _io_28;
integer _io_29;
integer _io_2a;
integer _io_2b;
integer _io_2c;
integer _io_2d;
integer _io_2e;
integer _io_2f;
integer _io_30;
integer _io_31;
integer _io_32;
integer _io_33;
integer _io_34;
integer _io_35;
integer _io_36;
integer _io_37;
integer _io_38;
integer _io_39;
integer _io_3a;
integer _io_3b;
integer _io_3c;
integer _io_3d;
integer _io_3e;
integer _io_3f;
integer _io_40;
integer _io_41;
integer _io_42;
integer _io_43;
integer _io_44;
integer _io_45;
integer _io_46;
integer _io_47;
integer _io_48;
integer _io_49;
integer _io_4a;
integer _io_4b;
integer _io_4c;
integer _io_4d;
integer _io_4e;
integer _io_4f;
integer _io_50;
integer _io_51;
integer _io_52;
integer _io_53;
integer _io_54;
integer _io_55;
integer _io_56;
integer _io_57;
integer _io_58;
integer _io_59;
integer _io_5a;
integer _io_5b;
integer _io_5c;
integer _io_5d;
integer _io_5e;
integer _io_5f;
integer _io_60;
integer _io_61;
integer _io_62;
integer _io_63;
integer _io_64;
integer _io_65;
integer _io_66;
integer _io_67;
integer _io_68;
integer _io_69;
integer _io_6a;
integer _io_6b;
integer _io_6c;
integer _io_6d;
integer _io_6e;
integer _io_6f;
integer _io_70;
integer _io_71;
integer _io_72;
integer _io_73;
integer _io_74;
integer _io_75;
integer _io_76;
integer _io_77;
integer _io_78;
integer _io_79;
integer _io_7a;
integer _io_7b;
integer _io_7c;
integer _io_7d;
integer _io_7e;
integer _io_7f;
integer _io_80;
integer _io_81;
integer _io_82;
integer _io_83;
integer _io_84;
integer _io_85;
integer _io_86;
integer _io_87;
integer _io_88;
integer _io_89;
integer _io_8a;
integer _io_8b;
integer _io_8c;
integer _io_8d;
integer _io_8e;
integer _io_8f;
integer _io_90;
integer _io_91;
integer _io_92;
integer _io_93;
integer _io_94;
integer _io_95;
integer _io_96;
integer _io_97;
integer _io_98;
integer _io_99;
integer _io_9a;
integer _io_9b;
integer _io_9c;
integer _io_9d;
integer _io_9e;
integer _io_9f;
integer _io_a0;
integer _io_a1;
integer _io_a2;
integer _io_a3;
integer _io_a4;
integer _io_a5;
integer _io_a6;
integer _io_a7;
integer _io_a8;
integer _io_a9;
integer _io_aa;
integer _io_ab;
integer _io_ac;
integer _io_ad;
integer _io_ae;
integer _io_af;
integer _io_b0;
integer _io_b1;
integer _io_b2;
integer _io_b3;
integer _io_b4;
integer _io_b5;
integer _io_b6;
integer _io_b7;
integer _io_b8;
integer _io_b9;
integer _io_ba;
integer _io_bb;
integer _io_bc;
integer _io_bd;
integer _io_be;
integer _io_bf;
integer _io_c0;
integer _io_c1;
integer _io_c2;
integer _io_c3;
integer _io_c4;
integer _io_c5;
integer _io_c6;
integer _io_c7;
integer _io_c8;
integer _io_c9;
integer _io_ca;
integer _io_cb;
integer _io_cc;
integer _io_cd;
integer _io_ce;
integer _io_cf;
integer _io_d0;
integer _io_d1;
integer _io_d2;
integer _io_d3;
integer _io_d4;
integer _io_d5;
integer _io_d6;
integer _io_d7;
integer _io_d8;
integer _io_d9;
integer _io_da;
integer _io_db;
integer _io_dc;
integer _io_dd;
integer _io_de;
integer _io_df;
integer _io_e0;
integer _io_e1;
integer _io_e2;
integer _io_e3;
integer _io_e4;
integer _io_e5;
integer _io_e6;
integer _io_e7;
integer _io_e8;
integer _io_e9;
integer _io_ea;
integer _io_eb;
integer _io_ec;
integer _io_ed;
integer _io_ee;
integer _io_ef;
integer _io_f0;
integer _io_f1;
integer _io_f2;
integer _io_f3;
integer _io_f4;
integer _io_f5;
integer _io_f6;
integer _io_f7;
integer _io_f8;
integer _io_f9;
integer _io_fa;
integer _io_fb;
integer _io_fc;
integer _io_fd;
integer _io_fe;
integer _io_ff;
integer XregL;
integer XregH;
integer YregL;
integer YregH;
integer ZregL;
integer ZregH;
integer SPL;
integer SPH;
integer RdBuffer;
integer SPMCR;
integer R0Buffer;
integer R1Buffer;
integer BusData;
integer Databuffer;
integer debug;
integer mem_instr;
integer address;
integer pointer_name;
integer q_val;
integer incdec_mode;
integer rw;
integer SP_L_ADDR;
integer SP_H_ADDR;
integer SREG_ADDR;
integer SPMCR_ADDR;
integer is_passthrough;
integer resp_val;
integer sreg_bus_write_pending;
integer sreg_bus_write_value;
integer sel;
integer write_data;
integer pc_full;
integer load_sel;
integer data;
integer ptr_offset;
integer x_new;
integer y_new;
integer z_new;
integer sp_new;
integer alu_commit;
integer eSREG_mask;
integer sreg_mask_from_bus;
integer write_mask;
integer write_value;
// initial
initial
begin
    MEM_X=1;
    MEM_X_PLUS=2;
    MEM_Y=3;
    MEM_Y_PLUS=4;
    MEM_Z=5;
    MEM_Z_PLUS=6;
    MEM_SP=7;
    MEM_SP_PLUS=8;
    MEM_RAM_ADDR_REG=9;
    MEM_Y_Q=10;
    MEM_Z_Q=11;
    MEM_RD=12;
    MEM_RR=13;
    MEM_WB_ADDR=14;
    MEM_RD_1=15;
    MEM_RR_1=16;
    MEM_A_5bit=17;
    MEM_A_6bit=18;
    MEM_INT_VECTOR_L=19;
    MEM_INT_VECTOR_H=20;
    INPUT_DATABUS=1;
    INPUT_RESL=2;
    INPUT_RESH=3;
    INPUT_GENERAL=4;
    INPUT_ROM_VALUE=5;
    INPUT_XL=6;
    INPUT_XH=7;
    INPUT_YL=8;
    INPUT_YH=9;
    INPUT_ZL=10;
    INPUT_ZH=11;
    INPUT_SPL=12;
    INPUT_SPH=13;
    INPUT_PCL=14;
    INPUT_PCH=15;
    INPUT_RD_BUFFER=16;
    INPUT_ROM_2=17;
    LOAD_BUS_DATA=1;
    LOAD_XL_MINUS=2;
    LOAD_XH_MINUS=3;
    LOAD_XL_PLUS=4;
    LOAD_XH_PLUS=5;
    LOAD_YL_MINUS=6;
    LOAD_YH_MINUS=7;
    LOAD_YL_PLUS=8;
    LOAD_YH_PLUS=9;
    LOAD_ZL_MINUS=10;
    LOAD_ZH_MINUS=11;
    LOAD_ZL_PLUS=12;
    LOAD_ZH_PLUS=13;
    LOAD_XL=1;
    LOAD_XH=2;
    LOAD_YL=3;
    LOAD_YH=4;
    LOAD_ZL=5;
    LOAD_ZH=6;
    LOAD_SPL=7;
    LOAD_SPH=8;
    LOAD_RD_BUFFER=14;
    LOAD_R0_BUFFER=15;
    LOAD_R1_BUFFER=16;
    INC_NONE=0;
    INC_POST_INC=1;
    INC_PRE_DEC=2;
    INC_POST_DEC=3;
    INC_PRE_INC=4;
    I_FLAG_BIT=7;
    _io_20=0;
    _io_21=0;
    _io_22=0;
    _io_23=0;
    _io_24=0;
    _io_25=0;
    _io_26=0;
    _io_27=0;
    _io_28=0;
    _io_29=0;
    _io_2a=0;
    _io_2b=0;
    _io_2c=0;
    _io_2d=0;
    _io_2e=0;
    _io_2f=0;
    _io_30=0;
    _io_31=0;
    _io_32=0;
    _io_33=0;
    _io_34=0;
    _io_35=0;
    _io_36=0;
    _io_37=0;
    _io_38=0;
    _io_39=0;
    _io_3a=0;
    _io_3b=0;
    _io_3c=0;
    _io_3d=0;
    _io_3e=0;
    _io_3f=0;
    _io_40=0;
    _io_41=0;
    _io_42=0;
    _io_43=0;
    _io_44=0;
    _io_45=0;
    _io_46=0;
    _io_47=0;
    _io_48=0;
    _io_49=0;
    _io_4a=0;
    _io_4b=0;
    _io_4c=0;
    _io_4d=0;
    _io_4e=0;
    _io_4f=0;
    _io_50=0;
    _io_51=0;
    _io_52=0;
    _io_53=0;
    _io_54=0;
    _io_55=0;
    _io_56=0;
    _io_57=0;
    _io_58=0;
    _io_59=0;
    _io_5a=0;
    _io_5b=0;
    _io_5c=0;
    _io_5d=0;
    _io_5e=0;
    _io_5f=0;
    _io_60=0;
    _io_61=0;
    _io_62=0;
    _io_63=0;
    _io_64=0;
    _io_65=0;
    _io_66=0;
    _io_67=0;
    _io_68=0;
    _io_69=0;
    _io_6a=0;
    _io_6b=0;
    _io_6c=0;
    _io_6d=0;
    _io_6e=0;
    _io_6f=0;
    _io_70=0;
    _io_71=0;
    _io_72=0;
    _io_73=0;
    _io_74=0;
    _io_75=0;
    _io_76=0;
    _io_77=0;
    _io_78=0;
    _io_79=0;
    _io_7a=0;
    _io_7b=0;
    _io_7c=0;
    _io_7d=0;
    _io_7e=0;
    _io_7f=0;
    _io_80=0;
    _io_81=0;
    _io_82=0;
    _io_83=0;
    _io_84=0;
    _io_85=0;
    _io_86=0;
    _io_87=0;
    _io_88=0;
    _io_89=0;
    _io_8a=0;
    _io_8b=0;
    _io_8c=0;
    _io_8d=0;
    _io_8e=0;
    _io_8f=0;
    _io_90=0;
    _io_91=0;
    _io_92=0;
    _io_93=0;
    _io_94=0;
    _io_95=0;
    _io_96=0;
    _io_97=0;
    _io_98=0;
    _io_99=0;
    _io_9a=0;
    _io_9b=0;
    _io_9c=0;
    _io_9d=0;
    _io_9e=0;
    _io_9f=0;
    _io_a0=0;
    _io_a1=0;
    _io_a2=0;
    _io_a3=0;
    _io_a4=0;
    _io_a5=0;
    _io_a6=0;
    _io_a7=0;
    _io_a8=0;
    _io_a9=0;
    _io_aa=0;
    _io_ab=0;
    _io_ac=0;
    _io_ad=0;
    _io_ae=0;
    _io_af=0;
    _io_b0=0;
    _io_b1=0;
    _io_b2=0;
    _io_b3=0;
    _io_b4=0;
    _io_b5=0;
    _io_b6=0;
    _io_b7=0;
    _io_b8=0;
    _io_b9=0;
    _io_ba=0;
    _io_bb=0;
    _io_bc=0;
    _io_bd=0;
    _io_be=0;
    _io_bf=0;
    _io_c0=0;
    _io_c1=0;
    _io_c2=0;
    _io_c3=0;
    _io_c4=0;
    _io_c5=0;
    _io_c6=0;
    _io_c7=0;
    _io_c8=0;
    _io_c9=0;
    _io_ca=0;
    _io_cb=0;
    _io_cc=0;
    _io_cd=0;
    _io_ce=0;
    _io_cf=0;
    _io_d0=0;
    _io_d1=0;
    _io_d2=0;
    _io_d3=0;
    _io_d4=0;
    _io_d5=0;
    _io_d6=0;
    _io_d7=0;
    _io_d8=0;
    _io_d9=0;
    _io_da=0;
    _io_db=0;
    _io_dc=0;
    _io_dd=0;
    _io_de=0;
    _io_df=0;
    _io_e0=0;
    _io_e1=0;
    _io_e2=0;
    _io_e3=0;
    _io_e4=0;
    _io_e5=0;
    _io_e6=0;
    _io_e7=0;
    _io_e8=0;
    _io_e9=0;
    _io_ea=0;
    _io_eb=0;
    _io_ec=0;
    _io_ed=0;
    _io_ee=0;
    _io_ef=0;
    _io_f0=0;
    _io_f1=0;
    _io_f2=0;
    _io_f3=0;
    _io_f4=0;
    _io_f5=0;
    _io_f6=0;
    _io_f7=0;
    _io_f8=0;
    _io_f9=0;
    _io_fa=0;
    _io_fb=0;
    _io_fc=0;
    _io_fd=0;
    _io_fe=0;
    _io_ff=0;
    XregL=0;
    XregH=0;
    YregL=0;
    YregH=0;
    ZregL=0;
    ZregH=0;
    SPL=0;
    SPH=0;
    RdBuffer=0;
    SPMCR=0;
    R0Buffer=0;
    R1Buffer=0;
    BusData=0;
    Databuffer=0;
    debug=1;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        XregL=0;
        XregH=0;
        YregL=0;
        YregH=0;
        ZregL=0;
        ZregH=0;
        SPL=0;
        SPH=0;
        SPMCR=0;
        BusData=0;
        RegisterOut<=0;
        address_ZL<=0;
        address_ZH<=0;
        memory_address<=0;
        memory_writedata<=0;
        memory_instype<=1;
    end
    else
    begin
        mem_instr=Mem_instruction;
        address=0;
        pointer_name=0;
        if ((mem_instr==MEM_X)||(mem_instr==MEM_X_PLUS))
        begin
            address=(XregH<<8)|XregL;
            pointer_name=1;
        end
        else
        begin
            if ((mem_instr==MEM_Y)||(mem_instr==MEM_Y_PLUS))
            begin
                address=(YregH<<8)|YregL;
                pointer_name=2;
            end
            else
            begin
                if ((mem_instr==MEM_Z)||(mem_instr==MEM_Z_PLUS))
                begin
                    address=(ZregH<<8)|ZregL;
                    pointer_name=3;
                end
                else
                begin
                    if ((mem_instr==MEM_SP)||(mem_instr==MEM_SP_PLUS))
                    begin
                        address=(SPH<<8)|SPL;
                        pointer_name=4;
                    end
                    else
                    begin
                        case (mem_instr)
                        MEM_RAM_ADDR_REG: begin
                        address=RomAddressValue;
                        pointer_name=5;
                    end
                    MEM_RD: begin
                    address=Rd&31;
                    pointer_name=0;
                end
                MEM_RR: begin
                address=Rr&31;
                pointer_name=0;
            end
            MEM_WB_ADDR: begin
            address=WbAddr&31;
            pointer_name=0;
        end
        MEM_Y_Q: begin
        q_val=Q&63;
        address=((YregH<<8)|YregL)+q_val;
    end
    MEM_Z_Q: begin
    q_val=Q&63;
    address=((ZregH<<8)|ZregL)+q_val;
end
MEM_RD_1: begin
address=(Rd+1)&31;
pointer_name=0;
end
MEM_RR_1: begin
address=(Rr+1)&31;
pointer_name=0;
end
MEM_A_5bit: begin
address=A_5bit+32;
pointer_name=0;
end
MEM_A_6bit: begin
address=A_6bit+32;
pointer_name=0;
end
MEM_INT_VECTOR_L: begin
address=254;
pointer_name=0;
end
MEM_INT_VECTOR_H: begin
address=255;
pointer_name=0;
end
default:;
endcase
end
end
end
end
incdec_mode=IncDec;
if (((pointer_name==1)||(pointer_name==2))||((pointer_name==3)||(pointer_name==4)))
begin
case (incdec_mode)
INC_PRE_DEC: address=address-1;
INC_PRE_INC: address=address+1;
default:;
endcase
end
address=address&65535;
memory_address<=address;
MAR_ValueOut<=address;
memory_instype<=1;
rw=ReadWrite;
SP_L_ADDR=93;
SP_H_ADDR=94;
SREG_ADDR=95;
SPMCR_ADDR=87;
is_passthrough=(((((address>=32)&&(address<=54))||(address==55))||(((address>=56)&&(address<=63))||((address>=64)&&(address<=111))))||(((address==112)||((address>=120)&&(address<=126)))||(((address>=128)&&(address<=139))||((address>=176)&&(address<=180)))))||((((address>=184)&&(address<=188))||((address>=192)&&(address<=199)))||((address>=254)&&(address<=255)));
resp_val=0;
sreg_bus_write_pending=0;
sreg_bus_write_value=0;
case (rw)
1: begin
sel=InputSelectMemory;
write_data=0;
case (sel)
INPUT_DATABUS: write_data=memory_readdata;
INPUT_RESL: write_data=ResL;
INPUT_RESH: write_data=ResH;
INPUT_GENERAL: write_data=K_val_Input;
INPUT_ROM_VALUE: write_data=RomAddressValue;
INPUT_XL: write_data=XregL;
INPUT_XH: write_data=XregH;
INPUT_YL: write_data=YregL;
INPUT_YH: write_data=YregH;
INPUT_ZL: write_data=ZregL;
INPUT_ZH: write_data=ZregH;
INPUT_SPL: write_data=SPL;
INPUT_SPH: write_data=SPH;
INPUT_PCL: begin
pc_full=(((PCH_VAL_IN<<8)|PCL_VAL_IN)+PC_Offset)&65535;
write_data=pc_full&255;
end
INPUT_PCH: begin
pc_full=(((PCH_VAL_IN<<8)|PCL_VAL_IN)+PC_Offset)&65535;
write_data=(pc_full>>8)&255;
end
INPUT_RD_BUFFER: write_data=RdBuffer;
INPUT_ROM_2: write_data=ROM_VAL;
default:;
endcase
BusData=write_data;
if (address==SP_L_ADDR)
begin
SPL=BusData&255;
memory_write<=0;
resp_val=1;
end
else
begin
if (address==SP_H_ADDR)
begin
SPH=BusData&255;
memory_write<=0;
resp_val=1;
end
else
begin
if (address==SREG_ADDR)
begin
sreg_bus_write_pending=1;
sreg_bus_write_value=BusData&255;
memory_write<=0;
resp_val=1;
end
else
begin
if (address==SPMCR_ADDR)
begin
SPMCR=BusData&255;
memory_write<=0;
resp_val=1;
end
else
begin
if (((address>=32)&&(address<256))&&(!is_passthrough))
begin
case (address)
32: _io_20=BusData&255;
33: _io_21=BusData&255;
34: _io_22=BusData&255;
35: _io_23=BusData&255;
36: _io_24=BusData&255;
37: _io_25=BusData&255;
38: _io_26=BusData&255;
39: _io_27=BusData&255;
40: _io_28=BusData&255;
41: _io_29=BusData&255;
42: _io_2a=BusData&255;
43: _io_2b=BusData&255;
44: _io_2c=BusData&255;
45: _io_2d=BusData&255;
46: _io_2e=BusData&255;
47: _io_2f=BusData&255;
48: _io_30=BusData&255;
49: _io_31=BusData&255;
50: _io_32=BusData&255;
51: _io_33=BusData&255;
52: _io_34=BusData&255;
53: _io_35=BusData&255;
54: _io_36=BusData&255;
55: _io_37=BusData&255;
56: _io_38=BusData&255;
57: _io_39=BusData&255;
58: _io_3a=BusData&255;
59: _io_3b=BusData&255;
60: _io_3c=BusData&255;
61: _io_3d=BusData&255;
62: _io_3e=BusData&255;
63: _io_3f=BusData&255;
64: _io_40=BusData&255;
65: _io_41=BusData&255;
66: _io_42=BusData&255;
67: _io_43=BusData&255;
68: _io_44=BusData&255;
69: _io_45=BusData&255;
70: _io_46=BusData&255;
71: _io_47=BusData&255;
72: _io_48=BusData&255;
73: _io_49=BusData&255;
74: _io_4a=BusData&255;
75: _io_4b=BusData&255;
76: _io_4c=BusData&255;
77: _io_4d=BusData&255;
78: _io_4e=BusData&255;
79: _io_4f=BusData&255;
80: _io_50=BusData&255;
81: _io_51=BusData&255;
82: _io_52=BusData&255;
83: _io_53=BusData&255;
84: _io_54=BusData&255;
85: _io_55=BusData&255;
86: _io_56=BusData&255;
87: _io_57=BusData&255;
88: _io_58=BusData&255;
89: _io_59=BusData&255;
90: _io_5a=BusData&255;
91: _io_5b=BusData&255;
92: _io_5c=BusData&255;
93: _io_5d=BusData&255;
94: _io_5e=BusData&255;
95: _io_5f=BusData&255;
96: _io_60=BusData&255;
97: _io_61=BusData&255;
98: _io_62=BusData&255;
99: _io_63=BusData&255;
100: _io_64=BusData&255;
101: _io_65=BusData&255;
102: _io_66=BusData&255;
103: _io_67=BusData&255;
104: _io_68=BusData&255;
105: _io_69=BusData&255;
106: _io_6a=BusData&255;
107: _io_6b=BusData&255;
108: _io_6c=BusData&255;
109: _io_6d=BusData&255;
110: _io_6e=BusData&255;
111: _io_6f=BusData&255;
112: _io_70=BusData&255;
113: _io_71=BusData&255;
114: _io_72=BusData&255;
115: _io_73=BusData&255;
116: _io_74=BusData&255;
117: _io_75=BusData&255;
118: _io_76=BusData&255;
119: _io_77=BusData&255;
120: _io_78=BusData&255;
121: _io_79=BusData&255;
122: _io_7a=BusData&255;
123: _io_7b=BusData&255;
124: _io_7c=BusData&255;
125: _io_7d=BusData&255;
126: _io_7e=BusData&255;
127: _io_7f=BusData&255;
128: _io_80=BusData&255;
129: _io_81=BusData&255;
130: _io_82=BusData&255;
131: _io_83=BusData&255;
132: _io_84=BusData&255;
133: _io_85=BusData&255;
134: _io_86=BusData&255;
135: _io_87=BusData&255;
136: _io_88=BusData&255;
137: _io_89=BusData&255;
138: _io_8a=BusData&255;
139: _io_8b=BusData&255;
140: _io_8c=BusData&255;
141: _io_8d=BusData&255;
142: _io_8e=BusData&255;
143: _io_8f=BusData&255;
144: _io_90=BusData&255;
145: _io_91=BusData&255;
146: _io_92=BusData&255;
147: _io_93=BusData&255;
148: _io_94=BusData&255;
149: _io_95=BusData&255;
150: _io_96=BusData&255;
151: _io_97=BusData&255;
152: _io_98=BusData&255;
153: _io_99=BusData&255;
154: _io_9a=BusData&255;
155: _io_9b=BusData&255;
156: _io_9c=BusData&255;
157: _io_9d=BusData&255;
158: _io_9e=BusData&255;
159: _io_9f=BusData&255;
160: _io_a0=BusData&255;
161: _io_a1=BusData&255;
162: _io_a2=BusData&255;
163: _io_a3=BusData&255;
164: _io_a4=BusData&255;
165: _io_a5=BusData&255;
166: _io_a6=BusData&255;
167: _io_a7=BusData&255;
168: _io_a8=BusData&255;
169: _io_a9=BusData&255;
170: _io_aa=BusData&255;
171: _io_ab=BusData&255;
172: _io_ac=BusData&255;
173: _io_ad=BusData&255;
174: _io_ae=BusData&255;
175: _io_af=BusData&255;
176: _io_b0=BusData&255;
177: _io_b1=BusData&255;
178: _io_b2=BusData&255;
179: _io_b3=BusData&255;
180: _io_b4=BusData&255;
181: _io_b5=BusData&255;
182: _io_b6=BusData&255;
183: _io_b7=BusData&255;
184: _io_b8=BusData&255;
185: _io_b9=BusData&255;
186: _io_ba=BusData&255;
187: _io_bb=BusData&255;
188: _io_bc=BusData&255;
189: _io_bd=BusData&255;
190: _io_be=BusData&255;
191: _io_bf=BusData&255;
192: _io_c0=BusData&255;
193: _io_c1=BusData&255;
194: _io_c2=BusData&255;
195: _io_c3=BusData&255;
196: _io_c4=BusData&255;
197: _io_c5=BusData&255;
198: _io_c6=BusData&255;
199: _io_c7=BusData&255;
200: _io_c8=BusData&255;
201: _io_c9=BusData&255;
202: _io_ca=BusData&255;
203: _io_cb=BusData&255;
204: _io_cc=BusData&255;
205: _io_cd=BusData&255;
206: _io_ce=BusData&255;
207: _io_cf=BusData&255;
208: _io_d0=BusData&255;
209: _io_d1=BusData&255;
210: _io_d2=BusData&255;
211: _io_d3=BusData&255;
212: _io_d4=BusData&255;
213: _io_d5=BusData&255;
214: _io_d6=BusData&255;
215: _io_d7=BusData&255;
216: _io_d8=BusData&255;
217: _io_d9=BusData&255;
218: _io_da=BusData&255;
219: _io_db=BusData&255;
220: _io_dc=BusData&255;
221: _io_dd=BusData&255;
222: _io_de=BusData&255;
223: _io_df=BusData&255;
224: _io_e0=BusData&255;
225: _io_e1=BusData&255;
226: _io_e2=BusData&255;
227: _io_e3=BusData&255;
228: _io_e4=BusData&255;
229: _io_e5=BusData&255;
230: _io_e6=BusData&255;
231: _io_e7=BusData&255;
232: _io_e8=BusData&255;
233: _io_e9=BusData&255;
234: _io_ea=BusData&255;
235: _io_eb=BusData&255;
236: _io_ec=BusData&255;
237: _io_ed=BusData&255;
238: _io_ee=BusData&255;
239: _io_ef=BusData&255;
240: _io_f0=BusData&255;
241: _io_f1=BusData&255;
242: _io_f2=BusData&255;
243: _io_f3=BusData&255;
244: _io_f4=BusData&255;
245: _io_f5=BusData&255;
246: _io_f6=BusData&255;
247: _io_f7=BusData&255;
248: _io_f8=BusData&255;
249: _io_f9=BusData&255;
250: _io_fa=BusData&255;
251: _io_fb=BusData&255;
252: _io_fc=BusData&255;
253: _io_fd=BusData&255;
254: _io_fe=BusData&255;
255: _io_ff=BusData&255;
default:;
endcase
memory_write<=0;
resp_val=1;
end
else
begin
memory_writedata<=BusData;
memory_write<=1;
resp_val=memory_resp;
end
end
end
end
end
memory_read<=0;
end
2: begin
if (address==SP_L_ADDR)
begin
BusData=SPL;
memory_read<=0;
resp_val=1;
end
else
begin
if (address==SP_H_ADDR)
begin
BusData=SPH;
memory_read<=0;
resp_val=1;
end
else
begin
if (address==SREG_ADDR)
begin
BusData=SREG_ReadValue;
resp_val=1;
end
else
begin
if (address==SPMCR_ADDR)
begin
BusData=SPMCR;
memory_read<=0;
resp_val=1;
end
else
begin
if (((address>=32)&&(address<256))&&(!is_passthrough))
begin
case (address)
32: BusData=_io_20;
33: BusData=_io_21;
34: BusData=_io_22;
35: BusData=_io_23;
36: BusData=_io_24;
37: BusData=_io_25;
38: BusData=_io_26;
39: BusData=_io_27;
40: BusData=_io_28;
41: BusData=_io_29;
42: BusData=_io_2a;
43: BusData=_io_2b;
44: BusData=_io_2c;
45: BusData=_io_2d;
46: BusData=_io_2e;
47: BusData=_io_2f;
48: BusData=_io_30;
49: BusData=_io_31;
50: BusData=_io_32;
51: BusData=_io_33;
52: BusData=_io_34;
53: BusData=_io_35;
54: BusData=_io_36;
55: BusData=_io_37;
56: BusData=_io_38;
57: BusData=_io_39;
58: BusData=_io_3a;
59: BusData=_io_3b;
60: BusData=_io_3c;
61: BusData=_io_3d;
62: BusData=_io_3e;
63: BusData=_io_3f;
64: BusData=_io_40;
65: BusData=_io_41;
66: BusData=_io_42;
67: BusData=_io_43;
68: BusData=_io_44;
69: BusData=_io_45;
70: BusData=_io_46;
71: BusData=_io_47;
72: BusData=_io_48;
73: BusData=_io_49;
74: BusData=_io_4a;
75: BusData=_io_4b;
76: BusData=_io_4c;
77: BusData=_io_4d;
78: BusData=_io_4e;
79: BusData=_io_4f;
80: BusData=_io_50;
81: BusData=_io_51;
82: BusData=_io_52;
83: BusData=_io_53;
84: BusData=_io_54;
85: BusData=_io_55;
86: BusData=_io_56;
87: BusData=_io_57;
88: BusData=_io_58;
89: BusData=_io_59;
90: BusData=_io_5a;
91: BusData=_io_5b;
92: BusData=_io_5c;
93: BusData=_io_5d;
94: BusData=_io_5e;
95: BusData=_io_5f;
96: BusData=_io_60;
97: BusData=_io_61;
98: BusData=_io_62;
99: BusData=_io_63;
100: BusData=_io_64;
101: BusData=_io_65;
102: BusData=_io_66;
103: BusData=_io_67;
104: BusData=_io_68;
105: BusData=_io_69;
106: BusData=_io_6a;
107: BusData=_io_6b;
108: BusData=_io_6c;
109: BusData=_io_6d;
110: BusData=_io_6e;
111: BusData=_io_6f;
112: BusData=_io_70;
113: BusData=_io_71;
114: BusData=_io_72;
115: BusData=_io_73;
116: BusData=_io_74;
117: BusData=_io_75;
118: BusData=_io_76;
119: BusData=_io_77;
120: BusData=_io_78;
121: BusData=_io_79;
122: BusData=_io_7a;
123: BusData=_io_7b;
124: BusData=_io_7c;
125: BusData=_io_7d;
126: BusData=_io_7e;
127: BusData=_io_7f;
128: BusData=_io_80;
129: BusData=_io_81;
130: BusData=_io_82;
131: BusData=_io_83;
132: BusData=_io_84;
133: BusData=_io_85;
134: BusData=_io_86;
135: BusData=_io_87;
136: BusData=_io_88;
137: BusData=_io_89;
138: BusData=_io_8a;
139: BusData=_io_8b;
140: BusData=_io_8c;
141: BusData=_io_8d;
142: BusData=_io_8e;
143: BusData=_io_8f;
144: BusData=_io_90;
145: BusData=_io_91;
146: BusData=_io_92;
147: BusData=_io_93;
148: BusData=_io_94;
149: BusData=_io_95;
150: BusData=_io_96;
151: BusData=_io_97;
152: BusData=_io_98;
153: BusData=_io_99;
154: BusData=_io_9a;
155: BusData=_io_9b;
156: BusData=_io_9c;
157: BusData=_io_9d;
158: BusData=_io_9e;
159: BusData=_io_9f;
160: BusData=_io_a0;
161: BusData=_io_a1;
162: BusData=_io_a2;
163: BusData=_io_a3;
164: BusData=_io_a4;
165: BusData=_io_a5;
166: BusData=_io_a6;
167: BusData=_io_a7;
168: BusData=_io_a8;
169: BusData=_io_a9;
170: BusData=_io_aa;
171: BusData=_io_ab;
172: BusData=_io_ac;
173: BusData=_io_ad;
174: BusData=_io_ae;
175: BusData=_io_af;
176: BusData=_io_b0;
177: BusData=_io_b1;
178: BusData=_io_b2;
179: BusData=_io_b3;
180: BusData=_io_b4;
181: BusData=_io_b5;
182: BusData=_io_b6;
183: BusData=_io_b7;
184: BusData=_io_b8;
185: BusData=_io_b9;
186: BusData=_io_ba;
187: BusData=_io_bb;
188: BusData=_io_bc;
189: BusData=_io_bd;
190: BusData=_io_be;
191: BusData=_io_bf;
192: BusData=_io_c0;
193: BusData=_io_c1;
194: BusData=_io_c2;
195: BusData=_io_c3;
196: BusData=_io_c4;
197: BusData=_io_c5;
198: BusData=_io_c6;
199: BusData=_io_c7;
200: BusData=_io_c8;
201: BusData=_io_c9;
202: BusData=_io_ca;
203: BusData=_io_cb;
204: BusData=_io_cc;
205: BusData=_io_cd;
206: BusData=_io_ce;
207: BusData=_io_cf;
208: BusData=_io_d0;
209: BusData=_io_d1;
210: BusData=_io_d2;
211: BusData=_io_d3;
212: BusData=_io_d4;
213: BusData=_io_d5;
214: BusData=_io_d6;
215: BusData=_io_d7;
216: BusData=_io_d8;
217: BusData=_io_d9;
218: BusData=_io_da;
219: BusData=_io_db;
220: BusData=_io_dc;
221: BusData=_io_dd;
222: BusData=_io_de;
223: BusData=_io_df;
224: BusData=_io_e0;
225: BusData=_io_e1;
226: BusData=_io_e2;
227: BusData=_io_e3;
228: BusData=_io_e4;
229: BusData=_io_e5;
230: BusData=_io_e6;
231: BusData=_io_e7;
232: BusData=_io_e8;
233: BusData=_io_e9;
234: BusData=_io_ea;
235: BusData=_io_eb;
236: BusData=_io_ec;
237: BusData=_io_ed;
238: BusData=_io_ee;
239: BusData=_io_ef;
240: BusData=_io_f0;
241: BusData=_io_f1;
242: BusData=_io_f2;
243: BusData=_io_f3;
244: BusData=_io_f4;
245: BusData=_io_f5;
246: BusData=_io_f6;
247: BusData=_io_f7;
248: BusData=_io_f8;
249: BusData=_io_f9;
250: BusData=_io_fa;
251: BusData=_io_fb;
252: BusData=_io_fc;
253: BusData=_io_fd;
254: BusData=_io_fe;
255: BusData=_io_ff;
default:BusData=0;
endcase
memory_read<=0;
resp_val=1;
end
else
begin
BusData=memory_readdata;
memory_read<=1;
resp_val=memory_resp;
end
end
end
end
end
memory_write<=0;
end
default:begin
memory_read<=0;
memory_write<=0;
resp_val=memory_resp;
end
endcase
Resp<=resp_val;
RegisterOut<=BusData;
address_ZL<=ZregL;
address_ZH<=ZregH;
MIH_PCL_LOAD_VAL<=BusData;
MIH_PCH_LOAD_VAL<=BusData;
if (WE)
begin
load_sel=LoadingMux;
data=BusData&255;
case (load_sel)
LOAD_XL: XregL=data;
LOAD_XH: XregH=data;
LOAD_YL: YregL=data;
LOAD_YH: YregH=data;
LOAD_ZL: ZregL=data;
LOAD_ZH: ZregH=data;
LOAD_SPL: SPL=data;
LOAD_SPH: SPH=data;
LOAD_RD_BUFFER: RdBuffer=data;
LOAD_R0_BUFFER: R0Buffer=data;
LOAD_R1_BUFFER: R1Buffer=data;
default:;
endcase
end
if (((pointer_name==1)||(pointer_name==2))||((pointer_name==3)||(pointer_name==4)))
begin
if (incdec_mode!=INC_NONE)
begin
ptr_offset=0;
if ((incdec_mode==INC_PRE_DEC)||(incdec_mode==INC_POST_DEC))
begin
ptr_offset=-1;
end
else
begin
if ((incdec_mode==INC_PRE_INC)||(incdec_mode==INC_POST_INC))
begin
ptr_offset=1;
end
end
case (pointer_name)
1: begin
x_new=((XregH<<8)|XregL)+ptr_offset;
XregL=x_new&255;
XregH=(x_new>>8)&255;
end
2: begin
y_new=((YregH<<8)|YregL)+ptr_offset;
YregL=y_new&255;
YregH=(y_new>>8)&255;
end
3: begin
z_new=((ZregH<<8)|ZregL)+ptr_offset;
ZregL=z_new&255;
ZregH=(z_new>>8)&255;
end
4: begin
sp_new=((SPH<<8)|SPL)+ptr_offset;
SPL=sp_new&255;
SPH=(sp_new>>8)&255;
end
default:;
endcase
end
end
alu_commit=ALU_Commit;
if (alu_commit)
begin
eSREG_mask=eSREG;
end
else
begin
eSREG_mask=0;
end
if (sreg_bus_write_pending)
begin
sreg_mask_from_bus=255;
end
else
begin
sreg_mask_from_bus=0;
end
write_mask=eSREG_mask|sreg_mask_from_bus;
write_value=SREG_IN&eSREG_mask;
if (sreg_bus_write_pending)
begin
write_value=write_value|(sreg_bus_write_value&(~eSREG_mask));
end
SREG_WriteValue<=write_value&255;
SREG_WriteMask<=write_mask&255;
R0_BUFFER_out<=R0Buffer;
R1_BUFFER_out<=R1Buffer;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module Reg16RE (
	input clk,
	input [15:0] d,
	input  e,
	input  r,
	output [15:0] q);
reg [15:0] rq = 0;
always @(posedge clk)
if (r == 1)
begin
   rq <= 0;
end
else
begin
if (e == 1)
begin
   rq <= d;
end
end
assign q = rq;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35bd9670 (
	input  sel,
	input [7:0] in0,
	input [7:0] in1,
	output [7:0] r);

assign r = (sel)? in1 : in0;
endmodule

// This file was automatically created by py4hw Verilog generator
module Reg8RE (
	input clk,
	input [7:0] d,
	input  e,
	input  r,
	output [7:0] q);
reg [7:0] rq = 0;
always @(posedge clk)
if (r == 1)
begin
   rq <= 0;
end
else
begin
if (e == 1)
begin
   rq <= d;
end
end
assign q = rq;
endmodule

// This file was automatically created by py4hw Verilog generator
module Reg1RE (
	input clk,
	input  d,
	input  e,
	input  r,
	output  q);
reg  rq = 0;
always @(posedge clk)
if (r == 1)
begin
   rq <= 0;
end
else
begin
if (e == 1)
begin
   rq <= d;
end
end
assign q = rq;
endmodule

// This file was automatically created by py4hw Verilog generator
module Mux_7f9e35be6210 (
	input  sel,
	input  in0,
	input  in1,
	output  r);

assign r = (sel)? in1 : in0;
endmodule

// This file was automatically created by py4hw Verilog generator
module control_Box_7f9e35be6900 (
	input clk,
	input [15:0] CB_Instruction,
	input  CB_Resp,
	input  CB_Branch,
	input  CB_Skip,
	input  CB_Interrupt,
	input  CB_Instruction_fetched,
	input  CB_Instruction_decoded,
	input  CB_Executed_Jump,
	input  CB_Address_fetched,
	input  CB_SPM_Done,
	input  CB_Reset,
	output [2:0] CB_LoadSelectMux,
	output [4:0] CB_LoadingMux,
	output [4:0] CB_Input_Select,
	output [5:0] CB_WE_MEMORY,
	output [1:0] CB_Read_Write,
	output [4:0] CB_mem_instr,
	output [2:0] CB_IncDec,
	output  CB_InputSelect,
	output [3:0] CB_WE_Buffer,
	output  CB_Load_Z,
	output  CB_Load_K,
	output  CB_Load_Jump,
	output  CB_relative_Absolute,
	output  CB_Load_Byte,
	output  CB_Fetch_next_instruction,
	output  CB_Fetch_Address,
	output [7:0] CB_WB_Addr,
	output  CB_JumpWidth,
	output  CB_LOAD_PCL,
	output  CB_LOAD_PCH,
	output [1:0] CB_K_Select,
	output [1:0] CB_LPM_req,
	output [1:0] CB_SPM_req,
	output  CB_Interrupt_Entrance,
	output  CB_I_Force_WE,
	output  CB_I_Force_Value,
	output  CB_ALU_Commit);
wire w_w_irq_done;
wire [1:0] w_w_irq_read_write;
wire w_w_run;
wire [4:0] w_w_irq_mem_instr;
wire w_w_interrupt_done;
wire [4:0] w_w_irq_input_select_mem;
wire w_w_ib_done;
wire [2:0] w_w_irq_incdec;
wire [1:0] w_w_ib_read_write;
wire w_w_irq_load_pcl;
wire [4:0] w_w_ib_mem_instr;
wire w_w_irq_load_pch;
wire [4:0] w_w_ib_input_select_mem;
wire [2:0] w_w_ib_incdec;
wire w_w_ib_load_pcl;
wire w_w_ib_load_pch;

MainFSM_7f9e35be7f50 i_MainFSM(.clk(clk),.Skip(CB_Skip),.Interrupt(CB_Interrupt),.Instruction_fetched(CB_Instruction_fetched),.Instruction_decoded(CB_Instruction_decoded),.Instruction(CB_Instruction),.done(CB_ALU_Commit),.Interrupt_Done(w_w_interrupt_done),.reset(CB_Reset),.run(w_w_run),.Fetch_next_instruction(CB_Fetch_next_instruction),.JumpWidth(CB_JumpWidth),.Interrupt_Entrance(CB_Interrupt_Entrance));
INSTRUCTION_FSM_BOX_7f9e35bec3b0 i_INSTRUCTION_FSM_BOX(.clk(clk),.reset(CB_Reset),.run(w_w_run),.Instruction(CB_Instruction),.Resp(CB_Resp),.Branch(CB_Branch),.Executed_Jump(CB_Executed_Jump),.Address_fetched(CB_Address_fetched),.SPM_Done(CB_SPM_Done),.done(w_w_ib_done),.LoadSelectMux(CB_LoadSelectMux),.LoadingMux(CB_LoadingMux),.Input_Select(w_w_ib_input_select_mem),.WE(CB_WE_MEMORY),.Read_Write(w_w_ib_read_write),.Mem_Instruction(w_w_ib_mem_instr),.IncDec(w_w_ib_incdec),.InputSelect(CB_InputSelect),.WE_Buffer(CB_WE_Buffer),.Load_Z(CB_Load_Z),.Load_K(CB_Load_K),.Load_Jump(CB_Load_Jump),.relative_Absolute(CB_relative_Absolute),.Load_Byte(CB_Load_Byte),.Fetch_Address(CB_Fetch_Address),.WB_Addr(CB_WB_Addr),.LOAD_PCL(w_w_ib_load_pcl),.LOAD_PCH(w_w_ib_load_pch),.K_Select(CB_K_Select),.LPM_req(CB_LPM_req),.SPM_req(CB_SPM_req));
InterruptFSM_7f9e35bfdfd0 i_InterruptFSM(.clk(clk),.Run(w_w_run),.Instruction(CB_Instruction),.Entrance(CB_Interrupt_Entrance),.Resp(CB_Resp),.reset(CB_Reset),.Done(w_w_irq_done),.Read_Write(w_w_irq_read_write),.Mem_Instruction(w_w_irq_mem_instr),.InputSelectMemory(w_w_irq_input_select_mem),.IncDec(w_w_irq_incdec),.LOAD_PCL(w_w_irq_load_pcl),.LOAD_PCH(w_w_irq_load_pch),.Interrupt_Done(w_w_interrupt_done),.I_Force_WE(CB_I_Force_WE),.I_Force_Value(CB_I_Force_Value));
_InterruptBusMerge_7f9e35bfe570 i_InterruptBusMerge(.ib_done(w_w_ib_done),.ib_read_write(w_w_ib_read_write),.ib_mem_instr(w_w_ib_mem_instr),.ib_input_select_mem(w_w_ib_input_select_mem),.ib_incdec(w_w_ib_incdec),.ib_load_pcl(w_w_ib_load_pcl),.ib_load_pch(w_w_ib_load_pch),.irq_done(w_w_irq_done),.irq_read_write(w_w_irq_read_write),.irq_mem_instr(w_w_irq_mem_instr),.irq_input_select_mem(w_w_irq_input_select_mem),.irq_incdec(w_w_irq_incdec),.irq_load_pcl(w_w_irq_load_pcl),.irq_load_pch(w_w_irq_load_pch),.out_done(CB_ALU_Commit),.out_read_write(CB_Read_Write),.out_mem_instr(CB_mem_instr),.out_input_select_mem(CB_Input_Select),.out_incdec(CB_IncDec),.out_load_pcl(CB_LOAD_PCL),.out_load_pch(CB_LOAD_PCH));
endmodule

// This file was automatically created by py4hw Verilog generator
module MainFSM_7f9e35be7f50 (
	input clk,
	input  Skip,
	input  Interrupt,
	input  Instruction_fetched,
	input  Instruction_decoded,
	input [15:0] Instruction,
	input  done,
	input  Interrupt_Done,
	input  reset,
	output  reg  run,
	output  reg  Fetch_next_instruction,
	output  reg  JumpWidth,
	output  reg  Interrupt_Entrance);
// Code generated from clock method
// wire/variable declaration
integer current_state;
integer skip_flag;
integer _bypass_next_fetch;
integer _prev_instr_fetched;
integer _boundary_checked;
integer debug;
integer instret_count;
integer skip;
integer irq;
integer instr_fetched;
integer instr_decoded;
integer instruction;
integer done_active;
integer jump_width;
integer interrupt_done;
integer run_local;
integer Fetch_next_instruction_local;
integer Interrupt_Entrance_local;
integer state;
integer next_state;
// initial
initial
begin
    current_state=0;
    skip_flag=0;
    _bypass_next_fetch=0;
    _prev_instr_fetched=0;
    _boundary_checked=0;
    debug=1;
    instret_count=0;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        current_state=0;
        skip_flag=0;
        _bypass_next_fetch=0;
        _prev_instr_fetched=0;
        _boundary_checked=0;
        Fetch_next_instruction<=0;
        run<=0;
        JumpWidth<=0;
        Interrupt_Entrance<=0;
    end
    else
    begin
        skip=Skip;
        irq=Interrupt;
        instr_fetched=Instruction_fetched;
        instr_decoded=Instruction_decoded;
        instruction=Instruction;
        done_active=done;
        if ((((instruction==34)||(instruction==107))||((instruction==119)||(instruction==31)))&&(current_state!=1))
        begin
            jump_width=1;
        end
        else
        begin
            jump_width=0;
        end
        interrupt_done=Interrupt_Done;
        run_local=0;
        Fetch_next_instruction_local=0;
        Interrupt_Entrance_local=0;
        state=current_state;
        next_state=state;
        case (state)
        0: if ((!_boundary_checked)&&(irq==1))
        begin
            _boundary_checked=1;
            next_state=1;
        end
        else
        begin
            _boundary_checked=1;
            Fetch_next_instruction_local=1;
            if ((instr_fetched==1)&&(_prev_instr_fetched==0))
            begin
                _prev_instr_fetched=1;
                if (_bypass_next_fetch==1)
                begin
                    _bypass_next_fetch=0;
                    next_state=2;
                end
                else
                begin
                    next_state=3;
                end
            end
            else
            begin
                _prev_instr_fetched=0;
            end
        end
        1: begin
        Interrupt_Entrance_local=1;
        if (interrupt_done==1)
        begin
            next_state=0;
            _boundary_checked=0;
        end
    end
    2: begin
    Fetch_next_instruction_local=0;
    if (Instruction_fetched==0)
    begin
        next_state=0;
        _boundary_checked=0;
    end
end
3: if (instr_decoded==1)
begin
    next_state=4;
end
4: if (instruction==129)
begin
    instret_count=instret_count+1;
    next_state=5;
end
else
begin
    if ((instruction==128)||((instruction==130)||(instruction==131)))
    begin
        instret_count=instret_count+1;
        if (skip==1)
        begin
            skip_flag=1;
            _bypass_next_fetch=1;
        end
        next_state=0;
        _boundary_checked=0;
    end
    else
    begin
        run_local=1;
        next_state=6;
    end
end
5: if (irq==1)
begin
    next_state=1;
end
6: if (done_active==1)
begin
    instret_count=instret_count+1;
    if (skip==1)
    begin
        skip_flag=1;
        _bypass_next_fetch=1;
    end
    next_state=0;
    _boundary_checked=0;
end
default:;
endcase
if (debug==1)
begin
/* print removed */
end
current_state=next_state;
Fetch_next_instruction<=Fetch_next_instruction_local;
run<=run_local;
JumpWidth<=jump_width;
Interrupt_Entrance<=Interrupt_Entrance_local;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module INSTRUCTION_FSM_BOX_7f9e35bec3b0 (
	input clk,
	input  reset,
	input  run,
	input [15:0] Instruction,
	input  Resp,
	input  Branch,
	input  Executed_Jump,
	input  Address_fetched,
	input  SPM_Done,
	output  done,
	output [2:0] LoadSelectMux,
	output [4:0] LoadingMux,
	output [4:0] Input_Select,
	output [5:0] WE,
	output [1:0] Read_Write,
	output [4:0] Mem_Instruction,
	output [2:0] IncDec,
	output  InputSelect,
	output [3:0] WE_Buffer,
	output  Load_Z,
	output  Load_K,
	output  Load_Jump,
	output  relative_Absolute,
	output  Load_Byte,
	output  Fetch_Address,
	output [7:0] WB_Addr,
	output  LOAD_PCL,
	output  LOAD_PCH,
	output [1:0] K_Select,
	output [1:0] LPM_req,
	output [1:0] SPM_req);
wire w_w_ldst_LOAD_PCL;
wire w_w_ldst_LOAD_PCH;
wire w_w_callret_done;
wire w_w_callret_LoadSelectMux;
wire [4:0] w_w_callret_LoadingMux;
wire [4:0] w_w_callret_Input_Select;
wire w_w_callret_WE;
wire [1:0] w_w_callret_Read_Write;
wire [4:0] w_w_callret_Mem_Instruction;
wire [2:0] w_w_callret_IncDec;
wire [2:0] w_w_callret_write_Opperand_Buffer;
wire w_w_callret_InputSelect;
wire w_w_callret_Load_Z;
wire w_w_callret_Load_K;
wire w_w_callret_Load_Jump;
wire w_w_callret_relative_Absolute;
wire w_w_callret_Load_Byte;
wire w_w_callret_Fetch_Address;
wire [7:0] w_w_callret_WB_Addr;
wire w_w_callret_LOAD_PCL;
wire w_w_callret_LOAD_PCH;
wire [1:0] w_w_callret_K_Select;
wire w_w_lpm_done;
wire w_w_lpm_NotExecute;
wire w_w_lpm_LoadSelectMux;
wire [4:0] w_w_lpm_LoadingMux;
wire [4:0] w_w_lpm_Input_Select;
wire w_w_lpm_WE;
wire [1:0] w_w_lpm_Read_Write;
wire [4:0] w_w_lpm_Mem_Instruction;
wire [2:0] w_w_lpm_IncDec;
wire [2:0] w_w_lpm_write_Opperand_Buffer;
wire w_w_lpm_InputSelect;
wire w_w_lpm_Write_Enable;
wire w_w_lpm_Load_Z;
wire w_w_lpm_Load_K;
wire w_w_lpm_Load_Jump;
wire w_w_lpm_relative_Absolute;
wire w_w_lpm_Load_Byte;
wire w_w_lpm_Fetch_next_instruction;
wire w_w_lpm_Fetch_Address;
wire [7:0] w_w_lpm_WB_Addr;
wire w_w_lpm_LOAD_PCL;
wire w_w_lpm_LOAD_PCH;
wire w_w_lpm_LPM_req;
wire w_w_lpm_SPM_req;
wire w_w_RUN_OPPFSM;
wire w_w_RUN_MOVFSM;
wire w_w_RUN_POPPUSHFSM;
wire w_w_RUN_LDSTFSM;
wire w_w_RUN_CALLRETFSM;
wire w_w_RUN_LPMFSM;
wire w_w_opp_done;
wire w_w_opp_LoadSelectMux;
wire [4:0] w_w_opp_LoadingMux;
wire [4:0] w_w_opp_Input_Select;
wire w_w_opp_WE;
wire [1:0] w_w_opp_Read_Write;
wire [4:0] w_w_opp_Mem_Instruction;
wire [2:0] w_w_opp_IncDec;
wire [2:0] w_w_opp_write_Opperand_Buffer;
wire w_w_opp_InputSelect;
wire w_w_opp_Load_Z;
wire w_w_opp_Load_K;
wire w_w_opp_Load_Jump;
wire w_w_opp_relative_Absolute;
wire w_w_opp_Load_Byte;
wire w_w_opp_Fetch_next_instruction;
wire w_w_opp_Fetch_Address;
wire [7:0] w_w_opp_WB_Addr;
wire w_w_opp_LOAD_PCL;
wire w_w_opp_LOAD_PCH;
wire [1:0] w_w_opp_K_Select;
wire w_w_mov_done;
wire w_w_mov_LoadSelectMux;
wire [4:0] w_w_mov_LoadingMux;
wire [4:0] w_w_mov_Input_Select;
wire w_w_mov_WE;
wire [1:0] w_w_mov_Read_Write;
wire [4:0] w_w_mov_Mem_Instruction;
wire [2:0] w_w_mov_IncDec;
wire [2:0] w_w_mov_write_Opperand_Buffer;
wire w_w_mov_InputSelect;
wire w_w_mov_Load_Z;
wire w_w_mov_Load_K;
wire w_w_mov_Load_Jump;
wire w_w_mov_relative_Absolute;
wire w_w_mov_Load_Byte;
wire w_w_mov_Fetch_next_instruction;
wire w_w_mov_Fetch_Address;
wire [7:0] w_w_mov_WB_Addr;
wire w_w_mov_LOAD_PCL;
wire w_w_mov_LOAD_PCH;
wire w_w_poppush_done;
wire w_w_poppush_LoadSelectMux;
wire [4:0] w_w_poppush_LoadingMux;
wire [4:0] w_w_poppush_Input_Select;
wire w_w_poppush_WE;
wire [1:0] w_w_poppush_Read_Write;
wire [4:0] w_w_poppush_Mem_Instruction;
wire [2:0] w_w_poppush_IncDec;
wire [2:0] w_w_poppush_write_Opperand_Buffer;
wire w_w_poppush_InputSelect;
wire w_w_poppush_Load_Z;
wire w_w_poppush_Load_K;
wire w_w_poppush_Load_Jump;
wire w_w_poppush_relative_Absolute;
wire w_w_poppush_Load_Byte;
wire w_w_poppush_Fetch_next_instruction;
wire w_w_poppush_Fetch_Address;
wire [7:0] w_w_poppush_WB_Addr;
wire w_w_poppush_LOAD_PCL;
wire w_w_poppush_LOAD_PCH;
wire w_w_ldst_done;
wire w_w_ldst_LoadSelectMux;
wire [4:0] w_w_ldst_LoadingMux;
wire [4:0] w_w_ldst_Input_Select;
wire w_w_ldst_WE;
wire [1:0] w_w_ldst_Read_Write;
wire [4:0] w_w_ldst_Mem_Instruction;
wire [2:0] w_w_ldst_IncDec;
wire [2:0] w_w_ldst_write_Opperand_Buffer;
wire w_w_ldst_InputSelect;
wire w_w_ldst_Load_Z;
wire w_w_ldst_Load_K;
wire w_w_ldst_Load_Jump;
wire w_w_ldst_relative_Absolute;
wire w_w_ldst_Load_Byte;
wire w_w_ldst_Fetch_next_instruction;
wire w_w_ldst_Fetch_Address;
wire [7:0] w_w_ldst_WB_Addr;

FSM_SELECTOR_7f9e35bee900 i_FSM_SELECTOR(.run(run),.instruction(Instruction),.RUN_OPPFSM(w_w_RUN_OPPFSM),.RUN_MOVFSM(w_w_RUN_MOVFSM),.RUN_POPPUSHFSM(w_w_RUN_POPPUSHFSM),.RUN_LDSTFSM(w_w_RUN_LDSTFSM),.RUN_CALLRETFSM(w_w_RUN_CALLRETFSM),.RUN_LPMFSM(w_w_RUN_LPMFSM));
OPP_FSM_7f9e35beec00 i_OPP_FSM(.clk(clk),.reset(reset),.run(w_w_RUN_OPPFSM),.Instruction(Instruction),.Resp(Resp),.Branch(Branch),.Executed_Jump(Executed_Jump),.done(w_w_opp_done),.LoadSelectMux(w_w_opp_LoadSelectMux),.LoadingMux(w_w_opp_LoadingMux),.InputSelectMemory(w_w_opp_Input_Select),.WEMEMORY(w_w_opp_WE),.Read_Write(w_w_opp_Read_Write),.Mem_Instruction(w_w_opp_Mem_Instruction),.IncDec(w_w_opp_IncDec),.InputSelectBuffer(w_w_opp_InputSelect),.WEBUFFER(w_w_opp_write_Opperand_Buffer),.Load_Z(w_w_opp_Load_Z),.Load_K(w_w_opp_Load_K),.Load_Jump(w_w_opp_Load_Jump),.relative_Absolute(w_w_opp_relative_Absolute),.Load_Byte(w_w_opp_Load_Byte),.Fetch_next_instruction(w_w_opp_Fetch_next_instruction),.WB_Addr(w_w_opp_WB_Addr),.Fetch_Address(w_w_opp_Fetch_Address),.LOAD_PCL(w_w_opp_LOAD_PCL),.LOAD_PCH(w_w_opp_LOAD_PCH),.K_Select(w_w_opp_K_Select));
MOV_FSM_7f9e35bef650 i_MOV_FSM(.clk(clk),.reset(reset),.run(w_w_RUN_MOVFSM),.Instruction(Instruction),.Resp(Resp),.Branch(Branch),.Executed_Jump(Executed_Jump),.done(w_w_mov_done),.LoadSelectMux(w_w_mov_LoadSelectMux),.LoadingMux(w_w_mov_LoadingMux),.InputSelectMemory(w_w_mov_Input_Select),.WEMEMORY(w_w_mov_WE),.Read_Write(w_w_mov_Read_Write),.Mem_Instruction(w_w_mov_Mem_Instruction),.IncDec(w_w_mov_IncDec),.InputSelectBuffer(w_w_mov_InputSelect),.WEBUFFER(w_w_mov_write_Opperand_Buffer),.Load_Z(w_w_mov_Load_Z),.Load_K(w_w_mov_Load_K),.Load_Jump(w_w_mov_Load_Jump),.relative_Absolute(w_w_mov_relative_Absolute),.Load_Byte(w_w_mov_Load_Byte),.Fetch_next_instruction(w_w_mov_Fetch_next_instruction),.WB_Addr(w_w_mov_WB_Addr),.Fetch_Address(w_w_mov_Fetch_Address),.LOAD_PCL(w_w_mov_LOAD_PCL),.LOAD_PCH(w_w_mov_LOAD_PCH));
PopPush_FSM_7f9e35bf8080 i_PopPush_FSM(.clk(clk),.reset(reset),.run(w_w_RUN_POPPUSHFSM),.Instruction(Instruction),.Resp(Resp),.Branch(Branch),.Executed_Jump(Executed_Jump),.done(w_w_poppush_done),.LoadSelectMux(w_w_poppush_LoadSelectMux),.LoadingMux(w_w_poppush_LoadingMux),.InputSelectMemory(w_w_poppush_Input_Select),.WEMEMORY(w_w_poppush_WE),.Read_Write(w_w_poppush_Read_Write),.Mem_Instruction(w_w_poppush_Mem_Instruction),.IncDec(w_w_poppush_IncDec),.InputSelectBuffer(w_w_poppush_InputSelect),.WEBUFFER(w_w_poppush_write_Opperand_Buffer),.Load_Z(w_w_poppush_Load_Z),.Load_K(w_w_poppush_Load_K),.Load_Jump(w_w_poppush_Load_Jump),.relative_Absolute(w_w_poppush_relative_Absolute),.Load_Byte(w_w_poppush_Load_Byte),.Fetch_next_instruction(w_w_poppush_Fetch_next_instruction),.WB_Addr(w_w_poppush_WB_Addr),.Fetch_Address(w_w_poppush_Fetch_Address),.LOAD_PCL(w_w_poppush_LOAD_PCL),.LOAD_PCH(w_w_poppush_LOAD_PCH));
LDST_FSM_7f9e35bf8a70 i_LDST_FSM(.clk(clk),.reset(reset),.run(w_w_RUN_LDSTFSM),.Instruction(Instruction),.Resp(Resp),.Branch(Branch),.Executed_Jump(Executed_Jump),.Address_fetched(Address_fetched),.done(w_w_ldst_done),.LoadSelectMux(w_w_ldst_LoadSelectMux),.LoadingMux(w_w_ldst_LoadingMux),.InputSelectMemory(w_w_ldst_Input_Select),.WEMEMORY(w_w_ldst_WE),.Read_Write(w_w_ldst_Read_Write),.Mem_Instruction(w_w_ldst_Mem_Instruction),.IncDec(w_w_ldst_IncDec),.InputSelectBuffer(w_w_ldst_InputSelect),.WEBUFFER(w_w_ldst_write_Opperand_Buffer),.Load_Z(w_w_ldst_Load_Z),.Load_K(w_w_ldst_Load_K),.Load_Jump(w_w_ldst_Load_Jump),.relative_Absolute(w_w_ldst_relative_Absolute),.Load_Byte(w_w_ldst_Load_Byte),.Fetch_next_instruction(w_w_ldst_Fetch_next_instruction),.WB_Addr(w_w_ldst_WB_Addr),.Fetch_Address(w_w_ldst_Fetch_Address),.LOAD_PCL(w_w_ldst_LOAD_PCL),.LOAD_PCH(w_w_ldst_LOAD_PCH));
CallRet_FSM_7f9e35bf94c0 i_CALLRET_FSM(.clk(clk),.reset(reset),.run(w_w_RUN_CALLRETFSM),.Instruction(Instruction),.Resp(Resp),.Branch(Branch),.Executed_Jump(Executed_Jump),.Address_fetched(Address_fetched),.done(w_w_callret_done),.LoadSelectMux(w_w_callret_LoadSelectMux),.LoadingMux(w_w_callret_LoadingMux),.InputSelectMemory(w_w_callret_Input_Select),.WEMEMORY(w_w_callret_WE),.Read_Write(w_w_callret_Read_Write),.Mem_Instruction(w_w_callret_Mem_Instruction),.IncDec(w_w_callret_IncDec),.InputSelectBuffer(w_w_callret_InputSelect),.WEBUFFER(w_w_callret_write_Opperand_Buffer),.Load_Z(w_w_callret_Load_Z),.Load_K(w_w_callret_Load_K),.Load_Jump(w_w_callret_Load_Jump),.relative_Absolute(w_w_callret_relative_Absolute),.Load_Byte(w_w_callret_Load_Byte),.WB_Addr(w_w_callret_WB_Addr),.Fetch_Address(w_w_callret_Fetch_Address),.LOAD_PCL(w_w_callret_LOAD_PCL),.LOAD_PCH(w_w_callret_LOAD_PCH),.K_SELECT(w_w_callret_K_Select));
LPM_FSM_7f9e35bf9f10 i_LPM_FSM(.clk(clk),.reset(reset),.run(w_w_RUN_LPMFSM),.Instruction(Instruction),.Resp(Resp),.Branch(Branch),.Executed_Jump(Executed_Jump),.Address_fetched(Address_fetched),.SPM_Done(SPM_Done),.done(w_w_lpm_done),.NotExecute(w_w_lpm_NotExecute),.LoadSelectMux(w_w_lpm_LoadSelectMux),.LoadingMux(w_w_lpm_LoadingMux),.Input_Select(w_w_lpm_Input_Select),.WE(w_w_lpm_WE),.Read_Write(w_w_lpm_Read_Write),.Mem_Instruction(w_w_lpm_Mem_Instruction),.IncDec(w_w_lpm_IncDec),.write_Opperand_Buffer(w_w_lpm_write_Opperand_Buffer),.InputSelect(w_w_lpm_InputSelect),.Write_Enable(w_w_lpm_Write_Enable),.Load_Z(w_w_lpm_Load_Z),.Load_K(w_w_lpm_Load_K),.Load_Jump(w_w_lpm_Load_Jump),.relative_Absolute(w_w_lpm_relative_Absolute),.Load_Byte(w_w_lpm_Load_Byte),.Fetch_next_instruction(w_w_lpm_Fetch_next_instruction),.Fetch_Address(w_w_lpm_Fetch_Address),.LOAD_PCL(w_w_lpm_LOAD_PCL),.LOAD_PCH(w_w_lpm_LOAD_PCH),.WB_Addr(w_w_lpm_WB_Addr),.LPM_req(w_w_lpm_LPM_req),.SPM_req(w_w_lpm_SPM_req));
FSM_OutputMerger_7f9e35bfaae0 i_FSM_OutputMerger(.opp_done(w_w_opp_done),.opp_LoadSelectMux(w_w_opp_LoadSelectMux),.opp_LoadingMux(w_w_opp_LoadingMux),.opp_Input_Select(w_w_opp_Input_Select),.opp_WE(w_w_opp_WE),.opp_Read_Write(w_w_opp_Read_Write),.opp_Mem_Instruction(w_w_opp_Mem_Instruction),.opp_IncDec(w_w_opp_IncDec),.opp_write_Opperand_Buffer(w_w_opp_write_Opperand_Buffer),.opp_InputSelect(w_w_opp_InputSelect),.opp_Load_Z(w_w_opp_Load_Z),.opp_Load_K(w_w_opp_Load_K),.opp_Load_Jump(w_w_opp_Load_Jump),.opp_relative_Absolute(w_w_opp_relative_Absolute),.opp_Load_Byte(w_w_opp_Load_Byte),.opp_Fetch_Address(w_w_opp_Fetch_Address),.opp_WB_Addr(w_w_opp_WB_Addr),.opp_LOAD_PCL(w_w_opp_LOAD_PCL),.opp_LOAD_PCH(w_w_opp_LOAD_PCH),.opp_K_Select(w_w_opp_K_Select),.mov_done(w_w_mov_done),.mov_LoadSelectMux(w_w_mov_LoadSelectMux),.mov_LoadingMux(w_w_mov_LoadingMux),.mov_Input_Select(w_w_mov_Input_Select),.mov_WE(w_w_mov_WE),.mov_Read_Write(w_w_mov_Read_Write),.mov_Mem_Instruction(w_w_mov_Mem_Instruction),.mov_IncDec(w_w_mov_IncDec),.mov_write_Opperand_Buffer(w_w_mov_write_Opperand_Buffer),.mov_InputSelect(w_w_mov_InputSelect),.mov_Load_Z(w_w_mov_Load_Z),.mov_Load_K(w_w_mov_Load_K),.mov_Load_Jump(w_w_mov_Load_Jump),.mov_relative_Absolute(w_w_mov_relative_Absolute),.mov_Load_Byte(w_w_mov_Load_Byte),.mov_Fetch_Address(w_w_mov_Fetch_Address),.mov_WB_Addr(w_w_mov_WB_Addr),.mov_LOAD_PCL(w_w_mov_LOAD_PCL),.mov_LOAD_PCH(w_w_mov_LOAD_PCH),.poppush_done(w_w_poppush_done),.poppush_LoadSelectMux(w_w_poppush_LoadSelectMux),.poppush_LoadingMux(w_w_poppush_LoadingMux),.poppush_Input_Select(w_w_poppush_Input_Select),.poppush_WE(w_w_poppush_WE),.poppush_Read_Write(w_w_poppush_Read_Write),.poppush_Mem_Instruction(w_w_poppush_Mem_Instruction),.poppush_IncDec(w_w_poppush_IncDec),.poppush_write_Opperand_Buffer(w_w_poppush_write_Opperand_Buffer),.poppush_InputSelect(w_w_poppush_InputSelect),.poppush_Load_Z(w_w_poppush_Load_Z),.poppush_Load_K(w_w_poppush_Load_K),.poppush_Load_Jump(w_w_poppush_Load_Jump),.poppush_relative_Absolute(w_w_poppush_relative_Absolute),.poppush_Load_Byte(w_w_poppush_Load_Byte),.poppush_Fetch_Address(w_w_poppush_Fetch_Address),.poppush_WB_Addr(w_w_poppush_WB_Addr),.poppush_LOAD_PCL(w_w_poppush_LOAD_PCL),.poppush_LOAD_PCH(w_w_poppush_LOAD_PCH),.ldst_done(w_w_ldst_done),.ldst_LoadSelectMux(w_w_ldst_LoadSelectMux),.ldst_LoadingMux(w_w_ldst_LoadingMux),.ldst_Input_Select(w_w_ldst_Input_Select),.ldst_WE(w_w_ldst_WE),.ldst_Read_Write(w_w_ldst_Read_Write),.ldst_Mem_Instruction(w_w_ldst_Mem_Instruction),.ldst_IncDec(w_w_ldst_IncDec),.ldst_write_Opperand_Buffer(w_w_ldst_write_Opperand_Buffer),.ldst_InputSelect(w_w_ldst_InputSelect),.ldst_Load_Z(w_w_ldst_Load_Z),.ldst_Load_K(w_w_ldst_Load_K),.ldst_Load_Jump(w_w_ldst_Load_Jump),.ldst_relative_Absolute(w_w_ldst_relative_Absolute),.ldst_Load_Byte(w_w_ldst_Load_Byte),.ldst_Fetch_Address(w_w_ldst_Fetch_Address),.ldst_WB_Addr(w_w_ldst_WB_Addr),.ldst_LOAD_PCL(w_w_ldst_LOAD_PCL),.ldst_LOAD_PCH(w_w_ldst_LOAD_PCH),.callret_done(w_w_callret_done),.callret_LoadSelectMux(w_w_callret_LoadSelectMux),.callret_LoadingMux(w_w_callret_LoadingMux),.callret_Input_Select(w_w_callret_Input_Select),.callret_WE(w_w_callret_WE),.callret_Read_Write(w_w_callret_Read_Write),.callret_Mem_Instruction(w_w_callret_Mem_Instruction),.callret_IncDec(w_w_callret_IncDec),.callret_write_Opperand_Buffer(w_w_callret_write_Opperand_Buffer),.callret_InputSelect(w_w_callret_InputSelect),.callret_Load_Z(w_w_callret_Load_Z),.callret_Load_K(w_w_callret_Load_K),.callret_Load_Jump(w_w_callret_Load_Jump),.callret_relative_Absolute(w_w_callret_relative_Absolute),.callret_Load_Byte(w_w_callret_Load_Byte),.callret_Fetch_Address(w_w_callret_Fetch_Address),.callret_WB_Addr(w_w_callret_WB_Addr),.callret_LOAD_PCL(w_w_callret_LOAD_PCL),.callret_LOAD_PCH(w_w_callret_LOAD_PCH),.callret_K_Select(w_w_callret_K_Select),.lpm_done(w_w_lpm_done),.lpm_LoadSelectMux(w_w_lpm_LoadSelectMux),.lpm_LoadingMux(w_w_lpm_LoadingMux),.lpm_Input_Select(w_w_lpm_Input_Select),.lpm_WE(w_w_lpm_WE),.lpm_Read_Write(w_w_lpm_Read_Write),.lpm_Mem_Instruction(w_w_lpm_Mem_Instruction),.lpm_IncDec(w_w_lpm_IncDec),.lpm_write_Opperand_Buffer(w_w_lpm_write_Opperand_Buffer),.lpm_InputSelect(w_w_lpm_InputSelect),.lpm_Load_Z(w_w_lpm_Load_Z),.lpm_Load_K(w_w_lpm_Load_K),.lpm_Load_Jump(w_w_lpm_Load_Jump),.lpm_relative_Absolute(w_w_lpm_relative_Absolute),.lpm_Load_Byte(w_w_lpm_Load_Byte),.lpm_Fetch_Address(w_w_lpm_Fetch_Address),.lpm_WB_Addr(w_w_lpm_WB_Addr),.lpm_LOAD_PCL(w_w_lpm_LOAD_PCL),.lpm_LOAD_PCH(w_w_lpm_LOAD_PCH),.lpm_LPM_req(w_w_lpm_LPM_req),.lpm_SPM_req(w_w_lpm_SPM_req),.out_done(done),.out_LoadSelectMux(LoadSelectMux),.out_LoadingMux(LoadingMux),.out_Input_Select(Input_Select),.out_WE(WE),.out_Read_Write(Read_Write),.out_Mem_Instruction(Mem_Instruction),.out_IncDec(IncDec),.out_write_Opperand_Buffer(WE_Buffer),.out_InputSelect(InputSelect),.out_Load_Z(Load_Z),.out_Load_K(Load_K),.out_Load_Jump(Load_Jump),.out_relative_Absolute(relative_Absolute),.out_Load_Byte(Load_Byte),.out_Fetch_Address(Fetch_Address),.out_WB_Addr(WB_Addr),.out_LOAD_PCL(LOAD_PCL),.out_LOAD_PCH(LOAD_PCH),.out_K_Select(K_Select),.out_LPM_req(LPM_req),.out_SPM_req(SPM_req));
endmodule

// This file was automatically created by py4hw Verilog generator
module FSM_SELECTOR_7f9e35bee900 (
	input  run,
	input [15:0] instruction,
	output  reg  RUN_OPPFSM,
	output  reg  RUN_MOVFSM,
	output  reg  RUN_POPPUSHFSM,
	output  reg  RUN_LDSTFSM,
	output  reg  RUN_CALLRETFSM,
	output  reg  RUN_LPMFSM);
// Code generated from propagate method
// wire/variable declaration
integer debug;
integer _prev_run;
integer run_active;
integer ins;
integer rising;
integer OPPFSM;
integer MOVFSM;
integer POPPUSHFSM;
integer LDSTFSM;
integer CALLRETFSM;
integer LPMFSM;
// initial
initial
begin
end
// process
always @(*)
begin
    run_active=run;
    ins=instruction;
    rising=(run_active==1)&&(_prev_run==0);
    _prev_run=run_active;
    OPPFSM=0;
    MOVFSM=0;
    POPPUSHFSM=0;
    LDSTFSM=0;
    CALLRETFSM=0;
    LPMFSM=0;
    if (run_active)
    begin
        if ((ins==1)||((ins==2)||((ins==3)||((ins==4)||((ins==5)||((ins==6)||((ins==7)||((ins==8)||((ins==9)||((ins==10)||((ins==11)||((ins==12)||((ins==13)||((ins==14)||((ins==15)||((ins==16)||((ins==17)||((ins==18)||((ins==19)||((ins==20)||((ins==21)||((ins==22)||((ins==23)||((ins==24)||((ins==25)||((ins==26)||((ins==27)||((ins==28)||((ins==37)||((ins==38)||((ins==39)||((ins==40)||((ins==41)||((ins==42)||((ins==43)||((ins==44)||((ins==45)||((ins==46)||((ins==47)||((ins==48)||((ins==49)||((ins==50)||((ins==51)||((ins==52)||((ins==53)||((ins==54)||((ins==55)||((ins==56)||((ins==57)||((ins==58)||((ins==59)||((ins==60)||((ins==61)||((ins==62)||((ins==63)||((ins==64)||((ins==65)||((ins==66)||((ins==67)||((ins==68)||((ins==69)||((ins==70)||((ins==71)||((ins==72)||((ins==73)||((ins==74)||((ins==75)||((ins==76)||((ins==77)||((ins==78)||((ins==79)||((ins==80)||((ins==81)||((ins==82)||((ins==83)||((ins==84)||((ins==85)||((ins==86)||((ins==87)||((ins==88)||((ins==89)||((ins==90)||((ins==91)||((ins==92)||(ins==93)))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))
        begin
            if ((debug==1)&&rising)
            begin
                /* print removed */
            end
            OPPFSM=1;
        end
        else
        begin
            if ((ins==93)||(ins==94))
            begin
                if ((debug==1)&&rising)
                begin
                    /* print removed */
                end
                MOVFSM=1;
            end
            else
            begin
                if ((ins==126)||(ins==127))
                begin
                    if ((debug==1)&&rising)
                    begin
                        /* print removed */
                    end
                    POPPUSHFSM=1;
                end
                else
                begin
                    if ((ins==95)||((ins==96)||((ins==97)||((ins==98)||((ins==99)||((ins==100)||((ins==101)||((ins==102)||((ins==103)||((ins==104)||((ins==105)||((ins==106)||((ins==107)||((ins==108)||((ins==109)||((ins==110)||((ins==111)||((ins==112)||((ins==113)||((ins==114)||((ins==115)||((ins==116)||((ins==117)||((ins==118)||((ins==119)||((ins==124)||(ins==125)))))))))))))))))))))))))))
                    begin
                        if ((debug==1)&&rising)
                        begin
                            /* print removed */
                        end
                        LDSTFSM=1;
                    end
                    else
                    begin
                        if ((ins==32)||((ins==33)||((ins==34)||((ins==35)||((ins==29)||((ins==30)||(ins==31)))))))
                        begin
                            if ((debug==1)&&rising)
                            begin
                                /* print removed */
                            end
                            CALLRETFSM=1;
                        end
                        else
                        begin
                            if ((ins==120)||((ins==121)||((ins==122)||(ins==123))))
                            begin
                                if ((debug==1)&&rising)
                                begin
                                    /* print removed */
                                end
                                LPMFSM=1;
                            end
                        end
                    end
                end
            end
        end
    end
    RUN_CALLRETFSM<=CALLRETFSM;
    RUN_LDSTFSM<=LDSTFSM;
    RUN_MOVFSM<=MOVFSM;
    RUN_OPPFSM<=OPPFSM;
    RUN_POPPUSHFSM<=POPPUSHFSM;
    RUN_LPMFSM<=LPMFSM;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module OPP_FSM_7f9e35beec00 (
	input clk,
	input  reset,
	input  run,
	input [15:0] Instruction,
	input  Resp,
	input  Branch,
	input  Executed_Jump,
	output  reg  done,
	output  reg  LoadSelectMux,
	output  reg [4:0] LoadingMux,
	output  reg [4:0] InputSelectMemory,
	output  reg  WEMEMORY,
	output  reg [1:0] Read_Write,
	output  reg [4:0] Mem_Instruction,
	output  reg [2:0] IncDec,
	output  reg  InputSelectBuffer,
	output  reg [2:0] WEBUFFER,
	output  reg  Load_Z,
	output  reg  Load_K,
	output  reg  Load_Jump,
	output  reg  relative_Absolute,
	output  reg  Load_Byte,
	output  reg  Fetch_next_instruction,
	output  reg [7:0] WB_Addr,
	output  reg  Fetch_Address,
	output  reg  LOAD_PCL,
	output  reg  LOAD_PCH,
	output  reg [1:0] K_Select);
// Code generated from clock method
// wire/variable declaration
integer current_state;
integer _latched_inst;
integer _pointer_update_pending;
integer debug;
integer inst;
integer resp;
integer branch;
integer executed_jump;
integer run_active;
integer InputSelect_Buffer;
integer WE_Buffer;
integer LoadSelectMux_local;
integer LoadingMux_local;
integer Read_Write_local;
integer Mem_Instruction_local;
integer IncDec_local;
integer InputSelect_Memory;
integer WE_Memory;
integer WB_Addr_local;
integer Load_Z_local;
integer Load_K_local;
integer Load_Jump_local;
integer relative_Absolute_local;
integer Load_Byte_local;
integer Fetch_Address_local;
integer K_select;
integer done_local;
integer state;
integer i;
integer next_state;
// initial
initial
begin
    current_state=0;
    _latched_inst=0;
    _pointer_update_pending=0;
    debug=0;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        current_state=0;
        done<=0;
        LoadSelectMux<=0;
        LoadingMux<=0;
        InputSelectMemory<=0;
        WEMEMORY<=0;
        Read_Write<=0;
        Mem_Instruction<=0;
        IncDec<=0;
        InputSelectBuffer<=0;
        WEBUFFER<=0;
        Load_Z<=0;
        Load_K<=0;
        Load_Jump<=0;
        relative_Absolute<=0;
        Load_Byte<=0;
        Fetch_next_instruction<=0;
        WB_Addr<=0;
        Fetch_Address<=0;
        LOAD_PCL<=0;
        LOAD_PCH<=0;
        K_Select<=0;
    end
    else
    begin
        inst=Instruction;
        resp=Resp;
        branch=Branch;
        executed_jump=Executed_Jump;
        run_active=run;
        InputSelect_Buffer=0;
        WE_Buffer=0;
        LoadSelectMux_local=0;
        LoadingMux_local=0;
        Read_Write_local=0;
        Mem_Instruction_local=0;
        IncDec_local=0;
        InputSelect_Memory=0;
        WE_Memory=0;
        WB_Addr_local=0;
        Load_Z_local=0;
        Load_K_local=0;
        Load_Jump_local=0;
        relative_Absolute_local=0;
        Load_Byte_local=0;
        Fetch_Address_local=0;
        K_select=0;
        done_local=0;
        state=current_state;
        i=_latched_inst;
        next_state=state;
        case (state)
        0: if (run_active)
        begin
            _latched_inst=inst;
            i=inst;
            if ((i==73)||((i==74)||((i==77)||((i==78)||((i==79)||((i==80)||((i==81)||((i==82)||((i==83)||((i==84)||((i==85)||((i==86)||((i==87)||((i==88)||((i==89)||((i==90)||((i==91)||(i==92))))))))))))))))))
            begin
                next_state=18;
            end
            else
            begin
                if ((i==45)||((i==46)||((i==47)||((i==48)||((i==49)||((i==50)||((i==51)||((i==52)||((i==53)||((i==54)||((i==55)||((i==56)||((i==57)||((i==58)||((i==59)||((i==60)||((i==61)||((i==62)||((i==63)||(i==64))))))))))))))))))))
                begin
                    next_state=19;
                end
                else
                begin
                    if ((i==41)||(i==42))
                    begin
                        next_state=4;
                    end
                    else
                    begin
                        if ((i==65)||(i==66))
                        begin
                            next_state=14;
                        end
                        else
                        begin
                            next_state=1;
                        end
                    end
                end
            end
        end
        1: begin
        Mem_Instruction_local=12;
        Read_Write_local=2;
        InputSelect_Memory=1;
        next_state=2;
    end
    2: begin
    Read_Write_local=2;
    Mem_Instruction_local=12;
    if (resp)
    begin
        next_state=3;
    end
end
3: begin
Mem_Instruction_local=12;
InputSelect_Memory=1;
WE_Buffer=1;
InputSelect_Buffer=1;
if (resp==1)
begin
    next_state=3;
end
else
begin
    if ((i==67)||((i==68)||((i==69)||((i==70)||((i==71)||((i==72)||((i==76)||((i==14)||((i==15)||((i==18)||((i==19)||((i==20)||((i==21)||(i==22))))))))))))))
    begin
        next_state=18;
    end
    else
    begin
        if (((((i==16)||(i==17))||((i==5)||(i==7)))||((i==10)||(i==12)))||(i==40))
        begin
            next_state=17;
        end
        else
        begin
            if ((i==43)||(i==44))
            begin
                next_state=14;
            end
            else
            begin
                if ((i==3)||(i==8))
                begin
                    next_state=8;
                end
                else
                begin
                    next_state=4;
                end
            end
        end
    end
end
end
8: begin
Mem_Instruction_local=15;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=9;
end
9: begin
Mem_Instruction_local=15;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp)
begin
next_state=10;
end
end
10: begin
Mem_Instruction_local=15;
InputSelect_Memory=1;
WE_Buffer=2;
InputSelect_Buffer=1;
if ((i==3)||(i==8))
begin
next_state=17;
end
else
begin
next_state=11;
end
end
4: begin
Mem_Instruction_local=13;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=5;
end
5: begin
Mem_Instruction_local=13;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp)
begin
next_state=6;
end
end
6: begin
Mem_Instruction_local=13;
InputSelect_Memory=1;
if ((i==41)||(i==42))
begin
WE_Buffer=1;
end
else
begin
WE_Buffer=3;
end
InputSelect_Buffer=1;
next_state=7;
end
7: if (resp==0)
begin
next_state=18;
end
11: begin
Mem_Instruction_local=16;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=12;
end
12: begin
Mem_Instruction_local=16;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp)
begin
next_state=13;
end
end
13: begin
WE_Buffer=4;
InputSelect_Buffer=1;
next_state=18;
end
14: begin
Mem_Instruction_local=17;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=15;
end
15: begin
Mem_Instruction_local=17;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp)
begin
next_state=16;
end
end
16: begin
if ((i==65)||(i==66))
begin
WE_Buffer=1;
end
else
begin
WE_Buffer=5;
end
InputSelect_Buffer=1;
if (resp==1)
begin
next_state=16;
end
else
begin
next_state=18;
end
end
17: begin
WE_Buffer=3;
InputSelect_Buffer=0;
next_state=18;
end
18: if (i==40)
begin
done_local=1;
next_state=0;
end
else
begin
if ((i==75)||((i==37)||((i==38)||(i==39))))
begin
done_local=1;
next_state=0;
end
else
begin
if ((i==37)||((i==41)||((i==42)||((i==43)||(i==44)))))
begin
done_local=1;
next_state=0;
end
else
begin
if ((i==73)||((i==74)||((i==77)||((i==78)||((i==79)||((i==80)||((i==81)||((i==82)||((i==83)||((i==84)||((i==85)||((i==86)||((i==87)||((i==88)||((i==89)||((i==90)||((i==91)||(i==92))))))))))))))))))
begin
done_local=1;
next_state=0;
end
else
begin
if ((i==23)||((i==24)||((i==25)||((i==26)||((i==27)||(i==28))))))
begin
next_state=23;
end
else
begin
if ((i==45)||((i==46)||((i==47)||((i==48)||((i==49)||((i==50)||((i==51)||((i==52)||((i==53)||((i==54)||((i==55)||((i==56)||((i==57)||((i==58)||((i==59)||((i==60)||((i==61)||((i==62)||((i==63)||(i==64))))))))))))))))))))
begin
done_local=1;
next_state=0;
end
else
begin
if ((i==65)||(i==66))
begin
next_state=21;
end
else
begin
next_state=23;
end
end
end
end
end
end
end
19: if (branch==1)
begin
next_state=20;
end
else
begin
done_local=1;
next_state=0;
end
20: begin
Load_K_local=1;
K_select=0;
if (executed_jump==1)
begin
done_local=1;
next_state=0;
end
end
23: begin
if ((i==23)||((i==24)||((i==25)||((i==26)||((i==27)||(i==28))))))
begin
Mem_Instruction_local=14;
WB_Addr_local=0;
end
else
begin
Mem_Instruction_local=12;
WB_Addr_local=0;
end
Read_Write_local=1;
InputSelect_Memory=2;
next_state=24;
end
24: begin
if ((i==23)||((i==24)||((i==25)||((i==26)||((i==27)||(i==28))))))
begin
Mem_Instruction_local=14;
WB_Addr_local=0;
end
else
begin
Mem_Instruction_local=12;
WB_Addr_local=0;
end
Read_Write_local=1;
InputSelect_Memory=2;
if (resp)
begin
if ((i==23)||((i==24)||((i==25)||((i==26)||((i==27)||((i==28)||((i==3)||(i==8))))))))
begin
next_state=25;
end
else
begin
done_local=1;
next_state=0;
end
end
end
25: if (resp==0)
begin
next_state=26;
end
26: begin
if ((i==23)||((i==24)||((i==25)||((i==26)||((i==27)||(i==28))))))
begin
Mem_Instruction_local=14;
WB_Addr_local=1;
end
else
begin
Mem_Instruction_local=15;
WB_Addr_local=0;
end
Read_Write_local=1;
InputSelect_Memory=3;
next_state=27;
end
27: begin
if ((i==23)||((i==24)||((i==25)||((i==26)||((i==27)||(i==28))))))
begin
Mem_Instruction_local=14;
WB_Addr_local=1;
end
else
begin
Mem_Instruction_local=15;
WB_Addr_local=0;
end
Read_Write_local=1;
InputSelect_Memory=3;
if (resp)
begin
done_local=1;
next_state=0;
end
end
21: begin
Mem_Instruction_local=17;
Read_Write_local=1;
InputSelect_Memory=2;
next_state=22;
end
22: begin
Mem_Instruction_local=17;
Read_Write_local=1;
InputSelect_Memory=2;
if (resp)
begin
done_local=1;
next_state=0;
end
end
default:;
endcase
LoadSelectMux<=LoadSelectMux_local;
LoadingMux<=LoadingMux_local;
InputSelectMemory<=InputSelect_Memory;
WEMEMORY<=WE_Memory;
Read_Write<=Read_Write_local;
Mem_Instruction<=Mem_Instruction_local;
IncDec<=IncDec_local;
InputSelectBuffer<=InputSelect_Buffer;
WEBUFFER<=WE_Buffer;
Load_Z<=Load_Z_local;
Load_K<=Load_K_local;
Load_Jump<=Load_Jump_local;
relative_Absolute<=relative_Absolute_local;
Load_Byte<=Load_Byte_local;
Fetch_Address<=Fetch_Address_local;
K_Select<=K_select;
done<=done_local;
WB_Addr<=WB_Addr_local;
if (debug==1)
begin
/* print removed */
end
current_state=next_state;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module MOV_FSM_7f9e35bef650 (
	input clk,
	input  reset,
	input  run,
	input [15:0] Instruction,
	input  Resp,
	input  Branch,
	input  Executed_Jump,
	output  reg  done,
	output  reg  LoadSelectMux,
	output  reg [4:0] LoadingMux,
	output  reg [4:0] InputSelectMemory,
	output  reg  WEMEMORY,
	output  reg [1:0] Read_Write,
	output  reg [4:0] Mem_Instruction,
	output  reg [2:0] IncDec,
	output  reg  InputSelectBuffer,
	output  reg [2:0] WEBUFFER,
	output  reg  Load_Z,
	output  reg  Load_K,
	output  reg  Load_Jump,
	output  reg  relative_Absolute,
	output  reg  Load_Byte,
	output  reg  Fetch_next_instruction,
	output  reg [7:0] WB_Addr,
	output  reg  Fetch_Address,
	output  reg  LOAD_PCL,
	output  reg  LOAD_PCH);
// Code generated from clock method
// wire/variable declaration
integer current_state;
integer _latched_inst;
integer debug;
integer inst;
integer resp;
integer branch;
integer executed_jump;
integer run_active;
integer InputSelect_Buffer;
integer WE_Buffer;
integer LoadSelectMux_local;
integer LoadingMux_local;
integer Read_Write_local;
integer Mem_Instruction_local;
integer IncDec_local;
integer InputSelect_Memory;
integer WE_Memory;
integer WB_Addr_local;
integer Load_Z_local;
integer Load_K_local;
integer Load_Jump_local;
integer relative_Absolute_local;
integer Load_Byte_local;
integer Fetch_Address_local;
integer done_local;
integer state;
integer next_state;
integer i;
// initial
initial
begin
    current_state=0;
    _latched_inst=0;
    debug=1;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        current_state=0;
        done<=0;
        LoadSelectMux<=0;
        LoadingMux<=0;
        InputSelectMemory<=0;
        WEMEMORY<=0;
        Read_Write<=0;
        Mem_Instruction<=0;
        IncDec<=0;
        InputSelectBuffer<=0;
        WEBUFFER<=0;
        Load_Z<=0;
        Load_K<=0;
        Load_Jump<=0;
        relative_Absolute<=0;
        Load_Byte<=0;
        Fetch_next_instruction<=0;
        WB_Addr<=0;
        Fetch_Address<=0;
        LOAD_PCL<=0;
        LOAD_PCH<=0;
    end
    else
    begin
        inst=Instruction;
        resp=Resp;
        branch=Branch;
        executed_jump=Executed_Jump;
        run_active=run;
        InputSelect_Buffer=0;
        WE_Buffer=0;
        LoadSelectMux_local=0;
        LoadingMux_local=0;
        Read_Write_local=0;
        Mem_Instruction_local=0;
        IncDec_local=0;
        InputSelect_Memory=0;
        WE_Memory=0;
        WB_Addr_local=0;
        Load_Z_local=0;
        Load_K_local=0;
        Load_Jump_local=0;
        relative_Absolute_local=0;
        Load_Byte_local=0;
        Fetch_Address_local=0;
        done_local=0;
        state=current_state;
        next_state=state;
        if ((state==0)&&run_active)
        begin
            _latched_inst=inst;
        end
        i=_latched_inst;
        case (state)
        0: if (run_active==1)
        begin
            next_state=1;
        end
        1: begin
        Mem_Instruction_local=13;
        Read_Write_local=2;
        InputSelect_Memory=1;
        next_state=2;
    end
    2: begin
    Mem_Instruction_local=13;
    Read_Write_local=2;
    InputSelect_Memory=1;
    if (resp==1)
    begin
        WE_Memory=1;
        LoadingMux_local=14;
        next_state=3;
    end
end
3: begin
Mem_Instruction_local=12;
Read_Write_local=1;
InputSelect_Memory=16;
next_state=4;
end
4: begin
Mem_Instruction_local=12;
Read_Write_local=1;
InputSelect_Memory=16;
if (resp==1)
begin
if (i==94)
begin
    next_state=5;
end
else
begin
    next_state=0;
    done_local=1;
end
end
end
5: if (resp==0)
begin
next_state=6;
end
6: begin
Mem_Instruction_local=16;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=7;
end
7: begin
Mem_Instruction_local=16;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp==1)
begin
WE_Memory=1;
LoadingMux_local=14;
next_state=8;
end
end
8: next_state=9;
9: begin
Mem_Instruction_local=15;
Read_Write_local=1;
InputSelect_Memory=16;
next_state=10;
end
10: begin
Mem_Instruction_local=15;
Read_Write_local=1;
InputSelect_Memory=16;
if (resp==1)
begin
next_state=0;
done_local=1;
end
end
default:;
endcase
LoadSelectMux<=LoadSelectMux_local;
LoadingMux<=LoadingMux_local;
InputSelectMemory<=InputSelect_Memory;
WEMEMORY<=WE_Memory;
Read_Write<=Read_Write_local;
Mem_Instruction<=Mem_Instruction_local;
IncDec<=IncDec_local;
InputSelectBuffer<=InputSelect_Buffer;
WEBUFFER<=WE_Buffer;
Load_Z<=Load_Z_local;
Load_K<=Load_K_local;
Load_Jump<=Load_Jump_local;
relative_Absolute<=relative_Absolute_local;
Load_Byte<=Load_Byte_local;
Fetch_Address<=Fetch_Address_local;
done<=done_local;
WB_Addr<=WB_Addr_local;
if (debug&&(current_state!=0))
begin
/* print removed */
end
current_state=next_state;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module PopPush_FSM_7f9e35bf8080 (
	input clk,
	input  reset,
	input  run,
	input [15:0] Instruction,
	input  Resp,
	input  Branch,
	input  Executed_Jump,
	output  reg  done,
	output  reg  LoadSelectMux,
	output  reg [4:0] LoadingMux,
	output  reg [4:0] InputSelectMemory,
	output  reg  WEMEMORY,
	output  reg [1:0] Read_Write,
	output  reg [4:0] Mem_Instruction,
	output  reg [2:0] IncDec,
	output  reg  InputSelectBuffer,
	output  reg [2:0] WEBUFFER,
	output  reg  Load_Z,
	output  reg  Load_K,
	output  reg  Load_Jump,
	output  reg  relative_Absolute,
	output  reg  Load_Byte,
	output  reg  Fetch_next_instruction,
	output  reg [7:0] WB_Addr,
	output  reg  Fetch_Address,
	output  reg  LOAD_PCL,
	output  reg  LOAD_PCH);
// Code generated from clock method
// wire/variable declaration
integer current_state;
integer _latched_inst;
integer _wb_addr_val;
integer _pointer_update_pending;
integer _push_saw_resp_low;
integer debug;
integer inst;
integer resp;
integer branch;
integer executed_jump;
integer run_active;
integer InputSelect_Buffer;
integer WE_Buffer;
integer LoadSelectMux_local;
integer LoadingMux_local;
integer Read_Write_local;
integer Mem_Instruction_local;
integer IncDec_local;
integer InputSelect_Memory;
integer WE_Memory;
integer WB_Addr_local;
integer Load_Z_local;
integer Load_K_local;
integer Load_Jump_local;
integer relative_Absolute_local;
integer Load_Byte_local;
integer Fetch_Address_local;
integer done_local;
integer state;
integer i;
integer next_state;
// initial
initial
begin
    current_state=0;
    _latched_inst=0;
    _wb_addr_val=0;
    _pointer_update_pending=0;
    _push_saw_resp_low=0;
    debug=1;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        current_state=0;
        _latched_inst=0;
        _pointer_update_pending=0;
        _wb_addr_val=0;
        _push_saw_resp_low=0;
        done<=0;
        LoadSelectMux<=0;
        LoadingMux<=0;
        InputSelectMemory<=0;
        WEMEMORY<=0;
        Read_Write<=0;
        Mem_Instruction<=0;
        IncDec<=0;
        InputSelectBuffer<=0;
        WEBUFFER<=0;
        Load_Z<=0;
        Load_K<=0;
        Load_Jump<=0;
        relative_Absolute<=0;
        Load_Byte<=0;
        Fetch_next_instruction<=0;
        WB_Addr<=0;
        Fetch_Address<=0;
        LOAD_PCL<=0;
        LOAD_PCH<=0;
    end
    else
    begin
        inst=Instruction;
        resp=Resp;
        branch=Branch;
        executed_jump=Executed_Jump;
        run_active=run;
        InputSelect_Buffer=0;
        WE_Buffer=0;
        LoadSelectMux_local=0;
        LoadingMux_local=0;
        Read_Write_local=0;
        Mem_Instruction_local=0;
        IncDec_local=0;
        InputSelect_Memory=0;
        WE_Memory=0;
        WB_Addr_local=0;
        Load_Z_local=0;
        Load_K_local=0;
        Load_Jump_local=0;
        relative_Absolute_local=0;
        Load_Byte_local=0;
        Fetch_Address_local=0;
        done_local=0;
        state=current_state;
        i=_latched_inst;
        next_state=state;
        if ((state==0)&&run_active)
        begin
            _latched_inst=inst;
            i=_latched_inst;
        end
        case (state)
        0: if (run_active)
        begin
            if (i==127)
            begin
                next_state=1;
            end
            else
            begin
                next_state=5;
            end
        end
        1: begin
        Mem_Instruction_local=7;
        Read_Write_local=2;
        IncDec_local=4;
        next_state=2;
    end
    2: begin
    Mem_Instruction_local=7;
    Read_Write_local=2;
    IncDec_local=0;
    if (resp)
    begin
        WE_Memory=1;
        LoadingMux_local=14;
        next_state=3;
    end
end
3: begin
Mem_Instruction_local=12;
Read_Write_local=1;
InputSelect_Memory=16;
next_state=4;
end
4: begin
Mem_Instruction_local=12;
Read_Write_local=1;
InputSelect_Memory=16;
if (resp)
begin
done_local=1;
next_state=0;
end
end
5: begin
Mem_Instruction_local=12;
Read_Write_local=2;
next_state=6;
end
6: begin
Mem_Instruction_local=12;
Read_Write_local=2;
if (resp)
begin
WE_Memory=1;
LoadingMux_local=14;
next_state=9;
end
end
9: next_state=7;
7: begin
Mem_Instruction_local=7;
Read_Write_local=1;
IncDec_local=3;
InputSelect_Memory=16;
_push_saw_resp_low=0;
next_state=8;
end
8: begin
Mem_Instruction_local=7;
Read_Write_local=1;
IncDec_local=0;
InputSelect_Memory=16;
if (!resp)
begin
_push_saw_resp_low=1;
end
else
begin
if (_push_saw_resp_low)
begin
done_local=1;
next_state=0;
end
end
end
default:;
endcase
LoadSelectMux<=LoadSelectMux_local;
LoadingMux<=LoadingMux_local;
InputSelectMemory<=InputSelect_Memory;
WEMEMORY<=WE_Memory;
Read_Write<=Read_Write_local;
Mem_Instruction<=Mem_Instruction_local;
IncDec<=IncDec_local;
InputSelectBuffer<=InputSelect_Buffer;
WEBUFFER<=WE_Buffer;
Load_Z<=Load_Z_local;
Load_K<=Load_K_local;
Load_Jump<=Load_Jump_local;
relative_Absolute<=relative_Absolute_local;
Load_Byte<=Load_Byte_local;
Fetch_Address<=Fetch_Address_local;
done<=done_local;
WB_Addr<=_wb_addr_val;
if (debug&&(current_state!=0))
begin
/* print removed */
end
current_state=next_state;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module LDST_FSM_7f9e35bf8a70 (
	input clk,
	input  reset,
	input  run,
	input [15:0] Instruction,
	input  Resp,
	input  Branch,
	input  Executed_Jump,
	input  Address_fetched,
	output  reg  done,
	output  reg  LoadSelectMux,
	output  reg [4:0] LoadingMux,
	output  reg [4:0] InputSelectMemory,
	output  reg  WEMEMORY,
	output  reg [1:0] Read_Write,
	output  reg [4:0] Mem_Instruction,
	output  reg [2:0] IncDec,
	output  reg  InputSelectBuffer,
	output  reg [2:0] WEBUFFER,
	output  reg  Load_Z,
	output  reg  Load_K,
	output  reg  Load_Jump,
	output  reg  relative_Absolute,
	output  reg  Load_Byte,
	output  reg  Fetch_next_instruction,
	output  reg [7:0] WB_Addr,
	output  reg  Fetch_Address,
	output  reg  LOAD_PCL,
	output  reg  LOAD_PCH);
// Code generated from clock method
// wire/variable declaration
integer current_state;
integer _latched_inst;
integer _wb_addr_val;
integer _pointer_update_pending;
integer _h_saw_resp_low;
integer _deferred_post_inc;
integer _ptr_mem_instruction;
integer debug;
integer inst;
integer resp;
integer branch;
integer executed_jump;
integer run_active;
integer InputSelect_Buffer;
integer WE_Buffer;
integer LoadSelectMux_local;
integer LoadingMux_local;
integer Read_Write_local;
integer Mem_Instruction_local;
integer IncDec_local;
integer InputSelect_Memory;
integer WE_Memory;
integer WB_Addr_local;
integer Load_Z_local;
integer Load_K_local;
integer Load_Jump_local;
integer relative_Absolute_local;
integer Load_Byte_local;
integer Fetch_Address_local;
integer done_local;
integer state;
integer next_state;
integer i;
// initial
initial
begin
    current_state=0;
    _latched_inst=0;
    _wb_addr_val=0;
    _pointer_update_pending=0;
    _h_saw_resp_low=0;
    _deferred_post_inc=0;
    _ptr_mem_instruction=0;
    debug=0;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        current_state=0;
        _deferred_post_inc=0;
        _h_saw_resp_low=0;
        _latched_inst=0;
        _pointer_update_pending=0;
        _ptr_mem_instruction=0;
        _wb_addr_val=0;
        done<=0;
        LoadSelectMux<=0;
        LoadingMux<=0;
        InputSelectMemory<=0;
        WEMEMORY<=0;
        Read_Write<=0;
        Mem_Instruction<=0;
        IncDec<=0;
        InputSelectBuffer<=0;
        WEBUFFER<=0;
        Load_Z<=0;
        Load_K<=0;
        Load_Jump<=0;
        relative_Absolute<=0;
        Load_Byte<=0;
        Fetch_next_instruction<=0;
        WB_Addr<=0;
        Fetch_Address<=0;
        LOAD_PCL<=0;
        LOAD_PCH<=0;
    end
    else
    begin
        inst=Instruction;
        resp=Resp;
        branch=Branch;
        executed_jump=Executed_Jump;
        run_active=run;
        InputSelect_Buffer=0;
        WE_Buffer=0;
        LoadSelectMux_local=0;
        LoadingMux_local=0;
        Read_Write_local=0;
        Mem_Instruction_local=0;
        IncDec_local=0;
        InputSelect_Memory=0;
        WE_Memory=0;
        WB_Addr_local=0;
        Load_Z_local=0;
        Load_K_local=0;
        Load_Jump_local=0;
        relative_Absolute_local=0;
        Load_Byte_local=0;
        Fetch_Address_local=0;
        done_local=0;
        state=current_state;
        next_state=state;
        if ((state==0)&&run_active)
        begin
            _latched_inst=inst;
        end
        i=_latched_inst;
        case (state)
        0: if (run_active)
        begin
            if (inst==95)
            begin
                next_state=8;
            end
            else
            begin
                if ((inst==107)||((inst==124)||((inst==125)||(inst==119))))
                begin
                    case (inst)
                    107: next_state=22;
                    119: next_state=14;
                    124: next_state=26;
                    125: next_state=14;
                    default:;
                endcase
            end
            else
            begin
                next_state=1;
            end
        end
    end
    1: begin
    if ((inst==96)||((inst==97)||((inst==98)||((inst==108)||((inst==109)||(inst==110))))))
    begin
        _wb_addr_val=26;
        WB_Addr_local=26;
    end
    else
    begin
        if ((inst==99)||((inst==100)||((inst==101)||((inst==102)||((inst==111)||((inst==112)||((inst==113)||(inst==114))))))))
        begin
            _wb_addr_val=28;
            WB_Addr_local=28;
        end
        else
        begin
            if ((inst==103)||((inst==104)||((inst==105)||((inst==106)||((inst==115)||((inst==116)||((inst==117)||(inst==118))))))))
            begin
                _wb_addr_val=30;
                WB_Addr_local=30;
            end
        end
    end
    Mem_Instruction_local=14;
    Read_Write_local=2;
    InputSelect_Memory=1;
    next_state=2;
end
2: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp)
begin
    next_state=3;
end
end
3: begin
WE_Memory=1;
if ((inst==96)||((inst==97)||((inst==98)||((inst==108)||((inst==109)||(inst==110))))))
begin
LoadingMux_local=1;
end
else
begin
if ((inst==99)||((inst==100)||((inst==101)||((inst==102)||((inst==111)||((inst==112)||((inst==113)||(inst==114))))))))
begin
    LoadingMux_local=3;
end
else
begin
    if ((inst==103)||((inst==104)||((inst==105)||((inst==106)||((inst==115)||((inst==116)||((inst==117)||(inst==118))))))))
    begin
        LoadingMux_local=5;
    end
end
end
next_state=4;
end
4: begin
Mem_Instruction_local=0;
Read_Write_local=0;
InputSelect_Memory=0;
next_state=5;
end
5: begin
if ((inst==96)||((inst==97)||((inst==98)||((inst==108)||((inst==109)||(inst==110))))))
begin
_wb_addr_val=27;
WB_Addr_local=27;
end
else
begin
if ((inst==99)||((inst==100)||((inst==101)||((inst==102)||((inst==111)||((inst==112)||((inst==113)||(inst==114))))))))
begin
_wb_addr_val=29;
WB_Addr_local=29;
end
else
begin
if ((inst==103)||((inst==104)||((inst==105)||((inst==106)||((inst==115)||((inst==116)||((inst==117)||(inst==118))))))))
begin
_wb_addr_val=31;
WB_Addr_local=31;
end
end
end
Mem_Instruction_local=14;
Read_Write_local=2;
InputSelect_Memory=1;
_h_saw_resp_low=0;
next_state=6;
end
6: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=2;
InputSelect_Memory=1;
if (!resp)
begin
_h_saw_resp_low=1;
end
else
begin
if (_h_saw_resp_low)
begin
next_state=7;
end
end
end
7: begin
WE_Memory=1;
if ((inst==96)||((inst==97)||((inst==98)||((inst==108)||((inst==109)||(inst==110))))))
begin
LoadingMux_local=2;
end
else
begin
if ((inst==99)||((inst==100)||((inst==101)||((inst==102)||((inst==111)||((inst==112)||((inst==113)||(inst==114))))))))
begin
LoadingMux_local=4;
end
else
begin
if ((inst==103)||((inst==104)||((inst==105)||((inst==106)||((inst==115)||((inst==116)||((inst==117)||(inst==118))))))))
begin
LoadingMux_local=6;
end
end
end
if ((i==96)||((i==97)||((i==98)||((i==99)||((i==100)||((i==101)||((i==102)||((i==103)||((i==104)||((i==105)||((i==106)||(i==107))))))))))))
begin
next_state=10;
end
else
begin
if ((i==108)||((i==109)||((i==110)||((i==111)||((i==112)||((i==113)||((i==114)||((i==115)||((i==116)||((i==117)||((i==118)||(i==119))))))))))))
begin
next_state=14;
end
else
begin
case (i)
124: next_state=26;
125: next_state=14;
default:next_state=0;
endcase
end
end
end
8: begin
_pointer_update_pending=0;
Mem_Instruction_local=12;
Read_Write_local=1;
InputSelect_Memory=4;
next_state=9;
end
9: begin
Mem_Instruction_local=12;
Read_Write_local=1;
InputSelect_Memory=4;
if (resp)
begin
done_local=1;
next_state=0;
end
end
10: begin
_pointer_update_pending=0;
_deferred_post_inc=0;
_h_saw_resp_low=0;
if ((i==96)||((i==97)||((i==98)||((i==108)||((i==109)||(i==110))))))
begin
case (i)
96: Mem_Instruction_local=1;
97: begin
Mem_Instruction_local=1;
_deferred_post_inc=1;
_pointer_update_pending=1;
end
98: begin
Mem_Instruction_local=1;
IncDec_local=2;
_pointer_update_pending=1;
end
default:;
endcase
end
else
begin
if ((i==99)||((i==100)||((i==101)||((i==102)||((i==111)||((i==112)||((i==113)||(i==114))))))))
begin
case (i)
99: Mem_Instruction_local=3;
100: begin
Mem_Instruction_local=3;
_deferred_post_inc=1;
_pointer_update_pending=1;
end
101: begin
Mem_Instruction_local=3;
IncDec_local=2;
_pointer_update_pending=1;
end
102: Mem_Instruction_local=10;
default:;
endcase
end
else
begin
if ((i==103)||((i==104)||((i==105)||((i==106)||((i==115)||((i==116)||((i==117)||(i==118))))))))
begin
case (i)
103: Mem_Instruction_local=5;
104: begin
Mem_Instruction_local=5;
_deferred_post_inc=1;
_pointer_update_pending=1;
end
105: begin
Mem_Instruction_local=5;
IncDec_local=2;
_pointer_update_pending=1;
end
106: Mem_Instruction_local=11;
default:;
endcase
end
end
end
_ptr_mem_instruction=Mem_Instruction_local;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=11;
end
11: begin
Mem_Instruction_local=_ptr_mem_instruction;
Read_Write_local=2;
InputSelect_Memory=1;
if (!resp)
begin
_h_saw_resp_low=1;
end
else
begin
if (_h_saw_resp_low)
begin
WE_Memory=1;
LoadingMux_local=14;
if (_deferred_post_inc)
begin
IncDec_local=1;
_deferred_post_inc=0;
end
next_state=12;
end
end
end
12: begin
Mem_Instruction_local=12;
Read_Write_local=1;
InputSelect_Memory=16;
next_state=13;
end
13: begin
Mem_Instruction_local=12;
Read_Write_local=1;
InputSelect_Memory=16;
if (resp)
begin
if (_pointer_update_pending)
begin
next_state=30;
end
else
begin
done_local=1;
next_state=0;
end
end
end
14: begin
_pointer_update_pending=0;
Mem_Instruction_local=12;
Read_Write_local=2;
InputSelect_Memory=1;
_h_saw_resp_low=0;
next_state=15;
end
15: begin
Mem_Instruction_local=12;
Read_Write_local=2;
InputSelect_Memory=1;
if (!resp)
begin
_h_saw_resp_low=1;
end
else
begin
if (_h_saw_resp_low)
begin
if ((i==119)||(i==125))
begin
next_state=16;
end
else
begin
if ((i==108)||((i==109)||((i==110)||((i==111)||((i==112)||((i==113)||((i==114)||((i==115)||((i==116)||((i==117)||((i==118)||(i==119))))))))))))
begin
WE_Memory=1;
LoadingMux_local=14;
next_state=17;
end
end
end
end
end
16: begin
Mem_Instruction_local=12;
Read_Write_local=2;
WE_Memory=0;
LoadingMux_local=14;
next_state=34;
end
34: begin
Mem_Instruction_local=12;
Read_Write_local=2;
LoadingMux_local=14;
if (resp)
begin
WE_Memory=1;
case (i)
119: next_state=19;
125: next_state=28;
default:;
endcase
end
else
begin
WE_Memory=0;
end
end
17: begin
_pointer_update_pending=0;
_deferred_post_inc=0;
if ((i==96)||((i==97)||((i==98)||((i==108)||((i==109)||(i==110))))))
begin
Mem_Instruction_local=1;
case (i)
109: begin
_deferred_post_inc=1;
_pointer_update_pending=1;
end
110: begin
IncDec_local=2;
_pointer_update_pending=1;
end
default:;
endcase
end
else
begin
if ((i==99)||((i==100)||((i==101)||((i==102)||((i==111)||((i==112)||((i==113)||(i==114))))))))
begin
if (i==114)
begin
Mem_Instruction_local=10;
end
else
begin
Mem_Instruction_local=3;
end
case (i)
112: begin
_deferred_post_inc=1;
_pointer_update_pending=1;
end
113: begin
IncDec_local=2;
_pointer_update_pending=1;
end
default:;
endcase
end
else
begin
if ((i==103)||((i==104)||((i==105)||((i==106)||((i==115)||((i==116)||((i==117)||(i==118))))))))
begin
if (i==118)
begin
Mem_Instruction_local=11;
end
else
begin
Mem_Instruction_local=5;
end
case (i)
116: begin
_deferred_post_inc=1;
_pointer_update_pending=1;
end
117: begin
IncDec_local=2;
_pointer_update_pending=1;
end
default:;
endcase
end
end
end
Read_Write_local=1;
InputSelect_Memory=16;
next_state=18;
end
18: begin
if (i==119)
begin
Mem_Instruction_local=9;
InputSelect_Memory=16;
end
else
begin
if ((i==96)||((i==97)||((i==98)||((i==108)||((i==109)||(i==110))))))
begin
Mem_Instruction_local=1;
InputSelect_Memory=16;
end
else
begin
if ((i==99)||((i==100)||((i==101)||((i==102)||((i==111)||((i==112)||((i==113)||(i==114))))))))
begin
if (i==114)
begin
Mem_Instruction_local=10;
end
else
begin
Mem_Instruction_local=3;
end
InputSelect_Memory=16;
end
else
begin
if ((i==103)||((i==104)||((i==105)||((i==106)||((i==115)||((i==116)||((i==117)||(i==118))))))))
begin
if (i==118)
begin
Mem_Instruction_local=11;
end
else
begin
Mem_Instruction_local=5;
end
InputSelect_Memory=16;
end
end
end
end
Read_Write_local=1;
if (resp)
begin
if (_deferred_post_inc)
begin
IncDec_local=1;
_deferred_post_inc=0;
end
if (_pointer_update_pending)
begin
next_state=30;
end
else
begin
done_local=1;
next_state=0;
end
end
end
26: begin
_pointer_update_pending=0;
Mem_Instruction_local=18;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=27;
end
27: begin
Mem_Instruction_local=18;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp)
begin
WE_Memory=1;
LoadingMux_local=14;
next_state=12;
end
end
28: begin
Mem_Instruction_local=18;
Read_Write_local=1;
InputSelect_Memory=16;
next_state=29;
end
29: begin
Mem_Instruction_local=18;
Read_Write_local=1;
InputSelect_Memory=16;
if (resp)
begin
done_local=1;
next_state=0;
end
end
30: begin
if ((i==96)||((i==97)||((i==98)||((i==108)||((i==109)||(i==110))))))
begin
_wb_addr_val=26;
WB_Addr_local=26;
end
else
begin
if ((i==99)||((i==100)||((i==101)||((i==102)||((i==111)||((i==112)||((i==113)||(i==114))))))))
begin
_wb_addr_val=28;
WB_Addr_local=28;
end
else
begin
if ((i==103)||((i==104)||((i==105)||((i==106)||((i==115)||((i==116)||((i==117)||(i==118))))))))
begin
_wb_addr_val=30;
WB_Addr_local=30;
end
end
end
Mem_Instruction_local=14;
Read_Write_local=1;
if ((i==96)||((i==97)||((i==98)||((i==108)||((i==109)||(i==110))))))
begin
InputSelect_Memory=6;
end
else
begin
if ((i==99)||((i==100)||((i==101)||((i==102)||((i==111)||((i==112)||((i==113)||(i==114))))))))
begin
InputSelect_Memory=8;
end
else
begin
if ((i==103)||((i==104)||((i==105)||((i==106)||((i==115)||((i==116)||((i==117)||(i==118))))))))
begin
InputSelect_Memory=10;
end
end
end
next_state=31;
end
31: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=1;
if ((i==96)||((i==97)||((i==98)||((i==108)||((i==109)||(i==110))))))
begin
InputSelect_Memory=6;
end
else
begin
if ((i==99)||((i==100)||((i==101)||((i==102)||((i==111)||((i==112)||((i==113)||(i==114))))))))
begin
InputSelect_Memory=8;
end
else
begin
if ((i==103)||((i==104)||((i==105)||((i==106)||((i==115)||((i==116)||((i==117)||(i==118))))))))
begin
InputSelect_Memory=10;
end
end
end
if (resp)
begin
next_state=32;
end
end
32: begin
if ((i==96)||((i==97)||((i==98)||((i==108)||((i==109)||(i==110))))))
begin
_wb_addr_val=27;
WB_Addr_local=27;
InputSelect_Memory=7;
end
else
begin
if ((i==99)||((i==100)||((i==101)||((i==102)||((i==111)||((i==112)||((i==113)||(i==114))))))))
begin
_wb_addr_val=29;
WB_Addr_local=29;
InputSelect_Memory=9;
end
else
begin
if ((i==103)||((i==104)||((i==105)||((i==106)||((i==115)||((i==116)||((i==117)||(i==118))))))))
begin
_wb_addr_val=31;
WB_Addr_local=31;
InputSelect_Memory=11;
end
end
end
Mem_Instruction_local=14;
Read_Write_local=1;
next_state=33;
end
33: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=1;
if ((i==96)||((i==97)||((i==98)||((i==108)||((i==109)||(i==110))))))
begin
InputSelect_Memory=7;
end
else
begin
if ((i==99)||((i==100)||((i==101)||((i==102)||((i==111)||((i==112)||((i==113)||(i==114))))))))
begin
InputSelect_Memory=9;
end
else
begin
if ((i==103)||((i==104)||((i==105)||((i==106)||((i==115)||((i==116)||((i==117)||(i==118))))))))
begin
InputSelect_Memory=11;
end
end
end
if (resp)
begin
done_local=1;
next_state=0;
end
end
19: begin
Fetch_Address_local=1;
next_state=20;
end
20: begin
Fetch_Address_local=1;
if (Address_fetched==1)
begin
next_state=21;
end
end
21: begin
Fetch_Address_local=1;
Mem_Instruction_local=9;
Read_Write_local=1;
InputSelect_Memory=16;
next_state=18;
end
22: begin
_pointer_update_pending=0;
Fetch_Address_local=1;
next_state=23;
end
23: begin
Fetch_Address_local=1;
if (Address_fetched==1)
begin
next_state=24;
end
end
24: begin
Fetch_Address_local=1;
Mem_Instruction_local=9;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=25;
end
25: begin
Fetch_Address_local=1;
Mem_Instruction_local=9;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp)
begin
WE_Memory=1;
LoadingMux_local=14;
next_state=12;
end
end
default:;
endcase
LoadSelectMux<=LoadSelectMux_local;
LoadingMux<=LoadingMux_local;
InputSelectMemory<=InputSelect_Memory;
WEMEMORY<=WE_Memory;
Read_Write<=Read_Write_local;
Mem_Instruction<=Mem_Instruction_local;
IncDec<=IncDec_local;
InputSelectBuffer<=InputSelect_Buffer;
WEBUFFER<=WE_Buffer;
Load_Z<=Load_Z_local;
Load_K<=Load_K_local;
Load_Jump<=Load_Jump_local;
relative_Absolute<=relative_Absolute_local;
Load_Byte<=Load_Byte_local;
Fetch_Address<=Fetch_Address_local;
done<=done_local;
WB_Addr<=WB_Addr_local;
if (debug)
begin
/* print removed */
end
current_state=next_state;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module CallRet_FSM_7f9e35bf94c0 (
	input clk,
	input  reset,
	input  run,
	input [15:0] Instruction,
	input  Resp,
	input  Branch,
	input  Executed_Jump,
	input  Address_fetched,
	output  reg  done,
	output  reg  LoadSelectMux,
	output  reg [4:0] LoadingMux,
	output  reg [4:0] InputSelectMemory,
	output  reg  WEMEMORY,
	output  reg [1:0] Read_Write,
	output  reg [4:0] Mem_Instruction,
	output  reg [2:0] IncDec,
	output  reg  InputSelectBuffer,
	output  reg [2:0] WEBUFFER,
	output  reg  Load_Z,
	output  reg  Load_K,
	output  reg  Load_Jump,
	output  reg  relative_Absolute,
	output  reg  Load_Byte,
	output  reg [7:0] WB_Addr,
	output  reg  Fetch_Address,
	output  reg  LOAD_PCL,
	output  reg  LOAD_PCH,
	output  reg [1:0] K_SELECT);
// Code generated from clock method
// wire/variable declaration
integer current_state;
integer _latched_inst;
integer _wb_addr_val;
integer _pointer_update_pending;
integer _h_saw_resp_low;
integer debug;
integer inst;
integer resp;
integer branch;
integer executed_jump;
integer run_active;
integer address_fetched;
integer InputSelect_Buffer;
integer WE_Buffer;
integer LoadSelectMux_local;
integer LoadingMux_local;
integer RH_K_select;
integer RH_Load_K;
integer Read_Write_local;
integer Mem_Instruction_local;
integer IncDec_local;
integer InputSelect_Memory;
integer WE_Memory;
integer WB_Addr_local;
integer Load_Z_local;
integer Load_K_local;
integer Load_Jump_local;
integer relative_Absolute_local;
integer Load_Byte_local;
integer Fetch_Address_local;
integer Load_PCL;
integer Load_PCH;
integer done_local;
integer JumpWidth;
integer K_select;
integer state;
integer i;
integer next_state;
// initial
initial
begin
    current_state=0;
    _latched_inst=0;
    _wb_addr_val=0;
    _pointer_update_pending=0;
    _h_saw_resp_low=0;
    debug=0;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        current_state=0;
        _latched_inst=0;
        _pointer_update_pending=0;
        _wb_addr_val=0;
        _h_saw_resp_low=0;
        done<=0;
        LoadSelectMux<=0;
        LoadingMux<=0;
        InputSelectMemory<=0;
        WEMEMORY<=0;
        Read_Write<=0;
        Mem_Instruction<=0;
        IncDec<=0;
        InputSelectBuffer<=0;
        WEBUFFER<=0;
        Load_Z<=0;
        Load_K<=0;
        Load_Jump<=0;
        relative_Absolute<=0;
        Load_Byte<=0;
        WB_Addr<=0;
        Fetch_Address<=0;
        LOAD_PCL<=0;
        LOAD_PCH<=0;
        K_SELECT<=0;
    end
    else
    begin
        inst=Instruction;
        resp=Resp;
        branch=Branch;
        executed_jump=Executed_Jump;
        run_active=run;
        address_fetched=Address_fetched;
        InputSelect_Buffer=0;
        WE_Buffer=0;
        LoadSelectMux_local=0;
        LoadingMux_local=0;
        RH_K_select=0;
        RH_Load_K=0;
        Read_Write_local=0;
        Mem_Instruction_local=0;
        IncDec_local=0;
        InputSelect_Memory=0;
        WE_Memory=0;
        WB_Addr_local=0;
        Load_Z_local=0;
        Load_K_local=0;
        Load_Jump_local=0;
        relative_Absolute_local=0;
        Load_Byte_local=0;
        Fetch_Address_local=0;
        Load_PCL=0;
        Load_PCH=0;
        done_local=0;
        JumpWidth=1;
        K_select=0;
        state=current_state;
        i=_latched_inst;
        next_state=state;
        case (state)
        0: if (run_active==1)
        begin
            _latched_inst=inst;
            case (_latched_inst)
            29: next_state=6;
            30: next_state=9;
            31: next_state=16;
            35: next_state=19;
            default:next_state=4;
        endcase
    end
    4: begin
    Read_Write_local=1;
    Mem_Instruction_local=7;
    InputSelect_Memory=15;
    IncDec_local=3;
    next_state=5;
end
5: begin
Read_Write_local=1;
Mem_Instruction_local=7;
InputSelect_Memory=15;
IncDec_local=0;
if (resp==1)
begin
    next_state=2;
end
end
2: begin
Read_Write_local=1;
Mem_Instruction_local=7;
InputSelect_Memory=14;
IncDec_local=3;
next_state=3;
end
3: begin
Read_Write_local=1;
Mem_Instruction_local=7;
InputSelect_Memory=14;
IncDec_local=0;
if (resp==1)
begin
case (i)
32: next_state=6;
33: next_state=9;
default:next_state=16;
endcase
end
end
6: begin
Load_K_local=1;
next_state=7;
end
7: next_state=8;
8: begin
Load_Jump_local=1;
K_select=1;
relative_Absolute_local=0;
if (executed_jump==1)
begin
next_state=0;
done_local=1;
end
end
9: begin
WB_Addr_local=30;
Mem_Instruction_local=14;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=10;
end
10: begin
WB_Addr_local=30;
Mem_Instruction_local=14;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp==1)
begin
next_state=11;
end
end
11: begin
WB_Addr_local=30;
Mem_Instruction_local=14;
Read_Write_local=2;
InputSelect_Memory=1;
WE_Memory=1;
LoadingMux_local=5;
next_state=12;
end
12: begin
WB_Addr_local=31;
Mem_Instruction_local=14;
Read_Write_local=2;
InputSelect_Memory=1;
next_state=13;
end
13: begin
WB_Addr_local=31;
Mem_Instruction_local=14;
Read_Write_local=2;
InputSelect_Memory=1;
if (resp==1)
begin
next_state=14;
end
end
14: begin
WB_Addr_local=31;
Mem_Instruction_local=14;
Read_Write_local=2;
WE_Memory=1;
LoadingMux_local=6;
next_state=15;
end
15: begin
Load_Z_local=1;
if (executed_jump==1)
begin
done_local=1;
next_state=0;
end
end
16: begin
Fetch_Address_local=1;
next_state=17;
end
17: if (address_fetched==1)
begin
Fetch_Address_local=0;
next_state=18;
end
18: begin
Load_Jump_local=1;
relative_Absolute_local=1;
K_select=2;
if (executed_jump==1)
begin
next_state=0;
done_local=1;
end
end
19: begin
Read_Write_local=2;
Mem_Instruction_local=7;
IncDec_local=4;
next_state=20;
end
20: begin
Read_Write_local=2;
Mem_Instruction_local=7;
IncDec_local=0;
if (resp==1)
begin
next_state=21;
end
end
21: next_state=22;
22: begin
Load_PCL=1;
next_state=23;
end
23: begin
Read_Write_local=2;
Mem_Instruction_local=7;
IncDec_local=4;
_h_saw_resp_low=0;
next_state=24;
end
24: begin
Read_Write_local=2;
Mem_Instruction_local=7;
IncDec_local=0;
if (!resp)
begin
_h_saw_resp_low=1;
end
else
begin
if (_h_saw_resp_low)
begin
next_state=25;
end
end
end
25: next_state=26;
26: begin
Load_PCH=1;
next_state=0;
done_local=1;
end
default:;
endcase
LoadSelectMux<=LoadSelectMux_local;
LoadingMux<=LoadingMux_local;
InputSelectMemory<=InputSelect_Memory;
WEMEMORY<=WE_Memory;
Read_Write<=Read_Write_local;
Mem_Instruction<=Mem_Instruction_local;
IncDec<=IncDec_local;
InputSelectBuffer<=InputSelect_Buffer;
WEBUFFER<=WE_Buffer;
Load_Z<=Load_Z_local;
Load_K<=Load_K_local;
Load_Jump<=Load_Jump_local;
relative_Absolute<=relative_Absolute_local;
Load_Byte<=Load_Byte_local;
Fetch_Address<=Fetch_Address_local;
LOAD_PCL<=Load_PCL;
LOAD_PCH<=Load_PCH;
WB_Addr<=WB_Addr_local;
done<=done_local;
K_SELECT<=K_select;
if (debug&&(current_state!=0))
begin
/* print removed */
end
current_state=next_state;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module LPM_FSM_7f9e35bf9f10 (
	input clk,
	input  reset,
	input  run,
	input [15:0] Instruction,
	input  Resp,
	input  Branch,
	input  Executed_Jump,
	input  Address_fetched,
	input  SPM_Done,
	output  reg  done,
	output  reg  NotExecute,
	output  reg  LoadSelectMux,
	output  reg [4:0] LoadingMux,
	output  reg [4:0] Input_Select,
	output  reg  WE,
	output  reg [1:0] Read_Write,
	output  reg [4:0] Mem_Instruction,
	output  reg [2:0] IncDec,
	output  reg [2:0] write_Opperand_Buffer,
	output  reg  InputSelect,
	output  reg  Write_Enable,
	output  reg  Load_Z,
	output  reg  Load_K,
	output  reg  Load_Jump,
	output  reg  relative_Absolute,
	output  reg  Load_Byte,
	output  reg  Fetch_next_instruction,
	output  reg  Fetch_Address,
	output  reg  LOAD_PCL,
	output  reg  LOAD_PCH,
	output  reg [7:0] WB_Addr,
	output  reg  LPM_req,
	output  reg  SPM_req);
// Code generated from clock method
// wire/variable declaration
integer current_state;
integer _latched_inst;
integer _wb_addr_val;
integer _pointer_update_pending;
integer _saw_resp_low;
integer debug;
integer inst;
integer resp;
integer executed_jump;
integer address_fetched;
integer run_active;
integer InputSelect_Buffer;
integer NotExecute_local;
integer LoadSelectMux_local;
integer LoadingMux_local;
integer Input_Select_local;
integer WE_local;
integer Read_Write_local;
integer Mem_Instruction_local;
integer IncDec_local;
integer write_Opperand_Buffer_local;
integer InputSelect_local;
integer Write_Enable_local;
integer Load_Z_local;
integer Load_K_local;
integer Load_Jump_local;
integer relative_Absolute_local;
integer Load_Byte_local;
integer Fetch_next_instruction_local;
integer Fetch_Address_local;
integer LOAD_PCL_local;
integer LOAD_PCH_local;
integer WB_Addr_local;
integer SPM_req_local;
integer done_local;
integer state;
integer next_state;
integer i;
// initial
initial
begin
    current_state=0;
    _latched_inst=0;
    _wb_addr_val=0;
    _pointer_update_pending=0;
    _saw_resp_low=0;
    debug=1;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        current_state=0;
        done<=0;
        NotExecute<=0;
        LoadSelectMux<=0;
        LoadingMux<=0;
        Input_Select<=0;
        WE<=0;
        Read_Write<=0;
        Mem_Instruction<=0;
        IncDec<=0;
        write_Opperand_Buffer<=0;
        InputSelect<=0;
        Write_Enable<=0;
        Load_Z<=0;
        Load_K<=0;
        Load_Jump<=0;
        relative_Absolute<=0;
        Load_Byte<=0;
        Fetch_next_instruction<=0;
        Fetch_Address<=0;
        LOAD_PCL<=0;
        LOAD_PCH<=0;
        WB_Addr<=0;
        LPM_req<=0;
        SPM_req<=0;
    end
    else
    begin
        inst=Instruction;
        resp=Resp;
        executed_jump=Executed_Jump;
        address_fetched=Address_fetched;
        run_active=run;
        InputSelect_Buffer=0;
        NotExecute_local=0;
        LoadSelectMux_local=0;
        LoadingMux_local=0;
        Input_Select_local=0;
        WE_local=0;
        Read_Write_local=0;
        Mem_Instruction_local=0;
        IncDec_local=0;
        write_Opperand_Buffer_local=0;
        InputSelect_local=0;
        Write_Enable_local=0;
        Load_Z_local=0;
        Load_K_local=0;
        Load_Jump_local=0;
        relative_Absolute_local=0;
        Load_Byte_local=0;
        Fetch_next_instruction_local=0;
        Fetch_Address_local=0;
        LOAD_PCL_local=0;
        LOAD_PCH_local=0;
        WB_Addr_local=_wb_addr_val;
        SPM_req_local=0;
        done_local=0;
        state=current_state;
        next_state=state;
        if ((state==0)&&run_active)
        begin
            _latched_inst=inst;
            _pointer_update_pending=inst==122;
        end
        i=_latched_inst;
        case (state)
        0: if (run_active)
        begin
            if ((inst==120)||((inst==121)||(inst==122)))
            begin
                next_state=1;
            end
            else
            begin
                if (inst==123)
                begin
                    next_state=21;
                end
                else
                begin
                    done_local=1;
                end
            end
        end
        1: begin
        _wb_addr_val=30;
        WB_Addr_local=30;
        Mem_Instruction_local=14;
        Read_Write_local=2;
        Input_Select_local=1;
        _saw_resp_low=0;
        next_state=2;
    end
    2: begin
    WB_Addr_local=_wb_addr_val;
    Mem_Instruction_local=14;
    Read_Write_local=2;
    Input_Select_local=1;
    if (!resp)
    begin
        _saw_resp_low=1;
    end
    else
    begin
        if (_saw_resp_low)
        begin
            next_state=3;
        end
    end
end
3: begin
WE_local=1;
LoadingMux_local=5;
next_state=4;
end
4: begin
_wb_addr_val=31;
WB_Addr_local=31;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
_saw_resp_low=0;
next_state=5;
end
5: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
if (!resp)
begin
_saw_resp_low=1;
end
else
begin
if (_saw_resp_low)
begin
next_state=6;
end
end
end
6: begin
WE_local=1;
LoadingMux_local=6;
next_state=7;
end
7: next_state=8;
8: begin
Load_Z_local=1;
relative_Absolute_local=1;
next_state=9;
end
9: begin
Load_Z_local=1;
relative_Absolute_local=1;
if (executed_jump)
begin
next_state=10;
end
end
10: begin
Fetch_Address_local=1;
next_state=11;
end
11: begin
Fetch_Address_local=1;
if (address_fetched)
begin
next_state=12;
end
end
12: begin
if (i==120)
begin
Mem_Instruction_local=14;
_wb_addr_val=0;
WB_Addr_local=0;
end
else
begin
Mem_Instruction_local=12;
end
Read_Write_local=1;
Input_Select_local=5;
next_state=13;
end
13: begin
if (i==120)
begin
Mem_Instruction_local=14;
WB_Addr_local=0;
end
else
begin
Mem_Instruction_local=12;
end
Read_Write_local=1;
Input_Select_local=5;
if (resp)
begin
next_state=14;
end
end
14: begin
Load_Jump_local=1;
relative_Absolute_local=0;
LOAD_PCL_local=1;
LOAD_PCH_local=1;
next_state=15;
end
15: begin
Load_Jump_local=1;
relative_Absolute_local=0;
LOAD_PCL_local=1;
LOAD_PCH_local=1;
if (executed_jump)
begin
if (_pointer_update_pending)
begin
next_state=16;
end
else
begin
done_local=1;
next_state=0;
end
end
end
16: begin
Mem_Instruction_local=6;
IncDec_local=1;
Read_Write_local=0;
next_state=17;
end
17: begin
_wb_addr_val=30;
WB_Addr_local=30;
Mem_Instruction_local=14;
Read_Write_local=1;
Input_Select_local=10;
next_state=18;
end
18: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=1;
Input_Select_local=10;
if (resp)
begin
next_state=19;
end
end
19: begin
_wb_addr_val=31;
WB_Addr_local=31;
Mem_Instruction_local=14;
Read_Write_local=1;
Input_Select_local=11;
next_state=20;
end
20: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=1;
Input_Select_local=11;
if (resp)
begin
done_local=1;
next_state=0;
end
end
21: begin
_wb_addr_val=30;
WB_Addr_local=30;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
_saw_resp_low=0;
next_state=22;
end
22: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
if (!resp)
begin
_saw_resp_low=1;
end
else
begin
if (_saw_resp_low)
begin
next_state=23;
end
end
end
23: begin
WE_local=1;
LoadingMux_local=5;
next_state=24;
end
24: begin
_wb_addr_val=31;
WB_Addr_local=31;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
_saw_resp_low=0;
next_state=25;
end
25: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
if (!resp)
begin
_saw_resp_low=1;
end
else
begin
if (_saw_resp_low)
begin
next_state=26;
end
end
end
26: begin
WE_local=1;
LoadingMux_local=6;
next_state=27;
end
27: next_state=28;
28: begin
_wb_addr_val=0;
WB_Addr_local=0;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
_saw_resp_low=0;
next_state=29;
end
29: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
if (!resp)
begin
_saw_resp_low=1;
end
else
begin
if (_saw_resp_low)
begin
next_state=30;
end
end
end
30: begin
WE_local=1;
LoadingMux_local=15;
next_state=31;
end
31: begin
_wb_addr_val=1;
WB_Addr_local=1;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
_saw_resp_low=0;
next_state=32;
end
32: begin
WB_Addr_local=_wb_addr_val;
Mem_Instruction_local=14;
Read_Write_local=2;
Input_Select_local=1;
if (!resp)
begin
_saw_resp_low=1;
end
else
begin
if (_saw_resp_low)
begin
next_state=33;
end
end
end
33: begin
WE_local=1;
LoadingMux_local=16;
next_state=34;
end
34: next_state=35;
35: begin
SPM_req_local=1;
next_state=36;
end
36: begin
SPM_req_local=1;
if (SPM_Done==1)
begin
done_local=1;
next_state=0;
end
end
default:;
endcase
NotExecute<=NotExecute_local;
LoadSelectMux<=LoadSelectMux_local;
LoadingMux<=LoadingMux_local;
Input_Select<=Input_Select_local;
WE<=WE_local;
Read_Write<=Read_Write_local;
Mem_Instruction<=Mem_Instruction_local;
IncDec<=IncDec_local;
write_Opperand_Buffer<=write_Opperand_Buffer_local;
InputSelect<=InputSelect_local;
Write_Enable<=Write_Enable_local;
Load_Z<=Load_Z_local;
Load_K<=Load_K_local;
Load_Jump<=Load_Jump_local;
relative_Absolute<=relative_Absolute_local;
Load_Byte<=Load_Byte_local;
Fetch_next_instruction<=Fetch_next_instruction_local;
Fetch_Address<=Fetch_Address_local;
LOAD_PCL<=LOAD_PCL_local;
LOAD_PCH<=LOAD_PCH_local;
done<=done_local;
WB_Addr<=WB_Addr_local;
SPM_req<=SPM_req_local;
if ((debug==1)&&((state!=0)||run_active))
begin
/* print removed */
end
current_state=next_state;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module FSM_OutputMerger_7f9e35bfaae0 (
	input  opp_done,
	input  opp_LoadSelectMux,
	input [4:0] opp_LoadingMux,
	input [4:0] opp_Input_Select,
	input  opp_WE,
	input [1:0] opp_Read_Write,
	input [4:0] opp_Mem_Instruction,
	input [2:0] opp_IncDec,
	input [2:0] opp_write_Opperand_Buffer,
	input  opp_InputSelect,
	input  opp_Load_Z,
	input  opp_Load_K,
	input  opp_Load_Jump,
	input  opp_relative_Absolute,
	input  opp_Load_Byte,
	input  opp_Fetch_Address,
	input [7:0] opp_WB_Addr,
	input  opp_LOAD_PCL,
	input  opp_LOAD_PCH,
	input [1:0] opp_K_Select,
	input  mov_done,
	input  mov_LoadSelectMux,
	input [4:0] mov_LoadingMux,
	input [4:0] mov_Input_Select,
	input  mov_WE,
	input [1:0] mov_Read_Write,
	input [4:0] mov_Mem_Instruction,
	input [2:0] mov_IncDec,
	input [2:0] mov_write_Opperand_Buffer,
	input  mov_InputSelect,
	input  mov_Load_Z,
	input  mov_Load_K,
	input  mov_Load_Jump,
	input  mov_relative_Absolute,
	input  mov_Load_Byte,
	input  mov_Fetch_Address,
	input [7:0] mov_WB_Addr,
	input  mov_LOAD_PCL,
	input  mov_LOAD_PCH,
	input  poppush_done,
	input  poppush_LoadSelectMux,
	input [4:0] poppush_LoadingMux,
	input [4:0] poppush_Input_Select,
	input  poppush_WE,
	input [1:0] poppush_Read_Write,
	input [4:0] poppush_Mem_Instruction,
	input [2:0] poppush_IncDec,
	input [2:0] poppush_write_Opperand_Buffer,
	input  poppush_InputSelect,
	input  poppush_Load_Z,
	input  poppush_Load_K,
	input  poppush_Load_Jump,
	input  poppush_relative_Absolute,
	input  poppush_Load_Byte,
	input  poppush_Fetch_Address,
	input [7:0] poppush_WB_Addr,
	input  poppush_LOAD_PCL,
	input  poppush_LOAD_PCH,
	input  ldst_done,
	input  ldst_LoadSelectMux,
	input [4:0] ldst_LoadingMux,
	input [4:0] ldst_Input_Select,
	input  ldst_WE,
	input [1:0] ldst_Read_Write,
	input [4:0] ldst_Mem_Instruction,
	input [2:0] ldst_IncDec,
	input [2:0] ldst_write_Opperand_Buffer,
	input  ldst_InputSelect,
	input  ldst_Load_Z,
	input  ldst_Load_K,
	input  ldst_Load_Jump,
	input  ldst_relative_Absolute,
	input  ldst_Load_Byte,
	input  ldst_Fetch_Address,
	input [7:0] ldst_WB_Addr,
	input  ldst_LOAD_PCL,
	input  ldst_LOAD_PCH,
	input  callret_done,
	input  callret_LoadSelectMux,
	input [4:0] callret_LoadingMux,
	input [4:0] callret_Input_Select,
	input  callret_WE,
	input [1:0] callret_Read_Write,
	input [4:0] callret_Mem_Instruction,
	input [2:0] callret_IncDec,
	input [2:0] callret_write_Opperand_Buffer,
	input  callret_InputSelect,
	input  callret_Load_Z,
	input  callret_Load_K,
	input  callret_Load_Jump,
	input  callret_relative_Absolute,
	input  callret_Load_Byte,
	input  callret_Fetch_Address,
	input [7:0] callret_WB_Addr,
	input  callret_LOAD_PCL,
	input  callret_LOAD_PCH,
	input [1:0] callret_K_Select,
	input  lpm_done,
	input  lpm_LoadSelectMux,
	input [4:0] lpm_LoadingMux,
	input [4:0] lpm_Input_Select,
	input  lpm_WE,
	input [1:0] lpm_Read_Write,
	input [4:0] lpm_Mem_Instruction,
	input [2:0] lpm_IncDec,
	input [2:0] lpm_write_Opperand_Buffer,
	input  lpm_InputSelect,
	input  lpm_Load_Z,
	input  lpm_Load_K,
	input  lpm_Load_Jump,
	input  lpm_relative_Absolute,
	input  lpm_Load_Byte,
	input  lpm_Fetch_Address,
	input [7:0] lpm_WB_Addr,
	input  lpm_LOAD_PCL,
	input  lpm_LOAD_PCH,
	input  lpm_LPM_req,
	input  lpm_SPM_req,
	output  reg  out_done,
	output  reg [2:0] out_LoadSelectMux,
	output  reg [4:0] out_LoadingMux,
	output  reg [4:0] out_Input_Select,
	output  reg [5:0] out_WE,
	output  reg [1:0] out_Read_Write,
	output  reg [4:0] out_Mem_Instruction,
	output  reg [2:0] out_IncDec,
	output  reg [3:0] out_write_Opperand_Buffer,
	output  reg  out_InputSelect,
	output  reg  out_Load_Z,
	output  reg  out_Load_K,
	output  reg  out_Load_Jump,
	output  reg  out_relative_Absolute,
	output  reg  out_Load_Byte,
	output  reg  out_Fetch_Address,
	output  reg [7:0] out_WB_Addr,
	output  reg  out_LOAD_PCL,
	output  reg  out_LOAD_PCH,
	output  reg [1:0] out_K_Select,
	output  reg [1:0] out_LPM_req,
	output  reg [1:0] out_SPM_req);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    out_done<=((((opp_done|mov_done)|poppush_done)|ldst_done)|callret_done)|lpm_done;
    out_LoadSelectMux<=((((opp_LoadSelectMux|mov_LoadSelectMux)|poppush_LoadSelectMux)|ldst_LoadSelectMux)|callret_LoadSelectMux)|lpm_LoadSelectMux;
    out_LoadingMux<=((((opp_LoadingMux|mov_LoadingMux)|poppush_LoadingMux)|ldst_LoadingMux)|callret_LoadingMux)|lpm_LoadingMux;
    out_Input_Select<=((((opp_Input_Select|mov_Input_Select)|poppush_Input_Select)|ldst_Input_Select)|callret_Input_Select)|lpm_Input_Select;
    out_WE<=((((opp_WE|mov_WE)|poppush_WE)|ldst_WE)|callret_WE)|lpm_WE;
    out_Read_Write<=((((opp_Read_Write|mov_Read_Write)|poppush_Read_Write)|ldst_Read_Write)|callret_Read_Write)|lpm_Read_Write;
    out_Mem_Instruction<=((((opp_Mem_Instruction|mov_Mem_Instruction)|poppush_Mem_Instruction)|ldst_Mem_Instruction)|callret_Mem_Instruction)|lpm_Mem_Instruction;
    out_IncDec<=((((opp_IncDec|mov_IncDec)|poppush_IncDec)|ldst_IncDec)|callret_IncDec)|lpm_IncDec;
    out_write_Opperand_Buffer<=((((opp_write_Opperand_Buffer|mov_write_Opperand_Buffer)|poppush_write_Opperand_Buffer)|ldst_write_Opperand_Buffer)|callret_write_Opperand_Buffer)|lpm_write_Opperand_Buffer;
    out_InputSelect<=((((opp_InputSelect|mov_InputSelect)|poppush_InputSelect)|ldst_InputSelect)|callret_InputSelect)|lpm_InputSelect;
    out_Load_Z<=((((opp_Load_Z|mov_Load_Z)|poppush_Load_Z)|ldst_Load_Z)|callret_Load_Z)|lpm_Load_Z;
    out_Load_K<=((((opp_Load_K|mov_Load_K)|poppush_Load_K)|ldst_Load_K)|callret_Load_K)|lpm_Load_K;
    out_Load_Jump<=((((opp_Load_Jump|mov_Load_Jump)|poppush_Load_Jump)|ldst_Load_Jump)|callret_Load_Jump)|lpm_Load_Jump;
    out_relative_Absolute<=((((opp_relative_Absolute|mov_relative_Absolute)|poppush_relative_Absolute)|ldst_relative_Absolute)|callret_relative_Absolute)|lpm_relative_Absolute;
    out_Load_Byte<=((((opp_Load_Byte|mov_Load_Byte)|poppush_Load_Byte)|ldst_Load_Byte)|callret_Load_Byte)|lpm_Load_Byte;
    out_Fetch_Address<=((((opp_Fetch_Address|mov_Fetch_Address)|poppush_Fetch_Address)|ldst_Fetch_Address)|callret_Fetch_Address)|lpm_Fetch_Address;
    out_WB_Addr<=((((opp_WB_Addr|mov_WB_Addr)|poppush_WB_Addr)|ldst_WB_Addr)|callret_WB_Addr)|lpm_WB_Addr;
    out_LOAD_PCL<=((((opp_LOAD_PCL|mov_LOAD_PCL)|poppush_LOAD_PCL)|ldst_LOAD_PCL)|callret_LOAD_PCL)|lpm_LOAD_PCL;
    out_LOAD_PCH<=((((opp_LOAD_PCH|mov_LOAD_PCH)|poppush_LOAD_PCH)|ldst_LOAD_PCH)|callret_LOAD_PCH)|lpm_LOAD_PCH;
    out_K_Select<=opp_K_Select|callret_K_Select;
    out_LPM_req<=lpm_LPM_req;
    out_SPM_req<=lpm_SPM_req;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module InterruptFSM_7f9e35bfdfd0 (
	input clk,
	input  Run,
	input [15:0] Instruction,
	input  Entrance,
	input  Resp,
	input  reset,
	output  reg  Done,
	output  reg [1:0] Read_Write,
	output  reg [4:0] Mem_Instruction,
	output  reg [4:0] InputSelectMemory,
	output  reg [2:0] IncDec,
	output  reg  LOAD_PCL,
	output  reg  LOAD_PCH,
	output  reg  Interrupt_Done,
	output  reg  I_Force_WE,
	output  reg  I_Force_Value);
// Code generated from clock method
// wire/variable declaration
integer current_state;
integer debug;
integer _reti_h_saw_resp_low;
integer _prev_entrance;
integer run;
integer instruction;
integer entrance;
integer resp;
integer Read_Write_local;
integer Mem_Instruction_local;
integer InputSelectMemory_local;
integer IncDec_local;
integer LOAD_PCL_local;
integer LOAD_PCH_local;
integer Done_local;
integer Interrupt_Done_local;
integer I_Force_WE_local;
integer I_Force_Value_local;
integer state;
integer next_state;
integer entrance_rising_edge;
// initial
initial
begin
    current_state=0;
    debug=1;
    _reti_h_saw_resp_low=0;
    _prev_entrance=0;
end
// process
always @(posedge clk)
begin
    if (reset)
    begin
        _prev_entrance=0;
        _reti_h_saw_resp_low=0;
        current_state=0;
        Done<=0;
        Read_Write<=0;
        Mem_Instruction<=0;
        InputSelectMemory<=0;
        IncDec<=0;
        LOAD_PCL<=0;
        LOAD_PCH<=0;
        Interrupt_Done<=0;
        I_Force_WE<=0;
        I_Force_Value<=0;
    end
    else
    begin
        run=Run;
        instruction=Instruction;
        entrance=Entrance;
        resp=Resp;
        Read_Write_local=0;
        Mem_Instruction_local=0;
        InputSelectMemory_local=0;
        IncDec_local=0;
        LOAD_PCL_local=0;
        LOAD_PCH_local=0;
        Done_local=0;
        Interrupt_Done_local=0;
        I_Force_WE_local=0;
        I_Force_Value_local=0;
        state=current_state;
        next_state=state;
        if ((state==1)||((state==2)||((state==4)||((state==5)||((state==6)||((state==7)||((state==8)||((state==9)||((state==10)||((state==11)||((state==12)||((state==13)||((state==14)||((state==15)||((state==16)||(state==17))))))))))))))))
        begin
            I_Force_WE_local=1;
            I_Force_Value_local=0;
        end
        entrance_rising_edge=(entrance==1)&&(_prev_entrance==0);
        _prev_entrance=entrance;
        case (state)
        0: if (entrance_rising_edge)
        begin
            next_state=1;
        end
        else
        begin
            if ((run==1)&&(instruction==36))
            begin
                next_state=3;
            end
        end
        1: begin
        I_Force_WE_local=1;
        I_Force_Value_local=0;
        next_state=2;
    end
    2: begin
    Read_Write_local=1;
    Mem_Instruction_local=7;
    InputSelectMemory_local=15;
    IncDec_local=3;
    next_state=4;
end
4: begin
Read_Write_local=1;
Mem_Instruction_local=7;
InputSelectMemory_local=15;
if (resp==1)
begin
    next_state=5;
end
end
5: next_state=6;
6: begin
Read_Write_local=1;
Mem_Instruction_local=7;
InputSelectMemory_local=14;
IncDec_local=3;
next_state=7;
end
7: begin
Read_Write_local=1;
Mem_Instruction_local=7;
InputSelectMemory_local=14;
if (resp==1)
begin
next_state=8;
end
end
8: next_state=9;
9: begin
Read_Write_local=2;
Mem_Instruction_local=19;
next_state=10;
end
10: begin
Read_Write_local=2;
Mem_Instruction_local=19;
if (resp==1)
begin
next_state=11;
end
end
11: begin
Read_Write_local=2;
Mem_Instruction_local=19;
next_state=12;
end
12: begin
Read_Write_local=2;
Mem_Instruction_local=19;
LOAD_PCL_local=1;
next_state=13;
end
13: begin
Read_Write_local=2;
Mem_Instruction_local=20;
next_state=14;
end
14: begin
Read_Write_local=2;
Mem_Instruction_local=20;
if (resp==1)
begin
next_state=15;
end
end
15: begin
Read_Write_local=2;
Mem_Instruction_local=20;
next_state=16;
end
16: begin
Read_Write_local=2;
Mem_Instruction_local=20;
LOAD_PCH_local=1;
next_state=17;
end
17: begin
Interrupt_Done_local=1;
next_state=0;
end
3: begin
Read_Write_local=2;
Mem_Instruction_local=7;
IncDec_local=4;
next_state=18;
end
18: begin
Read_Write_local=2;
Mem_Instruction_local=7;
if (resp==1)
begin
next_state=19;
end
end
19: next_state=20;
20: begin
LOAD_PCL_local=1;
next_state=21;
end
21: begin
Read_Write_local=2;
Mem_Instruction_local=7;
IncDec_local=4;
_reti_h_saw_resp_low=0;
next_state=22;
end
22: begin
Read_Write_local=2;
Mem_Instruction_local=7;
if (!resp)
begin
_reti_h_saw_resp_low=1;
end
else
begin
if (_reti_h_saw_resp_low)
begin
next_state=23;
end
end
end
23: next_state=24;
24: begin
LOAD_PCH_local=1;
next_state=25;
end
25: begin
I_Force_WE_local=1;
I_Force_Value_local=1;
Done_local=1;
next_state=0;
end
default:;
endcase
if (debug&&(current_state!=0))
begin
/* print removed */
end
current_state=next_state;
Read_Write<=Read_Write_local;
Mem_Instruction<=Mem_Instruction_local;
InputSelectMemory<=InputSelectMemory_local;
IncDec<=IncDec_local;
LOAD_PCL<=LOAD_PCL_local;
LOAD_PCH<=LOAD_PCH_local;
Done<=Done_local;
Interrupt_Done<=Interrupt_Done_local;
I_Force_WE<=I_Force_WE_local;
I_Force_Value<=I_Force_Value_local;
end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module _InterruptBusMerge_7f9e35bfe570 (
	input  ib_done,
	input [1:0] ib_read_write,
	input [4:0] ib_mem_instr,
	input [4:0] ib_input_select_mem,
	input [2:0] ib_incdec,
	input  ib_load_pcl,
	input  ib_load_pch,
	input  irq_done,
	input [1:0] irq_read_write,
	input [4:0] irq_mem_instr,
	input [4:0] irq_input_select_mem,
	input [2:0] irq_incdec,
	input  irq_load_pcl,
	input  irq_load_pch,
	output  reg  out_done,
	output  reg [1:0] out_read_write,
	output  reg [4:0] out_mem_instr,
	output  reg [4:0] out_input_select_mem,
	output  reg [2:0] out_incdec,
	output  reg  out_load_pcl,
	output  reg  out_load_pch);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    out_done<=ib_done|irq_done;
    out_read_write<=ib_read_write|irq_read_write;
    out_mem_instr<=ib_mem_instr|irq_mem_instr;
    out_input_select_mem<=ib_input_select_mem|irq_input_select_mem;
    out_incdec<=ib_incdec|irq_incdec;
    out_load_pcl<=ib_load_pcl|irq_load_pcl;
    out_load_pch<=ib_load_pch|irq_load_pch;
end
endmodule
