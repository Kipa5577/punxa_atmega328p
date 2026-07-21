; ============================================================
; BRSH (Branch if Same or Higher - Unsigned) test suite
; Modified so every BRSH target stays within ±63 words
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
    sts final_result, r16

; ============================================================
; TEST 1: Branch if Rd > Rr (unsigned)
; ============================================================
test1:
    ldi r16, 10
    ldi r17, 5
    cp r16, r17

    brsh branch1_ok
    rjmp fail
branch1_ok:
    rcall inc_case

; ============================================================
; TEST 2: Branch if Rd == Rr (unsigned)
; ============================================================
test2:
    ldi r16, 5
    ldi r17, 5
    cp r16, r17

    brsh branch2_ok
    rjmp fail
branch2_ok:
    rcall inc_case

; ============================================================
; TEST 3: Do NOT Branch if Rd < Rr (unsigned)
; ============================================================
test3:
    ldi r16, 5
    ldi r17, 10
    cp r16, r17

    brsh test3_fail
    rcall inc_case
    rjmp test3_done

test3_fail:
    rjmp fail

test3_done:

; ============================================================
; TEST 4: Branch with CPI (Rd > Rr)
; ============================================================
test4:
    ldi r16, 200
    cpi r16, 100

    brsh branch4_ok
    rjmp fail
branch4_ok:
    rcall inc_case

; ============================================================
; TEST 5: Branch with CPI (Rd == Rr)
; ============================================================
test5:
    ldi r16, 150
    cpi r16, 150

    brsh branch5_ok
    rjmp fail
branch5_ok:
    rcall inc_case

; ============================================================
; TEST 6: Do NOT Branch with CPI (Rd < Rr)
; ============================================================
test6:
    ldi r16, 50
    cpi r16, 100

    brsh test6_fail
    rcall inc_case
    rjmp test6_done

test6_fail:
    rjmp fail

test6_done:

; ============================================================
; TEST 7: Branch with SUB that doesn't cause borrow
; ============================================================
test7:
    ldi r16, 10
    ldi r17, 3
    sub r16, r17

    brsh branch7_ok
    rjmp fail
branch7_ok:
    rcall inc_case

; ============================================================
; TEST 8: Do NOT Branch with SUB that causes borrow
; ============================================================
test8:
    ldi r16, 3
    ldi r17, 10
    sub r16, r17

    brsh test8_fail
    rcall inc_case
    rjmp test8_done

test8_fail:
    rjmp fail

test8_done:

; ============================================================
; TEST 9: Branch with maximum values (Rd == Rr)
; ============================================================
test9:
    ldi r16, 255
    ldi r17, 255
    cp r16, r17

    brsh branch9_ok
    rjmp fail
branch9_ok:
    rcall inc_case

; ============================================================
; TEST 10: Branch with Rd > Rr (boundary)
; ============================================================
test10:
    ldi r16, 255
    ldi r17, 254
    cp r16, r17

    brsh branch10_ok
    rjmp fail
branch10_ok:
    rcall inc_case

; ============================================================
; TEST 11: Branch with ADD that doesn't set C
; ============================================================
test11:
    ldi r16, 10
    ldi r17, 20
    add r16, r17

    brsh branch11_ok
    rjmp fail
branch11_ok:
    rcall inc_case

; ============================================================
; TEST 12: Do NOT Branch with ADD that sets C
; ============================================================
test12:
    ldi r16, 0xFF
    ldi r17, 0x01
    add r16, r17

    brsh test12_fail
    rcall inc_case
    rjmp test12_done

test12_fail:
    rjmp fail

test12_done:

; ============================================================
; TEST 13: Branch with ADIW (unsigned word addition)
; ============================================================
test13:
    ldi r24, 0xF0
    ldi r25, 0x00
    adiw r24, 16

    brsh branch13_ok
    rjmp fail
branch13_ok:
    rcall inc_case

; ============================================================
; TEST 14: Branch after CLC
; ============================================================
test14:
    clc

    brsh branch14_ok
    rjmp fail
branch14_ok:
    rcall inc_case

; ============================================================
; TEST 15: Branch with LSL that doesn't set C
; ============================================================
test15:
    ldi r16, 0x40
    lsl r16

    brsh branch15_ok
    rjmp fail
branch15_ok:
    rcall inc_case

; ============================================================
; TEST 16: Do NOT Branch with LSL that sets C
; ============================================================
test16:
    ldi r16, 0x80
    lsl r16

    brsh test16_fail
    rcall inc_case
    rjmp success

test16_fail:
    rjmp fail

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