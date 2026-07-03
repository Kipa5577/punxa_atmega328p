; ============================================================
; IJMP (Indirect Jump) test suite with local trampolines
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
; TEST 1: Simple IJMP to a label
; ============================================================
test1:
    ldi r16, 0
    ldi r30, low(target1)
    ldi r31, high(target1)
    ijmp
    rjmp fail
target1:
    inc r16
    cpi r16, 1
    brne local_fail1
    rcall inc_case
    rjmp test2
local_fail1: rjmp fail

; ============================================================
; TEST 2: IJMP to multiple targets sequentially
; ============================================================
test2:
    ldi r17, 0
    ldi r30, low(func0_2)
    ldi r31, high(func0_2)
    ijmp
back_func0_2:
    ldi r30, low(func1_2)
    ldi r31, high(func1_2)
    ijmp
back_func1_2:
    ldi r30, low(func2_2)
    ldi r31, high(func2_2)
    ijmp
back_func2_2:
    cpi r17, 6
    brne local_fail2
    rcall inc_case
    rjmp test3
local_fail2: rjmp fail

func0_2: inc r17
        inc r17
        rjmp back_func0_2
func1_2: inc r17
        inc r17
        rjmp back_func1_2
func2_2: inc r17
        inc r17
        rjmp back_func2_2

; ============================================================
; TEST 3: Verify IJMP does NOT affect stack
; ============================================================
test3:
    in r18, SPL
    in r19, SPH
    ldi r30, low(stack_check3)
    ldi r31, high(stack_check3)
    ijmp
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
; TEST 4: IJMP with calculated offset (simplified)
; ============================================================
test4:
    ldi r25, 0
    ; Test offset 0
    ldi r30, low(table4)
    ldi r31, high(table4)
    ijmp
back4_a:
    ; Test offset 2 (entry 1)
    ldi r30, low(table4)
    ldi r31, high(table4)
    ldi r24, 1
    add r30, r24
    ldi r16, 0
    adc r31, r16
    ijmp
back4_b:
    ; Test offset 4 (entry 2)
    ldi r30, low(table4)
    ldi r31, high(table4)
    ldi r24, 2
    add r30, r24
    ldi r16, 0
    adc r31, r16
    ijmp
back4_c:
    cpi r25, 6
    brne local_fail4
    rcall inc_case
    rjmp test5
local_fail4: rjmp fail

table4:
    rjmp t4_e0
    rjmp t4_e1
    rjmp t4_e2

t4_e0: inc r25
      inc r25
      rjmp back4_a
t4_e1: inc r25
      inc r25
      rjmp back4_b
t4_e2: inc r25
      inc r25
      rjmp back4_c

; ============================================================
; TEST 5: IJMP chaining
; ============================================================
test5:
    ldi r26, 0
    ldi r30, low(chain5_a)
    ldi r31, high(chain5_a)
    ijmp
chain5_done:
    cpi r26, 3
    brne local_fail5
    rcall inc_case
    rjmp test6
local_fail5: rjmp fail

chain5_a:
    inc r26
    ldi r30, low(chain5_b)
    ldi r31, high(chain5_b)
    ijmp
chain5_b:
    inc r26
    ldi r30, low(chain5_c)
    ldi r31, high(chain5_c)
    ijmp
chain5_c:
    inc r26
    rjmp chain5_done

; ============================================================
; TEST 6: IJMP switch statement
; ============================================================
test6:
    ldi r27, 2
    ldi r30, low(switch_table6)
    ldi r31, high(switch_table6)
    add r30, r27
    ldi r16, 0
    adc r31, r16
    ijmp
switch_return6:
    cpi r28, 2
    brne local_fail6
    rcall inc_case
    rjmp test7
local_fail6: rjmp fail

switch_table6:
    rjmp case0_6
    rjmp case1_6
    rjmp case2_6
case0_6: ldi r28, 0
        rjmp switch_return6
case1_6: ldi r28, 1
        rjmp switch_return6
case2_6: ldi r28, 2
        rjmp switch_return6

; ============================================================
; TEST 7: IJMP with register preservation check
; ============================================================
test7:
    ldi r28, 0
    ldi r20, 0xAA
    ldi r21, 0x55
    ldi r30, low(target7)
    ldi r31, high(target7)
    ijmp
target7:
    inc r28
    cpi r20, 0xAA
    brne local_fail7
    cpi r21, 0x55
    brne local_fail7
    cpi r28, 1
    brne local_fail7
    rcall inc_case
    rjmp test8
local_fail7: rjmp fail

; ============================================================
; TEST 8: IJMP to RJMP
; ============================================================
test8:
    ldi r30, low(encoding_target8)
    ldi r31, high(encoding_target8)
    ijmp
encoding_return8:
    rcall inc_case
    rjmp test9
local_fail8: rjmp fail
encoding_target8: rjmp encoding_return8

; ============================================================
; TEST 9: Loop with IJMP
; ============================================================
test9:
    ldi r16, 0
    ldi r17, 5
loop_ijmp9:
    ldi r30, low(loop_target9)
    ldi r31, high(loop_target9)
    ijmp
loop_return9:
    dec r17
    brne loop_ijmp9
    cpi r16, 5
    brne local_fail9
    rcall inc_case
    rjmp test10
local_fail9: rjmp fail
loop_target9: inc r16
              rjmp loop_return9

; ============================================================
; TEST 10: IJMP to RET
; ============================================================
test10:
    ldi r18, 0x55
    rcall call_ret10
    cpi r18, 0x55
    brne local_fail10
    rcall inc_case
    rjmp test11
local_fail10: rjmp fail

call_ret10:
    ldi r30, low(just_ret10)
    ldi r31, high(just_ret10)
    ijmp
just_ret10: ret

; ============================================================
; TEST 11: IJMP with different Z values
; ============================================================
test11:
    ldi r19, 0
    ; Jump to target A
    ldi r30, low(ijmp_a11)
    ldi r31, high(ijmp_a11)
    ijmp
ijmp_a11:
    inc r19
    ; Jump to target B
    ldi r30, low(ijmp_b11)
    ldi r31, high(ijmp_b11)
    ijmp
ijmp_b11:
    inc r19
    cpi r19, 2
    brne local_fail11
    rcall inc_case
    rjmp test12
local_fail11: rjmp fail

; ============================================================
; TEST 12: IJMP state machine
; ============================================================
test12:
    ldi r22, 0
state_machine12:
    cpi r22, 3
    breq state_done12
    ldi r30, low(state_table12)
    ldi r31, high(state_table12)
    mov r23, r22
    add r30, r23
    ldi r16, 0
    adc r31, r16
    ijmp
state_table12:
    rjmp state0_12
    rjmp state1_12
    rjmp state2_12
state0_12: inc r22
          rjmp state_machine12
state1_12: inc r22
          rjmp state_machine12
state2_12: inc r22
          rjmp state_machine12
state_done12:
    cpi r22, 3
    brne local_fail12
    rcall inc_case
    rjmp success
local_fail12: rjmp fail

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