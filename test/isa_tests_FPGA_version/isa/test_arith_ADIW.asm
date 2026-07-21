; ============================================================
; ADIW instruction test suite (Manual Trampolines)
; ============================================================

.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16
    jmp test1

; ============================================================
; TEST 1: simple addition
; ============================================================
test1:
    ldi r24, 0x10
    ldi r25, 0x00
    adiw r24, 1
    brcs t1_fail_path       ; Manual trampoline
    mov r16, r24
    cpi r16, 0x11
    brne t1_fail_path
    mov r16, r25
    cpi r16, 0x00
    brne t1_fail_path
    call inc_case
    jmp test2
t1_fail_path:
    jmp fail

; ============================================================
; TEST 2: carry propagation
; ============================================================
test2:
    ldi r24, 0xFF
    ldi r25, 0x00
    adiw r24, 1
    brcs t2_fail_path
    mov r16, r24
    cpi r16, 0x00
    brne t2_fail_path
    mov r16, r25
    cpi r16, 0x01
    brne t2_fail_path
    call inc_case
    jmp test3
t2_fail_path:
    jmp fail

; ============================================================
; TEST 3: zero identity
; ============================================================
test3:
    ldi r24, 0x34
    ldi r25, 0x12
    adiw r24, 0
    brcs t3_fail_path
    mov r16, r24
    cpi r16, 0x34
    brne t3_fail_path
    mov r16, r25
    cpi r16, 0x12
    brne t3_fail_path
    call inc_case
    jmp test4
t3_fail_path:
    jmp fail

; ============================================================
; TEST 4: maximum immediate
; ============================================================
test4:
    ldi r24, 0x01
    ldi r25, 0x00
    adiw r24, 63
    brcs t4_fail_path
    mov r16, r24
    cpi r16, 0x40
    brne t4_fail_path
    mov r16, r25
    cpi r16, 0x00
    brne t4_fail_path
    call inc_case
    jmp test5
t4_fail_path:
    jmp fail

; ============================================================
; TEST 5: 16-bit wrap-around
; ============================================================
test5:
    ldi r24, 0xFF
    ldi r25, 0xFF
    adiw r24, 1
    brcc t5_fail_path
    mov r16, r24
    cpi r16, 0x00
    brne t5_fail_path
    mov r16, r25
    cpi r16, 0x00
    brne t5_fail_path
    call inc_case
    jmp test6
t5_fail_path:
    jmp fail

; ============================================================
; TEST 6: near overflow
; ============================================================
test6:
    ldi r24, 0xFE
    ldi r25, 0xFF
    adiw r24, 63
    brcc t6_fail_path
    mov r16, r24
    cpi r16, 0x3D
    brne t6_fail_path
    mov r16, r25
    cpi r16, 0x00
    brne t6_fail_path
    call inc_case
    jmp test7
t6_fail_path:
    jmp fail

; ============================================================
; TEST 7: X register pair
; ============================================================
test7:
    ldi r26, 0x64
    ldi r27, 0x00
    adiw r26, 10
    brcs t7_fail_path
    mov r16, r26
    cpi r16, 0x6E
    brne t7_fail_path
    mov r16, r27
    cpi r16, 0x00
    brne t7_fail_path
    call inc_case
    jmp test8
t7_fail_path:
    jmp fail

; ============================================================
; TEST 8: Y register pair
; ============================================================
test8:
    ldi r28, 0xF0
    ldi r29, 0x00
    adiw r28, 16
    brcs t8_fail_path
    mov r16, r28
    cpi r16, 0x00
    brne t8_fail_path
    mov r16, r29
    cpi r16, 0x01
    brne t8_fail_path
    call inc_case
    jmp test9
t8_fail_path:
    jmp fail

; ============================================================
; TEST 9: Z register pair
; ============================================================
test9:
    ldi r30, 0xFF
    ldi r31, 0xFF
    adiw r30, 1
    brcc t9_fail_path
    mov r16, r30
    cpi r16, 0x00
    brne t9_fail_path
    mov r16, r31
    cpi r16, 0x00
    brne t9_fail_path
    jmp success
t9_fail_path:
    jmp fail

; ============================================================
; Logic & Helpers
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
    jmp end

fail:
    ldi r16, -1
    sts final_result, r16
    jmp end

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret

end:
    rjmp end