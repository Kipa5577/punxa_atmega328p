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

        #TIMSK0
        self.OCIE0A = 0
        self.OCIE0B = 0
        self.TOIE0 = 0

        self.OC0A = 0 # This shold be an output and bit 
        self.OC1B = 0

        self.increment = True 
        self.PrevT0 = 0

        self.opMode = 'Normal'
        self.TOP = 0xFF
        self.BOTTOM = 0
        self.direction = 'Increment' # states 'Increment' or 'Decrement'
        #self.COMPARE_OC0A = True
        #self.COMPARE_OC0B = True

        self.WGM = 0 
        self.CS = 0
        
        self.COM0A = 0
        self.COM0B = 0

    def clock(self):
        #The register load or read
        self.ADDR = self.port0.address.get()
        if ((self.ADDR == self.TCCR0A_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TCCR0A_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCCR0A)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCCR0A = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCCR0B_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TCCR0B_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCNT0_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TCNT0_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR0A_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.OCR0A_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR0B_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.OCR0B_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIFR0_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TIFR0_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIMSK_addr_LS) and self.INSTYPE.get() == 0):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.GPIOR1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.GPIOR1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        else:
            self.port0.resp.prepare(0)
        
        # Parameter parsing
        #TCCR0B
        self.FOC0A = (self.TCCR0B&0b1<<7)>>7
        self.FOC0B = (self.TCCR0B&0b1<<6)>>6
        self.CS  = self.TCCR0B&0b111

        #TCCR0A
        self.COM0A = (self.TCCR0A>>6)&0b11
        self.COM0B = (self.TCCR0B>>4)&0b11
        self.WGM = self.TCCR0A&0b011 | (self.TCCR0B>>1)&0b100

        #TIMSK0
        self.OCIE0B = (self.TIMSK0>>2)&0b1
        self.OCIE0A = (self.TIMSK0>>1)&0b1
        self.TOIE0 = (self.TIMSK0&0b1)


        
        #prescaler set up 
        if self.CS == 0: # No clock Source
            self.prescaler = 0 
            self.increment = False
        elif self.CS == 1: # clk/(no prescaling)
            self.prescaler = 1
            self.increment = True
        elif self.CS == 2: # clk/8 
            self.prescaler = 8
            self.increment = True
        elif self.CS == 3: # clk/64
            self.prescaler = 64  
            self.increment = True
        elif self.CS == 4: # clk/256
            self.prescaler = 256
            self.increment = True 
        elif self.CS == 5: # clk/1024
            self.prescaler = 1024
            self.increment = True 
        elif self.CS == 6: # External clock on T0 pin. Clock on falling edge.
            if (self.PrevT0 == 1 and self.T0.get() == 0):
                self.prescaler = 1
                self.increment = True
            else:
                self.increment = False
            self.PrevT0 = self.T0.get()
        elif self.CS == 7: # External clock on T0 pin. Clock on rising edge.
            if (self.PrevT0 == 0 and self.T0.get() == 1):
                self.prescaler = 1
                self.increment = True
            else: 
                self.increment = False
            self.PrevT0 = self.T0.get()


        #waveform generation mode 
        if self.WGM == 0:   #0
            self.opMode = 'NORMAL'
            self.TOP =  0xFF
        elif self.WGM == 1: #1  
            self.opMode = 'Phase_Correct_PWM'
            self.TOP = 0xFF 
        elif self.WGM == 2: #2
            self.opMode = 'CTC'
            self.TOP = self.OCR0A
        elif self.WGM == 3: #3
            self.opMode = 'FAST_PWM'
            self.TOP = 0xFF
        elif self.WGM == 4: #4
            self.opMode = 'Reserved'
        elif self.WGM == 5: #5
            self.opMode = 'Phase_Correct_PWM'
            self.TOP = self.OCR0A
        elif self.WGM == 6: #6
            self.opMode = 'Reserved'
        elif self.WGM == 7: #7
            self.opMode = 'FAST_PWM'
            self.TOP = self.OCR0A



        if( self.increment == True):
            self.prescalerCounter +=1
            
        if (self.prescaler == self.prescalerCounter): 
            self.prescalerCounter = 0
            # Incrementing and Decrementing

            if self.direction == 'Increment':
                self.TCNT0  += 1
                if self.TCNT0 > self.TOP: 
                    self.TCNTO = self.BOTTOM

            
            elif self.direction == 'Decrement':
                self.TCNT0  -= 1
                if self.TCNT0 < self.BOTTOM:
                    self.TCNT0 = self.TOP

            # comparing
            #OC0A 
            #if (self.COM0A1 == 0) and (self.COM0A0 == 0):
                #OC0A not connected
            match self.opMode:

                case 'NORMAL':
                    #OC0A
                    if (self.COM0A1 == 0) and (self.COM0A0 == 1):
                        #self.TOP = 0xFF
                        #self.BOTTOM = 0
                        if self.OCR0A == self.TCNTO:
                            if self.OC0A.get() == 0:
                                self.OC0A.prepare(1)
                            else:
                                self.OC0A.prepare(0)

                    elif (self.COM0A1 == 1) and (self.COM0A0 == 0):
                        if self.OCR0A == self.TCNTO:
                            self.OC0A.prepare(0)

                    elif (self.COM0A1 == 1) and (self.COM0A0 == 1):
                        if self.OCR0A == self.TCNTO:
                            self.OC0A.prepare(1)

                    #OC0B
                    if (self.COM0B1 == 0) and (self.COM0B0 == 1):
                        self.TOP = 0xFF
                        self.BOTTOM = 0
                        if self.OCR0B == self.TCNTO:
                            if self.OC0B.get() == 0:
                                self.OC0B.prepare(1)
                            else:
                                self.OC0B.prepare(0)

                    elif (self.COM0B1 == 1) and (self.COM0B0 == 0):
                        if self.OCR0B == self.TCNTO:
                            self.OC0B.prepare(0)

                    elif (self.COM0B1 == 1) and (self.COM0B0 == 1):
                        if self.OCR0B == self.TCNTO:
                            self.OC0B.prepare(1)

                case 'FAST_PWM':

                    #OC0A
                    if (self.COM0A1 == 0) and (self.COM0A0 == 1): # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM02 == 1: # Toggle OC0A on compare match
                            if (self.OCR0A == self.TCNT0): 
                                if self.OC0A.get() == 0:
                                    self.OC0A.prepare(1)
                                else:
                                    self.OC0A.prepare(0)
                                
                    elif (self.COM0A1 == 1) and (self.COM0A0 == 0):
                        if self.OCR0A == self.TCNTO:
                            self.OC0A.prepare(0)

                    elif (self.COM0A1 == 1) and (self.COM0A0 == 1):
                        if self.OCR0A == self.TCNTO:
                            self.OC0A.prepare(1)

                    #OC0B
                    if (self.COM0B1 == 0) and (self.COM0B0 == 1): # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM02 == 1: # Toggle OC0A on compare match
                            if (self.OCR0B == self.TCNT0): 
                                if self.OC0B.get() == 0:
                                    self.OC0B.prepare(1)
                                else:
                                    self.OC0B.prepare(0)
                                
                    elif (self.COM0B1 == 1) and (self.COM0B0 == 0):
                        if self.OCR0B == self.TCNTO:
                            self.OC0B.prepare(0)

                    elif (self.COM0B1 == 1) and (self.COM0B0 == 1):
                        if self.OCR0B == self.TCNTO:
                            self.OC0B.prepare(1)


                case 'Phase_Correct_PWM':
                    #OC0A
                    if (self.COM0A1 == 0) and (self.COM0A0 == 1): # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM02 == 1: # Toggle OC0A on compare match
                            if self.OC0A.get() == 0:
                                self.OC0A.prepare(1)
                            else:
                                self.OC0A.prepare(0)
                                
                    elif (self.COM0A1 == 1) and (self.COM0A0 == 0):
                        if self.direction == 'Increment':
                            if self.OCR0A == self.TCNT0 :
                                self.OC0A.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0A == self.TCNT0 :
                                self.OC0A.prepare(1)

                    elif (self.COM0A1 == 1) and (self.COM0A0 == 1):
                        if self.direction == 'Increment':
                            if self.OCR0A == self.TCNT0 :
                                self.OC0A.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0A == self.TCNT0 :
                                self.OC0A.prepare(0)

                    #OC0B
                    if (self.COM0B1 == 0) and (self.COM0B0 == 1): # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM02 == 1: # Toggle OC0A on compare match
                            if self.OC0B.get() == 0:
                                self.OC0B.prepare(1)
                            else:
                                self.OC0B.prepare(0)
                                
                    elif (self.COM0B1 == 1) and (self.COM0B0 == 0):
                        if self.direction == 'Increment':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(1)

                    elif (self.COM0B1 == 1) and (self.COM0B0 == 1):
                        if self.direction == 'Increment':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(0)



