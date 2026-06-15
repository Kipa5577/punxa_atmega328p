import py4hw 
import Memory
import AU
import ALU_ConfCodeCalc # Corrected from 'import ALU'

import HandleC
import HandleH
import HandleI
import HandleN
import HandleT
import HandleS
import HandleV
import HandleZ

class ALU(py4hw.Logic):
    def __init__(self, parent, name:str,
                 ImputRegA0, ImputRegA1, ImputRegB0, ImputRegB1, ALUInstruction, SREG_STATE, BitPos, IOreg, Bit_To_Test, BranchOpp, BranchIns,
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
        self.Bit_To_Test = self.addIn('Bit_To_Test', Bit_To_Test)
        self.BranchOpp = self.addIn('BranchOPP', BranchOpp)
        self.BranchIns = self.addIn('BranchIns', BranchIns)

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
        self.w_arith_ctrl = py4hw.Wire(self, 'w_arith_ctrl')
        self.w_copp = py4hw.Wire(self, 'w_copp')
        self.w_zopp = py4hw.Wire(self, 'w_zopp')
        self.w_nopp = py4hw.Wire(self, 'w_nopp')
        self.w_vopp = py4hw.Wire(self, 'w_vopp')
        self.w_sopp = py4hw.Wire(self, 'w_sopp')
        self.w_hopp = py4hw.Wire(self, 'w_hopp')
        self.w_topp = py4hw.Wire(self, 'w_topp')
        self.w_iopp = py4hw.Wire(self, 'w_iopp')

        # AU Results
        self.w_res_l = py4hw.Wire(self, 'w_res_l')
        self.w_res_h = py4hw.Wire(self, 'w_res_h')

        # Individual Flag Inputs (Split from SREG_STATE bus)
        self.w_cin = py4hw.Wire(self, 'w_cin')
        self.w_zin = py4hw.Wire(self, 'w_zin')
        self.w_nin = py4hw.Wire(self, 'w_nin')
        self.w_vin = py4hw.Wire(self, 'w_vin')

        # Individual Flag Outputs (Calculated by Handlers)
        self.w_cout = py4hw.Wire(self, 'w_cout')
        self.w_zout = py4hw.Wire(self, 'w_zout')
        self.w_nout = py4hw.Wire(self, 'w_nout')
        self.w_vout = py4hw.Wire(self, 'w_vout')
        self.w_sout = py4hw.Wire(self, 'w_sout')
        self.w_hout = py4hw.Wire(self, 'w_hout')
        self.w_tout = py4hw.Wire(self, 'w_tout')
        self.w_iout = py4hw.Wire(self, 'w_iout')

        # ==========================================
        # SUB-COMPONENT INSTANTIATION
        # ==========================================
        
        # 1. Configuration & Control Unit
        self.conf_calc = ALU_ConfCodeCalc.ALU_ConfCodeCalc(self, 'ConfCalc',
            self.ALUins, self.w_arith_ctrl, self.w_copp, self.w_zopp, self.w_nopp,
            self.w_vopp, self.w_sopp, self.w_hopp, self.w_topp, self.w_iopp, self.eSREG_VAL)

        # 2. Arithmetic Unit
        self.au = AU.AU(self, 'AU',
            self.w_cin, self.ImputRegA0, self.ImputRegA1, self.ImputRegB0, self.ImputRegB1,
            self.w_arith_ctrl, self.w_res_l, self.w_res_h)

        # 3. Flag Handlers
        # Note: Depending on your exact schematic, ImputRegA0 is usually Rd (Destination) 
        # and ImputRegB0 is Rr (Source) for 8-bit operations.
        self.handle_c = HandleC.HandleC(self, 'HC', self.ImputRegB0, self.ImputRegA0, self.w_res_l, self.w_cin, self.w_copp, self.w_cout)
        self.handle_z = HandleZ.HandleZ(self, 'HZ', self.w_res_l, self.w_zin, self.w_zopp, self.w_zin, self.w_zout) 
        self.handle_n = HandleN.HandleN(self, 'HN', self.w_res_l, self.w_nopp, self.w_nout)
        self.handle_v = HandleV.HandleV(self, 'HV', self.ImputRegB0, self.ImputRegA0, self.w_res_l, self.w_nin, self.w_vopp, self.w_vout)
        self.handle_h = HandleH.HandleH(self, 'HH', self.ImputRegB0, self.ImputRegA0, self.w_res_l, self.w_hopp, self.w_hout)
        self.handle_t = HandleT.HandleT(self, 'HT', self.ImputRegA0, self.BitPos, self.w_topp, self.w_tout)
        self.handle_i = HandleI.HandleI(self, 'HI', self.w_iopp, self.w_iout)
        
        # Sign flag logic uses the *newly calculated* N and V flags (not the old ones)
        self.handle_s = HandleS.HandleS(self, 'HS', self.w_nout, self.w_vout, self.w_sopp, self.w_sout)


    def propagate(self):
        # ==========================================
        # SREG BUS SPLITTING
        # ==========================================
        sreg = self.SREG_state.get()

        # Extract bits based on Standard AVR Order: I(7), T(6), H(5), S(4), V(3), N(2), Z(1), C(0)
        c_val = sreg & 1
        z_val = (sreg >> 1) & 1
        n_val = (sreg >> 2) & 1
        v_val = (sreg >> 3) & 1
        
        # Feed the old states into the internal wires so sub-components can read them
        self.w_cin.put(c_val)
        self.w_zin.put(z_val)
        self.w_nin.put(n_val)
        self.w_vin.put(v_val)

        # ==========================================
        # RESULT BRIDGING
        # ==========================================
        # Pass the internal AU result wires directly to the ALU output pins
        self.OUTByte0.put(self.w_res_l.get())
        self.OUTByte1.put(self.w_res_h.get())

        # ==========================================
        # SREG BUS MERGING
        # ==========================================
        new_c = self.w_cout.get() & 1
        new_z = self.w_zout.get() & 1
        new_n = self.w_nout.get() & 1
        new_v = self.w_vout.get() & 1
        new_s = self.w_sout.get() & 1
        new_h = self.w_hout.get() & 1
        new_t = self.w_tout.get() & 1
        new_i = self.w_iout.get() & 1

        # Pack individual flags back into an 8-bit bus
        new_sreg = (new_i << 7) | (new_t << 6) | (new_h << 5) | (new_s << 4) | (new_v << 3) | (new_n << 2) | (new_z << 1) | new_c
        self.SREG_VAL.put(new_sreg)

        # ==========================================
        # BRANCH LOGIC
        # ==========================================
        branch_ins = self.BranchIns.get()
        branch_opp = self.BranchOpp.get()

        branch_out = 0
        if branch_ins == 1:
            # Assuming BranchOPP is 4 bits: Bit 3 is polarity (1=Set, 0=Clear), Bits 0-2 are Flag Index (0-7)
            flag_idx = branch_opp & 0x07
            polarity = (branch_opp >> 3) & 1
            flag_val = (sreg >> flag_idx) & 1
            
            if flag_val == polarity:
                branch_out = 1
                
        self.BRANCH.put(branch_out)

        # ==========================================
        # SKIP LOGIC
        # ==========================================
        bit_pos = self.Bit_To_Test.get()
        io_val = self.IOreg.get()

        # Extract the specific bit requested to test for skip conditions (e.g. SBRC, SBIC)
        skip_out = (io_val >> (bit_pos & 7)) & 1
        self.SKIP.put(skip_out)