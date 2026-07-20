; ============================================================
; ROR instruction test suite for ATmega328P
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ldi r16, 0x03
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Zero rotation
; 0x00 ROR (C=0) = 0x00
; ============================================================
test1:
    clc
    ldi r16, 0x00
    ror r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: LSB → carry
; 0x01 ROR (C=0) = 0x00
; ============================================================
test2:
    clc
    ldi r16, 0x01
    ror r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Even value shift
; 0x02 ROR (C=0) = 0x01
; ============================================================
test3:
    clc
    ldi r16, 0x02
    ror r16

    cpi r16, 0x01
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Carry-in injects MSB
; 0x00 ROR (C=1) = 0x80
; ============================================================
test4:
    sec
    ldi r16, 0x00
    ror r16

    cpi r16, 0x80
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: Pattern rotation
; 0x55 ROR (C=0) = 0x2A
; ============================================================
test5:
    clc
    ldi r16, 0x55
    ror r16

    cpi r16, 0x2A
    brne fail
    rcall inc_case

; ============================================================
; SUCCESS / FAILURE logic
; ============================================================

success:
    ldi r16, 1
    sts final_result, r16

end:
    rjmp end

fail:
    ldi r16, 255
    sts final_result, r16
    rjmp end

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret