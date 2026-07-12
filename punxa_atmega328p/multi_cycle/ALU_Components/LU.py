import py4hw

class BranchUnit(py4hw.Logic):
    def __init__(self, parent, name: str, 
                 SREG, RegisterToTest, RegisterB, IORegisterToTest, Bit, Operation, 
                 Skip, Branch):
        super().__init__(parent, name)

        # Inputs (Matches the left side of the second image)
        self.SREG = self.addIn('SREG', SREG)
        self.RegisterToTest = self.addIn('RegisterToTest', RegisterToTest)
        # Second operand register (Rr), needed only for CPSE's Rd==Rr
        # comparison. Every other skip/branch op ignores this input.
        self.RegisterB = self.addIn('RegisterB', RegisterB)
        self.IORegisterToTest = self.addIn('IORegisterToTest', IORegisterToTest)
        self.Bit = self.addIn('Bit', Bit)
        self.Operation = self.addIn('Operation', Operation)

        # Outputs (Matches the right side of the second image)
        self.Skip = self.addOut('Skip', Skip)
        self.Branch = self.addOut('Branch', Branch)

    def propagate(self):
        # 1. Fetch current values
        sreg = self.SREG.get()
        reg = self.RegisterToTest.get()
        reg_b = self.RegisterB.get()
        io_reg = self.IORegisterToTest.get()
        bit_idx = self.Bit.get()
        op = self.Operation.get()

        skip_out = 0
        branch_out = 0

        sreg_bit = (sreg >> bit_idx) & 1
        reg_bit = (reg >> bit_idx) & 1
        io_bit = (io_reg >> bit_idx) & 1
        
        # BRBS - Branch if bit in SREG is set
        if op == 1:
            branch_out = sreg_bit

        # BRBC - Branch if bit in SREG is clear
        elif op == 2:
            branch_out = 1 - sreg_bit

        # SBRC - Skip if bit in register is clear
        elif op == 3:
            skip_out = 1 - reg_bit

        # SBRS - Skip if bit in register is set
        elif op == 4:
            skip_out = reg_bit

        # SBIC - Skip if bit in I/O register is clear
        elif op == 5:
            skip_out = 1 - io_bit

        # SBIS - Skip if bit in I/O register is set
        elif op == 6:
            skip_out = io_bit

        # CPSE - Skip if Rd == Rr (full-byte comparison, not bit-indexed)
        elif op == 7:
            skip_out = 1 if reg == reg_b else 0

        self.Skip.put(skip_out)
        self.Branch.put(branch_out)