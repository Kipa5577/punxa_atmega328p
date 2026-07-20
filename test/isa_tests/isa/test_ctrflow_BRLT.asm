; ============================================================
; BRLT (Branch if Less Than - Signed) test suite
; ============================================================
; Tests that BRLT correctly branches when S flag = 1
; which means: Rd < Rr (signed comparison)
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

    rjmp test1

; ============================================================
; TEST 1: Branch if Rd < Rr (positive, no overflow)
; ============================================================
test1:
    ldi r16, 5
    ldi r17, 10
    cp r16, r17

    brlt branch1_ok
    jmp fail
branch1_ok:
    rcall inc_case
    rjmp test2

; ============================================================
; TEST 2: Do NOT Branch if Rd > Rr
; ============================================================
test2:
    ldi r16, 10
    ldi r17, 5
    cp r16, r17

    brge test2_ok
    jmp fail
test2_ok:
    rcall inc_case
    rjmp test3

; ============================================================
; TEST 3: Do NOT Branch if Rd == Rr
; ============================================================
test3:
    ldi r16, 5
    ldi r17, 5
    cp r16, r17

    brge test3_ok
    jmp fail
test3_ok:
    rcall inc_case
    rjmp test4

; ============================================================
; TEST 4: Branch if Rd < Rr (negative values)
; ============================================================
test4:
    ldi r16, -10
    ldi r17, -5
    cp r16, r17

    brlt branch4_ok
    jmp fail
branch4_ok:
    rcall inc_case
    rjmp test5

; ============================================================
; TEST 5: Do NOT Branch if Rd > Rr
; ============================================================
test5:
    ldi r16, -5
    ldi r17, -10
    cp r16, r17

    brge test5_ok
    jmp fail
test5_ok:
    rcall inc_case
    rjmp test6

; ============================================================
; TEST 6: Branch if Rd < Rr (overflow case)
; ============================================================
test6:
    ldi r16, -100
    ldi r17, 100
    cp r16, r17

    brlt branch6_ok
    jmp fail
branch6_ok:
    rcall inc_case
    rjmp test7

; ============================================================
; TEST 7: Do NOT Branch if Rd > Rr (overflow case)
; ============================================================
test7:
    ldi r16, 100
    ldi r17, -100
    cp r16, r17

    brge test7_ok
    jmp fail
test7_ok:
    rcall inc_case
    rjmp test8

; ============================================================
; TEST 8: Branch with SUBI producing negative
; ============================================================
test8:
    ldi r16, 3
    subi r16, 10

    brlt branch8_ok
    jmp fail
branch8_ok:
    rcall inc_case
    rjmp test9

; ============================================================
; TEST 9: Do NOT Branch with SUBI producing positive
; ============================================================
test9:
    ldi r16, 10
    subi r16, 3

    brge test9_ok
    jmp fail
test9_ok:
    rcall inc_case
    rjmp test10

; ============================================================
; TEST 10: Branch with overflow-generated S=1
; ============================================================
test10:
    ldi r16, -128
    ldi r17, -1
    add r16, r17

    brlt branch10_ok
    jmp fail
branch10_ok:
    rcall inc_case
    rjmp test11

; ============================================================
; TEST 11: Branch after CPSE
; ============================================================
test11:
    ldi r16, 5
    ldi r17, 10

    cpse r16, r17
    nop

    cp r16, r17

    brlt branch11_ok
    jmp fail
branch11_ok:
    rcall inc_case
    rjmp test12

; ============================================================
; TEST 12: Branch with S flag set via TST
; ============================================================
test12:
    ldi r16, -5
    tst r16

    brlt branch12_ok
    jmp fail
branch12_ok:
    rcall inc_case
    rjmp test13

; ============================================================
; TEST 13: Branch after CPI
; ============================================================
test13:
    ldi r16, -10
    cpi r16, 5

    brlt branch13_ok
    jmp fail
branch13_ok:
    rcall inc_case
    rjmp test14

; ============================================================
; TEST 14: Do NOT branch when condition false
; ============================================================
test14:
    ldi r16, 10
    ldi r17, 5
    cp r16, r17

    brge test14_ok
    jmp fail
test14_ok:
    rcall inc_case
    rjmp test15

; ============================================================
; TEST 15: Branch with negative comparison
; ============================================================
test15:
    ldi r16, -20
    ldi r17, -5
    cp r16, r17

    brlt branch15_ok
    jmp fail
branch15_ok:
    rcall inc_case
    rjmp test16

; ============================================================
; TEST 16: Do NOT branch when equal
; ============================================================
test16:
    ldi r16, 100
    ldi r17, 100
    cp r16, r17

    brge test16_ok
    jmp fail
test16_ok:
    rcall inc_case
    rjmp success

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