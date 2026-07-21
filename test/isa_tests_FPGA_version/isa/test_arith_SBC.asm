; ============================================================
; SBC instruction test suite for ATmega328P
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
; TEST 1: simple subtraction, carry clear
; C=0 -> 30 - 20 - 0 = 10
; ============================================================
test1:
    clc
    ldi r16, 30
    ldi r17, 20
    sbc r16, r17              ; r16 = 10
    cpi r16, 10
    breq skip_1
    rjmp fail
skip_1:
    rcall inc_case
; ============================================================
; TEST 2: carry flag contributes to result
; C=1 -> 30 - 20 - 1 = 9
; ============================================================
test2:
    sec
    ldi r16, 30
    ldi r17, 20
    sbc r16, r17              ; r16 = 9
    cpi r16, 9
    breq skip_2
    rjmp fail
skip_2:
    rcall inc_case
; ============================================================
; TEST 3: zero result, carry clear
; C=0 -> 55 - 55 - 0 = 0
; ============================================================
test3:
    clc
    ldi r16, 55
    ldi r17, 55
    sbc r16, r17              ; r16 = 0
    cpi r16, 0
    breq skip_3
    rjmp fail
skip_3:
    rcall inc_case
; ============================================================
; TEST 4: zero result pushed negative by carry
; C=1 -> 55 - 55 - 1 = 255 (underflow, mod 256)
; ============================================================
test4:
    sec
    ldi r16, 55
    ldi r17, 55
    sbc r16, r17              ; r16 = 255
    cpi r16, 255
    breq skip_4
    rjmp fail
skip_4:
    rcall inc_case
; ============================================================
; TEST 5: subtract zero, carry clear
; C=0 -> 77 - 0 - 0 = 77
; ============================================================
test5:
    clc
    ldi r16, 77
    ldi r17, 0
    sbc r16, r17              ; r16 = 77
    cpi r16, 77
    breq skip_5
    rjmp fail
skip_5:
    rcall inc_case
; ============================================================
; TEST 6: subtract zero, carry set
; C=1 -> 77 - 0 - 1 = 76
; ============================================================
test6:
    sec
    ldi r16, 77
    ldi r17, 0
    sbc r16, r17              ; r16 = 76
    cpi r16, 76
    breq skip_6
    rjmp fail
skip_6:
    rcall inc_case
; ============================================================
; TEST 7: underflow wrap-around, carry clear
; C=0 -> 10 - 20 - 0 = 246 (mod 256)
; ============================================================
test7:
    clc
    ldi r16, 10
    ldi r17, 20
    sbc r16, r17              ; r16 = 246
    cpi r16, 246
    breq skip_7
    rjmp fail
skip_7:
    rcall inc_case
; ============================================================
; TEST 8: underflow wrap-around, carry set
; C=1 -> 10 - 20 - 1 = 245 (mod 256)
; ============================================================
test8:
    sec
    ldi r16, 10
    ldi r17, 20
    sbc r16, r17              ; r16 = 245
    cpi r16, 245
    breq skip_8
    rjmp fail
skip_8:
    rcall inc_case
; ============================================================
; TEST 9: minimum underflow, carry clear
; C=0 -> 0 - 1 - 0 = 255 (mod 256)
; ============================================================
test9:
    clc
    ldi r16, 0
    ldi r17, 1
    sbc r16, r17              ; r16 = 255
    cpi r16, 255
    breq skip_9
    rjmp fail
skip_9:
    rcall inc_case
; ============================================================
; TEST 10: boundary crossed by carry alone
; C=1 -> 0 - 0 - 1 = 255 (mod 256)
; ============================================================
test10:
    sec
    ldi r16, 0
    ldi r17, 0
    sbc r16, r17              ; r16 = 255
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