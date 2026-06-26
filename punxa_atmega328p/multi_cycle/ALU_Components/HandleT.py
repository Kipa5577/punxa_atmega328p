import py4hw

class HandleT(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Rr, BitPos, Mode,
                 Tout):
        super().__init__(parent, name)

        # Inputs
        self.Rr = self.addIn('Rr', Rr)
        self.BitPos = self.addIn('BitPos', BitPos)
        self.Mode = self.addIn('Mode', Mode)
        
        # Output
        self.Tout = self.addOut('Tout', Tout)

    def propagate(self):
        # 1. Read input values
        rr = self.Rr.get()
        bit_pos = self.BitPos.get()
        mode = self.Mode.get()

        # Default T Out
        t_out = 0

        # 2. Mode Routing
        if mode == 0:
            # Mode 0: Force Clear (CLT instruction)
            t_out = 0
            
        elif mode == 1:
            # Mode 1: Force Set (SET instruction)
            t_out = 1
            
        elif mode == 2:
            # Mode 1: Bit Store (BST instruction)
            # We shift the register to the right by 'bit_pos' places, 
            # then mask it with 1 to extract strictly that target bit.
            t_out = (rr >> (bit_pos & 7)) & 1

        # Note: BLD (Bit Load) does not have a mode here because BLD 
        # reads the T flag to update a register; it does not write to the T flag.

        # 3. Output the calculated bit
        self.Tout.put(t_out & 1)