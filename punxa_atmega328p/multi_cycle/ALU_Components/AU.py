import py4hw

class AU(py4hw.Logic): 
    def __init__(self, parent, name: str,
                 Cval, RegAL, RegAH, RegBL, RegBH, Operation, BitPos,
                 ResL, ResH, MulCarryOut, Tval=None):
        super().__init__(parent, name)

        # Inputs
        self.Cval = self.addIn('Cval', Cval)
        # Tval: current T flag, needed only by BLD (op 76) to write bit
        # BitPos of Rd from T. Optional for backward compatibility with any
        # other instantiation site that doesn't wire it up.
        self.Tval = self.addIn('Tval', Tval) if Tval is not None else None
        self.RegAL = self.addIn('RegAL', RegAL)
        self.RegAH = self.addIn('RegAH', RegAH)
        self.RegBL = self.addIn('RegBL', RegBL)
        self.RegBH = self.addIn('RegBH', RegBH)
        self.Operation = self.addIn('Operation', Operation)
        self.Cval = self.addIn('C', Cval)
        self.RegAL = self.addIn('AL', RegAL)
        self.RegAH = self.addIn('AH', RegAH)
        self.RegBL = self.addIn('BL', RegBL)
        self.RegBH = self.addIn('BH', RegBH)
        self.Operation = self.addIn('op', Operation)
        # 3-bit index (0-7): which bit SBI/CBI target within RegAL. Every
        # other opcode ignores this input.
        self.BitPos = self.addIn('BitPos', BitPos)

        # Outputs 
        self.ResL = self.addOut('ResL', ResL)
        self.ResH = self.addOut('ResH', ResH)
        # FIX: dedicated carry-out for the 8x8 multiply family. This is
        # bit 15 of the RAW (unshifted) 16-bit product, i.e. the bit that
        # gets shifted out of R1:R0 for FMUL/FMULS/FMULSU. ResH alone
        # cannot carry this information -- it's masked to 8 bits and only
        # covers bits [15:8] of the (possibly shifted) stored result, so
        # the true carry bit was previously being silently discarded.
        self.MulCarryOut = self.addOut('MulCarryOut', MulCarryOut)

        # FIX: ADC/SBC/SBCI/CPC read the incoming Carry flag as a genuine
        # computational input, not just an output flag. But ADC etc. are
        # multi-cycle instructions in this design (FETCH_RD -> FETCH_RR ->
        # DETERMINE_OUTPUT -> ...), and the decoded opcode (hence
        # ALU_ConfCodeCalc's eSREG write-enable mask) stays constant across
        # every one of those cycles, while MemoryInterfaceHandler commits
        # SREG unconditionally on EVERY cycle eSREG is nonzero -- not just
        # once when the result is final. During the early fetch cycles
        # (before Rr is even loaded), A/B are still stale/incomplete, so
        # the ALU commits a garbage Carry to SREG -- which ADC/SBC then
        # read straight back as their own carry-in, corrupting their own
        # result before the real computation ever happens.
        # Fix: latch Cval exactly once, the instant a new opcode appears on
        # Operation (i.e. before this instruction's own writes can have
        # touched SREG yet), and hold it stable for the rest of this
        # instruction's multi-cycle execution. Only ADC/SBC/SBCI/CPC use
        # this latched copy; every other opcode is unaffected.
        # NOTE: this detects "new instruction" via Operation changing, so a
        # literal back-to-back repeat of the exact same opcode (e.g. two
        # ADCs in a row with no other instruction between) will not
        # re-latch. A fully general fix needs a dedicated "commit" pulse
        # threaded from OppFSM through to MemoryInterfaceHandler.
        self._latched_C = 0
        self._prev_op = None

    def clock(self):
        op = self.Operation.get()
        if op != self._prev_op:
            self._latched_C = self.Cval.get() & 1
            self._prev_op = op

    def propagate(self): 
        # Retrieve current values from pins
        op = self.Operation.get()
        A = self.RegAL.get()
        B = self.RegBL.get()
        bit_pos = self.BitPos.get() & 0x7
        
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
            res_l = A + B + self._latched_C
            
        elif op in (4, 5, 38, 40): # SUB / SUBI / CP / CPI
            res_l = A - B
            
        elif op in (6, 7, 39): # SBC / SBCI / CPC
            res_l = A - B - self._latched_C
            
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

        elif op == 72: # SWAP (swap nibbles)
            res_l = ((A & 0x0F) << 4) | ((A >> 4) & 0x0F)

        elif op == 67: # LSL (Logical Shift Left) -- carry handled by HandleC (mode 10, old bit7)
            res_l = (A << 1) & 0xFF

        elif op == 68: # LSR (Logical Shift Right) -- carry handled by HandleC (mode 9, old bit0)
            res_l = (A >> 1) & 0x7F

        elif op == 69: # ROL (Rotate Left through Carry)
            res_l = ((A << 1) | self._latched_C) & 0xFF

        elif op == 70: # ROR (Rotate Right through Carry)
            res_l = ((A >> 1) | (self._latched_C << 7)) & 0xFF

        elif op == 71: # ASR (Arithmetic Shift Right, sign bit preserved)
            res_l = ((A >> 1) | (A & 0x80)) & 0xFF

        elif op == 93: # MOV (Rd <- Rr)
            # FIX: MOV was not implemented at all -- op 93 fell through
            # every branch and AU output 0, so OppFSM's write-back stored
            # 0 into Rd for every MOV. The data path is: OppFSM fetches
            # Rr into OperandBuffer B0, which arrives here as RegBL (B);
            # MOV just passes it through as the result.
            res_l = B

        # Default: no multiply in progress this cycle
        mul_carry = 0

        # --- MULTIPLY INSTRUCTIONS ---
        # FIX: all six 8x8 multiply variants now go through one path.
        # The raw (unshifted) 16-bit product is computed first, using the
        # correct signed/unsigned interpretation per opcode, and its bit 15
        # is captured as `mul_carry` BEFORE any shift is applied. That bit
        # is exactly the carry-out the AVR spec defines for these ops --
        # for plain MUL/MULS/MULSU it's simply bit 15 of the stored result
        # (no shift, nothing lost); for FMUL/FMULS/FMULSU it's the bit that
        # gets shifted out of R1:R0 and would otherwise vanish the moment
        # ResH is masked down to 8 bits.
        if op in (23, 24, 25, 26, 27, 28):
            if op in (24, 27):        # MULS / FMULS: both operands signed
                val_A = A if A < 128 else A - 256
                val_B = B if B < 128 else B - 256
            elif op in (25, 28):      # MULSU / FMULSU: A signed, B unsigned
                val_A = A if A < 128 else A - 256
                val_B = B
            else:                     # MUL / FMUL: both unsigned
                val_A = A
                val_B = B

            raw = (val_A * val_B) & 0xFFFF   # raw 16-bit product, pre-shift
            mul_carry = (raw >> 15) & 1

            if op in (26, 27, 28):    # fractional variants: shift left 1
                res16 = (raw << 1) & 0xFFFF
            else:
                res16 = raw

            res_l = res16 & 0xFF
            res_h = (res16 >> 8) & 0xFF

        elif op in (73, 74): # BSET / BCLR 
            pass # No arithmetic needed for flag-only operations

        elif op == 65: # SBI (Set Bit in I/O Register)
            res_l = A | (1 << bit_pos)

        elif op == 66: # CBI (Clear Bit in I/O Register)
            res_l = A & ~(1 << bit_pos)

        elif op == 76: # BLD (Bit Load: Rd[bit_pos] <- T)
            t_val = (self.Tval.get() & 1) if self.Tval is not None else 0
            if t_val:
                res_l = A | (1 << bit_pos)
            else:
                res_l = A & ~(1 << bit_pos)

        # Output the results (Masked to 8 bits to simulate hardware registers)
        self.ResL.put(res_l & 0xFF)
        self.MulCarryOut.put(mul_carry & 1)
        
        # Word and Multiply operations populate High byte; others zero it out
        # Mapped to: ADIW(3), SBIW(8), MUL(23), MULS(24), MULSU(25), FMUL(26), FMULS(27), FMULSU(28)
        if op in [3, 8, 23, 24, 25, 26, 27, 28]:
            self.ResH.put(res_h & 0xFF)
        else:
            self.ResH.put(0)