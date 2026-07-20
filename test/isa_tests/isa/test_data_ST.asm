; ============================================================
; ST (Store Indirect to Data Space) test suite
; ============================================================
; Tests that ST correctly:
; 1. Stores data to SRAM address pointed to by X/Y/Z
; 2. Can store with/without displacement (STD)
; 3. Can post-increment or pre-decrement pointer
; 4. Does not modify the source register or flags
; ============================================================
; ST is a 1-word (16-bit) instruction
; Formats:
;   ST X, Rr         (1001 001r rrrr 1100)
;   ST X+, Rr        (1001 001r rrrr 1101)
;   ST -X, Rr        (1001 001r rrrr 1110)
;   ST Y, Rr         (1000 001r rrrr 1000)
;   ST Y+, Rr        (1001 001r rrrr 1001)
;   ST -Y, Rr        (1001 001r rrrr 1010)
;   STD Y+q, Rr      (10q0 qq1r rrrr 1qqq)
;   ST Z, Rr         (1000 001r rrrr 0000)
;   ST Z+, Rr        (1001 001r rrrr 0001)
;   ST -Z, Rr        (1001 001r rrrr 0010)
;   STD Z+q, Rr      (10q0 qq1r rrrr 0qqq)
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
; TEST 1: ST X, Rr (store through X pointer)
; ============================================================
test1_start:
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    
    ldi r16, 0x42
    st X, r16
    
    ld r17, X
    cpi r17, 0x42
    breq t1_ok
    rjmp fail
t1_ok:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: ST X+, Rr (store and post-increment)
; ============================================================
test2_start:
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    
    ldi r16, 0xAA
    st X+, r16
    ldi r16, 0xBB
    st X+, r16
    
    cpi r26, low(DATA_START+2)
    breq t2_ok1
    rjmp fail
t2_ok1:
    cpi r27, high(DATA_START+2)
    breq t2_ok2
    rjmp fail
t2_ok2:
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    ld r17, X+
    cpi r17, 0xAA
    breq t2_ok3
    rjmp fail
t2_ok3:
    ld r17, X+
    cpi r17, 0xBB
    breq t2_ok4
    rjmp fail
t2_ok4:
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: ST -X, Rr (pre-decrement and store)
; ============================================================
test3_start:
    ldi r26, low(DATA_START+2)
    ldi r27, high(DATA_START+2)
    
    ldi r16, 0xCC
    st -X, r16
    
    cpi r26, low(DATA_START+1)
    breq t3_ok1
    rjmp fail
t3_ok1:
    cpi r27, high(DATA_START+1)
    breq t3_ok2
    rjmp fail
t3_ok2:
    ldi r26, low(DATA_START+1)
    ldi r27, high(DATA_START+1)
    ld r17, X
    cpi r17, 0xCC
    breq t3_ok3
    rjmp fail
t3_ok3:
    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4: ST Y, Rr (store through Y pointer)
; ============================================================
test4_start:
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    
    ldi r16, 0x5A
    st Y, r16
    
    ld r17, Y
    cpi r17, 0x5A
    breq t4_ok
    rjmp fail
t4_ok:
    rcall inc_case
    rjmp test5_start

; ============================================================
; TEST 5: ST Y+, Rr (store and post-increment with Y)
; ============================================================
test5_start:
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    
    ldi r16, 0x11
    st Y+, r16
    ldi r16, 0x22
    st Y+, r16
    
    cpi r28, low(DATA_START+2)
    breq t5_ok1
    rjmp fail
t5_ok1:
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    ld r17, Y+
    cpi r17, 0x11
    breq t5_ok2
    rjmp fail
t5_ok2:
    ld r17, Y+
    cpi r17, 0x22
    breq t5_ok3
    rjmp fail
t5_ok3:
    rcall inc_case
    rjmp test6_start

; ============================================================
; TEST 6: ST -Y, Rr (pre-decrement and store with Y)
; ============================================================
test6_start:
    ldi r28, low(DATA_START+2)
    ldi r29, high(DATA_START+2)
    
    ldi r16, 0xDD
    st -Y, r16
    
    cpi r28, low(DATA_START+1)
    breq t6_ok1
    rjmp fail
t6_ok1:
    ldi r28, low(DATA_START+1)
    ldi r29, high(DATA_START+1)
    ld r17, Y
    cpi r17, 0xDD
    breq t6_ok2
    rjmp fail
t6_ok2:
    rcall inc_case
    rjmp test7_start

