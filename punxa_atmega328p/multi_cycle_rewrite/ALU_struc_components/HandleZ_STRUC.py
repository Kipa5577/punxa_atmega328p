import py4hw

class HandleZ_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Res, Mode, Zprev, Zout):
        super().__init__(parent, name)
        
        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.Res = self.addIn('Res', Res)
        self.Mode = self.addIn('Mode', Mode)
        self.Zprev = self.addIn('Zprev', Zprev)
        
        self.Zout = self.addOut('Zout', Zout)

        # -------------------------------------------------------------
        # 2. CONSTANTS & UTILITY WIRES
        # -------------------------------------------------------------
        self.w_zero1 = self.wire("w_zero1", 1)
        self.w_one1 = self.wire("w_one1", 1)
        self.w_zero8 = self.wire("w_zero8", 8)
        self.w_zero16 = self.wire("w_zero16", 16)
        
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)
        py4hw.Constant(self, "Const1_1", 1, self.w_one1)
        py4hw.Constant(self, "Const0_8", 0, self.w_zero8)
        py4hw.Constant(self, "Const0_16", 0, self.w_zero16)

        # -------------------------------------------------------------
        # 3. STRUCTURAL DATAPATHS (All execute continuously in parallel)
        # -------------------------------------------------------------
        
        # Extract the lower 8 bits from the result (for 8-bit operations)
        self.w_res_l = self.wire("w_res_l", 8)
        py4hw.Range(self, "Res_Low_Byte", self.Res, 7, 0, self.w_res_l)

        # Zero Detector 1: 8-bit Result == 0
        self.w_z_8 = self.wire("w_z_8", 1)
        py4hw.Equal(self, "Eq_8bit", self.w_res_l, self.w_zero8, self.w_z_8)

        # Zero Detector 2: 16-bit Result == 0
        self.w_z_16 = self.wire("w_z_16", 1)
        py4hw.Equal(self, "Eq_16bit", self.Res, self.w_zero16, self.w_z_16)

        # Chained Zero (SBC/CPC): Z_prev AND (8-bit Result == 0)
        self.w_z_chained = self.wire("w_z_chained", 1)
        py4hw.And2(self, "And_ChainedZ", self.Zprev, self.w_z_8, self.w_z_chained)

        # -------------------------------------------------------------
        # 4. MUX ARRAY CONSTRUCTION
        # -------------------------------------------------------------
        # The Mode signal ranges from 0 to 5. We use an 8-element array for safety.
        MUX_SIZE = 8
        
        # Initialize default routes to 0
        z_inputs = [self.w_zero1] * MUX_SIZE

        # Route computed 1-bit wires to their exact Mode indices
        z_inputs[0] = self.w_zero1       # Mode 0: Explicit Clear (CLZ) -> 0
        z_inputs[1] = self.w_one1        # Mode 1: Explicit Set (SEZ) -> 1
        z_inputs[2] = self.w_z_8         # Mode 2: 8-bit standard
        z_inputs[3] = self.w_z_16        # Mode 3: 16-bit standard
        z_inputs[4] = self.w_z_chained   # Mode 4: Chained 8-bit Subtraction
        z_inputs[5] = self.w_z_chained   # Mode 5: Identical to Mode 4

        # -------------------------------------------------------------
        # 5. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        # Dynamically selects the appropriate Z flag evaluation based on 'Mode'
        py4hw.Mux(self, "Mux_Zout", self.Mode, z_inputs, self.Zout)