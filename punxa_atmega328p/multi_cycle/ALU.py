import py4hw 
from ..Memory import * 
from .ALU_Components.AU import *
from .ALU_Components.LU import * 
from .ALU_Components.ALU_ConfCodeCalc import *

from .ALU_Components.HandleC import *
from .ALU_Components.HandleH import * 
from .ALU_Components.HandleI import *
from .ALU_Components.HandleN import * 
from .ALU_Components.HandleT import * 
from .ALU_Components.HandleS import *
from .ALU_Components.HandleV import * 
from .ALU_Components.HandleZ import *

from .ALU_Components.WireCombiner16 import *


"""
=============================================================================
AI Agent Component Reference: Top-Level ALU (Arithmetic Logic Unit)
=============================================================================

Description:
This class is the top-level orchestrator for the ALU. Designed for the py4hw 
event-driven simulator, it acts as a wiring harness that connects several 
behavioral leaf components: the Arithmetic Unit (AU), the Branch/Skip Unit (LU), 
the Instruction Decoder (ALU_ConfCodeCalc), and eight independent Flag Handlers.

Inputs:
- ImputRegA0 (8-bit): The lower byte of the primary operand / Destination Register (Rd).
- ImputRegA1 (8-bit): The upper byte of the primary operand (for 16-bit operations).
- ImputRegB0 (8-bit): The lower byte of the secondary operand / Source Register (Rr).
- ImputRegB1 (8-bit): The upper byte of the secondary operand.
- ALUInstruction (int): The opcode or decoded control signal defining the arithmetic/logic operation to perform.
- SREG_STATE (8-bit): The incoming state of the Status Register, packed in standard AVR order (I-T-H-S-V-N-Z-C).
- BitPos (int): A 3-bit index (0-7) targeting a specific bit for bitwise operations, branch conditions, or skips.
- IOreg (8-bit): The current value of a specified I/O register, utilized exclusively for Skip instructions (SBIC/SBIS).

Outputs:
- ALUOUTPUTByte0 (8-bit): The lower byte of the computation's numerical result.
- ALUOUTPUTByte1 (8-bit): The upper byte of the computation's numerical result (active during 16-bit operations).
- SREG_VAL (8-bit): The newly calculated Status Register values, merged back into a single 8-bit bus.
- eSREG_VAL (8-bit): The write-enable mask for the SREG. A '1' indicates the flag should be updated by the current instruction; a '0' indicates it must be held.
- BRANCH (1-bit boolean): Signals HIGH (1) if a conditional branch requirement (e.g., BRBS, BRBC) evaluates to True.
- SKIP (1-bit boolean): Signals HIGH (1) if an instruction skip requirement (e.g., SBRS, SBIC) evaluates to True.
=============================================================================
"""
class SREG_Splitter(py4hw.Logic):
    """Splits the 8-bit SREG bus into individual flag wires."""
    def __init__(self, parent, name, sreg_state, w_cin, w_zin, w_nin, w_vin):
        super().__init__(parent, name)
        self.sreg_state = self.addIn('SREG_STATE', sreg_state)
        self.w_cin = self.addOut('w_cin', w_cin)
        self.w_zin = self.addOut('w_zin', w_zin)
        self.w_nin = self.addOut('w_nin', w_nin)
        self.w_vin = self.addOut('w_vin', w_vin)

    def propagate(self):
        sreg = self.sreg_state.get()
        self.w_cin.put(sreg & 1)
        self.w_zin.put((sreg >> 1) & 1)
        self.w_nin.put((sreg >> 2) & 1)
        self.w_vin.put((sreg >> 3) & 1)

