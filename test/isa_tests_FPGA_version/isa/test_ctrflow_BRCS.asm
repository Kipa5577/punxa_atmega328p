; ============================================================
; BRCS (Branch if Carry Set) test suite
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

; ============================================================
; TEST 1: Branch if Carry Flag is SET (C=1)
; ============================================================
test1:
    sec
    brcs branch1_ok
    jmp fail_t1
branch1_ok:
    rcall inc_case
    rjmp test2
fail_t1: jmp fail

; ============================================================
; TEST 2: Do NOT Branch if Carry Flag is CLEAR (C=0)
; ============================================================
test2:
    clc
    brcs fail_t2
    rcall inc_case
    rjmp test3
fail_t2: jmp fail

; ============================================================
; TEST 3: Branch if C=1 after addition
; ============================================================
test3:
    ldi r16, 0xFF
    ldi r17, 0x01
    add r16, r17
    brcs branch3_ok
    jmp fail_t3
branch3_ok:
    rcall inc_case
    rjmp test4
fail_t3: jmp fail

; ============================================================
; TEST 4: Do NOT Branch if C=0 after addition
; ============================================================
test4:
    ldi r16, 0x10
    ldi r17, 0x20
    add r16, r17
    brcs fail_t4
    rcall inc_case
    rjmp test5
fail_t4: jmp fail

; ============================================================
; TEST 5: Branch if C=1 after subtraction
; ============================================================
test5:
    ldi r16, 0x20
    ldi r17, 0x50
    sub r16, r17
    brcs branch5_ok
    jmp fail_t5
branch5_ok:
    rcall inc_case
    rjmp test6
fail_t5: jmp fail

; ============================================================
; TEST 6: Do NOT Branch if C=0 after subtraction
; ============================================================
test6:
    ldi r16, 0x50
    ldi r17, 0x20
    sub r16, r17
    brcs fail_t6
    rcall inc_case
    rjmp test7
fail_t6: jmp fail

; ============================================================
; TEST 7: Branch if C=1 after LSL
; ============================================================
test7:
    ldi r16, 0x80
    lsl r16
    brcs branch7_ok
    jmp fail_t7
branch7_ok:
    rcall inc_case
    rjmp test8
fail_t7: jmp fail

; ============================================================
; TEST 8: Do NOT Branch if C=0 after LSL
; ============================================================
test8:
    ldi r16, 0x40
    lsl r16
    brcs fail_t8
    rcall inc_case
    rjmp test9
fail_t8: jmp fail

; ============================================================
; TEST 9: Branch if C=1 after LSR
; ============================================================
test9:
    ldi r16, 0x01
    lsr r16
    brcs branch9_ok
    jmp fail_t9
branch9_ok:
    rcall inc_case
    rjmp test10
fail_t9: jmp fail

; ============================================================
; TEST 10: Do NOT Branch if C=0 after LSR
; ============================================================
test10:
    ldi r16, 0x02
    lsr r16
    brcs fail_t10
    rcall inc_case
    rjmp test11
fail_t10: jmp fail

; ============================================================
; TEST 11: Branch if C=1 after SEC
; ============================================================
test11:
    sec
    brcs branch11_ok
    jmp fail_t11
branch11_ok:
    rcall inc_case
    rjmp test12
fail_t11: jmp fail

; ============================================================
; TEST 12: Do NOT Branch if C=0 after CLC
; ============================================================
test12:
    clc
    ldi r16, 0x00
    ror r16
    brcs fail_t12
    rcall inc_case
    rjmp test13
fail_t12: jmp fail

; ============================================================
; TEST 13: Branch if C=1 after CPI
; ============================================================
test13:
    ldi r16, 3
    cpi r16, 5
    brcs branch13_ok
    jmp fail_t13
branch13_ok:
    rcall inc_case
    rjmp test14
fail_t13: jmp fail

; ============================================================
; TEST 14: Do NOT Branch if C=0 after CPI
; ============================================================
test14:
    ldi r16, 10
    cpi r16, 5
    brcs fail_t14
    rcall inc_case
    rjmp test15
fail_t14: jmp fail

; ============================================================
; TEST 15: Branch if C=1 after ADC
; ============================================================
test15:
    clc
    ldi r16, 0xFF
    ldi r17, 0x01
    adc r16, r17
    brcs branch15_ok
    jmp fail_t15
branch15_ok:
    rcall inc_case
    rjmp test16
fail_t15: jmp fail

; ============================================================
; TEST 16: Branch if C=1 after ASR
; ============================================================
test16:
    ldi r16, 0x01
    asr r16
    brcs branch16_ok
    jmp fail_t16
branch16_ok:
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