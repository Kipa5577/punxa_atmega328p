; ============================================================
; ADC instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
; ============================================================
; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SPH          = 0x3E
.equ SPL          = 0x3D
; -------------------------
; Reset
; -------------------------
reset:
; init stack
    ldi r16, 0x03
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16
; init state
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16
; ============================================================
; TEST 1: simple addition, carry clear
; C=0 -> 10 + 20 + 0 = 30
; ============================================================
test1:
    clc
    ldi r16, 10
    ldi r17, 20
    adc r16, r17              ; r16 = 30
    cpi r16, 30
    breq skip_1
    rjmp fail
skip_1:
    rcall inc_case
; ============================================================
; TEST 2: carry flag contributes to result
; C=1 -> 10 + 20 + 1 = 31
; ============================================================
test2:
    sec
    ldi r16, 10
    ldi r17, 20
    adc r16, r17              ; r16 = 31
    cpi r16, 31
    breq skip_2
    rjmp fail
skip_2:
    rcall inc_case
; ============================================================
; TEST 3: zero identity, carry clear
; C=0 -> 55 + 0 + 0 = 55
; ============================================================
test3:
    clc
    ldi r16, 55
    ldi r17, 0
    adc r16, r17              ; r16 = 55
    cpi r16, 55
    breq skip_3
    rjmp fail
skip_3:
    rcall inc_case
; ============================================================
; TEST 4: zero identity, carry set
; C=1 -> 55 + 0 + 1 = 56
; ============================================================
test4:
    sec
    ldi r16, 55
    ldi r17, 0
    adc r16, r17              ; r16 = 56
    cpi r16, 56
    breq skip_4
    rjmp fail
skip_4:
    rcall inc_case
; ============================================================
; TEST 5: overflow wrap-around, carry clear
; C=0 -> 200 + 100 + 0 = 44 (mod 256)
; ============================================================
test5:
    clc
    ldi r16, 200
    ldi r17, 100
    adc r16, r17              ; r16 = 44
    cpi r16, 44
    breq skip_5
    rjmp fail
skip_5:
    rcall inc_case
; ============================================================
; TEST 6: overflow wrap-around, carry set
; C=1 -> 200 + 100 + 1 = 45 (mod 256)
; ============================================================
test6:
    sec
    ldi r16, 200
    ldi r17, 100
    adc r16, r17              ; r16 = 45
    cpi r16, 45
    breq skip_6
    rjmp fail
skip_6:
    rcall inc_case
; ============================================================
; TEST 7: maximum unsigned overflow, carry clear
; C=0 -> 255 + 1 + 0 = 0
; ============================================================
test7:
    clc
    ldi r16, 255
    ldi r17, 1
    adc r16, r17              ; r16 = 0
    cpi r16, 0
    breq skip_7
    rjmp fail
skip_7:
    rcall inc_case
; ============================================================
; TEST 8: boundary crossed by carry alone
; C=1 -> 255 + 0 + 1 = 0
; ============================================================
test8:
    sec
    ldi r16, 255
    ldi r17, 0
    adc r16, r17              ; r16 = 0
    cpi r16, 0
    breq skip_8
    rjmp fail
skip_8:
    rcall inc_case
; ============================================================
; TEST 9: both operands max, carry clear
; C=0 -> 255 + 255 + 0 = 254 (mod 256)
; ============================================================
test9:
    clc
    ldi r16, 255
    ldi r17, 255
    adc r16, r17              ; r16 = 254
    cpi r16, 254
    breq skip_9
    rjmp fail
skip_9:
    rcall inc_case
; ============================================================
; TEST 10: both operands max, carry set
; C=1 -> 255 + 255 + 1 = 255 (mod 256)
; ============================================================
test10:
    sec
    ldi r16, 255
    ldi r17, 255
    adc r16, r17              ; r16 = 255
    cpi r16, 255
    breq skip_10
    rjmp fail
skip_10:
    rcall inc_case
; ============================================================
; SUCCESS
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end
; ============================================================
; FAILURE
; final_result = -1, stop execution
; ============================================================
fail:
    ldi r16, -1
    sts final_result, r16
    rjmp end
; ============================================================
; increment test_case
; ============================================================
inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret