import py4hw

class HandleS(py4hw.Logic):
    def __init__(self, parent, name: str,
                 N, V, Mode,
                 Sout):
        super().__init__(parent, name)

        # Inputs
        self.N = self.addIn('N', N)
        self.V = self.addIn('V', V)
        self.Mode = self.addIn('Mode', Mode)
        
        # Output
        self.Sout = self.addOut('Sout', Sout)

    def propagate(self):
        # 1. Read input values
        n_flag = self.N.get()
        v_flag = self.V.get()
        mode = self.Mode.get()

        # Default S Out
        s_out = 0

        # 2. Mode Routing
        if mode == 0:
            # Mode 0: Force Clear (CLS instruction)
            s_out = 0
            
        elif mode == 1:
            # Mode 1: Force Set (SES instruction)
            s_out = 1
            
        elif mode == 2:
            # Mode 1: Standard Sign Logic (ADD, SUB, AND, OR, INC, DEC, NEG, etc.)
            # The S flag is the logical XOR of the N and V flags
            s_out = (n_flag & 1) ^ (v_flag & 1)

        # 3. Output the calculated bit
        self.Sout.put(s_out & 1)