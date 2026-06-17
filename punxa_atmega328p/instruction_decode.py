#number of instructions 131

#Instructions in the data sheet 131
#Acounted for 131
#Decoded by the function 131 
#Instructions found in test 98 + CBR + BRLO +ROL + BRCC + SBR + TST + CLR +LPM+ 16(for the SREG clear and set instructions) Total: 123 ,missing 8 instructions
#SBR and CBR Fake instruction
#SER is an alias for LDI Rd,0xFF
#          #|15|14|13|12|11|10| 9| 8| 7| 6| 5| 4| 3| 2| 1| 0|
#1         #| OP              | R| D| D  D  D  D| R  R  R  R|'ADD' 'ADC' 'SUB' 'SBC' 'AND' 'OR' 'EOR' 'CPSE' 'CP' 'CPC' 'MUL' 'MOV'
#2         #| OP        | K  K  K  K| D  D  D  D| K  K  K  K|'SBCI' 'SUBI' 'ANDI' 'ORI' 'SBR' 'CBR' 'CPI'
#3         #| OP                    | D  D  D  D| OP        |'SER' 
#4         #| OP                       | D  D  D|OP| R  R  R|'MULSU' 'FMUL' 'FMULS' 'FMULSU'
#5         #| OP                    | D  D  D  D| R  R  R  R| 'MULS' 'MOVW'
#6         #| OP                    | K  K| D  D| K  K  K  K|'ADIW' 'SBIW' 
#7         #| OP                 | D  D  D  D  D| OP        |'INC' 'DEC'  'LSR' 'ROR' 'ASR' 'SWAP' 'POP' 'PUSH' 'LPMZ' 'LPMZ+' 'ST' 'COM' 'NEG' 'LDX' 'LDX+' 'LD-X' 'LDY' 'LDY+' 'LD-Y' 'LDZ' 'LD+Z' 'LD-Z' 'STX' 'STX+' 'ST-X' 'STY' 'STY+' 'ST-Y' 'STZ' 'STZ+' 'ST-Z' 'ELPM'
#8         #| OP              | D  D  D  D  D  D  D  D  D  D|'TST' 'LSL' 'ROL' 'CLR'
#9         #| OP                       | S  S  S|OP         |'BSET' 'BCLR'
#10        #| OP        | K  K  K  K  K  K  K  K  K  K  K  K|'RJMP' 'RCALL' 'LDI'
#11        #| OP                                            |'IJMP' 'ICALL' 'RET' 'RETI' 'SEC' 'CLC' 'SEN' 'CLN' 'SEZ' 'CLZ' 'SEI' 'CLI' 'SES' 'CLS' 'SEV' 'CLV' 'SET' 'CLT' 'SEH' 'CLH' 'NOP' 'SLEEP' 'WDR' 'BREAK' 'SPM' 'LPM'     
#12        #| OP                    | A  A  A  A  A| B  B  B|'SBIC' 'SBIS' 'SBI' CBI'
#13        #| OP              | K  K  K  K  K  K  K| S  S  S|'BRBS' 'BRBC'
#14        #| OP              | K  K  K  K  K  K  K|OP      |'BREQ' 'BRNE' 'BRCS' 'BRCC' 'BRSH' 'BRLO' 'BRMI' 'BRPL' 'BRGE' 'BRLT' 'BRHS' 'BRHC' 'BRTS' 'BRTC' 'BRVS' 'BRVC' 'BRIE' 'BRID'
#15        #| OP                 | D  D  D  D  D|OP| B  B  B|'BST' 'BLD' 
#16        #| OP           | A  A| R  R  R  R  R| A  A  A  A|'OUT' 'IN'
#17        #| OP  | q|OP| q  q|OP| D  D  D  D  D|OP| q  q  q|'LDDZ' 'LDDZ' 'STDY' 'STDZ'

#2line
#18         | OP                 | K  K  K  K  K|OP      | K| 'CALL' 'JMP' 
#           | K  K  K  K  K  K  K  K  K  K  K  K  K  K  K  K|
#19         | OP                 | D  D  D  D  D| OP        | 'STS' 'LDS'
#           | K  K  K  K  K  K  K  K  K  K  K  K  K  K  K  K|

#20        #| OP                 | D  D  D  D  D|OP| B  B  B| 'SBRC' 'SBRS'