; ============================================================
; TEST 7: ST Z, Rr (store through Z pointer)
; ============================================================
test7_start:
    ldi r30, low(DATA_START)
    ldi r31, high(DATA_START)
    
    ldi r16, 0x3C
    st Z, r16
    
    ld r17, Z
    cpi r17, 0x3C
    breq t7_ok
    rjmp fail
t7_ok:
    rcall inc_case
    rjmp test8_start

; ============================================================
; TEST 8: ST Z+, Rr (store and post-increment with Z)
; ============================================================
test8_start:
    ldi r30, low(DATA_START)
    ldi r31, high(DATA_START)
    
    ldi r16, 0x77
    st Z+, r16
    ldi r16, 0x88
    st Z+, r16
    
    cpi r30, low(DATA_START+2)
    breq t8_ok1
    rjmp fail
t8_ok1:
    ldi r30, low(DATA_START)
    ldi r31, high(DATA_START)
    ld r17, Z+
    cpi r17, 0x77
    breq t8_ok2
    rjmp fail
t8_ok2:
    ld r17, Z+
    cpi r17, 0x88
    breq t8_ok3
    rjmp fail
t8_ok3:
    rcall inc_case
    rjmp test9_start

; ============================================================
; TEST 9: ST -Z, Rr (pre-decrement and store with Z)
; ============================================================
test9_start:
    ldi r30, low(DATA_START+2)
    ldi r31, high(DATA_START+2)
    
    ldi r16, 0xEE
    st -Z, r16
    
    cpi r30, low(DATA_START+1)
    breq t9_ok1
    rjmp fail
t9_ok1:
    ldi r30, low(DATA_START+1)
    ldi r31, high(DATA_START+1)
    ld r17, Z
    cpi r17, 0xEE
    breq t9_ok2
    rjmp fail
t9_ok2:
    rcall inc_case
    rjmp test10_start

; ============================================================
; TEST 10: STD Y+q, Rr (store with displacement Y)
; ============================================================
test10_start:
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    
    ldi r16, 0x01
    std Y+0, r16
    ldi r16, 0x02
    std Y+1, r16
    ldi r16, 0x03
    std Y+2, r16
    ldi r16, 0x04
    std Y+3, r16
    ldi r16, 0x05
    std Y+4, r16
    
    ldd r17, Y+0
    cpi r17, 0x01
    breq t10_ok1
    rjmp fail
t10_ok1:
    ldd r17, Y+1
    cpi r17, 0x02
    breq t10_ok2
    rjmp fail
t10_ok2:
    ldd r17, Y+2
    cpi r17, 0x03
    breq t10_ok3
    rjmp fail
t10_ok3:
    ldd r17, Y+3
    cpi r17, 0x04
    breq t10_ok4
    rjmp fail
t10_ok4:
    ldd r17, Y+4
    cpi r17, 0x05
    breq t10_ok5
    rjmp fail
t10_ok5:
    rcall inc_case
    rjmp test11_start

; ============================================================
; TEST 11: STD Z+q, Rr (store with displacement Z)
; ============================================================
test11_start:
    ldi r30, low(DATA_START)
    ldi r31, high(DATA_START)
    
    ldi r16, 0x10
    std Z+0, r16
    ldi r16, 0x20
    std Z+1, r16
    
    ldd r17, Z+0
    cpi r17, 0x10
    breq t11_ok1
    rjmp fail
t11_ok1:
    ldd r17, Z+1
    cpi r17, 0x20
    breq t11_ok2
    rjmp fail
t11_ok2:
    rcall inc_case
    rjmp test12_start

; ============================================================
; TEST 12: ST from different registers (R0-R31)
; ============================================================
test12_start:
    ldi r26, low(DATA_START+16)
    ldi r27, high(DATA_START+16)
    
    ldi r16, 0xAB
    mov r0, r16
    st X+, r0
    ldi r16, 0xCD
    st X+, r16
    ldi r31, 0xEF
    st X+, r31
    
    ldi r26, low(DATA_START+16)
    ldi r27, high(DATA_START+16)
    ld r17, X+
    cpi r17, 0xAB
    breq t12_ok1
    rjmp fail
t12_ok1:
    ld r17, X+
    cpi r17, 0xCD
    breq t12_ok2
    rjmp fail
t12_ok2:
    ld r17, X+
    cpi r17, 0xEF
    breq t12_ok3
    rjmp fail
t12_ok3:
    rcall inc_case
    rjmp test13_start

