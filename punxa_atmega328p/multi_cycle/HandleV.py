import py4hw

class HandleV(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Rr, Rd, Res, N, Mode,
                 Vout):
        super().__init__(parent, name)

        # Inputs
        self.Rr = self.addIn('Rr', Rr)
        self.Rd = self.addIn('Rd', Rd)
        self.Res = self.addIn('Res', Res)
        self.N = self.addIn('N', N)
        self.Mode = self.addIn('Mode', Mode)
        
        # Output
        self.Vout = self.addOut('Vout', Vout)

    def propagate(self):
        # 1. Read input values
        rr = self.Rr.get()
        rd = self.Rd.get()
        res = self.Res.get()
        n_flag = self.N.get()
        mode = self.Mode.get()

        # 2. Extract specific bits for 8-bit operations
        rd7 = (rd >> 7) & 1   # MSB of Destination Register
        rr7 = (rr >> 7) & 1   # MSB of Source Register
        r7  = (res >> 7) & 1  # MSB of Result

        not_rd7 = (~rd7) & 1
        not_rr7 = (~rr7) & 1
        not_r7  = (~r7) & 1

        # 3. Extract specific bits for 16-bit operations (Word Math)
        rd15 = (rd >> 15) & 1 # 16-bit MSB of Destination
        r15  = (res >> 15) & 1 # 16-bit MSB of Result
        
        not_rd15 = (~rd15) & 1
        not_r15  = (~r15) & 1

        # Default V Out
        v_out = 0

        # 4. Mode Routing
        if mode == 0:
            # Mode 0: Force Clear (CLV, AND, OR, EOR, COM)
            v_out = 0

        elif mode == 1:
            # Mode 1: Force Set (SEV)
            v_out = 1

        elif mode == 2:
            # Mode 1: 8-bit Addition (ADD, ADC)
            v_out = (rd7 & rr7 & not_r7) | (not_rd7 & not_rr7 & r7)

        elif mode == 3:
            # Mode 2: 8-bit Subtraction / Compare (SUB, SBC, CP, CPC)
            v_out = (rd7 & not_rr7 & not_r7) | (not_rd7 & rr7 & r7)

        elif mode == 4:
            # Mode 3: 16-bit Addition (ADIW)
            v_out = not_rd15 & r15

        elif mode == 5:
            # Mode 13: 16-bit Subtraction (SBIW)
            v_out = rd15 & not_r15

        elif mode == 6 or mode == 7:
            # Mode 5/6: Two's Complement Negation (NEG) and Increment (INC)
            v_out = 1 if (res & 0xFF) == 0x80 else 0

        elif mode == 9:
            # Mode 7: Decrement (DEC)
            v_out = 1 if (res & 0xFF) == 0x7F else 0

        # 5. Output calculated bit
        self.Vout.put(v_out & 1)