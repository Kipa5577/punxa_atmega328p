// This file was automatically created by py4hw Verilog generator
module ALU (
	input [7:0] ImputRegA0,
	input [7:0] ImputRegA1,
	input [7:0] ImputRegB0,
	input [7:0] ImputRegB1,
	input [7:0] ALUInstruction,
	input [7:0] SREG_STATE,
	input [2:0] BitPos,
	input [7:0] IOreg,
	output [7:0] ALUOUTPUTByte0,
	output [7:0] ALUOUTPUTByte1,
	output [7:0] SREG_VAL,
	output [7:0] eSREG_VAL,
	output  BRANCH,
	output  SKIP);
wire [2:0] w_w_nopp;
wire w_w_zout;
wire [3:0] w_w_vopp;
wire w_w_vout;
wire [2:0] w_w_sopp;
wire w_w_sout;
wire [1:0] w_w_hopp;
wire w_w_hout;
wire [1:0] w_w_topp;
wire w_w_tout;
wire w_w_iopp;
wire w_w_iout;
wire [15:0] w_w_regA_16;
wire [2:0] w_w_branchOpp;
wire [7:0] w_w_res_l;
wire [15:0] w_w_regB_16;
wire [7:0] w_w_res_H;
wire [15:0] w_w_res_16;
wire w_w_mul_carry;
wire w_w_cin;
wire w_w_zin;
wire w_w_nin;
wire w_w_vin;
wire [7:0] w_w_arith_ctrl;
wire [3:0] w_w_copp;
wire w_w_cout;
wire [2:0] w_w_zopp;
wire w_w_nout;

SREG_Splitter_7fd117274490 i_SREGSplitter(.SREG_STATE(SREG_STATE),.w_cin(w_w_cin),.w_zin(w_w_zin),.w_nin(w_w_nin),.w_vin(w_w_vin));
WireCombiner16_7fd1172744d0 i_ConcatA(.in_high(ImputRegA1),.in_low(ImputRegA0),.out_16(w_w_regA_16));
WireCombiner16_7fd117274990 i_ConcatB(.in_high(ImputRegB1),.in_low(ImputRegB0),.out_16(w_w_regB_16));
WireCombiner16_7fd117274bd0 i_ConcatRes(.in_high(w_w_res_H),.in_low(w_w_res_l),.out_16(w_w_res_16));
ALU_ConfCodeCalc_7fd117274e10 i_ConfCodeCalc(.ALUInstruction(ALUInstruction),.BitPos(BitPos),.ArithmeticControl(w_w_arith_ctrl),.Copp(w_w_copp),.Zopp(w_w_zopp),.Nopp(w_w_nopp),.Vopp(w_w_vopp),.Sopp(w_w_sopp),.Hopp(w_w_hopp),.Topp(w_w_topp),.Iopp(w_w_iopp),.eSREG(eSREG_VAL),.BranchOpp(w_w_branchOpp));
AU_7fd117275350 i_AU(.Cval(w_w_cin),.RegAL(ImputRegA0),.RegAH(ImputRegA1),.RegBL(ImputRegB0),.RegBH(ImputRegB1),.Operation(w_w_arith_ctrl),.BitPos(BitPos),.ResL(w_w_res_l),.ResH(w_w_res_H),.MulCarryOut(w_w_mul_carry));
BranchUnit_7fd1172757d0 i_LU(.SREG(SREG_STATE),.RegisterToTest(ImputRegA0),.RegisterB(ImputRegB0),.IORegisterToTest(IOreg),.Bit(BitPos),.Operation(w_w_branchOpp),.Skip(SKIP),.Branch(BRANCH));
HandleC_7fd117275b90 i_HC(.Rr(w_w_regB_16),.Rd(w_w_regA_16),.Res(w_w_res_16),.Mode(w_w_copp),.MulCarry(w_w_mul_carry),.Cout(w_w_cout));
HandleZ_7fd117275ed0 i_HZ(.Res(w_w_res_16),.Mode(w_w_zopp),.Zprev(w_w_zin),.Zout(w_w_zout));
HandleN_7fd117275f10 i_HN(.Res(w_w_res_16),.Mode(w_w_nopp),.Nout(w_w_nout));
HandleV_7fd117276410 i_HV(.Rr(w_w_regB_16),.Rd(w_w_regA_16),.Res(w_w_res_16),.N(w_w_nin),.Mode(w_w_vopp),.C(w_w_cin),.Vout(w_w_vout));
HandleH_7fd117276790 i_HH(.Rr(w_w_regB_16),.Rd(w_w_regA_16),.Res(w_w_res_16),.Mode(w_w_hopp),.Hout(w_w_hout));
HandleT_7fd1172767d0 i_HT(.Rr(w_w_regA_16),.BitPos(BitPos),.Mode(w_w_topp),.Tout(w_w_tout));
HandleI_7fd117276b50 i_HI(.Mode(w_w_iopp),.Iout(w_w_iout));
HandleS_7fd117277090 i_HS(.N(w_w_nout),.V(w_w_vout),.Mode(w_w_sopp),.Sout(w_w_sout));
ALU_MergerAndLogic_7fd1172770d0 i_ALUMerger(.w_cout(w_w_cout),.w_zout(w_w_zout),.w_nout(w_w_nout),.w_vout(w_w_vout),.w_sout(w_w_sout),.w_hout(w_w_hout),.w_tout(w_w_tout),.w_iout(w_w_iout),.w_res_l(w_w_res_l),.w_res_h(w_w_res_H),.sreg_val(SREG_VAL),.out_byte0(ALUOUTPUTByte0),.out_byte1(ALUOUTPUTByte1));
endmodule

