; ============================================================
; INC (Increment) instruction test suite for ATmega328P
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
; TEST 1: Simple increment
; 10 + 1 = 11
; ============================================================
test1:
    ldi r16, 10
    inc r16

    cpi r16, 11
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Increment at boundary (Wrap-around)
; 255 + 1 = 0
; ============================================================
test2:
    ldi r16, 255
    inc r16

    cpi r16, 0
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Increment to 1 (Zero Flag Check)
; 0 + 1 = 1
; ============================================================
test3:
    ldi r16, 0
    inc r16
    
    cpi r16, 1
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Signed increment (Negative to Positive boundary)
; 127 + 1 = 128
; ============================================================
test4:
    ldi r16, 127
    inc r16

    cpi r16, 128
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