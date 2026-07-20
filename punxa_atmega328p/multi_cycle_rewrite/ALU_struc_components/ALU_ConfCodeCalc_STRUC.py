import py4hw

class ALU_ConfCodeCalc(py4hw.Logic):
    def __init__(self, parent, name: str,
                 ALUInstruction, BitPos,
                 ArithmeticControl, Copp, Zopp, Nopp, Vopp, Sopp, Hopp, Topp, Iopp, eSREG, BranchOpp):
        super().__init__(parent, name)

        # -------------------------------------------------------------
        # 1. INPUTS & OUTPUTS
        # -------------------------------------------------------------
        self.ins = self.addIn('ALUInstruction', ALUInstruction)
        self.bit_pos = self.addIn('BitPos', BitPos)

        # FIX: the incoming ALUInstruction wire is 16 bits wide (it's
        # Datapath's raw opcode bus, D_Instruction, plugged straight
        # through ALU_STRUC's 'op' port with no truncation), but every
        # opcode value used below fits in 8 bits (max mapped index is
        # 131) and py4hw.Mux's balanced selection tree requires
        # sel.getWidth() == exactly log2(len(ins)). Slice the low 8 bits
        # off here and use that as every Mux's actual selector below,
        # rather than the raw 16-bit port.
        self._ins_sel = self.wire("w_ins_sel8", 8)
        py4hw.Range(self, "Range_InsSel", self.ins, 7, 0, self._ins_sel)
        
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

        # -------------------------------------------------------------
        # 2. CONSTANT WIRE CACHE UTILITY
        # -------------------------------------------------------------
        # Helper to generate and cache constant wires on the fly to 
        # avoid cluttering the module with dozens of py4hw.Constant calls.
        self._consts = {}
        def get_const(val):
            if val not in self._consts:
                w = self.wire(f"const_{val}", 8)
                py4hw.Constant(self, f"C_{val}", val, w)
                self._consts[val] = w
            return self._consts[val]

        # -------------------------------------------------------------
        # 3. DYNAMIC ESREG GENERATOR FOR BSET (73) & BCLR (74)
        # -------------------------------------------------------------
        # BSET/BCLR need a dynamic mask: 1 << BitPos
        self.w_dyn_esreg = self.wire("w_dyn_esreg", 8)
        py4hw.ShiftLeft(self, "Shl_BSET_Mask", get_const(1), self.bit_pos, self.w_dyn_esreg)

        # -------------------------------------------------------------
        # 4. MUX ARRAY (ROM) INITIALIZATION
        # -------------------------------------------------------------
        # Max opcode mapped is 131. py4hw.Mux builds a balanced binary
        # selection tree and requires len(ins) to be an exact power of 2
        # matching 2**sel.getWidth() (self.ins is 8 bits wide) -- 132
        # is not a power of 2, so this MUST be padded to 256, not just
        # large enough to cover the highest opcode.
        MUX_SIZE = 256

        # Initialize all arrays to default 0
        arith_inputs = [get_const(0)] * MUX_SIZE
        branch_inputs = [get_const(0)] * MUX_SIZE
        esreg_inputs = [get_const(0)] * MUX_SIZE
        
        copp_inputs = [get_const(0)] * MUX_SIZE
        zopp_inputs = [get_const(0)] * MUX_SIZE
        nopp_inputs = [get_const(0)] * MUX_SIZE
        vopp_inputs = [get_const(0)] * MUX_SIZE
        sopp_inputs = [get_const(0)] * MUX_SIZE
        hopp_inputs = [get_const(0)] * MUX_SIZE
        topp_inputs = [get_const(0)] * MUX_SIZE
        iopp_inputs = [get_const(0)] * MUX_SIZE

        # -------------------------------------------------------------
        # 5. POPULATE THE ROMS BASED ON INSTRUCTION MAP
        # -------------------------------------------------------------
        
        # --- A. Arithmetic Control (Filter out Branch Ops) ---
        _BRANCH_SKIP_INS = {
            37, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 
            51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64
        }
        for op in range(MUX_SIZE):
            if op not in _BRANCH_SKIP_INS:
                arith_inputs[op] = get_const(op)

        # --- B. Standard Instructions ---
        for op in (1, 2): # ADD, ADC
            esreg_inputs[op] = get_const(0x3F) # C,Z,N,V,S,H
            hopp_inputs[op] = get_const(2)
            vopp_inputs[op] = get_const(2)
            copp_inputs[op] = get_const(2)
            sopp_inputs[op] = get_const(2)
            zopp_inputs[op] = get_const(2)
            nopp_inputs[op] = get_const(2)

        for op in (4, 5, 38, 40): # SUB, SUBI, CP, CPI
            esreg_inputs[op] = get_const(0x3F)
            hopp_inputs[op] = get_const(3)
            vopp_inputs[op] = get_const(3)
            copp_inputs[op] = get_const(3)
            sopp_inputs[op] = get_const(2)
            zopp_inputs[op] = get_const(2)
            nopp_inputs[op] = get_const(2)
            
        for op in (6, 7, 39): # SBC, SBCI, CPC
            esreg_inputs[op] = get_const(0x3F)
            hopp_inputs[op] = get_const(3)
            vopp_inputs[op] = get_const(3)
            copp_inputs[op] = get_const(3)
            sopp_inputs[op] = get_const(2)
            zopp_inputs[op] = get_const(5) # Mode 5: Chained Zero
            nopp_inputs[op] = get_const(2)

        esreg_inputs[3] = get_const(0x1F) # ADIW (C,Z,N,V,S)
        vopp_inputs[3] = get_const(4)
        copp_inputs[3] = get_const(4)
        sopp_inputs[3] = get_const(2)
        zopp_inputs[3] = get_const(3) # 16-bit
        nopp_inputs[3] = get_const(3) # 16-bit

        esreg_inputs[8] = get_const(0x1F) # SBIW
        vopp_inputs[8] = get_const(5)
        copp_inputs[8] = get_const(5)
        sopp_inputs[8] = get_const(2)
        zopp_inputs[8] = get_const(3) # 16-bit
        nopp_inputs[8] = get_const(3) # 16-bit

        for op in (9, 10, 11, 12, 13, 16, 17, 20, 21): # Logic Ops
            esreg_inputs[op] = get_const(0x1E) # Z,N,V,S
            vopp_inputs[op] = get_const(0)     # Force Clear
            sopp_inputs[op] = get_const(2)
            zopp_inputs[op] = get_const(2)
            nopp_inputs[op] = get_const(2)

        esreg_inputs[14] = get_const(0x1F) # COM
        vopp_inputs[14] = get_const(0)
        copp_inputs[14] = get_const(6)
        sopp_inputs[14] = get_const(2)
        zopp_inputs[14] = get_const(2)
        nopp_inputs[14] = get_const(2)

        esreg_inputs[15] = get_const(0x3F) # NEG
        hopp_inputs[15] = get_const(4)
        vopp_inputs[15] = get_const(6)
        copp_inputs[15] = get_const(7)
        sopp_inputs[15] = get_const(2)
        zopp_inputs[15] = get_const(2)
        nopp_inputs[15] = get_const(2)

        for op in (18, 19): # INC, DEC
            esreg_inputs[op] = get_const(0x1E) # Z,N,V,S
            vopp_inputs[op] = get_const(6 if op == 18 else 7)
            sopp_inputs[op] = get_const(2)
            zopp_inputs[op] = get_const(2)
            nopp_inputs[op] = get_const(2)

        for op in (67, 68, 69, 70, 71): # Shifts & Rotates
            esreg_inputs[op] = get_const(0x1F) # C,Z,N,V,S
            zopp_inputs[op] = get_const(2)
            sopp_inputs[op] = get_const(2)
            vopp_inputs[op] = get_const(9)
            
            if op in (67, 69): # LSL, ROL
                copp_inputs[op] = get_const(10)
                nopp_inputs[op] = get_const(2)
            elif op == 68:     # LSR
                copp_inputs[op] = get_const(9)
                nopp_inputs[op] = get_const(0)
            else:              # ROR, ASR
                copp_inputs[op] = get_const(9)
                nopp_inputs[op] = get_const(2)

        for op in (23, 24, 25, 26, 27, 28): # MUL Family
            esreg_inputs[op] = get_const(0x03) # C,Z
            copp_inputs[op] = get_const(8)
            zopp_inputs[op] = get_const(3)

        # --- C. Bit Management & Single Flags ---
        
        # BSET (73) & BCLR (74) Use the dynamically calculated bitmask
        esreg_inputs[73] = self.w_dyn_esreg
        copp_inputs[73] = zopp_inputs[73] = nopp_inputs[73] = vopp_inputs[73] = get_const(1)
        sopp_inputs[73] = hopp_inputs[73] = topp_inputs[73] = iopp_inputs[73] = get_const(1)
        
        esreg_inputs[74] = self.w_dyn_esreg
        # Flags for BCLR are already default 0, so no need to map them explicitly

        esreg_inputs[75] = get_const(0x40) # BST sets T flag
        topp_inputs[75] = get_const(2)

        _SINGLE_FLAGS = {
            77: (0x01, copp_inputs, 1), 78: (0x01, copp_inputs, 0), # SEC/CLC
            79: (0x04, nopp_inputs, 1), 80: (0x04, nopp_inputs, 0), # SEN/CLN
            81: (0x02, zopp_inputs, 1), 82: (0x02, zopp_inputs, 0), # SEZ/CLZ
            83: (0x80, iopp_inputs, 1), 84: (0x80, iopp_inputs, 0), # SEI/CLI
            85: (0x10, sopp_inputs, 1), 86: (0x10, sopp_inputs, 0), # SES/CLS
            87: (0x08, vopp_inputs, 1), 88: (0x08, vopp_inputs, 0), # SEV/CLV
            89: (0x40, topp_inputs, 1), 90: (0x40, topp_inputs, 0), # SET/CLT
            91: (0x20, hopp_inputs, 1), 92: (0x20, hopp_inputs, 0)  # SEH/CLH
        }
        for op, (mask, opp_arr, val) in _SINGLE_FLAGS.items():
            esreg_inputs[op] = get_const(mask)
            opp_arr[op] = get_const(val)

        # --- D. Branch Operations ---
        for op in (45, 49, 47, 53, 61, 55, 57, 59, 63): branch_inputs[op] = get_const(1) # BRBS
        for op in (46, 50, 51, 52, 48, 54, 62, 56, 58, 60, 64): branch_inputs[op] = get_const(2) # BRBC
        branch_inputs[41] = get_const(3) # SBRC
        branch_inputs[42] = get_const(4) # SBRS
        branch_inputs[43] = get_const(5) # SBIC
        branch_inputs[44] = get_const(6) # SBIS
        branch_inputs[37] = get_const(7) # CPSE

        # -------------------------------------------------------------
        # 6. STRUCTURAL MULTIPLEXER INSTANTIATION
        # -------------------------------------------------------------
        # Connect the ROM arrays to output wires based on the incoming Instruction.
        py4hw.Mux(self, "Mux_Arithm", self._ins_sel, arith_inputs, self.ArithmCode)
        py4hw.Mux(self, "Mux_Branch", self._ins_sel, branch_inputs, self.BranchOpp)
        py4hw.Mux(self, "Mux_eSREG", self._ins_sel, esreg_inputs, self.eSREG)
        
        py4hw.Mux(self, "Mux_Copp", self._ins_sel, copp_inputs, self.Copp)
        py4hw.Mux(self, "Mux_Zopp", self._ins_sel, zopp_inputs, self.Zopp)
        py4hw.Mux(self, "Mux_Nopp", self._ins_sel, nopp_inputs, self.Nopp)
        py4hw.Mux(self, "Mux_Vopp", self._ins_sel, vopp_inputs, self.Vopp)
        py4hw.Mux(self, "Mux_Sopp", self._ins_sel, sopp_inputs, self.Sopp)
        py4hw.Mux(self, "Mux_Hopp", self._ins_sel, hopp_inputs, self.Hopp)
        py4hw.Mux(self, "Mux_Topp", self._ins_sel, topp_inputs, self.Topp)
        py4hw.Mux(self, "Mux_Iopp", self._ins_sel, iopp_inputs, self.Iopp)
# FIX: pre-existing naming mismatch -- ALU.py imports/calls this module as
# 'ALU_ConfCodeCalc_STRUC' (matching every other _STRUC-suffixed sibling
# file), but the class defined above is named 'ALU_ConfCodeCalc' (no
# suffix). Alias rather than rename the class itself, to keep this fix
# minimally invasive.
ALU_ConfCodeCalc_STRUC = ALU_ConfCodeCalc

