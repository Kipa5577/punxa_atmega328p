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

        #Warchdog Timer Configruation
        self.WDTCSR = 0
        self.WDTCSR_addr_LS = 0x60
        self.WDTCSR_addr_IO = 0x40
        self.WDG_val = 0  # Watchdog counter value

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
            yield from self.execute()
        
            self.csr[CSR_INSTRET] += 1
            
            # Watchdog Timer logic
            if (self.WDTCSR & 0b1000):  # WDE (Watchdog System Reset Enable) is set
                self.WDG_val += 1
                wdp = self.WDTCSR & 0b111
                # Threshold approximation based on WDP prescaler bits
                threshold = 1024 * (1 << wdp) 
                
                if self.WDG_val > threshold:
                    print(f"Watchdog Reset Triggered! WDG_val={self.WDG_val} > threshold={threshold}")
                    self.WDG_val = 0
                    self.pc = self.reset_address  # Reset PC back to reset vector
                    
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

    def readFlashWord(self, address):
        self.ins_mem.address.prepare(address)
        self.ins_mem.read.prepare(1)
        self.ins_mem.write.prepare(0)
        yield
        self.ins_mem.read.prepare(0)
        self.ins_mem.write.prepare(0)
        yield
        return self.ins_mem.read_data.get()

    def writeFlashWord(self, address, value):
        self.ins_mem.write.prepare(1)
        self.ins_mem.read.prepare(0)
        self.ins_mem.address.prepare(address)
        self.ins_mem.write_data.prepare(value)
        yield
        self.ins_mem.write.prepare(0)
        while (self.ins_mem.resp.get() == 0):
            yield
        yield

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


                self.H = 1 if (((vRd & 0x0F) + (vRr & 0x0F) + self.C) > 0x0F) else 0
                self.C = 1 if res > 0xFF else 0
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
                # SBR is a pseudo instruction for ORI
                raise Exception('SBR is a pseudo instruction for ORI, use ORI instead')
            
            case 'CBR':
                # CBR is a pseudo instruction for ANDI with complemented K
                raise Exception('CBR is a pseudo instruction for ANDI, use ANDI with complemented K instead')
                
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
                # ICALL -> 1001 0101 0001 1001
                zh = yield from self.readByte(31)
                zl = yield from self.readByte(30)
                add = (zh << 8) | zl

                ra = self.pc

                yield from self.writeByte(self.SP, (ra >> 8) & 0xFF)
                self.SP = (self.SP - 1) & 0xFFFF

                yield from self.writeByte(self.SP, ra & 0xFF)
                self.SP = (self.SP - 1) & 0xFFFF

                self.pc = add

                print(f'ICALL\t\t\t[{(self.SP+2)&0xFFFF:04X}]={(ra>>8):02X} [{(self.SP+1)&0xFFFF:04X}]={ra&0xFF:02X}')
                
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
                # SER is a pseudo instruction for LDI Rd, 0xFF
                raise Exception('SER is a pseudo instruction for LDI, use LDI Rd, 0xFF instead')
            
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

                yield from self.writeByte(self.SP, (ra >> 8) & 0xFF)
                self.SP = (self.SP - 1) & 0xFFFF

                yield from self.writeByte(self.SP, ra & 0xFF)
                self.SP = (self.SP - 1) & 0xFFFF

                self.pc += K

                print(f'RCALL {K:03X}\t\t[{(self.SP+2)&0xFFFF:04X}]={(ra>>8):02X} [{(self.SP+1)&0xFFFF:04X}]={ra&0xFF:02X}')
                    
            
                
            case 'CALL':
                ra = self.pc

                yield from self.writeByte(self.SP, (ra >> 8) & 0xFF)
                self.SP = (self.SP - 1) & 0xFFFF

                yield from self.writeByte(self.SP, ra & 0xFF)
                self.SP = (self.SP - 1) & 0xFFFF

                self.pc = add

                print(f'CALL {add:04X}\t\t[{(self.SP+2)&0xFFFF:04X}]={(ra>>8):02X} [{(self.SP+1)&0xFFFF:04X}]={ra&0xFF:02X}')

                        
            case 'RET':
                self.SP = (self.SP + 1) & 0xFFFF
                retl = yield from self.readByte(self.SP)

                self.SP = (self.SP + 1) & 0xFFFF
                reth = yield from self.readByte(self.SP)

                self.pc = (reth << 8) | retl

                print(f'RET\t\t\t\t[{SPH_REG:04X}]={(self.SP>>8):02X} [{SPL_REG:04X}]={(self.SP & 0xFF):02X}')
                
            case 'RETI':
                self.SP = (self.SP + 1) & 0xFFFF
                retl = yield from self.readByte(self.SP)

                self.SP = (self.SP + 1) & 0xFFFF
                reth = yield from self.readByte(self.SP)

                self.pc = (reth << 8) | retl
                self.I = 1

                print(f'RETI\t\t\t[{SPH_REG:04X}]={(self.SP>>8):02X} [{SPL_REG:04X}]={(self.SP & 0xFF):02X} {self.getFlagString()}')
                

            case 'CPSE':
                # CPSE Rd, Rr -> 0001 00rd dddd rrrr
                Rr, Rd = Rr5, Rd5
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                self.skip = (vRd == vRr)
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
                # CPC Rd, Rr -> 0000 01rd dddd rrrr
                # Compare with Carry
                Rr, Rd = Rr5, Rd5
                vRr = yield from self.readByte(Rr)
                vRd = yield from self.readByte(Rd)
                res = vRd - vRr - self.C

                self.C = 1 if (vRd < (vRr + self.C)) else 0
                self.H = 1 if ((vRd & 0x0F) < ((vRr & 0x0F) + self.C)) else 0
                rd_sign = (vRd >> 7) & 1
                rr_sign = (vRr >> 7) & 1
                res_sign = ((res & 0xFF) >> 7) & 1
                self.V = 1 if (rd_sign == 1 and rr_sign == 0 and res_sign == 0) or (rd_sign == 0 and rr_sign == 1 and res_sign == 1) else 0
                
                # Z flag is only cleared, never set (it's ANDed with previous Z)
                if (res & 0xFF) != 0:
                    self.Z = 0
                self.N = (res >> 7) & 1
                self.S = self.N ^ self.V

                print(f'CPC R{Rd}, R{Rr}\t\t{self.getFlagString()}')
            
            case 'CPI':
                # CPI Rd, k -> 0011 KKKK dddd KKKK
                # Compare with immediate
                K, Rd = K8, Rd4 + 16
                vRd = yield from self.readByte(Rd)
                
                res = (vRd - K) & 0xFF

                self.C = 1 if (vRd < K) else 0
                self.H =  1 if ((vRd & 0x0F) - (K & 0x0F)) < 0 else 0
                rd_sign = (vRd >> 7) & 1      # Bit 7 of RdB
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

            case 'BRGE':
                # BRGE k -> 1111 01kk kkkk k100
                K = py4hw.IntegerHelper.c2_to_signed((self.ins >> 3) & 0x7F, 7)

                if self.S == 0:
                    self.pc += K

                print(f'BRGE {K:+d}\t\tS={self.S}')

            case 'BRLT':
                # BRLT k -> 1111 00kk kkkk k100
                K = py4hw.IntegerHelper.c2_to_signed((self.ins >> 3) & 0x7F, 7)

                if self.S == 1:
                    self.pc += K

                print(f'BRLT {K:+d}\t\tS={self.S}')
                
            case 'LSL': 
                # LSL Rd -> 0000 11dd dddd dddd
                Rd = Rd5
                
                vRd = yield from self.readByte(Rd)
                
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
                
                old_C = self.C
                res =  vRd - K - old_C

                self.Z = 1 if (res & 0xFF) == 0 else 0
                self.N = (res >> 7) & 1
                self.C = 1 if res < 0 else 0
                self.H = 1 if ((vRd & 0x0F) - (K & 0x0F) - old_C) < 0 else 0
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
                # SWAP Rd -> 1001 010d dddd 0010
                # Swap nibbles
                Rd = Rd5
                vRd = yield from self.readByte(Rd)
                res = ((vRd & 0x0F) << 4) | ((vRd & 0xF0) >> 4)
                yield from self.writeByte(Rd, res)
                print(f'SWAP R{Rd}\t\tR{Rd}={res:02X}')
                
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
                Rd = (Rd5 & 0x0F) * 2
                Rr = (Rr5 & 0x0F) * 2

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
                
            case 'LDX':
                # LDX Rd, X -> 1001 000d dddd 1100
                # Load indirect from X
                Rd = Rd5
                xl = yield from self.readByte(26)
                xh = yield from self.readByte(27)
                add = (xh << 8) | xl
                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                print(f'LDX R{Rd}, X\t\tR{Rd}={v:02X} [X]={add:04X}')

            case 'LDX+':
                # LDX+ Rd, X+ -> 1001 000d dddd 1101
                Rd = Rd5
                xl = yield from self.readByte(26)
                xh = yield from self.readByte(27)
                add = (xh << 8) | xl
                v = yield from self.readByte(add)
                add = (add + 1) & 0xFFFF
                

                yield from self.writeByte(Rd, v)
                
                # THEN write the updated pointer (so it wins if Rd is 26 or 27)
                yield from self.writeByte(26, add & 0xFF)
                yield from self.writeByte(27, (add >> 8) & 0xFF)
                
                print(f'LDX+ R{Rd}, X+\t\tR{Rd}={v:02X} X={add:04X}')

            case 'LD-X':
                # LD-X Rd, -X -> 1001 000d dddd 1110
                # Load indirect from X with pre-decrement
                Rd = Rd5
                xl = yield from self.readByte(26)
                xh = yield from self.readByte(27)
                add = ((xh << 8) | xl) - 1
                add = add & 0xFFFF
                yield from self.writeByte(26, add & 0xFF)
                yield from self.writeByte(27, (add >> 8) & 0xFF)
                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                print(f'LD-X R{Rd}, -X\t\tR{Rd}={v:02X} X={add:04X}')

            case 'LDY':
                # LDY Rd, Y -> 1000 000d dddd 1000
                # Load indirect from Y
                Rd = Rd5
                yl = yield from self.readByte(28)
                yh = yield from self.readByte(29)
                add = (yh << 8) | yl
                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                print(f'LDY R{Rd}, Y\t\tR{Rd}={v:02X} [Y]={add:04X}')

            case 'LDY+':
                # LDY+ Rd, Y+ -> 1001 000d dddd 1001
                # Load indirect from Y and post-increment
                Rd = Rd5
                yl = yield from self.readByte(28)
                yh = yield from self.readByte(29)
                add = (yh << 8) | yl
                v = yield from self.readByte(add)
                add = (add + 1) & 0xFFFF
                yield from self.writeByte(28, add & 0xFF)
                yield from self.writeByte(29, (add >> 8) & 0xFF)
                yield from self.writeByte(Rd, v)
                print(f'LDY+ R{Rd}, Y+\t\tR{Rd}={v:02X} Y={add:04X}')

            case 'LD-Y':
                # LD-Y Rd, -Y -> 1001 000d dddd 1010
                # Load indirect from Y with pre-decrement
                Rd = Rd5
                yl = yield from self.readByte(28)
                yh = yield from self.readByte(29)
                add = ((yh << 8) | yl) - 1
                add = add & 0xFFFF
                yield from self.writeByte(28, add & 0xFF)
                yield from self.writeByte(29, (add >> 8) & 0xFF)
                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                print(f'LD-Y R{Rd}, -Y\t\tR{Rd}={v:02X} Y={add:04X}')

            case 'LDDY':
                # LDDY Rd, Y+q -> 10q0 qq0d dddd 0qqq
                # Load indirect from Y with displacement
                Rd = Rd5
                q = (self.ins & 0b111) | (((self.ins >> 10) & 0b11) << 3) | (((self.ins >> 13) & 0b1) << 5)
                yl = yield from self.readByte(28)
                yh = yield from self.readByte(29)
                add = ((yh << 8) | yl) + q
                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                print(f'LDDY R{Rd}, Y+{q}\t\tR{Rd}={v:02X} [Y+{q}]={add:04X}')

            case 'LDZ':
                # LDZ Rd, Z -> 1000 000d dddd 0000
                # Load indirect from Z
                Rd = Rd5
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                add = (zh << 8) | zl
                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                print(f'LDZ R{Rd}, Z\t\tR{Rd}={v:02X} [Z]={add:04X}')

            case 'LDZ+':
                # LDZ+ Rd, Z+ -> 1001 000d dddd 0001
                # Load indirect from Z and post-increment
                Rd = Rd5
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                add = (zh << 8) | zl
                v = yield from self.readByte(add)
                add = (add + 1) & 0xFFFF
                yield from self.writeByte(30, add & 0xFF)
                yield from self.writeByte(31, (add >> 8) & 0xFF)
                yield from self.writeByte(Rd, v)
                print(f'LDZ+ R{Rd}, Z+\t\tR{Rd}={v:02X} Z={add:04X}')

            case 'LD-Z':
                # LD-Z Rd, -Z -> 1001 000d dddd 0010
                # Load indirect from Z with pre-decrement
                Rd = Rd5
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                add = ((zh << 8) | zl) - 1
                add = add & 0xFFFF
                yield from self.writeByte(30, add & 0xFF)
                yield from self.writeByte(31, (add >> 8) & 0xFF)
                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                print(f'LD-Z R{Rd}, -Z\t\tR{Rd}={v:02X} Z={add:04X}')

                
            case 'LDDZ':
                # LDDZ Rd, Z+q -> 10q0 qq0d dddd 0qqq
                # Load indirect from Z with displacement
                Rd = Rd5
                q = (self.ins & 0b111) | (((self.ins >> 10) & 0b11) << 3) | (((self.ins >> 13) & 0b1) << 5)
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                add = ((zh << 8) | zl) + q
                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                print(f'LDDZ R{Rd}, Z+{q}\t\tR{Rd}={v:02X} [Z+{q}]={add:04X}')


            case 'LDS':
                # Load direct from sram
                Rd = Rd5
                # add is loaded in the skip logic

                v = yield from self.readByte(add)
                yield from self.writeByte(Rd, v)
                
                print(f'LDS R{Rd}, {add:04X}\tR{Rd}={v:02X}')
                
            case 'STX':
                # STX X, Rr -> 1001 001r rrrr 1100
                # Store indirect to X
                Rr = Rd5
                xl = yield from self.readByte(26)
                xh = yield from self.readByte(27)
                add = (xh << 8) | xl
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                print(f'STX X, R{Rr}\t\t[{add:04X}]={vRr:02X}')

            case 'STX+':
                # STX+ X+, Rr -> 1001 001r rrrr 1101
                # Store indirect to X and post-increment
                Rr = Rd5
                xl = yield from self.readByte(26)
                xh = yield from self.readByte(27)
                add = (xh << 8) | xl
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                add = (add + 1) & 0xFFFF
                yield from self.writeByte(26, add & 0xFF)
                yield from self.writeByte(27, (add >> 8) & 0xFF)
                print(f'STX+ X+, R{Rr}\t\t[{add-1:04X}]={vRr:02X} X={add:04X}')

            case 'ST-X':
                # ST-X -X, Rr -> 1001 001r rrrr 1110
                # Store indirect to X with pre-decrement
                Rr = Rd5
                xl = yield from self.readByte(26)
                xh = yield from self.readByte(27)
                add = ((xh << 8) | xl) - 1
                add = add & 0xFFFF
                yield from self.writeByte(26, add & 0xFF)
                yield from self.writeByte(27, (add >> 8) & 0xFF)
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                print(f'ST-X -X, R{Rr}\t\t[{add:04X}]={vRr:02X} X={add:04X}')

            case 'STY':
                # STY Y, Rr -> 1000 001r rrrr 1000
                # Store indirect to Y
                Rr = Rd5
                yl = yield from self.readByte(28)
                yh = yield from self.readByte(29)
                add = (yh << 8) | yl
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                print(f'STY Y, R{Rr}\t\t[{add:04X}]={vRr:02X}')

            case 'STY+':
                # ST Y+, Rr -> 1001 001r rrrr 1010
                # Note: The register is in bits 4-8, which maps to Rd5 in our parser
                Rr = Rd5 

                # Read the value from the register
                vRr = yield from self.readByte(Rr)

                # Read the Y pointer (R28 and R29)
                Y_low = yield from self.readByte(28)
                Y_high = yield from self.readByte(29)
                Y_ptr = (Y_high << 8) | Y_low

                # Store value to memory
                yield from self.writeByte(Y_ptr, vRr)

                # Post-increment Y pointer
                Y_ptr = (Y_ptr + 1) & 0xFFFF
                yield from self.writeByte(28, Y_ptr & 0xFF)
                yield from self.writeByte(29, (Y_ptr >> 8) & 0xFF)

            case 'ST-Y':
                # ST-Y -Y, Rr -> 1001 001r rrrr 1010
                # Store indirect to Y with pre-decrement
                Rr = Rd5
                yl = yield from self.readByte(28)
                yh = yield from self.readByte(29)
                add = ((yh << 8) | yl) - 1
                add = add & 0xFFFF
                yield from self.writeByte(28, add & 0xFF)
                yield from self.writeByte(29, (add >> 8) & 0xFF)
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                print(f'ST-Y -Y, R{Rr}\t\t[{add:04X}]={vRr:02X} Y={add:04X}')

            case 'STDY':
                # STDY Y+q, Rr -> 10q0 qq1r rrrr 1qqq
                Rr = (self.ins >> 4) & 0x1F     
                q = (((self.ins >> 13) & 0b1) << 5) | (((self.ins >> 10) & 0b11) << 3) | (self.ins & 0b111)
                yl = yield from self.readByte(28)
                yh = yield from self.readByte(29)
                add = (((yh << 8) | yl) + q) & 0xFFFF
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                print(f'STDY Y+{q}, R{Rr}\t\t[{add:04X}]={vRr:02X}')

            case 'STZ':
                # STZ Z, Rr -> 1000 001r rrrr 0000
                # Store indirect to Z
                Rr = Rd5
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                add = (zh << 8) | zl
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                print(f'STZ Z, R{Rr}\t\t[{add:04X}]={vRr:02X}')

            case 'STZ+':
                # STZ+ Z+, Rr -> 1001 001r rrrr 0001
                # Store indirect to Z and post-increment
                Rr = Rd5
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                add = (zh << 8) | zl
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                add = (add + 1) & 0xFFFF
                yield from self.writeByte(30, add & 0xFF)
                yield from self.writeByte(31, (add >> 8) & 0xFF)
                print(f'STZ+ Z+, R{Rr}\t\t[{add-1:04X}]={vRr:02X} Z={add:04X}')

            case 'ST-Z':
                # ST-Z -Z, Rr -> 1001 001r rrrr 0010
                # Store indirect to Z with pre-decrement
                Rr = Rd5
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                add = ((zh << 8) | zl) - 1
                add = add & 0xFFFF
                yield from self.writeByte(30, add & 0xFF)
                yield from self.writeByte(31, (add >> 8) & 0xFF)
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                print(f'ST-Z -Z, R{Rr}\t\t[{add:04X}]={vRr:02X} Z={add:04X}')

            case 'STDZ':
                # STDZ Z+q, Rr -> 10q0 qq1r rrrr 0qqq
                Rr = (self.ins >> 4) & 0x1F     
                q = (((self.ins >> 13) & 0b1) << 5) | (((self.ins >> 10) & 0b11) << 3) | (self.ins & 0b111)
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                add = (((zh << 8) | zl) + q) & 0xFFFF
                vRr = yield from self.readByte(Rr)
                yield from self.writeByte(add, vRr)
                print(f'STDZ Z+{q}, R{Rr}\t\t[{add:04X}]={vRr:02X}')
            
            case 'STS':
                # STS k, Rr -> 1001 001d dddd 0000 kkkk kkkk kkkk kkkk
                Rr = Rd5
                # add is loaded in the skip logic
                v = yield from self.readByte(Rr)
                yield from self.writeByte(add, v)
                print(f'STS {add:04X}, R{Rr}\t[{add:04X}]={v:02X}')

            case 'LPM':
                # LPM -> 1001 0101 1100 1000
                # Load byte at (Z) from program memory into R0. Z is unchanged.
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                Z = (zh << 8) | zl
                word = yield from self.readFlashWord(Z >> 1)
                v = (word >> 8) & 0xFF if (Z & 1) else word & 0xFF
                yield from self.writeByte(0, v)
                print(f'LPM\t\t\tR0={v:02X} [Z]={Z:04X}')


            case 'LPMZ':
                # LPMZ Rd, Z -> 1001 000d dddd 0100
                # Load byte at (Z) from program memory into Rd. Z is unchanged.
                Rd = Rd5
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                Z = (zh << 8) | zl
                word = yield from self.readFlashWord(Z >> 1)
                v = (word >> 8) & 0xFF if (Z & 1) else word & 0xFF
                yield from self.writeByte(Rd, v)
                print(f'LPMZ R{Rd}, Z\t\tR{Rd}={v:02X} [Z]={Z:04X}')


            case 'LPMZ+':
                # LPMZ+ Rd, Z+ -> 1001 000d dddd 0101
                # Load byte at (Z) from program memory into Rd, then post-increment Z.
                Rd = Rd5
                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                Z = (zh << 8) | zl
                word = yield from self.readFlashWord(Z >> 1)
                v = (word >> 8) & 0xFF if (Z & 1) else word & 0xFF
                yield from self.writeByte(Rd, v)
                Z = (Z + 1) & 0xFFFF
                yield from self.writeByte(30, Z & 0xFF)
                yield from self.writeByte(31, (Z >> 8) & 0xFF)
                print(f'LPMZ+ R{Rd}, Z+\t\tR{Rd}={v:02X} Z={Z:04X}')

            case 'SPM':
                # SPM -> 1001 0101 1110 1000
                SELFPRGEN = self.SPMCSR & 0b1
                PGERS     = (self.SPMCSR >> 1) & 0b1
                PGWRT     = (self.SPMCSR >> 2) & 0b1
                BLBSET    = (self.SPMCSR >> 3) & 0b1
                SPMIE     = (self.SPMCSR >> 7) & 0b1

                zl = yield from self.readByte(30)
                zh = yield from self.readByte(31)
                Z = (zh << 8) | zl

                word_addr = Z >> 1
                page_offset = word_addr % self.PAGE_SIZE_WORDS
                page_base_addr = word_addr - page_offset

                if SELFPRGEN == 1:
                    if (PGERS == 1) and (PGWRT == 0):
                        # --- PAGE ERASE: wipe the page in flash ---
                        for i in range(self.PAGE_SIZE_WORDS):
                            yield from self.writeFlashWord(page_base_addr + i, 0xFFFF)

                    elif (PGERS == 0) and (PGWRT == 1):
                        # --- PAGE WRITE: commit temp buffer into flash ---
                        # Flash bits can only go 1 -> 0, so AND with existing content
                        for i in range(self.PAGE_SIZE_WORDS):
                            existing = yield from self.readFlashWord(page_base_addr + i)
                            new_val = existing & self.temp_page_buffer[i]
                            yield from self.writeFlashWord(page_base_addr + i, new_val)
                        # Hardware auto-clears the temp buffer after a page write
                        self.temp_page_buffer = [0xFFFF] * self.PAGE_SIZE_WORDS

                    elif (PGERS == 0) and (PGWRT == 0) and (BLBSET == 0):
                        # --- FILL TEMPORARY BUFFER from R1:R0 ---
                        r0 = yield from self.readByte(0)
                        r1 = yield from self.readByte(1)
                        data_word = (r1 << 8) | r0
                        self.temp_page_buffer[page_offset] = data_word

                    # Hardware auto-clears the SPM enable bit after execution
                    self.SPMCSR &= ~0b1

                    if SPMIE == 1:
                        print('SPM Interrupt Triggered')

                print(f'SPM\t\t\tZ={Z:04X} SPMCSR={self.SPMCSR:02X}')



            case 'IN':
                # IN Rd, A -> 1011 0AAd dddd AAAA
                Rd = Rd5
                add = A6 + 0x20

                if add == SPH_REG:
                    v = (self.SP >> 8) & 0xFF
                elif add == SPL_REG:
                    v = self.SP & 0xFF
                elif add == SREG_REG:
                    v, _ = self.getSREG()
                else:
                    v = yield from self.readByte(add)

                yield from self.writeByte(Rd, v)
                print(f'IN R{Rd}, {A6:02X}\t\tR{Rd}={v:02X}')
                
            case 'OUT':
                # OUT Rr,A -> 1011 1AAr rrrr AAAA
                Rr = Rd5
                add = A6 + 0x20

                v = yield from self.readByte(Rr)

                if add == SPH_REG:
                    self.SP = ((v & 0xFF) << 8) | (self.SP & 0x00FF)
                    yield from self.writeByte(add, v)

                elif add == SPL_REG:
                    self.SP = (self.SP & 0xFF00) | (v & 0xFF)
                    yield from self.writeByte(add, v)

                elif add == SREG_REG:
                    self.I = (v >> 7) & 1
                    self.T = (v >> 6) & 1
                    self.H = (v >> 5) & 1
                    self.S = (v >> 4) & 1
                    self.V = (v >> 3) & 1
                    self.N = (v >> 2) & 1
                    self.Z = (v >> 1) & 1
                    self.C = v & 1
                    yield from self.writeByte(add, v)

                else:
                    yield from self.writeByte(add, v)

                print(f'OUT {A6:02X}, R{Rr}\t\t[{add:02X}]={v:02X}')

            case 'PUSH':
                # PUSH Rr → 1001 001d dddd 1111
                Rr = Rd5

                vRr = yield from self.readByte(Rr)

                # Store at current SP
                yield from self.writeByte(self.SP, vRr)

                oldSP = self.SP
                self.SP = (self.SP - 1) & 0xFFFF

                print(f'PUSH R{Rr}\t\t[{oldSP:04X}]={vRr:02X}')
            
            case 'POP':
                # POP Rd → 1001 000d dddd 1111
                Rd = Rd5

                # Advance SP to the last pushed value
                self.SP = (self.SP + 1) & 0xFFFF

                vRd = yield from self.readByte(self.SP)
                yield from self.writeByte(Rd, vRd)

                print(f'POP R{Rd}\t\tR{Rd}={vRd:02X}')             

            case 'NOP':
                # NOP -> 0000 0000 0000 0000
                print('NOP')
                
            case 'SLEEP':
                print('SLEEP')
            case 'WDR' :
                ## Watchdog Reset
                self.WDG_val = 0
                print('WDR')
            case 'BREAK':
                # BREAK = 1001 0111 1001 1000
                # If the On-Chip Debugger is enabled, this stops the CPU; otherwise
                # it is executed as a NOP.  Since we have no OCD attached, treat as NOP.
               
                print('BREAK')
            case 'invalid': #basicaly a nop
                raise Exception(f'invalid opocode: {self.ins:04X}')
                self.pc += 1
                
        yield