MEMORY_INSTRUCTIONS = ['POP','PUSH','LDX','LDX+','LD-X','LDY','LDY+','LD-Y','LDZ','LD+Z','LD-Z','STX','STX+','ST-X','STY','STY+','ST-Y','STZ','STZ+','ST-Z']

TWO_CYCLE_INSRUCTIONS = ['CALL','JMP','LDS','STS']
 # I need to investigate the spm instruction


ARITHMETIC_LOGIC_INSTRUCTIONS = [
    'ADD', 'ADC', 'ADIW', 'SUB', 'SUBI', 'SBC', 'SBCI', 'SBIW',
    'AND', 'ANDI', 'OR', 'ORI', 'EOR', 'COM', 'NEG', 'INC', 'DEC',
    'MUL', 'MULS', 'MULSU', 'FMUL', 'FMULS', 'FMULSU', 'DES'
]

SHIFT_ROTATE_INSTRUCTIONS = [
    'LSR', 'ROR', 'ASR', 'SWAP'
]

DATA_TRANSFER_INSTRUCTIONS = [
    'MOV', 'MOVW', 'LDI', 'LDS', 
    'LDX', 'LDX+', 'LD-X', 
    'LDY', 'LDY+', 'LD-Y', 'LDDZ', 'LDDY',
    'LDZ', 'LDZ+', 'LD-Z', 'STDZ', 'STDY',
    'STS', 'STX', 'STX+', 'ST-X', 
    'STY', 'STY+', 'ST-Y', 'STZ', 'STZ+', 'ST-Z',
    'IN', 'OUT', 'PUSH', 'POP', 
    'LPM', 'LPMZ', 'LPMZ+', 
    'ELPM', 'ELPMZ', 'ELPMZ+', 
    'SPM', 'SPMX+'
]

BIT_BIT_TEST_INSTRUCTIONS = [
    'SBI', 'CBI', 'SBIC', 'SBIS', 'SBRC', 'SBRS', 'BST', 'BLD', 'BSET', 'BCLR'
]

# The 16 explicit Status Register (SREG) instructions mapped to hardware
SREG_INSTRUCTIONS = [
    'SEC', 'CLC', 'SEN', 'CLN', 'SEZ', 'CLZ', 'SEI', 'CLI',
    'SES', 'CLS', 'SEV', 'CLV', 'SET', 'CLT', 'SEH', 'CLH'
]

BRANCH_INSTRUCTIONS = [
    'RJMP', 'IJMP', 'EIJMP', 'JMP', 'RCALL', 'ICALL', 'EICALL', 'CALL', 
    'RET', 'RETI', 'CPSE', 'CP', 'CPC', 'CPI', 'BRBS', 'BRBC'
]

# The 16 conditional relative branch variants mapped to hardware
CONDITIONAL_BRANCH_INSTRUCTIONS = [
    'BREQ', 'BRNE', 'BRCS', 'BRCC', 'BRSH', 'BRLO', 'BRMI', 'BRPL',
    'BRGE', 'BRLT', 'BRHS', 'BRHC', 'BRTS', 'BRTC', 'BRVS', 'BRVC',
    'BRIE', 'BRID'
]

MCU_CONTROL_INSTRUCTIONS = [
    'NOP', 'SLEEP', 'WDR', 'BREAK', 'HALT'
]


ALL_AVR_INSTRUCTIONS = (
    ARITHMETIC_LOGIC_INSTRUCTIONS +
    SHIFT_ROTATE_INSTRUCTIONS +
    DATA_TRANSFER_INSTRUCTIONS +
    BIT_BIT_TEST_INSTRUCTIONS +
    SREG_INSTRUCTIONS +
    BRANCH_INSTRUCTIONS +
    CONDITIONAL_BRANCH_INSTRUCTIONS +
    MCU_CONTROL_INSTRUCTIONS
)


