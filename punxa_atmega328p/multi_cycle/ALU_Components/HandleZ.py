import py4hw

class HandleZ(py4hw.Logic):
    def __init__(self, parent, name: str,
                 Res, Mode, Zprev, Zout):
        super().__init__(parent, name)
        
        # Inputs
        self.Res = self.addIn('Res', Res)
        self.Mode = self.addIn('Mode', Mode)
        
        # Zprev is strictly required for accurate SBC/CPC chained comparisons
        self.Zprev = self.addIn('Zprev', Zprev)
        
        # Output
        self.Zout = self.addOut('Zout', Zout)
    
    def propagate(self):
        # 1. Read input values
        res = self.Res.get()
        mode = self.Mode.get()
        z_prev = self.Zprev.get()

        # Default Zero Out
        z_out = 0

        # 2. Mode Routing
        if mode == 0:
            # Mode 0: Explicit Clear (CLZ)
            z_out = 0

        elif mode == 1:
            # Mode 0: Explicit Set (SEZ)
            z_out = 1

        elif mode == 2:
            # Mode 1: 8-bit Standard operations (ADD, SUB, AND, OR, INC, etc.)
            # Z = 1 if the 8-bit result is exactly 0x00
            z_out = 1 if (res & 0xFF) == 0 else 0

        elif mode == 3:
            # Mode 2: 16-bit Standard operations (ADIW, SBIW, MUL family)
            # Z = 1 if the 16-bit result is exactly 0x0000
            z_out = 1 if (res & 0xFFFF) == 0 else 0

        elif mode == 4:
            # Mode 3: Chained 8-bit Subtraction / Compare (SBC, SBCI, CPC)
            # Z = Z_prev AND (Result == 0x00)
            # This ensures that in multi-byte math, a previous non-zero byte keeps Z=0
            current_z = 1 if (res & 0xFF) == 0 else 0
            z_out = (z_prev & 1) & current_z

        elif mode == 5:
            current_z = 1 if (res & 0xFF) == 0 else 0
            z_out =  (z_prev & 1) & current_z


        # 3. Put calculated bit on the output wire
        self.Zout.put(z_out & 1)