; ============================================================
; ROL instruction test suite for ATmega328P
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
; 0x00 ROL (C=0) = 0x00
; ============================================================
test1:
    clc
    ldi r16, 0x00
    rol r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Single bit, no carry-in
; 0x01 ROL (C=0) = 0x02
; ============================================================
test2:
    clc
    ldi r16, 0x01
    rol r16

    cpi r16, 0x02
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Carry-out generation
; 0x80 ROL (C=0) = 0x00, C=1
; ============================================================
test3:
    clc
    ldi r16, 0x80
    rol r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Carry-in effect
; 0x00 ROL (C=1) = 0x01
; ============================================================
test4:
    sec
    ldi r16, 0x00
    rol r16

    cpi r16, 0x01
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: Full pattern rotation
; 0xAA ROL (C=0) = 0x54
; ============================================================
test5:
    clc
    ldi r16, 0xAA
    rol r16

    cpi r16, 0x54
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