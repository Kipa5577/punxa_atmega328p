import py4hw
from ..instruction_decode import *

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
                 ID_Instruction_decoded
                 ):
        super().__init__(parent, name)

        """
            STATE MACHINE

            +-------------------+
            | DECODE_INSTRUCTION|<------------|
            +-------------------+             |
                        |                     |
                    One CLOCK       Instruction_fetched == 1
                        |                     |
            +-------------------------+       |
            | WAIT_FOR_NEW_INSTRUCITON| ------|
            +-------------------------+

            In DECODE_INSTRUCTION: Read the instruction and update the outputs and put the instruction decoder output to 1
            In WAIT_FOR_NEW_INSTRUCITON: Keep the outputs as they were
        """

        # --- Inputs ---
        self.Instruction = self.addIn('Instruction', ID_Instruction)
        self.Instruction_fetched = self.addIn('Instruction_fetched', ID_Instruction_fetched)

        # --- Parameter Outputs ---
        self.InstructionCode = self.addOut('InstructionCode', ID_InstructionCode)

        # Register outputs (single, covers all d/r variants)
        self.Rd = self.addOut('Rd', ID_Rd)
        self.Rr = self.addOut('Rr', ID_Rr)

        # K immediate outputs (4 variants)
        self.K8  = self.addOut('K8',  ID_K8)   # 8-bit:  ANDI/CPI/LDI/ORI/SBCI/SUBI
        #self.K7  = self.addOut('K7',  K7)   # 7-bit:  AVRrc LDS/STS address
        self.K6  = self.addOut('K6',  ID_K6)   # 6-bit:  ADIW/SBIW
        self.K4  = self.addOut('K4',  ID_K4)   # 4-bit:  DES round key

        # k address/offset outputs (4 variants)
        self.k7  = self.addOut('k7',  ID_k7)   # 7-bit signed:   conditional branches
        self.k12 = self.addOut('k12', ID_k12)  # 12-bit signed:  RJMP/RCALL
        #self.k16 = self.addOut('k16', k16)  # 16-bit:         LDS/STS (second word — 0 from word 1)
        self.k7_22 = self.addOut('k7_22', ID_k7_22)  # 22-bit: JMP/CALL (upper 6 bits from word 1, pre-shifted)

        # Bit position outputs
        self.b  = self.addOut('b', ID_b)      # 3-bit: BLD/BST/CBI/SBI/SBIC/SBIS/SBRC/SBRS
        self.s  = self.addOut('s', ID_s)      # 3-bit SREG: BSET/BCLR/BRBS/BRBC

        # I/O address outputs (2 variants)
        self.A5 = self.addOut('A5',ID_A5)     # 5-bit: CBI/SBI/SBIC/SBIS (lower 32 I/O ports)
        self.A6 = self.addOut('A6',ID_A6)     # 6-bit: IN/OUT (all 64 I/O ports)

        # Displacement output
        self.q  = self.addOut('q', ID_q)      # 6-bit: LDD/STD (fragmented encoding)


        # --- Control Output ---
        self.Instruction_decoded = self.addOut('Instruction_decoded', ID_Instruction_decoded)

        self.lastins = 0
        self.instructionDecoded = 0

    def propagate(self):
        ins = self.Instruction.get()

        # 1. Decode Instruction via the external module
        inst_str = ins_to_str(ins)
        code = str_to_code(inst_str)

        # =====================================================================
        # 2. Extract ALL parameter variants from the first 16-bit word
        # =====================================================================

        # --- Rd (destination register) variants ---
        # d5: full range r0–r31, bits [8:4]
        rd_d5 = (ins >> 4) & 0x1F
        # d4: upper half r16–r31, bits [7:4] + 16
        rd_d4 = 16 + ((ins >> 4) & 0x0F)
        # d3: r16–r23 for multiply instructions, bits [6:4] + 16
        rd_d3 = 16 + ((ins >> 4) & 0x07)
        # d2: register pair r24–r30 for ADIW/SBIW, bits [5:4] → 24/26/28/30
        rd_d2 = 24 + (((ins >> 4) & 0x03) << 1)

        # --- Rr (source register) variants ---
        # r5: full range r0–r31, bit [9] and bits [3:0]
        rr_r5 = ((ins >> 5) & 0x10) | (ins & 0x0F)
        # r4: r16–r31 for MULS / register pair for MOVW, bits [3:0] + 16
        rr_r4 = 16 + (ins & 0x0F)
        # r3: r16–r23 for multiply instructions, bits [2:0] + 16
        rr_r3 = 16 + (ins & 0x07)

        # --- K (immediate data constant) variants ---
        # K8: 8-bit, bits [11:8] and [3:0]
        K_8bit = ((ins >> 4) & 0xF0) | (ins & 0x0F)
        # K7: 7-bit for AVRrc LDS/STS (reduced-core variant)
        # NOTE: Standard AVR does not use this; placeholder extraction
        K_7bit = (ins >> 2) & 0x7F
        # K6: 6-bit for ADIW/SBIW, bits [7:6] and [3:0]
        K_6bit = ((ins >> 2) & 0x30) | (ins & 0x0F)
        # K4: 4-bit DES round key, bits [7:4]
        K_4bit = (ins >> 4) & 0x0F

        # --- k (address / branch offset) variants ---
        # k7: 7-bit signed, bits [9:3]
        k_7bit = (ins >> 3) & 0x7F
        if k_7bit & 0x40:
            k_7bit -= 128                  # sign-extend from 7 bits
        # k12: 12-bit signed, bits [11:0]
        k_12bit = ins & 0x0FFF
        if k_12bit & 0x0800:
            k_12bit -= 4096               # sign-extend from 12 bits
        # k16: 16-bit address for 32-bit LDS/STS — entirely in second word
        #k_16bit = 0                        # no k16 bits in the first 16-bit word
        # k22: 22-bit absolute address for JMP/CALL
        #   Word 1: 1001 010k kkkk 111k  →  k[21]=ins[8], k[20:17]=ins[7:4], k[16]=ins[0]
        #   Word 2: kkkk kkkk kkkk kkkk  →  k[15:0]
        # Output has upper 6 bits pre-shifted to [21:16]; lower 16 bits are 0
        # so that:  final_address = k22_output | second_word
        k_22bit = (((ins >> 3) & 0x3E) | (ins & 0x01)) << 16

        # --- b (bit position in register / I/O) ---
        # b3: 3-bit, bits [2:0]
        b_bit = ins & 0x07

        # --- s (SREG bit selector) ---
        # s3: 3-bit, bits [6:4]
        s_bit = (ins >> 4) & 0x07

        # --- A (I/O address) variants ---
        # A5: 5-bit, bits [7:3] — lower 32 I/O ports
        A_5bit = (ins >> 3) & 0x1F
        # A6: 6-bit, bits [10:9] and [3:0] — all 64 I/O ports
        A_6bit = ((ins >> 5) & 0x30) | (ins & 0x0F)

        # --- q (displacement) ---
        # q6: 6-bit, fragmented across bits [13], [11:10], [2:0]
        # Encoding: 10q0 qq0d dddd 0qqq
        q_disp = ((ins >> 8) & 0x20) | ((ins >> 7) & 0x18) | (ins & 0x07)

        # =====================================================================
        # 3. Initialise all outputs to 0
        # =====================================================================
        out_rd  = 0
        out_rr  = 0
        out_K8  = 0
        #out_K7  = 0
        out_K6  = 0
        out_K4  = 0
        out_k7  = 0
        out_k12 = 0
        #out_k16 = 0
        out_k7_22 = 0
        out_b   = 0
        out_s   = 0
        out_A5  = 0
        out_A6  = 0
        out_q   = 0

        # =====================================================================
        # 4. Map parameters to outputs based on Instruction Code
        # =====================================================================

        # Format 1: Arithmetic & Logic with Two Registers — Rd[d5], Rr[r5]
        #   ADC, ADD, AND, CP, CPC, EOR, MOV, MUL, OR, SBC, SUB, ...
        if code in [1, 2, 4, 6, 9, 11, 13, 20, 23, 24, 25, 26, 27, 28, 37, 38, 39, 93]:
            out_rd = rd_d5
            out_rr = rr_r5
            # NOTE: If codes 24–28 correspond to MULS / MULSU / FMUL / FMULS / FMULSU,
            #       they require d4/r4 or d3/r3 variants.  Move them to the dedicated
            #       groups below once the exact code mapping is confirmed.

        # Format 1b: MOVW (Word copy) — register pairs
        elif code == 94:
            out_rd = ((ins >> 4) & 0x0F) * 2   # d4 pair → 0,2,…,30
            out_rr = (ins & 0x0F) * 2           # r4 pair → 0,2,…,30

        # Format 2: Immediate Operations — Rd[d4], K[K8]
        #   ANDI, CPI, LDI, ORI, SBCI, SUBI, ...
        elif code in [5, 7, 10, 12, 16, 17, 40, 95]:
            out_rd  = rd_d4
            out_K8  = K_8bit

        # Format 3: Immediate Word Operations — Rd[d2], K[K6]
        #   ADIW, SBIW
        elif code in [3, 8]:
            out_rd = rd_d2
            out_K6 = K_6bit

        # Format 4: Single Register Operations — Rd[d5]
        #   ASR, COM, DEC, INC, LSR, NEG, ROR, SWAP, PUSH, POP, ...
        elif code in [14, 15, 18, 19, 21, 22, 67, 68, 69, 70, 71, 72, 126, 127]:
            out_rd = rd_d5

        # Format 5: Relative Jump / Call — k[k12]
        #   RJMP, RCALL
        elif code in [29, 32]:
            out_k12 = k_12bit

        # Format 6: Conditional Branching — k[k7]
        #   BRBS, BRBC and all 18 derived branch instructions
        elif 45 <= code <= 64:
            out_k7 = k_7bit
            out_b  = b_bit          # SREG flag index the branch tests (bits [2:0])

        # Format 7: Long Jump / Call — k[k22] (upper 6 bits from word 1)
        #   JMP, CALL
        elif code in [31, 34]:
            # FIX: was `out_k22 = k_22bit`, a variable that doesn't exist
            # elsewhere — k7_22 output was silently never driven (always 0).
            # k_22bit already has the upper bits pre-shifted to [21:16];
            # the k7_22 wire is 7 bits wide, so pass bits [22:16] only.
            out_k7_22 = (k_22bit >> 16) & 0x7F

        # Format 8: Bit Test / Skip on Register — Rd or Rr, b[b3]
        #   SBRC, SBRS, BST (encoded in Rd position, output as Rr)
        elif code in [41, 42, 75]:
            out_rr = rd_d5
            out_b  = b_bit
        #   BLD (uses Rd)
        elif code == 76:
            out_rd = rd_d5
            out_b  = b_bit

        # Format 9: Bit Test / Skip on I/O Port — A[A5], b[b3]
        #   SBIC, SBIS, CBI, SBI
        elif code in [43, 44, 65, 66]:
            out_A5 = A_5bit
            out_b  = b_bit

        # Format 10: SREG Bit Set / Clear / Test — s[s3]
        #   BSET, BCLR, BRBS, BRBC
        elif code in [73, 74] or (77 <= code <= 92):
            out_s = s_bit

        # Format 11: General I/O — Rd[d5], A[A6]
        #   IN, OUT
        elif code in [124, 125]:
            out_rd = rd_d5
            out_A6 = A_6bit

        # Format 12: Memory Load / Store with Displacement — Rd[d5], q[q6]
        #   LDD Y+q, LDD Z+q, STD Y+q, STD Z+q
        elif code in [102, 106, 114, 118]:
            out_rd = rd_d5
            out_q  = q_disp

        # Format 13: Direct / Indirect Memory Load / Store — Rd[d5]
        #   LD/ST with X/Y/Z, LDS, STS (32-bit), LPM, ...
        elif (96 <= code <= 101 or 103 <= code <= 105 or
              108 <= code <= 113 or 115 <= code <= 117 or
              code in [107, 119, 121, 122]):
            out_rd = rd_d5

        # =====================================================================
        # 5. Drive all output wires
        # =====================================================================
        self.InstructionCode.prepare(code)
        self.Rd.prepare(out_rd)
        self.Rr.prepare(out_rr)
        self.K8.prepare(out_K8)
        #self.K7.prepare(out_K7)
        self.K6.prepare(out_K6)
        self.K4.prepare(out_K4)
        self.k7.prepare(out_k7)
        self.k12.prepare(out_k12)
        #self.k16.prepare(out_k16)
        self.k7_22.prepare(out_k7_22)
        self.b.prepare(out_b)
        self.s.prepare(out_s)
        self.A5.prepare(out_A5)
        self.A6.prepare(out_A6)
        self.q.prepare(out_q)

    # Default the instruction decoded signal to 0
        out_instruction_decoded = 0

        # Signal ControlBox that decoded outputs are valid for the current instruction
        if ins != self.lastins:
            self.lastins = ins
            # It takes a cycle to decode; leave out_instruction_decoded as default (0)
        elif self.Instruction_fetched.get() == 1:
            # Instruction matches last tick and fetch is high, signal decoded
            out_instruction_decoded = 1

        self.Instruction_decoded.prepare(out_instruction_decoded)