// This file was automatically created by py4hw Verilog generator
module SREG_Splitter_7fd117274490 (
	input [7:0] SREG_STATE,
	output  reg  w_cin,
	output  reg  w_zin,
	output  reg  w_nin,
	output  reg  w_vin);
// Code generated from propagate method
// wire/variable declaration
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
end
endmodule

// This file was automatically created by py4hw Verilog generator
module WireCombiner16_7fd1172744d0 (
	input [7:0] in_high,
	input [7:0] in_low,
	output  reg [15:0] out_16);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    val_high=in_high&255;
    val_low=in_low&255;
    combined=(val_high<<8)|val_low;
    out_16<=combined;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module WireCombiner16_7fd117274990 (
	input [7:0] in_high,
	input [7:0] in_low,
	output  reg [15:0] out_16);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    val_high=in_high&255;
    val_low=in_low&255;
    combined=(val_high<<8)|val_low;
    out_16<=combined;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module WireCombiner16_7fd117274bd0 (
	input [7:0] in_high,
	input [7:0] in_low,
	output  reg [15:0] out_16);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    val_high=in_high&255;
    val_low=in_low&255;
    combined=(val_high<<8)|val_low;
    out_16<=combined;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module ALU_ConfCodeCalc_7fd117274e10 (
	input [7:0] ALUInstruction,
	input [2:0] BitPos,
	output  reg [7:0] ArithmeticControl,
	output  reg [3:0] Copp,
	output  reg [2:0] Zopp,
	output  reg [2:0] Nopp,
	output  reg [3:0] Vopp,
	output  reg [2:0] Sopp,
	output  reg [1:0] Hopp,
	output  reg [1:0] Topp,
	output  reg  Iopp,
	output  reg [7:0] eSREG,
	output  reg [2:0] BranchOpp);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    inst=ALUInstruction;
    bit_pos=BitPos;
    arith_ctrl=inst;
    ien=0;
    ten=0;
    hen=0;
    sen=0;
    ven=0;
    nen=0;
    zen=0;
    cen=0;
    copp=0;
    zopp=0;
    nopp=0;
    vopp=0;
    sopp=0;
    hopp=0;
    topp=0;
    iopp=0;
    branch_opp=0;
    Z_MODE_8BIT=2;
    Z_MODE_16BIT=3;
    Z_MODE_CHAIN=5;
    N_MODE_8BIT=2;
    N_MODE_16BIT=3;
    S_MODE_XOR=2;
    if ((inst==1)||(inst==2))
    begin
        hen=1;
        sen=1;
        ven=1;
        nen=1;
        zen=1;
        cen=1;
        hopp=2;
        vopp=2;
        copp=2;
        sopp=S_MODE_XOR;
        zopp=Z_MODE_8BIT;
        nopp=N_MODE_8BIT;
    end
    else
    begin
        if ((((inst==4)||(inst==5))||((inst==6)||(inst==7)))||(((inst==38)||(inst==39))||(inst==40)))
        begin
            hen=1;
            sen=1;
            ven=1;
            nen=1;
            zen=1;
            cen=1;
            hopp=3;
            vopp=3;
            copp=3;
            sopp=S_MODE_XOR;
            nopp=N_MODE_8BIT;
            if (((inst==6)||(inst==7))||(inst==39))
            begin
                zopp=Z_MODE_CHAIN;
            end
            else
            begin
                zopp=Z_MODE_8BIT;
            end
        end
        else
        begin
            if (inst==3)
            begin
                sen=1;
                ven=1;
                nen=1;
                zen=1;
                cen=1;
                hen=0;
                hopp=0;
                vopp=4;
                copp=4;
                sopp=S_MODE_XOR;
                zopp=Z_MODE_16BIT;
                nopp=N_MODE_16BIT;
            end
            else
            begin
                if (inst==8)
                begin
                    sen=1;
                    ven=1;
                    nen=1;
                    zen=1;
                    cen=1;
                    hen=0;
                    hopp=0;
                    vopp=5;
                    copp=5;
                    sopp=S_MODE_XOR;
                    zopp=Z_MODE_16BIT;
                    nopp=N_MODE_16BIT;
                end
                else
                begin
                    if (((((inst==9)||(inst==10))||((inst==11)||(inst==12)))||(((inst==13)||(inst==16))||((inst==17)||(inst==20))))||(inst==21))
                    begin
                        sen=1;
                        ven=1;
                        nen=1;
                        zen=1;
                        cen=0;
                        hen=0;
                        vopp=0;
                        sopp=S_MODE_XOR;
                        zopp=Z_MODE_8BIT;
                        nopp=N_MODE_8BIT;
                    end
                    else
                    begin
                        if (inst==14)
                        begin
                            sen=1;
                            ven=1;
                            nen=1;
                            zen=1;
                            cen=1;
                            hen=0;
                            vopp=0;
                            copp=6;
                            sopp=S_MODE_XOR;
                            zopp=Z_MODE_8BIT;
                            nopp=N_MODE_8BIT;
                        end
                        else
                        begin
                            if (inst==15)
                            begin
                                hen=1;
                                sen=1;
                                ven=1;
                                nen=1;
                                zen=1;
                                cen=1;
                                hopp=3;
                                vopp=5;
                                copp=7;
                                sopp=S_MODE_XOR;
                                zopp=Z_MODE_8BIT;
                                nopp=N_MODE_8BIT;
                            end
                            else
                            begin
                                if (inst==18)
                                begin
                                    sen=1;
                                    ven=1;
                                    nen=1;
                                    zen=1;
                                    cen=0;
                                    hen=0;
                                    vopp=6;
                                    sopp=S_MODE_XOR;
                                    zopp=Z_MODE_8BIT;
                                    nopp=N_MODE_8BIT;
                                end
                                else
                                begin
                                    if (inst==19)
                                    begin
                                        sen=1;
                                        ven=1;
                                        nen=1;
                                        zen=1;
                                        cen=0;
                                        hen=0;
                                        vopp=7;
                                        sopp=S_MODE_XOR;
                                        zopp=Z_MODE_8BIT;
                                        nopp=N_MODE_8BIT;
                                    end
                                    else
                                    begin
                                        if (inst==22)
                                        begin
                                            zopp=zopp;
                                        end
                                        else
                                        begin
                                            if ((((inst==67)||(inst==68))||((inst==69)||(inst==70)))||(inst==71))
                                            begin
                                                cen=1;
                                                zen=1;
                                                nen=1;
                                                ven=1;
                                                sen=1;
                                                hen=0;
                                                zopp=Z_MODE_8BIT;
                                                sopp=S_MODE_XOR;
                                                vopp=8;
                                                if ((inst==67)||(inst==69))
                                                begin
                                                    copp=10;
                                                    nopp=N_MODE_8BIT;
                                                end
                                                else
                                                begin
                                                    if (inst==68)
                                                    begin
                                                        copp=9;
                                                        nopp=0;
                                                    end
                                                    else
                                                    begin
                                                        copp=9;
                                                        nopp=N_MODE_8BIT;
                                                    end
                                                end
                                            end
                                            else
                                            begin
                                                if ((((inst==23)||(inst==24))||((inst==25)||(inst==26)))||((inst==27)||(inst==28)))
                                                begin
                                                    zen=1;
                                                    cen=1;
                                                    nen=0;
                                                    ven=0;
                                                    sen=0;
                                                    hen=0;
                                                    copp=8;
                                                    zopp=Z_MODE_16BIT;
                                                end
                                                else
                                                begin
                                                    if (inst==73)
                                                    begin
                                                        if (bit_pos==0)
                                                        begin
                                                            cen=1;
                                                        end
                                                        else
                                                        begin
                                                            cen=0;
                                                        end
                                                        if (bit_pos==1)
                                                        begin
                                                            zen=1;
                                                        end
                                                        else
                                                        begin
                                                            zen=0;
                                                        end
                                                        if (bit_pos==2)
                                                        begin
                                                            nen=1;
                                                        end
                                                        else
                                                        begin
                                                            nen=0;
                                                        end
                                                        if (bit_pos==3)
                                                        begin
                                                            ven=1;
                                                        end
                                                        else
                                                        begin
                                                            ven=0;
                                                        end
                                                        if (bit_pos==4)
                                                        begin
                                                            sen=1;
                                                        end
                                                        else
                                                        begin
                                                            sen=0;
                                                        end
                                                        if (bit_pos==5)
                                                        begin
                                                            hen=1;
                                                        end
                                                        else
                                                        begin
                                                            hen=0;
                                                        end
                                                        if (bit_pos==6)
                                                        begin
                                                            ten=1;
                                                        end
                                                        else
                                                        begin
                                                            ten=0;
                                                        end
                                                        if (bit_pos==7)
                                                        begin
                                                            ien=1;
                                                        end
                                                        else
                                                        begin
                                                            ien=0;
                                                        end
                                                        iopp=1;
                                                        topp=1;
                                                        hopp=1;
                                                        sopp=1;
                                                        vopp=1;
                                                        nopp=1;
                                                        zopp=1;
                                                        copp=1;
                                                    end
                                                    else
                                                    begin
                                                        if (inst==74)
                                                        begin
                                                            if (bit_pos==0)
                                                            begin
                                                                cen=1;
                                                            end
                                                            else
                                                            begin
                                                                cen=0;
                                                            end
                                                            if (bit_pos==1)
                                                            begin
                                                                zen=1;
                                                            end
                                                            else
                                                            begin
                                                                zen=0;
                                                            end
                                                            if (bit_pos==2)
                                                            begin
                                                                nen=1;
                                                            end
                                                            else
                                                            begin
                                                                nen=0;
                                                            end
                                                            if (bit_pos==3)
                                                            begin
                                                                ven=1;
                                                            end
                                                            else
                                                            begin
                                                                ven=0;
                                                            end
                                                            if (bit_pos==4)
                                                            begin
                                                                sen=1;
                                                            end
                                                            else
                                                            begin
                                                                sen=0;
                                                            end
                                                            if (bit_pos==5)
                                                            begin
                                                                hen=1;
                                                            end
                                                            else
                                                            begin
                                                                hen=0;
                                                            end
                                                            if (bit_pos==6)
                                                            begin
                                                                ten=1;
                                                            end
                                                            else
                                                            begin
                                                                ten=0;
                                                            end
                                                            if (bit_pos==7)
                                                            begin
                                                                ien=1;
                                                            end
                                                            else
                                                            begin
                                                                ien=0;
                                                            end
                                                            iopp=0;
                                                            topp=0;
                                                            hopp=0;
                                                            sopp=0;
                                                            vopp=0;
                                                            nopp=0;
                                                            zopp=0;
                                                            copp=0;
                                                        end
                                                        else
                                                        begin
                                                            if (((((inst==45)||(inst==49))||((inst==47)||(inst==53)))||(((inst==61)||(inst==55))||((inst==57)||(inst==59))))||(inst==63))
                                                            begin
                                                                branch_opp=1;
                                                            end
                                                            else
                                                            begin
                                                                if (((((inst==46)||(inst==50))||((inst==51)||(inst==52)))||(((inst==48)||(inst==54))||((inst==62)||(inst==56))))||(((inst==58)||(inst==60))||(inst==64)))
                                                                begin
                                                                    branch_opp=2;
                                                                end
                                                                else
                                                                begin
                                                                    if (inst==41)
                                                                    begin
                                                                        branch_opp=3;
                                                                    end
                                                                    else
                                                                    begin
                                                                        if (inst==42)
                                                                        begin
                                                                            branch_opp=4;
                                                                        end
                                                                        else
                                                                        begin
                                                                            if (inst==43)
                                                                            begin
                                                                                branch_opp=5;
                                                                            end
                                                                            else
                                                                            begin
                                                                                if (inst==44)
                                                                                begin
                                                                                    branch_opp=6;
                                                                                end
                                                                                else
                                                                                begin
                                                                                    if (inst==37)
                                                                                    begin
                                                                                        branch_opp=7;
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
    esreg_val=(((((((ien<<7)|(ten<<6))|(hen<<5))|(sen<<4))|(ven<<3))|(nen<<2))|(zen<<1))|cen;
    if ((((((inst==37)||(inst==41))||((inst==42)||(inst==43)))||(((inst==44)||(inst==45))||((inst==46)||(inst==47))))||((((inst==48)||(inst==49))||((inst==50)||(inst==51)))||(((inst==52)||(inst==53))||((inst==54)||(inst==55)))))||(((((inst==56)||(inst==57))||((inst==58)||(inst==59)))||(((inst==60)||(inst==61))||((inst==62)||(inst==63))))||(inst==64)))
    begin
        arith_ctrl=0;
    end
    ArithmeticControl<=arith_ctrl;
    Copp<=copp;
    Zopp<=zopp;
    Nopp<=nopp;
    Vopp<=vopp;
    Sopp<=sopp;
    Hopp<=hopp;
    Topp<=topp;
    Iopp<=iopp;
    eSREG<=esreg_val;
    BranchOpp<=branch_opp;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module AU_7fd117275350 (
	input  Cval,
	input [7:0] RegAL,
	input [7:0] RegAH,
	input [7:0] RegBL,
	input [7:0] RegBH,
	input [7:0] Operation,
	input [2:0] BitPos,
	output  reg [7:0] ResL,
	output  reg [7:0] ResH,
	output  reg  MulCarryOut);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    op=Operation;
    A=RegAL;
    B=RegBL;
    C=Cval;
    bit_pos=BitPos&7;
    word_A=A|(RegAH<<8);
    word_B=B|(RegBH<<8);
    res_l=0;
    res_h=0;
    if (op==0)
    begin
        res_l=0;
    end
    else
    begin
        if (op==1)
        begin
            res_l=A+B;
        end
        else
        begin
            if (op==2)
            begin
                res_l=(A+B)+C;
            end
            else
            begin
                if (((op==4)||(op==5))||((op==38)||(op==40)))
                begin
                    res_l=A-B;
                end
                else
                begin
                    if (((op==6)||(op==7))||(op==39))
                    begin
                        res_l=(A-B)-C;
                    end
                    else
                    begin
                        if (op==3)
                        begin
                            res16=word_A+word_B;
                            res_l=res16&255;
                            res_h=(res16>>8)&255;
                        end
                        else
                        begin
                            if (op==8)
                            begin
                                res16=word_A-word_B;
                                res_l=res16&255;
                                res_h=(res16>>8)&255;
                            end
                            else
                            begin
                                if (((op==9)||(op==10))||(op==20))
                                begin
                                    res_l=A&B;
                                end
                                else
                                begin
                                    if (((op==11)||(op==12))||(op==16))
                                    begin
                                        res_l=A|B;
                                    end
                                    else
                                    begin
                                        if ((op==13)||(op==21))
                                        begin
                                            res_l=A^B;
                                        end
                                        else
                                        begin
                                            if (op==14)
                                            begin
                                                res_l=255-A;
                                            end
                                            else
                                            begin
                                                if (op==15)
                                                begin
                                                    res_l=0-A;
                                                end
                                                else
                                                begin
                                                    if (op==17)
                                                    begin
                                                        res_l=A&(255-B);
                                                    end
                                                    else
                                                    begin
                                                        if (op==18)
                                                        begin
                                                            res_l=A+1;
                                                        end
                                                        else
                                                        begin
                                                            if (op==19)
                                                            begin
                                                                res_l=A-1;
                                                            end
                                                            else
                                                            begin
                                                                if (op==22)
                                                                begin
                                                                    res_l=255;
                                                                end
                                                                else
                                                                begin
                                                                    if (op==93)
                                                                    begin
                                                                        res_l=B;
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
    mul_carry=0;
    if ((((op==23)||(op==24))||((op==25)||(op==26)))||((op==27)||(op==28)))
    begin
        if ((op==24)||(op==27))
        begin
            if (A<128)
            begin
                val_A=A;
            end
            else
            begin
                val_A=A-256;
            end
            if (B<128)
            begin
                val_B=B;
            end
            else
            begin
                val_B=B-256;
            end
        end
        else
        begin
            if ((op==25)||(op==28))
            begin
                if (A<128)
                begin
                    val_A=A;
                end
                else
                begin
                    val_A=A-256;
                end
                val_B=B;
            end
            else
            begin
                val_A=A;
                val_B=B;
            end
        end
        raw=(val_A*val_B)&65535;
        mul_carry=(raw>>15)&1;
        if (((op==26)||(op==27))||(op==28))
        begin
            res16=(raw<<1)&65535;
        end
        else
        begin
            res16=raw;
        end
        res_l=res16&255;
        res_h=(res16>>8)&255;
    end
    else
    begin
        if ((op==73)||(op==74))
        begin
            res_l=0;
        end
        else
        begin
            if (op==65)
            begin
                res_l=A|(1<<bit_pos);
            end
            else
            begin
                if (op==66)
                begin
                    res_l=A&(~(1<<bit_pos));
                end
            end
        end
    end
    ResL<=res_l&255;
    MulCarryOut<=mul_carry&1;
    if ((((op==3)||(op==8))||((op==23)||(op==24)))||(((op==25)||(op==26))||((op==27)||(op==28))))
    begin
        ResH<=res_h&255;
    end
    else
    begin
        ResH<=0;
    end
