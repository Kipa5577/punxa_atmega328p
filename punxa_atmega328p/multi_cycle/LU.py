import py4hw

class BranchUnit(py4hw.Logic):
    def __init__(self, parent, name: str, 
                 SREG, RegisterToTest, IORegisterToTest, Bit, Operation, 
                 Skip, Branch):
        super().__init__(parent, name)

        # Inputs (Matches the left side of the second image)
        self.SREG = self.addIn('SREG', SREG)
        self.RegisterToTest = self.addIn('RegisterToTest', RegisterToTest)
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
        io_reg = self.IORegisterToTest.get()
        bit_idx = self.Bit.get()
        op = self.Operation.get()

        # Extract individual bits from the Operation code (0-5)
        # Op[0]: 0=Clear check, 1=Set check
        # Op[1]: 0=RegisterToTest, 1=IORegisterToTest
        # Op[2]: 0=Skip instruction, 1=Branch instruction
        op_bit0 = op & 1
        op_bit1 = (op >> 1) & 1
        op_bit2 = (op >> 2) & 1

        # 2. First Stage: Register vs I/O Register Multiplexer
        selected_reg = io_reg if op_bit1 else reg

        # 3. Bit Extractors (Simulates the 'Sel' blocks)
        # Extracts the single bit at index 'bit_idx' from the 8-bit buses
        sreg_bit_val = (sreg >> bit_idx) & 1
        reg_bit_val = (selected_reg >> bit_idx) & 1

        # 4. Set or Clear Select Multiplexers
        # If op_bit0 is 0 (Clear check), invert the bit (1 - bit_val)
        # If op_bit0 is 1 (Set check), pass the bit as is
        branch_cond = sreg_bit_val if op_bit0 else (1 - sreg_bit_val)
        skip_cond = reg_bit_val if op_bit0 else (1 - reg_bit_val)

        # 5. Output Routing (Final AND gates mapping to Skip or Branch)
        # Op[2] routes the signal to Branch; inverted Op[2] routes to Skip
        skip_out = skip_cond if (not op_bit2) else 0
        branch_out = branch_cond if op_bit2 else 0

        # Output the final evaluated signals
        self.Skip.put(skip_out)
        self.Branch.put(branch_out)