class ALU_MergerAndLogic(py4hw.Logic):
    """Merges flags back to SREG, bridges output results, and computes Branch/Skip."""
    def __init__(self, parent, name,
                w_cout, w_zout, w_nout, w_vout,
                w_sout, w_hout, w_tout, w_iout,
                w_res_l, w_res_H,
                sreg_val, out_byte0, out_byte1):
        super().__init__(parent, name)
        # SREG inputs
        self.w_cout = self.addIn('w_cout', w_cout)
        self.w_zout = self.addIn('w_zout', w_zout)
        self.w_nout = self.addIn('w_nout', w_nout)
        self.w_vout = self.addIn('w_vout', w_vout)
        self.w_sout = self.addIn('w_sout', w_sout)
        self.w_hout = self.addIn('w_hout', w_hout)
        self.w_tout = self.addIn('w_tout', w_tout)
        self.w_iout = self.addIn('w_iout', w_iout)
        
        # AU outputs
        self.w_res_l = self.addIn('w_res_l', w_res_l)
        self.w_res_H = self.addIn('w_res_h', w_res_H)
        
        # Outputs
        self.sreg_val = self.addOut('sreg_val', sreg_val)
        self.out_byte0 = self.addOut('out_byte0', out_byte0)
        self.out_byte1 = self.addOut('out_byte1', out_byte1)

    def propagate(self):

        self.out_byte0.put(self.w_res_l.get())
        self.out_byte1.put(self.w_res_H.get())


        # 2. SREG Merging
        new_sreg = ((self.w_iout.get() & 1) << 7) | \
                   ((self.w_tout.get() & 1) << 6) | \
                   ((self.w_hout.get() & 1) << 5) | \
                   ((self.w_sout.get() & 1) << 4) | \
                   ((self.w_vout.get() & 1) << 3) | \
                   ((self.w_nout.get() & 1) << 2) | \
                   ((self.w_zout.get() & 1) << 1) | \
                   (self.w_cout.get() & 1)
        self.sreg_val.put(new_sreg)


