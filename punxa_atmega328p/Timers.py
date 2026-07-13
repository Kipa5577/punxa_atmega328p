import py4hw
from punxa_atmega328p.Memory import * 

#addres of each register

## *_IO = IN and OUT instruction address
## *_LS =  LD LDS ST STS instruction address
class TimerCounter0(py4hw.Logic): #8 Bit timer 
    def __init__(self,parent,name,port:MemoryInterface,OC0B,OC0A,T0,OCF0B,OCF0A,TOV0): # Signals to outside OC0B OC0A  
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        self.T0 = self.addIn('T0',T0)
        self.OC0B = self.addOut('OC0B',OC0B)
        self.OC0A = self.addOut('OC0A',OC0A)

        #Interrupts
        self.OCF0B = self.addOut('OCF0B',OCF0B)
        self.OCF0A = self.addOut('OCF0A',OCF0A)
        self.TOV0 = self.addOut('TOV0',TOV0)



        #wire value varibles
        self.OC0A_val = 0 
        self.OC0B_val = 0

        self.OCF0B_val= 0
        self.OCF0A_val= 0
        self.TOV0_val = 0

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
        self.TIMSK0 = 0
        self.TIMSK0_addr_LS = 0x6E
        self.TIFR0 = 0  #bit2: OCF0B | bit1: OCF0A | bit0: TOV0
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
        self.FOC0A = 0 
        self.FOC0B = 0
        self.WGM02 = 0
        self.CS02 = 0
        self.CS01 = 0
        self.CS00 = 0

        #TIMSK0
        self.OCIE0A = 0
        self.OCIE0B = 0
        self.TOIE0 = 0

        self.toggleA = 0
        self.toggleB = 0

        self.incrementEnable = True 
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

        self.prevCS = 17

    def Memory_access(self):
        #The register load or read
        self.ADDR = self.port0.address.get()
        if ((self.ADDR == self.TCCR0A_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.TCCR0A_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCCR0A & 0b11110011)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCCR0A = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCCR0B_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.TCCR0B_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCCR0B & 0b00001111)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCCR0B = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCNT0_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.TCNT0_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCNT0 & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCNT0 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR0A_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.OCR0A_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR0A & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR0A = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR0B_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.OCR0B_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR0B & 0b00000111)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR0B = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIFR0_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.TIFR0_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TIFR0 & 0b00000111)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TIFR0 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIMSK0_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TIMSK0&0b111)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TIMSK0 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        else:
            self.port0.resp.prepare(0)

    def Parse_control_registers(self):
        # Parameter parsing
        #TCCR0B
        self.FOC0A = (self.TCCR0B&(0b1<<7))>>7
        self.FOC0B = (self.TCCR0B&(0b1<<6))>>6
        self.CS  = self.TCCR0B&0b111

        #TCCR0A
        self.COM0A = (self.TCCR0A>>6)&0b11
        self.COM0B = (self.TCCR0A>>4)&0b11
        self.WGM = (self.TCCR0A&0b11) | ((self.TCCR0B>>1)&0b100)

        #TIMSK0
        self.OCIE0B = (self.TIMSK0>>2)&0b1
        self.OCIE0A = (self.TIMSK0>>1)&0b1
        self.TOIE0 = (self.TIMSK0&0b1)

    def update_prescaler(self):
        #prescaler set up 
        if self.CS == 0: # No clock Source
            self.prescaler = 0 
            self.incrementEnable = False
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 1: # clk/(no prescaling)
            self.prescaler = 1
            self.incrementEnable = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 2: # clk/8 
            self.prescaler = 8
            self.incrementEnable = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 3: # clk/64
            self.prescaler = 64  
            self.incrementEnable = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 4: # clk/256
            self.prescaler = 256
            self.incrementEnable = True 
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 5: # clk/1024
            self.prescaler = 1024
            self.incrementEnable = True 
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 6: # External clock on T0 pin. Clock on falling edge.
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0

            if (self.PrevT0 == 1 and self.T0.get() == 0):
                self.prescaler = 1
                self.incrementEnable = True
            else:
                self.incrementEnable = False
            self.PrevT0 = self.T0.get()

        elif self.CS == 7: # External clock on T0 pin. Clock on rising edge.
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0

            if (self.PrevT0 == 0 and self.T0.get() == 1):
                self.prescaler = 1
                self.incrementEnable = True
            else: 
                self.incrementEnable = False
            self.PrevT0 = self.T0.get()

    def update_wave_gen_mode(self):
        #waveform generation mode 
        #I should take in to account when OCR0A Updates
        if self.WGM == 0:   #0
            self.opMode = 'NORMAL'
            self.TOP = 0xFF
            self.BOTTOM = 0
        elif self.WGM == 1: #1  
            self.opMode = 'Phase_Correct_PWM'
            self.TOP = 0xFF
            self.BOTTOM = 0
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

    def handle_normal_mode(self):
        #OC0A ## toggle 
        if self.COM0A == 1:
            if self.OCR0A == self.TCNT0:
                if self.OC0A.get() == 0:
                    self.OC0A_val = 1 
                else:
                    self.OC0A_val = 0
                #Interrupts
                if self.OCIE0A == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b010

        elif self.COM0A == 2: ## clear 
            if self.OCR0A == self.TCNT0:
                self.OC0A_val = 0
                if self.OCIE0A == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b010

        elif self.COM0A == 3: ## SET
            if self.OCR0A == self.TCNT0:
                self.OC0A_val = 1
                #Interrupts
                if self.OCIE0A == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b010                

        else:
            self.OC0A_val = 0     ## normal operation disconnected
                

        #OC0B
        if self.COM0B == 1: ## toggle 
            if self.OCR0B == self.TCNT0:
                if self.OC0B.get() == 0:
                    self.OC0B_val = 1 
                else:
                    self.OC0B_val = 0
                #Interrupts
                if self.OCIE0B == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b100


        elif self.COM0B == 2: ## clear 
            if self.OCR0B == self.TCNT0:
                self.OC0B_val = 0
                #Interrupts
                if self.OCIE0B == 1:
                    #self.OCF0A_val = 1   
                    self.TIFR0 |= 0b100

        elif self.COM0B == 3: ## Set 
            if self.OCR0B == self.TCNT0:
                self.OC0B_val= 1
                #Interrupts
                if self.OCIE0B == 1:
                   #self.OCF0A_val = 1 
                   self.TIFR0 |= 0b100
                   
        else:
            self.OC0B_val = 0 ## disconected

    def handle_Phase_Correct_PWM_mode(self):
        #OC0A
        if self.COM0A == 1: # at 0 0 OC0A is disconected 
            #if self.WGM02 == 0: #normal port operation
            if self.WGM == 5: # Toggle OC0A on compare match 
                if (self.OCR0A == self.TCNT0): 
                    if self.OC0A.get() == 0:
                        self.OC0A_val = 1
                    else:
                        self.OC0A_val = 0  
                    if self.OCIE0A == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b010  
            else:
                self.OC0A_val = 0 #disconnected

        elif self.COM0A == 2:
            if self.direction == 'Increment':
                if self.OCR0A == self.TCNT0 :
                    self.OC0A_val = 0
                    if self.OCIE0A == 1:
                        #self.OCF0A_val = 1 
                        self.TIFR0 |= 0b010  


            elif self.direction == 'Decrement':
                if self.OCR0A == self.TCNT0 :
                    self.OC0A_val = 1
                    if self.OCIE0A == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b010  
                            
        elif self.COM0A == 3:
            if self.direction == 'Increment':
                if self.OCR0A == self.TCNT0 :
                    self.OC0A_val = 1
                    if self.OCIE0A == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b010

            elif self.direction == 'Decrement':
                if self.OCR0A == self.TCNT0 :
                    self.OC0A_val = 0
                    if self.OCIE0A == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b010

        #OC0B
        if self.COM0B == 1: 
            self.OC0B_val = 0
                    

        elif self.COM0B == 2:
            if self.direction == 'Increment':
                if self.OCR0B == self.TCNT0 :
                    self.OC0B_val = 0
                    if self.OCIE0B == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b100
            
            elif self.direction == 'Decrement':
                if self.OCR0B == self.TCNT0 :
                    self.OC0B_val = 1
                    if self.OCIE0B == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b100

        elif self.COM0B == 3:
            if self.direction == 'Increment':
                if self.OCR0B == self.TCNT0 :
                    self.OC0B_val = 1
                    if self.OCIE0B == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b100


            elif self.direction == 'Decrement':
                if self.OCR0B == self.TCNT0 :
                    self.OC0B_val = 0
                    if self.OCIE0B == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b100

    def handle_CTC_mode(self):
        #OC0A
        if self.COM0A == 1:
            if self.OCR0A == self.TCNT0:
                if self.OC0A.get() == 0:
                    self.OC0A_val = 1
                else:
                    self.OC0A_val = 0
                    
            #Interrupts
            if self.OCIE0A == 1:
                #self.OCF0A_val = 1
                self.TIFR0 |= 0b010 

        elif self.COM0A == 2:
            if self.OCR0A == self.TCNT0:
                self.OC0A_val = 0
            #Interrupts
            if self.OCIE0A == 1:
                #self.OCF0A_val = 1
                self.TIFR0 |= 0b010
                    
        elif self.COM0A == 3:
            if self.OCR0A == self.TCNT0:
                self.OC0A_val = 1
            #Interrupts
            if self.OCIE0A == 1:
                #self.OCF0A_val = 1
                self.TIFR0 |= 0b010
        else:
            self.OC0A_val = 0     
                
            

        #OC0B
        if self.COM0B == 1: ## toggle 
            if self.OCR0B == self.TCNT0:
                if self.OC0B.get() == 0:
                    self.OC0B_val = 1 
                else:
                    self.OC0B_val = 0
                #Interrupts
                if self.OCIE0B == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b100

        elif self.COM0B == 2: ## clear 
            if self.OCR0B == self.TCNT0:
                self.OC0B_val = 0
                #Interrupts
                if self.OCIE0B == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b100 

        elif self.COM0B == 3: ## Set 
            if self.OCR0B == self.TCNT0:
                self.OC0B_val= 1
                #Interrupts
                if self.OCIE0B == 1:
                   #self.OCF0A_val = 1
                   self.TIFR0 |= 0b100 
        else:
            self.OC0B_val = 0 ## disconected

    def handle_FAST_PWM_mode(self):
        #OC0A ## toggle 
        if self.COM0A == 1:
            if self.WGM == 7:  
                if self.OCR0A == self.TCNT0:
                    if self.OC0A.get() == 0:
                        self.OC0A_val = 1 
                    else:
                        self.OC0A_val = 0
                    #Interrupts
                    if self.OCIE0A == 1:
                        #self.OCF0A_val = 1
                        self.TIFR0 |= 0b010
            else:
                self.OC0A_val = 0

        elif self.COM0A == 2: ## clear 
            if self.OCR0A == self.TCNT0:
                self.OC0A_val = 0
                #Interrupts
                if self.OCIE0A == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b010

            if self.TCNT0 == self.BOTTOM:
                self.OC0A_val = 1


        elif self.COM0A == 3: # SET
            if self.OCR0A == self.TCNT0:
                self.OC0A_val = 1
                #Interrupts
                if self.OCIE0A == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b010

            if self.TCNT0 == self.BOTTOM:
                self.OC0A_val = 0

        else:
                self.OC0A_val = 0     ## normal operation disconnected



        #OC0B
        if self.COM0B == 1: ## toggle 
            self.OC0B_val = 0

        elif self.COM0B == 2: ## clear 
            if self.OCR0B == self.TCNT0:
                self.OC0B_val = 0
                #Interrupts
                if self.OCIE0B == 1:
                    #self.OCF0A_val = 1   
                    self.TIFR0 |= 0b100

            if self.TCNT0 == self.BOTTOM:
                self.OC0B_val = 1


        elif self.COM0B == 3: ## Set 
            if self.OCR0B == self.TCNT0:
                self.OC0B_val = 1
                #Interrupts
                if self.OCIE0B == 1:
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b100
            if self.TCNT0 == self.BOTTOM:
                self.OC0B_val = 0
 

        else:
                self.OC0B_val = 0 ## disconected

    def Phase_Correct_PWM_Increment(self):
        if self.direction == 'Increment':
            self.TCNT0 += 1
            if self.TCNT0 >= self.TOP:
                self.TCNT0    = self.TOP   
                self.direction = 'Decrement'
                #return skip compare match at TOP

        elif self.direction == 'Decrement':
            self.TCNT0 -= 1
            if self.TCNT0 <= self.BOTTOM:
                self.TCNT0    = self.BOTTOM
                self.direction = 'Increment'
                if self.TOIE0 == 1:
                    #self.TOV0_val = 1
                    self.TIFR0 |= 0b001

    def Other_modes_Increment(self):
        if self.direction == 'Increment':
            self.TCNT0 += 1
            if self.TCNT0 >= self.TOP:
                if self.opMode == 'CTC':
                    self.TCNT0 = self.BOTTOM
                else:
                    self.TCNT0 = self.BOTTOM
                if self.OCIE0A == 1: ## Interrupt
                    #self.OCF0A_val = 1
                    self.TIFR0 |= 0b010

                if self.TOIE0 == 1:
                    #self.TOV0_val = 1  
                    self.TIFR0 |= 0b001  
    
    def increment(self):
        if( self.incrementEnable == True):
            self.prescalerCounter +=1
            
        if (self.prescaler != 0) and (self.prescaler == self.prescalerCounter): 
            self.prescalerCounter = 0
            # Incrementing and Decrementing
            if self.opMode == 'Phase_Correct_PWM':
                self.Phase_Correct_PWM_Increment()
                #return   # skip determine_outputs at TOP turnaround
            else:  # NORMAL, CTC, FAST_PWM
                self.Other_modes_Increment()
            self.TCNT0 = self.TCNT0 & 0xFF

            self.determine_outputs()

    def determine_outputs(self):
            match self.opMode:
                case 'NORMAL' :
                    self.handle_normal_mode()
                case 'FAST_PWM':
                    self.handle_FAST_PWM_mode()
                case 'Phase_Correct_PWM':
                    self.handle_Phase_Correct_PWM_mode()
                case 'CTC' :
                    self.handle_CTC_mode()

    def update_outputs(self):
        self.OC0A.prepare(self.OC0A_val)
        self.OC0B.prepare(self.OC0B_val)
        self.OCF0B.prepare(((self.TIFR0>>2)&0b1))
        self.OCF0A.prepare(((self.TIFR0>>1)&0b1))
        self.TOV0.prepare(((self.TIFR0>>0)&0b1))

    def clock(self):
        self.Memory_access()
        self.Parse_control_registers()
        self.update_prescaler()
        self.update_wave_gen_mode()
        self.increment()
        self.update_outputs()

