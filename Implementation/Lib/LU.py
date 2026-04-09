import py4hw

class LUBehavioral(py4hw.Logic):

    def __init__(self,parent,name,on,H,S,V,N,Z,C,opp,OUT):
        super().__init__(parent,name)

        self.on = self.addIn('on',on)
        self.opp=self.addIn('opp',opp)
        self.OUT =self.addOut('OUT', OUT)

        #flags
        self.Z = self.addIn('Z',Z)
        self.C = self.addIn('C',C)
        self.N = self.addIn('N',N)
        self.H = self.addIn('H',H)
        self.S = self.addIn('S',S)
        self.V = self.addIn('V',V)


    def clock(self):
        if(self.on.get() == 1 ):
            match self.opp.get():
                
                case    :


                case    :


                case    :