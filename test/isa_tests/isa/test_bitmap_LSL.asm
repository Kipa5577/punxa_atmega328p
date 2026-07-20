; ============================================================
; LSL instruction test suite for ATmega328P
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
; 0x00 << 1 = 0x00
; ============================================================
test1:
    ldi r16, 0x00
    lsl r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Simple shift
; 0x01 << 1 = 0x02
; ============================================================
test2:
    ldi r16, 0x01
    lsl r16

    cpi r16, 0x02
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: MSB becomes set
; 0x40 << 1 = 0x80
; ============================================================
test3:
    ldi r16, 0x40
    lsl r16

    cpi r16, 0x80
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Carry generation
; 0x80 << 1 = 0x00
; ============================================================
test4:
    ldi r16, 0x80
    lsl r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: All bits set
; 0xFF << 1 = 0xFE
; ============================================================
test5:
    ldi r16, 0xFF
    lsl r16

    cpi r16, 0xFE
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