; ============================================================
; TEST 13: ST does not modify source register
; ============================================================
test13_start:
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    
    ldi r16, 0x55
    st X, r16
    
    cpi r16, 0x55
    breq t13_ok
    rjmp fail
t13_ok:
    rcall inc_case
    rjmp test14_start

; ============================================================
; TEST 14: ST does not modify flags
; ============================================================
test14_start:
    ldi r26, low(DATA_START)
    ldi r27, high(DATA_START)
    
    sec
    sez
    sen
    sev
    seh
    set
    
    ldi r16, 0xAA
    st X, r16
    
    brcs t14_pass1
    rjmp fail
t14_pass1:
    breq t14_pass2
    rjmp fail
t14_pass2:
    brmi t14_pass3
    rjmp fail
t14_pass3:
    brvs t14_pass4
    rjmp fail
t14_pass4:
    brhs t14_pass5
    rjmp fail
t14_pass5:
    brts t14_ok
    rjmp fail
t14_ok:
    rcall inc_case
    rjmp test15_start

; ============================================================
; TEST 15: STD with maximum displacement (63)
; ============================================================
test15_start:
    ldi r28, low(DATA_START)
    ldi r29, high(DATA_START)
    
    ldi r16, 0x63
    std Y+63, r16
    
    ldd r17, Y+63
    cpi r17, 0x63
    breq t15_ok
    rjmp fail
t15_ok:
    rcall inc_case
    rjmp test16_start

; ============================================================
; TEST 16: ST inside loop (array fill)
; ============================================================
test16_start:
    ldi r26, low(DATA_START+32)
    ldi r27, high(DATA_START+32)
    
    ldi r16, 0
    ldi r17, 10
fill_loop:
    st X+, r16
    inc r16
    dec r17
    brne fill_loop
    
    ldi r26, low(DATA_START+32)
    ldi r27, high(DATA_START+32)
    ldi r17, 0
    ldi r18, 10
verify_loop:
    ld r19, X+
    cp r17, r19
    breq t16_vok
    rjmp fail
t16_vok:
    inc r17
    dec r18
    brne verify_loop
    
    rcall inc_case
    rjmp test17_start

; ============================================================
; TEST 17: ST with pointer crossing page boundary
; ============================================================
test17_start:
    ldi r26, 0xFF
    ldi r27, 0x02
    ldi r16, 0xAA
    st X+, r16
    
    cpi r26, 0x00
    breq t17_ok1
    rjmp fail
t17_ok1:
    cpi r27, 0x03
    breq t17_ok2
    rjmp fail
t17_ok2:
    ldi r26, 0xFF
    ldi r27, 0x02
    ld r17, X
    cpi r17, 0xAA
    breq t17_ok3
    rjmp fail
t17_ok3:
    rcall inc_case
    rjmp test18_start

; ============================================================
; TEST 18: ST then LD from same address
; ============================================================
test18_start:
    ldi r26, low(DATA_START+50)
    ldi r27, high(DATA_START+50)
    
    ldi r16, 0xDE
    st X, r16
    
    ld r17, X
    cpi r17, 0xDE
    breq t18_ok
    rjmp fail
t18_ok:
    rcall inc_case
    rjmp test19_start

; ============================================================
; TEST 19: STD with displacement
; ============================================================
test19_start:
    ldi r28, low(DATA_START+60)
    ldi r29, high(DATA_START+60)
    
    ldi r16, 0x99
    std Y+5, r16
    
    ldd r17, Y+5
    cpi r17, 0x99
    breq t19_ok
    rjmp fail
t19_ok:
    rcall inc_case
    rjmp test20_start

; ============================================================
; TEST 20: Multiple ST operations with different pointers
; ============================================================
test20_start:
    ldi r26, low(DATA_START+80)
    ldi r27, high(DATA_START+80)
    ldi r16, 0xAA
    st X, r16
    
    ldi r28, low(DATA_START+81)
    ldi r29, high(DATA_START+81)
    ldi r16, 0xBB
    st Y, r16
    
    ldi r30, low(DATA_START+82)
    ldi r31, high(DATA_START+82)
    ldi r16, 0xCC
    st Z, r16
    
    lds r17, DATA_START+80
    cpi r17, 0xAA
    breq t20_ok1
    rjmp fail
t20_ok1:
    lds r17, DATA_START+81
    cpi r17, 0xBB
    breq t20_ok2
    rjmp fail
t20_ok2:
    lds r17, DATA_START+82
    cpi r17, 0xCC
    breq t20_ok3
    rjmp fail
t20_ok3:
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