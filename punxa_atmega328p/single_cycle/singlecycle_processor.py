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

SPL_REG =   0x5D 
SPH_REG =   0x5E
SREG_REG =  0x5F


class SingleCycleATmega328P(py4hw.Logic):
    def __init__(self,parent, name:str , ins_mem:MemoryInterface, memory:MemoryInterface, reset_address):
        #INT0,INT1,PCINT0,PCINT1,PCINT2,WDT,TIMER2_COMPA,TIMER2_COMPB,TIMER2_OVF,TIMER1_CAPT,TIMER1_COMPA,TIMER1_COMPB,TIMER1_OVF,TIMER0_COMPA,TIMER0_COMPB,TIMER0_OVF,SPI_STC,USART_RX,USART_UDRE,USART_TX,ADC,EE_READY,ANALOG_COMP,TWI,SPM_READY):
        super().__init__(parent,name)

        assert(ins_mem.read_data.getWidth() == 16)
        assert(memory.read_data.getWidth() == 8)
        
        self.ins_mem = self.addInterfaceSource('ins', ins_mem)
        self.mem = self.addInterfaceSource('data', memory)
        
        self.pc = reset_address # Reset address is a property of the processor. In Atmega328p it is stored in non-volatile memory and can be configured by JTAG
        
        #  0x3F00 ##bootloarder
        
        
        #self.reg = [0]*32  # REGS are stored in memory
        # self.ram = [0]*2048
        
        
        #self.stack_pointer  = 0x08FF ## value sould be known by using a register, I need to verify that it doesent go in to the negatives  
        self.next_cycle = False #varible to indicate that data is ready to read from ram/memeory
        self.ins = 0
        self.opp = 'NOP'
        self.FirstBoot = True #is this actuatly odable ?
        self.BOOTRST = 1
        self.databyteNb = 0
        
        # Registers
        self.SP = 0
        
        # Status flags
        self.Z = 0
        self.N = 0
        self.C = 0
        self.V = 0
        self.S = 0
        self.H = 0
        self.T = 0
        self.I = 0
        
        self.MCUCR = 0
        self.MCUCR_addr_IO = 0x35
        self.MCUCR_addr_LS = 0x55

        #Stack Pointer
        


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



        self.gotToGoFast = False

        self.insFiniteStateMachine = 'START'

        self.PAGE_SIZE_WORDS = 64
        
        self.temp_page_buffer = [0xFFFF] * self.PAGE_SIZE_WORDS     
        
        self.csr = {}
        self.csr[CSR_INSTRET] = 0
        self.csr[CSR_CYCLE] = 0
        
        self.skip = False  # Skip flag to support skip instructions
        
        self.co = self.run()

    
    def clock(self):
        next(self.co)
        
        self.csr[CSR_CYCLE] += 1
        
    def run(self):
        yield
        
        while (True):
            yield from self.fetchIns()
            # if (ins_to_str(self.ins) not in MEMORY_INSTRUCTIONS) and (self.gotToGoFast == 1):
            #     self.mem.read.prepare(0)
            #     self.mem.write.prepare(0)
    
            yield from self.execute()
        
            self.csr[CSR_INSTRET] += 1
            yield


    def getCSR(self, csr):
        # only assuming insret is implemented
        return self.csr[csr] 
        
    def updateFlags(self, alu_result, is16=False):
        if (is16):
            self.Z = 1 if (alu_result & 0xFFFF) == 0 else 0
            self.N = 1 if (alu_result & 0x8000) else 0
        else:
            self.Z = 1 if (alu_result & 0xFF) == 0 else 0
            self.N = 1 if (alu_result & 0x80) else 0
        
        self.S = self.N ^ self.V
        
    def getSREG(self):
        '''
        Returns the SREG register and the string with the name of the flags
        '''
        SREG = (self.I << 7) | (self.T<<6) | (self.H<<5) | (self.S<<4) | (self.V<<3) | (self.N<<2) | (self.Z<<1) | self.C 
        sSREG = 'ITHSVNZC'[::-1]
        return SREG, sSREG
    
    def setSREGField(self, f, v):
        match (f):
            case 0: self.C = v
            case 1: self.Z = v
            case 2: self.N = v
            case 3: self.V = v
            case 4: self.S = v
            case 5: self.H = v
            case 6: self.T = v
            case 7: self.I = v
    
    def writeByte(self, add, value):
        self.mem.write.prepare(1)
        self.mem.read.prepare(0) 
        self.mem.address.prepare(add)
        self.mem.write_data.prepare(value)
        yield
        self.mem.write.prepare(0) 
        
        while (self.mem.resp.get() == 0):
            # wait until response
            yield
            
        yield
    
    def readByte(self, add):
        self.mem.write.prepare(0)
        self.mem.read.prepare(1) 
        self.mem.address.prepare(add)
        yield
        self.mem.read.prepare(0) 
        
        while (self.mem.resp.get() == 0):
            # wait until response
            yield
            
        return self.mem.read_data.get()


    def readInsWord(self):
        self.ins_mem.address.prepare(self.pc)
        self.ins_mem.read.prepare(1)
        self.ins_mem.write.prepare(0)
        yield
        self.ins_mem.read.prepare(0)
        self.ins_mem.write.prepare(0)
        yield
        self.pc += 1
        return self.ins_mem.read_data.get()
        
        
        
    def fetchIns(self):
        print(f'{self.pc:04X} - ', end='')
        self.ins = yield from self.readInsWord()
        
        #print(f'FETCH INS: {self.pc:04X} -  {self.ins:04X}')
        

    def getFlagString(self):
        sZ = 'Z' if (self.Z) else ' '
        sC = 'C' if (self.C) else ' '
        sN = 'N' if (self.N) else ' '
        sV = 'V' if (self.V) else ' '
        sH = 'H' if (self.H) else ' '
        sS = 'S' if (self.S) else ' '
        
        return f'{sZ}{sC}{sN}{sV}{sH}{sS}'
        

    def execute(self):
        self.opp =  ins_to_str(self.ins)
        
        b3 = self.ins & 0b111
        s3 = (self.ins>>4) & 0b111
        
        Rd3 = ((self.ins>>4) & 0x7)
        Rd4 = ((self.ins>>4) & 0xF)
        Rd5 = ((self.ins>>4) & 0x1F)
        RdW = 24 + (((self.ins >> 4) & 0b11) * 2)

        Rr3 = (self.ins & 0x7)
        Rr5 = (((self.ins>>9) & 1) << 4) | (self.ins & 0xF)
        
        K6 = (((self.ins>>6) & 0b11) << 4) | (self.ins & 0xF)
        K7 = (self.ins>>3) & 0b1111111 
        K8 = (((self.ins>>8) & 0xF) << 4) | (self.ins & 0xF)
        
        sK7 = py4hw.IntegerHelper.c2_to_signed(K7, 7)
        
        A5 = (self.ins >> 3) & 0x1F
        A6 = ((((self.ins)>>9) & 0b11)<<4) | ((self.ins) & 0xF)  
        
        #print(f'{self.ins:04X}', self.opp)
        
        # We fetch address for 2 word instructions here to easily handle
        # skip instructions correctly
        if (self.opp in TWO_CYCLE_INSRUCTIONS):
            add = yield from self.readInsWord()

        if (self.skip):
            # Skip next instruction
            self.skip = False
            return
        
        match self.opp: 
            case 'ADD':
                # ADD Rd, Rr -> 0000 11rd dddd rrrr
                Rr, Rd = Rr5, Rd5
                
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                
                res = vRd + vRr
                
                self.C = 1 if (res > 0xFF) else 0                
                self.H =  1 if (((vRd & 0x0F) + (vRr & 0x0F)) > 0x0F) else 0
                rd_sign = (vRd >> 7) & 1      # Bit 7 of Rd
                rr_sign = (vRr >> 7) & 1      # Bit 7 of Rr
                res_sign = (res >> 7) & 1     # Bit 7 of result
                self.V = 1 if ((rd_sign == rr_sign) and (rd_sign != res_sign)) else 0
                self.updateFlags(res)
                
                yield from self.writeByte(Rd, res)
                
                print(f'ADD R{Rd}, R{Rr}\t\tR{Rd}={res:02X}\t{self.getFlagString()}')
                
                
            case 'ADC': # there may be a problem with this but I don't know what is the problem
                # 
                Rr, Rd = Rr5, Rd5
                
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                
                res =  vRd + vRr + self.C
                
                self.C = 1 if res > 0xFF else 0
                self.H = 1 if (((vRd & 0x0F) + (vRr & 0x0F) + self.C) > 0x0F) else 0
                rd_sign = (vRd >> 7) & 1
                rr_sign = (vRr >> 7) & 1
                res_sign = ((res & 0xFF) >> 7) & 1
                self.V = 1 if ((rd_sign == rr_sign) and (rd_sign != res_sign)) else 0
                self.updateFlags(res)
                yield from self.writeByte(Rd, res & 0xFF)
                
                print(f'ADD R{Rd}, R{Rr}\t\tR{Rd}={res:02X}\t{self.getFlagString()}')
                
                
            case 'ADIW':
                # ADIW Rd, K -> 1001 0110 KKdd KKKK
                K = (((self.ins>>6)&0b11)<<4)|(self.ins & 0xF)
                Rd = RdW 
                vRdh = yield from self.readByte(Rd+1)
                vRdl = yield from self.readByte(Rd)
                res =  (vRdh <<8 | vRdl )  +  K
                resh = (res >> 8) & 0xFF
                resl = res & 0xFF
                
                self.C = 1 if (res > 0xFFFF) else 0
                
                rd_sign = (vRdh >> 7) & 1
                res_sign = (res >> 15) & 1
                self.V = 1 if (rd_sign == 0) and (res_sign == 1) else 0
                self.updateFlags(res, is16=True)      
                yield from self.writeByte(Rd+1, resh)
                yield from self.writeByte(Rd, resl)
                print(f'ADIW R{Rd}, {K}\t\tR{Rd+1}={resh:02X} R{Rd}={resl:02X} {self.getFlagString()}')
                
            case 'AND':
                # AND Rd, Rr -> 0010 00rd dddd rrrr
                Rr, Rd = Rr5, Rd5
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                
                res =  vRd & vRr

                self.V = 0
                self.updateFlags(res)
                
                yield from self.writeByte(Rd, res)
                
                print(f'AND R{Rd}, R{Rr}\t\tR{Rd}={res:02X} {self.getFlagString()}')
                
                
            case 'ANDI':
                # ANDI Rd, K -> 0111 KKKK dddd KKKK
                # AND immediate
                K, Rd = K8, (Rd4+16)
                vRd = yield from self.readByte(Rd)
                res =  vRd & K 

                self.V = 0
                self.updateFlags(res)

                yield from self.writeByte(Rd, res)
                print(f'ANDI R{Rd}, {K:02X}\t\tR{Rd}={res:02X} {self.getFlagString()}')
                
            case 'ASR':
                # ASR Rd -> 1001 010d dddd 0101
                # Arithmetic Shift Right
                Rd = Rd5
                vRd = yield from self.readByte(Rd)
                bit_shifted_out = vRd & 0x01
                
                sign = ((vRd >> 7) & 1) << 7
                res = (vRd >> 1) | sign
                
                self.C = bit_shifted_out
                self.Z = 1 if res == 0 else 0
                self.V = self.N ^ self.C
                self.updateFlags(res)
                # self.H not affected                 
                yield from self.writeByte(Rd, res)                
                print(f'ASR R{Rd}\t\tR{Rd}={res:02X}')
                
            case 'BRBC':
                # BRBC s, k -> 1111 01kk kkkk ksss
                K, S = sK7, b3
                SREG, sSREG = self.getSREG()
                v = ((SREG >> S) & 1)
                cond = (v==0)
                if cond:
                    self.pc += K 
                print(f'BRBC {S}, {K:02X}\t\t({sSREG[S]} == 0)={cond}')
                
            case 'BRBS':
                # BRBS s, k -> 1111 00kk kkkk ksss
                K, S =  sK7,  b3
                SREG, sSREG = self.getSREG()                
                v = ((SREG >> S) & 1)
                cond = (v == 1)
                if (cond):
                    self.pc += K 
                print(f'BRBS {S}, {K:02X}\t\t({sSREG[S]} == 1)={cond}')
                
            case 'CBI': 
                # CBI A, b -> 1001 1000 AAAA Abbb
                # Clears bit in I/O register
                A, b = A5, b3
                v = yield from self.readByte(A + 0x20)
                v = (v & ~(1<<b))
                yield from self.writeByte(A + 0x20, v)
                print(f'CBI {A:02X}, {b}\t\t[{A+0x20:02X}]={v:02X}')                
                
            case 'OR':
                # OR Rd, Rr -> 0010 10rd dddd rrrr
                Rr, Rd = Rr5, Rd5
                
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                
                res = (vRd | vRr) & 0xFF  # Ensure it stays within 8-bit bounds
                
                # Update Flags according to AVR specifications for OR
                self.V = 0                # V is always cleared (0) for OR
                self.updateFlags(res)
                
                yield from self.writeByte(Rd, res)
                
                print(f'OR R{Rd}, R{Rr}\t\tR{Rd}={res:02X}\t{self.getFlagString()}')
            case 'ORI':
                # ORI Rd, K -> 0110 KKKK dddd KKKK
                # OR immediate
                K, Rd = K8, (Rd4+16)
                vRd = yield from self.readByte(Rd)
                res =  vRd | K 
                self.V = 0
                self.updateFlags(res)
                yield from self.writeByte(Rd, res)
                print(f'OR R{Rd}, {K:02X}\t\tR{Rd}={res:02X} {self.getFlagString()}')
                
            case 'EOR':
                Rr, Rd = Rr5, Rd5
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                
                res =  vRd ^ vRr

                self.Z = 1 if (res == 0) else 0
                self.N = (res >> 7) 
                self.C = 0
                self.V = 0
                self.S = self.N
                self.H = 0
                
                yield from self.writeByte(Rd, res)
                
                print(f'EOR R{Rd}, R{Rr}\t\tR{Rd} = {res:02X}\t{self.getFlagString()}')
                
            case 'COM':
                # COM Rd -> 1001 010d dddd 0000
                # One's complement
                Rd = Rd5
                vRd = yield from self.readByte(Rd)
                res = 0xFF - vRd
                self.C = 1
                self.H = 1
                self.V = 0
                self.updateFlags(res)
                yield from self.writeByte(Rd, res)
                print(f'COM R{Rd}\t\tR{Rd}={res:02X} {self.getFlagString()}')
                
            case 'NEG':
                # NEG Rd -> 1001 010d dddd 0001
                Rd = Rd5
                vRd = yield from self.readByte(Rd)
                res = (-vRd) & 0xFF

                self.C = 1 if res != 0 else 0
                self.H = 1 if ((res & 0x08) != 0) else 0
                self.V = 1 if (vRd == 0x80) else 0
                self.updateFlags(res)
                
                yield from self.writeByte(Rd, res )
                print('NEG R{Rd}\t\tR{Rd}={res&0xFF:02X} {self.getFlagString()}')
                
            case 'SBR':
                raise Exception('SBR is a psuedo instruction !!!')
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
                raise Exception('CBR not reviewed')
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] & self.K 

                self.testZ(self.res)
                self.testN(self.res)