def ins_to_str(ins): # I am packing all the OP bits, keeping the order 

    mask_4   = 0b1111_0000_0000_0000 # used by LDI, RJMP
    mask_6   = 0b1111_1100_0000_0000 # used in ADD
    mask_8   = 0b1111_1110_0000_1000 # used in SBRC, SBRS
    mask_8b  = 0b1111_1111_0000_0000 # used in MULS
    mask_10  = 0b1111_1110_0000_1110 # used in JMP, CALL
    mask_10b = 0b1111_1111_1000_1000 # used in MULSU
    mask_11  = 0b1111_1110_0000_1111 # used in LDS, STS, DEC
    mask_13  = 0b1111_1111_1000_1111 # used in BSET
    
    
    match (ins):
        case 0b1001_0101_0001_1001: return 'ICALL'
        case 0b1001_0100_0001_1001: return 'IJMP'
        
    match (ins & mask_4):
        case 0b0111_0000_0000_0000: return 'ANDI'
        case 0b1110_0000_0000_0000: return 'LDI'
        case 0b1100_0000_0000_0000: return 'RJMP'
        
    match (ins & mask_6):
        case 0b0000_1100_0000_0000: return 'ADD'
        
    match (ins & mask_8):
        case 0b1111_1010_0000_0000: return 'BST'
        case 0b1111_1000_0000_0000: return 'BLD'
        case 0b1111_1100_0000_0000: return 'SBRC'
        case 0b1111_1110_0000_0000: return 'SBRS'
        
    match (ins & mask_8b):
        case 0b0000_0010_0000_0000: return 'MULS'
        
    match (ins & mask_10):
        case 0b1001_0100_0000_1100: return 'JMP'
        case 0b1001_0100_0000_1110: return 'CALL'
    
    match (ins & mask_10b):
        case 0b0000_0011_0000_0000: return 'MULSU'
        case 0b0000_0011_1000_0000: return 'FMULS'
        case 0b0000_0011_1000_1000: return 'FMULSU'
        
    
    match (ins & mask_11):
        case 0b1001_0000_0000_0000: return 'LDS'
        case 0b1001_0010_0000_0000: return 'STS'
        case 0b1001_0100_0000_1010: return 'DEC'
        case 0b1000_0010_0000_0000: return 'STZ'
        
        
    match (ins & mask_13):
        case 0b1001_0100_0000_1000: return 'BSET'
        case 0b1001_0100_1000_1000: return 'BCLR'
    

    OP1A8A13 = ins>>10 # for lines 1,8 and 13 of the table
    OP2A10 = ins>>12 # for lines 2 and 10 of the table
    OP3  = ((ins>>8)<<4)|(ins&0x0F)
    OP4  = ((ins>>7)<<1)|((ins>>3)&0x01)
    OP5A6A12 = (ins>>8) # for lines 5,6 and 12 of the table
    OP7  = ((ins>>9)<<4)|(ins&0xF)
    OP9  = ((ins>>7)<<4)|(ins&0x0F)
    OP11 = ins 
    OP14 = ((ins>>10)<<3)|(ins&0b111)
    OP15 = ((ins>>9)<<1)|(ins>>3&0b1)
    OP16 = (ins>>11)
    OP17 = ((ins>>3)&0b1)|(((ins>>9)&0b1)<<1)|(((ins>>12)&0b1)<<2)|((ins>>14)<<3)
    


    match OP17:
        case 0b10011: return 'STDY'
        case 0b10010: return 'STDZ'
        case 0b10000: return 'LDDZ'
        case 0b10001: return 'LDDY'

    match OP16:
        case 0b10110: return 'IN'
        case 0b10111: return 'OUT'
        

    match OP15:
        case 0b11111010: return 'BST'
        case 0b11111000: return 'BLD'

    match OP9: 
        case 0b1001010001000: return 'BSET'
        case 0b1001010011000: return 'BCLR'


    match OP5A6A12: 
        case 0b00000010: return 'MULS'
        case 0b00000001: return 'MOVW'
        case 0b10010110: return 'ADIW'
        case 0b10010111: return 'SBIW'
        case 0b10011001: return 'SBIC'
        case 0b10011010: return 'SBI'
        case 0b10011000: return 'CBI'
        case 0b10011011: return 'SBIS'

    match OP3:
        case 0b111011111111: return 'SER'

    match OP7:
        case 0b10010100001: return 'NEG'
        case 0b10010100000: return 'COM'
        case 0b10010100011: return 'INC'
        case 0b10010101010: return 'DEC'
        case 0b10010100110: return 'LSR'
        case 0b10010100111: return 'ROR'
        case 0b10010100101: return 'ASR'
        case 0b10010100010: return 'SWAP'
        case 0b10010001111: return 'POP'
        case 0b10010011111: return 'PUSH'

        #memory instructions
        
        case 0b10010001100: return 'LDX'
        case 0b10010001101: return 'LDX+'
        case 0b10010001110: return 'LD-X'
        case 0b10000001000: return 'LDY'
        case 0b10010001001: return 'LDY+'
        case 0b10010001010: return 'LD-Y'
        case 0b10000000000: return 'LDZ'
        case 0b10010000001: return 'LDZ+'
        case 0b10010000010: return 'LD-Z'

        case 0b10010011100: return 'STX'
        case 0b10010011101: return 'STX+'
        case 0b10010011110: return 'ST-X'
        case 0b10000011000: return 'STY'
        case 0b10010011001: return 'STY+'
        case 0b10010011010: return 'ST-Y'
        case 0b10000010000: return 'STZ'#STDZ but q=0
        case 0b10010010001: return 'STZ+'
        case 0b10010010010: return 'ST-Z'

