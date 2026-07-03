import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program

# -----------------------------------------------------------------------------
# Test Bench & Simulation Setup
# -----------------------------------------------------------------------------

hw = py4hw.HWSystem()

program_Test = '''
main:
    ; --- 1. INITIALIZE STACK POINTER ---
    ; ATmega328P RAM ends at 0x08FF
    LDI R16, 0x08
    OUT 0x3E, R16   ; Write 0x08 to SPH (I/O address 0x3E)
    LDI R16, 0xFF
    OUT 0x3D, R16   ; Write 0xFF to SPL (I/O address 0x3D)

; --- Zero out RAM (0x0100 to 0x08FF) ---
    LDI R28, 0x00    ; Y-pointer low
    LDI R29, 0x01    ; Y-pointer high (start of SRAM)
    LDI R16, 0x00    ; Value to write
clear_loop:
    ST Y+, R16       ; Write 0, increment Y
    CPI R28, 0x00    ; Check if we reached the end (0x0900)
    CPI R29, 0x09
    BRNE clear_loop
    
    ; ---  START TESTS ---
    JMP Sequancer
arithmetic:
    LDI R24,120  ;ADD
    LDI R25,40
    ADD R24,R25
    LDI R24,255
    LDI R25,1
    ADD R24,R25
    LDI R24,0
    LDI R25,0
    ADD R24,R25
    LDI R24,5
    LDI R25,3
    ADD R24,R25
    SEC    ;ADC
    LDI R24,120
    LDI R25,40
    ADC R24,R25
    SEC
    LDI R24,255
    LDI R25,1
    ADC R24,R25
    SEC
    LDI R24,0
    LDI R25,0
    ADC R24,R25
    SEC
    LDI R24,5
    LDI R25,3
    ADC R24,R25
    LDI R24,120  ;ADIW
    LDI R25,40
    ADIW R24,59
    LDI R24,255
    LDI R25,1
    ADIW R24,1
    LDI R24,0
    LDI R25,0
    ADIW R24,2
    LDI R24,5
    LDI R25,3
    ADIW R24,5
    LDI R24,120  ;SUB
    LDI R25,40
    SUB R24,R25
    LDI R24,0
    LDI R25,1
    SUB R24,R25
    LDI R24,1
    LDI R25,1
    SUB R24,R25
    LDI R24,5
    LDI R25,3
    SUB R24,R25
    LDI R24,120  ;SUBI
    SUBI R24,20
    LDI R24,0
    SUBI R24,1
    LDI R24,1
    SUBI R24,1
    LDI R24,5
    SUBI R24,4
    SEC    ;SBC
    LDI R24,120
    LDI R25,40
    SBC R24,R25
    SEC
    LDI R24,0
    LDI R25,0
    SBC R24,R25
    SEC
    LDI R24,2
    LDI R25,1
    SBC R24,R25
    SEC
    LDI R24,6
    LDI R25,4
    SBC R24,R25
    SEC    ;SBCI
    LDI R24,120
    SBCI R24,20
    SEC
    LDI R24,0
    SBCI R24,0
    SEC
    LDI R24,2
    SBCI R24,1
    SEC
    LDI R24,6
    SBCI R24,4
    LDI R24,120 ;SBIW
    LDI R25,20
    SBIW R24,25
    LDI R24,0
    LDI R25,0
    SBIW R24,1
    LDI R24,2
    LDI R25,1
    SBIW R24,1
    LDI R24,6
    LDI R25,4
    SBIW R24,4
    LDI R24,120 ;AND
    LDI R25,20
    AND R24,R25
    LDI R24,3
    LDI R25,2
    AND R24,R25
    LDI R24,2
    LDI R25,1
    AND R24,R25
    LDI R24,7
    LDI R25,4
    AND R24,R25
    LDI R24,120 ;ANDI
    ANDI R24,20
    LDI R24,0
    ANDI R24,6
    LDI R24,7
    ANDI R24,4
    LDI R24,6
    ANDI R24,16
    LDI R24,120 ;OR
    LDI R25,20
    OR R24,R25
    LDI R24,3
    LDI R25,2
    OR R24,R25
    LDI R24,2
    LDI R25,1
    OR R24,R25
    LDI R24,7
    LDI R25,255
    OR R24,R25
    LDI R24,120 ;ORI
    ORI R24,20
    LDI R24,0
    ORI R24,6
    LDI R24,7
    ORI R24,4
    LDI R24,6
    ORI R24,16
    LDI R24,120 ;EOR
    LDI R25,20
    EOR R24,R25
    LDI R24,3
    LDI R25,3
    EOR R24,R25
    LDI R24,2
    LDI R25,1
    EOR R24,R25
    LDI R24,7
    LDI R25,255
    EOR R24,R25
    LDI R24,120 ;COM
    COM R24
    LDI R24,0
    COM R24
    LDI R24,7
    COM R24
    LDI R24,255
    COM R24
    LDI R24,120 ;NEG
    NEG R24
    LDI R24,0
    NEG R24
    LDI R24,7
    NEG R24
    LDI R24,255
    NEG R24
    LDI R24,255 ;INC
    INC R24
    INC R24
    INC R24
    INC R24
    LDI R24,1   ;DEC
    DEC R24
    DEC R24
    DEC R24
    DEC R24
    LDI R24,120 ;TST
    TST R24
    LDI R24,0
    TST R24
    LDI R24,128
    TST R24
    LDI R24,255
    TST R24
    LDI R24,120 ;CLR
    CLR R24
    LDI R24,250
    CLR R24
    LDI R24,128 ;SER
    SER R24
    LDI R24,0
    SER R24
    LDI R24,120 ;MUL
    LDI R25,40
    MUL R24,R25
    LDI R24,255
    LDI R25,1
    MUL R24,R25
    LDI R24,0
    LDI R25,0
    MUL R24,R25
    LDI R24,5
    LDI R25,3
    MUL R24,R25
    LDI R24,120 ;MULS
    LDI R25,40
    MULS R24,R25
    LDI R24,255
    LDI R25,1
    MULS R24,R25
    LDI R24,0
    LDI R25,0
    MULS R24,R25
    LDI R24,5
    LDI R25,3
    MULS R24,R25
    ORI R17,120 ;MULSU
    ORI R18,40
    MULSU R17,R18
    ORI R17,255
    ORI R18,1
    MULSU R17,R18
    ORI R17,0
    ORI R18,0
    MULSU R17,R18
    ORI R17,5
    ORI R18,3
    MULSU R17,R18
    LDI R17,120 ;FMUL
    LDI R18,40
    FMUL R17,R18
    LDI R17,255
    LDI R18,1
    FMUL R17,R18
    LDI R17,0
    LDI R18,0
    FMUL R17,R18
    LDI R17,5
    LDI R18,3
    FMUL R17,R18
    LDI R17,120 ;FMULS
    LDI R18,40
    FMULS R17,R18
    LDI R17,255
    LDI R18,1
    FMULS R17,R18
    LDI R17,0
    LDI R18,0
    FMULS R17,R18
    LDI R17,5
    LDI R18,3
    FMULS R17,R18
    LDI R17,120 ;FMULSU
    LDI R18,40
    FMULSU R17,R18
    LDI R17,255
    LDI R18,1
    FMULSU R17,R18
    LDI R17,0
    LDI R18,0
    FMULSU R17,R18
    LDI R17,5
    LDI R18,3
    FMULSU R17,R18
    LDI R24,120 ;LSL
    LSL R24
    LDI R24,255
    LSL R24
    LDI R24,0
    LSL R24
    LDI R24,5
    LSL R24
    LDI R24,120 ;LSR
    LSR R24
    LDI R24,255
    LSR R24
    LDI R24,0
    LSR R24
    LDI R24,5
    LSR R24
    LDI R24,120 ;ROL
    ROL R24
    LDI R24,255
    ROL R24
    LDI R24,0
    ROL R24
    LDI R24,5
    ROL R24
    LDI R24,120 ;ROR
    ROR R24
    LDI R24,255
    ROR R24
    LDI R24,0
    ROR R24
    LDI R24,5
    ROR R24
    LDI R24,120 ;ASR
    ASR R24
    LDI R24,255
    ASR R24
    LDI R24,0
    ASR R24
    LDI R24,5
    ASR R24
    LDI R24,120 ;SWAP
    SWAP R24
    LDI R24,255
    SWAP R24
    LDI R24,0
    SWAP R24
    LDI R24,5
    SWAP R24
    LDI R24,120 ;BST
    BST R24,0
    LDI R24,255
    BST R24,0
    LDI R24,0
    BST R24,0
    LDI R24,5
    BST R24,0
    SET ;BLD
    LDI R24,120
    BLD R24,0
    SET
    LDI R24,255
    BLD R24,0
    SET
    LDI R24,0
    BLD R24,0
    SET
    LDI R24,5
    BLD R24,0
    SEC
    SEN
    SEZ
    SEI
    SES
    SEV
    SET
    SEH
    CLC
    CLN
    CLZ
    CLI
    CLS
    CLV
    CLT
    CLH
    RET
memory:
    LDI R24,120 ;MOV
    MOV R5,R24
    LDI R24,35
    MOV R5,R2
    LDI R24,64
    MOV R5,R24
    LDI R24,120;MOVW
    LDI R25,5
    MOVW R2,R24
    LDI R24,35
    LDI R25,5
    MOVW R2,R24
    LDI R24,64
    LDI R25,5
    MOVW R2,R24
    LDI R26,123;ST
    LDI R27,1
    LDI R24,6
    ST X,R24   
    LDI R28,223
    LDI R29,1
    LDI R24,53
    ST Y,R24   
    LDI R30,100
    LDI R31,1
    LDI R24,153
    ST Z,R24
    LDI R26,124
    LDI R27,1
    LDI R24,32
    ST X+,R24
    LDI R24,31
    ST X,R24
    LDI R28,224
    LDI R29,1
    LDI R24,61
    ST Y+,R24
    LDI R24,26
    ST Y,R24
    LDI R30,101
    LDI R31,1
    LDI R24,72
    ST Z+,R24
    LDI R24,98
    ST Z,R24
    LDI R26,126
    LDI R27,1
    LDI R24,89
    ST X,R24
    LDI R24,92
    ST -X,R24
    LDI R28,226
    LDI R29,1
    LDI R24,67
    ST Y,R24
    LDI R24,87
    ST -Y,R24
    LDI R30,100
    LDI R31,1
    LDI R24,71
    ST Z,R24
    LDI R24,98
    ST -Z,R24
    LDI R28,223
    LDI R29,1
    LDI R24,1
    STD Y+10,R24
    LDI R30,100
    LDI R31,1
    LDI R24,2
    STD Z+10,R24
    LDI R26,123 ;LD
    LDI R27,1
    LD R24,X
    LDI R28,223
    LDI R29,1
    LD R24,Y
    LDI R30,100
    LDI R31,1
    LD R24,Z
    LDI R26,124
    LDI R27,1
    LD R24,X+
    LD R24,X
    LDI R28,224
    LDI R29,1
    LD R24,Y+
    LD R24,Y
    LDI R30,104
    LDI R31,1
    LD R24,Z+
    LD R24,Z
    LDI R26,126
    LDI R27,1
    LD R24,X
    LD R24,-X
    LDI R28,226
    LDI R29,1
    LD R24,Y
    LD R24,-Y
    LDI R30,106
    LDI R31,1
    LD R24,Z
    LD R24,-Z
    LDI R28,223
    LDI R29,1
    LDD R24,Y+10
    LDI R30,100
    LDI R31,1
    LDD R24,Z+10
    LDI R30,6 ;LPM
    LDI R31,0
    LPM 
    LDI R30,255
    LDI R31,71
    LDI R24,24
    LPM R24,Z
    LDI R30,0
    LDI R31,72
    LDI R24,8
    LPM R24,Z+
    LDI R24,19
    LPM R24,Z
    LDI R24,1 ;PUSH
    PUSH R24
    LDI R24,2
    PUSH R24
    LDI R24,3
    PUSH R24
    LDI R24,4
    PUSH R24
    LDI R24,5
    PUSH R24
    POP R24 ;POP
    POP R24
    POP R24
    POP R24
    POP R24
    NOP;NOP
    RET
branch: 
    LDI R24,6
    LDI R25,6
    ;BREQ TEST1
    CP R24,R25 ; Compare registers r1 and R24
    BREQ equal1
    NOP
    NOP
    NOP
equal1:
    LDI R24,6
    LDI R25,5
    ;BREQ TEST2
    CP R24,R25 ; Compare registers r1 and R24
    BREQ equal2
    NOP
    NOP
    NOP
equal2:
    ;BRLO TEST
    EOR r19,r19 ; Clear r19
AAAA: 
    INC r19 ; Increase r19
    CPI r19,0x10 ; Compare r19 with 0x10
    BRLO AAAA ; Branch if r19 < 0x10 (unsigned)
    ;BRSH TEST1
    LDI R19,16
    subi r19,4 ; Subtract 4 from r19
    BRSH highsm1 ; Branch if r19 >= 4 (unsigned)
    NOP
    NOP
    NOP
highsm1: 
    ;BRSH TEST2
    LDI R19,3
    subi r19,4 ; Subtract 4 from r19
    BRSH highsm2 ; Branch if r19 >= 4 (unsigned)
    NOP
    NOP
    NOP
highsm2: 
    ;BRNE TEST
    LDI R16, 20; counter register
    LDI R20, 0       
    LDI R21, 5
LOOP:  
    ADD R20, R21   
    DEC R16;          decrement the counter
    BRNE LOOP;        repeat until counter = 0
    ;BRLT
    LDI R17,16
    LDI R16,1
    CP R16,R17 ; Compare R16 to R25
    BRLT less1 ; Branch if R16 < R25
    NOP
    NOP
    NOP
less1:
    ;BRLT
    LDI R17,1
    LDI R16,16
    CP R16,R17 ; Compare R16 to R25
    BRLT less2 ; Branch if R16 < R25
    NOP
    NOP
    NOP
less2:
    LDI R21,16
    LDI R22,10
    CP R21,R22 ; Compare registers R11 and R12
    BRGE greateq1 ;  Branch if R11 > R12 (signed)
    NOP
    NOP
    NOP
greateq1:
    LDI R21,10
    LDI R22,16
    CP R21,R22 ; Compare registers R11 and R12
    BRGE greateq2 ;  Branch if R11 > R12 (signed)
    NOP
    NOP
    NOP
greateq2:
    LDI R24,255
    LDI R25,1
    ADD R24,R25 ;Add r4 to r3
    BRVS overfl1; Branch if overflow
    NOP
    NOP
    NOP
overfl1:
    LDI R24,255
    LDI R25,0
    ADD R24,R25 ;Add r4 to r3
    BRVS overfl2; Branch if overflow
    NOP
    NOP
    NOP
overfl2:
    LDI R24,255
    LDI R25,0
    ADD R24,R25 ;Add r4 to r3
    BRVS noover1; Branch if overflow
    NOP
    NOP
    NOP
noover1:
    LDI R24,255
    LDI R25,1
    ADD R24,R25 ;Add r4 to r3
    BRVS noover2; Branch if overflow
    NOP
    NOP
    NOP
noover2:
    ;SBRC TEST 1 
    LDI R24,25
    LDI R25,10
    SUB R24,R25 ;Substract R25 from R24
    SBRC R24,7 ; SKIP if bit 7 in R24 cleared 
    SUB R24,R25 ; Only executed if bit7 in R24 not cleared
    ;SBRC TEST 2
    LDI R24,10
    LDI R25,25
    SUB R24,R25 ;Substract R25 from R24
    SBRC R24,7 ; SKIP if bit 7 in R24 cleared 
    SUB R24,R25 ; Only executed if bit7 in R24 not cleared
    ;SBRS TEST1 
    LDI R24,10
    LDI R25,25
    SUB R24,R25 ;Subtract R25 from R24
    SBRS R24,7 ;Skip if bit 7 in R24 set
    NEG R24 ; only executed if bit 7 in R24 not set
    ;SBRS TEST2
    LDI R24,25
    LDI R25,10
    SUB R24,R25 ;Subtract R25 from R24
    SBRS R24,7 ;Skip if bit 7 in R24 set
    NEG R24 ; only executed if bit 7 in R24 not set
    ;CPSE TEST1
    LDI R24,6
    LDI R26,5
    INC R26 ; Increase R26
    CPSE R26,R24 ; Compare R26 to R24
    NEG R26 ; Only executed if R26==R24
    ;CPSE TEST2
    LDI R24,6
    LDI R26,4
    INC R26 ; Increase R26
    CPSE R26,R24 ; Compare R26 to R24
    NEG R26 ; Only executed if R26==R24
    ;CPC 
    ;Compare R3:R2 with R25:R24
    LDI R26,5
    LDI R27,6
    LDI R24,5
    LDI R25,6
    CP R26,R24 ;Compare low byte
    CPC R27,R25 ; Compare high byte 
    BRNE noteq1
    NOP
    NOP
    NOP
noteq1:
    ;CPC 
    ;Compare R3:R27 with R25:R24
    LDI R26,17
    LDI R27,49
    LDI R24,41
    LDI R25,30
    CP R26,R24 ;Compare low byte
    CPC R27,R25 ; Compare high byte 
    BRNE noteq2
    NOP
    NOP
    NOP
noteq2:
    LDI R24,4
    BST R24,2 ; Load T bit with bit 3 of R24 
    BRBS 6,bitset1 ; Branch T bit was set 
    NOP
    NOP
    NOP
bitset1:
    LDI R24,3
    BST R24,2 ; Load T bit with bit 3 of R24 
    BRBS 6,bitset2 ; Branch T bit was set 
    NOP
    NOP
    NOP
bitset2:
    LDI R24,3
    BST R24,2 ; Load T bit with bit 3 of R24 
    BRBC 6,bitcl1 ; Branch T bit was set 
    NOP
    NOP
    NOP
bitcl1:
    LDI R24,4
    BST R24,2 ; Load T bit with bit 3 of R24 
    BRBC 6,bitcl2 ; Branch T bit was set 
    NOP
    NOP
    NOP
bitcl2:
    LDI R26,0
    CPI R26,0x56 ; Compare R26 with 0x56
    BRCS carry1 ; Branch if carry cleared  
    NOP
    NOP
    NOP
carry1:
    LDI R26,0x60
    CPI R26,0x56 ; Compare R26 with 0x56
    BRCS carry2 ; Branch if carry cleared  
    NOP
    NOP
    NOP
carry2:
    LDI R22,255
    LDI R23,1
    ADD R22,R23
    BRCC nocarry1 ; Branch if carry cleared  
    NOP
    NOP
    NOP
nocarry1:
    LDI R22,60
    LDI R23,80
    ADD R22,R23
    BRCC nocarry2 ; Branch if carry cleared 
    NOP
    NOP
    NOP
nocarry2:
    LDI R19,2 
    SUBI R19,4 ; Subtract 4 from R19
    BRMI negative1 ; Branch if result negative 
    NOP
    NOP
    NOP
negative1:
    LDI R19,6 
    SUBI R19,4 ; Subtract 4 from R19
    BRMI negative2 ; Branch if result negative 
    NOP
    NOP
    NOP
negative2:
    SEH
    BRHS hset1 ;Branch if Half Carry flag set 
    NOP
    NOP
    NOP
hset1: ; Branch destination (do nothing)
    CLH
    BRHS hset2 ;Branch if Half Carry flag set 
    NOP
    NOP
    NOP
hset2: ; Branch destination (do nothing)
    CLH
    BRHS hcl1 ;Branch if Half Carry flag clear 
    NOP
    NOP
    NOP
hcl1: ; Branch destination (do nothing)
    SEH
    BRHS hcl2 ;Branch if Half Carry flag clear
    NOP
    NOP
    NOP
hcl2: ; Branch destination (do nothing)
    SET
    BRTS Tset1 
    NOP
    NOP
    NOP
Tset1: ; Branch destination (do nothing)
    CLT
    BRTS Tset2 
    NOP
    NOP
    NOP
Tset2: ; Branch destination (do nothing)
    CLT
    BRTC Tcl1 
    NOP
    NOP
    NOP
Tcl1: ; BrancT destination (do nothing)
    SET
    BRTC Tcl2 
    NOP
    NOP
    NOP
Tcl2: ; Branch destination (do nothing)
    SEV
    BRVS Vset1 ;
    NOP
    NOP
    NOP
Vset1: ; Branch destination (do nothing)
    CLV
    BRVS Vset2 
    NOP
    NOP
    NOP
Vset2: ; Branch destination (do nothing)
    CLV
    BRVC Vcl1 
    NOP
    NOP
    NOP
Vcl1: ; BrancT destination (do nothing)
    SEV
    BRVC Vcl2 
    NOP
    NOP
    NOP
Vcl2: ; Branch destination (do nothing)
    SEI
    BRIE Iset1 
    NOP
    NOP
    NOP
Iset1: ; Branch destination (do nothing)
    CLI
    BRIE Iset2 
    NOP
    NOP
    NOP
Iset2: ; Branch destination (do nothing)
    CLI
    BRID Icl1 
    NOP
    NOP
    NOP
Icl1: ; BrancT destination (do nothing)
    SEI
    BRID Icl2 
    NOP
    NOP
    NOP
Icl2: ; Branch destination (do nothing)
    RET
Sequancer:

    CALL arithmetic
    
    CALL branch 

    CALL memory

asm_function:
    ; --- 3. SAFE HALT ---
halt:
    RJMP halt 

'''





