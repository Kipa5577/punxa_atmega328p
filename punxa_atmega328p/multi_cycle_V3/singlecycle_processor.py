import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.instruction_decode import ins_to_str
from punxa_atmega328p.instruction_decode import TWO_CYCLE_INSRUCTIONS
from punxa_atmega328p.instruction_decode import MEMORY_INSTRUCTIONS
from punxa_atmega328p.Memory import *

from punxa_atmega328p.csr import *
from deprecated import deprecated

## *_IO = IN and OUT instruction address
## *_LS =  LD LDS ST STS instruction address

#0x0000 to 0x3FFF flash memory range 

#Start of Sram : 0x0100 | End of Sram : 0x08FF
#pointer registers
# R26 X-register Low Byte 
# R27 X-register High Byte
# R28 Y-register Low Byte
# R29 Y-register High Byte
# R30 Z-register Low Byte 
# R31 Z-register High Byte
 
# interupt wires to add: INT0, INT1, PCINT0, PCINT1, PCINT2, WDT, TIMER2 COMPA, TIMER2 COMPB, TIMER2 OVF, TIMER1 CAPT, TIMER1 COMPA, TIMER1 COMPB, TIMER1 OVF, TIMER0 COMPA, TIMER0 COMPB, TIMER0 OVF, SPI/STC , USART/RX , USART/UDRE , USART/TX , ADC , EE READY , ANALOG COMP, TWI, SPM READY.
 

# For this design I want the fetch to happen at the same time as the EXECUTION



STATES = [
    "STATE_RESET",
    "FETCH_INSTRUCTION","WAIT_FETCH_INSTRUCTION","STATE_DECODE_EXEC",
    "STATE_FETCH_OP2_REQ", "STATE_FETCH_OP2_WAIT",
    "STATE_FETCH_REQ","STATE_MEM_WAIT",
    # CALL/RET
    "STATE_CALL_PUSH_H","STATE_CALL_PUSH_L",
    "STATE_RET_POP_L","STATE_RET_POP_H",
    # Indirect load/store , LPM
    "STATE_INDIRECT_LOAD","STATE_INDIRECT_STORE",
    "STATE_LPM_REQ","STATE_LPM_WAIT",
    # I/O bit read-modify-write
    "STATE_IO_BIT_READ","STATE_IO_BIT_WRITE",
    # SKIP
    "STATE_SKIP_FETCH_REQ","STATE_SKIP_FETCH_WAIT"
]

FETCH_HANDLER_STATES = [
    "FETCH_INSTRUCTION","WAIT_FETCH_INSTRUCTION","STOP","STATE_RESET"
]

CPU_STATES = [

    #GENERAL_STATES
    "STATE_RESET",
    "EXECUTE_INSTRUCTION",
    "STATE_SLEEP",
    "STATE_WDT",

    # CALL/RET
    "STATE_CALL_PUSH_H","STATE_CALL_PUSH_L",
    "STATE_RET_POP_L","STATE_RET_POP_H",
    # Indirect load/store , LPM
    "STATE_INDIRECT_LOAD","STATE_INDIRECT_STORE",
    "STATE_LPM_REQ","STATE_LPM_WAIT",
    # I/O bit read-modify-write
    "STATE_IO_BIT_READ","STATE_IO_BIT_WRITE",
    # SKIP
    "STATE_SKIP_FETCH_REQ","STATE_SKIP_FETCH_WAIT",
]




class MultyCycleATmega328P_V3(py4hw.Logic):
    def __init__(self,parent, name:str , ins_mem:MemoryInterface,memory:MemoryInterface, reset_address):#INT0,INT1,PCINT0,PCINT1,PCINT2,WDT,TIMER2_COMPA,TIMER2_COMPB,TIMER2_OVF,TIMER1_CAPT,TIMER1_COMPA,TIMER1_COMPB,TIMER1_OVF,TIMER0_COMPA,TIMER0_COMPB,TIMER0_OVF,SPI_STC,USART_RX,USART_UDRE,USART_TX,ADC,EE_READY,ANALOG_COMP,TWI,SPM_READY):
        super().__init__(parent,name)

        assert(ins_mem.read_data.getWidth() == 16)
        assert(memory.read_data.getWidth() == 8)
        
        self.ins_mem = self.addInterfaceSource('ins', ins_mem)
        self.mem = self.addInterfaceSource('data', memory)
        self.pc = reset_address,
        self.reg = [0]*32

        self.reset_pc_address = reset_address

        
        self.next_cycle = False #varible to indicate that data is ready to read from ram/memeory
        self.ins = 0
        self.opp = 'NOP'
        self.Rr = 0
        self.Rd = 0
        self.res = 0
        self.K = 0
        self.FirstBoot = True #is this actuatly odable ?
        self.BOOTRST = 1
        self.databyteNb = 0
        self.FSM = 'Begin' 

        self.A = 0
        self.q = 0
        self.high = 0
        self.low = 0

        #registers
        self.SREG = 0 # b7: I b6: T b5: H b4: S b3: V b2: N b1: Z b0: C 
        self.SREG_addr_IO = 0x3F
        self.SREG_addr_LS = 0x5F

        self.MCUCR = 0
        self.MCUCR_addr_IO = 0x35
        self.MCUCR_addr_LS = 0x55

        #Stack Pointer
        self.SPH = 0x08
        self.SPH_addr_IO = 0x3E
        self.SPH_addr_LS = 0x5E

        self.SPL = 0xFF
        self.SPL_addr_IO = 0x3D
        self.SPH_addr_LS = 0x5D

        self.MCUSR = 0x02 # Power-on Reset  or it can be 0x02 External Reset
        self.MCUSR_addr_IO = 0x34
        self.MCUSR_addr_LS = 0x54

        #Warchdog Timer Configruation
        self.WDTCSR = 0
        self.WDTCSR_addr_LS = 0x60

        #SPMCSR - Store Program Memory Control and Status Register
        self.SPMCSR = 0 
        self.SPMCSR_addr_IO = 0x37
        self.SPMCSR_addr_LS = 0x57


        self.skip_next_instruction = False

        self.gotToGoFast = False

        self.insFiniteStateMachine = 'START'

        self.PAGE_SIZE_WORDS = 64
        
        self.temp_page_buffer = [0xFFFF] * self.PAGE_SIZE_WORDS     

        self.state_fetcher = "STATE_RESET"
        self.state_executor = "STATE_RESET"

        self.last_pc = 0

    def clock(self):

        # State Machine for the instruction fetcher 

        match self.state_fetcher:
            case "STATE_RESET":
                self.pc = self.reset_pc_val
                self.ins_mem.read.prepare(0)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.pc)

            case "STOP":
                self.ins_mem.read.prepare(0)
                self.ins_mem.write.prepare(0)
                if self.last_pc != self.pc:
                    self.state_fetcher = "FETCH_INSTRUCTION"
                    self.last_pc = self.pc
            
            case "FETCH_INSTRUCTION":
                self.ins_mem.read.prepare(1)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.pc)
            case "WAIT_FETCH_INSTRUCTION":
                self.ins_mem.read.prepare(1)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.pc)
                if  self.ins_mem.resp.get() == 1:
                    self.state_fetcher = "STOP"
                    self.ins = self.ins_mem.read_data.get()

        match self.state:

            case "FETCH_INSTRUCTION":
                self.ins_mem.read.prepare(1)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.pc)
                if  self.ins_mem.resp.get() == 1:
                    self.state = "EXECUTE_INSTRUCTION"
                    self.ins = self.ins_mem.read_data.get()
            case "EXECUTE_INSTRUCTION":
                self.execute()
                if self.last_pc != self.pc:
                    self.state = "FETCH_INSTRUCTION"

        # State Machine for the instrucion executor

        match self.state_executor:

            case "STATE_RESET":

            case "EXECUTE_INSTRUCTION":
                self.execute()

            case "STATE_SLEEP":

            case "STATE_WDT":

            
            
            


