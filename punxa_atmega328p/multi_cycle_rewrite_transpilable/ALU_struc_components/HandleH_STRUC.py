import py4hw

class HandleH_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Rr, Rd, Res, Mode,
                 Hout):
        super().__init__(parent, name)

        # ------------------------------------------------s-------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.Rr = self.addIn('Rr', Rr)
        self.Rd = self.addIn('Rd', Rd)
        self.Res = self.addIn('Res', Res)
        self.Mode = self.addIn('Mode', Mode)

        self.Hout = self.addOut('Hout', Hout)

        # -------------------------------------------------------------
        # 2. CONSTANTS
        # -------------------------------------------------------------
        self.w_zero1 = self.wire("w_zero1", 1)
        self.w_one1 = self.wire("w_one1", 1)
        
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)
        py4hw.Constant(self, "Const1_1", 1, self.w_one1)

        # -------------------------------------------------------------
        # 3. BIT EXTRACTIONS (Bit 3)
        # -------------------------------------------------------------
        self.w_rd3 = self.wire("w_rd3", 1)
        self.w_rr3 = self.wire("w_rr3", 1)
        self.w_r3  = self.wire("w_r3", 1)

        py4hw.Range(self, "Rng_Rd3", self.Rd, 3, 3, self.w_rd3)
        py4hw.Range(self, "Rng_Rr3", self.Rr, 3, 3, self.w_rr3)
        py4hw.Range(self, "Rng_R3", self.Res, 3, 3, self.w_r3)

        # Inversions for the boolean logic
        self.w_not_rd3 = self.wire("w_not_rd3", 1)
        self.w_not_r3  = self.wire("w_not_r3", 1)

        py4hw.Not(self, "Not_Rd3", self.w_rd3, self.w_not_rd3)
        py4hw.Not(self, "Not_R3", self.w_r3, self.w_not_r3)

        # -------------------------------------------------------------
        # 4. STRUCTURAL DATAPATHS FOR EACH MODE
        # -------------------------------------------------------------

        # --- Mode 2: Addition -> (rd3 & rr3) | (rr3 & not_r3) | (not_r3 & rd3) ---
        self.w_add_t1 = self.wire("w_add_t1", 1)
        self.w_add_t2 = self.wire("w_add_t2", 1)
        self.w_add_t3 = self.wire("w_add_t3", 1)
        
        py4hw.And2(self, "Add_And1", self.w_rd3, self.w_rr3, self.w_add_t1)
        py4hw.And2(self, "Add_And2", self.w_rr3, self.w_not_r3, self.w_add_t2)
        py4hw.And2(self, "Add_And3", self.w_not_r3, self.w_rd3, self.w_add_t3)

        self.w_add_or_temp = self.wire("w_add_or_temp", 1)
        self.w_h_add = self.wire("w_h_add", 1)
        
        py4hw.Or2(self, "Add_Or1", self.w_add_t1, self.w_add_t2, self.w_add_or_temp)
        py4hw.Or2(self, "Add_Or2", self.w_add_or_temp, self.w_add_t3, self.w_h_add)


        # --- Mode 3: Subtraction -> (not_rd3 & rr3) | (rr3 & r3) | (r3 & not_rd3) ---
        self.w_sub_t1 = self.wire("w_sub_t1", 1)
        self.w_sub_t2 = self.wire("w_sub_t2", 1)
        self.w_sub_t3 = self.wire("w_sub_t3", 1)
        
        py4hw.And2(self, "Sub_And1", self.w_not_rd3, self.w_rr3, self.w_sub_t1)
        py4hw.And2(self, "Sub_And2", self.w_rr3, self.w_r3, self.w_sub_t2)
        py4hw.And2(self, "Sub_And3", self.w_r3, self.w_not_rd3, self.w_sub_t3)

        self.w_sub_or_temp = self.wire("w_sub_or_temp", 1)
        self.w_h_sub = self.wire("w_h_sub", 1)
        
        py4hw.Or2(self, "Sub_Or1", self.w_sub_t1, self.w_sub_t2, self.w_sub_or_temp)
        py4hw.Or2(self, "Sub_Or2", self.w_sub_or_temp, self.w_sub_t3, self.w_h_sub)


        # --- Mode 4: Negation (NEG) -> r3 | rd3 ---
        self.w_h_neg = self.wire("w_h_neg", 1)
        py4hw.Or2(self, "Neg_Or", self.w_r3, self.w_rd3, self.w_h_neg)

        # -------------------------------------------------------------
        # 5. MUX ARRAY CONSTRUCTION
        # -------------------------------------------------------------
        # The Mode signal ranges from 0 to 4. An 8-element array handles this safely.
        MUX_SIZE = 8
        
        # Initialize default routes to 0
        h_inputs = [self.w_zero1] * MUX_SIZE

        # Route computed 1-bit wires to their exact Mode indices
        h_inputs[0] = self.w_zero1       # Mode 0: Force Clear (CLH)
        h_inputs[1] = self.w_one1        # Mode 1: Force Set (SEH)
        h_inputs[2] = self.w_h_add       # Mode 2: Addition (ADD, ADC)
        h_inputs[3] = self.w_h_sub       # Mode 3: Subtraction / Compare (SUB, SBC, CP, CPC)
        h_inputs[4] = self.w_h_neg       # Mode 4: Two's Complement Negation (NEG)

        # -------------------------------------------------------------
        # 6. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        py4hw.Mux(self, "Mux_Hout", self.Mode, h_inputs, self.Hout)