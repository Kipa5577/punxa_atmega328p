import py4hw

class ALU_ConfCodeCalc(py4hw.Logic):
    def __init__(self, parent, name: str,
                 ALUInstruction,
                 ArithmeticControl, Copp, Zopp, Nopp, Vopp, Sopp, Hopp, Topp, Iopp, eSREG):
        super().__init__(parent, name)

        self.ins = self.addIn('ALUInstruction', ALUInstruction)
        
        self.ArithmCode = self.addOut('ArithmeticControl', ArithmeticControl)
        self.Copp = self.addOut('Copp', Copp)
        self.Zopp = self.addOut('Zopp', Zopp)
        self.Nopp = self.addOut('Nopp', Nopp)
        self.Vopp = self.addOut('Vopp', Vopp)
        self.Sopp = self.addOut('Sopp', Sopp)
        self.Hopp = self.addOut('Hopp', Hopp)
        self.Topp = self.addOut('Topp', Topp)
        self.Iopp = self.addOut('Iopp', Iopp)
        
        self.eSREG = self.addOut('eSREG', eSREG)

    def propagate(self):
        inst = self.ins.get()
        
        # 1. Directly command the AU component (Operations 0 to 20)
        arith_ctrl = inst 
        
        # 2. Initialize Default SREG Enables (0 = Do not write)
        ien, ten, hen, sen, ven, nen, zen, cen = 0, 0, 0, 0, 0, 0, 0, 0
        
        # 3. Initialize Default Handler Modes (0 = Default/Hold/Clear)
        copp, zopp, nopp, vopp, sopp, hopp, topp, iopp = 0, 0, 0, 0, 0, 0, 0, 0

        # Mapped specifically to the modes defined in your Handle_X components:
        Z_MODE_8BIT  = 2 # HandleZ: 8-bit Zero
        Z_MODE_16BIT = 3 # HandleZ: 16-bit Zero
        Z_MODE_CHAIN = 5 # HandleZ: Chained (Update your HandleZ.py to use Mode 5 for this)
        
        N_MODE_8BIT  = 2 # HandleN: 8-bit Negative MSB
        N_MODE_16BIT = 3 # HandleN: 16-bit Negative MSB
        
        S_MODE_XOR   = 2 # HandleS: N XOR V (Update your HandleS.py to use Mode 2 for this)

        # 4. Decode the AU Operations and Assign SREG Behaviors
        if inst in (0, 1): # 0: ADD | 1: ADC
            hen, sen, ven, nen, zen, cen = 1, 1, 1, 1, 1, 1
            hopp = 2 # HandleH Mode 2: 8-bit Addition
            vopp = 2 # HandleV Mode 2: 8-bit Addition
            copp = 1 # HandleC Mode 1: 8-bit Addition
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst in (2, 3): # 2: SUB/SUBI | 3: SBC/SBCI
            hen, sen, ven, nen, zen, cen = 1, 1, 1, 1, 1, 1
            hopp = 3 # HandleH Mode 3: 8-bit Subtraction
            vopp = 3 # HandleV Mode 3: 8-bit Subtraction
            copp = 2 # HandleC Mode 2: 8-bit Subtraction
            sopp, nopp = S_MODE_XOR, N_MODE_8BIT
            
            # SBC uses chained Z-flag comparison to support multi-byte subtraction
            if inst == 3:
                zopp = Z_MODE_CHAIN 
            else:
                zopp = Z_MODE_8BIT

        elif inst == 4: # 4: ADIW 
            sen, ven, nen, zen, cen = 1, 1, 1, 1, 1
            hen = 0 # Word operations do NOT affect Half Carry
            hopp = 0
            vopp = 4 # HandleV Mode 4: 16-bit Addition
            copp = 3 # HandleC Mode 3: 16-bit Addition
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_16BIT, N_MODE_16BIT

        elif inst == 5: # 5: SBIW
            sen, ven, nen, zen, cen = 1, 1, 1, 1, 1
            hen = 0 
            hopp = 0
            vopp = 13 # HandleV Mode 13: 16-bit Subtraction
            copp = 13 # HandleC Mode 13: 16-bit Subtraction
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_16BIT, N_MODE_16BIT

        elif inst in (6, 7, 8, 11): # 6: AND/TST | 7: OR/SBR | 8: EOR/CLR | 11: CBR
            sen, ven, nen, zen = 1, 1, 1, 1
            cen, hen = 0, 0 
            vopp = 0 # HandleV Mode 0: Force Clear
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 9: # 9: COM
            sen, ven, nen, zen, cen = 1, 1, 1, 1, 1
            hen = 0
            vopp = 0 # HandleV Mode 0: Force Clear
            copp = 4 # HandleC Mode 4: Force Carry to 1
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 10: # 10: NEG
            hen, sen, ven, nen, zen, cen = 1, 1, 1, 1, 1, 1
            hopp = 3 # HandleH Mode 3: Subtraction logic 
            vopp = 5 # HandleV Mode 5: Two's Complement Negation
            copp = 5 # HandleC Mode 5: Two's Complement Negation
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 12: # 12: INC
            sen, ven, nen, zen = 1, 1, 1, 1
            cen, hen = 0, 0 # INC strictly leaves Carry unaffected
            vopp = 6 # HandleV Mode 6: Increment overflow
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 13: # 13: DEC
            sen, ven, nen, zen = 1, 1, 1, 1
            cen, hen = 0, 0 # DEC strictly leaves Carry unaffected
            vopp = 7 # HandleV Mode 7: Decrement overflow
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 14: # 14: SER
            # No flags are updated by SER (Equivalent to LDI)
            pass

        elif inst in (15, 16, 17, 18, 19, 20): # MUL Family
            zen, cen = 1, 1
            nen, ven, sen, hen = 0, 0, 0, 0
            copp = 8 # HandleC Mode 8: Multiplication carry takes bit 15
            zopp = Z_MODE_16BIT

        # 5. Pack Write Enables into the 8-bit eSREG signal
        # AVR Standard Register Order: I(7), T(6), H(5), S(4), V(3), N(2), Z(1), C(0)
        esreg_val = (ien << 7) | (ten << 6) | (hen << 5) | (sen << 4) | (ven << 3) | (nen << 2) | (zen << 1) | cen

        # 6. Put calculated values onto the wire components
        self.ArithmCode.put(arith_ctrl)
        self.Copp.put(copp)
        self.Zopp.put(zopp)
        self.Nopp.put(nopp)
        self.Vopp.put(vopp)
        self.Sopp.put(sopp)
        self.Hopp.put(hopp)
        self.Topp.put(topp)
        self.Iopp.put(iopp)
        self.eSREG.put(esreg_val)