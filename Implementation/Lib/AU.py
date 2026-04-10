import py4hw



class AUBehavioral(py4hw.Logic):

    def __init__(self,parent,name,on,A,B,OUT,opp,H,S,V,N,Z,C,REG2_OUT):# REG2_OUT is 2 register output
        super().__init__(parent, name)

        self.on = self.addIn('on',on)
        self.A =self.addIn('A', A )
        self.B =self.addIn('B', B)
        self.opp=self.addIn('opp',opp)
        self.OUT =self.addOut('OUT', OUT)
        self.REG2_OUT =self.addOu('MUL_OUT',REG2_OUT)

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
                case 'ADD' : #'ADD'
                    #self.OUT.prepare(self.A.get()+self.B.get())
                    res = self.A.get()+self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 'ADC' : #'ADD'
                    #self.OUT.prepare(self.A.get()+self.B.get())
                    res = self.A.get()+self.B.get()+self.C.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 'SUB' : # 'SUB'
                    #self.OUT.prepare(self.A.get()-self.B.get())
                    res = self.A.get()-self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 'SBC' : # 'SUB'
                    #self.OUT.prepare(self.A.get()-self.B.get())
                    res = self.A.get()-self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 'AND' : # 'AND'
                    #self.OUT.prepare(self.A.get()&self.B.get()) 
                    res = self.A.get()&self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.V.prepare(0)
                    self.OUT.prepare(res)

                case 'OR' : # 'OR'
                    #self.OUT.prepare(self.A.get()|self.B.get())
                    res = self.A.get()|self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 'TST' : # 'TST'
                    #self.OUT.prepare(self.A.get()|self.B.get())
                    res = self.A.get()&self.B.get()
                    self.testS()
                    self.testZ(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 'MUL' : # 'MUL'
                    #self.OUT.prepare(self.A.get()|self.B.get())
                    res = self.A.get()*self.B.get()
                    self.testC(res)
                    self.testZ(res)
                    self.REG2_OUT.prepare(res)

                case 'EOR' : # 'EOR'
                    #self.OUT.prepare(self.A.get()^self.B.get())
                    res = self.A.get()^self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.OUT.prepare(res)

                case 'CP' : # 'EOR'
                    #self.OUT.prepare(self.A.get()^self.B.get())
                    res = self.A.get()-self.B.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.testV(res)
                    self.testS()
                    self.testH(res)

                case 'CPC' : # 'EOR'
                    #self.OUT.prepare(self.A.get()^self.B.get())
                    res = self.A.get()-self.B.get()-self.C.get()
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.testV(res)
                    self.testS()
                    self.testH(res)

                case 'LSL' : # 'EOR'
                    #self.OUT.prepare(self.A.get()^self.B.get())
                    res = self.A.get()<<1
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.testV(res)
                    self.testS()
                    self.testH(res)
                    self.OUT.prepare(res)

                case 'LSR' : # 'EOR'
                    #self.OUT.prepare(self.A.get()^self.B.get())
                    res = self.A.get()>>1
                    self.testZ(res)
                    self.testC(res)
                    self.testN(res)
                    self.testV(res)
                    self.testS()
                    self.testH(res)
                    self.OUT.prepare(res)

                case 'ROR' : # 'ROR'
                    c = self.C.get()
                    self.C.prepare(self.A.get()[0])
                    res = self.A.get()>>1
                    res[7] = c 
                    self.testZ(res)
                    self.testN(res)
                    self.testV(res)
                    self.testS()
                    self.OUT.prepare(res)
                    
                case 'ROL' : # 'ROR'
                    c = self.C.get()
                    self.C.prepare(self.A.get()[7])
                    res = self.A.get()<<1
                    res[0] = c 
                    self.testZ(res)
                    self.testN(res)
                    self.testV(res)
                    self.testS()
                    self.OUT.prepare(res)

                case 'ASR' : # 'ASR'
                    self.C.prepare(self.A.get()[0])
                    res = self.A.get()>>1|self.A.get()&0x80
                    self.testZ(res)
                    self.testN(res)
                    self.testV(res)
                    self.testS()
                    self.OUT.prepare(res)

                case 'SWAP' : # 'ASR'
                    res = self.A.get()>>4|self.A.get()<<4
                    self.OUT.prepare(res)

                case 'CLR':
                    res = self.A.get()^self.B.get()
                    self.S.prepare(0)
                    self.V.prepare(0)
                    self.N.prepare(0)
                    self.Z.prepare(1)
                    self.OUT.prepare(res)
                
                #flag set instructions 
                case 'SEC' : 
                    self.C.prepare(1)
                case 'CLC' :
                    self.C.prepare(0)
                case 'SEN' :
                    self.N.prepare(1)
                case 'CLN' :
                    self.N.prepare(0)
                case 'SEZ' :
                    self.Z.prepare(1)
                case 'CLZ' :
                    self.Z.prepare(0)
                case 'SES' : 
                    self.S.prepare(1)
                case 'CLS' :
                    self.S.prepare(0)
                case 'SEV' :
                    self.V.prepare(1)
                case 'CLV' :
                    self.V.prepare(0)
                case 'SEH' :
                    self.H.prepare(1)
                case 'CLH' :
                    self.H.prepare(0)

                 

