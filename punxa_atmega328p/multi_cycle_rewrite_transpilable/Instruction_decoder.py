import py4hw


class Instruction_decoder(py4hw.Logic):
    def __init__(self, parent, name: str,
                 # --- Inputs ---
                 ID_Instruction, ID_Instruction_fetched,
                 # --- Parameter Outputs (Extracted from instruction) ---
                 ID_InstructionCode,
                 # Register outputs (single output each, covers all d/r variants)
                 ID_Rd, ID_Rr,
                 # K immediate outputs (4 variants)
                 ID_K8, ID_K6, ID_K4,  #K7,
                 # k address/offset outputs (4 variants)
                 ID_k7, ID_k12, ID_k16, ID_k7_22,
                 # Bit position outputs (separate for register/I/O vs SREG)
                 ID_b, ID_s,
                 # I/O address outputs (2 variants)
                 ID_A5, ID_A6,
                 # Displacement output
                 ID_q,
                 # --- Control Output ---
                 ID_Instruction_decoded,
                 # --- Reset
                 ID_Reset=None,
                 ):
        super().__init__(parent, name)

        # --- Inputs ---
        self.Instruction = self.addIn('Instruction', ID_Instruction)
        self.Instruction_fetched = self.addIn('Instruction_fetched', ID_Instruction_fetched)

        # --- Parameter Outputs ---
        self.InstructionCode = self.addOut('InstructionCode', ID_InstructionCode)

        # Register outputs 
        self.Rd = self.addOut('Rd', ID_Rd)
        self.Rr = self.addOut('Rr', ID_Rr)

        # K immediate outputs 
        self.K8  = self.addOut('K8',  ID_K8)   
        self.K6  = self.addOut('K6',  ID_K6)   
        self.K4  = self.addOut('K4',  ID_K4)   

        # k address/offset outputs 
        self.k7  = self.addOut('k7',  ID_k7)   
        self.k12 = self.addOut('k12', ID_k12)  
        self.k7_22 = self.addOut('k7_22', ID_k7_22)  

        # Bit position outputs
        self.b  = self.addOut('b', ID_b)      
        self.s  = self.addOut('s', ID_s)      

        # I/O address outputs 
        self.A5 = self.addOut('A5',ID_A5)     
        self.A6 = self.addOut('A6',ID_A6)     

        # Displacement output
        self.q  = self.addOut('q', ID_q)      


        # --- Control Output ---
        self.Instruction_decoded = self.addOut('Instruction_decoded', ID_Instruction_decoded)
        self.reset = self.addIn('reset', ID_Reset) 

        self.lastins = 0
        self.instructionDecoded = 0

    def propagate(self):
        if self.reset.get():  
            self.lastins = 0
            self.InstructionCode.prepare(0)
            self.Rd.prepare(0); self.Rr.prepare(0)
            self.K8.prepare(0); self.K6.prepare(0); self.K4.prepare(0)
            self.k7.prepare(0); self.k12.prepare(0); self.k7_22.prepare(0)
            self.b.prepare(0); self.s.prepare(0)
            self.A5.prepare(0); self.A6.prepare(0)
            self.q.prepare(0)
            self.Instruction_decoded.prepare(0)
        else:

            ins = self.Instruction.get()

            code = 0  # Defaults to 0 / Invalid

            mask_4   = ins & 0xF000
            mask_6   = ins & 0xFC00
            mask_8   = ins & 0xFE08
            mask_8b  = ins & 0xFF00
            mask_10  = ins & 0xFE0E
            mask_10b = ins & 0xFF88
            mask_11  = ins & 0xFE0F
            mask_13  = ins & 0xFF8F

            OP17 = ((ins >> 3) & 0b1) | (((ins >> 9) & 0b1) << 1) | (((ins >> 12) & 0b1) << 2) | ((ins >> 14) << 3)
            OP16 = ins >> 11
            OP5A6A12 = ins >> 8
            OP7  = ((ins >> 9) << 4) | (ins & 0xF)
            OP4  = ((ins >> 7) << 1) | ((ins >> 3) & 0b1)
            OP2A10 = ins >> 12
            OP1A8A13 = ins >> 10
            OP14 = ((ins >> 10) << 3) | (ins & 0b111)

            if ins == 0b1001_0101_0001_1001: code = 33 # ICALL
            elif ins == 0b1001_0100_0001_1001: code = 30 # IJMP

            elif mask_4 == 0b0111_0000_0000_0000: code = 10 # ANDI
            elif mask_4 == 0b1110_0000_0000_0000: code = 95 # LDI
            elif mask_4 == 0b1100_0000_0000_0000: code = 29 # RJMP

            elif mask_6 == 0b0000_1100_0000_0000: code = 1 # ADD

            elif mask_8 == 0b1111_1010_0000_0000: code = 75 # BST
            elif mask_8 == 0b1111_1000_0000_0000: code = 76 # BLD
            elif mask_8 == 0b1111_1100_0000_0000: code = 41 # SBRC
            elif mask_8 == 0b1111_1110_0000_0000: code = 42 # SBRS

            elif mask_8b == 0b0000_0010_0000_0000: code = 24 # MULS

            elif mask_10 == 0b1001_0100_0000_1100: code = 31 # JMP
            elif mask_10 == 0b1001_0100_0000_1110: code = 34 # CALL

            elif mask_10b == 0b0000_0011_0000_0000: code = 25 # MULSU
            elif mask_10b == 0b0000_0011_1000_0000: code = 27 # FMULS
            elif mask_10b == 0b0000_0011_1000_1000: code = 28 # FMULSU

            elif mask_11 == 0b1001_0000_0000_0000: code = 107 # LDS
            elif mask_11 == 0b1001_0010_0000_0000: code = 119 # STS
            elif mask_11 == 0b1001_0100_0000_1010: code = 19 # DEC
            elif mask_11 == 0b1000_0010_0000_0000: code = 115 # STZ

            elif mask_13 == 0b1001_0100_0000_1000: code = 73 # BSET
            elif mask_13 == 0b1001_0100_1000_1000: code = 74 # BCLR

            elif OP17 == 0b10011: code = 114 # STDY
            elif OP17 == 0b10010: code = 118 # STDZ
            elif OP17 == 0b10000: code = 106 # LDDZ
            elif OP17 == 0b10001: code = 102 # LDDY

            elif OP16 == 0b10110: code = 124 # IN
            elif OP16 == 0b10111: code = 125 # OUT

            elif OP5A6A12 == 0b00000001: code = 94 # MOVW
            elif OP5A6A12 == 0b10010110: code = 3 # ADIW
            elif OP5A6A12 == 0b10010111: code = 8 # SBIW
            elif OP5A6A12 == 0b10011001: code = 43 # SBIC
            elif OP5A6A12 == 0b10011010: code = 65 # SBI
            elif OP5A6A12 == 0b10011000: code = 66 # CBI
            elif OP5A6A12 == 0b10011011: code = 44 # SBIS

            elif OP7 == 0b10010100001: code = 15 # NEG
            elif OP7 == 0b10010100000: code = 14 # COM
            elif OP7 == 0b10010100011: code = 18 # INC
            elif OP7 == 0b10010101010: code = 19 # DEC
            elif OP7 == 0b10010100110: code = 68 # LSR
            elif OP7 == 0b10010100111: code = 70 # ROR
            elif OP7 == 0b10010100101: code = 71 # ASR
            elif OP7 == 0b10010100010: code = 72 # SWAP
            elif OP7 == 0b10010001111: code = 127 # POP
            elif OP7 == 0b10010011111: code = 126 # PUSH
            elif OP7 == 0b10010001100: code = 96 # LDX
            elif OP7 == 0b10010001101: code = 97 # LDX+
            elif OP7 == 0b10010001110: code = 98 # LD-X
            elif OP7 == 0b10000001000: code = 99 # LDY
            elif OP7 == 0b10010001001: code = 100 # LDY+
            elif OP7 == 0b10010001010: code = 101 # LD-Y
            elif OP7 == 0b10000000000: code = 103 # LDZ
            elif OP7 == 0b10010000001: code = 104 # LDZ+
            elif OP7 == 0b10010000010: code = 105 # LD-Z
            elif OP7 == 0b10010011100: code = 108 # STX
            elif OP7 == 0b10010011101: code = 109 # STX+
            elif OP7 == 0b10010011110: code = 110 # ST-X
            elif OP7 == 0b10000011000: code = 111 # STY
            elif OP7 == 0b10010011001: code = 112 # STY+
            elif OP7 == 0b10010011010: code = 113 # ST-Y
            elif OP7 == 0b10000010000: code = 115 # STZ
            elif OP7 == 0b10010010001: code = 116 # STZ+
            elif OP7 == 0b10010010010: code = 117 # ST-Z
            elif OP7 == 0b10010000100: code = 121 # LPMZ
            elif OP7 == 0b10010000101: code = 122 # LPMZ+

            elif OP4 == 0b0000001101: code = 26 # FMUL

            elif OP2A10 == 0b0100: code = 7 # SBCI
            elif OP2A10 == 0b0101: code = 5 # SUBI
            elif OP2A10 == 0b0110: code = 12 # ORI
            elif OP2A10 == 0b0011: code = 40 # CPI
            elif OP2A10 == 0b1101: code = 32 # RCALL

            elif OP1A8A13 == 0b0000_10: code = 6 # SBC
            elif OP1A8A13 == 0b0000_11: code = 1 # ADD
            elif OP1A8A13 == 0b0001_01: code = 38 # CP
            elif OP1A8A13 == 0b0001_11: code = 2 # ADC
            elif OP1A8A13 == 0b0001_10: code = 4 # SUB
            elif OP1A8A13 == 0b0010_00: code = 9 # AND
            elif OP1A8A13 == 0b0010_01: code = 13 # EOR
            elif OP1A8A13 == 0b0010_10: code = 11 # OR
            elif OP1A8A13 == 0b1001_11: code = 23 # MUL
            elif OP1A8A13 == 0b0000_01: code = 39 # CPC
            elif OP1A8A13 == 0b0010_11: code = 93 # MOV
            elif OP1A8A13 == 0b1111_00: code = 45 # BRBS
            elif OP1A8A13 == 0b1111_01: code = 46 # BRBC
            elif OP1A8A13 == 0b0001_00: code = 37 # CPSE

            elif OP14 == 0b111100001: code = 47 # BREQ
            elif OP14 == 0b111101001: code = 48 # BRNE
            elif OP14 == 0b111100000: code = 49 # BRCS
            elif OP14 == 0b111101000: code = 51 # BRSH
            elif OP14 == 0b111100010: code = 53 # BRMI
            elif OP14 == 0b111101010: code = 54 # BRPL
            elif OP14 == 0b111101100: code = 55 # BRGE
            elif OP14 == 0b111100100: code = 56 # BRLT
            elif OP14 == 0b111100101: code = 57 # BRHS
            elif OP14 == 0b111101101: code = 58 # BRHC
            elif OP14 == 0b111100110: code = 59 # BRTS
            elif OP14 == 0b111101110: code = 60 # BRTC
            elif OP14 == 0b111100011: code = 61 # BRVS
            elif OP14 == 0b111101011: code = 62 # BRVC
            elif OP14 == 0b111100111: code = 63 # BRIE
            elif OP14 == 0b111101111: code = 64 # BRID

            elif ins == 0x0: code = 128 # NOP
            elif ins == 0b1001010110001000: code = 129 # SLEEP
            elif ins == 0b1001010110101000: code = 130 # WDR
            elif ins == 0b1001010110011000: code = 131 # BREAK
            elif ins == 0b1001010100001000: code = 35 # RET
            elif ins == 0b1001010100011000: code = 36 # RETI
            elif ins == 0b1001010111101000: code = 123 # SPM
            elif ins == 0b1001010111111000: code = 123 # SPMZ+
            elif ins == 0x9004: code = 120 # LPM

            # --- Rd (destination register) variants ---
            rd_d5 = (ins >> 4) & 0x1F
            rd_d4 = 16 + ((ins >> 4) & 0x0F)
            rd_d3 = 16 + ((ins >> 4) & 0x07)
            rd_d2 = 24 + (((ins >> 4) & 0x03) << 1)

            # --- Rr (source register) variants ---
            rr_r5 = ((ins >> 5) & 0x10) | (ins & 0x0F)
            rr_r4 = 16 + (ins & 0x0F)
            rr_r3 = 16 + (ins & 0x07)

            # --- K (immediate data constant) variants ---
            K_8bit = ((ins >> 4) & 0xF0) | (ins & 0x0F)
            K_7bit = (ins >> 2) & 0x7F
            K_6bit = ((ins >> 2) & 0x30) | (ins & 0x0F)
            K_4bit = (ins >> 4) & 0x0F

            # --- k (address / branch offset) variants ---
            k_7bit = (ins >> 3) & 0x7F
            if k_7bit & 0x40:
                k_7bit -= 128
            k_12bit = ins & 0x0FFF
            if k_12bit & 0x0800:
                k_12bit -= 4096
            k_22bit = (((ins >> 3) & 0x3E) | (ins & 0x01)) << 16

            # --- b (bit position in register / I/O) ---
            b_bit = ins & 0x07

            # --- s (SREG bit selector) ---
            s_bit = (ins >> 4) & 0x07

            # --- A (I/O address) variants ---
            a5_local = (ins >> 3) & 0x1F
            a6_local = ((ins >> 5) & 0x30) | (ins & 0x0F)

            # --- q (displacement) ---
            q_disp = ((ins >> 8) & 0x20) | ((ins >> 7) & 0x18) | (ins & 0x07)

            out_rd  = 0
            out_rr  = 0
            out_K8  = 0
            out_K6  = 0
            out_K4  = 0
            out_k7  = 0
            out_k12 = 0
            out_k7_22 = 0
            out_b   = 0
            out_s   = 0
            out_A5  = 0
            out_A6  = 0
            out_q   = 0

            if (((code == 1) or ((code == 2) or ((code == 4) or ((code == 6) or ((code == 9) or ((code == 11) or ((code == 13) or ((code == 20) or ((code == 23) or ((code == 37) or ((code == 38) or ((code == 39) or (code == 93)))))))))))))):
                out_rd = rd_d5
                out_rr = rr_r5

            elif code == 24:
                out_rd = rd_d4
                out_rr = rr_r4

            elif (((code == 25) or ((code == 26) or ((code == 27) or (code == 28))))):
                out_rd = rd_d3
                out_rr = rr_r3

            elif code == 94:
                out_rd = ((ins >> 4) & 0x0F) * 2
                out_rr = (ins & 0x0F) * 2

            elif (((code == 5) or ((code == 7) or ((code == 10) or ((code == 12) or ((code == 16) or ((code == 17) or ((code == 40) or (code == 95))))))))):
                out_rd  = rd_d4
                out_K8  = K_8bit

            elif ((code == 3) or (code == 8)):
                out_rd = rd_d2
                out_K6 = K_6bit
                out_K8 = K_6bit

            elif (((code == 14) or ((code == 15) or ((code == 18) or ((code == 19) or ((code == 21) or ((code == 22) or ((code == 67) or ((code == 68) or ((code == 69) or ((code == 70) or ((code == 71) or ((code == 72) or ((code == 126) or (code == 127))))))))))))))):
                out_rd = rd_d5

            elif ((code == 29) or (code == 32)):
                out_k12 = k_12bit

            elif ((45 <= code) and (code <= 64)):
                out_k7 = k_7bit
                out_b  = b_bit

            elif ((code == 31) or (code == 34)):
                out_k7_22 = (k_22bit >> 16) & 0x7F

            elif (((code == 41) or ((code == 42) or (code == 75)))):
                out_rr = rd_d5
                out_b  = b_bit

            elif code == 76:
                out_rd = rd_d5
                out_b  = b_bit

            elif (((code == 43) or ((code == 44) or ((code == 65) or (code == 66))))):
                out_A5 = a5_local
                out_b  = b_bit

            elif ((code == 73) or (code == 74)) or (((77 <= code) and (code <= 92))):
                out_s = s_bit
                out_b = s_bit

            elif ((code == 124) or (code == 125)):
                out_rd = rd_d5
                out_A6 = a6_local

            elif (((code == 102) or ((code == 106) or ((code == 114) or (code == 118))))):
                out_rd = rd_d5
                out_q  = q_disp

            elif ((((96 <= code) and (code <= 101)) or (((103 <= code) and (code <= 105)) or (((108 <= code) and (code <= 113)) or (((115 <= code) and (code <= 117)) or ((code == 107) or ((code == 119) or ((code == 121) or (code == 122))))))))):
                out_rd = rd_d5

            self.InstructionCode.prepare(code)
            self.Rd.prepare(out_rd)
            self.Rr.prepare(out_rr)
            self.K8.prepare(out_K8)
            self.K6.prepare(out_K6)
            self.K4.prepare(out_K4)
            self.k7.prepare(out_k7)
            self.k12.prepare(out_k12)
            self.k7_22.prepare(out_k7_22)
            self.b.prepare(out_b)
            self.s.prepare(out_s)
            self.A5.prepare(out_A5)
            self.A6.prepare(out_A6)
            self.q.prepare(out_q)

            out_instruction_decoded = 0

            if ins != self.lastins:
                self.lastins = ins
            elif self.Instruction_fetched.get() == 1:
                out_instruction_decoded = 1

            self.Instruction_decoded.prepare(out_instruction_decoded)
