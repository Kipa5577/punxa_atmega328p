; ============================================================
; NOP (No Operation) test suite with local trampolines
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D
.equ GPIOR0 = 0x1E
.equ DATA_START = 0x0200

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
; TEST 1: Register preservation
; ============================================================
test1_start:
    ldi r16, 0x42
    ldi r17, 0x55
    ldi r18, 0xAA
    nop
    nop
    nop
    cpi r16, 0x42
    brne fail_t1
    cpi r17, 0x55
    brne fail_t1
    cpi r18, 0xAA
    brne fail_t1
    rcall inc_case
    rjmp test2_start
fail_t1: jmp fail

; ============================================================
; TEST 2: C flag preservation
; ============================================================
test2_start:
    clc
    nop
    brcs fail_t2
    sec
    nop
    brcc fail_t2
    rcall inc_case
    rjmp test3_start
fail_t2: jmp fail

; ============================================================
; TEST 3: Z flag preservation
; ============================================================
test3_start:
    ldi r16, 0
    tst r16
    nop
    brne fail_t3
    ldi r16, 1
    tst r16
    nop
    breq fail_t3
    rcall inc_case
    rjmp test4_start
fail_t3: jmp fail

; ============================================================
; TEST 4: N flag preservation
; ============================================================
test4_start:
    ldi r16, 0x80
    tst r16
    nop
    brpl fail_t4
    ldi r16, 0x7F
    tst r16
    nop
    brmi fail_t4
    rcall inc_case
    rjmp test5_start
fail_t4: jmp fail

; ============================================================
; TEST 5: V flag preservation
; ============================================================
test5_start:
    ldi r16, 0x7F
    ldi r17, 1
    add r16, r17
    nop
    brvc fail_t5
    clv
    nop
    brvs fail_t5
    rcall inc_case
    rjmp test6_start
fail_t5: jmp fail

; ============================================================
; TEST 6: H flag preservation
; ============================================================
test6_start:
    ldi r16, 0x0F
    ldi r17, 1
    add r16, r17
    nop
    brhc fail_t6
    clh
    nop
    brhs fail_t6
    rcall inc_case
    rjmp test7_start
fail_t6: jmp fail

; ============================================================
; TEST 7: T flag preservation
; ============================================================
test7_start:
    set
    nop
    brtc fail_t7
    clt
    nop
    brts fail_t7
    rcall inc_case
    rjmp test8_start
fail_t7: jmp fail

; ============================================================
; TEST 8: I flag preservation
; ============================================================
test8_start:
    sei
    nop
    brid fail_t8
    cli
    nop
    brie fail_t8
    sei
    rcall inc_case
    rjmp test9_start
fail_t8: jmp fail

; ============================================================
; TEST 9: SRAM preservation
; ============================================================
test9_start:
    ldi r16, 0xDE
    sts DATA_START, r16
    nop
    nop
    nop
    lds r17, DATA_START
    cpi r17, 0xDE
    brne fail_t9
    rcall inc_case
    rjmp test10_start
fail_t9: jmp fail

; ============================================================
; TEST 10: I/O preservation
; ============================================================
test10_start:
    ldi r16, 0xAD
    out GPIOR0, r16
    nop
    nop
    in r17, GPIOR0
    cpi r17, 0xAD
    brne fail_t10
    rcall inc_case
    rjmp test11_start
fail_t10: jmp fail

; ============================================================
; TEST 11: Stack Pointer preservation
; ============================================================
test11_start:
    in r16, SPL
    in r17, SPH
    nop
    nop
    nop
    in r18, SPL
    in r19, SPH
    cp r16, r18
    brne fail_t11
    cp r17, r19
    brne fail_t11
    rcall inc_case
    rjmp test12_start
fail_t11: jmp fail

; ============================================================
; TEST 12: PC Flow (non-branch)
; ============================================================
test12_start:
    ldi r16, 0
    nop
    inc r16
    nop
    inc r16
    nop
    inc r16
    cpi r16, 3
    brne fail_t12
    rcall inc_case
    rjmp test13_start
fail_t12: jmp fail

; ============================================================
; TEST 13: Loop Counter preservation
; ============================================================
test13_start:
    ldi r16, 5
delay_loop:
    nop
    nop
    nop
    dec r16
    brne delay_loop
    cpi r16, 0
    brne fail_t13
    rcall inc_case
    rjmp test14_start
fail_t13: jmp fail

; ============================================================
; TEST 14: Stack operations
; ============================================================
test14_start:
    ldi r16, 0xCA
    push r16
    nop
    nop
    pop r17
    cpi r17, 0xCA
    brne fail_t14
    rcall inc_case
    rjmp test15_start
fail_t14: jmp fail

; ============================================================
; TEST 15: Multiple NOPs
; ============================================================
test15_start:
    ldi r16, 0x12
    ldi r17, 0x34
    nop
    nop
    nop
    nop
    nop
    cpi r16, 0x12
    brne fail_t15
    cpi r17, 0x34
    brne fail_t15
    rcall inc_case
    rjmp test16_start
fail_t15: jmp fail

; ============================================================
; TEST 16: Branch condition integrity
; ============================================================
test16_start:
    ldi r16, 10
    ldi r17, 10
    cp r16, r17
    nop
    breq branch_taken16
    jmp fail_t16
branch_taken16:
    ldi r16, 10
    ldi r17, 20
    cp r16, r17
    nop
    brne branch_taken16b
    jmp fail_t16
branch_taken16b:
    rcall inc_case
    rjmp test17_start
fail_t16: jmp fail

; ============================================================
; TEST 17: Call/Return integrity
; ============================================================
test17_start:
    ldi r16, 0
    rcall nop_sub17
    cpi r16, 1
    brne fail_t17
    rcall inc_case
    rjmp test18_start
nop_sub17:
    nop
    nop
    inc r16
    ret
fail_t17: jmp fail

; ============================================================
; TEST 18: Pre-RET integrity
; ============================================================
test18_start:
    rcall ret_sub18
    rcall inc_case
    rjmp test19_start
ret_sub18:
    push r16
    ldi r16, 0x55
    nop
    nop
    pop r16
    ret
fail_t18: jmp fail

; ============================================================
; TEST 19: SREG Pattern
; ============================================================
test19_start:
    cli
    clt
    clh
    clv
    cln
    clz
    clc
    nop
    nop
    brie fail_t19  
    brtc ok_t19
    rjmp fail_t19  ; Swapped to 16-bit rjmp for safety
ok_t19:
    brhc ok_h19
    rjmp fail_t19
ok_h19:
    brvc ok_v19
    rjmp fail_t19
ok_v19:
    brpl ok_n19
    rjmp fail_t19
ok_n19:
    brne ok_z19
    rjmp fail_t19
ok_z19:
    brcc ok_c19
    rjmp fail_t19
ok_c19:
    rcall inc_case
    rjmp test20_start
fail_t19: jmp fail

; ============================================================
; TEST 20: Encoding Verification
; ============================================================
test20_start:
    ldi r16, 0x00
    nop
    inc r16
    nop
    inc r16
    cpi r16, 2
    brne fail_t20
    rcall inc_case
    rjmp success
fail_t20: jmp fail

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