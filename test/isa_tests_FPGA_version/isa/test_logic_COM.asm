; ============================================================
; COM (Complement) instruction test suite for ATmega328P
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
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
; TEST 1: Complement all zeros
; 0x00 -> 0xFF
; ============================================================
test1:
    ldi r16, 0x00
    com r16

    cpi r16, 0xFF
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Complement all ones
; 0xFF -> 0x00
; ============================================================
test2:
    ldi r16, 0xFF
    com r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Pattern inversion
; 0xAA (10101010) -> 0x55 (01010101)
; ============================================================
test3:
    ldi r16, 0xAA
    com r16

    cpi r16, 0x55
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Double complement (Identity)
; ((NOT X) NOT) = X
; ============================================================
test4:
    ldi r16, 0x33
    com r16          ; 0x33 becomes 0xCC
    com r16          ; 0xCC becomes 0x33

    cpi r16, 0x33
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