words, symbols = assemble_program(program_Test)
print(f"Assembled {len(words)} instructions")
print(f"Symbols: {symbols}")
dw = 8 
aw = 16

# --- Memory Map Interfaces ---
# 0x000 - 0x01F   GP Registers r0-r31
# 0x0C0 - 0x0C7   USART Registers
# 0x100 - ...     General SRAM
data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

reg_p = punxa.MemoryInterface(hw, 'reg_bus', dw, 5)         # 2^5 = 32 registers
usart_p = punxa.MemoryInterface(hw, 'usart_bus', dw, 3)     # 2^3 = 8 registers
mem_p = punxa.MemoryInterface(hw, 'ram_bus', dw, 11)        # 2048 bytes

# --- Bind Interfaces to the Data Bus ---
punxa.MultiplexedBus(hw, 'bus', data_p, [(reg_p, 0x0), (usart_p, 0xC0), (mem_p, 0x100)])

# --- Base Hardware Components ---
reg = punxa.Ram_Memory(hw, 'reg_mem', dw, 5, reg_p)                 # 32 B
mem = punxa.Ram_Memory(hw, 'ram_mem', dw, 11, mem_p)                # 2048 B
ins_mem = punxa.Ram_Memory(hw, 'ins_mem', 16, 14, ins_p)            # 16 k words (16-bit)
usart = punxa.VirtualUSART(hw, 'usart_block', usart_p)

