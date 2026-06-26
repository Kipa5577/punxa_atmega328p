import py4hw 

class OperandBuffer(py4hw.Logic):

    def __init__(self, parent, name,
                 OB_DATA_IN,
                 OB_K,
                 OB_WE,
                 OB_Reset,
                 OB_InputSelectBuffer,
                 OB_A0,
                 OB_A1,
                 OB_B0,
                 OB_B1,
                 OB_IOout):
        super().__init__(parent, name)


        self.DATA = self.addIn('OB_DATA_IN',OB_DATA_IN)
        self.K = self.addIn('OB_K',OB_K)
        self.Reset = self.addIn('OB_Reset',OB_Reset)
        self.WE = self.addIn('OB_WE',OB_WE)
        self.InputSelectBuffer = self.addIn('OB_InputSelectBuffer',OB_InputSelectBuffer)


        self.A0 = self.addOut('OB_A0',OB_A0)
        self.A1 = self.addOut('OB_A1',OB_A1)
        self.B0 = self.addOut('OB_B0',OB_B0)
        self.B1 = self.addOut('OB_B1',OB_B1)
        self.IOout = self.addOut('IO',OB_IOout)

        self.valueRd0 = 0
        self.valueRd1 = 0
        self.valueRr0 = 0
        self.valueRr1 = 0

        self.IOBuffer = 0


    def clock(self):

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
                self.valueRr0 = self.DATA.get() & 0xFF if self.InputSelectBuffer.get() == 1 else self.K.get()

            if self.WE.get() == 4:
                self.valueRr1 = self.DATA.get() & 0xFF

            if self.WE.get() == 5:
                self.IOBuffer = self.DATA.get() & 0xFF


        self.A0.put(self.valueRd0)
        self.A1.put(self.valueRd1)
        self.B0.put(self.valueRr0)
        self.B1.put(self.valueRr1)

        self.IOout.put(self.IOBuffer)