class TimerCounter2(py4hw.Logic): #8 Bit timer 
    def __init__(self,parent,name,port:MemoryInterface,OC2B,OC2A,T2,OCF2B,OCF2A,TOV2):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        self.T2 = self.addIn('T2',T2)
        self.OC2B = self.addOut('OC2B',OC2B)
        self.OC2A = self.addOut('OC2A',OC2A)

        #Interrupts
        self.OCF2B = self.addOut('OCF2B',OCF2B)
        self.OCF2A = self.addOut('OCF2A',OCF2A)
        self.TOV2 = self.addOut('TOV2',TOV2)

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

        self.incrementEnable = True 
        self.PrevT2 = 0

        self.opMode = 'Normal'
        self.TOP = 0xFF
        self.BOTTOM = 0
        self.direction = 'Increment' # states 'Increment' or 'Decrement'

        self.WGM = 0 
        self.CS = 0
        
        self.COM2A = 0
        self.COM2B = 0

        self.prevCS = 17

    def Memory_access(self):
        self.ADDR = self.port0.address.get()
        if ((self.ADDR == self.TCCR2A_addr_LS) and (self.port0.instype.get() == 1)):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCCR2A & 0b11110011)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCCR2A = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0) #TVNT1L_addr_LS
        elif ((self.ADDR == self.TCCR2B_addr_LS) and (self.port0.instype.get() == 1)):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCCR2B & 0x0F)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCCR2B = self.port0.write_data.get()
                self.port0.resp.prepare(1)   
            else:
                self.port0.resp.prepare(0)  
        elif ((self.ADDR == self.OCR2A_addr_LS) and (self.port0.instype.get() == 1)):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.OCR2A & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.OCR2A = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR2B_addr_LS) and (self.port0.instype.get() == 1)):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.OCR2B & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.OCR2B = self.port0.read_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIMSK2) and (self.port0.instype.get() == 1)):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIMSK2 & 0x07)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIMSK2 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIFR2_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.TIFR2_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIFR2 & 0x07)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIFR2 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)

    def Parse_control_registers(self):
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

    def update_prescaler(self):
        #prescaler set up 
        if self.CS == 0: # No clock Source
            self.prescaler = 0 
            self.increment = False
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 1: # clk/(no prescaling)
            self.prescaler = 1
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 2: # clk/8 
            self.prescaler = 8
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 3: # clk/64
            self.prescaler = 64  
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 4: # clk/256
            self.prescaler = 256
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 5: # clk/1024
            self.prescaler = 1024
            self.increment = True 
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 6: # External clock on T0 pin. Clock on falling edge.
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
            if (self.PrevT0 == 1 and self.T0.get() == 0):
                self.prescaler = 1
                self.increment = True
            else:
                self.increment = False
            self.PrevT0 = self.T0.get()

        elif self.CS == 7: # External clock on T0 pin. Clock on rising edge.
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
            if (self.PrevT0 == 0 and self.T0.get() == 1):
                self.prescaler = 1
                self.increment = True
            else: 
                self.increment = False
            self.PrevT0 = self.T0.get()
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0

    def update_wave_gen_mode(self):
        #waveform generation mode 
        if self.WGM == 0:   #0
            self.opMode = 'NORMAL'
            self.TOP =  0xFF
            self.BOTTOM = 0
        elif self.WGM == 1: #1  
            self.opMode = 'Phase_Correct_PWM'
            self.TOP = 0xFF 
            self.BOTTOM = 0
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

    def handle_normal_mode(self):

        if self.COM2A == 1:
            if self.OCR2A == self.TCNT2:
                if self.OC2A.get() == 0:
                    self.OC2A_val = 1 
                else:
                    self.OC2A_val = 0
                #Interrupts
                if self.OCIE2A == 1:
                    self.OCF2A_val = 1

        elif self.COM2A == 2: ## clear 
            if self.OCR2A == self.TCNT2:
                self.OC2A_val = 0
                if self.OCIE2A == 1:
                    self.OCF2A_val = 1


        elif self.COM2A == 3: ## SET
            if self.OCR2A == self.TCNT2:
                self.OC2A_val = 1
                #Interrupts
                if self.OCIE2A == 1:
                    self.OCF2A_val = 1
                    
        else:
            self.OC2A_val = 0     ## normal operation disconnected
                

                    #OC0B
        if self.COM2B == 1: ## toggle 
            if self.OCR2B == self.TCNT2:
                if self.OC2B.get() == 0:
                    self.OC2B_val = 1 
                else:
                    self.OC2B_val = 0
                #Interrupts
                if self.OCIE2B == 1:
                    self.OCF2B_val = 1

        elif self.COM2B == 2: ## clear 
            if self.OCR2B == self.TCNT2:
                self.OC0B_val = 0
                #Interrupts
                if self.OCIE2B == 1:
                    self.OCF2B_val = 1   

        elif self.COM2B == 3: ## Set 
            if self.OCR2B == self.TCNT2:
                self.OC2B_val= 1
                #Interrupts
                if self.OCIE2B == 1:
                   self.OCF2B_val = 1 

        else:
            self.OC2B_val = 0 ## disconected

    def handle_CTC_mode(self):
        #OC0A
        if self.COM2A == 1:
            if self.OCR2A == self.TCNT2:
                if self.OC2A.get() == 0:
                    self.OC2A_val = 1
                else:
                    self.OC2A_val = 0
                    
            #Interrupts
            if self.OCIE2A == 1:
                self.OCF2A_val = 1
                    
        elif self.COM2A == 2:
            if self.OCR2A == self.TCNT2:
                self.OC2A_val = 0
                
            #Interrupts
            if self.OCIE2A == 1:
                self.OCF2A_val = 1
                    
        elif self.COM2A == 3:
            if self.OCR2A == self.TCNT2:
                self.OC2A_val = 1

            #Interrupts
            if self.OCIE2A == 1:
                self.OCF2A_val = 1
                
        else:
            self.OC2A_val = 0     
                
            

        #OC0B
        if self.COM2B == 1: ## toggle 
            if self.OCR2B == self.TCNT2:
                if self.OC2B.get() == 0:
                    self.OC2B_val = 1 
                else:
                    self.OC2B_val = 0
                #Interrupts
                if self.OCIE2B == 1:
                    self.OCF2B_val = 1

        elif self.COM2B == 2: ## clear 
            if self.OCR2B == self.TCNT2:
                self.OC2B_val = 0
                #Interrupts
                if self.OCIE2B == 1:
                    self.OCF2B_val = 1   

        elif self.COM2B == 3: ## Set 
            if self.OCR2B == self.TCNT2:
                self.OC2B_val= 1
                #Interrupts
                if self.OCIE2B == 1:
                   self.OCF2B_val = 1 

        else:
            self.OC2B_val = 0 ## disconected

    def handle_FAST_PWM_mode(self):
        #OC0A ## toggle 
        if self.COM2A == 1:
            if self.WGM == 7:  
                if self.OCR2A == self.TCNT2:
                    if self.OC2A.get() == 0:
                        self.OC2A_val = 1 
                    else:
                        self.OC2A_val = 0
                    #Interrupts
                    if self.OCIE2A == 1:
                        self.OCF2A_val = 1
            else:
                self.OC2A_val = 0

        elif self.COM2A == 2: ## clear 
            if self.OCR2A == self.TCNT2:
                self.OC2A_val = 0
                #Interrupts
                if self.OCIE2A == 1:
                    self.OCF2A_val = 1
            if self.TCNT2 == self.BOTTOM:
                self.OC2A_val = 1


        elif self.COM2A == 3: # SET
            if self.OCR2A == self.TCNT2:
                self.OC2A_val = 1
                #Interrupts
                if self.OCIE2A == 1:
                    self.OCF2A_val = 1
            if self.TCNT2 == self.BOTTOM:
                self.OC2A_val = 0

        else:
                self.OC2A_val = 0     ## normal operation disconnected



        #OC0B
        if self.COM2B == 1: ## toggle 
            self.OC2B_val = 0

        elif self.COM2B == 2: ## clear 
            if self.OCR2B == self.TCNT2:
                self.OC2B_val = 0
                #Interrupts
                if self.OCIE2B == 1:
                    self.OCF2B_val = 1   
            if self.TCNT2 == self.BOTTOM:
                self.OC2B_val = 1


        elif self.COM2B == 3: ## Set 
            if self.OCR2B == self.TCNT2:
                self.OC2B_val = 1
                #Interrupts
                if self.OCIE2B == 1:
                    self.OCF2B_val = 1
            if self.TCNT2 == self.BOTTOM:
                self.OC2B_val = 0
 
        else:
                self.OC2B_val = 0 ## disconected

    def handle_Phase_Correct_PWM_mode(self):
        #OC2A
        if self.COM2A == 1: # at 0 0 OC2A is disconected 
            #if self.WGM02 == 0: #normal port operation
            if self.WGM == 5: # Toggle OC2A on compare match 
                if (self.OCR02A == self.TCNT2): 
                    if self.OC2A.get() == 0:
                        self.OC2A_val = 1
                    else:
                        self.OC2A_val = 0  
                    if self.OCIE2A == 1:
                        self.OCF2A_val = 1
            else:
                self.OC2A_val = 0 #disconnected

        elif self.COM2A == 2:
            if self.direction == 'Increment':
                if self.OCR2A == self.TCNT2 :
                    self.OC2A_val = 0
                    if self.OCIE2A == 1:
                        self.OCF2A_val = 1 
            elif self.direction == 'Decrement':
                if self.OCR2A == self.TCNT2 :
                    self.OC2A_val = 1
                    if self.OCIE2A == 1:
                        self.OCF2A_val = 1
                            
        elif self.COM2A == 3:
            if self.direction == 'Increment':
                if self.OCR2A == self.TCNT2 :
                    self.OC2A_val = 1
                    if self.OCIE2A == 1:
                        self.OCF2A_val = 1
            elif self.direction == 'Decrement':
                if self.OCR2A == self.TCNT2 :
                    self.OC2A_val = 0
                    if self.OCIE2A == 1:
                        self.OCF2A_val = 1

        #OC0B
        if self.COM2B == 1: 
            self.OC2B_val = 0
                    

        elif self.COM2B == 2:
            if self.direction == 'Increment':
                if self.OCR2B == self.TCNT2 :
                    self.OC2B_val = 0
                    if self.OCIE2B == 1:
                        self.OCF2B_val = 1
            elif self.direction == 'Decrement':
                if self.OCR2B == self.TCNT2 :
                    self.OC2B_val = 1
                    if self.OCIE2B == 1:
                        self.OCF2B_val = 1
        elif self.COM2B == 3:
            if self.direction == 'Increment':
                if self.OCR2B == self.TCNT2 :
                    self.OC2B_val = 1
                    if self.OCIE2B == 1:
                        self.OCF2B_val = 1
            elif self.direction == 'Decrement':
                if self.OCR2B == self.TCNT2 :
                    self.OC2B_val = 0
                    if self.OCIE2B == 1:
                        self.OCF2B_val = 1

    def Phase_Correct_PWM_Increment(self):
        if self.direction == 'Increment':
            self.TCNT2 += 1
            if self.TCNT2 >= self.TOP:
                self.TCNT2    = self.TOP   
                self.direction = 'Decrement'
                #return skip compare match at TOP

        elif self.direction == 'Decrement':
            self.TCNT2 -= 1
            if self.TCNT2 <= self.BOTTOM:
                self.TCNT2    = self.BOTTOM
                self.direction = 'Increment'
                if self.TOIE2 == 1:
                    self.TOV2_val = 1

    def Other_modes_Increment(self):
        if self.direction == 'Increment':
            self.TCNT2 += 1
            if self.TCNT2 >= self.TOP:
                if self.opMode == 'CTC':
                    self.TCNT2 = self.BOTTOM
                else:
                    self.TCNT2 = self.BOTTOM
                if self.OCIE2A == 1: ## Interrupt
                    self.OCF2A_val = 1

                if self.TOIE2 == 1:
                    self.TOV2_val = 1    
                else:
                    self.TOV2_val = 0

    def increment(self):
        if( self.incrementEnable == True):
            self.prescalerCounter +=1
            
        if (self.prescaler != 0) and (self.prescaler == self.prescalerCounter): 
            self.prescalerCounter = 0
            # Incrementing and Decrementing
            if self.opMode == 'Phase_Correct_PWM':
                self.Phase_Correct_PWM_Increment()
                #return   # skip determine_outputs at TOP turnaround
            else:  # NORMAL, CTC, FAST_PWM
                self.Other_modes_Increment()
            self.TCNT2 = self.TCNT2 & 0xFF

            self.determine_outputs()

    def determine_outputs(self):
            match self.opMode:
                case 'NORMAL' :
                    self.handle_normal_mode()
                case 'FAST_PWM':
                    self.handle_FAST_PWM_mode()
                case 'Phase_Correct_PWM':
                    self.handle_Phase_Correct_PWM_mode()
                case 'CTC' :
                    self.handle_CTC_mode()

    def update_outputs(self):
        self.OC2A.prepare(self.OC2A_val)
        self.OC2B.prepare(self.OC2B_val)
        self.OCF2B.prepare(self.OCF2B_val)
        self.OCF2A.prepare(self.OCF2A_val)
        self.TOV2.prepare(self.TOV2_val)

    def clock(self):
        self.Memory_access()
        self.Parse_control_registers()
        self.update_prescaler()
        self.update_wave_gen_mode()
        self.increment()
        self.update_outputs()

