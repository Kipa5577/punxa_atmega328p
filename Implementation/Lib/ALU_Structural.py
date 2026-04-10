import py4hw


import AU
import LU



class ALU_Structural(py4hw.Logic):

    def __init__(self,parent,name,on,H,S,V,N,Z,C,T,I,opp,OUT):
        super().__init__(parent,name)

        self.on = self.addIn('on',on)
