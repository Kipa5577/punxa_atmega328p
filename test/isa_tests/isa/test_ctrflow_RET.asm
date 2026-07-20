; ============================================================
; RET (Return from Subroutine) test suite with local trampolines
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
; TEST 1: Simple RET
; ============================================================
test1:
    rcall subroutine1
    cpi r16, 0x42
    brne local_fail1
    rcall inc_case
    rjmp test2
local_fail1: jmp fail

subroutine1:
    ldi r16, 0x42
    ret

; ============================================================
; TEST 2: Nested RETs
; ============================================================
test2:
    ldi r17, 0
    rcall outer2
    cpi r17, 0x02
    brne local_fail2
    rcall inc_case
    rjmp test3
local_fail2: jmp fail

outer2:
    inc r17
    rcall inner2
    ret
inner2:
    inc r17
    ret

; ============================================================
; TEST 3: 4-Level Nesting
; ============================================================
test3:
    ldi r18, 0
    rcall level1_3
    cpi r18, 4
    brne local_fail3
    rcall inc_case
    rjmp test4
local_fail3: jmp fail

level1_3: inc r18
          rcall level2_3
          ret
level2_3: inc r18
          rcall level3_3
          ret
level3_3: inc r18
          rcall level4_3
          ret
level4_3: inc r18
          ret

; ============================================================
; TEST 4: Stack Pointer Verification
; ============================================================
test4:
    in r19, SPL
    in r20, SPH
    rcall sp_test4
    in r21, SPL
    in r22, SPH
    cp r19, r21
    brne local_fail4
    cp r20, r22
    brne local_fail4
    rcall inc_case
    rjmp test5
local_fail4: jmp fail

sp_test4: ret

; ============================================================
; TEST 5: PUSH/POP Verification
; ============================================================
test5:
    ldi r25, 0x11
    ldi r26, 0x22
    ldi r27, 0x33
    rcall push_pop_test5
    cpi r25, 0x11
    brne local_fail5
    cpi r26, 0x22
    brne local_fail5
    cpi r27, 0x33
    brne local_fail5
    rcall inc_case
    rjmp test6
local_fail5: jmp fail

push_pop_test5:
    push r25
    push r26
    push r27
    ldi r25, 0xFF
    ldi r26, 0xFF
    ldi r27, 0xFF
    pop r27
    pop r26
    pop r25
    ret

; ============================================================
; TEST 6-8: Misc Calls & Preservation
; ============================================================
test6:
    call subroutine6
    cpi r28, 0x7E
    brne local_fail6
    rcall inc_case
    rjmp test7
local_fail6: jmp fail
subroutine6: ldi r28, 0x7E
             ret

test7:
    ldi r30, low(subroutine7)
    ldi r31, high(subroutine7)
    icall
    cpi r29, 0xAA
    brne local_fail7
    rcall inc_case
    rjmp test8
local_fail7: jmp fail
subroutine7: ldi r29, 0xAA
             ret

test8:
    ldi r16, 0xDE
    ldi r17, 0xAD
    rcall preserve_test8
    cpi r16, 0xDE
    brne local_fail8
    cpi r17, 0xAD
    brne local_fail8
    rcall inc_case
    rjmp test9
local_fail8: jmp fail
preserve_test8: push r16
                push r17
                ldi r16, 0xBE
                ldi r17, 0xEF
                pop r17
                pop r16
                ret

; ============================================================
; TEST 9: Flag Preservation
; ============================================================
test9:
    clc
    clz
    cln
    rcall flag_test9
    brcc next9
    jmp local_fail9
next9:
    breq local_fail9
    brmi local_fail9
    rcall inc_case
    rjmp test10
local_fail9: jmp fail
flag_test9: ret

; ============================================================
; TEST 10: Recursion
; ============================================================
test10:
    ldi r18, 0
    ldi r19, 5
    rcall recursive10
    cpi r18, 5
    brne local_fail10
    rcall inc_case
    rjmp test11
local_fail10: jmp fail
recursive10:
    inc r18
    dec r19
    breq rec_done10
    rcall recursive10
rec_done10: ret

; ============================================================
; TEST 11: Stack Frame Cleanup
; ============================================================
; ============================================================
; TEST 11: Stack Frame Cleanup
; ============================================================
test11:
    rcall frame_test11
    cpi r20, 0x42
    brne local_fail11
    rcall inc_case
    rjmp test12
local_fail11: jmp fail
frame_test11:
    push r16
    push r17
    ldi r20, 0x42
    pop r17
    pop r16
    ret

; ============================================================
; TEST 12-18: Remaining Coverage
; ============================================================
test12:
    rcall isr_sim12
    cpi r21, 0xCC
    brne local_fail12
    rcall inc_case
    rjmp test13
local_fail12: jmp fail
isr_sim12: ldi r21, 0xCC
           ret

test13:
    ldi r22, 0
    rcall a13
    cpi r22, 3
    brne local_fail13
    rcall inc_case
    rjmp test14
local_fail13: jmp fail
a13: inc r22
     rcall b13
     ret
b13: inc r22
     rcall c13
     ret
c13: inc r22
     ret

test14:
    rcall modify_stack_test14
    cpi r23, 0x55
    brne local_fail14
    rcall inc_case
    rjmp test15
local_fail14: jmp fail
modify_stack_test14: ldi r23, 0x55
                     ret

test15: rcall encoding_target15
        rcall inc_case
        rjmp test16
local_fail15: jmp fail
encoding_target15: ret

test16:
    ldi r24, 0x01
    ldi r25, 0x02
    ldi r26, 0x03
    ldi r27, 0x04
    rcall complex_stack16
    cpi r24, 0x01
    brne local_fail16
    cpi r27, 0x04
    brne local_fail16
    rcall inc_case
    rjmp test17
local_fail16: jmp fail
complex_stack16: push r24
                 push r27
                 pop r27
                 pop r24
                 ret

test17: ldi r16, 0
        rcall far_target17
        cpi r16, 1
        brne local_fail17
        rcall inc_case
        rjmp test18
local_fail17: jmp fail
far_target17: inc r16
              ret

test18: rcall tail_test18
        rjmp success
tail_test18: ret

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