#    def HandleInterupts(self):

    def writeToMemory(self,Rr,A,q):
        self.A = A
        self.Rr = Rr

        #preparing write operation
        if (self.databyteNb == 1) and (self.mem.resp.get() == 1):
            self.mem.write.prepare(0)
            self.mem.read.prepare(0) 
        else:
            self.mem.write.prepare(1)
            self.mem.read.prepare(0)

        if (self.databyteNb == 0) and (self.mem.resp.get() == 0):
            #writing the first byte
            self.mem.address.prepare(self.A+q)
            self.mem.write_data.prepare(self.reg[self.Rd])  
            self.databyteNb = 1 
            print("byte 1")
        elif((self.databyteNb == 1) and (self.mem.resp.get() == 1)):# if it is time to write the second byte and the memory finished writing the first byte
            self.pc += 1
            self.databyteNb = 0


    def readFromMemory(self,Rd,A,q):
        self.A = A
        self.Rd = Rd
        val = 0

        if (self.databyteNb == 0) and (self.mem.resp.get() == 0):
            self.mem.write.prepare(0)
            self.mem.read.prepare(1)
            self.mem.address.prepare(A)


        elif (self.databyteNb == 0) and (self.mem.resp.get() == 1):
            val = self.mem.read_data.get()
            self.databyteNb = 1 
            self.mem.write.prepare(0)
            self.mem.read.prepare(0)
            print("byte 1")


        elif (self.databyteNb == 2) and (self.mem.resp.get() == 1):

            print("low=",bin(self.low))
            self.databyteNb = 0
            print("byte 2")
            self.K = (self.high<<8) | self.low
            self.pc  = self.K
            SP = ((self.SPH<<8) | (self.SPL))+2
            self.SPH = (SP>>8)&0xFF
            self.SPL = SP&0xFF



    def execute(self):
        self.opp =  ins_to_str(self.ins)

        match self.opp: 
            case 'ADD':
                self.Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res = (self.reg[self.Rd] + self.reg[self.Rr]) &0xFF

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if (Rd7 & Rr7 )|( Rr7 & (not R7))|((not R7) & Rd7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & Rr7 & (not R7)) | ((not Rd7) & (not Rr7) & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if (Rd3 & Rr3)|(Rr3 & (not R3))|((not R3) & Rd3):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                
                self.reg[self.Rd] =  self.res

                self.pc += 1
            case 'ADC': # there may be a problem with this but I don't know what is the problem

                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>4) & 0x1F)
                Rd7 = (self.reg[self.Rd]>>7)&0b1
                Rr7 = (self.reg[self.Rr]>>7)&0b1

                self.res =  (self.reg[self.Rd] + self.reg[self.Rr] + (self.SREG & 0b1)) &0xFF
                Rd3 = (self.reg[self.Rd]>>3)&0b1
                Rr3 = (self.reg[self.Rr]>>3)&0b1

                R7  = (self.res>>7)&0b1
                R3  = (self.res>>3)&0b1

                #H
                if ((Rd3 & Rr3)|(Rr3 & (1 - R3))|(Rd3 & (1 - R3))):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)
                
                #self.SREG &= ~(1<<5) # This is a bipas 

                #C
                if (Rd7 & Rr7 )|( Rr7 & (not R7))|((not R7) & Rd7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)

                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                #V
                V = ((Rd7 & Rr7 & (not R7)) | ((not Rd7) & (not Rr7) & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] = self.res & 0xFF

                self.pc += 1
            case 'ADIW':
                self.K = (((self.ins>>6)&0b11)<<4)|(self.ins & 0xF)
                self.Rd = 24 + (((self.ins >> 4) & 0b11) * 2)
                self.res =  (self.reg[self.Rd+1]<<8|self.reg[self.Rd])  +  self.K

                Rdh7 = ((self.reg[self.Rd+1]>>7)&0b1)
                R15 = ((self.res>>15)&0b1)

                #C
                if (not R15) & Rdh7:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z
                N = (self.res == 0)
                if N == 1:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R15 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = (not Rdh7) & R15
                if V == 1 :
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if (N)^(V):
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] =  self.res & 0xFF
                self.reg[self.Rd+1] =  (self.res>>8) & 0xFF

                self.pc += 1
            case 'SUB':

                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  (self.reg[self.Rd] - self.reg[self.Rr]) & 0xFF


                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #C
                if ((not Rd7) & Rr7 )|( Rr7 & R7)|( R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & (not Rr7) & (not R7)) | ((not Rd7) & Rr7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1

                if ((not Rd3) & Rr3)|(Rr3 & R3)|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res & 0xFF

                self.pc += 1
            case 'SUBI':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = 16 + ((self.ins >> 4) & 0xF)
                self.res = self.reg[self.Rd] - self.K

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                K7= ((self.K&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #C
                if ((not Rd7) & K7 )|( K7 & R7)|( R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & (not K7) & (not R7)) | ((not Rd7) & K7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                K3= ((self.K&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1

                if ((not Rd3) & K3)|(K3 & R3)|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)



                self.reg[self.Rd] =  self.res & 0xFF

                self.pc += 1
            case 'SBC':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] - self.reg[self.Rr] - (self.SREG & 0b1)

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #C
                if ((not Rd7) & Rr7 )|( Rr7 & R7)|( R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                current_Z = (self.SREG >> 1) & 0b1
                if (self.res&0xFF == 0) and current_Z == 1:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & (not Rr7) & (not R7)) | ((not Rd7) & Rr7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1

                if ((not Rd3) & Rr3)|(Rr3 & R3)|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res & 0xFF
                self.pc += 1
            case 'SBCI':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] - self.K - (self.SREG & 0b1)

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                K7= ((self.K&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #C
                if ((not Rd7) & K7 )|( K7 & R7)|( R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                current_Z = (self.SREG >> 1) & 0b1
                if (self.res&0xFF == 0) and current_Z == 1:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & (not K7) & (not R7)) | ((not Rd7) & K7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                K3= ((self.K&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1

                if ((not Rd3) & K3)|(K3 & R3)|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res & 0xFF
                self.pc += 1
            case 'SBIW':
                self.K = (((self.ins>>6)&0b11)<<4)|(self.ins & 0xF)
                self.Rd = 24 + (((self.ins>>4)&0b11) * 2)
                self.res =  (self.reg[self.Rd+1]<<8|self.reg[self.Rd]) -  self.K

                Rdh7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                R15 = ((self.res&0xFF)>>7)&0b1

                #C
                if R15 & (not Rdh7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if (self.res&0xFF == 0):
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R15 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V

                V = (not R15) & Rdh7 
                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R15:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)


                self.reg[self.Rd] =  self.res&0xFF
                self.reg[self.Rd+1] = (self.res>>8)&0xFF 

                self.pc += 1
            case 'AND':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] & self.reg[self.Rr]


                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res

                self.pc += 1
            case 'ANDI':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] & self.K 

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  


                self.reg[self.Rd] =  self.res
                self.pc += 1
            case 'OR':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] | self.reg[self.Rr]

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  



                self.reg[self.Rd] =  self.res

                self.pc += 1
            case 'ORI':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] | self.K 

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res
                self.pc += 1
            case 'EOR':
                self.Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] ^ self.reg[self.Rr]

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res

                self.pc += 1
            case 'COM':
                self.Rd = ((self.ins>>4) & 0x1F)
                self.res = 0xFF - self.reg[self.Rd] 

                R7 =  ((self.res&0xFF)>>7)&0b1
                self.SREG |= (1<<0) #flag C to 1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res

                self.pc += 1
            case 'NEG':
                self.Rd = ((self.ins>>4) & 0x1F)
                self.res = (0x00 - self.reg[self.Rd]) & 0xFF 

                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if self.res != 0:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                
                #V
                V = (self.res == 0x80)
                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd])>>3)&0b1
                R3 = (self.res>>3)&0b1
                if (1- Rd3) | R3 :
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res
                self.pc += 1
            case 'SBR':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] | self.K 

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res
                self.pc += 1
                self.pc += 1
            case 'CBR':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] & self.K 

                self.testZ(self.res)
                self.testN(self.res)
