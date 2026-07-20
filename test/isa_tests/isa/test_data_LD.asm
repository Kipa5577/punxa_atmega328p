; ============================================================
; LD (Load Indirect from Data Space) test suite
; ============================================================
; Tests that LD correctly:
; 1. Loads data from SRAM address pointed to by X/Y/Z
; 2. Can load with/without displacement (LDD)
; 3. Can post-increment or pre-decrement pointer
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D
.equ DATA_START = 0x0200

reset:
    ; Initialize stack pointer
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    rjmp test1_start

; ============================================================
; TEST 1: LD Rd, X (load from X pointer)
; ============================================================
test1_start:
    ldi r17, 0x42
    sts DATA_START, r17
    
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    
    ld r16, X
    cpi r16, 0x42
    breq t1_ok
    rjmp fail
t1_ok:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: LD Rd, X+ (load and post-increment)
; ============================================================
test2_start:
    ldi r17, 0xAA
    sts DATA_START, r17
    ldi r17, 0xBB
    sts DATA_START+1, r17
    
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    
    ld r16, X+
    cpi r16, 0xAA
    breq t2_ok1
    rjmp fail
t2_ok1:
    cpi r26, low(DATA_START+1)
    breq t2_ok2
    rjmp fail
t2_ok2:
    cpi r27, high(DATA_START+1)
    breq t2_ok3
    rjmp fail
t2_ok3:
    ld r16, X+
    cpi r16, 0xBB
    breq t2_ok4
    rjmp fail
t2_ok4:
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: LD Rd, -X (pre-decrement and load)
; ============================================================
test3_start:
    ldi r17, 0xCC
    sts DATA_START+2, r17
    
    ldi r26, low(DATA_START+3)
    ldi r27, high(DATA_START+3)
    
    ld r16, -X
    cpi r16, 0xCC
    breq t3_ok1
    rjmp fail
t3_ok1:
    cpi r26, low(DATA_START+2)
    breq t3_ok2
    rjmp fail
t3_ok2:
    cpi r27, high(DATA_START+2)
    breq t3_ok3
    rjmp fail
t3_ok3:
    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4: LD Rd, Y (load from Y pointer)
; ============================================================
test4_start:
    ldi r17, 0x5A
    sts DATA_START, r17
    
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    
    ld r16, Y
    cpi r16, 0x5A
    breq t4_ok
    rjmp fail
t4_ok:
    rcall inc_case
    rjmp test5_start

; ============================================================
; TEST 5: LD Rd, Y+ (load and post-increment)
; ============================================================
test5_start:
    ldi r17, 0x11
    sts DATA_START, r17
    ldi r17, 0x22
    sts DATA_START+1, r17
    
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    
    ld r16, Y+
    cpi r16, 0x11
    breq t5_ok1
    rjmp fail
t5_ok1:
    cpi r28, low(DATA_START+1)
    breq t5_ok2
    rjmp fail
t5_ok2:
    ld r16, Y+
    cpi r16, 0x22
    breq t5_ok3
    rjmp fail
t5_ok3:
    rcall inc_case
    rjmp test6_start

; ============================================================
; TEST 6: LD Rd, -Y (pre-decrement and load)
; ============================================================
test6_start:
    ldi r17, 0xDD
    sts DATA_START+2, r17
    
    ldi r28, low(DATA_START+3)
    ldi r29, high(DATA_START+3)
    
    ld r16, -Y
    cpi r16, 0xDD
    breq t6_ok1
    rjmp fail
t6_ok1:
    cpi r28, low(DATA_START+2)
    breq t6_ok2
    rjmp fail
t6_ok2:
    rcall inc_case
    rjmp test7_start

; ============================================================
; TEST 7: LD Rd, Z (load from Z pointer)
; ============================================================
test7_start:
    ldi r17, 0x3C
    sts DATA_START, r17
    
    ldi r30, low(DATA_START)
    ldi r31, high(DATA_START)
    
    ld r16, Z
    cpi r16, 0x3C
    breq t7_ok
    rjmp fail
t7_ok:
    rcall inc_case
    rjmp test8_start

; ============================================================
; TEST 8: LD Rd, Z+ (load and post-increment)
; ============================================================
test8_start:
    ldi r17, 0x77
    sts DATA_START, r17
    ldi r17, 0x88
    sts DATA_START+1, r17
    
    ldi r30, low(DATA_START)
    ldi r31, high(DATA_START)
    
    ld r16, Z+
    cpi r16, 0x77
    breq t8_ok1
    rjmp fail
t8_ok1:
    cpi r30, low(DATA_START+1)
    breq t8_ok2
    rjmp fail
t8_ok2:
    ld r16, Z+
    cpi r16, 0x88
    breq t8_ok3
    rjmp fail
t8_ok3:
    rcall inc_case
    rjmp test9_start

; ============================================================
; TEST 9: LD Rd, -Z (pre-decrement and load)
; ============================================================
test9_start:
    ldi r17, 0xEE
    sts DATA_START+2, r17
    
    ldi r30, low(DATA_START+3)
    ldi r31, high(DATA_START+3)
    
    ld r16, -Z
    cpi r16, 0xEE
    breq t9_ok1
    rjmp fail
t9_ok1:
    cpi r30, low(DATA_START+2)
    breq t9_ok2
    rjmp fail
t9_ok2:
    rcall inc_case
    rjmp test10_start