class TimerCounter1(py4hw.Logic): #16 Bit timer

    def __init__(self,parent,name,port:MemoryInterface,INSTYPE,OC1B,OC1A,T0):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        self.INSTYPE = self.addIn('INSTYPE',INSTYPE)
        self.T0 = self.addIn('T0',T0)
        self.OC1B = self.addOut('OC1B',OC1B)
        self.OC1A = self.addOut('OC1A',OC1A)
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
        self.TCNT1L_addr_LS = 0x84

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

        self.increment = True 
        self.PrevT0 = 0

        self.opMode = 'Normal'
        self.TOP = 0xFF
        self.BOTTOM = 0
        self.direction = 'Increment' # states 'Increment' or 'Decrement'

        self.WGM = 0 
        self.CS = 0

        self.OCR1B = 0
        self.OCR1A = 0
        self.ICR1 = 0
        self.TCNT1 = 0
        self.COM1A = 0
        self.COM1B = 0
    

    def clock(self):
        
        #The register load or read
        self.ADDR = self.port0.address.get()
        if ((self.ADDR == self.OCR1BH_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR1BH)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR1BH = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR1BH_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR1BL)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR1BL = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR1AH_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR1AH)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR1AH = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR1AL_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR1AL)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR1AL = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.ICR1H_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.ICR1H)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.ICR1H = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.ICR1L_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.ICR1L)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.ICR1L = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCNT1H_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCNT1H)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCNT1H = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0) #TVNT1L_addr_LS
        elif ((self.ADDR == self.TCNT1L_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCNT1L)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCNT1L = self.port0.write_data.get()
                self.port0.resp.prepare(1)   
            else:
                self.port0.resp.prepare(0)  
        elif ((self.ADDR == self.TCCR1C_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCCR1C)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCCR1C = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCCR1B_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCCR1B)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1)
                self.TCCR1B = self.port0.read_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCCR1A_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCCR1A)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCCR1C = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIMSK1_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIMSK1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIMSK1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIFR1_addr_IO) and self.INSTYPE.get() == 1) or ((self.ADDR == self.TIFR1_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIFR1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIFR1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIFR0_addr_IO) and self.INSTYPE.get() == 1) or ((self.ADDR == self.TIFR0_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIFR0)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIFR0 = self.port0.read_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        else:
            self.port0.resp.prepare(0)
        

        self.OCR1B = self.OCR1BH<<8 | self.OCR1BL
        self.OCR1A = self.OCR1AH<<8 | self.OCR1BL
        self.ICR1 = self.ICR1H<<8 | self.ICR1L
        self.TCNT1 = self.TCNT1H<<8 | self.TCNT1L
        
        # Parameter parsing
        #TCCR1C
        self.FOC1A = (self.TCCR1B&0b1<<7)>>7
        self.FOC1B = (self.TCCR1B&0b1<<6)>>6

        #TCCR1B
        self.ICNC1 = (self.TCCR1B&0b1<<7)>>7
        self.ICES1 = (self.TCCR1B&0b1<<6)>>6
        self.WGM13 = (self.TCCR1B&0b1<<4)>>4
        self.WGM12 = (self.TCCR1B&0b1<<3)>>3
        self.CS = self.TCCR1B&0b111 


        #TCCR1A
        self.COM1A = (self.TCCR1A>>6)&0b11
        self.COM1B = (self.TCCR1B>>4)&0b11 
        self.WGM11 = (self.TCCR1A&0b1<<1)>>1
        self.WGM10 = (self.TCCR1A&0b1<<0)>>0

        #TIMSK1
        self.ICIE1 = (self.TIMSK1>>5)&0b1
        self.OCIE1B = (self.TIMSK1>>2)&0b1
        self.OCIE1A = (self.TIMSK1>>1)&0b1
        self.TOIE1 = (self.TIMSK1&0b1)

        #prescaler set up 
        if self.CS == 0: # No clock Source
            self.prescaler = 0 
            self.increment = False
        elif self.CS == 1: # clk/(no prescaling)
            self.prescaler = 1
            self.increment = True
        elif self.CS == 2: # clk/8 
            self.prescaler = 8
            self.increment = True
        elif self.CS == 3: # clk/64
            self.prescaler = 64  
            self.increment = True
        elif self.CS == 4: # clk/256
            self.prescaler = 256
            self.increment = True 
        elif self.CS == 5: # clk/1024
            self.prescaler = 1024
            self.increment = True 
        elif self.CS == 6: # External clock on T0 pin. Clock on falling edge.
            if (self.PrevT0 == 1 and self.T0.get() == 0):
                self.prescaler = 1
                self.increment = True
            else: 
                self.increment = False
            self.PrevT0 = self.T0.get()
        elif self.CS == 7: # External clock on T0 pin. Clock on rising edge.
            if (self.PrevT0 == 0 and self.T0.get() == 1):
                self.prescaler = 1
                self.increment = True
            else:
                self.increment = False
            self.PrevT0 = self.T0.get()

        self.WGM = self.WGM13<<3 | self.WGM12<<2 | self.WGM11<<1 | self.WGM10
        if self.WGM == 0:   #0
            self.opMode = 'NORMAL'
            self.TOP =  0xFF
        elif self.WGM == 1: #1  
            self.opMode = 'Phase_Correct_PWM_8bit'
            self.TOP = 0xFF 
        elif self.WGM == 2: #2
            self.opMode = 'Phase_Correct_PWM_9bit'
            self.TOP = self.OCR1A
        elif self.WGM == 3: #3
            self.opMode = 'Phase_Correct_PWM_10bit'
            self.TOP = 0xFF
        elif self.WGM == 4: #4
            self.opMode = 'CTC_O'
        elif self.WGM == 5: #5
            self.opMode = 'FAST_PWM_8bit'
            self.TOP = self.OCR0A
        elif self.WGM == 6: #6
            self.opMode = 'FAST_PWM_9bit'
        elif self.WGM == 7: #7
            self.opMode = 'FAST_PWM_10bit'
        elif self.WGM == 8:
            self.opMode = 'Phase_Correct_And_Frequency_PWM_I'
        elif self.WGM == 9:
            self.opMode = 'Phase_Correct_And_Frequency_PWM_O'
        elif self.WGM == 10:
            self.opMode = 'Phase_Correct_PWM_I'
        elif self.WGM == 11:
            self.opMode = 'Phase_Correct_PWM_O'
        elif self.WGM == 12:
            self.opMode = 'CTC_I'
        elif self.WGM == 13:
            self.opMode = 'Reserved'
        elif self.WGM == 14:
            self.opMode = 'FAST_PWM_I'
        elif self.WGM == 15:
            self.opMode = 'FAST_PWM_O'



        
        if( self.increment == True):
            self.prescalerCounter +=1
            
        if (self.prescaler == self.prescalerCounter): 
            self.prescalerCounter = 0
            # Incrementing and Decrementing

            if self.direction == 'Increment':
                self.TCNT0  += 1
                if self.TCNT0 > self.TOP: 
                    self.TCNTO = self.BOTTOM

            
            elif self.direction == 'Decrement':
                self.TCNT0  -= 1
                if self.TCNT0 < self.BOTTOM:
                    self.TCNT0 = self.TOP

            # comparing
            #OC0A 
            #if (self.COM0A1 == 0) and (self.COM0A0 == 0):
                #OC0A not connected
            match self.opMode:

                case 'NORMAL':
                    #OC0A
                    if self.COM1A == 1:# 1
                        #self.TOP = 0xFF
                        #self.BOTTOM = 0
                        if self.OCR1A == self.TCNTO:
                            if self.OC1A.get() == 0:
                                self.OC1A.prepare(1)
                            else:
                                self.OC1A.prepare(0)

                    elif self.COM1A == 2: # 2
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(0)

                    elif self.COM1A == 3: # 3
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(1)

                    #OC0B
                    if self.COM1B == 1:
                        self.TOP = 0xFF
                        self.BOTTOM = 0
                        if self.OCR1B == self.TCNTO:
                            if self.OC1B.get() == 0:
                                self.OC1B.prepare(1)
                            else:
                                self.OC1B.prepare(0)

                    elif self.COM1B == 2:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(0)

                    elif self.COM1B == 3:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(1)


                case 'Phase_Correct_PWM_8bit':

                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if self.OC1A.get() == 0:
                                self.OC1A.prepare(1)
                            else:
                                self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.direction == 'Increment':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(1)

                    elif self.COM1A == 3:
                        if self.direction == 'Increment':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(0)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if self.OC1B.get() == 0:
                                self.OC1B.prepare(1)
                            else:
                                self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.direction == 'Increment':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(1)

                    elif self.COM1B == 2:
                        if self.direction == 'Increment':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(0)

                case 'Phase_Correct_PWM_9bit':

                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if self.OC1A.get() == 0:
                                self.OC1A.prepare(1)
                            else:
                                self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.direction == 'Increment':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(1)

                    elif self.COM1A == 3:
                        if self.direction == 'Increment':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(0)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if self.OC1B.get() == 0:
                                self.OC1B.prepare(1)
                            else:
                                self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.direction == 'Increment':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(1)

                    elif self.COM1B == 3:
                        if self.direction == 'Increment':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(0)

                case 'Phase_Correct_PWM_10bit':

                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if self.OC1A.get() == 0:
                                self.OC1A.prepare(1)
                            else:
                                self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.direction == 'Increment':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(1)

                    elif self.COM1A == 3:
                        if self.direction == 'Increment':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(0)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if self.OC1B.get() == 0:
                                self.OC1B.prepare(1)
                            else:
                                self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.direction == 'Increment':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(1)

                    elif self.COM1B == 3:
                        if self.direction == 'Increment':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(0)


                case 'CTC_O':
                    print("CTC_O")
                    

                case 'FAST_PWM_8bit':
                    #OC0A
                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1A == self.TCNT0): 
                                if self.OC1A.get() == 0:
                                    self.OC1A.prepare(1)
                                else:
                                    self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(0)

                    elif self.COM1A == 3:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(1)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1B == self.TCNT0): 
                                if self.OC1B.get() == 0:
                                    self.OC1B.prepare(1)
                                else:
                                    self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(0)

                    elif self.COM1B == 3:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(1)

                case 'FAST_PWM_9bit':
                    #OC0A
                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1A == self.TCNT0): 
                                if self.OC1A.get() == 0:
                                    self.OC1A.prepare(1)
                                else:
                                    self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(0)

                    elif self.COM1A == 3:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(1)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1B == self.TCNT0): 
                                if self.OC1B.get() == 0:
                                    self.OC1B.prepare(1)
                                else:
                                    self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(0)

                    elif self.COM1B == 3:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(1)

                case 'FAST_PWM_10bit':
                    #OC0A
                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1A == self.TCNT0): 
                                if self.OC1A.get() == 0:
                                    self.OC1A.prepare(1)
                                else:
                                    self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(0)

                    elif self.COM1A == 3:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(1)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1B == self.TCNT0): 
                                if self.OC1B.get() == 0:
                                    self.OC1B.prepare(1)
                                else:
                                    self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(0)

                    elif self.COM1B == 3:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(1)

                case 'Phase_Correct_And_Frequency_PWM_I':
                    print("Phase_Correct_And_Frequency_PWM_I")

                case 'Phase_Correct_And_Frequency_PWM_O':
                    print("Phase_Correct_And_Frequency_PWM_O")

                case 'Phase_Correct_PWM_I':
                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if self.OC1A.get() == 0:
                                self.OC1A.prepare(1)
                            else:
                                self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.direction == 'Increment':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(1)

                    elif self.COM1A == 3:
                        if self.direction == 'Increment':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR1A == self.TCNT0 :
                                self.OC1A.prepare(0)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if self.OC1B.get() == 0:
                                self.OC1B.prepare(1)
                            else:
                                self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.direction == 'Increment':
                            if self.OCR1B == self.TCNT0 :
                                self.OC1B.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(1)

                    elif self.COM0B == 3:
                        if self.direction == 'Increment':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(0)

                case 'Phase_Correct_PWM_O':
                    if self.COM0A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM02 == 1: # Toggle OC0A on compare match
                            if self.OC0A.get() == 0:
                                self.OC0A.prepare(1)
                            else:
                                self.OC0A.prepare(0)
                                
                    elif self.COM0A == 2:
                        if self.direction == 'Increment':
                            if self.OCR0A == self.TCNT0 :
                                self.OC0A.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0A == self.TCNT0 :
                                self.OC0A.prepare(1)

                    elif self.COM0A == 3:
                        if self.direction == 'Increment':
                            if self.OCR0A == self.TCNT0 :
                                self.OC0A.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0A == self.TCNT0 :
                                self.OC0A.prepare(0)

                    #OC0B
                    if self.COM0B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM02 == 1: # Toggle OC0A on compare match
                            if self.OC0B.get() == 0:
                                self.OC0B.prepare(1)
                            else:
                                self.OC0B.prepare(0)
                                
                    elif self.COM0B == 2:
                        if self.direction == 'Increment':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(1)

                    elif self.COM0B == 3:
                        if self.direction == 'Increment':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR0B == self.TCNT0 :
                                self.OC0B.prepare(0)

                case 'CTC_I':
                    

                case 'Reserved':


                case 'FAST_PWM_I':
                    #OC0A
                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1A == self.TCNT0): 
                                if self.OC1A.get() == 0:
                                    self.OC1A.prepare(1)
                                else:
                                    self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(0)

                    elif self.COM1A == 3:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(1)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1B == self.TCNT0): 
                                if self.OC1B.get() == 0:
                                    self.OC1B.prepare(1)
                                else:
                                    self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(0)

                    elif self.COM1B == 3:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(1)

                case 'FAST_PWM_O':
                    #OC0A
                    if self.COM1A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1A == self.TCNT0): 
                                if self.OC1A.get() == 0:
                                    self.OC1A.prepare(1)
                                else:
                                    self.OC1A.prepare(0)
                                
                    elif self.COM1A == 2:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(0)

                    elif self.COM1A == 3:
                        if self.OCR1A == self.TCNTO:
                            self.OC1A.prepare(1)

                    #OC0B
                    if self.COM1B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM12 == 1: # Toggle OC0A on compare match
                            if (self.OCR1B == self.TCNT0): 
                                if self.OC1B.get() == 0:
                                    self.OC1B.prepare(1)
                                else:
                                    self.OC1B.prepare(0)
                                
                    elif self.COM1B == 2:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(0)

                    elif self.COM1B == 3:
                        if self.OCR1B == self.TCNTO:
                            self.OC1B.prepare(1)


