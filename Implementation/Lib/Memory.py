import py4hw
#2048 bytes of ram
#32256 of rom 



class ProgramMemory(py4hw.Logic):
    def __init__(self,parent,name,ADRESS,DATA_IN,DATA_OUT, Write_Enable): #RW = 0 then R else W
        super().__init__(parent, name)

        self.ADRESS = self.addIn('ADRESS', ADRESS)
        self.memory = [0]*32256 #address_width data_width
        self.DATA_OUT = self.addOut('DATA_OUT', DATA_OUT)
        self.DATA_IN = self.addIn('DATA_IN',DATA_IN)
        self.Write_Enable = self.addIn('Write_Enable',Write_Enable)

        def clock(self):
            if self.Write_Enable.get() == 1:
                self.DATA_OUT.prepare(self.memory[self.ADRESS.get()])
            else: 
                self.memory[self.ADRESS.get()] = self.DATA_IN
