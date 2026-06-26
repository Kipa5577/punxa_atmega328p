import py4hw

class HandleC(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Rr, Rd, Res, Mode,
                 Cout):
        super().__init__(parent, name)

        self.Rr = self.addIn('Rr', Rr)
        self.Rd = self.addIn('Rd', Rd)
        self.Res = self.addIn('Res', Res)
        self.Mode = self.addIn('Mode', Mode)
        
        self.Cout = self.addOut('Cout', Cout)

    def propagate(self):
        # 1. Read input values
        rr = self.Rr.get()
        rd = self.Rd.get()
        res = self.Res.get()
        mode = self.Mode.get()

        # 2. Extract specific bits for 8-bit operations
        rd7 = (rd >> 7) & 1   # MSB of Destination Register
        rr7 = (rr >> 7) & 1   # MSB of Source Register
        r7  = (res >> 7) & 1  # MSB of Result
        
        rd0 = rd & 1          # LSB of Destination (used for Shifts)

        # 3. Extract specific bits for 16-bit operations (Word / MUL)
        rd15 = (rd >> 15) & 1 # 16-bit MSB of Destination
        r15  = (res >> 15) & 1 # 16-bit MSB of Result

        # Default Carry Out
        c_out = 0

        # 4. Mode Routing
        if mode == 0:
            # Mode 0: Explicit Clear (CLC)
            c_out = 0

        if mode == 1:
            # Mode 1: Explicit Set (SEC)
            c_out = 1

        elif mode == 2:
            # Mode 2: 8-bit Addition (ADD, ADC)
            not_r7 = (~r7) & 1
            c_out = (rd7 & rr7) | (rr7 & not_r7) | (not_r7 & rd7)

        elif mode == 3:
            # Mode 3: 8-bit Subtraction / Compare (SUB, SBC, CP, CPC)
            not_rd7 = (~rd7) & 1
            c_out = (not_rd7 & rr7) | (rr7 & r7) | (r7 & not_rd7)

        elif mode == 4:
            # Mode 4: 16-bit Addition (ADIW)
            not_r15 = (~r15) & 1
            c_out = not_r15 & rd15

        elif mode == 5:
            # Mode 5: 16-bit Subtraction (SBIW)
            not_rd15 = (~rd15) & 1
            c_out = r15 & not_rd15

        elif mode == 6:
            # Mode 6: Force Carry to 1 (COM instruction)
            c_out = 1

        elif mode == 7:
            # Mode 7: Two's Complement Negation (NEG)
            # Carry is set if the result is NOT exactly 0x00
            c_out = 1 if (res & 0xFF) != 0 else 0

        elif mode == 8:
            # Mode 8: Multiplication (MUL)
            # Carry takes the 15th bit of the 16-bit result
            c_out = r15
            
        elif mode == 9:
            # Mode 9: Shift Right (LSR, ROR, ASR)
            # LSB of the original register is shifted into the Carry flag
            c_out = rd0
            
        elif mode == 10:
            # Mode 10: Shift Left (LSL, ROL)
            # MSB of the original register is shifted into the Carry flag
            c_out = rd7

        # 5. Put calculated bit on the output wire
        self.Cout.put(c_out & 1)