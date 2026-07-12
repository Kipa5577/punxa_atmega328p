; ============================================================
; RETI (Return from Interrupt) test suite
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SREG_ADDR = 0x5F
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ; Init stack
    ldi r16, 0x03
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

; ============================================================
; TEST 1: Simple RETI after interrupt simulation
; ============================================================
test1:
    cli
    ldi r30, low(return1)
    ldi r31, high(return1)
    push r31
    push r30
    rjmp isr1
return1:
    sei
    cpi r16, 0x42
    brne test1_fail
    rcall inc_case
    rjmp test1_done

test1_fail: rjmp fail

isr1:
    ldi r16, 0x42
    reti

test1_done:

; ============================================================
; TEST 2: RETI re-enables interrupts (sets I flag)
; ============================================================
test2:
    cli
    ldi r30, low(return2)
    ldi r31, high(return2)
    push r31
    push r30
    rjmp isr2
return2:
    brbs 7, i_set2
    rjmp test2_fail
i_set2:
    rcall inc_case
    rjmp test2_done

test2_fail: rjmp fail

isr2:
    reti

test2_done:

; ============================================================
; TEST 3: Nested RETI (simulating nested interrupts)
; ============================================================
test3:
    cli
    ldi r18, 0
    ldi r30, low(return3a)
    ldi r31, high(return3a)
    push r31
    push r30
    rjmp isr3a
return3a:
    cpi r18, 0x03
    brne test3_fail
    rcall inc_case
    rjmp test3_done

test3_fail: rjmp fail

isr3a:
    inc r18
    ldi r30, low(return3b)
    ldi r31, high(return3b)
    push r31
    push r30
    rjmp isr3b
return3b:
    inc r18
    reti

isr3b:
    inc r18
    reti

test3_done:

; ============================================================
; TEST 4: Verify stack pointer behavior with RETI
; ============================================================
test4:
    cli
    in r19, SPL
    in r20, SPH
    ldi r30, low(return4)
    ldi r31, high(return4)
    push r31
    push r30
    rjmp isr4
return4:
    in r21, SPL
    in r22, SPH
    cp r19, r21
    brne test4_fail
    cp r20, r22
    brne test4_fail
    rcall inc_case
    rjmp test4_done

test4_fail: rjmp fail

isr4:
    reti

test4_done:

; ============================================================
; TEST 5: RETI with preserved registers (PUSH/POP)
; ============================================================
test5:
    cli
    ldi r23, 0x11
    ldi r24, 0x22
    ldi r25, 0x33
    ldi r30, low(return5)
    ldi r31, high(return5)
    push r31
    push r30
    rjmp isr5
return5:
    cpi r23, 0x11
    brne test5_fail
    cpi r24, 0x22
    brne test5_fail
    cpi r25, 0x33
    brne test5_fail
    rcall inc_case
    rjmp test5_done

test5_fail: rjmp fail

isr5:
    push r23
    push r24
    push r25
    ldi r23, 0xFF
    ldi r24, 0xFF
    ldi r25, 0xFF
    pop r25
    pop r24
    pop r23
    reti

test5_done:

