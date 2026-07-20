; ============================================================
; RJMP (Relative Jump) test suite with local trampolines
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
; TEST 1: Simple forward RJMP
; ============================================================
test1:
    ldi r16, 0
    rjmp target1
    rjmp local_fail1
target1:
    inc r16
    cpi r16, 1
    brne local_fail1
    rcall inc_case
    rjmp test2
local_fail1: rjmp fail

; ============================================================
; TEST 2: Forward then backward RJMP
; ============================================================
test2:
    ldi r17, 0
    rjmp forward2
local_fail2: rjmp fail
forward2:
    inc r17
    rjmp backward2
backward2:
    inc r17
    cpi r17, 2
    brne local_fail2
    rcall inc_case
    rjmp test3

; ============================================================
; TEST 3: Verify RJMP does NOT affect stack
; ============================================================
test3:
    in r18, SPL
    in r19, SPH
    rjmp stack_check3
stack_return3:
    in r20, SPL
    in r21, SPH
    cp r18, r20
    brne local_fail3
    cp r19, r21
    brne local_fail3
    rcall inc_case
    rjmp test4
local_fail3: rjmp fail

stack_check3:
    in r22, SPL
    in r23, SPH
    cp r18, r22
    brne local_fail3
    cp r19, r23
    brne local_fail3
    rjmp stack_return3

; ============================================================
; TEST 4: RJMP out of loop
; ============================================================
test4:
    ldi r24, 0
    ldi r25, 5
loop4:
    inc r24
    dec r25
    brne loop4
    rjmp loop4_done
loop4_done:
    cpi r24, 5
    brne local_fail4
    rcall inc_case
    rjmp test5
local_fail4: rjmp fail

; ============================================================
; TEST 5: Conditional exit from self-loop via RJMP
; ============================================================
test5:
    ldi r26, 0
    rjmp loop5_entry
local_fail5: rjmp fail
loop5_entry:
    inc r26
    cpi r26, 1
    breq loop5_done
    rjmp loop5_entry
loop5_done:
    rcall inc_case
    rjmp test6

; ============================================================
; TEST 6: RJMP chain
; ============================================================
test6:
    ldi r27, 0
    rjmp chain6_1
local_fail6: rjmp fail
chain6_1: inc r27
         rjmp chain6_2
chain6_2: inc r27
         rjmp chain6_3
chain6_3: inc r27
         rjmp chain6_done
chain6_done:
    cpi r27, 3
    brne local_fail6
    rcall inc_case
    rjmp test7

; ============================================================
; TEST 7: RJMP to far target
; ============================================================
test7:
    ldi r28, 0
    rjmp far_target7
local_fail7: rjmp fail
far_target7:
    inc r28
    cpi r28, 1
    brne local_fail7
    rcall inc_case
    rjmp test8

; ============================================================
; TEST 8: RJMP forward then backward
; ============================================================
test8:
    ldi r29, 0
    rjmp forward8
local_fail8: rjmp fail
forward8:
    inc r29
    rjmp backward8
backward8:
    inc r29
    cpi r29, 2
    brne local_fail8
    rcall inc_case
    rjmp test9

; ============================================================
; TEST 9: RJMP skip instruction
; ============================================================
test9:
    ldi r16, 0
    rjmp skip_inc9
    inc r16          ; This should be skipped
skip_inc9:
    inc r16
    cpi r16, 1
    brne local_fail9
    rcall inc_case
    rjmp test10
local_fail9: rjmp fail

; ============================================================
; TEST 10: RJMP 3-level nesting
; ============================================================
test10:
    ldi r17, 0
    rjmp level1_10
local_fail10: rjmp fail
level1_10: inc r17
           rjmp level2_10
level2_10: inc r17
           rjmp level3_10
level3_10: inc r17
           rjmp level_done10
level_done10:
    cpi r17, 3
    brne local_fail10
    rcall inc_case
    rjmp test11

; ============================================================
; TEST 11: RJMP tail call pattern
; ============================================================
test11:
    ldi r18, 1
    rjmp tail_target11
    rjmp fail           ; This should never execute
tail_target11:
    cpi r18, 1
    brne local_fail11   ; ← Local label within range
    rcall inc_case
    rjmp test12
local_fail11: rjmp fail  ; ← RJMP has ±2047 word range

; ============================================================
; TEST 12: RJMP loop with counter
; ============================================================
test12:
    ldi r19, 0
    ldi r20, 10
loop12:
    inc r19
    dec r20
    brne loop12
    rjmp loop12_done
loop12_done:
    cpi r19, 10
    brne local_fail12
    rcall inc_case
    rjmp test13
local_fail12: rjmp fail

; ============================================================
; TEST 13: Multiple RJMP skips
; ============================================================
test13:
    ldi r21, 0
    rjmp skip_block13
    inc r21
    inc r21
    inc r21
skip_block13:
    inc r21
    cpi r21, 1
    brne local_fail13
    rcall inc_case
    rjmp test14
local_fail13: rjmp fail

; ============================================================
; TEST 14: RJMP to immediate next instruction
; ============================================================
test14:
    ldi r22, 0
    rjmp next14
next14:
    inc r22
    cpi r22, 1
    brne local_fail14
    rcall inc_case
    rjmp test15
local_fail14: rjmp fail

; ============================================================
; TEST 15: Long backward RJMP
; ============================================================
test15:
    rjmp forward15
local_fail15: rjmp fail
; Padding to create distance
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
backward_target15:
    ldi r23, 42
    rjmp check15
forward15:
    ldi r23, 0
    rjmp backward_target15
check15:
    cpi r23, 42
    brne local_fail15
    rcall inc_case
    rjmp test16

; ============================================================
; TEST 16: RJMP in conditional structure
; ============================================================
test16:
    ldi r24, 5
    cpi r24, 5
    breq take_branch16
    rjmp local_fail16
take_branch16:
    cpi r24, 5
    brne local_fail16
    rcall inc_case
    rjmp success
local_fail16: rjmp fail

; ============================================================
; SUCCESS / FAILURE logic
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
end: rjmp end

fail:
    ldi r16, 255
    sts final_result, r16
    rjmp end

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret