import py4hw

class HandleT_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Rr, BitPos, Mode,
                 Tout):
        super().__init__(parent, name)

        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.Rr = self.addIn('Rr', Rr)
        self.BitPos = self.addIn('BitPos', BitPos)
        self.Mode = self.addIn('Mode', Mode)
        
        self.Tout = self.addOut('Tout', Tout)

        # -------------------------------------------------------------
        # 2. CONSTANTS
        # -------------------------------------------------------------
        self.w_zero1 = self.wire("w_zero1", 1)
        self.w_one1 = self.wire("w_one1", 1)
        
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)
        py4hw.Constant(self, "Const1_1", 1, self.w_one1)

        # -------------------------------------------------------------
        # 3. STRUCTURAL DATAPATHS
        # -------------------------------------------------------------
        
        # Mode 2: Bit Store (BST). 
        # Unpack the 8-bit Rr wire into an array of 8 individual 1-bit wires.
        # BitsLSBF maps index 0 to the Least Significant Bit.
        self.rr_bits = [self.wire(f"w_rr_bit_{i}", 1) for i in range(8)]
        py4hw.BitsLSBF(self, "Split_Rr", self.Rr, self.rr_bits)
        
        # Feed the unpacked array into a Multiplexer. 
        # BitPos will select exactly the right bit wire from the array.
        self.w_bst = self.wire("w_bst", 1)
        py4hw.Mux(self, "Mux_BST_BitSelect", self.BitPos, self.rr_bits, self.w_bst)

        # -------------------------------------------------------------
        # 4. MUX ARRAY CONSTRUCTION (Main Mode Selector)
        # -------------------------------------------------------------
        # Max mode is 2, a 4-element array handles this safely
        MUX_SIZE = 4
        
        # Initialize default routes to 0
        t_inputs = [self.w_zero1] * MUX_SIZE

        # Route computed 1-bit wires to their exact Mode indices
        t_inputs[0] = self.w_zero1       # Mode 0: Force Clear (CLT)
        t_inputs[1] = self.w_one1        # Mode 1: Force Set (SET)
        t_inputs[2] = self.w_bst         # Mode 2: Bit Store (BST)

        # -------------------------------------------------------------
        # 5. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        py4hw.Mux(self, "Mux_Tout", self.Mode, t_inputs, self.Tout)