import py4hw
from Memory import * 

#addres of each register


class TimerCounter0(py4hw.Logic): #8 Bit timer 

    def __init__(self,parent,name,port:MemoryInterface):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        #creating the registers
        self.TCCR0A = 0 
        self.TCCR0B = 0
        self.OCR0A = 0
        self.OCR0B = 0
        self.TIMSK = 0
        self.TIFR0 = 0


    def clock(self):


class TimerCounter1
