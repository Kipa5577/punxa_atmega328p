import py4hw
from ..Instruction_Decoder import *  
from ..Memory import * 



class SingleCycleATmega328P(py4hw.Logic):
    def __init__(sel,parent, name:str , memory:MemoryInterface,):
        super().__init__(parent,name)

        self.mem = self.addInterfaceSource('memory',memory)
        self.pc = 0
        self.reg = [0]*32
        self.ram = [0]*2048
        self.flash = [0]*32256
        self.SREG = 0 # b7: I b6: T b5: H b4: S b3: V b2: N b1: Z b0: C 


    def clock():
            self.fetchIns()
            self.execute()

            if(self.should_jump):
                self.pc = self.jmp_address
            else:
                self.pc += 1


    def fetchIns(self):
        if(self.SREG[7]==1):# interruption
                print('interruption')

        self.ins =  self.flash[self.pc]
        

    def execute(self):
        opp =  ins_to_str(self.ins)

        match opp: 

            case 'ADD':
                  
            case 'ADC':
                  
            case 'ADIW':
            case 'SUB':
            case 'SUBI':
            case 'SBC':
            case 'SBCI':
            case 'SBIW':
            case 'AND':
            case 'ANDI':
            case 'OR':
            case 'ORI':
            case 'EOR':
            case 'COM':
            case 'NEG':
            case 'SBR':
            case 'CBR':
            case 'INC':
            case 'DEC':
            case 'TST':
            case 'CLR':
            case 'SER':
            case 'MUL':
            case 'MULS':
            case 'MULSU':
            case 'FMUL':
            case 'FMULS': 
            case 'FMULSU':






            case 'RJMP':
            case 'IJMP':
            case 'JMP':
            case 'RCALL':
            case 'ICALL':
            case 'CALL':
            case 'RET':
            case 'RETI':
            case 'CPSE':
            case 'CP':
            case 'CPC':
            case 'CPI':
            case 'SBRC':
            case 'SBRS':
            case 'SBIC':
            case 'SBIS':
            case 'BRBS':
            case 'BRBC':
            case 'BREQ':
            case 'BRNE':
            case 'BRCS':
            case 'BRCC':
            case 'BRSH':
            case 'BRLO':
            case 'BRMI':
            case 'BRGE':
            case 'BRLT':
            case 'BRHS':
            case 'BRHC':
            case 'BRTS':
            case 'BRTC':
            case 'BRVS':
            case 'BRVC':
            case 'BRIE':
            case 'BRID':



            case 'SBI':
            case 'CBI':
            case 'LSL':
            case 'LSR':
            case 'ROL':
            case 'ROR':
            case 'ASR':
            case 'SWAP':
            case 'BSET':
            case 'BCLR':
            case 'BST':
            case 'BLD':
            case 'SEC':
            case 'CLC':
            case 'SEN':
            case 'CLN':
            case 'SEZ':
            case 'CLZ':
            case 'SEI':
            case 'CLI':
            case 'SES':
            case 'CLS':
            case 'SEV':
            case 'CLV':
            case 'SET':
            case 'CLT':
            case 'SEH':
            case 'CLH':



            case 'MOV':
            case 'MOVW':
            case 'LDI':
            case 'LD': #X
            case 'LD': #X+
            case 'LD': #-X
            case 'LD': #Y
            case 'LD': #Y+
            case 'LD': #-Y
            case 'LDD':#Y+q
            case 'LD':#Z
            case 'LD':#Z+
            case 'LD':#–Z
            case 'LDD':#Z+q
            case 'LDS':#k
            case 'ST':#X
            case 'ST':#X+
            case 'ST':#–X
            case 'ST':#Y
            case 'ST':#Y+
            case 'ST':#–Y
            case 'STD':#Y+q
            case 'ST':#Z
            case 'ST':#Z+
            case 'ST':#–Z
            case 'STD':#Z+q
            case 'STS':#k
            case 'LPM': #R0 implied
            case 'LPM': #Z
            case 'LPM': #Z+
            case 'SPM':
            case 'IN':
            case 'OUT':
            case 'PUSH':
            case 'POP':

            case 'NOP':
            case 'SLEEP':
            case 'WDR' :
            case 'BREAK' : 