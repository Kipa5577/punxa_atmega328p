; ============================================================
; RCALL (Relative Call) test suite - CORRECTED
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

    rjmp test1_start

; ============================================================
; GLOBAL FAIL HANDLER (far away)
; ============================================================
fail:
    ldi r16, 255
    sts final_result, r16
    rjmp end

; ============================================================
; TEST COUNTER INCREMENT HELPER
; ============================================================
inc_case_generic:
    push r16            ; Preserve r16 to avoid clobbering test states
    lds r16, test_case
    inc r16
    sts test_case, r16
    pop r16
    ret

; ============================================================
; TEST 1
; ============================================================
test1_fail:
    rjmp fail

test1_start:
    ldi r16, 0xAA
    rcall sub1
    cpi r16, 0xBB
    brne test1_fail    
    rjmp inc1          ; FIXED: Use rjmp to prevent stack accumulation

sub1:
    ldi r16, 0xBB
    ret

inc1:
    rcall inc_case_generic ; FIXED: Update the SRAM counter
    rjmp test2_start       ; FIXED: Jump cleanly to next test

; ============================================================
; TEST 2
; ============================================================
test2_fail:
    rjmp fail

test2_start:
    ldi r17, 0x11
    rcall outer2
    cpi r17, 0x33
    brne test2_fail
    rjmp inc2

outer2:
    ldi r17, 0x22
    rcall inner2
    ret

inner2:
    ldi r17, 0x33
    ret

inc2:
    rcall inc_case_generic
    rjmp test3_start

; ============================================================
; TEST 3
; ============================================================
test3_fail:
    rjmp fail

test3_start:
    ldi r18, 1
    ldi r19, 2
    ldi r20, 3

    rcall pushpop3

    cpi r18, 1
    brne test3_fail
    cpi r19, 2
    brne test3_fail
    cpi r20, 3
    brne test3_fail

    rjmp inc3

pushpop3:
    push r18
    push r19
    push r20

    ldi r18, 9
    ldi r19, 9
    ldi r20, 9

    pop r20
    pop r19
    pop r18
    ret

inc3:
    rcall inc_case_generic
    rjmp test4_start

; ============================================================
; TEST 4
; ============================================================
test4_fail:
    rjmp fail

test4_start:
    in r21, SPL
    in r22, SPH

    rcall sp4

    in r23, SPL
    in r24, SPH

    cp r21, r23
    brne test4_fail
    cp r22, r24
    brne test4_fail

    rjmp inc4

sp4:
    ret

inc4:
    rcall inc_case_generic
    rjmp test5_start

; ============================================================
; TEST 5
; ============================================================
test5_fail:
    rjmp fail

test5_start:
    ldi r27, 0
    rcall near5
    cpi r27, 0x42
    brne test5_fail
    rjmp inc5

near5:
    ldi r27, 0x42
    ret

inc5:
    rcall inc_case_generic
    rjmp test6_start

; ============================================================
; TEST 6
; ============================================================
test6_fail:
    rjmp fail

test6_start:
    ldi r28, 0
    rcall c6
    rcall c6
    rcall c6

    cpi r28, 3
    brne test6_fail
    rjmp inc6

c6:
    inc r28
    ret

inc6:
    rcall inc_case_generic
    rjmp test7_start

; ============================================================
; TEST 7
; ============================================================
test7_fail:
    rjmp fail

test7_start:
    ldi r29, 0xAA
    rcall frame7

    cpi r29, 0xAA
    brne test7_fail
    rjmp inc7

frame7:
    push r16
    push r17

    ldi r16, 0xAA
    mov r29, r16

    pop r17
    pop r16
    ret

inc7:
    rcall inc_case_generic
    rjmp test8_start

; ============================================================
; TEST 8
; ============================================================
test8_fail:
    rjmp fail

test8_start:
    ldi r30, 0
    ldi r31, 5

loop8:
    rcall sub8
    dec r31
    brne loop8          
    
    cpi r30, 5
    brne test8_fail
    rjmp inc8

sub8:
    inc r30
    ret

inc8:
    rcall inc_case_generic
    rjmp test9_start

; ============================================================
; TEST 9
; ============================================================
test9_fail:
    rjmp fail

