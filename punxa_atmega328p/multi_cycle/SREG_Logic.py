import py4hw 
import Memory


class SREG_Logic(py4hw.Logic):
    def __init__(self,parent,name:str,
                 SREG_In,eSREG_In,Reset,
                 SREG_Out):
        super().__init__(parent,name)

        self.SREG_IN = self.addIn('SREG_In',SREG_In)
        self.eSREG = self.addIn('eSREG_In',eSREG_In)
        self.Reset = self.addIn('Reset',Reset)
        
        self.SREG = 0

        self.SREG_OUT = self.addOut('SREG_Out',SREG_Out)

    def propagate(self):
        if self.Reset:
            self.SREG = 0

        if self.eSREG > 0:
            self.SREG = (self.SREG & ~self.eSREG) | (self.SREG_IN & self.eSREG)

        self.SREG_OUT = self.SREG
            
        
        
