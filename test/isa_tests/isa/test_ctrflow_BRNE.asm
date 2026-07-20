; ============================================================
; BRNE (Branch if Not Equal) test suite with local trampolines
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ; Initialize Stack Pointer
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16
    rjmp test1

; ============================================================
; TEST 1: Branch if Rd != Rr
; ============================================================
test1:
    ldi r16, 5
    ldi r17, 10
    cp r16, r17
    brne branch1_ok
    jmp fail_t1
branch1_ok:
    rcall inc_case
    rjmp test2
fail_t1: jmp fail

; ============================================================
; TEST 2: Do NOT Branch if Rd == Rr
; ============================================================
test2:
    ldi r16, 5
    ldi r17, 5
    cp r16, r17
    brne fail_t2
    rcall inc_case
    rjmp test3
fail_t2: jmp fail

; ============================================================
; TEST 3: Branch with CPI (different)
; ============================================================
test3:
    ldi r16, 50
    cpi r16, 100
    brne branch3_ok
    jmp fail_t3
branch3_ok:
    rcall inc_case
    rjmp test4
fail_t3: jmp fail

; ============================================================
; TEST 4: Do NOT Branch with CPI (equal)
; ============================================================
test4:
    ldi r16, 50
    cpi r16, 50
    brne fail_t4
    rcall inc_case
    rjmp test5
fail_t4: jmp fail

; ============================================================
; TEST 5: Branch with SUB (non-zero)
; ============================================================
test5:
    ldi r16, 10
    ldi r17, 3
    sub r16, r17
    brne branch5_ok
    jmp fail_t5
branch5_ok:
    rcall inc_case
    rjmp test6
fail_t5: jmp fail

; ============================================================
; TEST 6: Do NOT Branch with SUB (zero result)
; ============================================================
test6:
    ldi r16, 5
    ldi r17, 5
    sub r16, r17
    brne fail_t6
    rcall inc_case
    rjmp test7
fail_t6: jmp fail

; ============================================================
; TEST 7: Branch with ADD (non-zero)
; ============================================================
test7:
    ldi r16, 10
    ldi r17, 20
    add r16, r17
    brne branch7_ok
    jmp fail_t7
branch7_ok:
    rcall inc_case
    rjmp test8
fail_t7: jmp fail

; ============================================================
; TEST 8: Do NOT Branch with ADD (zero result)
; ============================================================
test8:
    ldi r16, 0x80
    ldi r17, 0x80
    add r16, r17
    brne fail_t8
    rcall inc_case
    rjmp test9
fail_t8: jmp fail

; ============================================================
; TEST 9: Branch with AND (non-zero)
; ============================================================
test9:
    ldi r16, 0xFF
    ldi r17, 0x0F
    and r16, r17
    brne branch9_ok
    jmp fail_t9
branch9_ok:
    rcall inc_case
    rjmp test10
fail_t9: jmp fail

; ============================================================
; TEST 10: Do NOT Branch with AND (zero result)
; ============================================================
test10:
    ldi r16, 0x0F
    ldi r17, 0xF0
    and r16, r17
    brne fail_t10
    rcall inc_case
    rjmp test11
fail_t10: jmp fail

; ============================================================
; TEST 11: Branch with OR (non-zero)
; ============================================================
test11:
    ldi r16, 0x00
    ldi r17, 0x0F
    or r16, r17
    brne branch11_ok
    jmp fail_t11
branch11_ok:
    rcall inc_case
    rjmp test12
fail_t11: jmp fail

; ============================================================
; TEST 12: Do NOT Branch with OR (zero result)
; ============================================================
test12:
    ldi r16, 0x00
    ldi r17, 0x00
    or r16, r17
    brne fail_t12
    rcall inc_case
    rjmp test13
fail_t12: jmp fail

; ============================================================
; TEST 13: Branch with XOR (non-zero)
; ============================================================
test13:
    ldi r16, 0xAA
    ldi r17, 0x55
    eor r16, r17
    brne branch13_ok
    jmp fail_t13
branch13_ok:
    rcall inc_case
    rjmp test14
fail_t13: jmp fail

; ============================================================
; TEST 14: Do NOT Branch with XOR (zero result)
; ============================================================
test14:
    ldi r16, 0xAA
    ldi r17, 0xAA
    eor r16, r17
    brne fail_t14
    rcall inc_case
    rjmp test15
fail_t14: jmp fail

; ============================================================
; TEST 15: Branch with INC (non-zero)
; ============================================================
test15:
    ldi r16, 0x01
    inc r16
    brne branch15_ok
    jmp fail_t15
branch15_ok:
    rcall inc_case
    rjmp test16
fail_t15: jmp fail

; ============================================================
; TEST 16: Do NOT Branch with INC (wrapping)
; ============================================================
test16:
    ldi r16, 0xFF
    inc r16
    brne fail_t16
    rcall inc_case
    rjmp success
fail_t16: jmp fail

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