#        case 0b10010000111: return 'ELPM'
        case 0b10010000100: return 'LPMZ'
        case 0b10010000101: return 'LPMZ+'



    match OP4:
        case 0b0000001100: return 'MULSU'
        case 0b0000001101: return 'FMUL'
        case 0b0000001110: return 'FMULS'
        case 0b0000001111: return 'FMULSU'


    match OP2A10:
        case 0b0100: return 'SBCI'
        case 0b0101: return 'SUBI'

        
        case 0b0110: return 'ORI' ##or SBR it is the same thing
        case 0b0011: return 'CPI'

        case 0b1100: return 'RJMP'
        case 0b1101: return 'RCALL'



    match OP1A8A13 :
        case 0b0000_10: return 'SBC'
        case 0b0000_11: return 'ADD' # Collision LSL
        case 0b0000_11: return 'LSL' # Collision ADD
        case 0b0001_01: return 'CP'
        case 0b0001_11: return 'ADC' # Collision ROL
        case 0b0001_11: return 'ROL' # Collision ADC
        case 0b0001_10: return 'SUB'
        case 0b0010_00: return 'AND' # Collision TST
        case 0b0010_00: return 'TST' # Collision AND
        case 0b0010_01: return 'EOR' # Collision CLR
        case 0b0010_01: return 'CLR' # Collision EOR
        case 0b0010_10: return 'OR'
        case 0b1001_11: return 'MUL'
        case 0b0000_01: return 'CPC'
        case 0b0010_11: return 'MOV'
        
        
        case 0b111100: return 'BRBS'
        case 0b111101: return 'BRBC'
        case 0b000100: return 'CPSE'

    match OP14:
        case 0b111100001: return 'BREQ'
        case 0b111101001: return 'BRNE' 
        case 0b111100000: return 'BRCS' #or BRLO
        case 0b111101000: return 'BRSH' #or BRCC
        case 0b111100010: return 'BRMI'
        case 0b111101010: return 'BRPL'
        case 0b111101100: return 'BRGE'
        case 0b111100100: return 'BRLT'
        case 0b111100101: return 'BRHS'
        case 0b111101101: return 'BRHC'
        case 0b111100110: return 'BRTS'
        case 0b111101110: return 'BRTC'
        case 0b111100011: return 'BRVS'
        case 0b111101011: return 'BRVC'
        case 0b111100111: return 'BRIE'
        case 0b111101111: return 'BRID'  
    
    match OP11:
        ## These instructions are use less at harware level because they default to BSET or BCLR
        case 0b1001010000001000: return 'SEC'
        case 0b1001010010001000: return 'CLC'
        case 0b1001010000101000: return 'SEN'
        case 0b1001010010101000: return 'CLN'
        case 0b1001010000011000: return 'SEZ'
        case 0b1001010010011000: return 'CLZ'
        case 0b1001010001111000: return 'SEI'
        case 0b1001010011111000: return 'CLI'
        case 0b1001010001001000: return 'SES'
        case 0b1001010011001000: return 'CLS'
        case 0b1001010000111000: return 'SEV'
        case 0b1001010010111000: return 'CLV'
        case 0b1001010001101000: return 'SET'
        case 0b1001010011101000: return 'CLT'
        case 0b1001010001011000: return 'SEH'
        case 0b1001010011011000: return 'CLH'
        ##
        case 0x0: return 'NOP'
        case 0b1001010110001000: return 'SLEEP'
        case 0b1001010110101000: return 'WDR'
        case 0b1001010110011000: return 'BREAK'
                
        case 0b1001010100001000: return 'RET'
        case 0b1001010100011000: return 'RETI'
        case 0b1001010111101000: return'SPM'
        case 0b1001010111001000: return 'LPM'


    return 'invalid'


