import py4hw

class AU(py4hw.Logic): 
    def __init__(self, parent, name: str,
                 Cval, RegAL, RegAH, RegBL, RegBH, Operation,
                 ResL, ResH):
        super().__init__(parent, name)

        # Inputs
        self.Cval = self.addIn('Cval', Cval)
        self.RegAL = self.addIn('RegAL', RegAL)
        self.RegAH = self.addIn('RegAH', RegAH)
        self.RegBL = self.addIn('RegBL', RegBL)
        self.RegBH = self.addIn('RegBH', RegBH)
        self.Operation = self.addIn('Operation', Operation)

        # Outputs 
        self.ResL = self.addOut('ResL', ResL)
        self.ResH = self.addOut('ResH', ResH)

    def propagate(self): 
        # Retrieve current values from pins
        op = self.Operation.get()
        A = self.RegAL.get()
        B = self.RegBL.get()
        C = self.Cval.get()
        
        # 16-bit word concatenation for ADIW / SBIW
        word_A = A | (self.RegAH.get() << 8)
        word_B = B | (self.RegBH.get() << 8)

        # Default results
        res_l = 0
        res_h = 0

        # --- ARITHMETIC INSTRUCTIONS ---
        if op == 0:   # IDLE / No Operation
            pass      # Output remains 0
            
        elif op == 1: # ADD 
            res_l = A + B
            
        elif op == 2: # ADC
            res_l = A + B + C
            
        elif op in (4, 5, 38, 40): # SUB / SUBI / CP / CPI
            res_l = A - B
            
        elif op in (6, 7, 39): # SBC / SBCI / CPC
            res_l = A - B - C
            
        elif op == 3: # ADIW
            res16 = word_A + word_B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 8: # SBIW 
            res16 = word_A - word_B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF

        # --- LOGIC INSTRUCTIONS ---
        elif op in (9, 10, 20): # AND / ANDI / TST
            res_l = A & B
            
        elif op in (11, 12, 16): # OR / ORI / SBR
            res_l = A | B
            
        elif op in (13, 21): # EOR / CLR
            res_l = A ^ B
            
        elif op == 14: # COM (One's complement)
            res_l = 0xFF - A
            
        elif op == 15: # NEG (Two's complement)
            res_l = 0x00 - A
            
        elif op == 17: # CBR (Clear bits)
            res_l = A & (0xFF - B)
            
        elif op == 18: # INC
            res_l = A + 1
            
        elif op == 19: # DEC
            res_l = A - 1
            
        elif op == 22: # SER (Set Register)
            res_l = 0xFF

        # --- MULTIPLY INSTRUCTIONS ---
        elif op == 23: # MUL (Unsigned)
            res16 = A * B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 24: # MULS (Signed)
            # Convert 8-bit unsigned to signed integers in Python
            signed_A = A if A < 128 else A - 256
            signed_B = B if B < 128 else B - 256
            res16 = signed_A * signed_B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 25: # MULSU (Signed A * Unsigned B)
            signed_A = A if A < 128 else A - 256
            res16 = signed_A * B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 26: # FMUL (Fractional Unsigned)
            res16 = (A * B) << 1
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 27: # FMULS (Fractional Signed)
            signed_A = A if A < 128 else A - 256
            signed_B = B if B < 128 else B - 256
            res16 = (signed_A * signed_B) << 1
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 28: # FMULSU (Fractional Signed A * Unsigned B)
            signed_A = A if A < 128 else A - 256
            res16 = (signed_A * B) << 1
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op in (73, 74): # BSET / BCLR 
            pass # No arithmetic needed for flag-only operations

        # Output the results (Masked to 8 bits to simulate hardware registers)
        self.ResL.put(res_l & 0xFF)
        
        # Word and Multiply operations populate High byte; others zero it out
        # Mapped to: ADIW(3), SBIW(8), MUL(23), MULS(24), MULSU(25), FMUL(26), FMULS(27), FMULSU(28)
        if op in [3, 8, 23, 24, 25, 26, 27, 28]:
            self.ResH.put(res_h & 0xFF)
        else:
            self.ResH.put(0)