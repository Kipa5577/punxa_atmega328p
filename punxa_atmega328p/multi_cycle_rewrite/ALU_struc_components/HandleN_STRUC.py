import py4hw

class HandleN_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Res, Mode,
                 Nout):
        super().__init__(parent, name)

        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.Res = self.addIn('Res', Res)
        self.Mode = self.addIn('Mode', Mode)

        self.Nout = self.addOut('Nout', Nout)

        # -------------------------------------------------------------
        # 2. CONSTANTS
        # -------------------------------------------------------------
        self.w_zero1 = self.wire("w_zero1", 1)
        self.w_one1 = self.wire("w_one1", 1)
        
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)
        py4hw.Constant(self, "Const1_1", 1, self.w_one1)

        # -------------------------------------------------------------
        # 3. STRUCTURAL DATAPATHS (Bit Extractions)
        # -------------------------------------------------------------
        
        # Mode 2: 8-bit MSB (Bit 7)
        self.w_n8 = self.wire("w_n8", 1)
        py4hw.Range(self, "Rng_Bit7", self.Res, 7, 7, self.w_n8)

        # Mode 3: 16-bit MSB (Bit 15)
        self.w_n16 = self.wire("w_n16", 1)
        py4hw.Range(self, "Rng_Bit15", self.Res, 15, 15, self.w_n16)

        # -------------------------------------------------------------
        # 4. MUX ARRAY CONSTRUCTION
        # -------------------------------------------------------------
        # The Mode signal ranges from 0 to 3 in practice, but the incoming
        # wire (w_nopp in ALU_STRUC) is declared 3 bits wide (matching its
        # sibling opp signals), so the Mux selector is 3 bits -- the array
        # must be sized 8 (2**3), not 4, or py4hw.Mux rejects the width
        # mismatch. Indices 4-7 are unused/unreachable in practice.
        n_inputs = [
            self.w_zero1, # Mode 0: Force Clear (CLN)
            self.w_one1,  # Mode 1: Force Set (SEN)
            self.w_n8,    # Mode 2: Standard 8-bit Signed Operations
            self.w_n16,   # Mode 3: 16-bit Word/Multiply Operations
            self.w_zero1, self.w_zero1, self.w_zero1, self.w_zero1,  # unused
        ]

        # -------------------------------------------------------------
        # 5. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        py4hw.Mux(self, "Mux_Nout", self.Mode, n_inputs, self.Nout)