# =====================================================================
# Main ALU Block
# =====================================================================
class ALU(py4hw.Logic):
    def __init__(self, parent, name:str,
                 ImputRegA0, ImputRegA1, ImputRegB0, ImputRegB1, ALUInstruction, SREG_STATE, BitPos, IOreg,
                 ALUOUTPUTByte0, ALUOUTPUTByte1, SREG_VAL, eSREG_VAL, BRANCH, SKIP):
        super().__init__(parent, name)

        # --- Define External Inputs ---
        self.ImputRegA0 = self.addIn('ImputRegA0', ImputRegA0)
        self.ImputRegA1 = self.addIn('ImputRegA1', ImputRegA1)
        self.ImputRegB0 = self.addIn('ImputRegB0', ImputRegB0)
        self.ImputRegB1 = self.addIn('ImputRegB1', ImputRegB1)

        self.ALUins = self.addIn('ALUInstruction', ALUInstruction)
        self.SREG_state = self.addIn('SREG_STATE', SREG_STATE)
        self.BitPos = self.addIn('BitPos', BitPos)
        self.IOreg = self.addIn('IOreg', IOreg)

        # --- Define External Outputs ---
        self.OUTByte0 = self.addOut('ALUOUTPUTByte0', ALUOUTPUTByte0)
        self.OUTByte1 = self.addOut('ALUOUTPUTByte1', ALUOUTPUTByte1)
        self.SREG_VAL = self.addOut('SREG_VAL', SREG_VAL)
        self.eSREG_VAL = self.addOut('eSREG_VAL', eSREG_VAL)
        self.BRANCH = self.addOut('BRANCH', BRANCH)
        self.SKIP = self.addOut('SKIP', SKIP)

        # ==========================================
        # INTERNAL WIRES
        # ==========================================
        # Control Signals
        self.w_arith_ctrl = py4hw.Wire(self, 'w_arith_ctrl', 8)
        self.w_copp = py4hw.Wire(self, 'w_copp',4)
        self.w_zopp = py4hw.Wire(self, 'w_zopp',3)
        self.w_nopp = py4hw.Wire(self, 'w_nopp',3)
        self.w_vopp = py4hw.Wire(self, 'w_vopp',4)
        self.w_sopp = py4hw.Wire(self, 'w_sopp',3)
        self.w_hopp = py4hw.Wire(self, 'w_hopp',2)
        self.w_topp = py4hw.Wire(self, 'w_topp',2)
        self.w_iopp = py4hw.Wire(self, 'w_iopp',1)
        self.w_branchOpp = py4hw.Wire(self, 'w_branchOpp', 3)

        self.w_res_l = py4hw.Wire(self,'w_res_l',8)
        self.w_res_H = py4hw.Wire(self,'w_res_H',8)

        # Individual Flag Inputs (Split from SREG_STATE bus)
        self.w_cin = py4hw.Wire(self, 'w_cin',1)
        self.w_zin = py4hw.Wire(self, 'w_zin',1)
        self.w_nin = py4hw.Wire(self, 'w_nin',1)
        self.w_vin = py4hw.Wire(self, 'w_vin',1)

        # Individual Flag Outputs (Calculated by Handlers)
        self.w_cout = py4hw.Wire(self, 'w_cout',1)
        self.w_zout = py4hw.Wire(self, 'w_zout',1)
        self.w_nout = py4hw.Wire(self, 'w_nout',1)
        self.w_vout = py4hw.Wire(self, 'w_vout',1)
        self.w_sout = py4hw.Wire(self, 'w_sout',1)
        self.w_hout = py4hw.Wire(self, 'w_hout',1)
        self.w_tout = py4hw.Wire(self, 'w_tout',1)
        self.w_iout = py4hw.Wire(self, 'w_iout',1)

        # --- Combined 16-bit Data Wires ---
        self.w_regA_16 = py4hw.Wire(self, 'w_regA_16', 16)
        self.w_regB_16 = py4hw.Wire(self, 'w_regB_16', 16)
        self.w_res_16 = py4hw.Wire(self, 'w_res_16',16)

        # ==========================================
        # SUB-COMPONENT INSTANTIATION
        # ==========================================
        
        # 0. SREG Splitter
        self.sreg_splitter = SREG_Splitter(self, 'SREGSplitter',
            self.SREG_state, self.w_cin, self.w_zin, self.w_nin, self.w_vin)
        
        self.concat_A = WireCombiner16(self, 'ConcatA', self.ImputRegA1, self.ImputRegA0, self.w_regA_16)
        self.concat_B = WireCombiner16(self, 'ConcatB', self.ImputRegB1, self.ImputRegB0, self.w_regB_16)
        self.concat_res = WireCombiner16(self, 'ConcatRes', self.w_res_l, self.w_res_H, self.w_res_16)


        # 1. Configuration & Control Unit
        self.conf_calc = ALU_ConfCodeCalc(
                    self, 'ConfCodeCalc',
                    self.ALUins,          # ALUInstruction
                    self.BitPos,          # BitPos
                    self.w_arith_ctrl,    # ArithmeticControl
                    self.w_copp,          # Copp
                    self.w_zopp,          # Zopp
                    self.w_nopp,          # Nopp
                    self.w_vopp,          # Vopp
                    self.w_sopp,          # Sopp
                    self.w_hopp,          # Hopp
                    self.w_topp,          # Topp
                    self.w_iopp,          # Iopp
                    self.eSREG_VAL,        # eSREG
                    self.w_branchOpp 
                )
        # 2. Arithmetic And Logic Units
        self.au = AU(
                    self, 'AU',
                    self.w_cin,           # Cval
                    self.ImputRegA0,      # RegAL
                    self.ImputRegA1,      # RegAH
                    self.ImputRegB0,      # RegBL
                    self.ImputRegB1,      # RegBH
                    self.w_arith_ctrl,    # Operation
                    self.w_res_l,  # ResL
                    self.w_res_H,   # ResH
                )

        self.BranchUnit = BranchUnit(
            self,'LU',
            self.SREG_state,
            self.ImputRegA0,
            self.IOreg ,
            self.BitPos,
            self.w_branchOpp,
            self.SKIP,
            self.BRANCH,
        )

        # 3. Flag Handlers
        self.handle_c = HandleC(self, 'HC', self.w_regB_16, self.w_regA_16, self.w_res_16, self.w_copp, self.w_cout)
        self.handle_z = HandleZ(self, 'HZ', self.w_res_16, self.w_zopp, self.w_zin, self.w_zout) 
        self.handle_n = HandleN(self, 'HN', self.w_res_16, self.w_nopp, self.w_nout)
        self.handle_v = HandleV(self, 'HV', self.w_regB_16, self.w_regA_16, self.w_res_16, self.w_nin, self.w_vopp, self.w_vout)
        self.handle_h = HandleH(self, 'HH', self.w_regB_16, self.w_regA_16, self.w_res_16, self.w_hopp, self.w_hout)
        self.handle_t = HandleT(self, 'HT', self.w_regA_16, self.BitPos, self.w_topp, self.w_tout)
        self.handle_i = HandleI(self, 'HI', self.w_iopp, self.w_iout)
        self.handle_s = HandleS(self, 'HS', self.w_nout, self.w_vout, self.w_sopp, self.w_sout)

        # 4. Merger and Output Logic
        self.alu_merger = ALU_MergerAndLogic(
            self, 'ALUMerger',
            self.w_cout, self.w_zout, self.w_nout, self.w_vout,
            self.w_sout, self.w_hout, self.w_tout, self.w_iout,
            self.w_res_l, self.w_res_H,
            self.SREG_VAL, self.OUTByte0, self.OUTByte1
        )
