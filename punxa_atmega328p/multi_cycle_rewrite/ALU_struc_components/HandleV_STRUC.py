import py4hw

class HandleV_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Rr, Rd, Res, N, C, Mode,
                 Vout):
        super().__init__(parent, name)

        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.Rr = self.addIn('Rr', Rr)
        self.Rd = self.addIn('Rd', Rd)
        self.Res = self.addIn('Res', Res)
        self.N = self.addIn('N', N)
        self.C = self.addIn('C', C)
        self.Mode = self.addIn('Mode', Mode)
        
        self.Vout = self.addOut('Vout', Vout)

        # -------------------------------------------------------------
        # 2. CONSTANTS
        # -------------------------------------------------------------
        self.w_zero1 = self.wire("w_zero1", 1)
        self.w_one1 = self.wire("w_one1", 1)
        self.w_0x80 = self.wire("w_0x80", 8)
        self.w_0x7F = self.wire("w_0x7F", 8)
        
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)
        py4hw.Constant(self, "Const1_1", 1, self.w_one1)
        py4hw.Constant(self, "Const0x80", 0x80, self.w_0x80)
        py4hw.Constant(self, "Const0x7F", 0x7F, self.w_0x7F)

        # -------------------------------------------------------------
        # 3. BIT EXTRACTIONS (MSBs and 8-bit Result slice)
        # -------------------------------------------------------------
        self.w_rd7 = self.wire("w_rd7", 1)
        self.w_rr7 = self.wire("w_rr7", 1)
        self.w_r7  = self.wire("w_r7", 1)
        self.w_rd15 = self.wire("w_rd15", 1)
        self.w_r15  = self.wire("w_r15", 1)
        self.w_res_l = self.wire("w_res_l", 8)

        py4hw.Range(self, "Rng_Rd7", self.Rd, 7, 7, self.w_rd7)
        py4hw.Range(self, "Rng_Rr7", self.Rr, 7, 7, self.w_rr7)
        py4hw.Range(self, "Rng_R7", self.Res, 7, 7, self.w_r7)
        py4hw.Range(self, "Rng_Rd15", self.Rd, 15, 15, self.w_rd15)
        py4hw.Range(self, "Rng_R15", self.Res, 15, 15, self.w_r15)
        py4hw.Range(self, "Rng_ResLow", self.Res, 7, 0, self.w_res_l)

        # Inversions
        self.w_not_rd7 = self.wire("w_not_rd7", 1)
        self.w_not_rr7 = self.wire("w_not_rr7", 1)
        self.w_not_r7  = self.wire("w_not_r7", 1)
        self.w_not_rd15 = self.wire("w_not_rd15", 1)
        self.w_not_r15  = self.wire("w_not_r15", 1)

        py4hw.Not(self, "Not_Rd7", self.w_rd7, self.w_not_rd7)
        py4hw.Not(self, "Not_Rr7", self.w_rr7, self.w_not_rr7)
        py4hw.Not(self, "Not_R7", self.w_r7, self.w_not_r7)
        py4hw.Not(self, "Not_Rd15", self.w_rd15, self.w_not_rd15)
        py4hw.Not(self, "Not_R15", self.w_r15, self.w_not_r15)

        # -------------------------------------------------------------
        # 4. STRUCTURAL DATAPATHS FOR EACH MODE
        # -------------------------------------------------------------

        # Mode 2: 8-bit Addition -> (rd7 & rr7 & not_r7) | (not_rd7 & not_rr7 & r7)
        self.w_m2_t1_temp = self.wire("w_m2_t1_temp", 1)
        self.w_m2_t1 = self.wire("w_m2_t1", 1)
        py4hw.And2(self, "M2_And1a", self.w_rd7, self.w_rr7, self.w_m2_t1_temp)
        py4hw.And2(self, "M2_And1b", self.w_m2_t1_temp, self.w_not_r7, self.w_m2_t1)

        self.w_m2_t2_temp = self.wire("w_m2_t2_temp", 1)
        self.w_m2_t2 = self.wire("w_m2_t2", 1)
        py4hw.And2(self, "M2_And2a", self.w_not_rd7, self.w_not_rr7, self.w_m2_t2_temp)
        py4hw.And2(self, "M2_And2b", self.w_m2_t2_temp, self.w_r7, self.w_m2_t2)

        self.w_mode2 = self.wire("w_mode2", 1)
        py4hw.Or2(self, "M2_Or", self.w_m2_t1, self.w_m2_t2, self.w_mode2)

        # Mode 3: 8-bit Subtraction -> (rd7 & not_rr7 & not_r7) | (not_rd7 & rr7 & r7)
        self.w_m3_t1_temp = self.wire("w_m3_t1_temp", 1)
        self.w_m3_t1 = self.wire("w_m3_t1", 1)
        py4hw.And2(self, "M3_And1a", self.w_rd7, self.w_not_rr7, self.w_m3_t1_temp)
        py4hw.And2(self, "M3_And1b", self.w_m3_t1_temp, self.w_not_r7, self.w_m3_t1)

        self.w_m3_t2_temp = self.wire("w_m3_t2_temp", 1)
        self.w_m3_t2 = self.wire("w_m3_t2", 1)
        py4hw.And2(self, "M3_And2a", self.w_not_rd7, self.w_rr7, self.w_m3_t2_temp)
        py4hw.And2(self, "M3_And2b", self.w_m3_t2_temp, self.w_r7, self.w_m3_t2)

        self.w_mode3 = self.wire("w_mode3", 1)
        py4hw.Or2(self, "M3_Or", self.w_m3_t1, self.w_m3_t2, self.w_mode3)

        # Mode 4: 16-bit Addition -> not_rd15 & r15
        self.w_mode4 = self.wire("w_mode4", 1)
        py4hw.And2(self, "M4_And", self.w_not_rd15, self.w_r15, self.w_mode4)

        # Mode 5: 16-bit Subtraction -> rd15 & not_r15
        self.w_mode5 = self.wire("w_mode5", 1)
        py4hw.And2(self, "M5_And", self.w_rd15, self.w_not_r15, self.w_mode5)

        # Mode 6: INC -> Res_Low == 0x80
        self.w_mode6 = self.wire("w_mode6", 1)
        py4hw.Equal(self, "M6_Eq", self.w_res_l, self.w_0x80, self.w_mode6)

        # Mode 7: DEC -> Res_Low == 0x7F
        self.w_mode7 = self.wire("w_mode7", 1)
        py4hw.Equal(self, "M7_Eq", self.w_res_l, self.w_0x7F, self.w_mode7)

        # Mode 9: Shift/Rotate -> N XOR C
        self.w_mode9 = self.wire("w_mode9", 1)
        py4hw.Xor2(self, "M9_Xor", self.N, self.C, self.w_mode9)

        # -------------------------------------------------------------
        # 5. MUX ARRAY CONSTRUCTION
        # -------------------------------------------------------------
        # Max mode is 9, so a 16-element array handles this safely
        MUX_SIZE = 16
        
        # Initialize default routes to 0
        v_inputs = [self.w_zero1] * MUX_SIZE

        # Route computed 1-bit wires to their exact Mode indices
        v_inputs[0] = self.w_zero1       # Mode 0: Force Clear (CLV, AND, OR, etc)
        v_inputs[1] = self.w_one1        # Mode 1: Force Set (SEV)
        v_inputs[2] = self.w_mode2       # Mode 2: 8-bit Addition
        v_inputs[3] = self.w_mode3       # Mode 3: 8-bit Subtraction
        v_inputs[4] = self.w_mode4       # Mode 4: 16-bit Addition
        v_inputs[5] = self.w_mode5       # Mode 5: 16-bit Subtraction
        v_inputs[6] = self.w_mode6       # Mode 6: INC (Res == 0x80)
        v_inputs[7] = self.w_mode7       # Mode 7: DEC (Res == 0x7F)
        v_inputs[9] = self.w_mode9       # Mode 9: Shifts (N ^ C)

        # -------------------------------------------------------------
        # 6. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        py4hw.Mux(self, "Mux_Vout", self.Mode, v_inputs, self.Vout)