class TimerCounter1(py4hw.Logic): #16 Bit timer
    def __init__(self,parent,name,port:MemoryInterface,OC1B,OC1A,T1,OCF1B,OCF1A,TOV1,ICF1):
        super().__init__(parent,name)

        self.port0 =  self.addInterfaceSink('port',port)
        self.T1 = self.addIn('T1',T1)
        self.OC1B = self.addOut('OC1B',OC1B)
        self.OC1A = self.addOut('OC1A',OC1A)

        #Interrupts
        self.OCF1B = self.addOut('OCF1B',OCF1B)
        self.OCF1A = self.addOut('OCF1A',OCF1A)
        self.TOV1 = self.addOut('TOV1',TOV1)
        self.ICF1 = self.addOut('ICF1',ICF1)
        

        #wire value varibles
        self.OC1A_val = 0 
        self.OC1B_val = 0

        self.OCF1B_val= 0
        self.OCF1A_val= 0
        self.TOV1_val = 0
        self.ICF1_val = 0


        #creating the registers
        self.OCR1BH = 0 
        self.OCR1BH_addr_LS = 0x8B

        self.OCR1BL = 0
        self.OCR1BH_addr_LS = 0x8A

        self.OCR1AH = 0
        self.OCR1AH_addr_LS = 0x89

        self.OCR1AL = 0
        self.OCR1AL_addr_LS = 0x88

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


        self.incrementEnable = True 
        self.PrevT1 = 0

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
    

    def Memory_access(self):
        #The register load or read
        self.ADDR = self.port0.address.get()
        if ((self.ADDR == self.OCR1BH_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR1BH & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR1BH = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR1BH_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR1BL & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR1BL = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR1AH_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR1AH & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR1AH = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.OCR1AL_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.OCR1AL & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.OCR1AL = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.ICR1H_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.ICR1H & 0xFF) 
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.ICR1H = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.ICR1L_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.ICR1L & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.ICR1L = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCNT1H_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.TCNT1H & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.TCNT1H = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0) #TVNT1L_addr_LS
        elif ((self.ADDR == self.TCNT1L_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCNT1L & 0xFF)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCNT1L = self.port0.write_data.get()
                self.port0.resp.prepare(1)   
            else:
                self.port0.resp.prepare(0)  
        elif ((self.ADDR == self.TCCR1C_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCCR1C & 0x00)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCCR1C = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCCR1B_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCCR1B & 0b11011111)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCCR1B = self.port0.read_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TCCR1A_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TCCR1A & 0b11110011)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TCCR1C = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIMSK1_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIMSK1 & 0b00100111)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIMSK1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.TIFR1_addr_IO) and self.port0.instype.get() == 1) or ((self.ADDR == self.TIFR1_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.TIFR1 & 0b00100111)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.TIFR1 = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        else:
            self.port0.resp.prepare(0)

    def Parse_control_registers(self):
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

    def update_prescaler(self):
        #prescaler set up 
        if self.CS == 0: # No clock Source
            self.prescaler = 0 
            self.increment = False
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 1: # clk/(no prescaling)
            self.prescaler = 1
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 2: # clk/8 
            self.prescaler = 8
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 3: # clk/64
            self.prescaler = 64  
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 4: # clk/256
            self.prescaler = 256
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 5: # clk/1024
            self.prescaler = 1024
            self.increment = True
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0
        elif self.CS == 6: # External clock on T0 pin. Clock on falling edge.
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0

            if (self.PrevT1 == 1 and self.T1.get() == 0):
                self.prescaler = 1
                self.increment = True
            else: 
                self.increment = False
            self.PrevT1 = self.T1.get()
        elif self.CS == 7: # External clock on T0 pin. Clock on rising edge.
            if self.CS != self.prevCS:
                self.prevCS = self.CS
                self.prescalerCounter = 0

            if (self.PrevT1 == 0 and self.T1.get() == 1):
                self.prescaler = 1
                self.increment = True
            else:
                self.increment = False
            self.PrevT1 = self.T1.get()
            
    def update_wave_gen_mode(self):
        self.WGM = self.WGM13<<3 | self.WGM12<<2 | self.WGM11<<1 | self.WGM10
        if self.WGM == 0:   #0
            self.opMode = 'NORMAL'
            self.TOP = 0xFFFF
        elif self.WGM == 1: #1  
            self.opMode = 'Phase_Correct_PWM_8bit'
            self.TOP = 0x00FF
        elif self.WGM == 2: #2
            self.opMode = 'Phase_Correct_PWM_9bit'
            self.TOP = 0x01FF
        elif self.WGM == 3: #3
            self.opMode = 'Phase_Correct_PWM_10bit'
            self.TOP = 0x02FF
        elif self.WGM == 4: #4
            self.TOP = ((self.OCR1AH&0xFF)<<8) | (self.OCR1AH&0xFF)
            self.opMode = 'CTC_O'
        elif self.WGM == 5: #5
            self.TOP = 0x00FF
            self.opMode = 'FAST_PWM_8bit'
        elif self.WGM == 6: #6
            self.TOP = 0x01FF
            self.opMode = 'FAST_PWM_9bit'
        elif self.WGM == 7: #7
            self.TOP = 0x02FF
            self.opMode = 'FAST_PWM_10bit'
        elif self.WGM == 8:
            self.TOP = ((self.ICR1H&0xFF)<<8) | (self.ICR1L&0xFF)
            self.opMode = 'Phase_Correct_And_Frequency_PWM_I'
        elif self.WGM == 9:
            self.TOP = ((self.OCR1AH&0xFF)<<8) | (self.OCR1AH&0xFF)
            self.opMode = 'Phase_Correct_And_Frequency_PWM_O'
        elif self.WGM == 10:
            self.TOP = ((self.ICR1H&0xFF)<<8) | (self.ICR1L&0xFF)
            self.opMode = 'Phase_Correct_PWM_I'
        elif self.WGM == 11:
            self.TOP = ((self.OCR1AH&0xFF)<<8) | (self.OCR1AH&0xFF)
            self.opMode = 'Phase_Correct_PWM_O'
        elif self.WGM == 12:
            self.TOP = ((self.ICR1H&0xFF)<<8) | (self.ICR1L&0xFF)
            self.opMode = 'CTC_I'
        elif self.WGM == 13:
            self.opMode = 'Reserved'
        elif self.WGM == 14:
            self.TOP = ((self.ICR1H&0xFF)<<8) | (self.ICR1L&0xFF)
            self.opMode = 'FAST_PWM_I'
        elif self.WGM == 15:
            self.TOP = ((self.OCR1AH&0xFF)<<8) | (self.OCR1AH&0xFF)
            self.opMode = 'FAST_PWM_O'

    def handle_normal_mode(self):
        #OC0A ## toggle 
        if self.COM1A == 1:
            if self.OCR1A == self.TCNT1:
                if self.OC1A.get() == 0:
                    self.OC1A_val = 1 
                else:
                    self.OC1A_val = 0
                #Interrupts
                if self.OCIE1A == 1:
                    self.OCF1A_val = 1

        elif self.COM1A == 2: ## clear 
            if self.OCR1A == self.TCNT0:
                self.OC1A_val = 0
                if self.OCIE1A == 1:
                    self.OCF1A_val = 1


        elif self.COM1A == 3: ## SET
            if self.OCR1A == self.TCNT1:
                self.OC1A_val = 1
                #Interrupts
                if self.OCIE1A == 1:
                    self.OCF1A_val = 1
                    
        else:
            self.OC1A_val = 0     ## normal operation disconnected
                

                    #OC0B
        if self.COM1B == 1: ## toggle 
            if self.OCR1B == self.TCNT1:
                if self.OC1B.get() == 0:
                    self.OC1B_val = 1 
                else:
                    self.OC1B_val = 0
                #Interrupts
                if self.OCIE1B == 1:
                    self.OCF1B_val = 1

        elif self.COM1B == 2: ## clear 
            if self.OCR1B == self.TCNT1:
                self.OC1B_val = 0
                #Interrupts
                if self.OCIE1B == 1:
                    self.OCF1B_val = 1   

        elif self.COM1B == 3: ## Set 
            if self.OCR1B == self.TCNT1:
                self.OC1B_val= 1
                #Interrupts
                if self.OCIE1B == 1:
                   self.OCF1B_val = 1 

        else:
            self.OC1B_val = 0 ## disconected
                
    def handle_Phase_Correct_PWM_mode(self):
        #OC0A
        if self.COM1A == 1: # at 0 0 OC0A is disconected 
            #if self.WGM02 == 0: #normal port operation
            if (self.WGM == 14) | (self.WGM == 15): # Toggle OC0A on compare match 
                if (self.OCR1A == self.TCNT1): 
                    if self.OC1A.get() == 0:
                        self.OC1A_val = 1
                    else:
                        self.OC1A_val = 0  
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1
            else:
                self.OC1A_val = 0 #disconnected

        elif self.COM1A == 2:
            if self.direction == 'Increment':
                if self.OCR1A == self.TCNT1 :
                    self.OC1A_val = 0
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1 
            elif self.direction == 'Decrement':
                if self.OCR1A == self.TCNT1 :
                    self.OC1A_val = 1
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1
                            
        elif self.COM1A == 3:
            if self.direction == 'Increment':
                if self.OCR1A == self.TCNT1 :
                    self.OC1A_val = 1
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1
            elif self.direction == 'Decrement':
                if self.OCR1A == self.TCNT0 :
                    self.OC1A_val = 0
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1

        #OC0B
        if self.COM1B == 1: 
            self.OC1B_val = 0
        

        elif self.COM1B == 2:
            if self.direction == 'Increment':
                if self.OCR1B == self.TCNT1 :
                    self.OC1B_val = 0
                    if self.OCIE1B == 1:
                        self.OCF1B_val = 1
            elif self.direction == 'Decrement':
                if self.OCR1B == self.TCNT0 :
                    self.OC1B_val = 1
                    if self.OCIE1B == 1:
                        self.OCF1B_val = 1
        elif self.COM1B == 3:
            if self.direction == 'Increment':
                if self.OCR1B == self.TCNT1 :
                    self.OC1B_val = 1
                    if self.OCIE1B == 1:
                        self.OCF1B_val = 1
            elif self.direction == 'Decrement':
                if self.OCR1B == self.TCNT1:
                    self.OC1B_val = 0
                    if self.OCIE1B == 1:
                        self.OCF1B_val = 1

    def handle_CTC_mode(self):
        #OC0A
        if self.COM1A == 1:
            if self.OCR1A == self.TCNT1:
                if self.OC1A.get() == 0:
                    self.OC1A_val = 1
                else:
                    self.OC1A_val = 0
                    
            #Interrupts
            if self.OCIE1A == 1:
                self.OCF1A_val = 1
                    
        elif self.COM1A == 2:
            if self.OCR1A == self.TCNT1:
                self.OC1A_val = 0
                
            #Interrupts
            if self.OCIE1A == 1:
                self.OCF1A_val = 1
                    
        elif self.COM1A == 3:
            if self.OCR1A == self.TCNT1:
                self.OC1A_val = 1

            #Interrupts
            if self.OCIE1A == 1:
                self.OCF1A_val = 1
                
        else:
            self.OC1A_val = 0     
                
            

        #OC0B
        if self.COM1B == 1: ## toggle 
            if self.OCR1B == self.TCNT1:
                if self.OC1B.get() == 0:
                    self.OC1B_val = 1 
                else:
                    self.OC1B_val = 0
                #Interrupts
                if self.OCIE1B == 1:
                    self.OCF1B_val = 1

        elif self.COM1B == 2: ## clear 
            if self.OCR1B == self.TCNT1:
                self.OC1B_val = 0
                #Interrupts
                if self.OCIE1B == 1:
                    self.OCF1B_val = 1   

        elif self.COM1B == 3: ## Set 
            if self.OCR1B == self.TCNT1:
                self.OC1B_val= 1
                #Interrupts
                if self.OCIE1B == 1:
                   self.OCF1B_val = 1 
        else:
            self.OC1B_val = 0 ## disconected

    def handle_FAST_PWM_mode(self):
        #OC0A
        if self.COM1A == 1: # at 0 0 OC0A is disconected 
            #if self.WGM02 == 0: #normal port operation
            
            if (self.WGM == 14) or (self.WGM == 15): # Toggle OC0A on compare match
                if (self.OCR1A == self.TCNT1): 
                    if self.OC1A.get() == 0:
                        self.OC1A.prepare(1)
                    else:
                        self.OC1A.prepare(0)
                    
        elif self.COM1A == 2:
            if self.OCR1A == self. TCNT1:
                self.OC1A.prepare(0)

        elif self.COM1A == 3:
            if self.OCR1A == self. TCNT1:
                self.OC1A.prepare(1)

        #OC0B
        if self.COM1B == 1: # at 0 0 OC0A is disconected 
            #if self.WGM02 == 0: #normal port operation
            
            if self.WGM12 == 1: # Toggle OC0A on compare match
                if (self.OCR1B == self.TCNT1): 
                    if self.OC1B.get() == 0:
                        self.OC1B.prepare(1)
                    else:
                        self.OC1B.prepare(0)
                    
        elif self.COM1B == 2:
            if self.OCR1B == self. TCNT1:
                self.OC1B.prepare(0)

        elif self.COM1B == 3:
            if self.OCR1B == self. TCNT1:
                self.OC1B.prepare(1)

    def handle_Phase_Correct_And_Frequency_PWM_mode(self):
        #OC0A
        if self.COM1A == 1: # at 0 0 OC0A is disconected 
            #if self.WGM02 == 0: #normal port operation
            if (self.WGM == 9) | (self.WGM == 11): # Toggle OC0A on compare match 
                if (self.OCR1A == self.TCNT1): 
                    if self.OC1A.get() == 0:
                        self.OC1A_val = 1
                    else:
                        self.OC1A_val = 0  
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1
            else:
                self.OC1A_val = 0 #disconnected

        elif self.COM1A == 2:
            if self.direction == 'Increment':
                if self.OCR1A == self.TCNT1 :
                    self.OC1A_val = 0
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1 
            elif self.direction == 'Decrement':
                if self.OCR1A == self.TCNT1 :
                    self.OC1A_val = 1
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1
                            
        elif self.COM1A == 3:
            if self.direction == 'Increment':
                if self.OCR1A == self.TCNT1 :
                    self.OC1A_val = 1
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1
            elif self.direction == 'Decrement':
                if self.OCR1A == self.TCNT1 :
                    self.OC1A_val = 0
                    if self.OCIE1A == 1:
                        self.OCF1A_val = 1
                

        #OC0B
        if self.COM1B == 1: 
            self.OC1B_val = 0
                    

        elif self.COM1B == 2:
            if self.direction == 'Increment':
                if self.OCR1B == self.TCNT1 :
                    self.OC1B_val = 0
                    if self.OCIE1B == 1:
                        self.OCF1B_val = 1
            elif self.direction == 'Decrement':
                if self.OCR1B == self.TCNT1 :
                    self.OC1B_val = 1
                    if self.OCIE1B == 1:
                        self.OCF1B_val = 1
        elif self.COM1B == 3:
            if self.direction == 'Increment':
                if self.OCR1B == self.TCNT1 :
                    self.OC1B_val = 1
                    if self.OCIE1B == 1:
                        self.OCF1B_val = 1
            elif self.direction == 'Decrement':
                if self.OCR1B == self.TCNT1:
                    self.OC1B_val = 0
                    if self.OCIE1B == 1:
                        self.OCF1B_val = 1

    def Phase_Correct_PWM_Increment(self):
        if self.direction == 'Increment':
            self.TCNT1 += 1
            if self.TCNT1 >= self.TOP:
                self.TCNT1    = self.TOP   
                self.direction = 'Decrement'
                #return skip compare match at TOP

        elif self.direction == 'Decrement':
            self.TCNT1 -= 1
            if self.TCNT1 <= self.BOTTOM:
                self.TCNT1    = self.BOTTOM
                self.direction = 'Increment'
                if self.TOIE1 == 1:
                    self.TOV1_val = 1

    def Other_modes_Increment(self):
        if self.direction == 'Increment':
            self.TCNT1 += 1
            if self.TCNT1 >= self.TOP:
                if self.opMode == 'CTC':
                    self.TCNT1 = self.BOTTOM
                else:
                    self.TCNT1 = self.BOTTOM
                if self.OCIE1A == 1: ## Interrupt
                    self.OCF1A_val = 1

                if self.TOIE1 == 1:
                    self.TOV1_val = 1    
                else:
                    self.TOV1_val = 0

    def increment(self):
        if( self.incrementEnable == True):
            self.prescalerCounter +=1
            
        if (self.prescaler != 0) and (self.prescaler == self.prescalerCounter): 
            self.prescalerCounter = 0
            # Incrementing and Decrementing
            if (self.opMode == 'Phase_Correct_PWM') or (self.opMode == 'Phase_Correct_PWM_8bit') or (self.opMode == 'Phase_Correct_PWM_9bit') or (self.opMode == 'Phase_Correct_PWM_10bit') or (self.opMode == 'Phase_Correct_And_Frequency_PWM_I') or (self.opMode == 'Phase_Correct_And_Frequency_PWM_O'):
                self.Phase_Correct_PWM_Increment()
                #return   # skip determine_outputs at TOP turnaround
            else:  # NORMAL, CTC, FAST_PWM
                self.Other_modes_Increment()
            self.TCNT1 = self.TCNT1 & 0xFF

            self.determine_outputs()

    def determine_outputs(self):
            match self.opMode:
                case 'NORMAL':
                    self.handle_normal_mode()
                case 'Phase_Correct_PWM_8bit':
                    self.handle_Phase_Correct_PWM_mode()
                case 'Phase_Correct_PWM_9bit':
                    self.handle_Phase_Correct_PWM_mode()
                case 'Phase_Correct_PWM_10bit':
                    self.handle_Phase_Correct_PWM_mode()
                case 'CTC_O':
                    self.handle_CTC_mode()
                case 'FAST_PWM_8bit':
                    self.handle_FAST_PWM_mode()
                case 'FAST_PWM_9bit':
                    self.handle_FAST_PWM_mode()
                case 'FAST_PWM_10bit':
                    self.handle_FAST_PWM_mode()
                case 'Phase_Correct_And_Frequency_PWM_I':
                    self.handle_Phase_Correct_And_Frequency_PWM_mode()
                case 'Phase_Correct_And_Frequency_PWM_O':
                    self.handle_Phase_Correct_And_Frequency_PWM_mode()
                case 'Phase_Correct_PWM_I':
                    self.handle_Phase_Correct_PWM_mode()
                case 'Phase_Correct_PWM_O':
                    self.handle_Phase_Correct_PWM_mode()
                case 'CTC_I':   
                    self.handle_CTC_mode()
                case 'Reserved':
                    print("Reserved")
                case 'FAST_PWM_I':
                    self.handle_FAST_PWM_mode()
                case 'FAST_PWM_O':
                    self.handle_FAST_PWM_mode()

    def update_outputs(self):
        self.OC1A.prepare(self.OC1A_val)
        self.OC1B.prepare(self.OC1B_val)
        self.OCF1B.prepare(self.OCF1B_val)
        self.OCF1A.prepare(self.OCF1A_val)
        self.TOV1.prepare(self.TOV1_val)

    def clock(self):
        self.Memory_access()
        self.Parse_control_registers()
        self.update_prescaler()
        self.update_wave_gen_mode()
        self.increment()
        self.update_outputs()



class SimpleTimer(py4hw.Logic):
    def __init__(self, parent, name: str, memory: py4hw.Interface, TIMER0_OVF):
        super().__init__(parent, name)
 
        self.interface = self.addInterfaceSink('port', memory)
        self.TIMER0_OVF = self.addOut('TIMER0_OVF', TIMER0_OVF)
 
        self.tccr0a = 0x00
        self.tccr0b = 0x00
        self.tcnt0  = 0x00
        self.timsk0 = 0x00
        self.tifr0  = 0x00  # ADDED: Timer Interrupt Flag Register
        
        self.prescaler_counter = 0
 
    def clock(self):
        bus_active = (self.interface.read.get() == 1) or (self.interface.write.get() == 1)
        if bus_active:
            self.interface.resp.prepare(1)
        else:
            self.interface.resp.prepare(0)
 
        self.interface.read_data.prepare(0)
 
        # Handle Bus WRITE
        if self.interface.write.get() == 1:
            addr = self.interface.address.get()
            data = self.interface.write_data.get()
            
            if addr == 0x04:   self.tccr0a = data & 0xFF
            elif addr == 0x05: self.tccr0b = data & 0xFF
            elif addr == 0x06: self.tcnt0  = data & 0xFF
            elif addr == 0x07: 
                # Real AVR behavior: Writing a 1 to the flag bit clears it
                if (data & 0x01):
                    self.tifr0 &= ~0x01
            elif addr == 0x2E: self.timsk0 = data & 0xFF
 
        # Handle Bus READ
        elif self.interface.read.get() == 1:
            addr = self.interface.address.get()
            
            if addr == 0x04:   self.interface.read_data.prepare(self.tccr0a)
            elif addr == 0x05: self.interface.read_data.prepare(self.tccr0b)
            elif addr == 0x06: self.interface.read_data.prepare(self.tcnt0)
            elif addr == 0x07: self.interface.read_data.prepare(self.tifr0)
            elif addr == 0x2E: self.interface.read_data.prepare(self.timsk0)
 
        # Timer Counting & Prescaler Logic
        cs_bits = self.tccr0b & 0x07
        prescaler_limit = 0
        
        if cs_bits == 1: prescaler_limit = 1
        elif cs_bits == 2: prescaler_limit = 8
        elif cs_bits == 3: prescaler_limit = 64
        elif cs_bits == 4: prescaler_limit = 256
        elif cs_bits == 5: prescaler_limit = 1024
            
        if prescaler_limit > 0:
            self.prescaler_counter += 1
            if self.prescaler_counter >= prescaler_limit:
                self.prescaler_counter = 0
                
                if self.tcnt0 == 0xFF:
                    self.tcnt0 = 0x00
                    self.tifr0 |= 0x01  # LATCH THE OVERFLOW FLAG
                else:
                    self.tcnt0 += 1
 
        # Assert wire as long as flag is latched and interrupts are enabled
        if (self.timsk0 & 0x01) and (self.tifr0 & 0x01):
            self.TIMER0_OVF.prepare(1)
        else:
            self.TIMER0_OVF.prepare(0)
