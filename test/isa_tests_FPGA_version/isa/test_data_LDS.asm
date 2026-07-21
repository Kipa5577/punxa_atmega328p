; ============================================================
; LDS (Load Direct from Data Space) test suite
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D
.equ DATA_START = 0x0200
.equ EXT_ADDR = 0x08FF

reset:
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    rjmp test1_start

; ============================================================
; TEST 1: LDS to R16 from low SRAM address
; ============================================================
test1_start:
    ldi r16, 0x42
    sts DATA_START, r16
    
    lds r17, DATA_START
    cpi r17, 0x42
    breq t1_ok
    rjmp fail
t1_ok:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: LDS to R0 (lowest register)
; ============================================================
test2_start:
    ldi r16, 0xAA
    sts DATA_START+1, r16
    
    lds r0, DATA_START+1
    cpi r0, 0xAA
    breq t2_ok
    rjmp fail
t2_ok:
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: LDS to R31 (highest register)
; ============================================================
test3_start:
    ldi r16, 0xBB
    sts DATA_START+2, r16
    
    lds r31, DATA_START+2
    cpi r31, 0xBB
    breq t3_ok
    rjmp fail
t3_ok:
    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4: LDS from maximum SRAM address (0x08FF)
; ============================================================
test4_start:
    ldi r16, 0xCC
    sts EXT_ADDR, r16
    
    lds r17, EXT_ADDR
    cpi r17, 0xCC
    breq t4_ok
    rjmp fail
t4_ok:
    rcall inc_case
    rjmp test5_start

; ============================================================
; TEST 5: LDS from minimum safe SRAM address
; ============================================================
test5_start:
    ldi r16, 0xDD
    sts 0x0102, r16       ; FIXED: Changed from 0x0100 to avoid overwriting test_case
    
    lds r17, 0x0102
    cpi r17, 0xDD
    breq t5_ok
    rjmp fail
t5_ok:
    rcall inc_case
    rjmp test6_start

; ============================================================
; TEST 6: LDS with value 0x00
; ============================================================
test6_start:
    ldi r16, 0x00
    sts DATA_START+3, r16
    
    lds r17, DATA_START+3
    cpi r17, 0x00
    breq t6_ok
    rjmp fail
t6_ok:
    rcall inc_case
    rjmp test7_start

; ============================================================
; TEST 7: LDS with value 0xFF
; ============================================================
test7_start:
    ldi r16, 0xFF
    sts DATA_START+4, r16
    
    lds r17, DATA_START+4
    cpi r17, 0xFF
    breq t7_ok
    rjmp fail
t7_ok:
    rcall inc_case
    rjmp test8_start

; ============================================================
; TEST 8: LDS does not modify flags
; ============================================================
test8_start:
    sec
    sez
    sen
    sev
    seh
    set
    
    lds r16, DATA_START+4
    
    brcs t8_pass1         ; FIXED: Changed to Branch if Set
    rjmp fail
t8_pass1:
    breq t8_pass2         ; FIXED: Changed to Branch if Set
    rjmp fail
t8_pass2:
    brmi t8_pass3         
    rjmp fail
t8_pass3:
    brvs t8_pass4         
    rjmp fail
t8_pass4:
    brhs t8_pass5         ; FIXED: Changed to Branch if Set
    rjmp fail
t8_pass5:
    brts t8_ok            ; FIXED: Changed to Branch if Set
    rjmp fail
t8_ok:
    rcall inc_case
    rjmp test9_start

; ============================================================
; TEST 9: LDS from overlapping addresses
; ============================================================
test9_start:
    ldi r16, 0x11
    sts DATA_START+5, r16
    ldi r16, 0x22
    sts DATA_START+6, r16
    
    lds r17, DATA_START+5
    lds r18, DATA_START+6
    
    cpi r17, 0x11
    breq t9_ok1
    rjmp fail
t9_ok1:
    cpi r18, 0x22
    breq t9_ok2
    rjmp fail
t9_ok2:
    rcall inc_case
    rjmp test10_start

; ============================================================
; TEST 10: LDS then modify loaded register
; ============================================================
test10_start:
    ldi r16, 0x10
    sts DATA_START+7, r16
    
    lds r17, DATA_START+7
    inc r17
    cpi r17, 0x11
    breq t10_ok1
    rjmp fail
t10_ok1:
    lds r18, DATA_START+7
    cpi r18, 0x10
    breq t10_ok2
    rjmp fail
t10_ok2:
    rcall inc_case
    rjmp test11_start

; ============================================================
; TEST 11: LDS into register used as pointer
; ============================================================
test11_start:
    ldi r16, 0x99
    sts DATA_START+8, r16
    ldi r16, 0x88
    sts DATA_START+9, r16
    
    lds r26, DATA_START+8
    lds r27, DATA_START+9
    
    cpi r26, 0x99
    breq t11_ok1
    rjmp fail
t11_ok1:
    cpi r27, 0x88
    breq t11_ok2
    rjmp fail
t11_ok2:
    rcall inc_case
    rjmp test12_start