#                self.SREG &= ~(1<<V) # flag V to 0
                self.testS()     

                self.reg[self.Rd] =  self.res 
                self.pc += 1
            case 'INC':
                self.Rd = ((self.ins>>4) & 0x1F)
                self.res = (self.reg[self.Rd] + 1) & 0xFF
                
                R7 =  ((self.res&0xFF)>>7)&0b1

                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                
                #V
                V = (self.Rd == 0x80)
                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)



                self.reg[self.Rd] =  self.res 
                self.pc += 1
            case 'DEC':
                self.Rd = ((self.ins>>4) & 0x1F)
                self.res = (self.reg[self.Rd] - 1) & 0xFF

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                
                #V
                V = (self.Rd == 0x80)
                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] =  self.res
                self.pc += 1
            case 'SER':
                self.Rd = (self.ins>>4)&0b1111 + 16
                self.reg[self.Rd] = 0xFF
        

                self.pc +=1 
            case 'MUL':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] * self.reg[self.Rr]

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1] = (self.res>>8) &0xFF
                self.reg[0] = self.res & 0xFF

                self.pc += 1
            case 'MULS': 
                self.Rr = (self.ins & 0xF) + 16
                self.Rd = ((self.ins>>4) & 0xF) + 16

                val_Rd = self.reg[self.Rd] & 0xFF
                val_Rr = self.reg[self.Rr] & 0xFF

                if val_Rd >= 128:
                    val_Rd -=256
                if val_Rr >= 128:
                    val_Rr -=256

                self.res =  (val_Rd * val_Rr) & 0xFFFF

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= (self.res>>8) & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
            case 'MULSU':
                self.Rr = (self.ins & 0b111) + 16
                self.Rd = ((self.ins>>4) & 0b111) + 16

                val_Rd = self.reg[self.Rd] & 0xFF
                val_Rr = self.reg[self.Rr] & 0xFF

                if val_Rd >= 128:
                    val_Rd -=256
                if val_Rr >= 128:
                    val_Rr -=256

                self.res =  (val_Rd * val_Rr) & 0xFFFF

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= self.res>>8 & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
            case 'FMUL':
                self.Rr = (self.ins & 0b111) + 16
                self.Rd = ((self.ins>>4) & 0b111) + 16
                self.res =  (self.reg[self.Rd]&0xFF) * (self.reg[self.Rr]&0xFF)

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                self.res = (self.res <<1) &0xFFFF

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= self.res>>8 & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
            case 'FMULS': 
                self.Rr = (self.ins & 0b111) + 16
                self.Rd = ((self.ins>>4) & 0b111) + 16
                val_Rd = self.reg[self.Rd] & 0xFF
                val_Rr = self.reg[self.Rr] & 0xFF

                if val_Rd >= 128:
                    val_Rd -=256
                if val_Rr >= 128:
                    val_Rr -=256

                self.res =  (val_Rd * val_Rr) & 0xFFFF

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                self.res = (self.res <<1) &0xFFFF

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= (self.res>>8) & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
            case 'FMULSU':
                self.Rr = (self.ins & 0b111) + 16 
                self.Rd = ((self.ins>>4) & 0b111) + 16

                val_Rd = self.reg[self.Rd] & 0xFF
                val_Rr = self.reg[self.Rr] & 0xFF

                if val_Rd >= 128:
                    val_Rd -=256
                if val_Rr >= 128:
                    val_Rr -=256

                self.res =  (val_Rd * val_Rr) & 0xFFFF

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                self.res = (self.res <<1) &0xFFFF

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= (self.res>>8) & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
            case 'RJMP':
                self.K = self.ins & 0xFFF
                if self.K>>11:
                    self.pc -=((~self.K)&0xFFF) + 1 
                else:
                    self.pc += self.K + 1 
            case 'IJMP':
                self.pc  = + (self.reg[30] | self.reg[31]<<8)
            case 'JMP':
                self.K = (((self.ins>>4)&0x1F)<<17)|(self.ins&0b1<<16)|self.flash[self.pc+1] 
                self.pc = self.K
            case 'RCALL':
                self.K = self.ins&0xFFF
                #handeling negative K numbers
                if self.K>>11 == 1:
                    self.K = -(((~self.K)&0xFFF) + 1)
                else:
                    self.K = self.K
                    
                SP = ((self.SPH<<8) | (self.SPL))
                print("SP=",SP)
                PC_to_store = (self.pc+1)&0xFFFF
                print("PC_to_store=",bin(PC_to_store))
                #separation of PC in 2 bytes

                PClwo = PC_to_store&0xFF
                PChigh = PC_to_store>>8
                print("PClwo=",bin(PClwo))
                print("PChigh=",bin(PChigh))

                #preparing write operation
                if self.databyteNb == 2:
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 
                else:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                if (self.databyteNb == 0) and (self.mem.resp.get() == 0):
                    #writing the first byte
                    self.mem.address.prepare(SP)
                    self.mem.write_data.prepare(PClwo)  
                    self.databyteNb = 1 
                    print("byte 1")
                elif((self.databyteNb == 1) and (self.mem.resp.get() == 1)):# if it is time to write the second byte and the memory finished writing the first byte
                    self.mem.address.prepare(SP-1)
                    self.mem.write_data.prepare(PChigh)
                    self.databyteNb = 2
                    #changing the stack pointer
                    SP -= 2
                    self.SPH = (SP>>8)&0xFF
                    self.SPL = SP&0xFF
                    print("byte 2")
                elif((self.databyteNb == 2) and (self.mem.resp.get() == 1)):
                    self.pc += self.K + 1
                    self.databyteNb = 0
            case 'ICALL':
                self.A = (self.reg[30]&0xFF) | ((self.reg[31]&0xFF)<<8) 
                SP = ((self.SPH&0xFF)<<8) | (self.SPL&0xFF)


                PC_to_store = (self.pc+2)&0xFFFF


                PClwo = PC_to_store&0xFF
                PChigh = (PC_to_store>>8)&0xFF


                match self.insFiniteStateMachine:

                    case 'START':
                        self.mem.write.prepare(1)
                        self.mem.read.prepare(0)

                        self.mem.address.prepare(SP)
                        self.mem.write_data.prepare(PClwo)

                        if(self.mem.resp.get() == 1):
                            self.insFiniteStateMachine = 'STEP1'

                    case 'STEP1':

                        self.mem.write.prepare(0)
                        self.mem.read.prepare(0)
                    
                        self.insFiniteStateMachine = 'STEP2'

                    case 'STEP2':

                        self.mem.write.prepare(1)
                        self.mem.read.prepare(0)
                    
                        self.mem.address.prepare(SP-1)
                        self.mem.write_data.prepare(PChigh)

                        if(self.mem.resp.get() == 1):
                            self.insFiniteStateMachine = 'STEP3'

                    case 'STEP3':

                        self.mem.write.prepare(0)
                        self.mem.read.prepare(0)
                            
                        self.insFiniteStateMachine = 'START'

                        SP = SP - 2
                        self.SPH = (SP>>8)&0xFF
                        self.SPL = SP&0xFF

                        self.pc = self.A  
            case 'CALL':
                self.K = (((self.ins>>4)&0x1F)<<17)|((self.ins&0b1)<<16)|self.flash[self.pc+1] 
                SP = ((self.SPH&0xFF)<<8) | (self.SPL&0xFF)


                PC_to_store = (self.pc+2)&0xFFFF


                PClwo = PC_to_store&0xFF
                PChigh = (PC_to_store>>8)&0xFF


                match self.insFiniteStateMachine:

                    case 'START':
                        self.mem.write.prepare(1)
                        self.mem.read.prepare(0)

                        self.mem.address.prepare(SP)
                        self.mem.write_data.prepare(PClwo)

                        if(self.mem.resp.get() == 1):
                            self.insFiniteStateMachine = 'STEP1'

                    case 'STEP1':

                        self.mem.write.prepare(0)
                        self.mem.read.prepare(0)
                    
                        self.insFiniteStateMachine = 'STEP2'

                    case 'STEP2':

                        self.mem.write.prepare(1)
                        self.mem.read.prepare(0)
                    
                        self.mem.address.prepare(SP-1)
                        self.mem.write_data.prepare(PChigh)

                        if(self.mem.resp.get() == 1):
                            self.insFiniteStateMachine = 'STEP3'

                    case 'STEP3':

                        self.mem.write.prepare(0)
                        self.mem.read.prepare(0)
                            
                        self.insFiniteStateMachine = 'START'

                        SP = SP - 2
                        self.SPH = (SP>>8)&0xFF
                        self.SPL = SP&0xFF

                        self.pc = self.K
            case 'RET':


                match self.insFiniteStateMachine:
                    
                    case 'START':
                        SP = (((self.SPH&0xFF)<<8) | (self.SPL&0xFF))+1

                        self.mem.address.prepare(SP)
                        self.mem.write.prepare(0)
                        self.mem.read.prepare(1)

                        if self.mem.read.get() == 1:
                            self.insFiniteStateMachine = 'STEP1'
                            
                    case 'STEP1':
                        self.high = self.mem.read_data.get()
                        self.mem.write.prepare(0)
                        self.mem.read.prepare(0)
                        self.insFiniteStateMachine = 'STEP2'

                    case 'STEP2':
                        SP = (((self.SPH&0xFF)<<8) | (self.SPL&0xFF))+2
                        self.mem.address.prepare(SP)
                        self.mem.write.prepare(0)
                        self.mem.read.prepare(1)


                        if self.mem.read.get() == 1 :
                            self.insFiniteStateMachine = 'STEP3'

                    case 'STEP3': 
                        self.low = self.mem.read_data.get()
                        SP = (((self.SPH&0xFF)<<8) | (self.SPL&0xFF))+2

                        self.SPH = (SP>>8)&0x00FF
                        self.SPL = SP&0x00FF
                        self.pc  = ((self.high&0xFF)<<8) | (self.low&0xFF)
                        self.insFiniteStateMachine = 'START'
            case 'RETI':## return from interrupt 
                match self.insFiniteStateMachine:
                    
                    case 'START':
                        SP = (((self.SPH&0xFF)<<8) | (self.SPL&0xFF))+1

                        self.mem.address.prepare(SP)
                        self.mem.write.prepare(0)
                        self.mem.read.prepare(1)

                        if self.mem.read.get() == 1:
                            self.insFiniteStateMachine = 'STEP1'
                            
                    case 'STEP1':
                        self.high = self.mem.read_data.get()
                        self.mem.write.prepare(0)
                        self.mem.read.prepare(0)
                        self.insFiniteStateMachine = 'STEP2'

                    case 'STEP2':
                        SP = (((self.SPH&0xFF)<<8) | (self.SPL&0xFF))+2
                        self.mem.address.prepare(SP)
                        self.mem.write.prepare(0)
                        self.mem.read.prepare(1)


                        if self.mem.read.get() == 1 :
                            self.insFiniteStateMachine = 'STEP3'

                    case 'STEP3': 
                        self.low = self.mem.read_data.get()
                        SP = (((self.SPH&0xFF)<<8) | (self.SPL&0xFF))+2

                        self.SPH = (SP>>8)&0x00FF
                        self.SPL = SP&0x00FF
                        self.pc  = ((self.high&0xFF)<<8) | (self.low&0xFF)
                        self.insFiniteStateMachine = 'START'

            case 'CPSE':
                self.Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)


                if self.reg[self.Rr] == self.reg[self.Rd]:
                    next_ins = ins_to_str(self.flash[self.pc])
                    if(next_ins == 'CALL' or next_ins == 'JMP' or next_ins == 'STS' or next_ins == 'LDS'):
                        self.pc += 3 ##skip 2 word instruction
                    else:
                        self.pc += 2## skip 1 word instruction 
                else:
                    self.pc += 1
            case 'CP':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] - self.reg[self.Rr] 

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if ((not Rd7) & Rr7 )|( Rr7 & R7)|(R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)

                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                #V
                V = ((Rd7 & (not Rr7) & (not R7)) | ((not Rd7) & Rr7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if ((not Rd3) & Rr3)|(Rr3 & (not R3))|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.pc += 1
            case 'CPC':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  (self.reg[self.Rd] - self.reg[self.Rr] - (self.SREG & 0b1)) & 0xFF

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if ((not Rd7) & Rr7 )|( Rr7 & R7)|(R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)

                #Z 
                if (self.res == 0) or (((self.SREG>>1)&0b1)) :
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                #V
                V = ((Rd7 & (not Rr7) & (not R7)) | ((not Rd7) & Rr7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if ((not Rd3) & Rr3)|(Rr3 & R3 )|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.pc += 1
            case 'CPI':
                
                self.K = (self.ins&0xF)|(((self.ins>>8)&0xF)<<4)
                self.Rd = (self.ins>>4)&0xF + 16
                self.res = (self.reg[self.Rd]-self.K) & 0xFF


                print("K= ", self.K , "Rd =", self.Rd ,"Res", self.res)


                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                K7= ((self.K&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1


                #C
                if ((not Rd7) & K7 )|( K7 & R7)|(R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)


                #Z 
                if (self.res == 0):
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)


                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)


                #V
                V = ((Rd7 & (not K7) & (not R7)) | ((not Rd7) & K7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)


                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)


                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                K3= ((self.K&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1


                if ((not Rd3) & K3)|(K3 & R3 )|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)


                self.pc+=1
            case 'SBRC':
                b = self.ins&0b111
                self.A = (self.ins>>4)&0b11111
                if (self.reg[self.A]>>b)&1 == 0:
                    next_ins = ins_to_str(self.flash[self.pc])
                    if(next_ins == 'CALL' or next_ins == 'JMP' or next_ins == 'STS' or next_ins == 'LDS'):
                        self.pc += 3 ##skip 2 word instruction
                    else:
                        self.pc += 2## skip 1 word instruction 
                else:
                    self.pc += 1
            case 'SBRS':
                b = self.ins&0b111
                self.A = (self.ins>>4)&0b11111
                if (self.reg[self.A]>>b)&1 == 1:
                    next_ins = ins_to_str(self.flash[self.pc])
                    if(next_ins == 'CALL' or next_ins == 'JMP' or next_ins == 'STS' or next_ins == 'LDS'):
                        self.pc += 3 ##skip 2 word instruction
                    else:
                        self.pc += 2## skip 1 word instruction 
                else:
                    self.pc += 1
            case 'SBIC':
                b = self.ins&0b111
                A = (self.ins>>3)&0b11111
                ## implement I/O read to test if 0

                self.pc += 1
            case 'SBIS':
                b = self.ins&0b111
                A = (self.ins>>3)&0b11111
                ## implement I/O read to test if 1

                self.pc += 1
            case 'BRBS':
                self.K =  (self.ins>>3)&0b1111111 
                S =  self.ins&0b111

                if (self.K & 0x40):
                    self.K = self.K - 128
                
                if(self.SREG>>S)&1 == 1:
                    self.pc +=  self.K +1
                else:
                    self.pc += 1 
            case 'BRBC':
                self.K =  (self.ins>>3)&0b1111111 
                S =  self.ins&0b111

                if (self.K & 0x40):
                    self.K = self.K - 128

                if(self.SREG>>S)&1 == 0:
                    self.pc += + self.K + 1
                else:
                    self.pc += 1 
            case 'SBI': ## implement write in io 
                b = (self.ins & 0b111)
                self.A = ((self.ins>>3)&0x1F)

                #check if the address is valid
                if(self.A >= 0x00 ) and (self.A <= 31):
                    print(self.A)


                
                self.pc += 1
            case 'CBI': ## implement write in io 


                self.pc += 1

            case 'LSL': 
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res = (self.reg[self.Rd] + self.reg[self.Rr]) &0xFF

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if (Rd7 & Rr7 )|( Rr7 & (not R7))|((not R7) & Rd7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & Rr7 & (not R7)) | ((not Rd7) & (not Rr7) & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if (Rd3 & Rr3)|(Rr3 & (not R3))|((not R3) & Rd3):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                
                self.reg[self.Rd] =  self.res

                self.pc += 1
            case 'LSR':

                self.Rd =  (self.ins>>4)&0x1F
                
                #C 
                C = self.reg[self.Rd] & 0b1

                if C == 1:
                    self.SREG |= (1 << 0)
                else:
                    self.SREG &= ~(1 << 0)

                self.res = (self.reg[self.Rd]>>1)&0xFF
                
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.SREG &= ~(1<<2) # N is set to 0

                #V
                V = ((self.SREG&0b1)^0)
                if V == 1 :
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                
                #S
                if V == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)


                self.reg[self.Rd] = self.res
                self.pc += 1
            case 'ROL':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  (self.reg[self.Rd] + self.reg[self.Rr] + (self.SREG & 0b1)) &0xFF

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if (Rd7 & Rr7 )|( Rr7 & (not R7))|((not R7) & Rd7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & Rr7 & (not R7)) | ((not Rd7) & (not Rr7) & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if (Rd3 & Rr3)|(Rr3 & (not R3))|((not R3) & Rd3):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res

                self.pc += 1
            case 'ROR':
                self.Rd =  (self.ins>>4)&0x1F

                #C 
                C = self.reg[self.Rd] & 0b1

                self.res = (self.reg[self.Rd]>>1 & 0xFF) | (self.SREG&0b1)<<7

                if C == 1:
                    self.SREG |= (1 << 0)
                else:
                    self.SREG &= ~(1 << 0)

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = R7^C

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] = self.res & 0xFF

                self.pc += 1
            case 'ASR':
                self.Rd =  (self.ins>>4)&0x1F

                #C 
                C = self.reg[self.Rd] & 0b1
                if C == 1:
                    self.SREG |= (1 << 0)
                else:
                    self.SREG &= ~(1 << 0)

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                
                self.res = (self.reg[self.Rd]>>1 & 0xFF) | (Rd7)<<7

                R7 = ((self.res&0xFF)>>7)&0b1
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = R7^C

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] = self.res & 0xFF

                self.pc += 1
            case 'SWAP':
                self.Rd = (self.ins>>4)&0x1F
                self.reg[self.Rd]= ((self.reg[self.Rd]&0xF)<<4) | ((self.reg[self.Rd]&0xF0)>>4)

                self.pc += 1
            case 'BSET':
                s = (self.ins>>4)&0b111
                self.SREG |=(1<<s) 

                self.pc += 1
            case 'BCLR':
                s = (self.ins>>4)&0b111
                self.SREG &= ~(1<<s) 

                self.pc += 1
            case 'BST':
                b = self.ins&0b111
                self.Rd = (self.ins>>4)&0x1F
                bit = (self.reg[self.Rd]>>b)&1

                if bit:
                    self.SREG |= (1<<6)
                else:
                    self.SREG &= ~(1<<6)
 
                self.pc += 1
            case 'BLD':
                b = self.ins&0b111
                self.Rd = (self.ins>>4)&0x1F
                self.reg[self.Rd] &= ~(0b1<<b)
                self.reg[self.Rd] |= ((self.SREG>>6)&1)<<b

                self.pc += 1


            case 'MOV':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[self.Rd] =  self.reg[self.Rr]

                self.pc += 1
            case 'MOVW':
                self.Rr = (self.ins & 0xF) << 1
                self.Rd = ((self.ins>>4) & 0xF) << 1

                self.reg[self.Rd+1] = self.reg[self.Rr+1]
                self.reg[self.Rd] =  self.reg[self.Rr]

                self.pc += 1
            case 'LDI':
            
                self.Rd = ((self.ins>>4)&0xF)+16
                self.K = (self.ins&0xF)|((((self.ins)>>8)&0xF)<<4)

                self.reg[self.Rd] = self.K 
                self.pc += 1
            case 'LDX': #X
                self.Rd = (self.ins>>4)&0x1F
                self.A  = (self.reg[27]<<8)|(self.reg[26]&0xFF) #X address

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1
                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 

                    self.pc += 1
                    self.databyteNb = 0
            case 'LDX+': #X+
                self.Rd = (self.ins>>4)&0x1F
                self.A = self.reg[26]|(self.reg[27]<<8)

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1

                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 
                    self.A += 1 ##incrementing X
                    self.reg[26] = self.A&0xFF 
                    self.reg[27] = (self.A>>8)&0xFF

                    self.mem.instype.prepare(0)

                    self.pc += 1
                    self.databyteNb = 0
            case 'LD-X': #-X
                self.Rd = (self.ins>>4)&0x1F
                self.A = (self.reg[27]<<8)|(self.reg[26]&0xFF)

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.A -= 1 ##decrementing X
                    self.reg[26] = self.A&0xFF 
                    self.reg[27] = (self.A>>8)&0xFF

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1

                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 

                    self.pc += 1
                    self.databyteNb = 0
            case 'LDY': #Y
                self.Rd = (self.ins>>4)&0b11111
                self.A = self.reg[28]|(self.reg[29]<<8)

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1
                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.pc += 1
                    self.databyteNb = 0
            case 'LDY+': #Y+
                self.Rd = (self.ins>>4)&0b11111
                self.A = (self.reg[28]&0xFF)|(self.reg[29]<<8)

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1

                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 

                    self.mem.instype.prepare(0)

                    self.A = (self.A + 1) & 0xFFFF ##incrementing Y
                    self.reg[28] = self.A&0xFF 
                    self.reg[29] = (self.A>>8)&0xFF

                    self.pc += 1
                    self.databyteNb = 0
            case 'LD-Y': #-Y
                self.Rd = (self.ins>>4)&0x1F
                self.A = (self.reg[29]<<8)|self.reg[28]

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.A -= 1 ##decrementing Y
                    self.reg[28] = self.A&0xFF 
                    self.reg[29] = (self.A>>8)&0xFF

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1
                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 

                    self.pc += 1
                    self.databyteNb = 0
            case 'LDDY':#Y+q
                self.Rd = (self.ins>>4)&0x1F
                self.q = (self.ins&0b111)|(((self.ins>>10)&0b11)<<3)|(((self.ins>>13)&0b1)<<5)
                self.A = (((self.reg[28]&0xFF)|((self.reg[29]&0xFF)<<8))+self.q) & 0xFFFF # Y address
                
                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1

                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 

                    self.pc += 1
                    self.databyteNb = 0
            case 'LDZ':#Z
                self.Rd = (self.ins>>4)&0x1F
                self.A = (self.reg[30]&0xFF)|(self.reg[31]<<8) # A but it is a Z memory address

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1
                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.pc += 1
                    self.databyteNb = 0
            case 'LDZ+':#Z+
                self.Rd = (self.ins>>4)&0x1F
                self.A = self.reg[30]|(self.reg[31]<<8)

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1
                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 
                    self.A += 1 ##incrementing Y
                    self.reg[30] = self.A&0xFF 
                    self.reg[31] = (self.A>>8)&0xFF

                    self.mem.instype.prepare(0)

                    self.pc += 1
                    self.databyteNb = 0
            case 'LD-Z':#–Z
                self.Rd = (self.ins>>4)&0x1F
                self.A = (self.reg[30]&0xFF)|(self.reg[31]<<8)

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.A -= 1 ##decrementing Y
                    self.reg[30] = self.A&0xFF 
                    self.reg[31] = (self.A>>8)&0xFF

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1
                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0) 

                    self.pc += 1
                    self.databyteNb = 0
            case 'LDDZ':#Z+q  verify this implementation
                self.Rd = (self.ins>>4)&0b11111
                self.q = (self.ins&0b111)|(((self.ins>>10)&0b11)<<3)|(((self.ins>>13)&0b1)<<5)
                self.A = ((self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8))+self.q # Y address
                

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1
                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0)

                    self.pc += 1
                    self.databyteNb = 0
            case 'LDS':#k  Load direct from sram
                self.Rd = (self.ins>>4)&0x1F
                self.A = self.flash[self.pc+1]


                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1

                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.instype.prepare(0)

                    self.pc += 1
                    self.databyteNb = 0
            case 'STX':#X
                self.Rr = (self.ins>>4)&0x1F
                self.A = (self.reg[26]&0xFF)|((self.reg[27]&0xFF)<<8) #X adress

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])

                    self.databyteNb = 1
                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'STX+':#X+
                self.Rr = (self.ins>>4)&0x1F
                self.A = self.reg[26]|(self.reg[27]<<8) #X addres 

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])
                    
                    self.databyteNb = 1
                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.A += 1 ##incrementing X
                    self.reg[26] = self.A&0xFF 
                    self.reg[27] = (self.A>>8)&0xFF

                    self.pc += 1 
                    self.databyteNb = 0
            case 'ST-X':#–X
                self.Rr = (self.ins>>4)&0x1F
                self.A = self.reg[26]|(self.reg[27]<<8) #X address


                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.A -= 1 ##decrementing X
                    self.reg[26] = self.A&0xFF 
                    self.reg[27] = (self.A>>8)&0xFF

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])
                    
                    self.databyteNb = 1
                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'STY':#Y
                self.Rr = (self.ins>>4)&0x1F
                self.A = self.reg[28]|(self.reg[29]<<8) #Y address


                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])
                    
                    self.databyteNb = 1
                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'STY+':#Y+
                self.Rr = (self.ins>>4)&0x1F
                self.A = self.reg[28]|(self.reg[29]<<8) #Y address

                if self.mem.resp.get() == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])

                    self.databyteNb = 1
                    
                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.A += 1 ##incrementing Y
                    self.reg[28] = self.A&0xFF 
                    self.reg[29] = (self.A>>8)&0xFF

                    self.pc += 1 
                    self.databyteNb = 0
            case 'ST-Y':#–Y

                self.Rr = (self.ins>>4)&0x1F
                self.A = self.reg[28]|(self.reg[29]<<8) #Y address

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.A -= 1 ##decrementing Y
                    self.reg[28] = self.A&0xFF 
                    self.reg[29] = (self.A>>8)&0xFF

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])
                    
                    self.databyteNb = 1

                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'STDY':#Y+q or STY
                self.Rd = (self.ins>>4)&0x1F
                self.q = (self.ins&0b111)|(((self.ins>>10)&0b11)<<3)|(((self.ins>>13)&0b1)<<5)
                self.A = ((self.reg[28]&0xFF)|(self.reg[29]<<8))+self.q # Y address
                
                
                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])

                    self.mem.instype.prepare(1)

                    self.databyteNb = 1

                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'STZ':#Z
                self.Rr = (self.ins>>4)&0x1F
                self.A = self.reg[30]|(self.reg[31]<<8) # Z

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.instype.prepare(1)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])

                    self.databyteNb = 1
                    
                else:

                    self.mem.instype.prepare(0)

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'STZ+':#Z+
                self.Rr = (self.ins>>4)&0x1F
                self.A = self.reg[30]|(self.reg[31]<<8)

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])

                    self.mem.instype.prepare(1)

                    self.databyteNb = 1
                    
                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.A += 1 ##incrementing Z
                    self.reg[30] = self.A&0xFF 
                    self.reg[31] = (self.A>>8)&0xFF

                    self.mem.instype.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'ST-Z':#–Z
                self.Rr = (self.ins>>4)&0b11111
                Z = self.reg[30]&0xFF|(self.reg[31]<<8) # Z address

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.A -= 1 ##decrementing Z
                    self.reg[30] = self.A&0xFF 
                    self.reg[31] = (self.A>>8)&0xFF

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])

                    self.mem.instype.prepare(1)

                    self.databyteNb = 1

                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'STDZ':#Z+q or STZ
                self.Rr = (self.ins>>4)&0x1F
                self.q = (self.ins&0b111) | (((self.ins>>10)&0b11)<<3) | (((self.ins>>13)&0b11)<<3)
                self.A = self.reg[30]|(self.reg[31]<<8) #named A but it is a Z address

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.address.prepare(self.A+self.q)
                    self.mem.write_data.prepare(self.reg[self.Rd])

                    self.mem.instype.prepare(1)

                    self.databyteNb = 1

                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0
            case 'STS':#k
                self.Rr = (self.ins>>4)&0x1F
                self.A =  self.flash[self.pc+1]

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rd])
                    self.mem.instype.prepare(1)
                    
                    self.databyteNb = 1

                else:

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.mem.instype.prepare(0)

                    self.pc += 2
                    self.databyteNb = 0
            case 'LPM': #R0 implied

                self.A = (self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8)

                if(self.A&0b1 == 1 ):##high byte
                    self.reg[1] = (self.flash[(self.A>>1)] & 0xFF00)>>8
                else: ## low byte 
                    self.reg[0] = (self.flash[(self.A>>1)]&0xFF)

                self.pc += 1 
            case 'LPMZ': #Z

                self.Rd = ((self.ins>>4)&0x1F)
                self.A = (self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8)


                if(self.A&0b1 == 1 ):##high byte
                    self.reg[self.Rd] = (self.flash[(self.A>>1)] & 0xFF00)>>8
                else: ## low byte 
                    self.reg[self.Rd] = (self.flash[(self.A>>1)]&0xFF)


                self.pc += 1
            case 'LPMZ+': #Z+

                self.Rd = ((self.ins>>4)&0x1F) 
                self.A = (self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8)

                original_address = self.A

                if(self.A&0b1 == 1 ):##high byte
                    self.reg[self.Rd+1] = (self.flash[(self.A>>1)] & 0xFF00)>>8
                else: ## low byte 
                    self.reg[self.Rd] = (self.flash[(self.A>>1)]&0xFF)

                original_address += 1 ##decrementing Z
                self.reg[30] = original_address&0xFF 
                self.reg[31] = (original_address>>8)&0xFF

                self.pc+=1
            case 'SPM':
                # must use SPMCSR
                SELFPRGEN = self.SPMCSR & 0b1
                PGERS = (self.SPMCSR >> 1) & 0b1
                PGWRT = (self.SPMCSR >> 2) & 0b1
                BLBSET = (self.SPMCSR >> 3) & 0b1
                RWWSRE = (self.SPMCSR >> 4) & 0b1
                RES = (self.SPMCSR >> 5) & 0b1
                SPMIE = (self.SPMCSR >> 7) & 0b1

                self.Z = (self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)

                word_addr = self.Z >> 1

                page_offset = word_addr % self.PAGE_SIZE_WORDS
                page_base_addr = word_addr - page_offset

                if SELFPRGEN == 1: # SPM operation is enabled

                    # --- 1. PAGE ERASE ---
                    if (PGERS == 1) and (PGWRT == 0): 
                        # Wipe the entire page in actual flash memory
                        for i in range(self.PAGE_SIZE_WORDS):
                            if (page_base_addr + i) < len(self.flash):
                                self.flash[page_base_addr + i] = 0xFFFF
                        
                    # --- 2. PAGE WRITE ---
                    elif (PGERS == 0) and (PGWRT == 1): 
                        # Commit the temporary buffer to the flash memory page
                        for i in range(self.PAGE_SIZE_WORDS):
                            if (page_base_addr + i) < len(self.flash):
                                # Flash can only change bits from 1 to 0. 
                                # A bitwise AND correctly simulates writing over existing data.
                                self.flash[page_base_addr + i] &= self.temp_page_buffer[i]
                        
                        # Hardware auto-erases the temporary buffer after a Page Write
                        self.temp_page_buffer = [0xFFFF] * self.PAGE_SIZE_WORDS

                    # --- 3. FILL TEMPORARY BUFFER ---
                    elif (PGERS == 0) and (PGWRT == 0) and (BLBSET == 0):
                        # Load the data word from R1:R0 (R0 is LSB, R1 is MSB)
                        data_word = (self.reg[0] & 0xFF) | ((self.reg[1] & 0xFF) << 8)
                        
                        # Write into the temporary buffer at the specified offset
                        self.temp_page_buffer[page_offset] = data_word

                    # Hardware auto-clears the SPM enable bit after execution
                    self.SPMCSR &= ~0b1

                    # Trigger interrupt if enabled
                    if SPMIE == 1:
                        print("SPM Interrupt Triggered")

                self.pc += 1

            case 'IN':
                self.Rd = (self.ins>>4)&0b11111
                self.A = ((self.ins)&0xF) | ((((self.ins)>>9)&0b11)<<4) #don't know what is the port

                #verify if the address is valid
                #Minimum Address: 0x00
                #Maximum Address: 0x3F
                if (self.A >= 0x00) and (self.A <=0x3F):
                    #internal addresses
                    if (self.A == self.SREG_addr_IO):
                        self.reg[self.Rd] = self.SREG #status register
                        print("Register:SREG")
                        self.pc += 1
                    elif (self.A == self.MCUSR_addr_IO):
                        self.reg[self.Rd] = self.MCUSR
                        print("Register:MCUSR = {val}".format(val = self.MCUSR))  
                        self.pc += 1 
        
                    if self.databyteNb == 0 :
                        self.mem.write.prepare(0)
                        self.mem.read.prepare(1) 

                        self.mem.address.prepare(self.A)
                        self.databyteNb = 1
                    elif self.mem.resp.get() == 1:
                        self.reg[self.Rd] = self.mem.read_data.get()

                        self.pc += 1
                        self.databyteNb = 0
                else:
                    # increment by one if the address is invalid    
                    self.pc+=1
            case 'OUT':
                self.Rr = (self.ins>>4)&0b11111
                self.A = ((self.ins)&0xF) | ((((self.ins)>>9)&0b11)<<4) #don't know what is the port

                #verify if the address is valid
                #Minimum Address: 0x00
                #Maximum Address: 0x3F
                if (self.A >= 0x00) and (self.A <=0x3F):
                    #internal addresses
                    if (self.A == self.SREG_addr_IO):
                        self.SREG = self.reg[self.Rr] #status register
                        print("Register:SREG")
                        self.pc += 1 
                    elif (self.A == self.MCUSR_addr_IO):
                        self.MCUSR = self.reg[self.Rr]
                        print("Register:MCUSR = {val}".format(val = self.MCUSR)) 
                        self.pc += 1 

                    if self.databyteNb == 0 :
                        self.mem.write.prepare(0)
                        self.mem.read.prepare(1) 

                        self.mem.instype.prepare(0)

                        self.mem.address.prepare(self.A)
                        self.databyteNb = 1
                    elif self.mem.resp.get() == 1:
                        self.reg[self.Rd] = self.mem.read_data.get()

                        self.mem.instype.prepare(0)

                        self.pc += 1
                        self.databyteNb = 0
                else:
                    # increment by one if the address is invalid
                    self.pc+=1
            case 'PUSH':
                self.Rr = (self.ins>>4)&0x1F
                self.A = (self.SPH<<8) | (self.SPL&0xFF)

                if self.databyteNb == 0:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)

                    self.mem.address.prepare(self.A)
                    self.mem.write_data.prepare(self.reg[self.Rr])

                    self.databyteNb = 1

                else:
                    self.A -= 1 ##decrementing SP
                    self.SPL = self.A&0xFF 
                    self.SPH = (self.A>>8)&0xFF

                    self.mem.write.prepare(0)
                    self.mem.write.prepare(0)

                    self.pc += 1 
                    self.databyteNb = 0            
            case 'POP':
                self.Rd = (self.ins>>4)&0x1F
                self.A = ((self.SPH&0xFF)<<8) | (self.SPL&0xFF)

                if self.databyteNb == 0 :
                    self.mem.write.prepare(0)
                    self.mem.read.prepare(1) 

                    self.A = (self.A + 1 ) & 0xFFFF ##incrementing SP

                    self.SPL = self.A&0xFF 
                    self.SPH = (self.A>>8)&0xFF

                    self.mem.address.prepare(self.A)
                    self.databyteNb = 1

                elif self.mem.resp.get() == 1:
                    self.reg[self.Rd] = self.mem.read_data.get()

                    self.mem.write.prepare(0)
                    self.mem.read.prepare(0)

                    self.pc += 1
                    self.databyteNb = 0
            case 'NOP':
                self.pc += 1 
            case 'SLEEP':
                ##activation of SLEEP MODE
                self.pc += 1
            case 'WDR' :
                ## Watchdog Reset
                self.pc +=1
            case 'BREAK' : 
                ## Sould enter debug mode
                self.pc += 1
            case 'invalid': #basicaly a nop
                self.pc += 1