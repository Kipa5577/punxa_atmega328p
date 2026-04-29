import py4hw
from Memory import * 

#addres of each register

## *_IO = IN and OUT instruction address
## *_LS =  LD LDS ST STS instruction address
class TimerCounter0(py4hw.Logic): #8 Bit timer 

    def __init__(self,parent,name,port:MemoryInterface,INSTYPE,OC0B,OC0A,T0): # Signals to outside OC0B OC0A  
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        self.INSTYPE = self.addIn('INSTYPE',INSTYPE)
        self.T0 = self.addIn('T0',T0)
        self.OC0B = self.addOut('OC0B',OC0B)
        self.OC0A = self.addOut('OC0A',OC0A)

        #creating the registers
        self.TCCR0A = 0 #Bit7:COM0A1 Bit6: COM0A0 Bit5: COM0B1 Bit4: COM0B0  Bit3: - Bit2: - Bit1: WGM01 Bit0: WGM00 
        self.TCCR0A_addr_IO = 0x24
        self.TCCR0A_addr_LS = 0x44
        self.TCCR0B = 0 #Bit7: FOC0A Bit6: FOC0B Bit5: - Bit4: - Bit3: WGM02 Bit2: CS02 Bit2: CS01 Bit1: CS00
        self.TCCR0B_addr_IO = 0x25
        self.TCCR0B_addr_LS = 0x45

        self.TCNT0 = 0
        self.TCNT0_addr_IO = 0x26
        self.TCNT0_addr_LS = 0x46
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

        self.ADDR = 0

        self.prescaler = 0
        self.prescalerCounter = 0

        ## Control bits
        #TCCR0A
        self.COM0A1 = 0
        self.COM0A0 = 0 
        self.COM0B1 = 0
        self.COM0B0 = 0 
        self.WGM01 = 0
        self.WGM00 = 0

        #TCCR0B
        self.FOC0B = 0 
        self.FOC0B = 0
        self.WGM02 = 0
        self.CS02 = 0
        self.CS01 = 0
        self.CS00 = 0

        self.OC0A = 0 # This shold be an output and bit 
        self.OC1B = 0

        self.increment = True 
        self.PrevT0 = 0

        self.opMode = 'Normal'
        self.TOP = 0xFF

    def clock(self):
        #The register load or read
        self.ADDR = self.port0.address.get()
        if ((self.ADDR == self.TCCR0A_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TCCR0A_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCCR0A)
                self.port0.resp.prepare(0)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCCR0A = self.port0.write_data.get()
                self.port0.resp.prepare(0)
            else:
                self.port0.resp.prepare(1)
        elif ((self.ADDR == self.TCCR0B_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TCCR0B_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(0)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(0)
            else:
                self.port0.resp.prepare(1)
        elif ((self.ADDR == self.TCNT0_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TCNT0_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(0)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(0)
            else:
                self.port0.resp.prepare(1)
        elif ((self.ADDR == self.OCR0A_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.OCR0A_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(0)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(0)
            else:
                self.port0.resp.prepare(1)
        elif ((self.ADDR == self.OCR0B_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.OCR0B_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(0)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(0)
            else:
                self.port0.resp.prepare(1)
        elif ((self.ADDR == self.TIFR0_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TIFR0_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(0)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(0)
            else:
                self.port0.resp.prepare(1)
        elif ((self.ADDR == self.TIMSK_addr_LS) and self.INSTYPE.get() == 0):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(0)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(0)
            else:
                self.port0.resp.prepare(1)
        
        
        # Parameter parsing
        #TCCR0B
        self.FOC0A = (self.TCCR0B&0b1<<7)>>7
        self.FOC0B = (self.TCCR0B&0b1<<6)>>6
        self.WGM02 = (self.TCCR0B&0b1<<3)>>3
        self.CS02 = (self.TCCR0B&0b1<<2)>>2
        self.CS01 = (self.TCCR0B&0b1<<1)>>1
        self.CS00 = (self.TCCR0B&0b1<<0)>>0

        #TCCR0A
        self.COM0A1 = (self.TCCR0A&0b1<<7)>>7
        self.COM0A0 = (self.TCCR0A&0b1<<6)>>6 
        self.COM0B1 = (self.TCCR0A&0b1<<5)>>5
        self.COM0B0 = (self.TCCR0A&0b1<<4)>>4 
        self.WGM01 = (self.TCCR0A&0b1<<1)>>1
        self.WGM00 = (self.TCCR0A&0b1<<0)>>0
        
        #prescaler set up 
        if (self.CS02 == 0) and  (self.CS01 == 0) and (self.CS00 == 0): # No clock Source
            self.prescaler = 0 
            self.increment = False

        elif (self.CS02 == 0) and  (self.CS01 == 0) and (self.CS00 == 1): # clk/(no prescaling)
            self.prescaler = 0

        elif (self.CS02 == 0) and  (self.CS01 == 1) and (self.CS00 == 0): # clk/8 
            self.prescaler = 8

        elif (self.CS02 == 0) and  (self.CS01 == 1) and (self.CS00 == 1): # clk/64
            self.prescaler = 64  

        elif (self.CS02 == 1) and  (self.CS01 == 0) and (self.CS00 == 0): # clk/256
            self.prescaler = 256

        elif (self.CS02 == 1) and  (self.CS01 == 0) and (self.CS00 == 1): # clk/1024
            self.prescaler = 1024

        elif (self.CS02 == 1) and  (self.CS01 == 1) and (self.CS00 == 0): # External clock on T0 pin. Clock on falling edge.
            if (self.PrevT0 == 1 and self.T0.get() == 0):
            
            self.PrevT0 = self.T0.get()

        elif (self.CS02 == 1) and  (self.CS01 == 1) and (self.CS00 == 1): # External clock on T0 pin. Clock on rising edge.
            if (self.PrevT0 == 0 and self.T0.get() == 1):
                self.increment = True
            self.PrevT0 = self.T0.get()


        if self.increment == True: 
            self.TCNT0 += 1
            self.increment = False  
        else:
            print("test")



        #if (self.COM0B1 == 0) and (self.COM0B0 == 0): ## OC0B disconected 
                
        #elif (self.COM0B1 == 0) and (self.COM0B0 == 0): # Toggle OC0B on compare match 

        #elif (self.COM0B1 == 1) and (self.COM0B0 == 0): # Clear OC0B on compare match 

        #elif (self.COM0B1 == 1) and (self.COM0B0 == 1): # Set OC0B on compare match 



        #if

        #waveform generation mode 
        if (self.WGM02 == 0) and (self.WGM01 == 0) and (self.WGM00 == 0):   #0
            self.opMode = 'NORMAL'
            self.TOP =  0xFF

        elif (self.WGM02 == 0) and (self.WGM01 == 0) and (self.WGM00 == 1): #1  
            self.opMode = 'PWM,phase correct'
            self.TOP = 0xFF 

        elif (self.WGM02 == 0) and (self.WGM01 == 1) and (self.WGM00 == 0): #2
            self.opMode = 'CTC'
            self.TOP = self.OCR0A

        elif (self.WGM02 == 0) and (self.WGM01 == 1) and (self.WGM00 == 1): #3
            self.opMode = 'Fast PWM'
            self.TOP = 0xFF

        elif (self.WGM02 == 1) and (self.WGM01 == 0) and (self.WGM00 == 0): #4
            self.opMode = 'Reserved'

        elif (self.WGM02 == 1) and (self.WGM01 == 0) and (self.WGM00 == 1): #5
            self.opMode = 'PWM,phase correct'
            self.TOP = self.OCR0A

        elif (self.WGM02 == 1) and (self.WGM01 == 1) and (self.WGM00 == 0): #6
            self.opMode = 'Reserved'

        elif (self.WGM02 == 1) and (self.WGM01 == 1) and (self.WGM00 == 1): #7
            self.opMode = 'Fast PWM'
            self.TOP = self.OCR0A



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