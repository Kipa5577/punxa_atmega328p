; ============================================================
; LDI (Load Immediate) test suite
; ============================================================
; Tests that LDI correctly:
; 1. Loads an 8-bit constant into the destination register
; 2. Only works with registers R16-R31 (upper half)
; 3. Does not modify any flags
; ============================================================
; LDI is a 1-word (16-bit) instruction
; Format: 1110 KKKK dddd KKKK
; Operation: Rd <- K (8-bit constant)
; Registers: R16-R31 only
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ; Initialize stack pointer
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    ldi r16, 0
    sts final_result, r16

    rjmp test1_start

; ============================================================
; TEST 1: LDI to R16 (smallest upper register)
; ============================================================
test1_start:
    ldi r16, 0x42
    cpi r16, 0x42
    breq test1_ok
    jmp fail
test1_ok:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: LDI to R31 (largest register)
; ============================================================
test2_start:
    ldi r31, 0x7E
    cpi r31, 0x7E
    breq test2_ok
    jmp fail
test2_ok:
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: LDI with 0x00 value
; ============================================================
test3_start:
    ldi r17, 0x00
    cpi r17, 0x00
    breq test3_ok
    jmp fail
test3_ok:
    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4: LDI with 0xFF value
; ============================================================
test4_start:
    ldi r18, 0xFF
    cpi r18, 0xFF
    breq test4_ok
    jmp fail
test4_ok:
    rcall inc_case
    rjmp test5_start

; ============================================================
; TEST 5: LDI with 0x01 value
; ============================================================
test5_start:
    ldi r19, 0x01
    cpi r19, 0x01
    breq test5_ok
    jmp fail
test5_ok:
    rcall inc_case
    rjmp test6_start

; ============================================================
; TEST 6: LDI with 0x80 value (MSB set)
; ============================================================
test6_start:
    ldi r20, 0x80
    cpi r20, 0x80
    breq test6_ok
    jmp fail
test6_ok:
    rcall inc_case
    rjmp test7_start

; ============================================================
; TEST 7: LDI to all upper registers (R16-R31)
; ============================================================
test7_start:
    ldi r16, 0x10
    ldi r17, 0x11
    ldi r18, 0x12
    ldi r19, 0x13
    ldi r20, 0x14
    ldi r21, 0x15
    ldi r22, 0x16
    ldi r23, 0x17
    ldi r24, 0x18
    ldi r25, 0x19
    ldi r26, 0x1A
    ldi r27, 0x1B
    ldi r28, 0x1C
    ldi r29, 0x1D
    ldi r30, 0x1E
    ldi r31, 0x1F

    cpi r16, 0x10
    breq test7_chk1
    jmp fail
test7_chk1:
    cpi r17, 0x11
    breq test7_chk2
    jmp fail
test7_chk2:
    cpi r18, 0x12
    breq test7_chk3
    jmp fail
test7_chk3:
    cpi r19, 0x13
    breq test7_chk4
    jmp fail
test7_chk4:
    cpi r20, 0x14
    breq test7_chk5
    jmp fail
test7_chk5:
    cpi r21, 0x15
    breq test7_chk6
    jmp fail
test7_chk6:
    cpi r22, 0x16
    breq test7_chk7
    jmp fail
test7_chk7:
    cpi r23, 0x17
    breq test7_chk8
    jmp fail
test7_chk8:
    cpi r24, 0x18
    breq test7_chk9
    jmp fail
test7_chk9:
    cpi r25, 0x19
    breq test7_chk10
    jmp fail
test7_chk10:
    cpi r26, 0x1A
    breq test7_chk11
    jmp fail
test7_chk11:
    cpi r27, 0x1B
    breq test7_chk12
    jmp fail
test7_chk12:
    cpi r28, 0x1C
    breq test7_chk13
    jmp fail
test7_chk13:
    cpi r29, 0x1D
    breq test7_chk14
    jmp fail
test7_chk14:
    cpi r30, 0x1E
    breq test7_chk15
    jmp fail
test7_chk15:
    cpi r31, 0x1F
    breq test7_ok
    jmp fail
test7_ok:
    rcall inc_case
    rjmp test8_start

; ============================================================
; TEST 8: LDI does not modify flags
; ============================================================
test8_start:
    ; Set all flags
    sec                 ; C=1
    sez                 ; Z=1
    sen                 ; N=1
    sev                 ; V=1
    seh                 ; H=1
    set                 ; T=1

    ; Execute LDI (should not change flags)
    ldi r16, 0x55

    ; Verify all flags still set
    brcs test8_chk1
    jmp fail
test8_chk1:
    breq test8_chk2
    jmp fail
test8_chk2:
    brmi test8_chk3
    jmp fail
test8_chk3:
    brvs test8_chk4
    jmp fail
test8_chk4:
    brhs test8_chk5
    jmp fail
test8_chk5:
    brts test8_ok
    jmp fail
test8_ok:
    rcall inc_case
    rjmp test9_start

; ============================================================
; TEST 9: LDI with overlapping writes
; ============================================================
test9_start:
    ldi r16, 0xAA
    ldi r16, 0xBB
    cpi r16, 0xBB
    breq test9_ok
    jmp fail
test9_ok:
    rcall inc_case
    rjmp test10_start

