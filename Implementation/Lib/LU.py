import py4hw

class LUBehavioral(py4hw.Logic):

    def __init__(self,parent,name,on,H,S,V,N,Z,C,T,I,opp,OUT):
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
        self.T = self.addIn('T',T)
        self.I = self.addIn('I',I)


    def clock(self):
        if(self.on.get() == 1 ):
            match self.opp.get():
                
                case 'BREQ':
                    if self.Z.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case  'BRNE':
                    if self.Z.get() == 0:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case  'BRCS' :
                    if self.C.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)
                
                case 'BRCC' : 
                    if self.C.get() == 0:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case 'BRSH' :
                    if self.C.get() == 0:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case 'BRLO' :
                    if self.C.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case 'BRMI' : 
                    if self.N.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)
                
                case 'BRPL' :
                    if self.N.get() == 0:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)
                
                case 'BRGE' :
                    if self.S.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)
                
                case 'BRLT' :
                    if self.S.get() == 0:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case 'BRHS' :
                    if self.H.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case 'BRHC' : 
                    if self.H.get() == 0:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case 'BRTS' :
                    if self.T.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)
                
                case 'BRTC' :
                    if self.T.get() == 0:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)
                
                case 'BRVS' :
                    if self.V.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)
                
                case 'BRVC' :
                    if self.V.get() == 0:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                case 'BRIE' :
                    if self.I.get() == 1:
                        self.OUT.prepare(1)
                    else:
                        self.OUT.prepare(0)

                    
