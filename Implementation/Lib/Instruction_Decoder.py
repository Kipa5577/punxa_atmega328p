#number of instructions 131

#Instructions in the data sheet 131
#Acounted for 131
#Decoded by the function 131 
#Instructions found in test 98 + CBR + BRLO + BRCC + SBR + TST +CLR +LPM+ 16(for the SREG clear and set instructions) Total: 122 ,missing 9 instructions


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


 # I need to investigate the spm instruction

def ins_to_str(ins): # I am packing all the OP bits, keeping the order 
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
    OP18 = (ins>>1&0b111)|((ins>>9)<<3) 
    OP19 = (ins&0b1111)|((ins>>9)<<4)
    OP20 = ((ins>>3)&0b1)|((ins>>10)<<1)

    match OP20:
        case 0b11111100: 'SBRC'
        case 0b11111110: 'SBRS'
    
    match OP19: 
        case 0b10010000000: return 'LDS'
        case 0b10010010000: return 'STS'

    match OP18:
        
        case 0b1001010111: return 'CALL'
        case 0b1001010110: return 'JMP'


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
        case 0b10000010000: return 'STZ'
        case 0b10010010001: return 'STZ+'
        case 0b10010010010: return 'ST-Z'

        case 0b10010000111: return 'ELPM'
        case 0b10010000100: return 'LPMZ'
        case 0b10010000101: return 'LPMZ+'



    match OP4:
        case 0b0000001100: return 'MULSU'
        case 0b0000001101: return 'FMUL'
        case 0b0000001110: return 'FMULS'
        case 0b0000001111: return 'FMULSU'

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


    match OP2A10:
        case 0b0100: return 'SBCI'
        case 0b0101: return 'SUBI'

        case 0b0111: return 'ANDI' ##or CBR it is the same thing
        case 0b0110: return 'ORI' ##or SBR it is the same thing
        case 0b0011: return 'CPI'

        case 0b1100: return 'RJMP'
        case 0b1101: return 'RCALL'
        case 0b1110: return 'LDI'


    match OP1A8A13 :
        case 0b000011: return 'ADD'
        case 0b000111: return 'ADC'
        case 0b000110: return 'SUB'
        case 0b000010: return 'SBC'
        case 0b001000: return 'AND'
        case 0b001010: return 'OR'
        case 0b001001: return 'EOR'
        case 0b001000: return 'TST'
        case 0b100111: return 'MUL'
        case 0b000101: return 'CP'
        case 0b000001: return 'CPC'
        case 0b001011: return 'MOV'
        
        case 0b000011: return 'LSL'
        case 0b000111: return 'ROL'
        case 0b001001: return 'CLR'

        case 0b111100: return 'BRBS'
        case 0b111101: return 'BRBC'
        case 0b000100: return 'CPSE'

    
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
        case 0b1001010000001001: return 'IJMP'
        case 0b1001010100001001: return 'ICALL'
        case 0b1001010100001000: return 'RET'
        case 0b1001010100011000: return 'RETI'
        case 0b1001010111101000: return'SPM'
        case 0b1001010111001000: return 'LPM'


    return 'invalid'







    