; ============================================================
; LSR instruction test suite for ATmega328P
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
; TEST 1: Shift zero
; 0x00 >> 1 = 0x00
; ============================================================
test1:
    ldi r16, 0x00
    lsr r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Single-bit LSB
; 0x01 >> 1 = 0x00
; ============================================================
test2:
    ldi r16, 0x01
    lsr r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Even value
; 0x02 >> 1 = 0x01
; ============================================================
test3:
    ldi r16, 0x02
    lsr r16

    cpi r16, 0x01
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: MSB only
; 0x80 >> 1 = 0x40
; ============================================================
test4:
    ldi r16, 0x80
    lsr r16

    cpi r16, 0x40
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: General pattern + carry check behavior
; 0xFF >> 1 = 0x7F
; ============================================================
test5:
    ldi r16, 0xFF
    lsr r16

    cpi r16, 0x7F
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