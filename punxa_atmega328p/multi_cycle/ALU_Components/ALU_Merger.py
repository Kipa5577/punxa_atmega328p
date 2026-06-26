import py4hw

class ALU_Merger(py4hw.Logic):
    """
    Behavioral leaf component that merges individual flags back into the SREG bus, 
    bridges the AU results to the ALU outputs, and computes Branch and Skip conditions.
    """
    def __init__(self, parent, name,
             w_cout, w_zout, w_nout, w_vout, w_sout, w_hout, w_tout, w_iout,
             sreg_val): 

        super().__init__(parent, name)
        
        # --- Inputs: Individual Flags calculated by Handlers ---
        self.w_cout = self.addIn('w_cout', w_cout)
        self.w_zout = self.addIn('w_zout', w_zout)
        self.w_nout = self.addIn('w_nout', w_nout)
        self.w_vout = self.addIn('w_vout', w_vout)
        self.w_sout = self.addIn('w_sout', w_sout)
        self.w_hout = self.addIn('w_hout', w_hout)
        self.w_tout = self.addIn('w_tout', w_tout)
        self.w_iout = self.addIn('w_iout', w_iout)
        

        # --- Outputs ---
        self.sreg_val = self.addOut('sreg_val', sreg_val)


    def propagate(self):

        # 2. SREG Merging: Standard AVR Order: I(7), T(6), H(5), S(4), V(3), N(2), Z(1), C(0)
        new_sreg = ((self.w_iout.get() & 1) << 7) | \
                   ((self.w_tout.get() & 1) << 6) | \
                   ((self.w_hout.get() & 1) << 5) | \
                   ((self.w_sout.get() & 1) << 4) | \
                   ((self.w_vout.get() & 1) << 3) | \
                   ((self.w_nout.get() & 1) << 2) | \
                   ((self.w_zout.get() & 1) << 1) | \
                   (self.w_cout.get() & 1)
        self.sreg_val.put(new_sreg)
