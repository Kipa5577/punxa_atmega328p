; ============================================================
; DEC (Decrement) instruction test suite for ATmega328P
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
; TEST 1: Simple decrement
; 10 - 1 = 9
; ============================================================
test1:
    ldi r16, 10
    dec r16

    cpi r16, 9
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Decrement zero (Wrap-around)
; 0 - 1 = 255 (0xFF)
; ============================================================
test2:
    ldi r16, 0
    dec r16

    cpi r16, 255
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Decrement to zero (Check Zero flag condition)
; 1 - 1 = 0
; ============================================================
test3:
    ldi r16, 1
    dec r16
    
    ; Should set the Zero flag
    brne fail           ; If Z flag NOT set, jump to fail
    cpi r16, 0
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Signed decrement / Negative boundary
; 128 - 1 = 127
; ============================================================
test4:
    ldi r16, 128
    dec r16

    cpi r16, 127
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