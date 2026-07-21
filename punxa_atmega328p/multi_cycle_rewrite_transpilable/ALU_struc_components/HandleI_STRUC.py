import py4hw

class HandleI_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str, Mode, Iout):
        super().__init__(parent, name)

        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.Mode = self.addIn('Mode', Mode)
        self.Iout = self.addOut('Iout', Iout)

        # -------------------------------------------------------------
        # 2. CONSTANTS
        # -------------------------------------------------------------
        self.w_zero1 = self.wire("w_zero1", 1)
        self.w_one1 = self.wire("w_one1", 1)
        
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)
        py4hw.Constant(self, "Const1_1", 1, self.w_one1)

        # -------------------------------------------------------------
        # 3. MUX ARRAY CONSTRUCTION
        # -------------------------------------------------------------
        # Since Mode only goes up to 1 for this flag, a 2-element array is all we need.
        i_inputs = [
            self.w_zero1, # Mode 0: Force Clear (CLI instruction)
            self.w_one1   # Mode 1: Force Set (SEI instruction)
        ]

        # -------------------------------------------------------------
        # 4. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        py4hw.Mux(self, "Mux_Iout", self.Mode, i_inputs, self.Iout)