end
endmodule

// This file was automatically created by py4hw Verilog generator
module BranchUnit_7fd1172757d0 (
	input [7:0] SREG,
	input [7:0] RegisterToTest,
	input [7:0] RegisterB,
	input [7:0] IORegisterToTest,
	input [2:0] Bit,
	input [2:0] Operation,
	output  reg  Skip,
	output  reg  Branch);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    sreg=SREG;
    reg=RegisterToTest;
    reg_b=RegisterB;
    io_reg=IORegisterToTest;
    bit_idx=Bit;
    op=Operation;
    skip_out=0;
    branch_out=0;
    sreg_bit=(sreg>>bit_idx)&1;
    reg_bit=(reg>>bit_idx)&1;
    io_bit=(io_reg>>bit_idx)&1;
    if (op==1)
    begin
        branch_out=sreg_bit;
    end
    else
    begin
        if (op==2)
        begin
            branch_out=1-sreg_bit;
        end
        else
        begin
            if (op==3)
            begin
                skip_out=1-reg_bit;
            end
            else
            begin
                if (op==4)
                begin
                    skip_out=reg_bit;
                end
                else
                begin
                    if (op==5)
                    begin
                        skip_out=1-io_bit;
                    end
                    else
                    begin
                        if (op==6)
                        begin
                            skip_out=io_bit;
                        end
                        else
                        begin
                            if (op==7)
                            begin
                                if (reg==reg_b)
                                begin
                                    skip_out=1;
                                end
                                else
                                begin
                                    skip_out=0;
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    Skip<=skip_out;
    Branch<=branch_out;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleC_7fd117275b90 (
	input [15:0] Rr,
	input [15:0] Rd,
	input [15:0] Res,
	input [3:0] Mode,
	input  MulCarry,
	output  reg  Cout);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    rr=Rr;
    rd=Rd;
    res=Res;
    mode=Mode;
    rd7=(rd>>7)&1;
    rr7=(rr>>7)&1;
    r7=(res>>7)&1;
    rd0=rd&1;
    rd15=(rd>>15)&1;
    r15=(res>>15)&1;
    c_out=0;
    if (mode==0)
    begin
        c_out=0;
    end
    if (mode==1)
    begin
        c_out=1;
    end
    else
    begin
        if (mode==2)
        begin
            not_r7=(~r7)&1;
            c_out=((rd7&rr7)|(rr7&not_r7))|(not_r7&rd7);
        end
        else
        begin
            if (mode==3)
            begin
                not_rd7=(~rd7)&1;
                c_out=((not_rd7&rr7)|(rr7&r7))|(r7&not_rd7);
            end
            else
            begin
                if (mode==4)
                begin
                    not_r15=(~r15)&1;
                    c_out=not_r15&rd15;
                end
                else
                begin
                    if (mode==5)
                    begin
                        not_rd15=(~rd15)&1;
                        c_out=r15&not_rd15;
                    end
                    else
                    begin
                        if (mode==6)
                        begin
                            c_out=1;
                        end
                        else
                        begin
                            if (mode==7)
                            begin
                                if ((res&255)!=0)
                                begin
                                    c_out=1;
                                end
                                else
                                begin
                                    c_out=0;
                                end
                            end
                            else
                            begin
                                if (mode==8)
                                begin
                                    c_out=MulCarry&1;
                                end
                                else
                                begin
                                    if (mode==9)
                                    begin
                                        c_out=rd0;
                                    end
                                    else
                                    begin
                                        if (mode==10)
                                        begin
                                            c_out=rd7;
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
    Cout<=c_out&1;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleZ_7fd117275ed0 (
	input [15:0] Res,
	input [2:0] Mode,
	input  Zprev,
	output  reg  Zout);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    res=Res;
    mode=Mode;
    z_prev=Zprev;
    z_out=0;
    if (mode==0)
    begin
        z_out=0;
    end
    else
    begin
        if (mode==1)
        begin
            z_out=1;
        end
        else
        begin
            if (mode==2)
            begin
                z_out=if ((res&255)==0)
                begin
                    1
                end
                else
                begin
                    0
                end
                ;
            end
            else
            begin
                if (mode==3)
                begin
                    z_out=if ((res&65535)==0)
                    begin
                        1
                    end
                    else
                    begin
                        0
                    end
                    ;
                end
                else
                begin
                    if (mode==4)
                    begin
                        current_z=if ((res&255)==0)
                        begin
                            1
                        end
                        else
                        begin
                            0
                        end
                        ;
                        z_out=(z_prev&1)&current_z;
                    end
                    else
                    begin
                        if (mode==5)
                        begin
                            current_z=if ((res&255)==0)
                            begin
                                1
                            end
                            else
                            begin
                                0
                            end
                            ;
                            z_out=(z_prev&1)&current_z;
                        end
                    end
                end
            end
        end
    end
    Zout<=z_out&1;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleN_7fd117275f10 (
	input [15:0] Res,
	input [2:0] Mode,
	output  reg  Nout);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    mode=Mode;
    res=Res;
    N_out=0;
    if (mode==0)
    begin
        N_out=0;
    end
    else
    begin
        if (mode==1)
        begin
            N_out=1;
        end
        else
        begin
            if (mode==2)
            begin
                N_out=(res>>7)&1;
            end
            else
            begin
                if (mode==3)
                begin
                    N_out=(res>>15)&1;
                end
            end
        end
    end
    Nout<=N_out&1;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleV_7fd117276410 (
	input [15:0] Rr,
	input [15:0] Rd,
	input [15:0] Res,
	input  N,
	input [3:0] Mode,
	input  C,
	output  reg  Vout);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    rr=Rr;
    rd=Rd;
    res=Res;
    n_flag=N;
    c_flag=C&1;
    mode=Mode;
    rd7=(rd>>7)&1;
    rr7=(rr>>7)&1;
    r7=(res>>7)&1;
    not_rd7=(~rd7)&1;
    not_rr7=(~rr7)&1;
    not_r7=(~r7)&1;
    rd15=(rd>>15)&1;
    r15=(res>>15)&1;
    not_rd15=(~rd15)&1;
    not_r15=(~r15)&1;
    v_out=0;
    if (mode==0)
    begin
        v_out=0;
    end
    else
    begin
        if (mode==1)
        begin
            v_out=1;
        end
        else
        begin
            if (mode==2)
            begin
                v_out=((rd7&rr7)&not_r7)|((not_rd7&not_rr7)&r7);
            end
            else
            begin
                if (mode==3)
                begin
                    v_out=((rd7&not_rr7)&not_r7)|((not_rd7&rr7)&r7);
                end
                else
                begin
                    if (mode==4)
                    begin
                        v_out=not_rd15&r15;
                    end
                    else
                    begin
                        if (mode==5)
                        begin
                            v_out=rd15&not_r15;
                        end
                        else
                        begin
                            if (mode==6)
                            begin
                                if ((res&255)==128)
                                begin
                                    v_out=1;
                                end
                                else
                                begin
                                    v_out=0;
                                end
                            end
                            else
                            begin
                                if (mode==7)
                                begin
                                    if ((res&255)==127)
                                    begin
                                        v_out=1;
                                    end
                                    else
                                    begin
                                        v_out=0;
                                    end
                                end
                                else
                                begin
                                    if (mode==9)
                                    begin
                                        v_out=(n_flag&1)^c_flag;
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    Vout<=v_out&1;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleH_7fd117276790 (
	input [15:0] Rr,
	input [15:0] Rd,
	input [15:0] Res,
	input [1:0] Mode,
	output  reg  Hout);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    rr=Rr;
    rd=Rd;
    res=Res;
    mode=Mode;
    rd3=(rd>>3)&1;
    rr3=(rr>>3)&1;
    r3=(res>>3)&1;
    not_rd3=(~rd3)&1;
    not_r3=(~r3)&1;
    h_out=0;
    if (mode==0)
    begin
        h_out=0;
    end
    else
    begin
        if (mode==1)
        begin
            h_out=1;
        end
        else
        begin
            if (mode==2)
            begin
                h_out=((rd3&rr3)|(rr3&not_r3))|(not_r3&rd3);
            end
            else
            begin
                if (mode==3)
                begin
                    h_out=((not_rd3&rr3)|(rr3&r3))|(r3&not_rd3);
                end
            end
        end
    end
    Hout<=h_out&1;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleT_7fd1172767d0 (
	input [15:0] Rr,
	input [2:0] BitPos,
	input [1:0] Mode,
	output  reg  Tout);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    rr=Rr;
    bit_pos=BitPos;
    mode=Mode;
    t_out=0;
    if (mode==0)
    begin
        t_out=0;
    end
    else
    begin
        if (mode==1)
        begin
            t_out=1;
        end
        else
        begin
            if (mode==2)
            begin
                t_out=(rr>>(bit_pos&7))&1;
            end
        end
    end
    Tout<=t_out&1;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleI_7fd117276b50 (
	input  Mode,
	output  reg  Iout);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    mode=Mode;
    I_out=0;
    if (mode==0)
    begin
        I_out=0;
    end
    else
    begin
        if (mode==1)
        begin
            I_out=1;
        end
    end
    Iout<=I_out;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module HandleS_7fd117277090 (
	input  N,
	input  V,
	input [2:0] Mode,
	output  reg  Sout);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    n_flag=N;
    v_flag=V;
    mode=Mode;
    s_out=0;
    if (mode==0)
    begin
        s_out=0;
    end
    else
    begin
        if (mode==1)
        begin
            s_out=1;
        end
        else
        begin
            if (mode==2)
            begin
                s_out=(n_flag&1)^(v_flag&1);
            end
        end
    end
    Sout<=s_out&1;
end
endmodule

// This file was automatically created by py4hw Verilog generator
module ALU_MergerAndLogic_7fd1172770d0 (
	input  w_cout,
	input  w_zout,
	input  w_nout,
	input  w_vout,
	input  w_sout,
	input  w_hout,
	input  w_tout,
	input  w_iout,
	input [7:0] w_res_l,
	input [7:0] w_res_h,
	output  reg [7:0] sreg_val,
	output  reg [7:0] out_byte0,
	output  reg [7:0] out_byte1);
// Code generated from propagate method
// wire/variable declaration
// initial
initial
begin
end
// process
always @(*)
begin
    out_byte0<=w_res_l;
    out_byte1<=w_res_h;
    new_sreg=((((((((w_iout&1)<<7)|((w_tout&1)<<6))|((w_hout&1)<<5))|((w_sout&1)<<4))|((w_vout&1)<<3))|((w_nout&1)<<2))|((w_zout&1)<<1))|(w_cout&1);
    sreg_val<=new_sreg;
end
endmodule
