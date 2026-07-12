; ============================================================
; MOV (Copy Register) test suite - ATmega328P SAFE VERSION
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D


reset:
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    rjmp test1_start

; ============================================================
; TEST 1
; ============================================================
test1_start:
    ldi r16, 0x42
    mov r17, r16
    cpi r17, 0x42
    breq t1_ok
    rjmp fail
t1_ok:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2
; ============================================================
test2_start:
    ldi r18, 0x7E
    mov r31, r18
    cpi r31, 0x7E
    breq t2_ok
    rjmp fail
t2_ok:
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3
; ============================================================
test3_start:
    ldi r31, 0xAA
    mov r18, r31
    cpi r18, 0xAA
    breq t3_ok
    rjmp fail
t3_ok:
    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4
; ============================================================
test4_start:
    ldi r16, 0x55
    mov r16, r16
    cpi r16, 0x55
    breq t4_ok
    rjmp fail
t4_ok:
    rcall inc_case
    rjmp test5_start

; ============================================================
; TEST 5
; ============================================================
test5_start:
    ldi r16, 0x00
    mov r17, r16
    cpi r17, 0x00
    breq t5_ok
    rjmp fail
t5_ok:
    rcall inc_case
    rjmp test6_start

; ============================================================
; TEST 6
; ============================================================
test6_start:
    ldi r16, 0xFF
    mov r17, r16
    cpi r17, 0xFF
    breq t6_ok
    rjmp fail
t6_ok:
    rcall inc_case
    rjmp test7_start

; ============================================================
; TEST 7
; ============================================================
test7_start:
    ldi r16, 0x33
    mov r17, r16
    cpi r16, 0x33
    breq t7_ok1
    rjmp fail
t7_ok1:
    cpi r17, 0x33
    breq t7_ok2
    rjmp fail
t7_ok2:
    rcall inc_case
    rjmp test8_start

; ============================================================
; TEST 8
; ============================================================
test8_start:
    in r20, SREG
    ori r20, 0xFF
    out SREG, r20

    ldi r16, 0x55
    mov r17, r16

    in r21, SREG
    cpi r21, 0xFF
    breq t8_ok
    rjmp fail
t8_ok:
    rcall inc_case
    rjmp test9_start

; ============================================================
; TEST 9
; ============================================================
test9_start:
    ldi r16, 0x12
    mov r17, r16
    mov r18, r17
    mov r19, r18
    mov r20, r19

    cpi r20, 0x12
    breq t9_ok
    rjmp fail
t9_ok:
    rcall inc_case
    rjmp test10_start

; ============================================================
; TEST 10
; ============================================================
test10_start:
    ldi r16, 0x01
    mov r17, r16
    mov r18, r17
    mov r19, r18
    mov r20, r19
    mov r21, r20
    mov r22, r21
    mov r23, r22
    mov r24, r23
    mov r25, r24
    mov r26, r25
    mov r27, r26
    mov r28, r27
    mov r29, r28
    mov r30, r29
    mov r31, r30

    cpi r31, 0x01
    breq t10_ok
    rjmp fail
t10_ok:
    rcall inc_case
    rjmp test11_start

; ============================================================
; TEST 11
; ============================================================
test11_start:
    ldi r16, 0xAB
    mov r17, r16
    ldi r16, 0xCD

    cpi r17, 0xAB
    breq t11_ok1
    rjmp fail
t11_ok1:
    cpi r16, 0xCD
    breq t11_ok2
    rjmp fail
t11_ok2:
    rcall inc_case
    rjmp test12_start

; ============================================================
; TEST 12
; ============================================================
test12_start:
    ldi r16, 0xDE
    mov r17, r16
    ldi r17, 0xAD

    cpi r16, 0xDE
    breq t12_ok1
    rjmp fail
t12_ok1:
    cpi r17, 0xAD
    breq t12_ok2
    rjmp fail
t12_ok2:
    rcall inc_case
    rjmp test13_start

; ============================================================
; TEST 13
; ============================================================
test13_start:
    ldi r16, 0x12
    ldi r17, 0x34

    mov r18, r16
    mov r16, r17
    mov r17, r18

    cpi r16, 0x34
    breq t13_ok1
    rjmp fail
t13_ok1:
    cpi r17, 0x12
    breq t13_ok2
    rjmp fail
t13_ok2:
    rcall inc_case
    rjmp test14_start

; ============================================================
; TEST 14
; ============================================================
test14_start:
    ldi r16, 0x55
    mov r17, r16
    cpi r17, 0x55
    breq t14_ok1
    rjmp fail
t14_ok1:
    ldi r16, 0xAA
    mov r17, r16
    cpi r17, 0xAA
    breq t14_ok2
    rjmp fail
t14_ok2:
    rcall inc_case
    rjmp test15_start

; ============================================================
; TEST 15
; ============================================================
test15_start:
    ldi r16, 0xCA
    mov r17, r16
    push r17
    ldi r17, 0x00
    pop r18

    cpi r18, 0xCA
    breq t15_ok
    rjmp fail
t15_ok:
    rcall inc_case
    rjmp test16_start

; ============================================================
; TEST 16
; ============================================================
test16_start:
    ldi r16, 10
    mov r17, r16
    inc r17

    cpi r17, 11
    breq t16_ok1
    rjmp fail
t16_ok1:
    cpi r16, 10
    breq t16_ok2
    rjmp fail
t16_ok2:
    rcall inc_case
    rjmp test17_start

; ============================================================
; TEST 17
; ============================================================
test17_start:
    ldi r16, 0x01
    mov r17, r16
    cpi r17, 0x01
    breq t17_ok
    rjmp fail
t17_ok:
    rcall inc_case
    rjmp test18_start

; ============================================================
; TEST 18
; ============================================================
test18_start:
    ldi r16, 0x80
    mov r17, r16
    cpi r17, 0x80
    breq t18_ok
    rjmp fail
t18_ok:
    rcall inc_case
    rjmp test19_start

; ============================================================
; TEST 19
; ============================================================
test19_start:
    ldi r16, 0xFE
    mov r17, r16
    call mov_sub19
    cpi r17, 0xFE
    breq t19_ok
    rjmp fail
t19_ok:
    rcall inc_case
    rjmp test20_start

mov_sub19:
    ldi r18, 0xFF
    ret

; ============================================================
; TEST 20
; ============================================================
test20_start:
    ldi r16, 0x00
    mov r17, r16
    tst r17
    breq mov_zero_ok20
    rjmp fail

mov_zero_ok20:
    ldi r16, 0x01
    mov r17, r16
    tst r17
    brne mov_nonzero_ok20
    rjmp fail

mov_nonzero_ok20:
    rcall inc_case
    rjmp success

; ============================================================
; SUCCESS / FAILURE
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