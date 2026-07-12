# -*- coding: utf-8 -*-
"""
Created on Tue May 19 16:56:55 2026

@author: dcr
"""

import py4hw
import punxa_atmega328p as punxa

#from punxa_atmega328p.single_cycle.singlecycle_processor import SingleCycleATmega328P
#from punxa_atmega328p.Memory import MemoryInterface
#from punxa_atmega328p.Memory import Memory
#from punxa_atmega328p.Memory import Memory

hw = py4hw.HWSystem()


program = '''
; Bare-metal, linear sequence for ATmega328P (16 MHz clock, 9600 Baud)

; 1. Initialize USART0 Baud Rate (UBRR = 103)
LDI R16, 0
STS 0xC5, R16        ; UBRRH0 <- 0
LDI R16, 103
STS 0xC4, R16        ; UBRRL0 <- 103

; 2. Enable USART0 Transmitter
LDI R16, 8
STS 0xC1, R16        ; UCSR0B <- 0x08 (TXEN0 enabled)

; 3. Set Frame Format (8 data bits, 1 stop bit)
LDI R16, 6
STS 0xC2, R16        ; UCSR0C <- 0x06 (UCSZ01 and UCSZ00 enabled)


; 4. Sequential Transmission (Poll buffer state, then push literal ASCII value)

; --- Byte 1: 'H' (0x48) ---
LDS R16, 0xC0        ; Read UCSR0A
SBRS R16, 5          ; Check UDRE0 bit. If set, skip next line
RJMP -4              ; Jump back to LDS command if buffer is busy
LDI R17, 0x48        ; Load 'H'
STS 0xC6, R17        ; Push to UDR0

; --- Byte 2: 'e' (0x65) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x65        ; Load 'e'
STS 0xC6, R17

; --- Byte 3: 'l' (0x6C) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6C        ; Load 'l'
STS 0xC6, R17

; --- Byte 4: 'l' (0x6C) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6C        ; Load 'l'
STS 0xC6, R17

; --- Byte 5: 'o' (0x6F) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6F        ; Load 'o'
STS 0xC6, R17

; --- Byte 6: ',' (0x2C) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x2C        ; Load ','
STS 0xC6, R17

; --- Byte 7: ' ' (0x20) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x20        ; Load space
STS 0xC6, R17

; --- Byte 8: 'W' (0x57) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x57        ; Load 'W'
STS 0xC6, R17

; --- Byte 9: 'o' (0x6F) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6F        ; Load 'o'
STS 0xC6, R17

; --- Byte 10: 'r' (0x72) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x72        ; Load 'r'
STS 0xC6, R17

; --- Byte 11: 'l' (0x6C) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6C        ; Load 'l'
STS 0xC6, R17

; --- Byte 12: 'd' (0x64) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x64        ; Load 'd'
STS 0xC6, R17

; --- Byte 13: '!' (0x21) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x21        ; Load '!'
STS 0xC6, R17

; --- Byte 14: Carriage Return (0x0D) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x0D        ; Load CR
STS 0xC6, R17

; --- Byte 15: Line Feed (0x0A) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x0A        ; Load LF
STS 0xC6, R17


; 5. Catch-trap execution pipeline to prevent runaway execution
RJMP -1              ; Infinite self-loop
'''
from punxa_atmega328p.assembly import assemble_program
 
words = assemble_program(program)
dw = 8 
aw = 16

# Memory Map
# 0x0 - 0x1r   GP Registers r0-r31
data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

cpu_p = punxa.MemoryInterface(hw, 'cpu', dw, aw)
reg_p = punxa.MemoryInterface(hw, 'reg', dw, 5)         # 2^5 = 32 registers
usart_p = punxa.MemoryInterface(hw, 'usart', dw, 3)     # 2^3 = 8 registers
mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)        # 2048 bytes


punxa.MultiplexedBus(hw, 'bus', data_p, [(reg_p, 0x0), (usart_p, 0xC0), (mem_p, 0x100)])
punxa.MultiplexedBus(hw, 'cpu', cpu_p, [(reg_p, 0x0), (usart_p, 0xC0), (mem_p, 0x100)])

cpu = punxa.SingleCycleATmega328P(hw, 'cpu', ins_p, data_p, reset_address=0)
reg = punxa.Ram_Memory(hw, 'reg', dw, 5, reg_p)                 # 32 B
mem = punxa.Ram_Memory(hw, 'men', dw, 11, mem_p)                # 2048 B
ins_mem = punxa.Ram_Memory(hw, 'ins_men', 16, 14, ins_p)        # 16 k words (of 16 bits) 
usart = punxa.VirtualUSART(hw, 'usart', usart_p)

watch = []
watch.extend(py4hw.debug.getInterfaceWires(ins_p))
watch.extend(py4hw.debug.getInterfaceWires(data_p))
watch.extend(py4hw.debug.getInterfaceWires(reg_p))
wvf = py4hw.Waveform(hw, 'wvf', watch)

# Load program into memory
for i, b in enumerate(words):
    ins_mem.writeWord(i, b)
    
#py4hw.gui.Workbench(hw)

import punxa_atmega328p.interactive_commands as ci

ci._ci_hw = hw
ci._ci_cpu = cpu

from punxa_atmega328p.interactive_commands import *

banner = '''
██████╗ ██╗   ██╗███╗   ██╗██╗  ██╗ █████╗
██╔══██╗██║   ██║████╗  ██║╚██╗██╔╝██╔══██╗      _   _                        __ __  __
██████╔╝██║   ██║██╔██╗ ██║ ╚███╔╝ ███████║     /_\ | |_ _ __  ___ ___   __    _) _)(__) __
██╔═══╝ ██║   ██║██║╚██╗██║ ██╔██╗ ██╔══██║    / _ \| '_| '  \/ -_) _ \ / _`| __)/_ (__) |_)
██║     ╚██████╔╝██║ ╚████║██╔╝ ██╗██║  ██║   /_/ \_\_| |_|_|_\___\__, \__,_|            |
╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝                       |___/                

                    The Atmega328p system simulator
'''

print(banner)
py4hw.gui.Workbench(hw)
