import py4hw

class AU_STRUC(py4hw.Logic): 
    def __init__(self, parent, name: str,
                 Cval, RegAL, RegAH, RegBL, RegBH, Operation, BitPos,
                 ResL, ResH, MulCarryOut, Tval=None):
        super().__init__(parent, name)

        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.Cval = self.addIn('Cval', Cval)
        self.Tval = self.addIn('Tval', Tval) if Tval is not None else None
        
        self.RegAL = self.addIn('RegAL', RegAL)
        self.RegAH = self.addIn('RegAH', RegAH)
        self.RegBL = self.addIn('RegBL', RegBL)
        self.RegBH = self.addIn('RegBH', RegBH)
        self.Operation = self.addIn('Operation', Operation)
        self.BitPos = self.addIn('BitPos', BitPos)

        self.ResL = self.addOut('ResL', ResL)
        self.ResH = self.addOut('ResH', ResH)
        self.MulCarryOut = self.addOut('MulCarryOut', MulCarryOut)

        # -------------------------------------------------------------
        # 2. CONSTANTS & UTILITY WIRES
        # -------------------------------------------------------------
        self.w_zero8 = self.wire("w_zero8", 8)
        self.w_zero16 = self.wire("w_zero16", 16)
        self.w_zero1 = self.wire("w_zero1", 1)
        self.w_one8 = self.wire("w_one8", 8)
        self.w_ff = self.wire("w_ff", 8)
        self.w_Cval8 = self.wire("w_Cval8", 8)

        py4hw.Constant(self, "Const0_8", 0, self.w_zero8)
        py4hw.Constant(self, "Const0_16", 0, self.w_zero16)
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)
        py4hw.Constant(self, "Const1_8", 1, self.w_one8)
        py4hw.Constant(self, "ConstFF", 255, self.w_ff)

        # Pad 1-bit Carry to 8-bit for arithmetic usage
        self.w_zero7 = self.wire("w_zero7", 7)
        py4hw.Constant(self, "Const0_7", 0, self.w_zero7)
        py4hw.ConcatenateLSBF(self, "Pad_Cval", [self.Cval, self.w_zero7], self.w_Cval8)

        # -------------------------------------------------------------
        # 3. STRUCTURAL DATAPATHS (All execute in parallel)
        # -------------------------------------------------------------
        
        # --- Basic Arithmetic (ADD, ADC, SUB, SBC) ---
        self.w_add = self.wire("w_add", 8)
        py4hw.Add(self, 'ADD_Unit', self.RegAL, self.RegBL, self.w_add)
        
        self.w_adc_temp = self.wire("w_adc_temp", 8)
        self.w_adc = self.wire("w_adc", 8)
        py4hw.Add(self, 'ADC_Add1', self.RegAL, self.RegBL, self.w_adc_temp)
        py4hw.Add(self, 'ADC_Add2', self.w_adc_temp, self.w_Cval8, self.w_adc)
        
        self.w_sub = self.wire("w_sub", 8)
        py4hw.Sub(self, 'SUB_Unit', self.RegAL, self.RegBL, self.w_sub)

        self.w_sbc_temp = self.wire("w_sbc_temp", 8)
        self.w_sbc = self.wire("w_sbc", 8)
        py4hw.Sub(self, 'SBC_Sub1', self.RegAL, self.RegBL, self.w_sbc_temp)
        py4hw.Sub(self, 'SBC_Sub2', self.w_sbc_temp, self.w_Cval8, self.w_sbc)

        # --- INC / DEC ---
        self.w_inc = self.wire("w_inc", 8)
        py4hw.Add(self, 'INC_Unit', self.RegAL, self.w_one8, self.w_inc)

        self.w_dec = self.wire("w_dec", 8)
        py4hw.Sub(self, 'DEC_Unit', self.RegAL, self.w_one8, self.w_dec)

        # --- 16-Bit Word Arithmetic (ADIW / SBIW) ---
        self.w_wordA = self.wire("w_wordA", 16)
        self.w_wordB = self.wire("w_wordB", 16)
        py4hw.ConcatenateLSBF(self, 'ConcatA', [self.RegAL, self.RegAH], self.w_wordA)
        py4hw.ConcatenateLSBF(self, 'ConcatB', [self.RegBL, self.RegBH], self.w_wordB)

        self.w_adiw16 = self.wire("w_adiw16", 16)
        py4hw.Add(self, 'ADIW_Unit', self.w_wordA, self.w_wordB, self.w_adiw16)
        self.w_adiw_l = self.wire("w_adiw_l", 8)
        self.w_adiw_h = self.wire("w_adiw_h", 8)
        py4hw.Range(self, "adiw_low", self.w_adiw16, 7, 0, self.w_adiw_l)
        py4hw.Range(self, "adiw_high", self.w_adiw16, 15, 8, self.w_adiw_h)

        self.w_sbiw16 = self.wire("w_sbiw16", 16)
        py4hw.Sub(self, 'SBIW_Unit', self.w_wordA, self.w_wordB, self.w_sbiw16)
        self.w_sbiw_l = self.wire("w_sbiw_l", 8)
        self.w_sbiw_h = self.wire("w_sbiw_h", 8)
        py4hw.Range(self, "sbiw_low", self.w_sbiw16, 7, 0, self.w_sbiw_l)
        py4hw.Range(self, "sbiw_high", self.w_sbiw16, 15, 8, self.w_sbiw_h)

        # --- Basic Logic ---
        self.w_and = self.wire("w_and", 8)
        py4hw.And2(self, 'AND_Unit', self.RegAL, self.RegBL, self.w_and)

        self.w_or = self.wire("w_or", 8)
        py4hw.Or2(self, 'OR_Unit', self.RegAL, self.RegBL, self.w_or)

        self.w_xor = self.wire("w_xor", 8)
        py4hw.Xor2(self, 'XOR_Unit', self.RegAL, self.RegBL, self.w_xor)

        self.w_com = self.wire("w_com", 8)
        py4hw.Not(self, 'COM_Unit', self.RegAL, self.w_com)

        self.w_neg = self.wire("w_neg", 8)
        py4hw.Sub(self, 'NEG_Unit', self.w_zero8, self.RegAL, self.w_neg)

        self.w_notB = self.wire("w_notB", 8)
        py4hw.Not(self, 'NOT_B', self.RegBL, self.w_notB)
        self.w_cbr = self.wire("w_cbr", 8)
        py4hw.And2(self, 'CBR_Unit', self.RegAL, self.w_notB, self.w_cbr)

        # --- Shifts and Rotates (Using Concat & Range) ---
        self.w_A_6_0 = self.wire("w_A_6_0", 7)
        self.w_A_7_1 = self.wire("w_A_7_1", 7)
        self.w_A_7 = self.wire("w_A_7", 1)
        
        py4hw.Range(self, "Rng_6_0", self.RegAL, 6, 0, self.w_A_6_0)
        py4hw.Range(self, "Rng_7_1", self.RegAL, 7, 1, self.w_A_7_1)
        py4hw.Range(self, "Rng_7", self.RegAL, 7, 7, self.w_A_7)

        self.w_lsl = self.wire("w_lsl", 8)
        py4hw.ConcatenateLSBF(self, "LSL_Concat", [self.w_zero1, self.w_A_6_0], self.w_lsl)

        self.w_lsr = self.wire("w_lsr", 8)
        py4hw.ConcatenateLSBF(self, "LSR_Concat", [self.w_A_7_1, self.w_zero1], self.w_lsr)

        self.w_rol = self.wire("w_rol", 8)
        py4hw.ConcatenateLSBF(self, "ROL_Concat", [self.Cval, self.w_A_6_0], self.w_rol)

        self.w_ror = self.wire("w_ror", 8)
        py4hw.ConcatenateLSBF(self, "ROR_Concat", [self.w_A_7_1, self.Cval], self.w_ror)

        self.w_asr = self.wire("w_asr", 8)
        py4hw.ConcatenateLSBF(self, "ASR_Concat", [self.w_A_7_1, self.w_A_7], self.w_asr)

        # --- SWAP Nibbles ---
        self.w_A_3_0 = self.wire("w_A_3_0", 4)
        self.w_A_7_4 = self.wire("w_A_7_4", 4)
        py4hw.Range(self, "Rng_3_0", self.RegAL, 3, 0, self.w_A_3_0)
        py4hw.Range(self, "Rng_7_4", self.RegAL, 7, 4, self.w_A_7_4)
        self.w_swap = self.wire("w_swap", 8)
        py4hw.ConcatenateLSBF(self, "SWAP_Concat", [self.w_A_7_4, self.w_A_3_0], self.w_swap) 

        # --- Dynamic Bit Manipulation (SBI, CBI, BLD) ---
        self.w_bit_mask = self.wire("w_bit_mask", 8)
        py4hw.ShiftLeft(self, "Shl_Mask", self.w_one8, self.BitPos, self.w_bit_mask)

        self.w_sbi = self.wire("w_sbi", 8)
        py4hw.Or2(self, "SBI_Unit", self.RegAL, self.w_bit_mask, self.w_sbi)

        self.w_not_mask = self.wire("w_not_mask", 8)
        py4hw.Not(self, "Not_Mask", self.w_bit_mask, self.w_not_mask)
        self.w_cbi = self.wire("w_cbi", 8)
        py4hw.And2(self, "CBI_Unit", self.RegAL, self.w_not_mask, self.w_cbi)

        self.w_bld = self.wire("w_bld", 8)
        if self.Tval is not None:
            py4hw.Mux(self, "BLD_Mux", self.Tval, [self.w_cbi, self.w_sbi], self.w_bld)
        else:
            py4hw.Buf(self, "BLD_Null", self.w_cbi, self.w_bld)

        # --- MULTIPLIERS ---
        # MUL / FMUL (both unsigned x unsigned) share this base 16-bit product.
        self.w_mul16 = self.wire("w_mul16", 16)
        py4hw.Mul(self, "MUL_Unit", self.RegAL, self.RegBL, self.w_mul16)
        
        self.w_mul_l = self.wire("w_mul_l", 8)
        self.w_mul_h = self.wire("w_mul_h", 8)
        py4hw.Range(self, "mul_low", self.w_mul16, 7, 0, self.w_mul_l)
        py4hw.Range(self, "mul_high", self.w_mul16, 15, 8, self.w_mul_h)

        self.w_fmul16 = self.wire("w_fmul16", 16)
        # FIX (spurious py4hw warning): this is always a fixed "shift left
        # by exactly 1" (the AVR FMUL family doubles the raw product to
        # correct for the implied binary point), not a genuinely dynamic
        # shift. The previous version drove it through the general-purpose
        # variable-amount py4hw.ShiftLeft using w_one8 (the constant 1) as
        # the *shift-amount* input -- functionally fine, since w_one8's
        # VALUE is always 1, but w_one8 is 8 bits *wide*, which builds an
        # 8-layer barrel shifter capable of shifting by up to 128 (only
        # the low bit ever actually fires) and trips py4hw's own
        # "shift registers with shifting value width > 5 are not common"
        # sanity warning on every prepareTest() call. ShiftLeftConstant
        # takes the shift amount as a plain Python int rather than a wire,
        # which is what a fixed shift-by-1 actually is.
        py4hw.ShiftLeftConstant(self, "FMUL_Shift", self.w_mul16, 1, self.w_fmul16)
        self.w_fmul_l = self.wire("w_fmul_l", 8)
        self.w_fmul_h = self.wire("w_fmul_h", 8)
        py4hw.Range(self, "fmul_low", self.w_fmul16, 7, 0, self.w_fmul_l)
        py4hw.Range(self, "fmul_high", self.w_fmul16, 15, 8, self.w_fmul_h)

        self.w_mul_carry = self.wire("w_mul_carry", 1)
        py4hw.Range(self, "mul_carry_ext", self.w_mul16, 15, 15, self.w_mul_carry)

        # FIX: MULS/FMULS (signed x signed) and MULSU/FMULSU (signed x
        # unsigned) were previously routed through the same *unsigned*
        # w_mul16 above -- wrong for any operand with bit 7 set. Real
        # signed/mixed multiplies below, using py4hw.SignedMul (treats
        # each operand as two's complement per its own wire width).

        # MULS: both operands are already signed in their native 8 bits,
        # so SignedMul can consume RegAL/RegBL directly -- no extension
        # needed, product range (-128*-128..127*-128) fits in 16 bits.
        self.w_muls16 = self.wire("w_muls16", 16)
        py4hw.SignedMul(self, "MULS_Unit", self.RegAL, self.RegBL, self.w_muls16)
        self.w_muls_l = self.wire("w_muls_l", 8)
        self.w_muls_h = self.wire("w_muls_h", 8)
        py4hw.Range(self, "muls_low", self.w_muls16, 7, 0, self.w_muls_l)
        py4hw.Range(self, "muls_high", self.w_muls16, 15, 8, self.w_muls_h)
        self.w_muls_carry = self.wire("w_muls_carry", 1)
        py4hw.Range(self, "muls_carry_ext", self.w_muls16, 15, 15, self.w_muls_carry)

        self.w_fmuls16 = self.wire("w_fmuls16", 16)
        # Same fix as FMUL_Shift above -- fixed shift-by-1, not dynamic.
        py4hw.ShiftLeftConstant(self, "FMULS_Shift", self.w_muls16, 1, self.w_fmuls16)
        self.w_fmuls_l = self.wire("w_fmuls_l", 8)
        self.w_fmuls_h = self.wire("w_fmuls_h", 8)
        py4hw.Range(self, "fmuls_low", self.w_fmuls16, 7, 0, self.w_fmuls_l)
        py4hw.Range(self, "fmuls_high", self.w_fmuls16, 15, 8, self.w_fmuls_h)

        # MULSU: RegAL (Rd) is signed, RegBL (Rr) is unsigned -- SignedMul
        # treats both operands as signed per their wire width, so RegBL
        # must first be widened to 9 bits with its sign bit forced to 0
        # (ZeroExtend), which preserves its 0-255 magnitude as a
        # non-negative 9-bit signed value; RegAL is widened to 9 bits via
        # SignExtend to preserve its actual sign. Product range
        # (-128*255..127*255) fits comfortably in 16 bits.
        self.w_regA_9s = self.wire("w_regA_9s", 9)
        self.w_regB_9u = self.wire("w_regB_9u", 9)
        py4hw.SignExtend(self, "MULSU_SignExtA", self.RegAL, self.w_regA_9s)
        py4hw.ZeroExtend(self, "MULSU_ZeroExtB", self.RegBL, self.w_regB_9u)
        self.w_mulsu16 = self.wire("w_mulsu16", 16)
        py4hw.SignedMul(self, "MULSU_Unit", self.w_regA_9s, self.w_regB_9u, self.w_mulsu16)
        self.w_mulsu_l = self.wire("w_mulsu_l", 8)
        self.w_mulsu_h = self.wire("w_mulsu_h", 8)
        py4hw.Range(self, "mulsu_low", self.w_mulsu16, 7, 0, self.w_mulsu_l)
        py4hw.Range(self, "mulsu_high", self.w_mulsu16, 15, 8, self.w_mulsu_h)
        self.w_mulsu_carry = self.wire("w_mulsu_carry", 1)
        py4hw.Range(self, "mulsu_carry_ext", self.w_mulsu16, 15, 15, self.w_mulsu_carry)

        self.w_fmulsu16 = self.wire("w_fmulsu16", 16)
        # Same fix as FMUL_Shift above -- fixed shift-by-1, not dynamic.
        py4hw.ShiftLeftConstant(self, "FMULSU_Shift", self.w_mulsu16, 1, self.w_fmulsu16)
        self.w_fmulsu_l = self.wire("w_fmulsu_l", 8)
        self.w_fmulsu_h = self.wire("w_fmulsu_h", 8)
        py4hw.Range(self, "fmulsu_low", self.w_fmulsu16, 7, 0, self.w_fmulsu_l)
        py4hw.Range(self, "fmulsu_high", self.w_fmulsu16, 15, 8, self.w_fmulsu_h)

        # -------------------------------------------------------------
        # 4. MUX ARRAY CONSTRUCTION (Map to max opcode 93)
        # -------------------------------------------------------------
        MUX_SIZE = 128
        
        # Initialize default routes to zero
        res_l_inputs = [self.w_zero8] * MUX_SIZE
        res_h_inputs = [self.w_zero8] * MUX_SIZE
        mul_carry_inputs = [self.w_zero1] * MUX_SIZE

        # Route arithmetic & word ops
        res_l_inputs[1] = self.w_add       # ADD
        res_l_inputs[2] = self.w_adc       # ADC
        for op in (4, 5, 38, 40): res_l_inputs[op] = self.w_sub       # SUB, SUBI, CP, CPI
        for op in (6, 7, 39): res_l_inputs[op] = self.w_sbc       # SBC, SBCI, CPC
        res_l_inputs[18] = self.w_inc      # INC
        res_l_inputs[19] = self.w_dec      # DEC
        
        res_l_inputs[3] = self.w_adiw_l    # ADIW (Low)
        res_h_inputs[3] = self.w_adiw_h    # ADIW (High)
        res_l_inputs[8] = self.w_sbiw_l    # SBIW (Low)
        res_h_inputs[8] = self.w_sbiw_h    # SBIW (High)

        # Route logic ops
        for op in (9, 10, 20): res_l_inputs[op] = self.w_and      # AND, ANDI, TST
        for op in (11, 12, 16): res_l_inputs[op] = self.w_or       # OR, ORI, SBR
        for op in (13, 21): res_l_inputs[op] = self.w_xor      # EOR, CLR
        res_l_inputs[14] = self.w_com      # COM
        res_l_inputs[15] = self.w_neg      # NEG
        res_l_inputs[17] = self.w_cbr      # CBR
        res_l_inputs[22] = self.w_ff       # SER 

        # Route shifts & bit ops
        res_l_inputs[65] = self.w_sbi      # SBI
        res_l_inputs[66] = self.w_cbi      # CBI
        res_l_inputs[76] = self.w_bld      # BLD
        res_l_inputs[67] = self.w_lsl      # LSL
        res_l_inputs[68] = self.w_lsr      # LSR
        res_l_inputs[69] = self.w_rol      # ROL
        res_l_inputs[70] = self.w_ror      # ROR
        res_l_inputs[71] = self.w_asr      # ASR
        res_l_inputs[72] = self.w_swap     # SWAP

        # Data Transfer
        res_l_inputs[93] = self.RegBL      # MOV 

        # Route Multipliers
        res_l_inputs[23] = self.w_mul_l     # MUL (unsigned x unsigned)
        res_h_inputs[23] = self.w_mul_h
        mul_carry_inputs[23] = self.w_mul_carry

        res_l_inputs[24] = self.w_muls_l    # MULS (signed x signed)
        res_h_inputs[24] = self.w_muls_h
        mul_carry_inputs[24] = self.w_muls_carry

        res_l_inputs[25] = self.w_mulsu_l   # MULSU (signed x unsigned)
        res_h_inputs[25] = self.w_mulsu_h
        mul_carry_inputs[25] = self.w_mulsu_carry

        res_l_inputs[26] = self.w_fmul_l    # FMUL (unsigned x unsigned, <<1)
        res_h_inputs[26] = self.w_fmul_h
        mul_carry_inputs[26] = self.w_mul_carry   # carry = bit15 of PRE-shift product

        res_l_inputs[27] = self.w_fmuls_l   # FMULS (signed x signed, <<1)
        res_h_inputs[27] = self.w_fmuls_h
        mul_carry_inputs[27] = self.w_muls_carry

        res_l_inputs[28] = self.w_fmulsu_l  # FMULSU (signed x unsigned, <<1)
        res_h_inputs[28] = self.w_fmulsu_h
        mul_carry_inputs[28] = self.w_mulsu_carry

        # -------------------------------------------------------------
        # 5. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        # FIX: two bugs, same family as ALU_ConfCodeCalc_STRUC's Mux calls --
        # (a) args were passed (ins, sel, r) instead of py4hw.Mux's actual
        #     (parent, name, sel, ins, r) order, and
        # (b) self.Operation is an 8-bit wire but MUX_SIZE=128 needs a
        #     7-bit sel (log2(128)=7). Values on Operation never exceed
        #     127 (max routed index above is 93), so bit 7 is always 0 --
        #     slicing to bits [6:0] is lossless.
        self.w_op_sel7 = self.wire("w_op_sel7", 7)
        py4hw.Range(self, "Range_OpSel", self.Operation, 6, 0, self.w_op_sel7)
        py4hw.Mux(self, "Main_Mux_ResL", self.w_op_sel7, res_l_inputs, self.ResL)
        py4hw.Mux(self, "Main_Mux_ResH", self.w_op_sel7, res_h_inputs, self.ResH)
        py4hw.Mux(self, "Main_Mux_MulC", self.w_op_sel7, mul_carry_inputs, self.MulCarryOut)