import py4hw 

class OperandBuffer(py4hw.Logic):

    def __init__(self, parent, name,
                 DATAInterface,K,WE,Reset,
                 A0,A1,B0,B1,IOout):
        super().__init__(parent, name)


        self.DATA = self.addIn('DATA',DATAInterface)
        self.K = self.addIn('K',K)
        self.Reset = self.addIn('Reset',Reset)
        self.WE = self.addIn('WE',WE)


        self.A0 = self.addOut('A0',A0)
        self.A1 = self.addOut('A1',A1)
        self.B0 = self.addOut('B0',B0)
        self.B1 = self.addOut('B1',B1)
        self.IOout = self.addOut('IO',IOout)

        self.valueRd0 = 0
        self.valueRd1 = 0
        self.valueRr0 = 0
        self.valueRr1 = 0

        self.IOBuffer = 0


    def Clock(self):

        if self.Reset.get():
            self.valueRd0 = 0
            self.valueRd1 = 0
            self.valueRr0 = 0
            self.valueRr1 = 0
            self.IOBuffer = 0
        else:

            if self.WE.get() == 1:
                self.valueRd0 = self.DATA.get() & 0xFF

            if self.WE.get() == 2:
                self.valueRd1 = self.DATA.get() & 0xFF

            if self.WE.get() == 3:
                self.valueRr0 = self.DATA.get() & 0xFF

            if self.WE.get() == 4:
                self.valueRr1 = self.DATA.get() & 0xFF

            if self.WE.get() == 5:
                self.IOBuffer = self.IOBuffer.get() & 0xFF

        self.A0.put(self.valueRd0)
        self.A1.put(self.valueRd1)
        self.B0.put(self.valueRr0)
        self.B1.put(self.valueRr1)

        self.IOout.put(self.IOBuffer)