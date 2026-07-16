import py4hw

class HandleC_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Rr, Rd, Res, Mode, MulCarry,
                 Cout):
        super().__init__(parent, name)

        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.Rr = self.addIn('Rr', Rr)
        self.Rd = self.addIn('Rd', Rd)
        self.Res = self.addIn('Res', Res)
        self.Mode = self.addIn('Mode', Mode)
        self.MulCarry = self.addIn('MulCarry', MulCarry)
        
        self.Cout = self.addOut('Cout', Cout)

        # -------------------------------------------------------------
        # 2. CONSTANTS
        # -------------------------------------------------------------
        self.w_zero1 = self.wire("w_zero1", 1)
        self.w_one1 = self.wire("w_one1", 1)
        self.w_zero8 = self.wire("w_zero8", 8)
        
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)
        py4hw.Constant(self, "Const1_1", 1, self.w_one1)
        py4hw.Constant(self, "Const0_8", 0, self.w_zero8)

        # -------------------------------------------------------------
        # 3. BIT EXTRACTIONS
        # -------------------------------------------------------------
        self.w_rd7 = self.wire("w_rd7", 1)
        self.w_rr7 = self.wire("w_rr7", 1)
        self.w_r7  = self.wire("w_r7", 1)
        self.w_rd0 = self.wire("w_rd0", 1)
        self.w_rd15 = self.wire("w_rd15", 1)
        self.w_r15  = self.wire("w_r15", 1)
        self.w_res_l = self.wire("w_res_l", 8)

        # 8-bit MSBs
        py4hw.Range(self, "Rng_Rd7", self.Rd, 7, 7, self.w_rd7)
        py4hw.Range(self, "Rng_Rr7", self.Rr, 7, 7, self.w_rr7)
        py4hw.Range(self, "Rng_R7", self.Res, 7, 7, self.w_r7)
        
        # Shift LSB
        py4hw.Range(self, "Rng_Rd0", self.Rd, 0, 0, self.w_rd0)
        
        # 16-bit MSBs
        py4hw.Range(self, "Rng_Rd15", self.Rd, 15, 15, self.w_rd15)
        py4hw.Range(self, "Rng_R15", self.Res, 15, 15, self.w_r15)
        
        # Lower 8-bits for NEG 0x00 check
        py4hw.Range(self, "Rng_ResL", self.Res, 7, 0, self.w_res_l)

        # Inversions
        self.w_not_r7  = self.wire("w_not_r7", 1)
        self.w_not_rd7 = self.wire("w_not_rd7", 1)
        self.w_not_r15 = self.wire("w_not_r15", 1)
        self.w_not_rd15 = self.wire("w_not_rd15", 1)

        py4hw.Not(self, "Not_R7", self.w_r7, self.w_not_r7)
        py4hw.Not(self, "Not_Rd7", self.w_rd7, self.w_not_rd7)
        py4hw.Not(self, "Not_R15", self.w_r15, self.w_not_r15)
        py4hw.Not(self, "Not_Rd15", self.w_rd15, self.w_not_rd15)

        # -------------------------------------------------------------
        # 4. STRUCTURAL DATAPATHS FOR EACH MODE
        # -------------------------------------------------------------

        # --- Mode 2: 8-bit Addition -> (rd7 & rr7) | (rr7 & not_r7) | (not_r7 & rd7) ---
        self.w_add_t1 = self.wire("w_add_t1", 1)
        self.w_add_t2 = self.wire("w_add_t2", 1)
        self.w_add_t3 = self.wire("w_add_t3", 1)
        
        py4hw.And2(self, "Add_And1", self.w_rd7, self.w_rr7, self.w_add_t1)
        py4hw.And2(self, "Add_And2", self.w_rr7, self.w_not_r7, self.w_add_t2)
        py4hw.And2(self, "Add_And3", self.w_not_r7, self.w_rd7, self.w_add_t3)

        self.w_add_or_temp = self.wire("w_add_or_temp", 1)
        self.w_c_add = self.wire("w_c_add", 1)
        
        py4hw.Or2(self, "Add_Or1", self.w_add_t1, self.w_add_t2, self.w_add_or_temp)
        py4hw.Or2(self, "Add_Or2", self.w_add_or_temp, self.w_add_t3, self.w_c_add)

        # --- Mode 3: 8-bit Subtraction -> (not_rd7 & rr7) | (rr7 & r7) | (r7 & not_rd7) ---
        self.w_sub_t1 = self.wire("w_sub_t1", 1)
        self.w_sub_t2 = self.wire("w_sub_t2", 1)
        self.w_sub_t3 = self.wire("w_sub_t3", 1)
        
        py4hw.And2(self, "Sub_And1", self.w_not_rd7, self.w_rr7, self.w_sub_t1)
        py4hw.And2(self, "Sub_And2", self.w_rr7, self.w_r7, self.w_sub_t2)
        py4hw.And2(self, "Sub_And3", self.w_r7, self.w_not_rd7, self.w_sub_t3)

        self.w_sub_or_temp = self.wire("w_sub_or_temp", 1)
        self.w_c_sub = self.wire("w_c_sub", 1)
        
        py4hw.Or2(self, "Sub_Or1", self.w_sub_t1, self.w_sub_t2, self.w_sub_or_temp)
        py4hw.Or2(self, "Sub_Or2", self.w_sub_or_temp, self.w_sub_t3, self.w_c_sub)

        # --- Mode 4: 16-bit Addition (ADIW) -> not_r15 & rd15 ---
        self.w_c_adiw = self.wire("w_c_adiw", 1)
        py4hw.And2(self, "Adiw_And", self.w_not_r15, self.w_rd15, self.w_c_adiw)

        # --- Mode 5: 16-bit Subtraction (SBIW) -> r15 & not_rd15 ---
        self.w_c_sbiw = self.wire("w_c_sbiw", 1)
        py4hw.And2(self, "Sbiw_And", self.w_r15, self.w_not_rd15, self.w_c_sbiw)

        # --- Mode 7: Negation (NEG) -> 1 if (res & 0xFF) != 0 else 0 ---
        self.w_res_is_zero = self.wire("w_res_is_zero", 1)
        self.w_c_neg = self.wire("w_c_neg", 1)
        py4hw.Equal(self, "Neg_Eq_0", self.w_res_l, self.w_zero8, self.w_res_is_zero)
        py4hw.Not(self, "Neg_Not_Eq_0", self.w_res_is_zero, self.w_c_neg)

        # -------------------------------------------------------------
        # 5. MUX ARRAY CONSTRUCTION
        # -------------------------------------------------------------
        # The Mode signal ranges from 0 to 10. A 16-element array handles this safely.
        MUX_SIZE = 16
        
        # Initialize default routes to 0
        c_inputs = [self.w_zero1] * MUX_SIZE

        # Route computed 1-bit wires to their exact Mode indices
        c_inputs[0] = self.w_zero1       # Mode 0: Explicit Clear (CLC)
        c_inputs[1] = self.w_one1        # Mode 1: Explicit Set (SEC)
        c_inputs[2] = self.w_c_add       # Mode 2: 8-bit Addition (ADD, ADC)
        c_inputs[3] = self.w_c_sub       # Mode 3: 8-bit Subtraction (SUB, SBC, CP, CPC)
        c_inputs[4] = self.w_c_adiw      # Mode 4: 16-bit Addition (ADIW)
        c_inputs[5] = self.w_c_sbiw      # Mode 5: 16-bit Subtraction (SBIW)
        c_inputs[6] = self.w_one1        # Mode 6: Force Carry to 1 (COM)
        c_inputs[7] = self.w_c_neg       # Mode 7: Two's Complement Negation (NEG)
        c_inputs[8] = self.MulCarry      # Mode 8: Multiplication family (MULs)
        c_inputs[9] = self.w_rd0         # Mode 9: Shift Right (LSR, ROR, ASR)
        c_inputs[10] = self.w_rd7        # Mode 10: Shift Left (LSL, ROL)

        # -------------------------------------------------------------
        # 6. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        py4hw.Mux(self, "Mux_Cout", self.Mode, c_inputs, self.Cout)