test9_start:
    ldi r16, 0x55
    mov r1, r16
    rcall sub9
    mov r16, r1
    cpi r16, 0xFF       ; FIXED: Compare to 0xFF (0x55 + 0xAA)
    brne test9_fail
    rjmp inc9

sub9:
    ldi r17, 0xAA
    add r1, r17
    ret

inc9:
    rcall inc_case_generic
    rjmp test10_start

; ============================================================
; TEST 10
; ============================================================
test10_fail:
    rjmp fail

test10_start:
    ldi r16, 0
    rcall level1_10
    cpi r16, 5
    brne test10_fail
    rjmp inc10

level1_10:
    inc r16
    cpi r16, 5
    breq done10
    rcall level1_10
done10:
    ret

inc10:
    rcall inc_case_generic
    rjmp test11_start

; ============================================================
; TEST 11
; ============================================================
test11_fail:
    rjmp fail

test11_start:
    rcall get1_11
    tst r16
    breq test11_fail

    rcall get0_11
    tst r16
    brne test11_fail

    rjmp inc11

get1_11:
    ldi r16, 1
    ret

get0_11:
    ldi r16, 0
    ret

inc11:
    rcall inc_case_generic
    rjmp test12_start

; ============================================================
; TEST 12
; ============================================================
test12_fail:
    rjmp fail

test12_start:
    ldi r16, 0xDE
    ldi r17, 0xAD

    rcall preserve12

    cpi r16, 0xDE
    brne test12_fail
    cpi r17, 0xAD
    brne test12_fail

    rjmp inc12

preserve12:
    push r16
    push r17

    ldi r16, 0xBE
    ldi r17, 0xEF

    pop r17
    pop r16
    ret

inc12:
    rcall inc_case_generic
    rjmp test13_start

; ============================================================
; TEST 13
; ============================================================
test13_fail:
    rjmp fail

test13_start:
    ldi r18, 0
    rcall forward13

    cpi r18, 2
    brne test13_fail
    rjmp inc13

forward13:
    inc r18
    rcall inner13
    ret

inner13:
    inc r18
    ret

inc13:
    rcall inc_case_generic
    rjmp test14_start

; ============================================================
; TEST 14
; ============================================================
test14_fail:
    rjmp fail

test14_start:
    ldi r19, 0
    rcall rel14
    cpi r19, 1
    brne test14_fail
    rjmp inc14

rel14:
    inc r19
    ret

inc14:
    rcall inc_case_generic
    rjmp test15_start

; ============================================================
; TEST 15
; ============================================================
test15_fail:
    rjmp fail

test15_start:
    ldi r20, 0
    rcall tgt15
    cpi r20, 0x55
    brne test15_fail
    rjmp inc15

tgt15:
    ldi r20, 0x55
    ret

inc15:
    rcall inc_case_generic
    rjmp test16_start

; ============================================================
; TEST 16
; ============================================================
test16_fail:
    rjmp fail

test16_start:
    ldi r21, 0
    rcall c16_1
    rcall c16_2
    rcall c16_3

    cpi r21, 3
    brne test16_fail
    rjmp inc16

c16_1:
    inc r21
    ret

c16_2:
    inc r21
    ret

c16_3:
    inc r21
    ret

inc16:
    rcall inc_case_generic
    rjmp test17_start

; ============================================================
; TEST 17
; ============================================================
test17_fail:
    rjmp fail

test17_start:
    ldi r22, 0
    rcall isr17
    cpi r22, 0xAA
    brne test17_fail
    rjmp inc17

isr17:
    ldi r22, 0xAA
    ret

inc17:
    rcall inc_case_generic
    rjmp test18_start

; ============================================================
; TEST 18
; ============================================================
test18_fail:
    rjmp fail

test18_start:
    ldi r23, 0
    rcall s0_18
    rcall s1_18
    rcall s2_18

    cpi r23, 6
    brne test18_fail
    rjmp success        ; FIXED: Clean jump instead of rcall

s0_18: inc r23
       ret
s1_18: inc r23
       inc r23
       ret
s2_18: inc r23
       inc r23
       inc r23
       ret

; ============================================================
; SUCCESS AND END
; ============================================================
success:
    rcall inc_case_generic ; Increment one last time to signify completion (optional, up to your test harness)
    ldi r16, 1
    sts final_result, r16

end:
    rjmp end