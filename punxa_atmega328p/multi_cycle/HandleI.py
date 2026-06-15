import py4hw


class HandleI(py4hw.Logic):
    def __init__(self, parent, name:str,
                 Mode,
                 Iout):
        super().__init__(parent, name:str)

        self.Mode =  self.addIn('Mode',Mode)

        self.Iout = self.addIn('Iout',Iout)


    def propagate(self):
        mode = self.Mode.get()

        I_out = 0

        if mode == 0:
            # Mode 0: Force Clear (CLI instruction)
            I_out = 0

        elif mode == 1:
            # Mode 1: Force Clear (SEI instruction)
            I_out = 1 
        

        self.Iout.put()


