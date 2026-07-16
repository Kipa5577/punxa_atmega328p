import py4hw 

#ALU_STRUC COMPONENTS
from .ALU_struc_components.AU_STRUC import *
from .ALU_struc_components.LU_STRUC import *
from .ALU_struc_components.ALU_ConfCodeCalc_STRUC import *

from .ALU_struc_components.HandleC_STRUC import *
from .ALU_struc_components.HandleH_STRUC import *
from .ALU_struc_components.HandleI_STRUC import *
from .ALU_struc_components.HandleN_STRUC import *
from .ALU_struc_components.HandleT_STRUC import *
from .ALU_struc_components.HandleS_STRUC import *
from .ALU_struc_components.HandleV_STRUC import *
from .ALU_struc_components.HandleZ_STRUC import *



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
    def __init__(self, parent, name, sreg_state, w_cin, w_zin, w_nin, w_vin, w_tin):
        super().__init__(parent, name)
        # NOTE: attribute renamed to match the addIn port label exactly
        # (SREG_STATE) -- the py4hw RTL transpiler emits the attribute
        # name as the internal wire reference, so a mismatched attribute
        # name/label pair (e.g. self.sreg_state for label 'SREG_STATE')
        # produces Verilog that references an undeclared signal.
        self.SREG_STATE = self.addIn('SREG_STATE', sreg_state)
        self.w_cin = self.addOut('w_cin', w_cin)
        self.w_zin = self.addOut('w_zin', w_zin)
        self.w_nin = self.addOut('w_nin', w_nin)
        self.w_vin = self.addOut('w_vin', w_vin)
        # T is bit 6 in this project's SREG ordering (I-T-H-S-V-N-Z-C).
        # Needed as BLD's real T-flag source -- see AU.Tval wiring below.
        self.w_tin = self.addOut('w_tin', w_tin)

    def propagate(self):
        sreg = self.SREG_STATE.get()
        self.w_cin.put(sreg & 1)
        self.w_zin.put((sreg >> 1) & 1)
        self.w_nin.put((sreg >> 2) & 1)
        self.w_vin.put((sreg >> 3) & 1)
        self.w_tin.put((sreg >> 6) & 1)

class ALU_MergerAndLogic(py4hw.Logic):
    """
    Merges flags back to SREG, bridges output results, and computes Branch/Skip.
    @todo this is just a concatenation of wires, use concatenate
    """
    def __init__(self, parent, name,
                w_cout, w_zout, w_nout, w_vout,
                w_sout, w_hout, w_tout, w_iout,
                sreg_val):
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

        # Outputs
        self.sreg_val = self.addOut('sreg_val', sreg_val)
        

    def propagate(self):

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



