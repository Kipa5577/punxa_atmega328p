; ============================================================
; JMP (Direct Jump) test suite with local trampolines
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
    jmp test1_start

; ============================================================
; TEST 1: Simple JMP
; ============================================================
test1_start:
    ldi r16, 0
    jmp target1
    rjmp local_fail1
target1:
    inc r16
    cpi r16, 1
    brne local_fail1
    rcall inc_case
    jmp test2_start
local_fail1: jmp fail

; ============================================================
; TEST 2: Far JMP
; ============================================================
test2_start:
    ldi r17, 0
    jmp far_target2
    rjmp local_fail2
far_target2:
    inc r17
    cpi r17, 1
    brne local_fail2
    rcall inc_case
    jmp test3_start
local_fail2: jmp fail

; ============================================================
; TEST 3: Verify stack neutrality
; ============================================================
test3_start:
    in r18, SPL
    in r19, SPH
    jmp stack_check3
stack_return3:
    in r20, SPL
    in r21, SPH
    cp r18, r20
    brne local_fail3
    cp r19, r21
    brne local_fail3
    rcall inc_case
    jmp test4_start
local_fail3: jmp fail

stack_check3:
    in r22, SPL
    in r23, SPH
    cp r18, r22
    brne local_fail3
    cp r19, r23
    brne local_fail3
    jmp stack_return3

; ============================================================
; TEST 4: JMP Loop
; ============================================================
test4_start:
    ldi r24, 0
    ldi r25, 5
loop4:
    inc r24
    dec r25
    brne loop4_continue
    jmp loop4_done
loop4_continue:
    jmp loop4
loop4_done:
    cpi r24, 5
    brne local_fail4
    rcall inc_case
    jmp test5_start
local_fail4: jmp fail

; ============================================================
; TEST 5: JMP to target with return
; ============================================================
test5_start:
    ldi r26, 0
    jmp jmp_target5
    rjmp local_fail5
jmp_target5:
    inc r26
    cpi r26, 1
    brne local_fail5
    rjmp back_from_jmp5
back_from_jmp5:
    rcall inc_case
    jmp test6_start
local_fail5: jmp fail

; ============================================================
; TEST 6: JMP Chain
; ============================================================
test6_start:
    ldi r27, 0
    jmp chain1
local_fail6: jmp fail
chain1: inc r27
        jmp chain2
chain2: inc r27
        jmp chain3
chain3: inc r27
        jmp chain_done
chain_done:
    cpi r27, 3
    brne local_fail6
    rcall inc_case
    jmp test7_start

; ============================================================
; TEST 7: JMP skipping multiple instructions
; ============================================================
test7_start:
    ldi r28, 0
    jmp skip_block7
    inc r28
    inc r28
    inc r28
    inc r28
    inc r28
skip_block7:
    inc r28
    cpi r28, 1
    brne local_fail7
    rcall inc_case
    jmp test8_start
local_fail7: jmp fail

; ============================================================
; TEST 8: Reset simulation
; ============================================================
test8_start:
    ldi r16, 0
    jmp reset_vector8
local_fail8: jmp fail
reset_vector8:
    inc r16
    jmp main8
main8:
    inc r16
    cpi r16, 2
    brne local_fail8
    rcall inc_case
    jmp test9_start

; ============================================================
; TEST 9: Self-JMP loop
; ============================================================
test9_start:
    ldi r17, 0
    jmp loop9_entry
local_fail9: jmp fail
loop9_entry:
    inc r17
    cpi r17, 1
    breq loop9_done
    jmp loop9_entry
loop9_done:
    rcall inc_case
    jmp test10_start

; ============================================================
; TEST 10: Conditional JMP
; ============================================================
test10_start:
    ldi r18, 0
    cpi r18, 0
    breq take_jmp10
    rjmp local_fail10
take_jmp10:
    jmp target10
local_fail10: jmp fail
target10:
    inc r18
    cpi r18, 1
    brne local_fail10
    rcall inc_case
    jmp test11_start

; ============================================================
; TEST 11: Forward/Backward JMP
; ============================================================
test11_start:
    ldi r19, 0
    jmp forward11
local_fail11: jmp fail
forward11:
    inc r19
    jmp backward11
backward11:
    inc r19
    cpi r19, 2
    brne local_fail11
    rcall inc_case
    jmp test12_start

; ============================================================
; TEST 12: Success
; ============================================================
test12_start:
    ldi r20, 0
    jmp far_away12
local_fail12: jmp fail
far_away12:
    inc r20
    cpi r20, 1
    brne local_fail12
    rcall inc_case
    jmp success

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