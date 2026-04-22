import py4hw
from ..Instruction_Decoder import *  
from ..Memory import * 

C = 0
Z = 1
N = 2
V = 3
S = 4
H = 5 
T = 6
I = 7


#pointer registers
# R26 X-register Low Byte 
# R27 X-register High Byte
# R28 Y-register Low Byte
# R29 Y-register High Byte
# R30 Z-register Low Byte 
# R31 Z-register High Byte 

class SingleCycleATmega328P(py4hw.Logic):
    def __init__(self,parent, name:str , memory:MemoryInterface):
        super().__init__(parent,name)

        self.mem = self.addInterfaceSource('memory',memory)
        self.pc = 0
        self.reg = [0]*32
        self.ram = [0]*2048
        self.flash = [0]*32256
        self.SREG = 0 # b7: I b6: T b5: H b4: S b3: V b2: N b1: Z b0: C 
        self.should_jump = False
        self.stack_pointer  = 0 ## value sould be known by using a register
        self.next_cycle = False #varible to indicate that data is ready to read from ram/memeory


    def clock(self):
        self.fetchIns()
        self.execute()


    def fetchIns(self):
        if(self.SREG[7]==1):# interruption
                print('interruption')

        self.ins =  self.flash[self.pc]
        

    def execute(self):
        opp =  ins_to_str(self.ins)

        match opp: 
            case 'ADD':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] + self.reg[Rr]

                self.pc += 1
            case 'ADC':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] + self.reg[Rr] + (self.SREG & 0b1)

                self.pc += 1
            case 'ADIW':
                K = (((self.ins>>6)&0b11)<<4)|(self.ins & 0xF)
                Rd = (self.ins>>4)&0b11
                self.reg[Rd] =  self.reg[Rd] +  K

                self.pc += 1
            case 'SUB':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] - self.reg[Rr]

                self.pc += 1
            case 'SUBI':
                K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                Rd = (self.ins>>4)&0b11
                self.reg[Rd] =  self.reg[Rd] -  K

                self.pc += 1
            case 'SBC':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] - self.reg[Rr] - (self.SREG & 0b1)

                self.pc += 1
            case 'SBCI':
                K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] - K - (self.SREG & 0b1)

                self.pc += 1
            case 'SBIW':
                K = (((self.ins>>6)&0b11)<<4)|(self.ins & 0xF)
                Rd = (self.ins>>4)&0b11
                self.reg[Rd] =  self.reg[Rd] +  K

                self.pc += 1
            case 'AND':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] & self.reg[Rr]

                self.pc += 1
            case 'ANDI':
                K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] & K 

                self.pc += 1
            case 'OR':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] | self.reg[Rr]

                self.pc += 1
            case 'ORI':
                K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] & K 

                self.pc += 1
            case 'EOR':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] ^ self.reg[Rr]

                self.pc += 1
            case 'COM':
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] = 0xFF - self.reg[Rd] 

                self.pc += 1
            case 'NEG':
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] = 0x00 - self.reg[Rd] 

                self.pc += 1
            case 'SBR':
                K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] | K 

                self.pc += 1
            case 'CBR':
                K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rd] & K 

                self.pc += 1
            case 'INC':
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] = self.reg[Rd] + 1 

                self.pc += 1
            case 'DEC':
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] = self.reg[Rd] - 1

                self.pc += 1
            case 'TST':
                Rd1 = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                #Rd2 = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd1] =  self.reg[Rd1] & self.reg[Rd1]

                self.pc +=1

            case 'CLR':
                Rd1 = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                #Rd2 = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd1] =  self.reg[Rd1] ^ self.reg[Rd1]

                self.pc +=1

            case 'SER':
                Rd = (self.ins>>4)&0b11
                self.reg[Rd1] = 0xFF

                self.pc +=1 
            case 'MUL':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                res =  self.reg[Rd] * self.reg[Rr]
                self.reg[1] = res>>8 &0xFF
                self.reg[0] = res & 0xFF

                self.pc += 1
            case 'MULS': ## Don't know the implementation difference with MUL
                Rr = (self.ins & 0xF)
                Rd = ((self.ins>>4) & 0xF)
                res =  self.reg[Rd] * self.reg[Rr]
                self.reg[1]= res>>8 & 0xFF
                self.reg[0]= res & 0xFF

                self.pc += 1
            case 'MULSU':## Don't know the implementation difference with MUL
                Rr = (self.ins & 0b111)
                Rd = ((self.ins>>4) & 0b111)
                res =  self.reg[Rd] * self.reg[Rr]
                self.reg[1]= res>>8 & 0xFF
                self.reg[0]= res & 0xFF

                self.pc += 1
            case 'FMUL':## Don't know the implementation difference with MUL
                Rr = (self.ins & 0b111)
                Rd = ((self.ins>>4) & 0b111)
                res =  self.reg[Rd] * self.reg[Rr]
                self.reg[1]= res>>8 & 0xFF
                self.reg[0]= res & 0xFF

                self.pc += 1

            case 'FMULS': ## Don't know the implementation difference with MUL
                Rr = (self.ins & 0b111)
                Rd = ((self.ins>>4) & 0b111)
                res =  self.reg[Rd] * self.reg[Rr]
                self.reg[1]= res>>8 & 0xFF
                self.reg[0]= res & 0xFF

                self.pc += 1

            case 'FMULSU':## Don't know the implementation difference with MUL
                Rr = (self.ins & 0b111)
                Rd = ((self.ins>>4) & 0b111)
                res =  self.reg[Rd] * self.reg[Rr]
                self.reg[1]= res>>8 & 0xFF
                self.reg[0]= res & 0xFF

                self.pc += 1





            case 'RJMP':
                K= self.ins & 0xFFF

                self.pc += K + 1 

            case 'IJMP':
                self.pc  = + (self.reg[30] | self.reg[31]<<8)
            case 'JMP':
                K = (((self.ins&0b1)|((self.ins>>4)&0xF)|((self.ins>>8)&0b1))<<16)|self.flash[self.pc+1]
                self.pc = K
            case 'RCALL':
                K = self.ins&0xFFF
                self.pc += K

            ##case 'ICALL':

                
            ##case 'CALL':



            ##case 'RET':


            ##case 'RETI':## return from interrupt 


            case 'CPSE':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                if Rr == Rd:
                    next_ins = ins_to_str(self.flash[self.pc])
                    if(next_ins == 'CALL' or next_ins == 'JMP' or next_ins == 'STS' or next_ins == 'LDS'):
                        self.pc += 3 ##skip 2 word instruction
                    else:
                        self.pc += 2## skip 1 word instruction 
                else:
                    self.pc += 1


            case 'CP':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                res =  self.reg[Rd] + self.reg[Rr] 

                self.pc += 1
            case 'CPC':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                res =  self.reg[Rd] + self.reg[Rr] + (self.SREG & 0b1)

                self.pc += 1
            case 'CPI':
                K = (self.ins&0xF)|(self.ins>>4)&0xF0
                d = (self.ins>>4)&0xF
                res = self.reg[d]-K


                self.pc+=1
            case 'SBRC':
                b = self.ins&0b111
                A = (self.ins>>4)&0b11111
                if (self.reg[A]>>b)&1 == 0:
                    next_ins = ins_to_str(self.flash[self.pc])
                    if(next_ins == 'CALL' or next_ins == 'JMP' or next_ins == 'STS' or next_ins == 'LDS'):
                        self.pc += 3 ##skip 2 word instruction
                    else:
                        self.pc += 2## skip 1 word instruction 
                else:
                    self.pc += 1

            case 'SBRS':
                b = self.ins&0b111
                A = (self.ins>>4)&0b11111
                if (self.reg[A]>>b)&1 == 1:
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

            case 'SBIS':
                b = self.ins&0b111
                A = (self.ins>>3)&0b11111
                ## implement I/O read to test if 1

            case 'BRBS':
                K =  (self.ins>>3)&0b1111111 
                S =  self.ins&0b111
                if(self.SREG>>S)&1 == 1:
                    self.pc += + K +1
                else:
                    self.pc += 1 

            case 'BRBC':
                K =  (self.ins>>3)&0b1111111 
                S =  self.ins&0b111
                if(self.SREG>>S)&1 == 0:
                    self.pc += + K +1
                else:
                    self.pc += 1 

            case 'BREQ':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>Z)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1
            case 'BRNE':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>Z)&1) == 0:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRCS':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>C)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRCC':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>C)&1) == 0:
                    self.pc += K + 1
                else:
                    self.pc += 1
            case 'BRSH':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>C)&1) == 0:
                    self.pc += K + 1
                else:
                    self.pc += 1
            case 'BRLO':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>C)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRMI':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>N)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRGE':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>S)&1) == 0:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRLT':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>S)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRHS':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>H)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRHC':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>H)&1) == 0:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRTS':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>T)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRTC':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>T)&1) == 0:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRVS':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>V)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRVC':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>V)&1) == 0:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRIE':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>I)&1) == 1:
                    self.pc += K + 1
                else:
                    self.pc += 1

            case 'BRID':
                K = (self.ins>>3) & 0b1111111
                if((self.SREG>>I)&1) == 0:
                    self.pc += K + 1
                else:
                    self.pc += 1



            case 'SBI': ## implement write in io 
                print("SBI")
            ##case 'CBI': ## implement write in io 

            case 'LSL': ## jsut add I don't know what the best implementation would be 
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] += self.reg[Rd]
                
                self.pc += 1

            case 'LSR':
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.SREG = self.SREG | ((self.reg[Rd]&1)<<C)
                self.reg[Rd] = self.reg[Rd]>>1
                
                self.pc += 1

            case 'ROL':
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.SREG = self.SREG | ((self.reg[Rd]&1)<<C)
                self.reg[Rd] = self.reg[Rd]>>1
                
                self.pc += 1
            case 'ROR':
                print("ROR")
            ##case 'ASR':

            case 'SWAP':
                Rd = (self.ins>>4)&11111
                self.reg[Rd]= ((self.reg[Rd]>>4)&0xF) | ((self.reg[Rd]<<4)&0xF0)

                self.pc += 1
            case 'BSET':
                s = (self.ins>>4)&0b111
                self.SREG |=(0b1<<s) 

                self.pc = 1
            case 'BCLR':
                s = (self.ins>>4)&0b111
                self.SREG &=~(0b1<<s) 

                self.pc = 1
            case 'BST':
                b = self.ins&0b111
                Rd = (self.ins>>4)&0b11111
                self.SREG &= ~(0b1<<T)
                self.SREG |= ((self.reg[Rd]>>b)&1)<<T

                self.pc += 1
            case 'BLD':
                b = self.ins&0b111
                Rd = (self.ins>>4)&0b11111
                self.reg[Rd] &= ~(0b1<<b)
                self.reg[Rd] |= ((self.SREG>>T)&1)<<b

                self.pc += 1
            case 'SEC':
                self.SREG |= (1<<C)   
                self.pc += 1
            case 'CLC':
                self.SREG &= ~(1<<C)   
                self.pc += 1                
            case 'SEN':
                self.SREG |= (1<<N)   
                self.pc += 1
            case 'CLN':
                self.SREG &= ~(1<<N)   
                self.pc += 1
            case 'SEZ':
                self.SREG |= (1<<Z)   
                self.pc += 1
            case 'CLZ':
                self.SREG &= ~(1<<Z)   
                self.pc += 1
            case 'SEI':
                self.SREG |= (1<<I)   
                self.pc += 1
            case 'CLI':
                self.SREG &= ~(1<<I)   
                self.pc += 1
            case 'SES':
                self.SREG |= (1<<S)   
                self.pc += 1
            case 'CLS':
                self.SREG &= ~(1<<S)   
                self.pc += 1
            case 'SEV':
                self.SREG |= (1<<V)   
                self.pc += 1
            case 'CLV':
                self.SREG &= ~(1<<V)   
                self.pc += 1
            case 'SET':
                self.SREG |= (1<<T)   
                self.pc += 1
            case 'CLT':
                self.SREG &= ~(1<<T)   
                self.pc += 1
            case 'SEH':
                self.SREG |= (1<<H)   
                self.pc += 1
            case 'CLH':
                self.SREG &= ~(1<<H)   
                self.pc += 1

