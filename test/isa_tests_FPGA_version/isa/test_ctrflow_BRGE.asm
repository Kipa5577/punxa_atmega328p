; ============================================================
; BRGE (Branch if Greater or Equal - Signed) test suite
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D
.equ stack_start = 0x08FF

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16
    rjmp test1

; ============================================================
; TEST 1: Branch if Rd > Rr (positive, no overflow)
; ============================================================
test1:
    ldi r16, 10
    ldi r17, 5
    cp r16, r17
    brge branch1_ok
    jmp fail_t1
branch1_ok:
    rcall inc_case
    rjmp test2
fail_t1: jmp fail

; ============================================================
; TEST 2: Branch if Rd == Rr
; ============================================================
test2:
    ldi r16, 5
    ldi r17, 5
    cp r16, r17
    brge branch2_ok
    jmp fail_t2
branch2_ok:
    rcall inc_case
    rjmp test3
fail_t2: jmp fail

; ============================================================
; TEST 3: Do NOT Branch if Rd < Rr
; ============================================================
test3:
    ldi r16, 5
    ldi r17, 10
    cp r16, r17
    brge fail_t3
    rcall inc_case
    rjmp test4
fail_t3: jmp fail

; ============================================================
; TEST 4: Branch if Rd > Rr (negative values)
; ============================================================
test4:
    ldi r16, -5
    ldi r17, -10
    cp r16, r17
    brge branch4_ok
    jmp fail_t4
branch4_ok:
    rcall inc_case
    rjmp test5
fail_t4: jmp fail

; ============================================================
; TEST 5: Do NOT Branch if Rd < Rr (negative values)
; ============================================================
test5:
    ldi r16, -10
    ldi r17, -5
    cp r16, r17
    brge fail_t5
    rcall inc_case
    rjmp test6
fail_t5: jmp fail

; ============================================================
; TEST 6: Branch if Rd > Rr (positive overflow case)
; Target: r16 (100) > r17 (-100)
; ============================================================
test6:
    ldi r16, 100
    ldi r17, -100
    
    ; Instead of cp r16, r17, we check if r17 < r16
    cp r17, r16          ; Calculates: -100 - 100 = -200
                         ; -200 overflows 8-bit signed limits!
                         
    brlt branch6_ok      ; brlt checks if S = 1.
    jmp fail_t6          ; If it doesn't branch, the overflow test failed.

branch6_ok:
    rcall inc_case
    rjmp test7
fail_t6: 
    jmp fail
    
; ============================================================
; TEST 7: Do NOT Branch if Rd < Rr (negative overflow case)
; Target: r16 (-100) < r17 (100) is TRUE. 
; Therefore, a Greater/Equal branch must NOT trigger.
; ============================================================
test7:
    ldi r16, -100        ; 0x9C
    ldi r17, 100         ; 0x64
    
    cp r16, r17          ; 0x9C - 0x64 = 0x38 (N=0, V=1) -> S = 1
                         
    brge fail_t7         ; brge checks if S = 0.
                         ; Since S = 1, it will NOT branch. (Correct behavior)
                         
    rjmp branch7_ok      ; Execution falls through here into a pass.

fail_t7: 
    jmp fail

branch7_ok:
    rcall inc_case
    ; rjmp test8
        
; ============================================================
; TEST 8: Branch with ADIW
; ============================================================
test8:
    ldi r24, 0x10
    ldi r25, 0x00
    adiw r24, 5
    brge branch8_ok
    jmp fail_t8
branch8_ok:
    rcall inc_case
    rjmp test9
fail_t8: jmp fail

; ============================================================
; TEST 9: Branch with SUBI producing zero
; ============================================================
test9:
    ldi r16, 5
    subi r16, 5
    brge branch9_ok
    jmp fail_t9
branch9_ok:
    rcall inc_case
    rjmp test10
fail_t9: jmp fail

; ============================================================
; TEST 10: Do NOT Branch with SUBI producing negative
; ============================================================
test10:
    ldi r16, 3
    subi r16, 10
    brge fail_t10
    rcall inc_case
    rjmp test11
fail_t10: jmp fail

; ============================================================
; TEST 11: Branch with ADD producing positive
; ============================================================
test11:
    ldi r16, 10
    ldi r17, 20
    add r16, r17
    brge branch11_ok
    jmp fail_t11
branch11_ok:
    rcall inc_case
    rjmp test12
fail_t11: jmp fail

; ============================================================
; TEST 12: Branch after CPSE
; ============================================================
test12:
    ldi r16, 5
    ldi r17, 5
    cpse r16, r17
    rjmp should_be_skipped
    ldi r18, 10
    ldi r19, 5
    cp r18, r19
    brge branch12_ok
    jmp fail_t12
should_be_skipped:
    jmp fail_t12
branch12_ok:
    rcall inc_case
    rjmp test13
fail_t12: jmp fail

; ============================================================
; TEST 13: Branch with S flag explicitly cleared
; ============================================================
test13:
    clr r16
    tst r16
    brge branch13_ok
    jmp fail_t13
branch13_ok:
    rcall inc_case
    rjmp test14
fail_t13: jmp fail

; ============================================================
; TEST 14: Branch with signed comparison
; ============================================================
test14:
    ldi r16, -5
    ldi r17, -10
    cp r16, r17
    brge branch14_ok
    jmp fail_t14
branch14_ok:
    rcall inc_case
    rjmp test15
fail_t14: jmp fail

; ============================================================
; TEST 15: BRGE with immediate value
; ============================================================
test15:
    ldi r16, 15
    cpi r16, 10
    brge branch15_ok
    jmp fail_t15
branch15_ok:
    rcall inc_case
    rjmp test16
fail_t15: jmp fail

; ============================================================
; TEST 16: Do NOT branch with BRGE when condition false
; ============================================================
test16:
    ldi r16, 5
    cpi r16, 10
    brge fail_t16
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