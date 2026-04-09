import py4hw



class AUBehavioral(py4hw.Logic):

    def __init__(self,parent,name,on,A,B,OUT,opp,H,S,V,N,Z,C):#
        super().__init__(parent, name)

        self.on = self.addIn('on',on)
        self.A =self.addIn('A', A )
        self.B =self.addIn('B', B)
        self.opp=self.addIn('opp',opp)
        self.OUT =self.addOut('OUT', OUT)

        #flags
        self.Z = self.addOut('Z',Z)
        self.C = self.addOut('C',C)
        self.N = self.addOut('N',N)
        self.H = self.addOut('H',H)
        self.S = self.addOut('S',S)
        self.V = self.addOut('V',V)


    def testZ(self,val):
        if val == 0 :
            self.Z.prepare(1)
        else:
            self.Z.prepare(0)
    def testC(self,val):
        if (val>>8) == 1 :
            self.C.prepare(1)
        else:
            self.C.prepare(0)
    def testN(self,val):
        if val < 0 :
            self.N.prepare(1)
        else:
            self.N.prepare(0)
    def testV(self,val):
        if (self.A.get()< 0 and self.B.get()< 0) and val>0 : 
            self.V.prepare(1)
        elif (self.A.get()>0 and self.B.get()>0) and val<0 : 
            self.V.prepare(1)
        else:
            self.V.prepare(0)
    def testH(self,val):
        if(self.A.get()[3] or self.B.get()[3] and self.B.get()[3] or not val[3] and not val[3] and self.A.get()[3]):
            self.H.prepare(1)
        else:
            self.H.prepare(0)
    def testS(self):
        self.S.prepare(self.N.get()^self.V.get()) 

    def clock(self):
        if(self.on.get() == 1):
            match self.opp.get():
                case 0b000011 : #'ADD'
                    #self.OUT.prepare(self.A.get()+self.B.get())
                    res = self.A.get()+self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 0b000110 : # 'SUB'
                    #self.OUT.prepare(self.A.get()-self.B.get())
                    res = self.A.get()-self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 0b001000 : # 'AND'
                    #self.OUT.prepare(self.A.get()&self.B.get()) 
                    res = self.A.get()&self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.V.prepare(0)
                    self.OUT.prepare(res)

                case 0b001010 : # 'OR'
                    #self.OUT.prepare(self.A.get()|self.B.get())
                    res = self.A.get()|self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 0b001001 : # 'EOR'
                    #self.OUT.prepare(self.A.get()^self.B.get())
                    res = self.A.get()^self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)