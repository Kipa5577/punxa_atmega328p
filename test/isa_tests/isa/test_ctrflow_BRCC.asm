; ============================================================
; BRCC (Branch if Carry Clear) test suite (Trampoline Version)
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16
    jmp test1

; ============================================================
; TESTS
; ============================================================
test1:
    clc
    brcc branch1_ok
    jmp fail
branch1_ok:
    call inc_case
    jmp test2

test2:
    sec
    brcc t2_fail_trampoline
    rjmp t2_skip
t2_fail_trampoline:
    jmp fail
t2_skip:
    call inc_case
    jmp test3

test3:
    ldi r16, 0x10
    ldi r17, 0x20
    add r16, r17
    brcc branch3_ok
    jmp fail
branch3_ok:
    call inc_case
    jmp test4

test4:
    ldi r16, 0xFF
    ldi r17, 0x01
    add r16, r17
    brcc t4_fail_trampoline
    rjmp t4_skip
t4_fail_trampoline:
    jmp fail
t4_skip:
    call inc_case
    jmp test5

test5:
    ldi r16, 0x50
    ldi r17, 0x20
    sub r16, r17
    brcc branch5_ok
    jmp fail
branch5_ok:
    call inc_case
    jmp test6

test6:
    ldi r16, 0x20
    ldi r17, 0x50
    sub r16, r17
    brcc t6_fail_trampoline
    rjmp t6_skip
t6_fail_trampoline:
    jmp fail
t6_skip:
    call inc_case
    jmp test7

test7:
    ldi r16, 0x40
    lsl r16
    brcc branch7_ok
    jmp fail
branch7_ok:
    call inc_case
    jmp test8

test8:
    ldi r16, 0x80
    lsl r16
    brcc t8_fail_trampoline
    rjmp t8_skip
t8_fail_trampoline:
    jmp fail
t8_skip:
    call inc_case
    jmp test9

test9:
    ldi r16, 0x02
    lsr r16
    brcc branch9_ok
    jmp fail
branch9_ok:
    call inc_case
    jmp test10

test10:
    ldi r16, 0x01
    lsr r16
    brcc t10_fail_trampoline
    rjmp t10_skip
t10_fail_trampoline:
    jmp fail
t10_skip:
    call inc_case
    jmp test11

test11:
    clc
    ldi r16, 0x02
    ror r16
    brcc branch11_ok
    jmp fail
branch11_ok:
    call inc_case
    jmp test12

test12:
    sec
    brcc t12_fail_trampoline
    rjmp t12_skip
t12_fail_trampoline:
    jmp fail
t12_skip:
    call inc_case
    jmp test13

test13:
    ldi r16, 10
    cpi r16, 5
    brcc branch13_ok
    jmp fail
branch13_ok:
    call inc_case
    jmp test14

test14:
    ldi r16, 3
    cpi r16, 5
    brcc t14_fail_trampoline
    rjmp t14_skip
t14_fail_trampoline:
    jmp fail
t14_skip:
    call inc_case
    jmp test15

test15:
    clc
    brcc branch15_ok
    jmp fail
branch15_ok:
    call inc_case
    jmp test16

test16:
    sec
    brcc t16_fail_trampoline
    rjmp t16_skip
t16_fail_trampoline:
    jmp fail
t16_skip:
    call inc_case
    jmp success

; ============================================================
; SUCCESS / FAILURE / HELPERS
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
    jmp end

fail:
    ldi r16, 255
    sts final_result, r16
    jmp end

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret

end:
    rjmp end