#                self.SREG &= ~(1<<V) # flag V to 0
                self.testS()     

                self.reg[self.Rd] =  self.res 
                self.pc += 1
                
            case 'FMUL':
                # FMUL Rd, Rr -> 0000 0011 0ddd 1rrr
                Rr , Rd = Rr3 + 16, Rd3 + 16
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                res =  (vRd * vRr) 
                self.C = (res >> 15) & 1
                res = res << 1
                self.updateFlags(res, is16=True)
                yield from self.writeByte(1, (res >> 8) & 0xFF)
                yield from self.writeByte(0, res & 0xFF)
                
            case 'FMULS': 
                # FMULS Rd, Rr -> 0000 0011 1ddd 0rrr
                Rr , Rd = Rr3 + 16, Rd3 + 16
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                vRd = py4hw.IntegerHelper.c2_to_signed(vRd, 8)
                vRr = py4hw.IntegerHelper.c2_to_signed(vRr, 8)
                res =  vRd * vRr
                self.C = (res >> 15) & 1
                res = res << 1
                self.updateFlags(res, is16=True)
                yield from self.writeByte(1, (res >> 8) & 0xFF)
                yield from self.writeByte(0, res & 0xFF)
                
            case 'FMULSU':
                # FMULSU Rd, Rr -> 0000 0011 1ddd 1rrr
                Rr , Rd = Rr3 + 16, Rd3 + 16
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                vRd = py4hw.IntegerHelper.c2_to_signed(vRd, 8)
                res =  vRd * vRr
                self.C = (res >> 15) & 1
                res = res << 1
                self.updateFlags(res, is16=True)
                yield from self.writeByte(1, (res >> 8) & 0xFF)
                yield from self.writeByte(0, res & 0xFF)
                
            case 'ICALL':
                # ICALL-> 1001 0101 0001 1001
                # Indirect call to Z
                zh = yield from self.readByte(31)
                zl = yield from self.readByte(30)
                add = (zh << 8) | zl
                ra = self.pc
                self.SP -= 1
                yield from self.writeByte(self.SP, ra >> 8)
                self.SP -= 1
                yield from self.writeByte(self.SP, ra & 0xFF)
                self.pc = add
                print(f'ICALL \t\t\t[{self.SP+1:04X}]={ra>>8:02X} [{self.SP:04X}]={ra & 0xFF}')
                
            case 'IJMP':
                # IJMP -> 1001 0100 0001 1001
                # Indirect jmp to Z
                zh = yield from self.readByte(31)
                zl = yield from self.readByte(30)
                add = (zh << 8) | zl
                self.pc = add
                print(f'IJMP')
                
            case 'INC':
                # INC Rd --> 1001 010d dddd 0011.
                Rd = Rd5
                vRd = yield from self.readByte(Rd)
                
                res = vRd + 1
                
                self.V = 1 if vRd == 0x7F else 0
                self.updateFlags(res)
                
                yield from self.writeByte(Rd, res & 0xFF)

                print(f'INC\t\t\t\t{self.getFlagString()}')
                
            case 'DEC':
                # DEC Rd --> 1001 010d dddd 1010.
                Rd = Rd5
                vRd = yield from self.readByte(Rd)
                
                res = vRd - 1
                self.V = 1 if (vRd == 0x80) else 0 
                self.updateFlags(res)
                
                yield from self.writeByte(Rd, res & 0xFF)

                print(f'INC\t\t\t\t{self.getFlagString()}')
                
            case 'SER':
                raise Exception('SER not reviewed')
                self.Rd = (self.ins>>4)&0b1111 + 16
                self.reg[self.Rd] = 0xFF
        

                self.pc +=1 
            case 'MUL':
                Rr, Rd = Rr5, Rd5
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                res =  vRd * vRr
                yield from self.writeByte(1, (res >> 8) & 0xFF)
                yield from self.writeByte(0, res & 0xFF)
                
                self.Z = 1 if (res == 0) else 0
                self.C = 1 if (res & 0x8000) else 0   
                print(f'MUL R{Rd}, R{Rr}\t\tR1:R0={res:04X}\t{self.getFlagString()}')
    

            case 'MULS': 
                # MULS Rd, Rr -> 0000 0010 dddd rrrr
                Rr , Rd = Rr3 + 16, Rd3 + 16
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                vRd = py4hw.IntegerHelper.c2_to_signed(vRd, 8)
                vRr = py4hw.IntegerHelper.c2_to_signed(vRr, 8)
                res =  vRd * vRr
                self.C = (res >> 15) & 1
                self.updateFlags(res, is16=True)
                yield from self.writeByte(1, (res >> 8) & 0xFF)
                yield from self.writeByte(0, res & 0xFF)
                
            case 'MULSU':
                # MULSU Rd, Rr -> 0000 0011 0ddd 0rrr
                Rr , Rd = Rr3 + 16, Rd3 + 16
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                vRd = py4hw.IntegerHelper.c2_to_signed(vRd, 8)
                res =  vRd * vRr
                self.C = (res >> 15) & 1
                self.updateFlags(res, is16=True)
                yield from self.writeByte(1, (res >> 8) & 0xFF)
                yield from self.writeByte(0, res & 0xFF)
                
            
                
            case 'RJMP':
                # RJMP k → 1100 kkkk kkkk kkkk
                off = self.ins & 0xFFF
                soff = py4hw.IntegerHelper.c2_to_signed(off, 12)
                self.pc += soff
                print(f'RJMP {soff}')
                
            
            case 'JMP':
                # add is loaded in the skip logic
                self.pc = add
                print(f'JMP {add:04X}')
                
            case 'RCALL':
                K = py4hw.IntegerHelper.c2_to_signed(self.ins & 0xFFF, 12)
                ra = self.pc
                
                self.SP -= 1
                yield from self.writeByte(self.SP, ra >> 8)
                self.SP -= 1
                yield from self.writeByte(self.SP, ra & 0xFF)
                
                self.pc += K                    
                
                print(f'RCALL {K:03X}\t\t[{self.SP+1:04X}]={ra>>8:02X} [{self.SP:04X}]={ra & 0xFF}')
                    
            
                
            case 'CALL':
                # add is loaded in the skip logic
                ra = self.pc
                self.SP -= 1
                yield from self.writeByte(self.SP, ra >> 8)
                self.SP -= 1
                yield from self.writeByte(self.SP, ra & 0xFF)
                self.pc = add
                print(f'CALL {add:04X}\t\t[{self.SP+1:04X}]={ra>>8:02X} [{self.SP:04X}]={ra & 0xFF}')

                        
            case 'RET':
                retl = yield from self.readByte(self.SP)
                self.SP += 1
                reth = yield from self.readByte(self.SP)
                self.SP += 1
                
                self.pc = (reth << 8) | retl
                print(f'RET\t\t\t\t[{SPH_REG:04X}]={(self.SP>>8):02X} [{SPL_REG:04X}]={(self.SP & 0xFF):02X}')
                
            case 'RETI':
                # RETI -> 1001 0101 0001 1000
                # Return from interrupt
                retl = yield from self.readByte(self.SP)
                self.SP += 1
                reth = yield from self.readByte(self.SP)
                self.SP += 1
                self.pc = (reth << 8) | retl
                self.I = 1
                print(f'RET\t\t\t\t[{SPH_REG:04X}]={(self.SP>>8):02X} [{SPL_REG:04X}]={(self.SP & 0xFF):02X} {self.getFlagString()}')
                

            case 'CPSE':
                # CPSE Rd, Rr -> 0001 00rd dddd rrrr
                Rr, Rd = Rr5, Rd5
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                self.skip = (vRd == vRd)
                print(f'CPSE R{Rd}, R{Rr}\t\tskip={self.skip}')
                
            case 'CP':
                # CP Rd, Rr -> 0001 01rd dddd rrrr
                Rr, Rd = Rr5, Rd5
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                res =  vRd - vRr

                
                self.C = 1 if vRd < vRr else 0
                self.H = 1 if ((vRr & 0x0F) > (vRd & 0x0F)) else 0
                rd_sign = (vRd >> 7) & 1
                rr_sign = (vRr >> 7) & 1
                res_sign = ((res & 0xFF) >> 7) & 1
                self.V = 1 if (rd_sign == 1 and rr_sign == 0 and res_sign == 0) or (rd_sign == 0 and rr_sign == 1 and res_sign == 1) else 0
                self.updateFlags(res)
                
                print(f'CP R{Rr}, R{Rd}\t\t{self.getFlagString()}')
                
            case 'CPC':
                raise Exception('CPC not reviewed')
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
                # CPI Rd, k -> 0011 KKKK dddd KKKK
                # Compare with immediate
                K, Rd = K8, Rd4 + 16
                vRd = yield from self.readByte(Rd)
                
                res = (vRd - K) & 0xFF

                self.C = 1 if (vRd < K) else 0
                self.H =  1 if ((vRd & 0x0F) - (K & 0x0F)) < 0 else 0
                rd_sign = (vRd >> 7) & 1      # Bit 7 of Rd
                rr_sign = (K >> 7) & 1      # Bit 7 of Rr
                res_sign = (res >> 7) & 1     # Bit 7 of result
                self.V = 1 if ((rd_sign != rr_sign) and (rd_sign != res_sign)) else 0
                
                self.updateFlags(res)
                
                print(f'CPI R{Rd}, {K:02X}\t\t{self.getFlagString()}')
                
            case 'SBRC':
                # SBRC Rd, b -> 1111 110r rrrr 0bbb
                Rd, b = Rd5, b3
                vRd = yield from self.readByte(Rd)

                self.skip = ((vRd>>b)&1 == 0)
                print(f'SBRC R{Rd}, {b}\t\tskip={self.skip}')

            case 'SBRS':
                # SBRS Rd, b -> 1111 111r rrrr 0bbb
                b = b3      # bit position
                Rd = Rd5    # Register
                
                v = yield from self.readByte(Rd)
                self.skip = bool((v >> b) & 1)
                print(f'SBRS R{Rd}, {b}\t\t{v:08b} & {1 << b:08b} = {self.skip}')
                
            case 'SBIC':
                # SBIC A, b -> 1001 1001 AAAA Abbb
                A, b = A5, b3
                vA = yield from self.readByte(A + 0x20)
                self.skip = ((vA >> b) & 1) == 0
                print(f'SBIC {A:02X}, {b}\t\tskip={self.skip}')
                
            case 'SBIS':
                # SBIS A, b -> 1001 1011 AAAA Abbb
                A, b = A5, b3
                vA = yield from self.readByte(A + 0x20)
                self.skip = bool((vA >> b) & 1) 
                print(f'SBIS {A:02X}, {b}\t\tskip={self.skip}')
                    
            case 'SBI': 
                # SBI A, b → 1001 1010 AAAAA bbb
                # Set Bit in I/O register
                A, b = A5, b3
                v = yield from self.readByte(A + 0x20)
                v = v | (1 << b)
                yield from self.writeByte(A + 0x20, v)
                print(f'SBI {A:02X}, b3\t\t[{A+0x20:02X}]={v:02X}') 
                
            case 'LSL': 
                # LSL Rd -> 0000 11dd dddd dddd
                Rd = Rd5
                
                vRd = yield from self.readByte(Rr)
                
                res = vRd + vRd

                self.Z = 1 if (res == 0) else 0
                self.N = (res >> 7)
                self.C = 1 if (res > 0xFF) else 0
                self.H =  1 if (((vRd & 0x0F) + (vRr & 0x0F)) > 0x0F) else 0
                rd_sign = (vRd >> 7) & 1
                res_sign = (res >> 7) & 1
                self.V = 1 if (rd_sign != res_sign) else 0
                self.S = self.N ^ self.V

                yield from self.writeByte(Rd, res)

                print(f'LSL R{Rd}\t\tR{Rd}={res:02X}\t{self.getFlagString()}')
                
            case 'LSR':
                # LSR Rd -> 1001 010d dddd 0110
                # Logical Shift Right
                Rd = Rd5
                vRd = yield from self.readByte(Rd)
                bit_shifted_out = vRd & 0x01
                
                res = (vRd >> 1) 
                
                self.C = bit_shifted_out
                self.Z = 1 if res == 0 else 0
                self.N = 0
                self.V = self.N ^ self.C
                self.S = self.N ^ self.V
                # self.H not affected                 
                yield from self.writeByte(Rd, res)                
                print(f'LSR R{Rd}\t\tR{Rd}={res:02X}')
            
                
            case 'ROR':
                # ROR Rd -> 1001 010d dddd 0111
                # Rotate right
                Rd =  Rd5
                vRd = yield from self.readByte(Rd)
                
                C = vRd & 1
                res = (vRd >> 1) | (self.C << 7)

                self.Z = 0 if res == 0 else 1
                self.C = C
                self.N = res & 0x80
                self.V = vRd ^ C
                # self.H = undefined
                yield from self.writeByte(Rd, res)
                print(f'ROR R{Rd}\t\tR{Rd}={res:02X}')

            case 'SUB':
                # SUB Rd, Rr -> 0001 10rd dddd rrrr
                Rr, Rd = Rr5, Rd5
                
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                
                res =  vRd - vRr

                self.C = 1 if vRd < vRr else 0
                self.H = 1 if (vRd & 0x0F) < (vRr & 0x0F) else 0
                rd_sign = (vRd >> 7) & 1
                rr_sign = (vRr >> 7) & 1
                res_sign = (res >> 7) & 1
                self.V = 1 if (rd_sign != rr_sign) and (res_sign != rd_sign) else 0
                
                
                self.updateFlags(res)

                yield from self.writeByte(Rd, res & 0xFF)
                
                print(f'SUB R{Rd}, R{Rr}\t\tR{Rd}={res&0xFF:02X} {self.getFlagString()}')

            case 'SUBI':
                # SUBI Rd, K -> 0101 KKKK dddd KKKK
                # Subtract Immediate
                K, Rd = K8, Rd4 + 16
                vRd = yield from self.readByte(Rd)
                res = vRd - K

                self.C = 1 if vRd < K else 0
                self.H = 1 if (vRd & 0x0F) < (K & 0x0F) else 0
                rd_sign = (vRd >> 7) & 1
                rr_sign = (K >> 7) & 1
                res_sign = (res >> 7) & 1
                self.V = 1 if (rd_sign != rr_sign) and (res_sign != rd_sign) else 0
                
                
                self.updateFlags(res)

                yield from self.writeByte(Rd, res & 0xFF)
                
                print(f'SUBI R{Rd}, {K}\t\tR{Rd}={res&0xFF:02X} {self.getFlagString()}')
                
            case 'SBC':
                # SBC Rd,Rr -> 0000 10rd dddd rrrr
                Rr, Rd = Rr5, Rd5

                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)

                res = vRd - vRr - self.C

                self.Z = 1 if (res & 0xFF) == 0 else 0
                self.N = (res >> 7) & 1
                self.C = 1 if vRd < vRr else 0
                self.H = 1 if (vRd & 0x0F) < (vRr & 0x0F) else 0
                rd_sign = (vRd >> 7) & 1
                rr_sign = (vRr >> 7) & 1
                res_sign = (res >> 7) & 1
                self.V = 1 if (rd_sign != rr_sign) and (res_sign != rd_sign) else 0
                self.S = self.N ^ self.V

                yield from self.writeByte(Rd, res & 0xFF)
                
                print(f'SBC R{Rd}, R{Rr}, C{self.C}\t\tR{Rd}={res&0xFF:02X} {self.getFlagString()}')
                
            case 'SBCI':
                # SBCI Rd, K -> 0100 KKKK dddd KKKK
                # Subtract Immediate with Carry
                K , Rd =  K8, Rd4 + 16 
                vRd = yield from self.readByte(Rd)
                
                res =  vRd - K - self.C

                self.Z = 1 if (res & 0xFF) == 0 else 0
                self.N = (res >> 7) & 1
                self.C = 1 if vRd < K else 0
                self.H = 1 if (vRd & 0x0F) < (K & 0x0F) else 0
                rd_sign = (vRd >> 7) & 1
                rr_sign = (K >> 7) & 1
                res_sign = (res >> 7) & 1
                self.V = 1 if (rd_sign != rr_sign) and (res_sign != rd_sign) else 0
                self.S = self.N ^ self.V

                yield from self.writeByte(Rd, res & 0xFF)
                print(f'SBCI R{Rd}, {K}, C{self.C}\t\tR{Rd}={res&0xFF:02X} {self.getFlagString()}')
                
            case 'SBIW':
                # SBIW Rd, K -> 1001 0111 KKdd KKKK
                K = K6
                Rd = 24 + (((self.ins>>4)&0b11) * 2)
                vRh = yield from self.readByte(Rd+1)
                vRl = yield from self.readByte(Rd)
                
                val = ((vRh << 8) | vRl)
                res = val - K

                
                self.C = 1 if K > val else 0
                val_sign = (val >> 15) & 1
                res_sign = (res >> 15) & 1
                self.V = 1 if (val_sign == 0 and res_sign == 1) else 0
                
                self.updateFlags(res, is16=True)
                yield from self.writeByte(Rd + 1 , (res>>8) & 0xFF)
                yield from self.writeByte(Rd, res & 0xFF)
                
                print(f'SBIW R{Rd}, {K:04X}\t\tR{Rd+1}={((res>>8) & 0xFF):02X} R{Rd}={(res & 0xFF):02X} {self.getFlagString()}')
                
            case 'SWAP':
                raise Exception('SWAP not reviewed')
                self.Rd = (self.ins>>4)&0x1F
                self.reg[self.Rd]= ((self.reg[self.Rd]&0xF)<<4) | ((self.reg[self.Rd]&0xF0)>>4)

                self.pc += 1
                
            case 'BSET':
                # BSET s -> 1001 0100 0sss 1000
                s = s3
                self.setSREGField(s, 1)
                SREG, sSREG = self.getSREG()
                print(f'BSET {s}\t\t{sSREG[s]}=1')
                
            case 'BCLR':
                # BCLR s -> 1001 0100 1sss 1000
                s = s3
                self.setSREGField(s, 0)
                SREG, sSREG = self.getSREG()
                print(f'BCLR {s}\t\t{sSREG[s]}=0')
                
            case 'BST':
                # BST Rr, b -> 1111 101r rrrr 0bbb
                # Bit store from T flag
                Rr, b = Rd5, b3
                vRr = yield from self.readByte(Rr)
                self.T = (vRr >> b3) & 1
                print(f'BST R{Rr}, {b}\t\tT={(vRr >> b3) & 1}')
 
            case 'BLD':
                # BLD Rd, b -> 1111 100d dddd 0bbb
                # Bit load from T Flag
                Rd, b = Rd5, b3
                vRd = yield from self.readByte(Rd)
                vRd = (self.T << b) | (vRd & ~(1 << b))
                yield from self.writeByte(Rd, vRd)
                print(f'BLD R{Rd}, {b}\t\tR{Rd}={vRd:02X}')

            case 'MOV':
                # MOV Rd, Rr -> 0010 11rd dddd rrrr
                Rr, Rd = Rr5, Rd5 
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(Rd, vRr)
                print(f'MOV R{Rd}, R{Rr}\t\tR{Rd}={vRr:02X}')
                
            case 'MOVW':
                # MOVW Rd, Rr -> 0000 0001 dddd rrrr
                Rr, Rd = Rr5, Rd5
                vRh = yield from self.readByte(Rr+1)
                vRl = yield from self.readByte(Rr)
                    
                yield from self.writeByte(Rd+1, vRh)
                yield from self.writeByte(Rd, vRl)
                print(f'MOVW R{Rd}, R{Rr}\t\tR{Rd+1}={vRh:02X} R{Rd}={vRl:02X}')
                
            case 'LDI':
                # LDI Rd, K -> 1110 KKKK dddd KKKK
                Rd = Rd4+16                      
                K = K8
                yield from self.writeByte(Rd, K)
                
                print(f'LDI R{Rd}, {K:02X}\t\tR{Rd}={K:02X}')
                
            case 'LDX': #X
                raise Exception('LDX not reviewed')
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
                raise Exception('LDX+ not reviewed')
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
                raise Exception('LD-X not reviewed')
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
                raise Exception('LDY not reviewed')
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
                raise Exception('LDY+ not reviewed')
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
                raise Exception('LD-Y not reviewed')
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
                raise Exception('LDDY not reviewed')
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
                raise Exception('LDZ not reviewed')
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
                raise Exception('LDZ+ not reviewed')
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
                raise Exception('LD-Z not reviewed')
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
                raise Exception('LDDZ not reviewed')
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
            case 'LDS':
                # Load direct from sram
                Rd = Rd5
                # add is loaded in the skip logic

                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                
                print(f'LDS R{Rd}, {add:04X}\tR{Rd}={v:02X}')
                
            case 'STX':#X
                raise Exception('STX not reviewed')
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
                raise Exception('STX+ not reviewed')
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
                raise Exception('ST-X not reviewed')
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
                raise Exception('STY not reviewed')
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
                raise Exception('STY+ not reviewed')
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
                raise Exception('ST-Y not reviewed')
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
                raise Exception('STDY not reviewed')
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
                raise Exception('STZ not reviewed')
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
                raise Exception('STZ+ not reviewed')
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
                raise Exception('ST-Z not reviewed')
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
                raise Exception('STDZ not reviewed')
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
            
            case 'STS':
                # STS k, Rr -> 1001 001d dddd 0000 kkkk kkkk kkkk kkkk
                Rr = Rd5
                # add is loaded in the skip logic
                v = yield from self.readByte(Rr)
                yield from self.writeByte(add, v)
                print(f'STS {add:04X}, R{Rr}\t[{add:04X}]={v:02X}')

            case 'LPM': #R0 implied
                raise Exception('LPM not reviewed')
                self.A = (self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8)

                if(self.A&0b1 == 1 ):##high byte
                    self.reg[1] = (self.flash[(self.A>>1)] & 0xFF00)>>8
                else: ## low byte 
                    self.reg[0] = (self.flash[(self.A>>1)]&0xFF)

                self.pc += 1 
            case 'LPMZ': #Z
                raise Exception('LPMZ not reviewed')
                self.Rd = ((self.ins>>4)&0x1F)
                self.A = (self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8)


                if(self.A&0b1 == 1 ):##high byte
                    self.reg[self.Rd] = (self.flash[(self.A>>1)] & 0xFF00)>>8
                else: ## low byte 
                    self.reg[self.Rd] = (self.flash[(self.A>>1)]&0xFF)


                self.pc += 1
            case 'LPMZ+': #Z+
                raise Exception('LPMZ+ not reviewed')
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
                raise Exception('SPM not reviewed')
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
                # IN Rd, A -> 1011 0AAd dddd AAAA
                Rd = Rd5
                add = A6 + 0x20
                
                if (add == SPH_REG):
                    v = self.SP >> 8
                elif (add == SPL_REG):
                    v = self.SP & 0xF
                elif (add == SREG_REG):
                    v, _ = self.getSREG()
                else:
                    v = yield from self.readByte(add)
                
                yield from self.writeByte(Rd, v)
                print(f'IN R{Rd}, {A6:02X}\t\tR{Rd}={v:02X}')
                
            case 'OUT':
                # -> 1011 1AAr rrrr AAAA
                Rr = Rd5
                add = A6 + 0x20
                
                v = yield from self.readByte(Rr)
                
                if (add == SPH_REG):
                    self.SP = (v << 8) | self.SP & 0x00FF
                elif (add == SPL_REG):
                    self.SP = v | self.SP & 0xFF00
                elif (add == SREG_REG):
                    self.I = (v >> 7) & 1
                    self.T = (v >> 6) & 1
                    self.H = (v >> 5) & 1
                    self.S = (v >> 4) & 1
                    self.V = (v >> 3) & 1
                    self.N = (v >> 2) & 1
                    self.Z = (v >> 1) & 1
                    self.C = (v & 1)
                else:
                    yield from self.writeByte(add, v)
                
                print(f'OUT {A6:02X}, R{Rr}\t\t[{add:02X}]={v:02X}')

            case 'PUSH':
                # PUSH Rr → 1001 001d dddd 1111
                Rr = Rd5
                self.SP -= 1
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(self.SP, vRr)
                print(f'PUSH R{Rr}\t\t[self.SP:04X]={vRr:02X}')                
            
            case 'POP':
                # POP Rd → 1001 000d dddd 1111
                Rd = Rd5
                vRd = yield from self.readByte(self.SP)
                self.SP += 1
                yield from self.writeByte(Rd, vRd)
                print(f'POP R{Rd}\t\tR{Rd}={vRd:02X}')                

            case 'NOP':
                # NOP -> 0000 0000 0000 0000
                print('NOP')
                
            case 'SLEEP':
                ##activation of SLEEP MODE
                raise Exception('SLEEP not validated')
                self.pc += 1
            case 'WDR' :
                ## Watchdog Reset
                raise Exception('WDR not validated')
                self.pc +=1
            case 'BREAK' : 
                ## Sould enter debug mode
                raise Exception('BREAK not validated')
                self.pc += 1
            case 'invalid': #basicaly a nop
                raise Exception(f'invalid opocode: {self.ins:04X}')
                self.pc += 1
                
        yield