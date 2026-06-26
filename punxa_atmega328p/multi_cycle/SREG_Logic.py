import py4hw 


class SREG_Logic(py4hw.Logic):
    def __init__(self,parent,name:str,
                 SREG_In,eSREG_In,SREG_Reset,
                 SREG_Out):
        super().__init__(parent,name)

        self.SREG_IN = self.addIn('SREG_In',SREG_In)
        self.eSREG = self.addIn('eSREG_In',eSREG_In)
        self.SREG_Reset = self.addIn('SREG_Reset',SREG_Reset)
        
        self.SREG = 0

        self.SREG_OUT = self.addOut('SREG_Out',SREG_Out)

    def clock(self):
        if self.SREG_Reset.get():
            self.SREG = 0

        if self.eSREG.get() > 0:
            self.SREG = (self.SREG & ~self.eSREG.get()) | (self.SREG_IN.get() & self.eSREG.get())
        self.SREG_OUT.prepare(self.SREG)