class TimerCounter2(py4hw.Logic): #8 Bit timer 

    def __init__(self,parent,name,port:MemoryInterface,INSTYPE,OC2B,OC2A,T2):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        self.INSTYPE = self.addIn('INSTYPE',INSTYPE)
        self.T2 = self.addIn('T0',T2)
        self.OC2B = self.addOut('OC0B',OC2B)
        self.OC2A = self.addOut('OC0A',OC2A)

        #creating the registers
        self.TCCR2A = 0 
        self.TCCR2A_addr_LS = 0xB0

        self.TCCR2B = 0
        self.TCCR2B_addr_LS = 0xB1

        self.TCNT2 = 0 
        self.TCNT2_addr_LS = 0xB2

        self.OCR2A = 0
        self.OCR2A_addr_LS = 0xB3

        self.OCR2B = 0
        self.OCR2B_addr_LS = 0xB4

        self.TIMSK2 = 0
        self.TIMSK2_addr_LS = 0x70

        self.TIFR2 = 0
        self.TIFR2_addr_IO = 0x17
        self.TIFR2_addr_LS = 0x37

        self.opMode = 'Normal'
        self.TOP = 0xFF
        self.BOTTOM = 0
        self.direction = 'Increment' # states 'Increment' or 'Decrement'

        self.WGM = 0 
        self.CS = 0
        
        self.COM2A = 0
        self.COM2B = 0

    def clock(self):

        self.ADDR = self.port0.address.get()
        if ((self.ADDR == self.TCCR2A_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCCR2A)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCCR2A = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0) #TVNT1L_addr_LS
        elif ((self.ADDR == self.TCCR2B_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCCR2B)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCCR2B = self.port0.write_data.get()
                self.port0.resp.prepare(1)   
            else:
                self.port0.resp.prepare(0)  
        elif ((self.ADDR == self.OCR2A_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.OCR2A)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.OCR2A = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR2B_addr_LS) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.OCR2B)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1)
                self.OCR2B = self.port0.read_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIMSK2) and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIMSK2)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIMSK2 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)

            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIMSK1)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIMSK1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIFR2_addr_IO) and self.INSTYPE.get() == 0) or ((self.ADDR == self.TIFR2_addr_LS)and self.INSTYPE.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIFR2)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIFR2 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)


        
        # Parameter parsing
        #TCCR0B
        self.FOC2A = (self.TCCR2B&0b1<<7)>>7
        self.FOC2B = (self.TCCR2B&0b1<<6)>>6
        self.CS  = self.TCCR2B&0b111

        #TCCR0A
        self.COM2A = (self.TCCR0A>>6)&0b11
        self.COM2B = (self.TCCR0B>>4)&0b11
        self.WGM = self.TCCR0A&0b011 | (self.TCCR0B>>1)&0b100

        #TIMSK0
        self.OCIE2B = (self.TIMSK0>>2)&0b1
        self.OCIE2A = (self.TIMSK0>>1)&0b1
        self.TOIE2 = (self.TIMSK0&0b1)


        
        #prescaler set up 
        if self.CS == 0: # No clock Source
            self.prescaler = 0 
            self.increment = False
        elif self.CS == 1: # clk/(no prescaling)
            self.prescaler = 1
            self.increment = True
        elif self.CS == 2: # clk/8 
            self.prescaler = 8
            self.increment = True
        elif self.CS == 3: # clk/64
            self.prescaler = 64  
            self.increment = True
        elif self.CS == 4: # clk/256
            self.prescaler = 256
            self.increment = True 
        elif self.CS == 5: # clk/1024
            self.prescaler = 1024
            self.increment = True 
        elif self.CS == 6: # External clock on T0 pin. Clock on falling edge.
            if (self.PrevT0 == 1 and self.T0.get() == 0):
                self.prescaler = 1
                self.increment = True
            else:
                self.increment = False
            self.PrevT0 = self.T0.get()
        elif self.CS == 7: # External clock on T0 pin. Clock on rising edge.
            if (self.PrevT0 == 0 and self.T0.get() == 1):
                self.prescaler = 1
                self.increment = True
            else: 
                self.increment = False
            self.PrevT0 = self.T0.get()


        #waveform generation mode 
        if self.WGM == 0:   #0
            self.opMode = 'NORMAL'
            self.TOP =  0xFF
        elif self.WGM == 1: #1  
            self.opMode = 'Phase_Correct_PWM'
            self.TOP = 0xFF 
        elif self.WGM == 2: #2
            self.opMode = 'CTC'
            self.TOP = self.OCR0A
        elif self.WGM == 3: #3
            self.opMode = 'FAST_PWM'
            self.TOP = 0xFF
        elif self.WGM == 4: #4
            self.opMode = 'Reserved'
        elif self.WGM == 5: #5
            self.opMode = 'Phase_Correct_PWM'
            self.TOP = self.OCR2A
        elif self.WGM == 6: #6
            self.opMode = 'Reserved'
        elif self.WGM == 7: #7
            self.opMode = 'FAST_PWM'
            self.TOP = self.OCR2A



        if( self.increment == True):
            self.prescalerCounter +=1
            
        if (self.prescaler == self.prescalerCounter): 
            self.prescalerCounter = 0
            # Incrementing and Decrementing

            if self.direction == 'Increment':
                self.TCNT2  += 1
                if self.TCNT2 > self.TOP: 
                    self.TCNT2 = self.BOTTOM

            
            elif self.direction == 'Decrement':
                self.TCNT2  -= 1
                if self.TCNT2 < self.BOTTOM:
                    self.TCNT2 = self.TOP

            # comparing
            #OC0A 
            #if (self.COM0A1 == 0) and (self.COM0A0 == 0):
                #OC0A not connected
            match self.opMode:

                case 'NORMAL':
                    #OC0A
                    if self.COM2A == 1:
                        #self.TOP = 0xFF
                        #self.BOTTOM = 0
                        if self.OCR2A == self.TCNT2:
                            if self.OC2A.get() == 0:
                                self.OC2A.prepare(1)
                            else:
                                self.OC2A.prepare(0)

                    elif self.COM2A == 2:
                        if self.OCR2A == self.TCNT2:
                            self.OC2A.prepare(0)

                    elif self.COM2A == 3:
                        if self.OCR2A == self.TCNT2:
                            self.OC2A.prepare(1)

                    #OC0B
                    if self.COM2B == 1:
                        self.TOP = 0xFF
                        self.BOTTOM = 0
                        if self.OCR2B == self.TCNT2:
                            if self.OC2B.get() == 0:
                                self.OC2B.prepare(1)
                            else:
                                self.OC2B.prepare(0)

                    elif self.COM2B == 2:
                        if self.OCR2B == self.TCNT2:
                            self.OC2B.prepare(0)

                    elif self.COM2B == 3:
                        if self.OCR2B == self.TCNT2:
                            self.OC2B.prepare(1)

                case 'FAST_PWM':

                    #OC0A
                    if self.COM2A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM>>2 == 1: # Toggle OC0A on compare match
                            if (self.OCR2A == self.TCNT2): 
                                if self.OC2A.get() == 0:
                                    self.OC2A.prepare(1)
                                else:
                                    self.OC2A.prepare(0)
                                
                    elif self.COM2A == 2:
                        if self.OCR2A == self.TCNT2:
                            self.OC2A.prepare(0)

                    elif self.COM2A == 3:
                        if self.OCR2A == self.TCNT2:
                            self.OC2A.prepare(1)

                    #OC0B
                    if self.COM2B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM>>2 == 1: # Toggle OC0A on compare match
                            if (self.OCR2B == self.TCNT2): 
                                if self.OC2B.get() == 0:
                                    self.OC2B.prepare(1)
                                else:
                                    self.OC2B.prepare(0)
                                
                    elif self.COM2B == 2:
                        if self.OCR2B == self.TCNT2:
                            self.OC2B.prepare(0)

                    elif self.COM2B == 3:
                        if self.OCR2B == self.TCNT2:
                            self.OC2B.prepare(1)


                case 'Phase_Correct_PWM':
                    #OC0A
                    if self.COM2A == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM>>2 == 1: # Toggle OC0A on compare match
                            if self.OC2A.get() == 0:
                                self.OC2A.prepare(1)
                            else:
                                self.OC2A.prepare(0)
                                
                    elif self.COM2A == 2:
                        if self.direction == 'Increment':
                            if self.OCR2A == self.TCNT2 :
                                self.OC2A.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR2A == self.TCNT2 :
                                self.OC2A.prepare(1)

                    elif self.COM2A == 3:
                        if self.direction == 'Increment':
                            if self.OCR2A == self.TCNT2 :
                                self.OC2A.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR2A == self.TCNT2 :
                                self.OC2A.prepare(0)

                    #OC0B
                    if self.COM2B == 1: # at 0 0 OC0A is disconected 
                        #if self.WGM02 == 0: #normal port operation
                        
                        if self.WGM>>2 == 1: # Toggle OC0A on compare match
                            if self.OC2B.get() == 0:
                                self.OC2B.prepare(1)
                            else:
                                self.OC2B.prepare(0)
                                
                    elif self.COM2B == 2:
                        if self.direction == 'Increment':
                            if self.OCR2B == self.TCNT2 :
                                self.OC2B.prepare(0)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR2B == self.TCNT2 :
                                self.OC2B.prepare(1)

                    elif self.COM2B == 3:
                        if self.direction == 'Increment':
                            if self.OCR2B == self.TCNT2 :
                                self.OC2B.prepare(1)
                        
                        elif self.direction == 'Decrement':
                            if self.OCR2B == self.TCNT2 :
                                self.OC2B.prepare(0)

