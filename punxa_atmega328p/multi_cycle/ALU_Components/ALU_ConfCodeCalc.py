import py4hw

# ADD register to store the ALU value
class ALU_ConfCodeCalc(py4hw.Logic):
    def __init__(self, parent, name: str,
                 ALUInstruction, BitPos,
                 ArithmeticControl, Copp, Zopp, Nopp, Vopp, Sopp, Hopp, Topp, Iopp, eSREG, BranchOpp):
        super().__init__(parent, name)

        self.ins = self.addIn('ALUInstruction', ALUInstruction)
        self.bit_pos = self.addIn('BitPos',BitPos)
        
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
        self.BranchOpp = self.addOut('BranchOpp', BranchOpp)

    def propagate(self):
        inst = self.ins.get()
        bit_pos = self.bit_pos.get()
        
        # 1. Directly command the AU component 
        arith_ctrl = inst 

        # Every jump/skip-type instruction is handled entirely by
        # BranchUnit (LU) via branch_opp below; AU must never see these on
        # its Operation port. arith_ctrl is forced to 0 (IDLE) for all of
        # them just before it's driven onto the wire. NOTE: SBI(65)/CBI(66)
        # are deliberately NOT in this set -- they are real read-modify-
        # write bit operations that AU now implements, so they must reach
        # AU with arith_ctrl == inst.
        _BRANCH_SKIP_INS = {
            37,                                               # CPSE
            41, 42, 43, 44,                                   # SBRC SBRS SBIC SBIS
            45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,    # BRBS/BRBC family
            57, 58, 59, 60, 61, 62, 63, 64,
        }
        
        # 2. Initialize Default SREG Enables (0 = Do not write)
        ien, ten, hen, sen, ven, nen, zen, cen = 0, 0, 0, 0, 0, 0, 0, 0
        
        # 3. Initialize Default Handler Modes (0 = Default/Hold/Clear)
        copp, zopp, nopp, vopp, sopp, hopp, topp, iopp = 0, 0, 0, 0, 0, 0, 0, 0

        branch_opp = 0

        # Mapped specifically to the modes defined in your Handle_X components:
        Z_MODE_8BIT  = 2 # HandleZ: 8-bit Zero
        Z_MODE_16BIT = 3 # HandleZ: 16-bit Zero
        Z_MODE_CHAIN = 5 # HandleZ: Chained (Update your HandleZ.py to use Mode 5 for this)
        
        N_MODE_8BIT  = 2 # HandleN: 8-bit Negative MSB
        N_MODE_16BIT = 3 # HandleN: 16-bit Negative MSB
        
        S_MODE_XOR   = 2 # HandleS: N XOR V (Update your HandleS.py to use Mode 2 for this)

        # 4. Decode the AU Operations and Assign SREG Behaviors
        if inst in (1, 2): # 1: ADD | 2: ADC
            hen, sen, ven, nen, zen, cen = 1, 1, 1, 1, 1, 1
            hopp = 2 # HandleH Mode 2: 8-bit Addition
            vopp = 2 # HandleV Mode 2: 8-bit Addition
            copp = 2 # HandleC Mode 1: 8-bit Addition
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst in (4, 5, 6, 7, 38, 39, 40): # 4: SUB | 5: SUBI | 6: SBC | 7: SBCI | 38: CP | 39: CPC | 40: CPI
            hen, sen, ven, nen, zen, cen = 1, 1, 1, 1, 1, 1
            hopp = 3 # HandleH Mode 3: 8-bit Subtraction
            vopp = 3 # HandleV Mode 3: 8-bit Subtraction
            copp = 3 # HandleC Mode 2: 8-bit Subtraction
            sopp, nopp = S_MODE_XOR, N_MODE_8BIT
            
            # SBC, SBCI, and CPC use chained Z-flag comparison to support multi-byte operations
            if inst in (6, 7, 39):
                zopp = Z_MODE_CHAIN 
            else:
                zopp = Z_MODE_8BIT

        elif inst == 3: # 3: ADIW 
            sen, ven, nen, zen, cen = 1, 1, 1, 1, 1
            hen = 0 # Word operations do NOT affect Half Carry
            hopp = 0
            vopp = 4 # HandleV Mode 4: 16-bit Addition
            copp = 4 # HandleC Mode 3: 16-bit Addition
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_16BIT, N_MODE_16BIT

        elif inst == 8: # 8: SBIW
            sen, ven, nen, zen, cen = 1, 1, 1, 1, 1
            hen = 0 
            hopp = 0
            vopp = 5 # HandleV Mode 13: 16-bit Subtraction
            copp = 5 # HandleC Mode 13: 16-bit Subtraction
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_16BIT, N_MODE_16BIT

        elif inst in (9, 10, 11, 12, 13, 16, 17, 20, 21): # 9: AND | 10: ANDI | 11: OR | 12: ORI | 13: EOR | 16: SBR | 17: CBR | 20: TST | 21: CLR
            sen, ven, nen, zen = 1, 1, 1, 1
            cen, hen = 0, 0 
            vopp = 0 # HandleV Mode 0: Force Clear
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 14: # 14: COM
            sen, ven, nen, zen, cen = 1, 1, 1, 1, 1
            hen = 0
            vopp = 0 # HandleV Mode 0: Force Clear
            copp = 4 # HandleC Mode 4: Force Carry to 1
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 15: # 15: NEG
            hen, sen, ven, nen, zen, cen = 1, 1, 1, 1, 1, 1
            hopp = 3 # HandleH Mode 3: Subtraction logic 
            vopp = 5 # HandleV Mode 5: Two's Complement Negation
            copp = 5 # HandleC Mode 5: Two's Complement Negation
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 18: # 18: INC
            sen, ven, nen, zen = 1, 1, 1, 1
            cen, hen = 0, 0 # INC strictly leaves Carry unaffected
            vopp = 6 # HandleV Mode 6: Increment overflow
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 19: # 19: DEC
            sen, ven, nen, zen = 1, 1, 1, 1
            cen, hen = 0, 0 # DEC strictly leaves Carry unaffected
            vopp = 7 # HandleV Mode 7: Decrement overflow
            sopp, zopp, nopp = S_MODE_XOR, Z_MODE_8BIT, N_MODE_8BIT

        elif inst == 22: # 22: SER
            # No flags are updated by SER (Equivalent to LDI)
            pass

        elif inst in (23, 24, 25, 26, 27, 28): # 23-28: MUL Family (MUL, MULS, MULSU, FMUL, FMULS, FMULSU)
            zen, cen = 1, 1
            nen, ven, sen, hen = 0, 0, 0, 0
            copp = 8 # HandleC Mode 8: Multiplication carry takes bit 15
            zopp = Z_MODE_16BIT 

        elif inst == 73: # 73: BSET Instruction 
            # 1. Masking: Enable ONLY the specific SREG bit matching bit_pos
            cen = 1 if bit_pos == 0 else 0
            zen = 1 if bit_pos == 1 else 0
            nen = 1 if bit_pos == 2 else 0
            ven = 1 if bit_pos == 3 else 0
            sen = 1 if bit_pos == 4 else 0
            hen = 1 if bit_pos == 5 else 0
            ten = 1 if bit_pos == 6 else 0
            ien = 1 if bit_pos == 7 else 0
            
            # 2. Output SET modes to the handlers.
            # ALL handlers use Mode 1 for Set
            iopp, topp, hopp, sopp, vopp, nopp, zopp, copp = 1, 1, 1, 1, 1, 1, 1, 1

        elif inst == 74: # 74: BCLR Instruction
            # 1. Masking: Enable ONLY the specific SREG bit matching bit_pos
            cen = 1 if bit_pos == 0 else 0
            zen = 1 if bit_pos == 1 else 0
            nen = 1 if bit_pos == 2 else 0
            ven = 1 if bit_pos == 3 else 0
            sen = 1 if bit_pos == 4 else 0
            hen = 1 if bit_pos == 5 else 0
            ten = 1 if bit_pos == 6 else 0
            ien = 1 if bit_pos == 7 else 0
                    
            # 2. Output CLEAR mode (0) to all handlers
            iopp, topp, hopp, sopp, vopp, nopp, zopp, copp = 0, 0, 0, 0, 0, 0, 0, 0

        elif inst in (45,49,47,53,61,55,57,59,63): # BRBS 
            # Test one specific bit of SREG, bit index is carried in BitPos,
            branch_opp = 1

        elif inst in (46,50,51,52,48,54,62,56,58,60,64): # BRBC
            branch_opp = 2

        elif inst == 41: # SBRC 
            branch_opp = 3

        elif inst == 42: # SBRS
            branch_opp = 4

        elif inst == 43: # SBIC
            branch_opp = 5

        elif inst == 44: # SBIS
            branch_opp = 6

        elif inst == 37: # CPSE - Skip if Rd == Rr
            branch_opp = 7
        

        # 5. Pack Write Enables into the 8-bit eSREG signal
        # AVR Standard Register Order: I(7), T(6), H(5), S(4), V(3), N(2), Z(1), C(0)
        esreg_val = (ien << 7) | (ten << 6) | (hen << 5) | (sen << 4) | (ven << 3) | (nen << 2) | (zen << 1) | cen

        # 6. Put calculated values onto the wire components
        # Keep AU out of the jump/skip path entirely.
        if inst in _BRANCH_SKIP_INS:
            arith_ctrl = 0
            
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

        self.BranchOpp.put(branch_opp)