import py4hw



class ALU_ConfCodeCalc(py4hw.Logic):
    def __init__(self,parent,name:str,
                 Cval,RegAL,RegAH,RegBL,RegBH,Operation,
                 ResL,ResH):
        super().__init__(parent,name)

        self.Cval = self.addIn('Cval',Cval)
        self.RegAL = self.addIn('RegAL',RegAL)
        self.RegAH = self.addIn('RegAH',RegAH)
        self.RegBL = self.addIn('RegBL',RegBL)
        self.RegBH = self.addIn('RegBH',RegBH)
        self.Operation =  self.addIn('Operation',Operation)

        self.ResL = self.addIn('ResL',ResL)
        self.ResH = self.addIn('ResH',ResH)

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
        if op == 0:   # ADD
            res_l = A + B
        elif op == 1: # ADC
            res_l = A + B + C
        elif op == 2: # SUB / SUBI
            res_l = A - B
        elif op == 3: # SBC / SBCI
            res_l = A - B - C
        elif op == 4: # ADIW
            res16 = word_A + word_B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
        elif op == 5: # SBIW (Fixed from addition)
            res16 = word_A - word_B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF

        # --- LOGIC INSTRUCTIONS ---
        elif op == 6: # AND / ANDI / TST
            res_l = A & B
        elif op == 7: # OR / ORI / SBR
            res_l = A | B
        elif op == 8: # EOR / CLR
            res_l = A ^ B
        elif op == 9: # COM (One's complement)
            res_l = 0xFF - A
        elif op == 10: # NEG (Two's complement)
            res_l = 0x00 - A
        elif op == 11: # CBR (Clear bits)
            res_l = A & (0xFF - B)
        elif op == 12: # INC
            res_l = A + 1
        elif op == 13: # DEC
            res_l = A - 1
        elif op == 14: # SER (Set Register)
            res_l = 0xFF

        # --- MULTIPLY INSTRUCTIONS ---
        elif op == 15: # MUL (Unsigned)
            res16 = A * B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 16: # MULS (Signed)
            # Convert 8-bit unsigned to signed integers in Python
            signed_A = A if A < 128 else A - 256
            signed_B = B if B < 128 else B - 256
            res16 = signed_A * signed_B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 17: # MULSU (Signed A * Unsigned B)
            signed_A = A if A < 128 else A - 256
            res16 = signed_A * B
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 18: # FMUL (Fractional Unsigned)
            res16 = (A * B) << 1
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 19: # FMULS (Fractional Signed)
            signed_A = A if A < 128 else A - 256
            signed_B = B if B < 128 else B - 256
            res16 = (signed_A * signed_B) << 1
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF
            
        elif op == 20: # FMULSU (Fractional Signed A * Unsigned B)
            signed_A = A if A < 128 else A - 256
            res16 = (signed_A * B) << 1
            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF

        # Output the results (Masked to 8 bits to simulate hardware registers)
        self.ResL.put(res_l & 0xFF)
        
        # Word and Multiply operations populate High byte; others typically zero it
        if op in [4, 5, 15, 16, 17, 18, 19, 20]:
            self.ResH.put(res_h & 0xFF)
        else:
            self.ResH.put(0)