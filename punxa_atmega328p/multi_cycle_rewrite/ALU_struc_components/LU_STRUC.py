import py4hw

class BranchUnit_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str, 
                 SREG, RegisterToTest, RegisterB, IORegisterToTest, Bit, Operation, 
                 Skip, Branch):
        super().__init__(parent, name)

        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.SREG = self.addIn('SREG', SREG)
        self.RegisterToTest = self.addIn('RegisterToTest', RegisterToTest)
        self.RegisterB = self.addIn('RegisterB', RegisterB)
        self.IORegisterToTest = self.addIn('IORegisterToTest', IORegisterToTest)
        self.Bit = self.addIn('Bit', Bit)
        self.Operation = self.addIn('Operation', Operation)

        self.Skip = self.addOut('Skip', Skip)
        self.Branch = self.addOut('Branch', Branch)

        # -------------------------------------------------------------
        # 2. CONSTANTS
        # -------------------------------------------------------------
        self.w_zero1 = self.wire("w_zero1", 1)
        py4hw.Constant(self, "Const0_1", 0, self.w_zero1)

        # -------------------------------------------------------------
        # 3. STRUCTURAL BIT EXTRACTIONS (Dynamic via 'Bit' input)
        # -------------------------------------------------------------
        
        # Split SREG into 8 wires and MUX to get the target bit
        self.sreg_bits = [self.wire(f"w_sreg_bit_{i}", 1) for i in range(8)]
        py4hw.BitsLSBF(self, "Split_SREG", self.SREG, self.sreg_bits)
        self.w_sreg_bit = self.wire("w_sreg_bit", 1)
        py4hw.Mux(self, "Mux_SREG_Bit", self.Bit, self.sreg_bits, self.w_sreg_bit)

        # Split RegisterToTest into 8 wires and MUX to get the target bit
        self.reg_bits = [self.wire(f"w_reg_bit_{i}", 1) for i in range(8)]
        py4hw.BitsLSBF(self, "Split_Reg", self.RegisterToTest, self.reg_bits)
        self.w_reg_bit = self.wire("w_reg_bit", 1)
        py4hw.Mux(self, "Mux_Reg_Bit", self.Bit, self.reg_bits, self.w_reg_bit)

        # Split IORegisterToTest into 8 wires and MUX to get the target bit
        self.io_bits = [self.wire(f"w_io_bit_{i}", 1) for i in range(8)]
        py4hw.BitsLSBF(self, "Split_IO", self.IORegisterToTest, self.io_bits)
        self.w_io_bit = self.wire("w_io_bit", 1)
        py4hw.Mux(self, "Mux_IO_Bit", self.Bit, self.io_bits, self.w_io_bit)

        # -------------------------------------------------------------
        # 4. INVERSIONS AND EQUALITY DATAPATHS
        # -------------------------------------------------------------
        
        self.w_not_sreg_bit = self.wire("w_not_sreg_bit", 1)
        py4hw.Not(self, "Not_SREG_Bit", self.w_sreg_bit, self.w_not_sreg_bit)

        self.w_not_reg_bit = self.wire("w_not_reg_bit", 1)
        py4hw.Not(self, "Not_Reg_Bit", self.w_reg_bit, self.w_not_reg_bit)

        self.w_not_io_bit = self.wire("w_not_io_bit", 1)
        py4hw.Not(self, "Not_IO_Bit", self.w_io_bit, self.w_not_io_bit)

        # Full-byte equality check for CPSE (Skip if Rd == Rr)
        self.w_cpse_skip = self.wire("w_cpse_skip", 1)
        py4hw.Equal(self, "Eq_CPSE", self.RegisterToTest, self.RegisterB, self.w_cpse_skip)

        # -------------------------------------------------------------
        # 5. MUX ARRAY CONSTRUCTION
        # -------------------------------------------------------------
        # The Operation signal ranges from 0 to 7, so an 8-element array is needed.
        MUX_SIZE = 8
        
        # Initialize default routes to 0
        branch_inputs = [self.w_zero1] * MUX_SIZE
        skip_inputs = [self.w_zero1] * MUX_SIZE

        # Route computed branch signals
        branch_inputs[1] = self.w_sreg_bit       # BRBS (Branch if SREG bit is set)
        branch_inputs[2] = self.w_not_sreg_bit   # BRBC (Branch if SREG bit is clear)

        # Route computed skip signals
        skip_inputs[3] = self.w_not_reg_bit      # SBRC (Skip if Register bit is clear)
        skip_inputs[4] = self.w_reg_bit          # SBRS (Skip if Register bit is set)
        skip_inputs[5] = self.w_not_io_bit       # SBIC (Skip if IO Register bit is clear)
        skip_inputs[6] = self.w_io_bit           # SBIS (Skip if IO Register bit is set)
        skip_inputs[7] = self.w_cpse_skip        # CPSE (Skip if RegisterToTest == RegisterB)

        # -------------------------------------------------------------
        # 6. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        py4hw.Mux(self, "Mux_Skip", self.Operation, skip_inputs, self.Skip)
        py4hw.Mux(self, "Mux_Branch", self.Operation, branch_inputs, self.Branch)