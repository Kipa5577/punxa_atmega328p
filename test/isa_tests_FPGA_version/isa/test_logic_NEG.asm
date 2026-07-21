; ============================================================
; NEG instruction test suite for ATmega328P
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
; TEST 1: Negation of zero
; NEG(0x00) = 0x00
; ============================================================
test1:
    ldi r16, 0x00
    neg r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Negation of one
; NEG(0x01) = 0xFF
; ============================================================
test2:
    ldi r16, 0x01
    neg r16

    cpi r16, 0xFF
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Negation of -1
; NEG(0xFF) = 0x01
; ============================================================
test3:
    ldi r16, 0xFF
    neg r16

    cpi r16, 0x01
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Overflow corner case
; NEG(0x80) = 0x80
; ============================================================
test4:
    ldi r16, 0x80
    neg r16

    cpi r16, 0x80
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: Typical value
; NEG(0x55) = 0xAB
; ============================================================
test5:
    ldi r16, 0x55
    neg r16

    cpi r16, 0xAB
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