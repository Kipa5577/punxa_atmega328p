; ============================================================
; CBR instruction test suite for ATmega328P
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
; TEST 1: Clear no bits
; 0x55 CBR 0x00 = 0x55
; ============================================================
test1:
    ldi r16, 0x55
    cbr r16, 0x00

    cpi r16, 0x55
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Clear all bits
; 0xFF CBR 0xFF = 0x00
; ============================================================
test2:
    ldi r16, 0xFF
    cbr r16, 0xFF

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Clear lower nibble
; 0xAF CBR 0x0F = 0xA0
; ============================================================
test3:
    ldi r16, 0xAF
    cbr r16, 0x0F

    cpi r16, 0xA0
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Clear bits already zero
; 0xF0 CBR 0x0F = 0xF0
; ============================================================
test4:
    ldi r16, 0xF0
    cbr r16, 0x0F

    cpi r16, 0xF0
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: General mixed case
; 0x7E CBR 0x24 = 0x5A
; ============================================================
test5:
    ldi r16, 0x7E
    cbr r16, 0x24

    cpi r16, 0x5A
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