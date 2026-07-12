import py4hw

class HandleH(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Rr, Rd, Res, Mode,
                 Hout):
        super().__init__(parent, name)

        # Inputs
        self.Rr = self.addIn('Rr', Rr)
        self.Rd = self.addIn('Rd', Rd)
        self.Res = self.addIn('Res', Res)
        self.Mode = self.addIn('Mode', Mode)

        # Output
        self.Hout = self.addOut('Hout', Hout)

    def propagate(self):
        # 1. Read input values
        rr = self.Rr.get()
        rd = self.Rd.get()
        res = self.Res.get()
        mode = self.Mode.get()

        # 2. Extract strictly Bit 3 for Half-Carry calculations
        rd3 = (rd >> 3) & 1   # Bit 3 of Destination Register
        rr3 = (rr >> 3) & 1   # Bit 3 of Source Register
        r3  = (res >> 3) & 1  # Bit 3 of Result

        not_rd3 = (~rd3) & 1
        not_r3  = (~r3) & 1

        # Default H Out
        h_out = 0

        # 3. Mode Routing
        if mode == 0:
            # Mode 0: Force Clear (CLH instruction)
            h_out = 0
            
        elif mode == 1:
            # Mode 1: Force Set (SEH instruction)
            h_out = 1

        elif mode == 2:
            # Mode 1: Addition (ADD, ADC)
            # H = (Rd3 AND Rr3) OR (Rr3 AND NOT R3) OR (NOT R3 AND Rd3)
            h_out = (rd3 & rr3) | (rr3 & not_r3) | (not_r3 & rd3)

        elif mode == 3:
            # Mode 2: Subtraction / Compare / Negate (SUB, SBC, CP, CPC, NEG)
            # H = (NOT Rd3 AND Rr3) OR (Rr3 AND R3) OR (R3 AND NOT Rd3)
            h_out = (not_rd3 & rr3) | (rr3 & r3) | (r3 & not_rd3)

        # Note: Instructions like INC, DEC, Shifts, Word operations, and Logical ops 
        # do not update the H flag in AVR. Your ConfCodeCalc handles this by 
        # outputting hen = 0, so whatever h_out produces here is safely ignored.

        # 4. Output the calculated bit
        self.Hout.put(h_out & 1)