; ============================================================
; TEST 6: RETI vs RET comparison (RET doesn't set I flag)
; ============================================================
test6:
    cli
    ldi r30, low(ret_return)
    ldi r31, high(ret_return)
    push r31
    push r30
    rjmp test_ret
ret_return:
    brbs 7, test6_fail
    ldi r30, low(reti_return)
    ldi r31, high(reti_return)
    push r31
    push r30
    rjmp test_reti
reti_return:
    brbc 7, test6_fail
    rcall inc_case
    rjmp test6_done

test6_fail: rjmp fail

test_ret:
    ret

test_reti:
    reti

test6_done:

; ============================================================
; TEST 7: Multiple RETI calls (simulating multiple interrupts)
; ============================================================
test7:
    cli
    ldi r28, 0
    ldi r30, low(return7a)
    ldi r31, high(return7a)
    push r31
    push r30
    rjmp isr7a
return7a:
    ldi r30, low(return7b)
    ldi r31, high(return7b)
    push r31
    push r30
    rjmp isr7b
return7b:
    cpi r28, 0x04
    brne test7_fail
    rcall inc_case
    rjmp test7_done

test7_fail: rjmp fail

isr7a:
    inc r28
    reti
isr7b:
    inc r28
    inc r28
    inc r28
    reti

test7_done:

; ============================================================
; TEST 8: RETI after complex stack operations
; ============================================================
test8:
    cli
    ldi r29, 0x01
    ldi r30, 0x02
    ldi r31, 0x03
    ldi r16, low(return8)
    ldi r17, high(return8)
    push r17
    push r16
    rjmp isr8
return8:
    cpi r29, 0x01
    brne test8_fail
    cpi r30, 0x02
    brne test8_fail
    cpi r31, 0x03
    brne test8_fail
    rcall inc_case
    rjmp test8_done

test8_fail: rjmp fail

isr8:
    push r29
    push r30
    push r31
    ldi r29, 0xFF
    ldi r30, 0xFF
    ldi r31, 0xFF
    pop r31
    pop r30
    pop r29
    reti

test8_done:

; ============================================================
; TEST 9: RETI preserves all other flags
; ============================================================
test9:
    cli
    sec
    sez
    sen
    sev
    seh
    set
    ldi r16, low(return9)
    ldi r17, high(return9)
    push r17
    push r16
    rjmp isr9
return9:
    brcc test9_fail      ; C should be 1
    brne test9_fail      ; Z should be 1
    brpl test9_fail      ; N should be 1 (Fixed from BRMI)
    brvc test9_fail      ; V should be 1 (Fixed from BRVS)
    brhc test9_fail      ; H should be 1
    brtc test9_fail      ; T should be 1
    rcall inc_case
    rjmp test9_done

test9_fail: rjmp fail

isr9:
    reti

test9_done:

; ============================================================
; TEST 10: RETI from deep nested ISR simulation
; ============================================================
test10:
    cli
    ldi r16, 0
    ldi r17, low(return10a)
    ldi r18, high(return10a)
    push r18
    push r17
    rjmp isr10a
return10a:
    cpi r16, 0x03
    brne test10_fail
    rcall inc_case
    rjmp test10_done

test10_fail: rjmp fail

isr10a:
    inc r16
    ldi r17, low(return10b)
    ldi r18, high(return10b)
    push r18
    push r17
    rjmp isr10b
return10b:
    inc r16
    reti

isr10b:
    inc r16
    reti

test10_done:

; ============================================================
; TEST 11: Verify RETI encoding (fixed opcode 0x9518)
; ============================================================
test11:
    cli
    ldi r16, low(return11)
    ldi r17, high(return11)
    push r17
    push r16
    rjmp encoding_test11
return11:
    rcall inc_case
    rjmp test11_done

test11_fail: rjmp fail

encoding_test11:
    reti

test11_done:

; ============================================================
; TEST 12: RETI after SPM/ZIG (special cases)
; ============================================================
test12:
    cli
    ldi r16, low(return12)
    ldi r17, high(return12)
    push r17
    push r16
    rjmp isr12
return12:
    rcall inc_case
    rjmp test12_done

test12_fail: rjmp fail

isr12:
    ldi r18, 0xAA
    ldi r19, 0xBB
    add r18, r19
    reti

test12_done:

; ============================================================
; TEST 13: RETI with SREG manually saved/restored
; ============================================================
test13:
    cli
    in r20, SREG_ADDR
    push r20
    ldi r16, low(return13)
    ldi r17, high(return13)
    push r17
    push r16
    rjmp isr13
return13:
    brbs 7, i_ok13
    rjmp test13_fail
i_ok13:
    pop r20
    out SREG_ADDR, r20
    rcall inc_case
    rjmp test13_done

test13_fail: rjmp fail

isr13:
    reti

test13_done:

; ============================================================
; TEST 14: RETI after clearing I flag inside ISR
; ============================================================
test14:
    cli
    ldi r16, low(return14)
    ldi r17, high(return14)
    push r17
    push r16
    rjmp isr14
return14:
    brbc 7, test14_fail
    rcall inc_case
    rjmp test14_done

test14_fail: rjmp fail

isr14:
    cli
    reti

test14_done:

; ============================================================
; TEST 15: RETI with multiple PUSH/POP before return
; ============================================================
test15:
    cli
    ldi r23, 0xDE
    ldi r24, 0xAD
    ldi r25, 0xBE
    ldi r26, 0xEF
    ldi r16, low(return15)
    ldi r17, high(return15)
    push r17
    push r16
    rjmp isr15
return15:
    cpi r23, 0xDE
    brne test15_fail
    cpi r24, 0xAD
    brne test15_fail
    cpi r25, 0xBE
    brne test15_fail
    cpi r26, 0xEF
    brne test15_fail
    rcall inc_case
    rjmp test15_done

test15_fail: rjmp fail

isr15:
    push r23
    push r24
    push r25
    push r26
    ldi r23, 0x00
    ldi r24, 0x00
    ldi r25, 0x00
    ldi r26, 0x00
    pop r26
    pop r25
    pop r24
    pop r23
    reti

test15_done:

; ============================================================
; TEST 16: RETI after stack cleanup (frame pointer)
; ============================================================
test16:
    cli
    ldi r16, low(return16)
    ldi r17, high(return16)
    push r17
    push r16
    rjmp isr16
return16:
    rcall inc_case
    rjmp test16_done

test16_fail: rjmp fail

isr16:
    push r28
    push r29
    in r28, SPL
    in r29, SPH
    st Y, r18
    pop r29
    pop r28
    reti

test16_done:

; ============================================================
; TEST 17: RETI with watchdog simulation
; ============================================================
test17:
    cli
    ldi r16, low(return17)
    ldi r17, high(return17)
    push r17
    push r16
    rjmp isr17
return17:
    rcall inc_case
    rjmp test17_done

test17_fail: rjmp fail

isr17:
    wdr
    reti

test17_done:

; ============================================================
; TEST 18: RETI final test - ensure I flag is set
; ============================================================
test18:
    cli
    ldi r16, low(return18)
    ldi r17, high(return18)
    push r17
    push r16
    rjmp isr18
return18:
    brbc 7, test18_fail
    rcall inc_case
    rjmp success

test18_fail: rjmp fail

isr18:
    reti

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