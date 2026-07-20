; ============================================================
; CALL (Call Subroutine) test suite with local trampolines
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
    rjmp test1

; ============================================================
; TEST 1: Simple CALL that returns
; ============================================================
test1:
    ldi r16, 0xAA
    call subroutine1
    cpi r16, 0xBB
    brne fail_t1
    rcall inc_case
    rjmp test2
fail_t1: jmp fail

subroutine1:
    ldi r16, 0xBB
    ret

; ============================================================
; TEST 2: Nested CALLs
; ============================================================
test2:
    ldi r17, 0x11
    call outer
    cpi r17, 0x33
    brne fail_t2
    rcall inc_case
    rjmp test3
fail_t2: jmp fail

outer:
    ldi r17, 0x22
    call inner
    ret
inner:
    ldi r17, 0x33
    ret

; ============================================================
; TEST 3: CALL with multiple PUSH/POP
; ============================================================
test3:
    ldi r18, 0x01
    ldi r19, 0x02
    ldi r20, 0x03
    call push_pop_test
    cpi r18, 0x01
    brne fail_t3
    cpi r19, 0x02
    brne fail_t3
    cpi r20, 0x03
    brne fail_t3
    rcall inc_case
    rjmp test4
fail_t3: jmp fail

push_pop_test:
    push r18
    push r19
    push r20
    ldi r18, 0xFF
    ldi r19, 0xFF
    ldi r20, 0xFF
    pop r20
    pop r19
    pop r18
    ret

; ============================================================
; TEST 4: Stack pointer verification
; ============================================================
test4:
    in r21, SPL
    in r22, SPH
    call sp_test
    in r23, SPL
    in r24, SPH
    cp r21, r23
    brne fail_t4
    cp r22, r24
    brne fail_t4
    rcall inc_case
    rjmp test5
fail_t4: jmp fail

sp_test:
    ret

; ============================================================
; TEST 5: CALL to address
; ============================================================
test5:
    ldi r27, 0
    call far_target
    cpi r27, 0x42
    brne fail_t5
    rcall inc_case
    rjmp test6
fail_t5: jmp fail

far_target:
    ldi r27, 0x42
    ret

; ============================================================
; TEST 6: Multiple CALLs
; ============================================================
test6:
    ldi r28, 0
    call counter_sub
    call counter_sub
    call counter_sub
    cpi r28, 3
    brne fail_t6
    rcall inc_case
    rjmp test7
fail_t6: jmp fail

counter_sub:
    inc r28
    ret

; ============================================================
; TEST 7: CALL with stack frame
; ============================================================
test7:
    call frame_test
    cpi r29, 0xAA
    brne fail_t7
    rcall inc_case
    rjmp test8
fail_t7: jmp fail

frame_test:
    push r16
    push r17
    ldi r16, 0xAA
    ldi r17, 0xBB
    mov r29, r16
    pop r17
    pop r16
    ret

; ============================================================
; TEST 8: CALL inside a loop
; ============================================================
test8:
    ldi r30, 0
    ldi r31, 5
loop_call:
    call loop_sub
    dec r31
    brne loop_call
    cpi r30, 5
    brne fail_t8
    rcall inc_case
    rjmp test9
fail_t8: jmp fail

loop_sub:
    inc r30
    ret

; ============================================================
; TEST 9: CALL with R0 preservation
; ============================================================
test9:
    ldi r16, 0x55
    mov r0, r16
    call ret_test
    ldi r16, 0x55
    cp r0, r16
    brne fail_t9
    rcall inc_case
    rjmp test10
fail_t9: jmp fail

ret_test:
    ; Use high registers to perform addition
    ldi r16, 0xAA
    ldi r17, 0xBB
    add r16, r17
    ret

; ============================================================
; TEST 10: Deep nesting
; ============================================================
test10:
    ldi r16, 0
    call level1
    cpi r16, 5
    brne fail_t10
    rcall inc_case
    rjmp test11
fail_t10: jmp fail

level1:
    inc r16
    cpi r16, 5
    breq level1_done
    call level1
level1_done:
    ret

; ============================================================
; TEST 11: CALL then conditional branch
; ============================================================
test11:
    call get_value
    tst r16
    breq fail_t11
    call get_zero
    tst r16
    brne fail_t11
    rcall inc_case
    rjmp test12
fail_t11: jmp fail

get_value: ldi r16, 0x01
    ret
get_zero: ldi r16, 0x00
    ret

; ============================================================
; TEST 12: CALL with preserved registers
; ============================================================
test12:
    ldi r16, 0xDE
    ldi r17, 0xAD
    call preserve_test
    cpi r16, 0xDE
    brne fail_t12
    cpi r17, 0xAD
    brne fail_t12
    rcall inc_case
    rjmp success
fail_t12: jmp fail

preserve_test:
    push r16
    push r17
    ldi r16, 0xBE
    ldi r17, 0xEF
    pop r17
    pop r16
    ret

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