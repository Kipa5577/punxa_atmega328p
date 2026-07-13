# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 16:21:50 2026

@author: dcr
"""

import re

# Predefined AVR constants to prevent 'unknown constant' errors
AVR_CONSTANTS = {
    'SREG': 0x3F, 'SPL': 0x3D, 'SPH': 0x3E, 'RAMPZ': 0x3B, 'EIND': 0x3C,
    'SPMCSR': 0x37, 'MCUCR': 0x35, 'MCUSR': 0x34, 'SMCR': 0x33,
    'OSCCAL': 0x39, 'CLKPR': 0x61, 'PRR': 0x64, 'WDTCSR': 0x60,
    'EICRA': 0x69, 'EICRB': 0x6A, 'EIMSK': 0x1D, 'EIFR': 0x1C,
    'PCICR': 0x68, 'PCMSK0': 0x6B, 'PCMSK1': 0x6C, 'PCMSK2': 0x6D,
    'ADCSRA': 0x7A, 'ADCSRB': 0x7B, 'ADMUX': 0x7C, 'ADCL': 0x78, 'ADCH': 0x79,
    'DIDR0': 0x7E, 'DIDR1': 0x7F,
    'TIMSK0': 0x6E, 'TIMSK1': 0x6F, 'TIMSK2': 0x70,
    'TIFR0': 0x35, 'TIFR1': 0x36, 'TIFR2': 0x37,
    'TCCR0A': 0x44, 'TCCR0B': 0x45, 'TCNT0': 0x46, 'OCR0A': 0x47, 'OCR0B': 0x48,
    'TCCR1A': 0x80, 'TCCR1B': 0x81, 'TCCR1C': 0x82,
    'TCNT1H': 0x85, 'TCNT1L': 0x84, 'ICR1H': 0x87, 'ICR1L': 0x86,
    'OCR1AH': 0x89, 'OCR1AL': 0x88, 'OCR1BH': 0x8B, 'OCR1BL': 0x8A,
    'TCCR2A': 0xB0, 'TCCR2B': 0xB1, 'TCNT2': 0xB2, 'OCR2A': 0xB3, 'OCR2B': 0xB4,
    'ASSR': 0xB6, 'TWBR': 0xB8, 'TWSR': 0xB9, 'TWAR': 0xBA, 'TWDR': 0xBB, 'TWCR': 0xBC,
    'UCSR0A': 0xC0, 'UCSR0B': 0xC1, 'UCSR0C': 0xC2, 'UBRR0H': 0xC5, 'UBRR0L': 0xC4, 'UDR0': 0xC6,
    'SPCR': 0x2C, 'SPSR': 0x2D, 'SPDR': 0x2E,
    'RAMEND': 0x08FF, 'FLASHEND': 0x7FFF, 'E2END': 0x03FF,
}

def split_parts(s):
    # Preserve contents inside parentheses to prevent splitting macros like low() and high()
    macros = []
    def save_macro(match):
        macros.append(match.group(0))
        return f"__MACRO_{len(macros)-1}__"
    
    s_no_parens = re.sub(r'\([^()]*\)', save_macro, s)
    
    # Split by commas first, then by whitespace
    parts = re.split(r'[,]', s_no_parens)
    ret = []
    for part in parts:
        sub_parts = part.split()
        for sp in sub_parts:
            if len(sp) > 0:
                ret.append(sp)
                
    # Restore macros
    for i, m in enumerate(macros):
        for j, p in enumerate(ret):
            if f"__MACRO_{i}__" in p:
                ret[j] = p.replace(f"__MACRO_{i}__", m)
                
    # Merge math operators (e.g., '0', '+', '0' -> '0+0')
    merged = []
    i = 0
    while i < len(ret):
        p = ret[i]
        if not merged:
            merged.append(p)
        elif p in ('+', '*', '/', '<<', '>>', '|', '&', '^', '==', '!='):
            merged[-1] += p
            if i + 1 < len(ret):
                i += 1
                merged[-1] += ret[i]
        elif p == '-':
            # Distinguish math subtraction from pointer mode like '-X'
            is_prev_num = (merged[-1][0].isdigit() or 
                           merged[-1][0] in 'abcdefABCDEF(' or 
                           merged[-1] in AVR_CONSTANTS)
            is_next_num = (i + 1 < len(ret)) and (ret[i+1][0].isdigit() or ret[i+1][0] in 'abcdefABCDEF(' or ret[i+1] in AVR_CONSTANTS)
            
            if is_prev_num and is_next_num:
                merged[-1] += p
                i += 1
                merged[-1] += ret[i]
            else:
                merged.append(p)
        else:
            merged.append(p)
        i += 1
    return merged

def reg_to_index(reg):
    reg = reg.lower()
    if (reg[0] == 'r'): return int(reg[1:])
    raise Exception(f'unknown register {reg}')
    
def get_int(v):
    if (isinstance(v, int)):
        return v
    if (isinstance(v, str)):
        v = v.strip()
        if (v[0:2] == '0x' or v[0:2] == '0X'):
            return int(v, 16)
        elif (v[0:2] == '0b' or v[0:2] == '0B'):
            return int(v, 2)
        else:
            try:
                return int(v)
            except ValueError:
                if v.isidentifier():
                    if v in AVR_CONSTANTS:
                        return AVR_CONSTANTS[v]
                    raise Exception(f'Unknown constant {v}')
                try:
                    return eval(v, {"__builtins__": None}, AVR_CONSTANTS)
                except Exception as e:
                    raise Exception(f'Cannot evaluate expression {v}') from e
    
def parts_to_ins(parts):
    
    op = parts[0].upper()
    
    if (op == 'ADD'):
        p0 = 0b0000
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'ADC'):
        p0 = 0b0001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'ADIW'):
        p0 = 0b1001
        p1 = 0b0110
        r = (reg_to_index(parts[1]) - 24) // 2
        k = get_int(parts[2])
        p2 = ((k >> 4) << 2) | (r)
        p3 = (k & 0xF)
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'AND'):
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b0000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'ANDI'):
        Rd = reg_to_index(parts[1])
        K = get_int(parts[2])
        p1 = (K >> 4) & 0xF
        p2 = (Rd - 16) & 0xF
        p3 = K & 0xF
        return [0b0111_0000_0000_0000 | (p1 << 8) | (p2 << 4) | p3 ]
    
    elif (op == 'ASR'):
        p0 = 0b1001
        Rd = reg_to_index(parts[1])
        p1 = 0b0100 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0b0101
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
        
    elif (op == 'BCLR'):
        p0 = 0b1001
        s = get_int(parts[1])
        p1 = 0b0100 
        p2 = 0b1000 | s
        p3 = 0b1000
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BLD'):
        p0 = 0b1111
        Rd = reg_to_index(parts[1])
        b = get_int(parts[2])
        p1 = 0b1000 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = b & 0x7
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRBC'):
        p0 = 0b1111
        k = get_int(parts[2])
        s = get_int(parts[1])
        assert (s >= 0) and (s <= 7)
        p1 = 0b0100  | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | s
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRBS'):
        p0 = 0b1111
        k = get_int(parts[2])
        s = get_int(parts[1])
        assert (s >= 0) and (s <= 7)
        p1 = 0b0000  | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | s
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRCC'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = (1 << 2) | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRCS'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BREAK'):
        return [0b1001_0101_1001_1000]
    
    elif (op == 'BREQ'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 1
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRGE'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b100
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRHC'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b101
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRHS'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0000 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b101
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRID'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRIE'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0000 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRLO'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b000
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRLT'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b100
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRMI'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b010
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRNE'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 1
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRPL'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = (1 << 2) | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b010
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRTC'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b110
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRTS'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0000 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b110
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRSH'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = 0b0100 | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b000
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRVC'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = (1 << 2) | ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = (k & 1) << 3 | 0b011
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BRVS'):
        p0 = 0b1111
        k = get_int(parts[1])
        p1 = ((k >> 5) & 0b11)
        p2 = (k >> 1) & 0xF
        p3 = ((k & 1) << 3) | 0b011
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BSET'):
        p0 = 0b1001
        s = get_int(parts[1])
        p1 = 0b0100 
        p2 = 0b0000 | s
        p3 = 0b1000
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'BST'):
        p0 = 0b1111
        Rr = reg_to_index(parts[1])
        b = get_int(parts[2])
        p1 = 0b1010 | (Rr>>4)
        p2 = Rr & 0xF
        p3 = b & 0x7
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CALL'):
        p0 = 0b1001
        k = get_int(parts[1])
        p1 = 0b0100 | (k >> 21)
        p2 = (k >> 17) & 0xF
        p3 = 0b1110 | ((k >> 16) & 1)
        w = k & 0xFFFF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) , w]
        
    elif (op == 'CBI'):
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
        r = reg_to_index(parts[1])
        k = get_int(parts[2])
        k = 0xff - k
        p1 = k >> 4
        p2 = (r - 16) & 0xF
        p3 = k & 0xF
        return [((0b0111 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CLC'):
        return [ 0b1001_0100_1000_1000]
        
    elif (op == 'CLH'):
        return [0b1001_0100_1101_1000]
    
    elif (op == 'CLI'):
        return [0b1001_0100_1111_1000]
    
    elif (op == 'CLR'):
        p0 = 0b0010
        r =  reg_to_index(parts[1]) 
        p1 = (1<<2) | ((r >> 4) << 1) | (r>>4)
        p2 = (r & 0xF)
        p3 = (r & 0xF)
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CLN'):
        return [0b1001_0100_1010_1000]
    
    elif (op == 'CLS'):
        return [0b1001_0100_1100_1000]
    
    elif (op == 'CLT'):
        return [ 0b1001_0100_1110_1000]
    
    elif (op == 'CLV'):
        return [0b1001_0100_1011_1000]
    
    elif (op == 'CLZ'):
        return [0b1001_0100_1001_1000]
    
    elif (op == 'COM'):
        p0 = 0b1001
        Rd = reg_to_index(parts[1])
        p1 = 0b0100 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CP'):
        p0 = 0b0001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b0100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CPC'):
        p0 = 0b0001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b0000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CPI'):
        r = reg_to_index(parts[1])
        k = get_int(parts[2])
        p1 = k >> 4
        p2 = (r - 16) & 0xF
        p3 = k & 0xF
        return [((0b0011 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'CPSE'):
        Rd =  reg_to_index(parts[1]) 
        Rr =  reg_to_index(parts[2])
        p1 = ((Rr >> 4) << 1) | (Rd>>4)
        p2 = (Rd & 0xF)
        p3 = (Rr & 0xF)
        return [0b0001_0000_0000_0000 | (p1 << 8) | (p2 << 4) | p3 ]
    
    elif (op == 'DEC'):
        p0 = 0b1001
        Rd =  reg_to_index(parts[1]) 
        p1 = 0b0100 | (Rd >> 4)
        p2 = Rd & 0xF
        p3 = 0b1010
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'EOR'):
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b0100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF    
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'FMUL'):
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        return [0b0000_0011_0000_1000 | ((Rd & 0x7) << 4) | (Rr & 0x7)]
        
    elif (op == 'FMULS'):
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        return [0b0000_0011_1000_0000 | ((Rd & 0x7) << 4) | (Rr & 0x7)]
    
    elif (op == 'FMULSU'):
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        return [0b0000_0011_1000_1000 | ((Rd & 0x7) << 4) | (Rr & 0x7)]
    
    elif (op == 'ICALL'):
        return [0b1001_0101_0001_1001]
    
    elif (op == 'IJMP'):
        return [0b1001_0100_0001_1001]
    
    elif (op == 'IN'):
        p0 = 0b1011
        Rd = reg_to_index(parts[1]) 
        A = get_int(parts[2])
        p1 = (A >> 4) << 1 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = A & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'INC'):
        p0 = 0b1001
        Rd =  reg_to_index(parts[1]) 
        p1 = 0b0100 | (Rd >> 4)
        p2 = Rd & 0xF
        p3 = 0b0011
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
        
    elif (op == 'JMP'):
        p0 = 0b1001
        k = get_int(parts[1])
        p1 = 0b0100 | (k >> 21)
        p2 = (k >> 17) & 0xF
        p3 = 0b1100 | ((k >> 16) & 1)
        w = k & 0xFFFF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) , w]
        
    elif (op == 'LD'):
        r = reg_to_index(parts[1])
        mode = parts[2].strip().upper()
        
        if (mode == 'X'): m1, m2 = 1, 0b1100
        elif (mode == 'X+'): m1, m2 = 1, 0b1101
        elif (mode == '-X'): m1, m2 = 1, 0b1110
        elif (mode == 'Y'): m1, m2 = 0, 0b1000
        elif (mode == 'Y+'): m1, m2 = 1, 0b1001 
        elif (mode == '-Y'): m1, m2 = 1, 0b1010  
        elif (mode == 'Z'): m1, m2 = 0, 0b0000
        elif (mode == 'Z+'): m1, m2 = 1, 0b0001
        elif (mode == '-Z'): m1, m2 = 1, 0b0010
        else: raise Exception(f'Not supported yet= {mode}')
            
        p0 = 0b1000 | m1
        p1 = 0b0000 | (r>>4)
        p2 = r & 0xF
        p3 = m2
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
    
    elif (op == 'LDD'):
        Rd = reg_to_index(parts[1])
        mode_part = parts[2].strip().upper()
        
        if '+' in mode_part:
            reg_part, q_str = mode_part.split('+')
            q = get_int(q_str)
            assert q >= 0 and q <= 63
        else:
            raise Exception(f'Invalid LDD mode: {mode_part}')
        
        reg_bit = 1 if reg_part == 'Y' else 0
        word = (1 << 15) | (((q >> 3) & 0b11) << 10) | ((q >> 5) << 13) | ((Rd & 0x1F) << 4) | (reg_bit << 3) | (q & 0b111)
        return [word]

    elif (op == 'LDI'):
        r = reg_to_index(parts[1]) 
        off = get_int(parts[2]) & 0xFF
        p1 = off >> 4
        p2 = (r - 16) & 0xF 
        p3 = off & 0xF
        return [((0b1110 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'LDS'):
        p0 = 0b1001
        r = reg_to_index(parts[1])
        p1 = 0b0000 | (r >> 4)
        p2 = r & 0xF
        p3 = 0
        w1 = get_int(parts[2]) >> 8
        w2 = get_int(parts[2]) & 0xFF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) , ((w1 << 8) | w2 )]
    
    elif (op == 'LPM'):
        if len(parts) == 1:
            return [0b1001_0000_0000_0100]
        else:
            Rd = reg_to_index(parts[1])
            mode = parts[2].strip().upper()
            if mode == 'Z':
                return [0b1001_0000_0000_0100 | (Rd << 4)]
            elif mode == 'Z+':
                return [0b1001_0000_0000_0101 | (Rd << 4)]
            else:
                raise Exception(f'Invalid LPM mode: {mode}')
    
    elif (op == 'LSL'):
        p0 = 0b0000
        Rd = reg_to_index(parts[1])
        p1 = 0b1100 | ((Rd >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rd & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'LSR'):
        p0 = 0b1001
        r = reg_to_index(parts[1])
        p1 = 0b0100 | (r >> 4)
        p2 = r & 0xF
        p3 = 0b0110
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
    
    elif (op == 'MOV'):
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'MOVW'):
            # reg_to_index returns 0-31. MOVW needs the pair index (0-15).
            Rd_pair = reg_to_index(parts[1]) >> 1
            Rr_pair = reg_to_index(parts[2]) >> 1
            
            # Opcode base for MOVW is 0x0100 (0001 0000 0000 0000)
            p_base = 0x01 
            p2 = Rd_pair & 0xF
            p3 = Rr_pair & 0xF
            
            return [((p_base << 8) | (p2 << 4) | p3)]
    
    elif (op == 'MUL'):
        p0 = 0b1001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1100 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'MULS'):
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        return [0b0000_0010_0000_0000 | ((Rd & 0xF) << 4) | (Rr & 0xF)]
    
    elif (op == 'MULSU'):
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        return [0b0000_0011_0000_0000 | ((Rd & 0b111) << 4) | (Rr & 0b111)]
    
    elif (op == 'NEG'):
        p0 = 0b1001
        r = reg_to_index(parts[1])
        p1 = 0b0100 | (r >> 4)
        p2 = r & 0xF
        p3 = 0b0001
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
    
    elif (op == 'NOP'):
        return [0b0000_0000_0000_0000]
    
    elif (op == 'OR'):
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF        
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'ORI'):
        r = reg_to_index(parts[1]) 
        off = get_int(parts[2]) & 0xFF
        p1 = off >> 4
        p2 = (r - 16) & 0xF 
        p3 = off & 0xF
        return [((0b0110 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'OUT'):
        p0 = 0b1011
        r = reg_to_index(parts[2])
        A = get_int(parts[1])
        p1 = (1 << 3) | (A >> 4) << 1 | (r >> 4)
        p2 = r & 0XF
        p3 = A & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'POP'):
        p0 = 0b1001
        Rd = reg_to_index(parts[1])        
        p1 = 0b0000 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0b1111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'PUSH'):
        p0 = 0b1001
        Rd = reg_to_index(parts[1])        
        p1 = 0b0010 | (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0b1111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
        
    elif (op == 'RCALL'):
        ip1 = get_int(parts[1])
        return [0b1101_0000_0000_0000 | (ip1 & 0xFFF)]
    
    elif (op == 'RET'):
        return [0b1001_0101_0000_1000]
    
    elif (op == 'RETI'):
        return [0b1001_0101_0001_1000]
    
    elif (op == 'RJMP'):
        p0 = 0b1100
        off = get_int(parts[1]) 
        return [(p0 << 12) | (off & 0xFFF) ]
    
    elif (op == 'ROL'):
        p0 = 0b0001
        Rd = reg_to_index(parts[1])        
        p1 = 0b1100 | ((Rd >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rd & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'ROR'):
        p0 = 0b1001
        Rd = reg_to_index(parts[1])        
        p1 = 0b0100 |  (Rd>>4)
        p2 = Rd & 0xF
        p3 = 0b0111
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBC'):
        p0 = 0b0000
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBCI'):
        Rd = reg_to_index(parts[1])
        K = get_int(parts[2])
        p1 = (K >> 4)
        p2 = (Rd - 16) & 0xF
        p3 = K & 0xF
        return [((0b0100 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBI'):
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
        p0 = 0b1001
        p1 = 0b0111
        r = (reg_to_index(parts[1]) - 24) // 2
        k = get_int(parts[2])
        p2 = ((k >> 4) << 2) | (r)
        p3 = (k & 0xF)
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBR'):
        r = reg_to_index(parts[1]) 
        off = get_int(parts[2]) & 0xFF
        p1 = off >> 4
        p2 = (r - 16) & 0xF 
        p3 = off & 0xF
        return [((0b0110 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SBRC'):
        p0 = 0b1111
        r = reg_to_index(parts[1])
        p1 = 0b1100 | (r >> 4)
        p2 = r & 0xF
        p3 = get_int(parts[2])
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]

    elif (op == 'SBRS'):
        p0 = 0b1111
        r = reg_to_index(parts[1])
        p1 = 0b1110 | (r >> 4)
        p2 = r & 0xF
        p3 = get_int(parts[2])
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SEC'):
        return [0b1001_0100_0000_1000]
    
    elif (op == 'SEH'):
        return [0b1001_0100_0101_1000]
    
    elif (op == 'SEI'):
        return [0b1001_0100_0111_1000]
    
    elif (op == 'SEN'):
        return [0b1001_0100_0010_1000]
    
    elif (op == 'SER'):
        r = reg_to_index(parts[1])
        return [0b1110_1111_0000_1111 | (((r - 16) & 0xF) << 4)]
    
    elif (op == 'SES'):
        return [0b1001_0100_0100_1000]
    
    elif (op == 'SET'):
        return [0b1001_0100_0110_1000]
    
    elif (op == 'SEV'):
        return [0b1001_0100_0011_1000]
    
    elif (op == 'SEZ'):
        return [0b1001_0100_0001_1000]
    
    elif (op == 'SLEEP'):
        return [0b1001_0101_1000_1000]
    
    elif (op == 'SPM'):
        if len(parts) == 1:
            return [0b1001_0101_1110_1000]
        elif parts[1].strip().upper() == 'Z+':
            return [0b1001_0101_1111_1000]
        else:
            raise Exception(f'Invalid SPM mode: {parts[1]}')
    
    elif (op == 'ST'):
        mode = parts[1].strip().upper()
        Rr = reg_to_index(parts[2])
        if (mode == 'X'): m1, m2 = 1, 0b1100
        elif (mode == 'X+'): m1, m2 = 1, 0b1101
        elif (mode == '-X'): m1, m2 = 1, 0b1110
        elif (mode == 'Y'): m1, m2 = 0, 0b1000
        elif (mode == 'Y+'): m1, m2 = 1, 0b1001 
        elif (mode == '-Y'): m1, m2 = 1, 0b1010 
        elif (mode == 'Z'): m1, m2 = 0, 0b0000
        elif (mode == 'Z+'): m1, m2 = 1, 0b0001
        elif (mode == '-Z'): m1, m2 = 1, 0b0010
        else: raise Exception(f'Not supported yet= {mode}')
            
        p0 = 0b1000 | m1
        p1 = 0b0010 | (Rr>>4)
        p2 = Rr & 0xF
        p3 = m2
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
    
    elif (op == 'STD'):
        mode_part = parts[1].strip().upper()
        Rr = reg_to_index(parts[2])
        
        if '+' in mode_part:
            reg_part, q_str = mode_part.split('+')
            q = get_int(q_str)
            assert q >= 0 and q <= 63
        else:
            raise Exception(f'Invalid STD mode: {mode_part}')
        
        reg_bit = 1 if reg_part == 'Y' else 0
        word = (1 << 15) | (((q >> 3) & 0b11) << 10) | ((q >> 5) << 13) | (1 << 9) | ((Rr & 0x1F) << 4) | (reg_bit << 3) | (q & 0b111)
        return [word]
        
    elif (op == 'STS'):
        p0 = 0b1001
        r = reg_to_index(parts[2])
        p1 = 0b0010 | (r >> 4)
        p2 = r & 0xF
        p3 = 0
        w = get_int(parts[1])  & 0xFFFF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) , w]
    
    elif (op == 'SUB'):
        p0 = 0b0001
        Rd = reg_to_index(parts[1])
        Rr = reg_to_index(parts[2])
        p1 = 0b1000 | ((Rr >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rr & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SUBI'):
        r = reg_to_index(parts[1]) 
        off = get_int(parts[2]) & 0xFF
        p1 = off >> 4
        p2 = (r - 16) & 0xF 
        p3 = off & 0xF
        return [((0b0101 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'SWAP'):
        p0 = 0b1001
        Rd = reg_to_index(parts[1])
        p1 = 0b0100 | (Rd >> 4)
        p2 = Rd & 0xF
        p3 = 0b0010
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3)]
    
    elif (op == 'TST'):
        p0 = 0b0010
        Rd = reg_to_index(parts[1])
        p1 = 0b0000 | ((Rd >> 4) << 1) | (Rd>>4)
        p2 = Rd & 0xF
        p3 = Rd & 0xF
        return [((p0 << 12) | (p1 << 8) | (p2 << 4) | p3) ]
    
    elif (op == 'WDR'):
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
    if (parts[0] in ['RCALL', 'RJMP', 'BRBC', 'BRBS', 'BRCC', 'BRCS', 'BRSH', 'BRLO', 
                     'BREQ', 'BRGE', 'BRLT', 'BRNE', 'BRMI', 'BRHC', 'BRHS', 'BRID', 
                     'BRIE', 'BRTC', 'BRTS', 'BRVC', 'BRVS', 'BRPL']): return True
    return False

def is_valid_relative(asm, delta):
    parts = split_parts(asm.upper())
    valid12 = (delta <= 2047 ) and (delta >= -2048)
    valid7 = (delta <= 63 ) and (delta >= -64)
    
    if (parts[0] in ['RCALL', 'RJMP']): return valid12
    if (parts[0] in ['BRBC', 'BRBS', 'BRCC', 'BRCS', 'BRSH', 'BRLO', 'BREQ', 'BRGE', 
                     'BRLT', 'BRNE', 'BRMI', 'BRHC', 'BRHS', 'BRID', 'BRIE', 'BRTC', 
                     'BRTS', 'BRVC', 'BRVS', 'BRPL']): return valid7
    return False

def expand_macros(line):
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

def assemble_program(program, debug=False, inject_vector_table=False):
    # ---  VECTOR TABLE INJECTION LOGIC ---
    if inject_vector_table:
        # 1. Put a jump at the reset vector (0x0000) pointing to our code
        vec_table = ".org 0x0000\nRJMP __auto_main\n"
        
        # 2. Fill all potential interrupt vectors (0x0001 - 0x0032) with RETI
        # This acts as a safety net. If an old test triggers a stray interrupt, 
        # it will immediately return instead of crashing the CPU.
        for i in range(1, 0x33):
            vec_table += f".org 0x{i:04X}\nRETI\n"
            
        # 3. Start the actual legacy program safely after the table
        vec_table += ".org 0x0033\n__auto_main:\n"
        
        program = vec_table + program
        
    ret = []
    labels = []
    lines = []
    
    # Flash image for .db/.dw data: word_address -> word_value
    flash_image = {}
    
    def add_flash_byte(byte_addr, byte_val):
        """Add a byte to the flash image at the given byte address."""
        word_addr = byte_addr >> 1
        if byte_addr & 1:  # Odd address = high byte
            flash_image[word_addr] = (flash_image.get(word_addr, 0xFFFF) & 0x00FF) | (byte_val << 8)
        else:  # Even address = low byte
            flash_image[word_addr] = (flash_image.get(word_addr, 0xFFFF) & 0xFF00) | (byte_val & 0xFF)
    
    def parse_db_directive(values_str, current_word_off):
        """Parse .db values and add to flash image. Returns new word offset."""
        values = [get_int(v.strip()) for v in values_str.split(',')]
        byte_off = current_word_off * 2  # Convert word to byte address
        for val in values:
            add_flash_byte(byte_off, val & 0xFF)
            byte_off += 1
        # Return new word offset (ceiling division for odd byte count)
        return (byte_off + 1) // 2
    
    def parse_dw_directive(values_str, current_word_off):
        """Parse .dw values and add to flash image. Returns new word offset."""
        values = [get_int(v.strip()) for v in values_str.split(',')]
        byte_off = current_word_off * 2
        for val in values:
            # AVR is little-endian: low byte first
            add_flash_byte(byte_off, val & 0xFF)
            add_flash_byte(byte_off + 1, (val >> 8) & 0xFF)
            byte_off += 2
        return byte_off // 2
    
    # ==================== Parse lines ====================
    for line in program.split('\n'):
        if (';' in line):
            line = line.split(';')[0]
        line = line.strip()
        if (len(line) == 0):
            continue
        if (':' in line):
            pos = line.find(':')
            label = line[:pos]
            labels.append(label)
            lines.append(f'{label}:')
            line = line[pos+1:].strip()
            if (len(line) == 0):
                continue
        lines.append(line)
    
    # ==================== First pass: collect labels and addresses ====================
    off = 0  # Word offset (this assembler uses word addressing)
    label_address = {}
    
    for line in lines:
        if (line[-1] == ':'):
            label = line[:-1]
            label_address[label] = off
        elif (line[0] == '.'):
            line_lower = line.lower()
            
            if line_lower.startswith('.equ'):
                parts = line[5:].split('=')
                label = parts[0].strip()
                v = get_int(parts[1].strip())
                labels.append(label)
                label_address[label] = v
                
            elif line_lower.startswith('.org'):
                parts = line.split()
                if len(parts) > 1:
                    off = get_int(parts[1])
                    
            elif line_lower.startswith('.db'):
                values_str = line[3:].strip()
                off = parse_db_directive(values_str, off)
                
            elif line_lower.startswith('.dw'):
                values_str = line[3:].strip()
                off = parse_dw_directive(values_str, off)
                
            # Skip other directives (.include, .macro, etc.)
        else:
            # Regular instruction - expand and count words
            for label in labels:
                tokens = get_line_tokens(line)
                if (label in tokens):
                    line = line.replace(label, '0')
            line = expand_macros(line)         
            words = assemble(line)  
            assert(isinstance(words, list))
            off += len(words)
    
    program_end = off
    
    # ==================== Second pass: generate code with merged data ====================
    output_words = {}  # word_address -> word_value
    word_off = 0
    
    for line in lines:
        if (line[-1] == ':'):
            continue
            
# ==================== Second pass: generate code with merged data ====================
    output_words = {}  # word_address -> word_value
    word_off = 0
    
    for line in lines:
        if (line[-1] == ':'):
            continue
            
        if (line[0] == '.'):
            # FIXED: We must respect .org in the second pass so instructions 
            # are placed at the correct vector addresses!
            line_lower = line.lower()
            if line_lower.startswith('.org'):
                parts = line.split()
                if len(parts) > 1:
                    word_off = get_int(parts[1])
            continue  # Skip other directives in second pass
        
        # Insert any .db/.dw words that should come BEFORE this instruction
        while word_off in flash_image and word_off not in output_words:
            output_words[word_off] = flash_image[word_off]
            word_off += 1
        
        # Process instruction - resolve labels
        line_copy = line
        for label in labels:
            tokens = get_line_tokens(line_copy)
            if (label in tokens):
                add = label_address[label]
                if is_relative_jump(line_copy):
                    assert (add >= 0) and (add <= program_end)
                    add -= word_off + 1
                    if not(is_valid_relative(line_copy, add)):
                        raise Exception(f'relative jump outside of range {add} in {line_copy}')
                line_copy = line_copy.replace(label, f'{add}')
        
        line_copy = expand_macros(line_copy)
        words = assemble(line_copy)   
        print(f'0x{word_off:04X} -', line_copy, [f'{w:04X}' for w in words])
        
        for w in words:
            output_words[word_off] = w
            word_off += 1
        
        if (debug):
            sbytes = ''
            for word in words:
                sbytes += f'{word:04X} '
            print(f'{sbytes:20}', line_copy)
    
    # ==================== Append remaining .db/.dw words (after all code) ====================
    for wa in sorted(flash_image.keys()):
        if wa not in output_words:
            print(f'0x{wa:04X} - .db/.dw data', [f'{flash_image[wa]:04X}'])
            output_words[wa] = flash_image[wa]
    
    # ==================== Convert to list, filling gaps with 0xFFFF ====================
    if output_words:
        max_addr = max(output_words.keys())
        ret = [output_words.get(i, 0xFFFF) for i in range(max_addr + 1)]
    else:
        ret = []
    
    return ret, label_address