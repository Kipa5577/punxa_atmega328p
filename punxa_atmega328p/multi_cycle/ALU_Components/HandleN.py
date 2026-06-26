import py4hw

class HandleN(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Res, Mode,
                 Nout):
        super().__init__(parent, name) # Fixed syntax error here

        self.Res = self.addIn('Res', Res)
        self.Mode = self.addIn('Mode', Mode)

        self.Nout = self.addOut('Nout', Nout)

    def propagate(self):
        mode = self.Mode.get()
        res = self.Res.get()

        N_out = 0 
        
        if mode == 0:
            # Mode 0: Force Clear (CLN instruction, or logic overrides)
            N_out = 0

        elif mode == 1:
            # Mode 1: Force Set (SEN instruction)
            N_out = 1 

        elif mode == 2:
            # Mode 2: Standard 8-bit Signed Operations (ADD, SUB, AND, OR, INC, DEC, etc.)
            # Extract the 7th bit of the result
            N_out = (res >> 7) & 1

        elif mode == 3:
            # Mode 3: 16-bit Word/Multiply Operations (ADIW, SBIW, MUL, MULS, etc.)
            # Extract the 15th bit of the 16-bit result
            N_out = (res >> 15) & 1

        # 3. Output the calculated bit to the wire
        self.Nout.put(N_out & 1)