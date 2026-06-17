# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 16:21:50 2026

@author: dcr
"""

import re

def split_parts(s):
    parts = re.split('[, ()]', s)
    ret = []
    
    for part in parts:
        if len(part)>0:
            ret.append(part)
            
    return ret

def reg_to_index(reg):
    reg = reg.lower()
    if (reg[0] == 'r'): return int(reg[1:])
    raise Exception(f'unknown register {reg}')
    
def get_int(v):
    if (isinstance(v, int)):
        return v
    if (isinstance(v, str)):
        if (v[0:2] == '0x'):
            return int(v, 16)
        else:
            return int(v)
    
def parts_to_ins(parts):
    
    op = parts[0].upper()
    
    
    if (op == 'ADD'):
        # ADD Rd, Rr -> 0000 11rd dddd rrrr
        p0 = 0b0000
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'ADC'):
        # ADC Rd, Rr -> 0001 11rd dddd rrrr
        p0 = 0b0001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'ADIW'):
        # ADIW Rd, K -> 1001 0110 KKdd KKKK
        p0 = 0b1001
        p1 = 0b0110
        r = (reg_to_index(parts[1]) - 24) // 2
        k = get_int(parts[2])
        p2 = ((k >> 4) << 2) | (r)
        p3 = (k & 0xF)
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'AND'):
        # AND Rd, Rr -> 0010 00rd dddd rrrr
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b0000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'ANDI'):
        # ANDI Rd, K -> 0111 KKKK dddd KKKK
        Rd = reg_to_index(parts[1])
        assert(Rd >= 16)
        K = get_int(parts[2])
        p1 = (K >> 4) & 0xF
        p2 = (Rd - 16) & 0xF
        p3 = K & 0xF
        return [0b0111_0000_0000_0000 | (p1 << 8) | (p2 << 4) | p3 ]
    
    elif (op == 'ASR'):
        # ASR Rd -> 1001 010d dddd 0101
        p0 = 0b1001
        Rd = reg_to_index(parts[1])
        p1 = 0b0100 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0b0101
        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
        
    elif (op == 'BCLR'):
        # BCLR s -> 1001 0100 1sss 1000
        p0 = 0b1001
        s = get_int(parts[1])
        p1 = 0b0100 
        p2 = 0b1000 | s
        p3 = 0b1000
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BLD'):
        # BLD Rd, b -> 1111 100d dddd 0bbb
        p0 = 0b1111
        Rd = reg_to_index(parts[1])
        b = get_int(parts[2])
        p1 = 0b1000 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = b & 0x7
        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRBC'):
        # BRBC s, k -> 1111 01kk kkkk ksss
        p0 = 0b1111
        k = get_int(parts[2])
        s = get_int(parts[1])
        assert (s >= 0) and (s <= 7)
        p1 = 0b0100  | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | s
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRBS'):
        # BRBS s, k -> 1111 00kk kkkk ksss
        p0 = 0b1111
        k = get_int(parts[2])
        s = get_int(parts[1])
        assert (s >= 0) and (s <= 7)
        p1 = 0b0000  | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | s
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRCC'):
        # BRCC k -> 1111 01kk kkkk k000
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = (1 << 2) | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRCS'):
        # BRCS k -> 1111 00kk kkkk k000
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BREAK'):
        # BREAK -> 1001 0101 1001 1000
        return [0b1001_0101_1001_1000]
    
    elif (op == 'BREQ'):
        # BREQ k -> 1111 00kk kkkk k001
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 1
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRGE'):
        # BRGE k -> 1111 01kk kkkk k100
        k = get_int(parts[1]) & 0x7F
        return [ 0b1111_0100_0000_0100 | (k<<3)]
    
    elif (op == 'BRHC'):
        # BRHC k -> 1111 01kk kkkk k101
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b101
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRHS'):
        # BRHS -> 1111 00kk kkkk k101
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0000 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b101
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRID'):
        # BRID k -> 1111 01kk kkkk k111
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRIE'):
        # BRIE k -> 1111 00kk kkkk k111 
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0000 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRLO'):
        # BRLO k -> 1111 00kk kkkk k000
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b000
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRLT'):
        # BRLT k -> 1111 00kk kkkk k100
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b100
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRMI'):
        # BRMI k -> 1111 00kk kkkk k010
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b010
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRNE'):
        # BRNE k -> 1111 01kk kkkk k001
        # psuedo instruction (BRBC 1, k)
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 1
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRPL'):
        # BRPL k -> 1111 01kk kkkk k010
        # pseudo instruction (BRBC 2, k)
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = (1 << 2) | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b010
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRTC'):
        # BRTC k → 1111 01kk kkkk k110
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b110
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRTS'):
        # BRTS k -> 1111 00kk kkkk k110
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0000 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b110
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRSH'):
        # BRSH k -> 1111 01kk kkkk k000
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b000
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRVC'):
        # BRVC k -> 1111 01kk kkkk k011
        # pseudo instruction (BRBC 3, k)
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = (1 << 2) | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b011
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRVS'):
        # BRVS k -> 1111 00kk kkkk k011
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b011
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BSET'):
        # BSET s -> 1001 0100 0sss 1000
        p0 = 0b1001
        s = get_int(parts[1])
        p1 = 0b0100 
        p2 = 0b0000 | s
        p3 = 0b1000
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BST'):
        # BST Rr, b -> 1111 101r rrrr 0bbb
        p0 = 0b1111
        Rr = reg_to_index(parts[1])
        b = get_int(parts[2])
        p1 = 0b1010 | (Rr>>4)
        p2 = Rr & 0xF
        p3 = b & 0x7
        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CALL'):
        # CALL k -> 1001 010k kkkk 111k kkkk kkkk kkkk kkkk
        p0 = 0b1001
        k = get_int(parts[1])
        p1 = 0b0100 | (k >> 21)
        p2 = (k >> 17) & 0xF
        p3 = 0b1110 | ((k >> 16) & 1)
        w = k & 0xFFFF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) , w]
        
    elif (op == 'CBI'):
        # CBI A, b -> 1001 1000 AAAA Abbb
        p0 = 0b1001
        A = get_int(parts[1])
        b = get_int(parts[2])
        assert (A >= 0) and (A <= 0x1F)
        assert (b >= 0) and (b <= 7)
        p1 = 0b1000 
        p2 = A >> 1
        p3 = ((A & 1) << 3) | b
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'CBR'):
        # CBR Rd, K -> 0111 KKKK dddd KKKK
        p0 = 0b0111
        r = reg_to_index(parts[1])
        k = get_int(parts[2])
        k = 0xff - k
        p1 = k >> 4
        assert(r >= 16)
        p2 = r - 16
        p3 = k & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CLC'):
        # CLC -> 1001 0100 1000 1000
        return [ 0b1001_0100_1000_1000]
        
    elif (op == 'CLH'):
        # CLH -> 1001 0100 1101 1000
        return [0b1001_0100_1101_1000]
    
    elif (op == 'CLI'):
        # CLI -> 1001 0100 1111 1000
        return [0b1001_0100_1111_1000]
    
    elif (op == 'CLR'):
        p0 = 0b0010
        r =  reg_to_index(parts[1]) 
    
        p1 = (1<<2) | ((r >> 4) << 1) | (r>>4)
        p2 = (r & 0xF)
        p3 = (r & 0xF)
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CLN'):
        # CLN -> 1001 0100 1011 1000
        return [0b1001_0100_1011_1000]
    
    elif (op == 'CLT'):
        # CLT -> 1001 0100 1110 1000
        # Pseudo-instruction (BCLR 6)
        return [ 0b1001_0100_1110_1000]
    
    elif (op == 'CLV'):
        # CLV -> 1001 0100 1010 1000
        return [0b1001_0100_1010_1000]
    
    elif (op == 'CLZ'):
        # CLZ -> 1001 0100 1001 1000
        return [0b1001_0100_1001_1000]
    
    elif (op == 'COM'):
        # COM Rd → 1001 010d dddd 0000
        p0 = 0b1001
        Rd = reg_to_index(parts[1])
        p1 = 0b0100 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CP'):
        # CP Rd, Rr -> 0001 01rd dddd rrrr
        p0 = 0b0001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b0100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CPI'):
        # CPI Rd, k -> 0011 KKKK dddd KKKK
        p0 = 0b0011
        r = reg_to_index(parts[1])
        k = get_int(parts[2])
        p1 = k >> 4
        assert(r >= 16)
        p2 = r - 16
        p3 = k & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CPSE'):
        # CPSE Rd, Rr -> 0001 00rd dddd rrrr
        Rd =  reg_to_index(parts[1]) 
        Rr =  reg_to_index(parts[1]) 
        p1 = ((Rr >> 4) << 1) | (Rd>>4)
        p2 = (Rd & 0xF)
        p3 = (Rr & 0xF)
        return [0b0001_0000_0000_0000 | (p1 << 8) | (p2 << 4) | p3 ]
    
    elif (op == 'DEC'):
        # DEC Rd --> 1001 010d dddd 1010.
        p0 = 0b1001
        Rd =  reg_to_index(parts[1]) 
        p1 = 0b0100 | (Rd >> 4)
        p2 = Rd & 0xF
        p3 = 0b1010
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'EOR'):
        # EOR Rd, Rr -> 0010 01rd dddd rrrr
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b0100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF    
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'FMUL'):
        # FMUL Rd, Rr -> 0000 0011 0ddd 1rrr
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        assert (Rd >= 16) and (Rd <= 23)
        assert (Rr >= 16) and (Rr <= 23)        
        return [0b0000_0011_0000_1000 | (Rd << 4) | (Rr)]
        
    elif (op == 'FMULS'):
        # FMULS Rd, Rr -> 0000 0011 1ddd 0rrr
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        assert (Rd >= 16) and (Rd <= 23)
        assert (Rr >= 16) and (Rr <= 23)        
        return [0b0000_0011_1000_0000 | (Rd << 4) | (Rr)]
    
    elif (op == 'FMULSU'):
        # FMULSU Rd, Rr -> 0000 0011 1ddd 1rrr
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        assert (Rd >= 16) and (Rd <= 23)
        assert (Rr >= 16) and (Rr <= 23)        
        return [0b0000_0011_1000_1000 | (Rd << 4) | (Rr)]
    
    elif (op == 'ICALL'):
        # ICALL-> 1001 0101 0001 1001
        return [0b1001_0101_0001_1001]
    
    elif (op == 'IJMP'):
        # IJMP -> 1001 0100 0001 1001
        return [0b1001_0100_0001_1001]
    
    elif (op == 'IN'):
        # IN Rd, A -> 1011 0AAd dddd AAAA
        p0 = 0b1011
        Rd = reg_to_index(parts[1]) 
        A = get_int(parts[2])
        p1 = (A >> 4) << 1 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = A & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'INC'):
        # INC Rd --> 1001 010d dddd 0011.
        p0 = 0b1001
        Rd =  reg_to_index(parts[1]) 
        p1 = 0b0100 | (Rd >> 4)
        p2 = Rd & 0xF
        p3 = 0b0011
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
        
    elif (op == 'JMP'):
        # JMP k -> 1001 010k kkkk 110k kkkk kkkk kkkk kkkk
        p0 = 0b1001
        k = get_int(parts[1])
        p1 = 0b0100 | (k >> 21)
        p2 = (k >> 17) & 0xF
        p3 = 0b1100 | ((k >> 16) & 1)
        w = k & 0xFFFF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) , w]
        
    elif (op == 'LD'):
        # LD Rd, mode -> 1001 000d dddd 1100
        # ST mode, r -> 10qi qq1r rrrr pqqq
        r = reg_to_index(parts[1])
        mode = parts[2].strip().upper()
        
        if   (mode == 'X'):  m1, m2 = 1, 0b1100
        elif (mode == 'X+'): m1, m2 = 1, 0b1101
        elif (mode == '-X'): m1, m2 = 1, 0b1110
        elif (mode == 'Y'):  m1, m2 = 0, 0b1000
        elif (mode == 'Y+'): m1, m2 = 1, 0b1001
        elif (mode == '-Y'): m1, m2 = 1, 0b1010
        elif (mode == 'Z'):  m1, m2 = 0, 0b0000
        elif (mode == 'Z+'): m1, m2 = 1, 0b0001
        elif (mode == '-Z'): m1, m2 = 1, 0b0010
        else: raise Exception(f'Not supported yet= {mode}')
            
        p0 = 0b1000 | m1
        p1 = 0b0000 | (r>>4)
        p2 = r & 0xF
        p3 = m2
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
    
    elif (op == 'LDI'):
        # LDI Rd, K -> 1110 KKKK dddd KKKK
        p0 = 0b1110
        r = reg_to_index(parts[1]) 
        assert(r >= 16)
        off = get_int(parts[2]) & 0xFF
        p1 = off >> 4
        p2 = (r - 16) 
        p3 = off & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'LDS'):
        p0 = 0b1001
        r = reg_to_index(parts[1])
        p1 = 0b0000 | (r >> 4)
        p2 = r & 0xF
        p3 = 0
        w1 = get_int(parts[2]) >> 8
        w2 = get_int(parts[2]) & 0xFF
        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) , ((w1 << 8) | w2 )]
    
    elif (op == 'LSL'):
        # LSL Rd -> 1001 010d dddd 0011
        # Pseudo instruction (ADD Rd, Rd)
        p0 = 0b0000
        Rd = reg_to_index(parts[1])
        p1 = 0b1100 | ((Rd >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rd & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'LSR'):
        # LSR Rd -> 1001 010d dddd 0110
        p0 = 0b1001
        r = reg_to_index(parts[1])
        p1 = 0b0100 | (r >> 4)
        p2 = r & 0xF
        p3 = 0b0110
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
    
    
    elif (op == 'MOV'):
        # MOV Rd, Rr -> 0010 11rd dddd rrrr
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'MOVW'):
        # MOVW Rd, Rr -> 0000 0001 dddd rrrr
        p0 = 0b0000
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b0001 
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'MUL'):
        # MUL Rd, Rr -> 1001 11rd dddd rrrr
        p0 = 0b1001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'MULS'):
        # MULS Rd, Rr -> 0000 0010 dddd rrrr
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        assert (Rd >= 16) and (Rd <= 31)
        assert (Rr >= 16) and (Rr <= 31)        
        return [0b0000_0010_0000_0000 | ((Rd & 0xF) << 4) | (Rr & 0xF)]
    
    elif (op == 'MULSU'):
        # MULSU Rd, Rr -> 0000 0011 0ddd 0rrr
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        assert (Rd >= 16) and (Rd <= 23)
        assert (Rr >= 16) and (Rr <= 23)        
        return [0b0000_0011_0000_0000 | ((Rd & 0b111) << 4) | (Rr & 0b111)]
    
    elif (op == 'NEG'):
        # NEG Rd -> 1001 010d dddd 0001
        p0 = 0b1001
        r = reg_to_index(parts[1])
        p1 = 0b0100 | (r >> 4)
        p2 = r & 0xF
        p3 = 0b0001
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
    
    elif (op == 'NOP'):
        # NOP -> 0000 0000 0000 0000
        return [0b0000_0000_0000_0000]
    
    elif (op == 'OR'):
        # OR Rd, Rr -> 0010 10rd dddd rrrr
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'ORI'):
        # ORI Rd, K -> 0110 KKKK dddd KKKK
        p0 = 0b0110
        r = reg_to_index(parts[1]) 
        off = get_int(parts[2]) & 0xFF
        p1 = off >> 4
        p2 = (r - 16) 
        p3 = off & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'OUT'):
        p0 = 0b1011
        r = reg_to_index(parts[2])
        A = get_int(parts[1])
        p1 = (1 << 3) | (A >> 4) << 1 | (r >> 4)
        p2 = r & 0XF
        p3 = A & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'POP'):
        # POP Rd → 1001 000d dddd 1111
        p0 = 0b1001
        Rd = reg_to_index(parts[1])        
        p1 = 0b0000 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0b1111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'PUSH'):
        # PUSH Rr → 1001 001d dddd 1111
        p0 = 0b1001
        Rd = reg_to_index(parts[1])        
        p1 = 0b0010 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0b1111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
        
    elif (op == 'RCALL'):
        # RCALl k -> 1101 kkkk kkkk kkkk
        ip1 = get_int(parts[1])
        return [0b1101_0000_0000_0000 | (ip1 & 0xFFF)]
        
    
    elif (op == 'RET'):
        return [0b1001_0101_0000_1000]
    
    elif (op == 'RETI'):
        # RETI -> 1001 0101 0001 1000
        return [0b1001_0101_0001_1000]
    
    elif (op == 'RJMP'):
        # RJMP k → 1100 kkkk kkkk kkkk
        p0 = 0b1100
        off = get_int(parts[1]) 
        
        return [(p0 << 12) | (off & 0xFFF) ]
    
    elif (op == 'ROL'):
        # ROL Rd -> 0001 11rd dddd rrrr
        # Pseudo instruction (ADC Rd, Rd)
        p0 = 0b0001
        Rd = reg_to_index(parts[1])        
        p1 = 0b1100 | ((Rd >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rd & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'ROR'):
        # ROR Rd -> 1001 010d dddd 0111
        p0 = 0b1001
        Rd = reg_to_index(parts[1])        
        p1 = 0b0100 |  (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0b0111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBC'):
        # SBC Rd, Rr -> 0000 10rd dddd rrrr
        p0 = 0b0000
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBCI'):
        # SBCI Rd, K -> 0100 KKKK dddd KKKK
        p0 = 0b0100
        Rd = reg_to_index(parts[1]) - 16
        K = get_int(parts[2])
        p1 = (K >> 4)
        p2 = Rd
        p3 = K & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBI'):
        # SBI A, b -> 1001 1010 AAAA Abbb
        p0 = 0b1001
        A = get_int(parts[1])
        b = get_int(parts[2])
        assert (A >= 0) and (A <= 0x1F)
        assert (b >= 0) and (b <= 7)
        p1 = 0b1010 
        p2 = A >> 1
        p3 = ((A & 1) << 3) | b        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
        
    elif (op == 'SBIC'):
        # SBIC A, b -> 1001 1001 AAAAA bbb
        p0 = 0b1001
        A = get_int(parts[1])
        b = get_int(parts[2])
        assert (A >= 0) and (A <= 0x1F)
        assert (b >= 0) and (b <= 7)
        p1 = 0b1001 
        p2 = A >> 1
        p3 = ((A & 1) << 3) | b        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBIS'):
        # SBIS A, b -> 1001 1011 AAAA Abbb
        p0 = 0b1001
        A = get_int(parts[1])
        b = get_int(parts[2])
        assert (A >= 0) and (A <= 0x1F)
        assert (b >= 0) and (b <= 7)
        p1 = 0b1011 
        p2 = A >> 1
        p3 = ((A & 1) << 3) | b        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'SBIW'):
        # SBIW Rd, K -> 1001 0111 KKdd KKKK
        p0 = 0b1001
        p1 = 0b0111
        r = (reg_to_index(parts[1]) - 24) // 2
        k = get_int(parts[2])
        p2 = ((k >> 4) << 2) | (r)
        p3 = (k & 0xF)
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBR'):
        # SBR Rd, K -> 0110 KKKK dddd KKKK
        # Pseudo-Instruction (ORI Rd, K)
        p0 = 0b0110
        r = reg_to_index(parts[1]) 
        off = get_int(parts[2]) & 0xFF
        p1 = off >> 4
        p2 = (r - 16) 
        p3 = off & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBRC'):
        # SBRC Rd, b -> 1111 110r rrrr 0bbb
        p0 = 0b1111
        r = reg_to_index(parts[1])
        p1 = 0b1100 | (r >> 4)
        p2 = r & 0xF
        p3 = get_int(parts[2])
        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'SBRS'):
        # SBRS Rd, b -> 1111 111r rrrr 0bbb
        p0 = 0b1111
        r = reg_to_index(parts[1])
        p1 = 0b1110 | (r >> 4)
        p2 = r & 0xF
        p3 = get_int(parts[2])
        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SEC'):
        # SEC -> 1001 0100 0000 1000
        return [0b1001_0100_0000_1000]
    
    elif (op == 'SEH'):
        # SEH -> 1001 0100 0101 1000
        return [0b1001_0100_0101_1000]
    
    elif (op == 'SEI'):
        # SEI → 1001 0100 0111 1000
        return [0b1001_0100_0111_1000]
    
    elif (op == 'SEN'):
        # SEN -> 1001 0100 0011 1000
        return [0b1001_0100_0011_1000]
    
    elif (op == 'SET'):
        # SET -> 1001 0100 0110 1000
        return [0b1001_0100_0110_1000]
    
    elif (op == 'SEV'):
        # SEV -> 1001 0100 0011 1000
        return [0b1001_0100_0011_1000]
    
    elif (op == 'SEZ'):
        # SEZ -> 1001 0100 0001 1000
        return [0b1001_0100_0001_1000]
    
    elif (op == 'SLEEP'):
        # SLEEP -> 1001 0101 1000 1000
        return [0b1001_0101_1000_1000]
    
    elif (op == 'ST'):
        # ST mode, r -> 10qi qq1r rrrr pqqq
        mode = parts[1].strip().upper()
        r = reg_to_index(parts[2])
        if   (mode == 'X'):  m1, m2 = 1, 0b1100
        elif (mode == 'X+'): m1, m2 = 1, 0b1101
        elif (mode == '-X'): m1, m2 = 1, 0b1110
        elif (mode == 'Y'):  m1, m2 = 0, 0b1000
        elif (mode == 'Y+'): m1, m2 = 1, 0b1001
        elif (mode == '-Y'): m1, m2 = 1, 0b1010
        elif (mode == 'Z'):  m1, m2 = 0, 0b0000
        elif (mode == 'Z+'): m1, m2 = 1, 0b0001
        elif (mode == '-Z'): m1, m2 = 1, 0b0010
        else: raise Exception(f'Not supported yet= {mode}')
            
        p0 = 0b1000 | m1
        p1 = 0b0010 | (r>>4)
        p2 = r & 0xF
        p3 = m2
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
        
    elif (op == 'STS'):
        # STS k, Rr -> 1001 001d dddd 0000 kkkk kkkk kkkk kkkk
        p0 = 0b1001
        r = reg_to_index(parts[2])
        p1 = 0b0010 | (r >> 4)
        p2 = r & 0xF
        p3 = 0
        w = get_int(parts[1])  & 0xFFFF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) , w]
    
    elif (op == 'SUB'):
        # SUB Rd, Rr -> 0001 10rd dddd rrrr
        p0 = 0b0001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SUBI'):
        # SUBI Rd, K -> 0101 KKKK dddd KKKK
        p0 = 0b0101
        r = reg_to_index(parts[1]) 
        assert (r >= 16)
        off = get_int(parts[2]) & 0xFF
        p1 = off >> 4
        p2 = (r - 16) 
        p3 = off & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'TST'):
        # TST Rd → 0010 00dd dddd dddd 
        # Pseudo instruction (AND Rd, Rd)
        # AND Rd, Rr -> 0010 00rd dddd rrrr
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        p1 = 0b0000 | ((Rd >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rd & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'WDR'):
        # WDR -> 1001 0101 1010 1000
        return [0b1001_0101_1010_1000]
    
    else:
        raise Exception(f'{op} not supported')
    
    return
    
def assemble(asm):
    ret = 0
    
    try:
        ret = parts_to_ins(split_parts(asm))
    except Exception as e:
        raise Exception(f'Failed to assemble "{asm}"') from e
    
    return ret 

def is_relative_jump(asm):
    parts = split_parts(asm.upper())
    
    if (parts[0] == 'RCALL'): return True
    if (parts[0] == 'RJMP'): return True    
    if (parts[0] == 'BRBC'): return True
    if (parts[0] == 'BRBS'): return True
    if (parts[0] == 'BRCC'): return True
    if (parts[0] == 'BRCS'): return True
    if (parts[0] == 'BRSH'): return True
    if (parts[0] == 'BRLO'): return True
    if (parts[0] == 'BREQ'): return True
    if (parts[0] == 'BRGE'): return True
    if (parts[0] == 'BRLT'): return True
    if (parts[0] == 'BRNE'): return True
    return False

def is_valid_relative(asm, delta):
    parts = split_parts(asm.upper())
    
    valid12 = (delta <= 2047 ) and (delta >= -2048)
    valid7 = (delta <= 63 ) and (delta >= -64)
    
    if (parts[0] == 'RCALL'): return valid12
    if (parts[0] == 'RJMP'): return valid12
    if (parts[0] == 'BRBC'): return valid7
    if (parts[0] == 'BRBS'): return valid7
    if (parts[0] == 'BRCC'): return valid7
    if (parts[0] == 'BRCS'): return valid7
    if (parts[0] == 'BRSH'): return valid7
    if (parts[0] == 'BRLO'): return valid7
    if (parts[0] == 'BREQ'): return valid7
    if (parts[0] == 'BRGE'): return valid7
    if (parts[0] == 'BRLT'): return valid7
    if (parts[0] == 'BRNE'): return valid7
    
    return False



def expand_macros(line):
    """
    Expand macros like high(expr) and low(expr) where expr is already
    a resolved numeric value.
    Supports:
      high(N)  -> (N >> 8) & 0xFF
      low(N)   -> N & 0xFF
    """
    if ('high(' in line):
        sm = line.find('high(')
        tm = line.find(')', sm)
        macro = line[sm:tm+1]
        value = get_int(macro[5:-1])
        return line.replace(macro, hex(value >> 8))
    elif ('low(' in line):
        sm = line.find('low(')
        tm = line.find(')', sm)
        macro = line[sm:tm+1]
        value = get_int(macro[4:-1])
        return line.replace(macro, hex(value & 0xFF))
    else:
        return line

def get_line_tokens(line):
    import io
    import tokenize
    stream = io.StringIO(line)
    tokens = list(tokenize.generate_tokens(stream.readline))
    return [tok.string for tok in tokens if tok.type == 1]

def assemble_program(program, debug=False):
    """
    Assemble an Assembly Program.
    The assembler supports labels

    Parameters
    ----------
    program : TYPE
        DESCRIPTION.
    debug : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    ret : TYPE
        DESCRIPTION.
    label_address : TYPE
        DESCRIPTION.

    Raises
    ------
    Exception
        DESCRIPTION.
    """
    
    
    ret = []
    
    labels = []
    lines = []
    
    # Step 1: remove empty lines and comments and collect labels
    for line in program.split('\n'):
        if (';' in line):
            line = line.split(';')[0]
            
        line = line.strip()
        
        if (len(line) == 0):
            # skip empty lines
            continue
        
        if (':' in line):
            pos = line.find(':')
            label = line[:pos]
            labels.append(label)
            lines.append(f'{label}:')
            line = line[pos+1:].strip()
            if (len(line) == 0):
                # if no instruction in the same line we are done
                continue
            
        lines.append(line)
        
    print('LABELS:', labels)
        
    # Step 2: assemble substituting labels for zeros to compute label addresses 
    # also process definifions
    off = 0 
    label_address = {}
    
    for line in lines:
        if (line[-1] == ':'):
            label = line[:-1]
            label_address[label] = off
        elif ('.equ' in line.lower()):
            parts = line[5:].split('=')
            label = parts[0].strip()
            v = get_int(parts[1].strip())
            labels.append(label)
            label_address[label] = v
        else:
            # substitute the labels
            for label in labels:
                tokens = get_line_tokens(line)
                if (label in tokens):
                    line = line.replace(label, '0')
                
            line = expand_macros(line)         
            
            print('label->0', line)
            words = assemble(line)  
            assert(isinstance(words, list))
            #print(line, '-', words)
            off += len(words)
    
    program_end = off
            
    # Step 3: substitute labels by offsets
    off = 0 
    for line in lines:
        # ignore labels
        if (line[-1] == ':'):
            continue
        if (line[0] == '.'):
            continue
        
        for label in labels:
            tokens = get_line_tokens(line)
            if (label in tokens):
                add = label_address[label]
                
                if is_relative_jump(line):
                    assert (add >= 0) and (add <= program_end)
                    
                    add -= off + 1
                    if not(is_valid_relative(line, add)):
                        raise Exception(f'relative jump outside of range {add} in {line}')
                    
                line = line.replace(label, f'{add}')
                
        line = expand_macros(line)
        
        words = assemble(line)   
        print(f'0x{off:02X} -', line,  [f'{w:04X}' for w in words])
        
        ret.extend(words)
        off += len(words)
        
        if (debug):
            sbytes = ''
            for word in words:
                sbytes += f'{word:04X} '
                
            print(f'{sbytes:20}', line)
            
    #print(label_address)
    
    return ret, label_address