; ============================================================
; TEST 10: LDD Rd, Y+q (load with displacement)
; ============================================================
test10_start:
    ldi r17, 0x01
    sts DATA_START, r17
    ldi r17, 0x02
    sts DATA_START+1, r17
    ldi r17, 0x03
    sts DATA_START+2, r17
    ldi r17, 0x04
    sts DATA_START+3, r17
    ldi r17, 0x05
    sts DATA_START+4, r17
    
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    
    ldd r16, Y+0
    cpi r16, 0x01
    breq t10_ok1
    rjmp fail
t10_ok1:
    ldd r16, Y+1
    cpi r16, 0x02
    breq t10_ok2
    rjmp fail
t10_ok2:
    ldd r16, Y+2
    cpi r16, 0x03
    breq t10_ok3
    rjmp fail
t10_ok3:
    ldd r16, Y+3
    cpi r16, 0x04
    breq t10_ok4
    rjmp fail
t10_ok4:
    ldd r16, Y+4
    cpi r16, 0x05
    breq t10_ok5
    rjmp fail
t10_ok5:
    rcall inc_case
    rjmp test11_start

; ============================================================
; TEST 11: LDD Rd, Z+q (load with displacement)
; ============================================================
test11_start:
    ldi r17, 0x10
    sts DATA_START, r17
    ldi r17, 0x20
    sts DATA_START+1, r17
    
    ldi r30, low(DATA_START)
    ldi r31, high(DATA_START)
    
    ldd r16, Z+0
    cpi r16, 0x10
    breq t11_ok1
    rjmp fail
t11_ok1:
    ldd r16, Z+1
    cpi r16, 0x20
    breq t11_ok2
    rjmp fail
t11_ok2:
    rcall inc_case
    rjmp test12_start

; ============================================================
; TEST 12: LD to different registers (R0-R31)
; ============================================================
test12_start:
    ldi r17, 0xAB
    sts DATA_START, r17
    
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    
    ; Test loading into R0
    ld r0, X
    mov r16, r0            ; Move R0 to R16 (CPI cannot use R0)
    cpi r16, 0xAB
    breq t12_ok1
    rjmp fail
    
t12_ok1:
    ; Test loading into R16
    ld r16, X
    cpi r16, 0xAB
    breq t12_ok2
    rjmp fail
    
t12_ok2:
    ; Test loading into R31
    ld r31, X
    cpi r31, 0xAB
    breq t12_ok3
    rjmp fail
    
t12_ok3:
    rcall inc_case
    rjmp test13_start

; ============================================================
; TEST 13: LD does not modify flags
; ============================================================
test13_start:
    sec
    sez
    sen
    sev
    seh
    set
    
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    ld r16, X
    
    brcs t13_ok1       ; If C is still 1 (good), go to next check
    rjmp fail           ; If C was cleared (bad), fail
t13_ok1:
    breq t13_ok2       ; If Z is still 1 (good), go to next check
    rjmp fail
t13_ok2:
    brmi t13_ok3       ; If N is still 1 (good), go to next check
    rjmp fail
t13_ok3:
    brvs t13_ok4       ; If V is still 1 (good), go to next check
    rjmp fail
t13_ok4:
    brhs t13_ok5       ; If H is still 1 (good), go to next check
    rjmp fail
t13_ok5:
    brts t13_ok        ; If T is still 1 (good), go to final ok
    rjmp fail
t13_ok:
    rcall inc_case

; ============================================================
; TEST 14: LD with pointer crossing page boundary
; ============================================================
test14_start:
    ldi r17, 0xFF
    sts 0x02FF, r17
    
    ldi r26, 0xFF
    ldi r27, 0x02
    
    ld r16, X
    cpi r16, 0xFF
    breq t14_ok1
    rjmp fail
t14_ok1:
    ld r16, X+
    cpi r16, 0xFF
    breq t14_ok2
    rjmp fail
t14_ok2:
    cpi r26, 0x00
    breq t14_ok3
    rjmp fail
t14_ok3:
    cpi r27, 0x03
    breq t14_ok4
    rjmp fail
t14_ok4:
    rcall inc_case
    rjmp test15_start

; ============================================================
; TEST 15: LDD with maximum displacement (63)
; ============================================================
test15_start:
    ldi r17, 0x63
    sts DATA_START+63, r17
    
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    
    ldd r16, Y+63
    cpi r16, 0x63
    breq t15_ok
    rjmp fail
t15_ok:
    rcall inc_case
    rjmp test16_start

; ============================================================
; TEST 16: LD inside loop (string copy simulation)
; ============================================================
test16_start:
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    ldi r28, low(DATA_START+32)
    ldi r29, high(DATA_START+32)
    
    ldi r16, 1
    sts DATA_START, r16
    ldi r16, 2
    sts DATA_START+1, r16
    ldi r16, 3
    sts DATA_START+2, r16
    ldi r16, 4
    sts DATA_START+3, r16
    
    ldi r18, 4
copy_loop:
    ld r16, X+
    st Y+, r16
    dec r18
    brne copy_loop
    
    ldi r28, low(DATA_START+32)
    ldi r29, high(DATA_START+32)
    ld r16, Y+
    cpi r16, 1
    breq t16_ok1
    rjmp fail
t16_ok1:
    ld r16, Y+
    cpi r16, 2
    breq t16_ok2
    rjmp fail
t16_ok2:
    ld r16, Y+
    cpi r16, 3
    breq t16_ok3
    rjmp fail
t16_ok3:
    ld r16, Y+
    cpi r16, 4
    breq t16_ok4
    rjmp fail
t16_ok4:
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