class ALU_STRUC(py4hw.Logic):
    def __init__(self, parent, name: str,
                 A0, A1, B0, B1, op, SREG_STATE, BitPos, IOreg, R0, R1, SREG_VAL, eSREG_VAL, BRANCH, SKIP,
                 reset=None):
        # reset: accepted for interface consistency with every other CPU
        # component (rewrite spec). ALU_STRUC is purely combinational
        # (propagate() only, no internal registers), so this is a no-op --
        # kept as a real port rather than silently dropped in case a future
        # ALU revision adds pipeline/latch state.
        super().__init__(parent, name)
        if reset is not None:
            self.addIn('reset', reset)

        # --- Define External Inputs ---
        self.addIn('A0', A0)
        self.addIn('A1', A1)
        self.addIn('B0', B0)
        self.addIn('B1', B1)
 
        self.addIn('op', op)
        self.addIn('SREG_STATE', SREG_STATE)
        self.addIn('BitPos', BitPos)
        self.addIn('IOreg', IOreg)
 
        # --- Define External Outputs ---
        self.addOut('R0', R0)
        self.addOut('R1', R1)
        self.addOut('SREG_VAL', SREG_VAL)
        self.addOut('eSREG_VAL', eSREG_VAL)
        self.addOut('BRANCH', BRANCH)
        self.addOut('SKIP', SKIP)
 
        # ==========================================
        # INTERNAL WIRES
        # ==========================================
        # Control Signals
        w_arith_ctrl = py4hw.Wire(self, 'w_arith_ctrl', 8)
        w_copp = py4hw.Wire(self, 'w_copp', 4)
        w_zopp = py4hw.Wire(self, 'w_zopp', 3)
        w_nopp = py4hw.Wire(self, 'w_nopp', 3)
        w_vopp = py4hw.Wire(self, 'w_vopp', 4)
        w_sopp = py4hw.Wire(self, 'w_sopp', 3)
        # FIX: was declared 2 bits, but ALU_ConfCodeCalc_STRUC's
        # hopp_inputs table assigns index 4 (NEG, "Mode 4: Two's Complement
        # Negation") to this signal -- 4 == 0b100 does not fit in 2 bits
        # (max representable value 3) and would silently wrap to 0,
        # corrupting NEG's half-carry flag. HandleH_STRUC's own Mux array
        # is already sized MUX_SIZE=8 (3-bit selector), so this was the
        # one out-of-sync wire.
        w_hopp = py4hw.Wire(self, 'w_hopp', 3)
        w_topp = py4hw.Wire(self, 'w_topp', 2)
        w_iopp = py4hw.Wire(self, 'w_iopp', 1)
        w_branchOpp = py4hw.Wire(self, 'w_branchOpp', 3)
 
        # Dedicated carry-out from AU for the multiply family, bit 15
        # of the raw (unshifted) product -- consumed by HandleC_STRUC (Mode 8).
        w_mul_carry = py4hw.Wire(self, 'w_mul_carry', 1)
 
        # Individual Flag Inputs (Split from SREG_STATE bus)
        w_cin = py4hw.Wire(self, 'w_cin', 1)
        w_zin = py4hw.Wire(self, 'w_zin', 1)
        w_nin = py4hw.Wire(self, 'w_nin', 1)
        w_vin = py4hw.Wire(self, 'w_vin', 1)
        w_tin = py4hw.Wire(self, 'w_tin_sink', 1)
 
        # Individual Flag Outputs (Calculated by Handlers)
        w_cout = py4hw.Wire(self, 'w_cout', 1)
        w_zout = py4hw.Wire(self, 'w_zout', 1)
        w_nout = py4hw.Wire(self, 'w_nout', 1)
        w_vout = py4hw.Wire(self, 'w_vout', 1)
        w_sout = py4hw.Wire(self, 'w_sout', 1)
        w_hout = py4hw.Wire(self, 'w_hout', 1)
        w_tout = py4hw.Wire(self, 'w_tout', 1)
        w_iout = py4hw.Wire(self, 'w_iout', 1)
 
        # --- Combined 16-bit Data Wires ---
        w_regA_16 = py4hw.Wire(self, 'w_regA_16', 16)
        w_regB_16 = py4hw.Wire(self, 'w_regB_16', 16)
        w_res_16 = py4hw.Wire(self, 'w_res_16', 16)
 
        # ==========================================
        # SUB-COMPONENT INSTANTIATION
        # ==========================================
 
        # 0. SREG Splitter
        SREG_Splitter(self, 'SREGSplitter', SREG_STATE, w_cin, w_zin, w_nin, w_vin, w_tin)
 
        py4hw.ConcatenateLSBF(self, 'A', [A0, A1], w_regA_16)
        py4hw.ConcatenateLSBF(self, 'B', [B0, B1], w_regB_16)
        py4hw.ConcatenateLSBF(self, 'ConcatRes', [R0, R1], w_res_16)
 
        # 1. Configuration & Control Unit
        ALU_ConfCodeCalc_STRUC(
            self, 'ConfCodeCalc',
            op,              # ALUInstruction
            BitPos,          # BitPos
            w_arith_ctrl,    # ArithmeticControl
            w_copp,          # Copp
            w_zopp,          # Zopp
            w_nopp,          # Nopp
            w_vopp,          # Vopp
            w_sopp,          # Sopp
            w_hopp,          # Hopp
            w_topp,          # Topp
            w_iopp,          # Iopp
            eSREG_VAL,       # eSREG
            w_branchOpp
        )
 
        # 2. Arithmetic And Logic Unit
        # AU_STRUC exposes an extra MulCarryOut port (bit 15 of the raw
        # 16-bit product) which HandleC_STRUC needs for the MUL family (Mode 8).
        AU_STRUC(
            self, 'AU',
            w_cin,           # Cval
            A0,              # RegAL
            A1,              # RegAH
            B0,              # RegBL
            B1,              # RegBH
            w_arith_ctrl,    # Operation
            BitPos,          # BitPos (SBI/CBI only)
            R0,              # ResL
            R1,              # ResH
            w_mul_carry,     # MulCarryOut
            # FIX: w_tin (the T flag, already split out of SREG_STATE by
            # SREG_Splitter above) was computed but never passed on to
            # AU_STRUC. Without a real Tval, AU_STRUC's BLD path always
            # took its Tval-is-None fallback (a plain buffer of the CBI
            # bit-clear result), so BLD never actually read T -- it just
            # cleared the target bit regardless of T's value.
            Tval=w_tin,
        )
 
        # @todo why is the branch unit in the ALU?
        BranchUnit_STRUC(self, 'LU', SREG_STATE, A0,
                   B0,        # RegisterB (Rr), for CPSE only
                   IOreg, BitPos, w_branchOpp, SKIP, BRANCH)
 
        # 3. Flag Handlers
        # HandleC_STRUC now also needs MulCarry wired in (Mode 8: MUL family).
        HandleC_STRUC(self, 'HC', w_regB_16, w_regA_16, w_res_16, w_copp, w_mul_carry, w_cout)
        HandleZ_STRUC(self, 'HZ', w_res_16, w_zopp, w_zin, w_zout)
        HandleN_STRUC(self, 'HN', w_res_16, w_nopp, w_nout)
 
        # HandleV_STRUC needs both N and C (Mode 9: shifts -> N ^ C).
        # These must be the *post-operation* N/C flags computed by HandleN/HandleC
        # above, not the pre-operation SREG_STATE bits.
        HandleV_STRUC(self, 'HV', w_regB_16, w_regA_16, w_res_16, w_nout, w_cout, w_vopp, w_vout)
 
        HandleH_STRUC(self, 'HH', w_regB_16, w_regA_16, w_res_16, w_hopp, w_hout)
 
        # HandleT_STRUC splits Rr into 8 individual bits (BST Rd, b), so it
        # must receive the 8-bit register (A0), not the 16-bit concatenation.
        # FIX: BST's register operand is decoded into the *Rr* slot, not
        # Rd (see Instruction_decoder.py Format 8 comment: "SBRC, SBRS,
        # BST encoded in Rd position, output as Rr"), so OppFSM stages it
        # into BL/B0, not AL/A0. HandleT_STRUC was reading A0, which for
        # BST always holds whatever's staged for the (unused) Rd slot --
        # confirmed empirically: BL held the real operand while A0 stayed
        # 0 throughout a BST instruction's execution window.
        HandleT_STRUC(self, 'HT', B0, BitPos, w_topp, w_tout)
 
        HandleI_STRUC(self, 'HI', w_iopp, w_iout)
        HandleS_STRUC(self, 'HS', w_nout, w_vout, w_sopp, w_sout)
 
        # 4. Merger and Output Logic
        self.alu_merger = ALU_MergerAndLogic(self, 'ALUMerger',
            w_cout, w_zout, w_nout, w_vout, w_sout, w_hout, w_tout, w_iout, SREG_VAL)
