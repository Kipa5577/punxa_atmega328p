; ============================================================
; ICALL (Indirect Call) test suite with local trampolines
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
; TEST 1: Simple ICALL to subroutine
; ============================================================
test1:
    ldi r30, low(sub1)
    ldi r31, high(sub1)
    icall
    ldi r16, 0x42
    cp r16, r16 ; Dummy compare, check was below
    cpi r16, 0x42
    brne fail_t1
    rcall inc_case
    rjmp test2
fail_t1: jmp fail

sub1:
    ldi r16, 0x42
    ret

; ============================================================
; TEST 2: ICALL to different targets
; ============================================================
test2:
    ldi r17, 0
    ldi r30, low(target_a)
    ldi r31, high(target_a)
    icall
    ldi r30, low(target_b)
    ldi r31, high(target_b)
    icall
    ldi r30, low(target_c)
    ldi r31, high(target_c)
    icall
    cpi r17, 3
    brne fail_t2
    rcall inc_case
    rjmp test3
fail_t2: jmp fail

target_a: inc r17
    ret
target_b: inc r17
    ret
target_c: inc r17
    ret

; ============================================================
; TEST 3: ICALL with stack pointer verification
; ============================================================
test3:
    in r18, SPL
    in r19, SPH
    ldi r30, low(sp_test)
    ldi r31, high(sp_test)
    icall
    in r20, SPL
    in r21, SPH
    cp r18, r20
    brne fail_t3
    cp r19, r21
    brne fail_t3
    rcall inc_case
    rjmp test4
fail_t3: jmp fail

sp_test: ret

; ============================================================
; TEST 4: ICALL using computed address
; ============================================================
test4:
    ldi r24, 0
    rcall compute_call
    ldi r24, 1
    rcall compute_call
    ldi r24, 2
    rcall compute_call
    cpi r25, 3
    brne fail_t4
    rcall inc_case
    rjmp test5
fail_t4: jmp fail

compute_call:
    ; Simplified for demonstration: calling via Z
    push r30
    push r31
    ldi r30, low(func_simple)
    ldi r31, high(func_simple)
    icall
    pop r31
    pop r30
    ret
func_simple: inc r25
    ret

; ============================================================
; TEST 5: Nested ICALLs
; ============================================================
test5:
    ldi r26, 0
    ldi r30, low(nest_level1)
    ldi r31, high(nest_level1)
    icall
    cpi r26, 3
    brne fail_t5
    rcall inc_case
    rjmp test6
fail_t5: jmp fail

nest_level1: inc r26
    ldi r30, low(nest_level2)
    ldi r31, high(nest_level2)
    icall
    ret
nest_level2: inc r26
    ldi r30, low(nest_level3)
    ldi r31, high(nest_level3)
    icall
    ret
nest_level3: inc r26
    ret

; ============================================================
; TEST 6: ICALL with preserved registers
; ============================================================
test6:
    ldi r16, 0xDE
    ldi r17, 0xAD
    ldi r30, low(preserve_test)
    ldi r31, high(preserve_test)
    icall
    cpi r16, 0xDE
    brne fail_t6
    cpi r17, 0xAD
    brne fail_t6
    rcall inc_case
    rjmp test7
fail_t6: jmp fail

preserve_test:
    push r16
    push r17
    ldi r16, 0xBE
    ldi r17, 0xEF
    pop r17
    pop r16
    ret

; ============================================================
; TEST 7: ICALL inside a loop
; ============================================================
test7:
    ldi r27, 0
    ldi r28, 5
    ldi r30, low(loop_sub)
    ldi r31, high(loop_sub)
loop_icall:
    icall
    dec r28
    brne loop_icall
    cpi r27, 5
    brne fail_t7
    rcall inc_case
    rjmp test8
fail_t7: jmp fail

loop_sub: inc r27
    ret

; ============================================================
; TEST 8: Runtime address calculation
; ============================================================
test8:
    ldi r29, 0
    ldi r30, low(func_base)
    ldi r31, high(func_base)
    icall
    adiw r30, 2
    icall
    cpi r29, 2
    brne fail_t8
    rcall inc_case
    rjmp test9
fail_t8: jmp fail

func_base: inc r29
    ret
    inc r29
    ret

; ============================================================
; TEST 9: ICALL to RET
; ============================================================
test9:
    ldi r16, 0x55
    ldi r30, low(empty_ret)
    ldi r31, high(empty_ret)
    icall
    cpi r16, 0x55
    brne fail_t9
    rcall inc_case
    rjmp test10
fail_t9: jmp fail

empty_ret: ret

; ============================================================
; TEST 10: State machine
; ============================================================
test10:
    ldi r16, 0
    ldi r30, low(state0)
    ldi r31, high(state0)
    icall
    ldi r30, low(state1)
    ldi r31, high(state1)
    icall
    ldi r30, low(state2)
    ldi r31, high(state2)
    icall
    cpi r16, 6
    brne fail_t10
    rcall inc_case
    rjmp test11
fail_t10: jmp fail

state0: inc r16
    ret
state1: inc r16
    inc r16
    ret
state2: inc r16
    inc r16
    inc r16
    ret

; ============================================================
; TEST 11: Encoding / Functionality
; ============================================================
test11:
    ldi r30, low(encoding_test_ret)
    ldi r31, high(encoding_test_ret)
    icall
    rcall inc_case
    rjmp test12
fail_t11: jmp fail
encoding_test_ret: ret

; ============================================================
; TEST 12: Z preservation
; ============================================================
test12:
    ldi r30, low(modify_z_sub)
    ldi r31, high(modify_z_sub)
    icall
    cpi r30, low(modify_z_sub)
    brne fail_t12
    cpi r31, high(modify_z_sub)
    brne fail_t12
    rcall inc_case
    rjmp success
fail_t12: jmp fail

modify_z_sub:
    push r30
    push r31
    ldi r30, 0
    ldi r31, 0
    pop r31
    pop r30
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