def str_to_code(instruction_str):
    """
    Takes an instruction string (e.g., returned from ins_to_str) 
    and returns its uniquely assigned decimal code.
    Returns 0 if the instruction is invalid or not found.
    """
    op_codes = {
        # Arithmetic and Logic
        'ADD': 1, 'ADC': 2, 'ADIW': 3, 'SUB': 4, 'SUBI': 5, 'SBC': 6, 'SBCI': 7, 'SBIW': 8,
        'AND': 9, 'ANDI': 10, 'OR': 11, 'ORI': 12, 'EOR': 13, 'COM': 14, 'NEG': 15,
        'SBR': 16, 'CBR': 17, 'INC': 18, 'DEC': 19, 'TST': 20, 'CLR': 21, 'SER': 22,
        
        # Multipliers
        'MUL': 23, 'MULS': 24, 'MULSU': 25, 'FMUL': 26, 'FMULS': 27, 'FMULSU': 28,
        
        # Branch Instructions
        'RJMP': 29, 'IJMP': 30, 'JMP': 31, 'RCALL': 32, 'ICALL': 33, 'CALL': 34,
        'RET': 35, 'RETI': 36, 'CPSE': 37, 'CP': 38, 'CPC': 39, 'CPI': 40,
        'SBRC': 41, 'SBRS': 42, 'SBIC': 43, 'SBIS': 44, 
        'BRBS': 45, 'BRBC': 46, 'BREQ': 47, 'BRNE': 48, 'BRCS': 49, 'BRCC': 50, 
        'BRSH': 51, 'BRLO': 52, 'BRMI': 53, 'BRPL': 54, 'BRGE': 55, 'BRLT': 56, 
        'BRHS': 57, 'BRHC': 58, 'BRTS': 59, 'BRTC': 60, 'BRVS': 61, 'BRVC': 62, 
        'BRIE': 63, 'BRID': 64,
        
        # Bit and Bit-Test Instructions
        'SBI': 65, 'CBI': 66, 'LSL': 67, 'LSR': 68, 'ROL': 69, 'ROR': 70, 'ASR': 71,
        'SWAP': 72, 'BSET': 73, 'BCLR': 74, 'BST': 75, 'BLD': 76,
        'SEC': 77, 'CLC': 78, 'SEN': 79, 'CLN': 80, 'SEZ': 81, 'CLZ': 82, 
        'SEI': 83, 'CLI': 84, 'SES': 85, 'CLS': 86, 'SEV': 87, 'CLV': 88, 
        'SET': 89, 'CLT': 90, 'SEH': 91, 'CLH': 92,
        
        # Data Transfer Instructions
        'MOV': 93, 'MOVW': 94, 'LDI': 95,
        
        # Memory Transfers (Mapped exactly to your ins_to_str string outputs)
        'LDX': 96,  'LDX+': 97,  'LD-X': 98, 
        'LDY': 99,  'LDY+': 100, 'LD-Y': 101, 'LDDY': 102,
        'LDZ': 103, 'LDZ+': 104, 'LD-Z': 105, 'LDDZ': 106, 
        'LDS': 107,
        
        'STX': 108, 'STX+': 109, 'ST-X': 110, 
        'STY': 111, 'STY+': 112, 'ST-Y': 113, 'STDY': 114,
        'STZ': 115, 'STZ+': 116, 'ST-Z': 117, 'STDZ': 118, 
        'STS': 119,
        
        'LPM': 120, 'LPMZ': 121, 'LPMZ+': 122, 'SPM': 123,
        
        # I/O and Stack
        'IN': 124, 'OUT': 125, 'PUSH': 126, 'POP': 127,
        
        # MCU Control
        'NOP': 128, 'SLEEP': 129, 'WDR': 130, 'BREAK': 131
    }
    
    return op_codes.get(instruction_str, 0) # 0 maps to Idle/Invalid instruction




    