; ============================================================
; TEST 12: Multiple LDS from same address
; ============================================================
test12_start:
    ldi r16, 0x77
    sts DATA_START+10, r16
    
    lds r17, DATA_START+10
    lds r18, DATA_START+10
    lds r19, DATA_START+10
    
    cpi r17, 0x77
    breq t12_ok1
    rjmp fail
t12_ok1:
    cpi r18, 0x77
    breq t12_ok2
    rjmp fail
t12_ok2:
    cpi r19, 0x77
    breq t12_ok3
    rjmp fail
t12_ok3:
    rcall inc_case
    rjmp test13_start

; ============================================================
; TEST 13: LDS from I/O space address (0x20-0x5F mapping)
; ============================================================
test13_start:
    ldi r16, 0x5A
    sts 0x003E, r16
    
    lds r17, 0x003E
    cpi r17, 0x5A
    breq t13_ok
    rjmp fail
t13_ok:
    rcall inc_case
    rjmp test14_start

; ============================================================
; TEST 14: LDS then store back with STS
; ============================================================
test14_start:
    ldi r16, 0x12
    sts DATA_START+11, r16
    
    lds r17, DATA_START+11
    inc r17
    sts DATA_START+12, r17
    
    lds r18, DATA_START+12
    cpi r18, 0x13
    breq t14_ok
    rjmp fail
t14_ok:
    rcall inc_case
    rjmp test15_start

; ============================================================
; TEST 15: LDS within a loop (array read attempt)
; ============================================================
test15_start:
    ldi r16, 1
    sts DATA_START+16, r16
    ldi r16, 2
    sts DATA_START+17, r16
    ldi r16, 3
    sts DATA_START+18, r16
    ldi r16, 4
    sts DATA_START+19, r16
    
    ldi r20, 0
    ldi r21, 4
    ldi r22, 16
    
test15_loop:
    lds r23, DATA_START+16 ; Note: LDS is an absolute address. It reads '1' four times.
    add r20, r23
    inc r22
    dec r21
    brne test15_loop
    
    cpi r20, 4            ; FIXED: 4 iterations * 1 = 4. 
    breq t15_ok
    rjmp fail
t15_ok:
    rcall inc_case
    rjmp test16_start

; ============================================================
; TEST 16: LDS across page boundary (0x02FF to 0x0300)
; ============================================================
test16_start:
    ldi r16, 0xAB
    sts 0x02FF, r16
    ldi r16, 0xCD
    sts 0x0300, r16
    
    lds r17, 0x02FF
    lds r18, 0x0300
    
    cpi r17, 0xAB
    breq t16_ok1
    rjmp fail
t16_ok1:
    cpi r18, 0xCD
    breq t16_ok2
    rjmp fail
t16_ok2:
    rcall inc_case
    rjmp test17_start

; ============================================================
; TEST 17: LDS to all register types in sequence
; ============================================================
test17_start:
    ldi r16, 0xAA
    sts DATA_START+20, r16
    
    lds r0, DATA_START+20
    lds r16, DATA_START+20
    lds r31, DATA_START+20
    
    cpi r0, 0xAA
    breq t17_ok1
    rjmp fail
t17_ok1:
    cpi r16, 0xAA
    breq t17_ok2
    rjmp fail
t17_ok2:
    cpi r31, 0xAA
    breq t17_ok3
    rjmp fail
t17_ok3:
    rcall inc_case
    rjmp test18_start

; ============================================================
; TEST 18: LDS from addresses with pattern
; ============================================================
test18_start:
    ldi r16, 0x55
    sts DATA_START+32, r16
    ldi r16, 0xAA
    sts DATA_START+33, r16
    ldi r16, 0x55
    sts DATA_START+34, r16
    
    lds r17, DATA_START+32
    lds r18, DATA_START+33
    lds r19, DATA_START+34
    
    cpi r17, 0x55
    breq t18_ok1
    rjmp fail
t18_ok1:
    cpi r18, 0xAA
    breq t18_ok2
    rjmp fail
t18_ok2:
    cpi r19, 0x55
    breq t18_ok3
    rjmp fail
t18_ok3:
    rcall inc_case
    rjmp test19_start

; ============================================================
; TEST 19: LDS used in arithmetic chain
; ============================================================
test19_start:
    ldi r16, 10
    sts DATA_START+40, r16
    ldi r16, 20
    sts DATA_START+41, r16
    ldi r16, 30
    sts DATA_START+42, r16
    
    lds r17, DATA_START+40
    lds r18, DATA_START+41
    lds r19, DATA_START+42
    
    add r17, r18
    add r17, r19
    
    cpi r17, 60
    breq t19_ok
    rjmp fail
t19_ok:
    rcall inc_case
    rjmp test20_start

; ============================================================
; TEST 20: LDS with immediate value then conditional branch
; ============================================================
test20_start:
    ldi r16, 0x00
    sts DATA_START+50, r16
    
    lds r17, DATA_START+50
    tst r17
    breq lds_zero_ok20
    rjmp fail
lds_zero_ok20:
    
    ldi r16, 0x01
    sts DATA_START+51, r16
    lds r17, DATA_START+51
    tst r17
    brne lds_nonzero_ok20
    rjmp fail
lds_nonzero_ok20:
    
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