import py4hw
from ..instruction_decode import *

class Instruction_decoder(py4hw.Logic):
    def __init__(self, parent, name: str,
                 # --- Inputs ---
                 Instruction,Instruction_fetched,
                 # --- Parameter Outputs (Extracted from instruction) ---
                 InstructionCode, Rd, Rr, K, k_addr, b, A, q,
                 # --- Control Outpus ---
                 Instruction_decoded
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
        self.Instruction = self.addIn('Instruction', Instruction)
        self.Instruction_fetched = self.addIn('Instruction_fetched',Instruction_fetched) # This is a signal form the RomHandler that tells the instruction decoder that it has a new instruction to decode

        # --- Parameter Outputs ---
        self.InstructionCode = self.addOut('InstructionCode', InstructionCode)
        self.Rd = self.addOut('Rd', Rd)
        self.Rr = self.addOut('Rr', Rr)
        self.K = self.addOut('K', K)              # Immediate value
        self.k_addr = self.addOut('k_addr', k_addr) # Address/Jump offset
        self.b = self.addOut('b', b)              # Bit position
        self.A = self.addOut('A', A)              # I/O Register Address (SBI/CBI)
        self.q = self.addOut('q', q)              # Memory displacement
        self.Instruction_decoded = self.addOut('Instruction_decoded',Instruction_decoded) # This signal is put to 1 in DECODE_INSTRUCTION state and set to 0 in the WAIT_FOR_NEW_INSTRUCITON state

    def propagate(self):
        ins = self.Instruction.get()

    
        # 1. Decode Instruction via the external module
        inst_str = ins_to_str(ins)
        code = str_to_code(inst_str)
        
        
        # 2. Perform optimistic parameter extractions across all formats
        rd_default = (ins >> 4) & 0x1F
        rr_default = ((ins >> 5) & 0x10) | (ins & 0x0F)
        
        rd_imm = 16 + ((ins >> 4) & 0x0F)
        k_8bit = ((ins >> 4) & 0xF0) | (ins & 0x0F)
        
        rd_word = 24 + (((ins >> 4) & 0x03) << 1)
        k_6bit = ((ins >> 2) & 0x30) | (ins & 0x0F)
        
        k_12bit = ins & 0x0FFF
        if k_12bit & 0x0800: k_12bit -= 4096 # Sign extend 12-bit
        
        k_7bit = (ins >> 3) & 0x7F
        if k_7bit & 0x40: k_7bit -= 128      # Sign extend 7-bit Branch extraction
        
        b_reg = ins & 0x07 # Bit 
        b_sreg = (ins >> 4) & 0x07
        
        p_io = ((ins >> 5) & 0x30) | (ins & 0x0F)
        p_bitio = (ins >> 3) & 0x1F
        
        q_disp = ((ins >> 8) & 0x20) | ((ins >> 7) & 0x18) | (ins & 0x07) # Memory instrucion
        
        # 3. Defaults for Output Generation 
        out_rd, out_rr, out_K, out_k_addr, out_b, out_A, out_q = 0, 0, 0, 0, 0, 0, 0

        # 4. Filter and map parameters based on Instruction Code groupings
        
        # Format 1: Arithmetic & Logic with Two Registers (Rd, Rr)
        if code in [1, 2, 4, 6, 9, 11, 13, 20, 23, 24, 25, 26, 27, 28, 37, 38, 39, 93]:
            out_rd = rd_default
            out_rr = rr_default
            
        # Format 1b: MOVW (Word copy)
        elif code == 94:
            out_rd = ((ins >> 4) & 0x0F) * 2
            out_rr = (ins & 0x0F) * 2
            
        # Format 2: Immediate Ops (Rd[16-31], K[8-bit])
        elif code in [5, 7, 10, 12, 16, 17, 40, 95]:
            out_rd = rd_imm
            out_K = k_8bit

        # Format 3: Immediate Word Ops (Rd[24,26,28,30], K[6-bit])
        elif code in [3, 8]:
            out_rd = rd_word
            out_K = k_6bit

        # Format 4: Single Register Ops (Rd)
        elif code in [14, 15, 18, 19, 21, 22, 67, 68, 69, 70, 71, 72, 126, 127]:
            out_rd = rd_default

        # Format 5: Relative Branch/Call (k[12-bit])
        elif code in [29, 32]:
            out_k_addr = k_12bit
            
        # Format 6: Conditional Branching (k[7-bit])
        elif 45 <= code <= 64:
            out_k_addr = k_7bit

        # Format 7: Long Jumps (k[22-bit... extracting upper 6 bits from Word 1])
        elif code in [31, 34]:
            out_k_addr = ((ins >> 3) & 0x3E) | (ins & 0x01)
            
        # Format 8: Bit operations in Register (Rr/Rd, b[3-bit])
        elif code in [41, 42, 75]: # SBRC, SBRS, BST 
            out_rr = rd_default 
            out_b = b_reg
        elif code == 76:           # BLD
            out_rd = rd_default
            out_b = b_reg

        # Format 9: Bit Operations in I/O Port (A[5-bit], b[3-bit])
        elif code in [43, 44, 65, 66]:
            out_A = p_bitio
            out_b = b_reg
            
        # Format 10: Status Flag Set/Clear (s/b[3-bit])
        elif code in [73, 74] or (77 <= code <= 92):
            out_b = b_sreg
            
        # Format 11: General I/O (Rd, A[6-bit])
        elif code in [124, 125]:
            out_rd = rd_default
            out_A = p_io

        # Format 12: Memory Load/Store with Displacement (Rd, q[6-bit])
        elif code in [102, 106, 114, 118]:
            out_rd = rd_default
            out_q = q_disp

        # Format 13: Direct/Indirect Memory Load/Store (Rd)
        elif 96 <= code <= 101 or 103 <= code <= 105 or 108 <= code <= 113 or 115 <= code <= 117 or code in [107, 119, 121, 122]:
            out_rd = rd_default


        # 5. Push exact mapped parameters onto the hardware wires
        self.InstructionCode.prepare(code)
        self.Rd.prepare(out_rd)
        self.Rr.prepare(out_rr)
        self.K.prepare(out_K)
        self.k_addr.prepare(out_k_addr) # this is a 22 bit output always
        self.b.prepare(out_b)
        self.A.prepare(out_A)
        self.q.prepare(out_q)
        