; ============================================================
; TEST 10: LDI followed by ADD (verify register content)
; ============================================================
test10_start:
    ldi r16, 0x10
    ldi r17, 0x20
    add r16, r17
    cpi r16, 0x30
    breq test10_ok
    jmp fail
test10_ok:
    rcall inc_case
    rjmp test11_start

; ============================================================
; TEST 11: LDI followed by SUB
; ============================================================
test11_start:
    ldi r16, 0x50
    ldi r17, 0x30
    sub r16, r17
    cpi r16, 0x20
    breq test11_ok
    jmp fail
test11_ok:
    rcall inc_case
    rjmp test12_start

; ============================================================
; TEST 12: LDI to initialize pointer registers
; ============================================================
test12_start:
    ; Initialize X pointer (R27:R26)
    ldi r26, 0x34
    ldi r27, 0x12
    cpi r26, 0x34
    breq test12_chk1
    jmp fail
test12_chk1:
    cpi r27, 0x12
    breq test12_chk2
    jmp fail
test12_chk2:
    ; Initialize Y pointer (R29:R28)
    ldi r28, 0x78
    ldi r29, 0x56
    cpi r28, 0x78
    breq test12_chk3
    jmp fail
test12_chk3:
    cpi r29, 0x56
    breq test12_chk4
    jmp fail
test12_chk4:
    ; Initialize Z pointer (R31:R30)
    ldi r30, 0xBC
    ldi r31, 0x9A
    cpi r30, 0xBC
    breq test12_chk5
    jmp fail
test12_chk5:
    cpi r31, 0x9A
    breq test12_ok
    jmp fail
test12_ok:
    rcall inc_case
    rjmp test13_start

; ============================================================
; TEST 13: LDI with value 0x00 (zero register)
; ============================================================
test13_start:
    ldi r16, 0x00
    cpi r16, 0x00
    breq test13_ok
    jmp fail
test13_ok:
    rcall inc_case
    rjmp test14_start

; ============================================================
; TEST 14: LDI with pattern alternating bits (0x55)
; ============================================================
test14_start:
    ldi r16, 0x55
    cpi r16, 0x55
    breq test14_ok
    jmp fail
test14_ok:
    rcall inc_case
    rjmp test15_start

; ============================================================
; TEST 15: LDI with pattern alternating bits (0xAA)
; ============================================================
test15_start:
    ldi r16, 0xAA
    cpi r16, 0xAA
    breq test15_ok
    jmp fail
test15_ok:
    rcall inc_case
    rjmp test16_start

; ============================================================
; TEST 16: LDI with all possible upper registers in loop
; ============================================================
test16_start:
    ldi r16, 0
    ldi r17, 1
    ldi r18, 2
    ldi r19, 3
    ldi r20, 4
    ldi r21, 5
    ldi r22, 6
    ldi r23, 7
    ldi r24, 8
    ldi r25, 9
    ldi r26, 10
    ldi r27, 11
    ldi r28, 12
    ldi r29, 13
    ldi r30, 14
    ldi r31, 15

    ; Add them all to R16
    add r16, r17
    add r16, r18
    add r16, r19
    add r16, r20
    add r16, r21
    add r16, r22
    add r16, r23
    add r16, r24
    add r16, r25
    add r16, r26
    add r16, r27
    add r16, r28
    add r16, r29
    add r16, r30
    add r16, r31

    ; Sum 0+1+2+...+15 = 120 (0x78)
    cpi r16, 0x78
    breq test16_ok
    jmp fail
test16_ok:
    rcall inc_case
    rjmp test17_start

; ============================================================
; TEST 17: LDI into register then push/pop
; ============================================================
test17_start:
    ldi r16, 0xDE
    push r16
    ldi r16, 0xAD
    pop r17
    cpi r17, 0xDE
    breq test17_ok
    jmp fail
test17_ok:
    rcall inc_case
    rjmp test18_start

; ============================================================
; TEST 18: Multiple LDIs to same register in sequence
; ============================================================
test18_start:
    ldi r16, 0x01
    ldi r16, 0x02
    ldi r16, 0x03
    ldi r16, 0x04
    ldi r16, 0x05

    cpi r16, 0x05
    breq test18_ok
    jmp fail
test18_ok:
    rcall inc_case
    rjmp test19_start

; ============================================================
; TEST 19: LDI used in arithmetic expression
; ============================================================
test19_start:
    ldi r16, 10
    ldi r17, 20
    ldi r18, 30

    add r16, r17
    add r16, r18

    cpi r16, 60
    breq test19_ok
    jmp fail
test19_ok:
    rcall inc_case
    rjmp test20_start

; ============================================================
; TEST 20: LDI maximum value (0xFF) to all registers
; ============================================================
test20_start:
    ldi r16, 0xFF
    ldi r17, 0xFF
    ldi r18, 0xFF
    ldi r19, 0xFF
    ldi r20, 0xFF

    cpi r16, 0xFF
    breq test20_chk1
    jmp fail
test20_chk1:
    cpi r17, 0xFF
    breq test20_chk2
    jmp fail
test20_chk2:
    cpi r18, 0xFF
    breq test20_chk3
    jmp fail
test20_chk3:
    cpi r19, 0xFF
    breq test20_chk4
    jmp fail
test20_chk4:
    cpi r20, 0xFF
    breq test20_ok
    jmp fail
test20_ok:
    rcall inc_case
    rjmp success

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