# --- CPU Control Wires ---
interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
interrupt_wire.put(0)

reset_wire = py4hw.Wire(hw, 'Reset_Line', 1)
reset_wire.put(0)

# --- Instantiate Multicycle Processor ---

cpu = punxa.multicycleProcessor(
    parent=hw, 
    name='multicycle_cpu', 
    Interrupt=interrupt_wire, 
    ins_mem=ins_p, 
    memory=data_p, 
    reset=reset_wire, 
    reset_address=0
)

# --- Waveform Debugging ---
#watch = []
#watch.extend(py4hw.debug.getInterfaceWires(ins_p))
#watch.extend(py4hw.debug.getInterfaceWires(data_p))
#watch.extend(py4hw.debug.getInterfaceWires(reg_p))

#internal CPU wires to the waveform viewer for deeper debug
#watch.append(cpu.w_instruction)
#watch.append(cpu.W_CODE)
#watch.append(cpu.w_rom_address)

#wvf = py4hw.Waveform(hw, 'wvf', watch)

# --- Load Program into Instruction Memory ---
for i, b in enumerate(words):
    ins_mem.writeWord(i, b)

# --- Interactive CLI & GUI Startup ---
import punxa_atmega328p.interactive_commands as ci

# Map the global references so the interactive shell can hook them
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

             The Atmega328p Multicycle System Simulator
'''

print(banner)
py4hw.gui.Workbench(hw)