; ============================================================
; SBCI instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; SBCI Rd, K  :  Rd = Rd - K - C   (K is an 8-bit immediate)
; Only works on registers r16..r31
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
    ldi r16, 0x08
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
    sbci r16, 20              ; r16 = 10
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
    sbci r16, 20              ; r16 = 9
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
    sbci r16, 55              ; r16 = 0
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
    sbci r16, 55              ; r16 = 255
    cpi r16, 255
    breq skip_4
    rjmp fail
skip_4:
    rcall inc_case
; ============================================================
; TEST 5: subtract zero immediate, carry clear
; C=0 -> 77 - 0 - 0 = 77
; ============================================================
test5:
    clc
    ldi r16, 77
    sbci r16, 0               ; r16 = 77
    cpi r16, 77
    breq skip_5
    rjmp fail
skip_5:
    rcall inc_case
; ============================================================
; TEST 6: subtract zero immediate, carry set
; C=1 -> 77 - 0 - 1 = 76
; ============================================================
test6:
    sec
    ldi r16, 77
    sbci r16, 0               ; r16 = 76
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
    sbci r16, 20              ; r16 = 246
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
    sbci r16, 20              ; r16 = 245
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
    sbci r16, 1               ; r16 = 255
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
    sbci r16, 0               ; r16 = 255
    cpi r16, 255
    breq skip_10
    rjmp fail
skip_10:
    rcall inc_case
; ============================================================
; TEST 11: maximum immediate value, carry clear
; C=0 -> 255 - 255 - 0 = 0
; ============================================================
test11:
    clc
    ldi r16, 255
    sbci r16, 255             ; r16 = 0
    cpi r16, 0
    breq skip_11
    rjmp fail
skip_11:
    rcall inc_case
; ============================================================
; TEST 12: maximum immediate value, carry set
; C=1 -> 255 - 255 - 1 = 255 (underflow, mod 256)
; ============================================================
test12:
    sec
    ldi r16, 255
    sbci r16, 255             ; r16 = 255
    cpi r16, 255
    breq skip_12
    rjmp fail
skip_12:
    rcall inc_case
; ============================================================
; TEST 13: subtract from 255, carry clear
; C=0 -> 255 - 1 - 0 = 254
; ============================================================
test13:
    clc
    ldi r16, 255
    sbci r16, 1               ; r16 = 254
    cpi r16, 254
    breq skip_13
    rjmp fail
skip_13:
    rcall inc_case
; ============================================================
; TEST 14: subtract from 255, carry set
; C=1 -> 255 - 1 - 1 = 253
; ============================================================
test14:
    sec
    ldi r16, 255
    sbci r16, 1               ; r16 = 253
    cpi r16, 253
    breq skip_14
    rjmp fail
skip_14:
    rcall inc_case
; ============================================================
; TEST 15: chained use — SBCI on upper byte of 16-bit value
; 16-bit value: 0x0210 (528), subtract 0x0101 (257) with C=0
; Low byte:  r16 = 0x10, sbci r16, 0x01 -> 0x0F, C=0
; High byte: r17 = 0x02, sbci r17, 0x01 -> 0x01, C=0
; Result: 0x010F (271) = 528 - 257
; ============================================================
test15:
    clc
    ldi r16, 0x10             ; low byte
    ldi r17, 0x02             ; high byte
    sbci r16, 0x01            ; low byte result = 0x0F, no borrow
    sbci r17, 0x01            ; high byte result = 0x01
    cpi r16, 0x0F
    brne fail15
    cpi r17, 0x01
    breq skip_15
fail15:
    rjmp fail
skip_15:
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