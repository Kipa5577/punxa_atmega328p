import py4hw
from Memory import * 

#addres of each register

## *_IO = IN and OUT instruction address
## *_LS =  LD LDS ST STS instruction address
class TimerCounter0(py4hw.Logic): #8 Bit timer 

    def __init__(self,parent,name,port:MemoryInterface):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        #creating the registers
        self.TCCR0A = 0 
        self.TCCR0A_addr_IO = 0x24
        self.TCCR0A_addr_LS = 0x44
        self.TCCR0B = 0
        self.TCCR0B_addr_IO = 0x25
        self.TCCR0B_addr_LS = 0x45
        self.OCR0A = 0
        self.OCR0A_addr_IO = 0x27
        self.OCR0A_addr_LS = 0x47
        self.OCR0B = 0
        self.OCR0B_addr_IO = 0x28 
        self.OCR0B_addr_LS = 0x48
        
        #intterupts
        self.TIMSK = 0
        self.TIMSK_addr_LS = 0x6E
        self.TIFR0 = 0
        self.TIFR0_addr_IO = 0x15
        self.TIFR0_addr_LS = 0x35


    def clock(self):
        print("nop") 

#Bit flags 
#TCCR1A
COM1A1 = 7
COM1A0 = 6
COM1B1 = 5
COM1B0 = 4
WGM11 = 1
WGM10 = 0
#TCCR1B
ICNC1 = 7
ICES1 = 6
WGM13 = 4 
WGM12 = 3
CS12 = 2
CS11 = 1 
CS10 = 0
#TCCR1C


class TimerCounter1(py4hw.Logic): #16 Bit timer

    def __init__(self,parent,name,port:MemoryInterface,OCNA,OCNB):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        #creating the registers
        self.OCR1BH = 0 
        self.OCR1BH_addr_LS = 0x8B
        self.OCR1BL = 0
        self.OCR1BH_addr_LS = 0x8A
        self.OCR1AH = 0
        self.OCR1AH_addr_LS = 0x89
        self.OCR1AL = 0
        self.OCR1AL_addr_LS = 0x89
        self.ICR1H = 0
        self.ICR1H_addr_LS = 0x87 
        self.ICR1L = 0
        self.ICR1L_addr_LS = 0x86
        self.TCNT1H = 0
        self.TCNT1H_addr_LS = 0x85
        self.TCNT1L = 0
        self.TVNT1L_addr_LS = 0x84
        self.TCCR1C = 0
        self.TCCR1C_addr_LS = 0x82
        self.TCCR1B = 0
        self.TCCR1B_addr_LS = 0x81
        self.TCCR1A = 0
        self.TCCR1A_addr_LS = 0x80

        #Interrupts:
        self.TIMSK1 = 0
        self.TIMSK1_addr_LS = 0x6F
        self.TIFR1 = 0
        self.TIFR1_addr_IO = 0x16
        self.TIFR1_addr_LS = 0x36
        self.TIFR0 = 0
        self.TIFR0_addr_IO = 0x15
        self.TIFR0_addr_LS = 0x35

class TimerCounter2(py4hw.Logic): #8 Bit timer 

    def __init__(self,parent,name,port:MemoryInterface):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        #creating the registers
        self.TCCR2A = 0 
        self.TCCR2A_addr_LS = 0xB0
        self.TCCR2B = 0
        self.TCCR2B_addr_LS = 0xB1
        self.OCR2A = 0
        self.OCR2A_addr_LS = 0xB3
        self.OCR2B = 0
        self.OCR2B_addr_LS = 0xB4
        self.TIMSK2 = 0
        self.TIMSK2_addr_LS = 0x70
        self.TIFR2 = 0
        self.TIFR2_addr_IO = 0x17
        self.TIFR2_addr_LS = 0x37


    def clock(self):