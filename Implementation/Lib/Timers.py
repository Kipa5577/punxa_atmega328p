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


class TimerCounter1(py4hw.Logic): #16 Bit timer

    def __init__(self,parent,name,port:MemoryInterface,OCNA,OCNB):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        #creating the registers
        self.OCR1BH = 0 
        self.OCR1BL = 0
        self.OCR1AH = 0
        self.OCR1AL = 0
        self.ICR1H = 0
        self.ICR1L = 0
        self.TCNT1H = 0
        self.TCNT1L = 0

        self.TCCR1C = 0
        self.TCCR1B = 0
        self.TCCR1A = 0

        #Interrupts:
        self.TIMSK1 = 0
        self.TIFR1 = 0
        self.TIFR0 = 0

class TimerCounter2(py4hw.Logic): #8 Bit timer 

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