#pointer registers
# R26 X-register Low Byte 
# R27 X-register High Byte
# R28 Y-register Low Byte
# R29 Y-register High Byte
# R30 Z-register Low Byte 
# R31 Z-register High Byte 

            case 'MOV':
                Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rr]

                self.pc += 1
            case 'MOVW':
                Rr = (self.ins & 0xF)
                Rd = ((self.ins>>4) & 0xF)
                self.reg[Rd] =  self.reg[Rr]
                self.reg[Rd+1] = self.reg[Rr+1]

                self.pc += 1
            case 'LDI':
                Rd = (self.ins>>4)&0b1111
                K = (self.ins&0xF)|(((self.ins)>>4)&0xF0)

                self.reg[Rd] = K 
                self.pc += 1

            case 'LDX': #X
                Rd = (self.ins>>4)&0b11111 
                X  = self.reg[26]|(self.reg[27]<<8)
                self.mem.address.prepare(X)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'LDX+': #X+
                Rd = (self.ins>>4)&0b11111
                X = self.reg[26]|(self.reg[27]<<8)
                self.mem.address.prepare(X)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

                X += 1 ##incrementing X
                self.reg[26] = X&0xFF 
                self.reg[27] = (X>>8)&0xFF

            case 'LD-X': #-X
                Rd = (self.ins>>4)&0b11111
                X = self.reg[26]|(self.reg[27]<<8)
                X -= 1 ##decrementing X
                self.reg[26] = X&0xFF 
                self.reg[27] = (X>>8)&0xFF

                self.mem.address.prepare(X)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 



            case 'LDY': #Y
                Rd = (self.ins>>4)&0b11111
                Y = self.reg[28]|(self.reg[29]<<8)
                self.mem.address.prepare(Y)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'LDY+': #Y+
                Rd = (self.ins>>4)&0b11111
                Y = self.reg[28]|(self.reg[29]<<8)
                self.mem.address.prepare(Y)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

                Y += 1 ##incrementing Y
                self.reg[28] = Y&0xFF 
                self.reg[29] = (Y>>8)&0xFF

            case 'LD-Y': #-Y
                Rd = (self.ins>>4)&0b11111
                Y = self.reg[28]|(self.reg[29]<<8)

                Y += 1 ##incrementing Y
                self.reg[28] = Y&0xFF 
                self.reg[29] = (Y>>8)&0xFF

                self.mem.address.prepare(Y)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 


            case 'LDDY':#Y+q
                Rd = (self.ins>>4)&0b11111
                Y = self.reg[28]|(self.reg[29]<<8)
                q = (self.ins&0b111)|(self.ins&0b11000>>6)|(self.ins&0b100000>>7)
                
                self.mem.address.prepare(Y+q)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

                

            case 'LDZ':#Z
                Rd = (self.ins>>4)&0b11111
                Z = self.reg[30]|(self.reg[31]<<8)

                self.mem.address.prepare(Z)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'LDZ+':#Z+
                Rd = (self.ins>>4)&0b11111
                Z = self.reg[28]|(self.reg[29]<<8)
                self.mem.address.prepare(Z)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

                Z += 1 ##incrementing Z
                self.reg[28] = Z&0xFF 
                self.reg[29] = (Z>>8)&0xFF


            case 'LD-Z':#–Z
                Rd = (self.ins>>4)&0b11111
                Z = self.reg[26]|(self.reg[27]<<8)
                Z -= 1 ##decrementing Z
                self.reg[26] = Z&0xFF 
                self.reg[27] = (Z>>8)&0xFF

                self.mem.address.prepare(Z)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'LDDZ':#Z+q  verify this implementation
                Rd = (self.ins>>4)&0b11111
                Z = self.reg[28]|(self.reg[29]<<8)
                q = (self.ins&0b111)|(self.ins&0b11000>>6)|(self.ins&0b100000>>7)
                
                self.mem.address.prepare(Z+q)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'LDS':#k  Load direct from sram
                Rd = (self.ins>>4)&0b11111
                K = self.flash[self.pc+1]

                self.mem.address.prepare(K)
                self.mem.write.prepare(0)
                self.mem.read.prepare(1)
                self.mem.read.be(1)

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.reg[Rd] = self.mem.read_data.get()
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'STX':#X
                Rr = (self.ins>>4)&0b11111
                X = self.reg[26]|(self.reg[27]<<8)
                self.mem.address.prepare(X)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be(1)
                self.mem.write_data(self.reg[Rr])

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 


            case 'STX+':#X+
                Rr = (self.ins>>4)&0b11111
                X = self.reg[26]|(self.reg[27]<<8)
                self.mem.address.prepare(X)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be.preapre(1) 
                self.mem.write_data.prepare(self.reg[Rr]) # IMPORTANT  I have to check if this is a 2 cycle operation(ST) or 3 cycle 

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

                x += 1 ##incrementing X
                self.reg[28] = X&0xFF 
                self.reg[29] = (X>>8)&0xFF


            case 'ST-X':#–X
                Rr = (self.ins>>4)&0b11111
                x -= 1 ##incrementing X
                self.reg[27] = X&0xFF 
                self.reg[28] = (X>>8)&0xFF

                self.mem.address.prepare(X)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be.prepare(1)
                self.mem.write_data.prepare(self.reg[Rr])

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'STY':#Y
                Rr = (self.ins>>4)&0b11111
                Y = self.reg[27]|(self.reg[28]<<8)
                self.mem.address.prepare(X)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be(1)
                self.mem.write_data(self.reg[Rr])

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 


            case 'STY+':#Y+
                Rr = (self.ins>>4)&0b11111
                Y = self.reg[28]|(self.reg[29]<<8)
                self.mem.address.prepare(X)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be(1)
                self.mem.write_data(self.reg[Rr])

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

                Y += 1 ##incrementing Y
                self.reg[28] = Y&0xFF 
                self.reg[29] = (Y>>8)&0xFF

            case 'ST-Y':#–Y
                Rr = (self.ins>>4)&0b11111
                Y = self.reg[26]|(self.reg[27]<<8)
                Y -= 1 ##incrementing Y
                self.reg[28] = Y&0xFF 
                self.reg[29] = (Y>>8)&0xFF

                self.mem.address.prepare(Y)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be(1)
                self.mem.write_data(self.reg[Rr])

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'STD':#Y+q
                Rr = (self.ins>>4)&0b11111


            case 'STZ':#Z
                Rr = (self.ins>>4)&0b11111
                Y = self.reg[26]|(self.reg[27]<<8)
                self.mem.address.prepare(X)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be(1)
                self.mem.write_data(self.reg[Rr])

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'STZ+':#Z+
                Rr = (self.ins>>4)&0b11111
                Z = self.reg[30]|(self.reg[31]<<8)
                self.mem.address.prepare(Z)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be(1)
                self.mem.write_data(self.reg[Rr])

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'ST-Z':#–Z
                Rr = (self.ins>>4)&0b11111
                Z = self.reg[30]|(self.reg[31]<<8)
                self.mem.address.prepare(Z)
                self.mem.write.prepare(1)
                self.mem.read.prepare()
                self.mem.read.be(1)
                self.mem.write_data(self.reg[Rr])

                if self.next_cycle == True: ## this is to wait a cycle for the data to be ready
                    self.pc += 1
                    self.next_cycle = False 
                else: 
                    self.next_cycle = True 

            case 'STD':#Z+q
                Rr = (self.ins>>4)&0b11111


            case 'STS':#k
                Rr = (self.ins>>4)&0b11111


            case 'LPM': #R0 implied
                Z = self.reg[30]|(self.reg[31]<<8)
                self.reg[0] = self.flash[Z]


            case 'LPM': #Z
                Rd = (self.ins>>4)&0b11111
                Z = self.reg[30]|(self.reg[31]<<8)

                self.reg[Rd] = self.flash[Z]

            case 'LPM': #Z+
                Rd = (self.ins>>4)&0b11111
                Z = self.reg[30]|(self.reg[31]<<8)

                self.reg[Rd] = self.flash[Z]

                Z += 1 ##decrementing Z
                self.reg[26] = Z&0xFF 
                self.reg[27] = (Z>>8)&0xFF
            case 'SPM':
                Z = self.reg[30]|(self.reg[31]<<8)

                self.flash[Z] = self.reg[0]|(self.reg[1]<<8) #verifi the order of the registers

            case 'IN':
                Rd = (self.ins>>4)&0b11111
                A = (self.ins)&0xF | ((self.ins)>>5)&0b110000 #don't know what is the port



            case 'OUT':
                Rr = (self.ins>>4)&0b11111
                A = (self.ins)&0xF | ((self.ins)>>5)&0b110000 #don't know what is the port


            case 'PUSH':
                d =  (self.ins>>4)&11111
                self.ram[self.stack_pointer]=self.reg[d]
                self.stack_pointer -= 1
                self.pc+=1

            case 'POP':
                d =  (self.ins>>4)&11111
                self.stack_pointer += 1
                self.pc+=1

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