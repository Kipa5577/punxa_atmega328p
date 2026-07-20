; ============================================================
; OUT (Store to I/O Register) test suite
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D
.equ SREG = 0x3F
.equ PORTC = 0x08
.equ DDRC = 0x07
.equ PINC = 0x06

.equ GPIOR0 = 0x1E
.equ GPIOR1 = 0x1A

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
; TEST 1: OUT to GPIOR0 from R16
; ============================================================
test1_start:
    ldi r16, 0x42
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0x42
    breq t1_ok
    rjmp fail
t1_ok:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: OUT to GPIOR1 from R0 (lowest register)
; ============================================================
test2_start:
    ldi r16, 0xAA
    mov r0, r16
    out GPIOR1, r0
    
    in r17, GPIOR1
    cpi r17, 0xAA
    breq t2_ok
    rjmp fail
t2_ok:
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: OUT to GPIOR0 from R31 (highest register)
; ============================================================
test3_start:
    ldi r31, 0xBB
    out GPIOR0, r31
    
    in r16, GPIOR0
    cpi r16, 0xBB
    breq t3_ok
    rjmp fail
t3_ok:
    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4: OUT with value 0x00
; ============================================================
test4_start:
    ldi r16, 0x00
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0x00
    breq t4_ok
    rjmp fail
t4_ok:
    rcall inc_case
    rjmp test5_start

; ============================================================
; TEST 5: OUT with value 0xFF
; ============================================================
test5_start:
    ldi r16, 0xFF
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0xFF
    breq t5_ok
    rjmp fail
t5_ok:
    rcall inc_case
    rjmp test6_start

; ============================================================
; TEST 6: OUT does not modify flags
; ============================================================
test6_start:
    sec
    sez
    sen
    sev
    seh
    set
    
    ldi r16, 0x55
    out GPIOR0, r16
    
    brcs t6_pass1
    rjmp fail
t6_pass1:
    breq t6_pass2
    rjmp fail
t6_pass2:
    brmi t6_pass3
    rjmp fail
t6_pass3:
    brvs t6_pass4
    rjmp fail
t6_pass4:
    brhs t6_pass5
    rjmp fail
t6_pass5:
    brts t6_ok
    rjmp fail
t6_ok:
    rcall inc_case
    rjmp test7_start

; ============================================================
; TEST 7: OUT to multiple I/O addresses
; ============================================================
test7_start:
    ldi r16, 0x11
    out GPIOR0, r16
    ldi r16, 0x22
    out GPIOR1, r16
    
    in r17, GPIOR0
    in r18, GPIOR1
    
    cpi r17, 0x11
    breq t7_ok1
    rjmp fail
t7_ok1:
    cpi r18, 0x22
    breq t7_ok2
    rjmp fail
t7_ok2:
    rcall inc_case
    rjmp test8_start

; ============================================================
; TEST 8: OUT to PORTC (output port)
; ============================================================
test8_start:
    ldi r16, 0xFF
    out DDRC, r16
    
    ldi r16, 0x5A
    out PORTC, r16
    
    in r17, PORTC
    cpi r17, 0x5A
    breq t8_ok
    rjmp fail
t8_ok:
    rcall inc_case
    rjmp test9_start

; ============================================================
; TEST 9: OUT to SREG (Status Register)
; ============================================================
test9_start:
    in r16, SREG
    push r16
    
    ldi r16, 0b11000000
    out SREG, r16
    
    in r17, SREG
    cpi r17, 0b11000000
    breq t9_ok1
    rjmp fail
t9_ok1:
    pop r16
    out SREG, r16
    rcall inc_case
    rjmp test10_start

; ============================================================
; TEST 10: OUT to SPH/SPL (Stack Pointer)
; ============================================================
test10_start:
    in r20, SPL
    in r21, SPH
    
    ldi r16, 0x34
    out SPL, r16
    ldi r16, 0x12
    out SPH, r16
    
    in r18, SPL
    in r19, SPH
    cpi r18, 0x34
    breq t10_ok1
    rjmp fail
t10_ok1:
    cpi r19, 0x12
    breq t10_ok2
    rjmp fail
t10_ok2:
    out SPH, r21
    out SPL, r20
    rcall inc_case
    rjmp test11_start

; ============================================================
; TEST 11: OUT with pattern alternating bits (0x55)
; ============================================================
test11_start:
    ldi r16, 0x55
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0x55
    breq t11_ok
    rjmp fail
t11_ok:
    rcall inc_case
    rjmp test12_start

; ============================================================
; TEST 12: OUT with pattern alternating bits (0xAA)
; ============================================================
test12_start:
    ldi r16, 0xAA
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0xAA
    breq t12_ok
    rjmp fail
t12_ok:
    rcall inc_case
    rjmp test13_start

; ============================================================
; TEST 13: OUT from register that is then modified
; ============================================================
test13_start:
    ldi r16, 0xDE
    out GPIOR0, r16
    ldi r16, 0xAD
    
    in r17, GPIOR0
    cpi r17, 0xDE
    breq t13_ok
    rjmp fail
t13_ok:
    rcall inc_case
    rjmp test14_start

; ============================================================
; TEST 14: OUT to same address multiple times
; ============================================================
test14_start:
    ldi r16, 0x01
    out GPIOR0, r16
    ldi r16, 0x02
    out GPIOR0, r16
    ldi r16, 0x03
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0x03
    breq t14_ok
    rjmp fail
t14_ok:
    rcall inc_case
    rjmp test15_start

; ============================================================
; TEST 15: OUT using all register types in sequence
; ============================================================
test15_start:
    ldi r16, 0xAA
    mov r0, r16
    out GPIOR0, r0
    in r16, GPIOR0
    cpi r16, 0xAA
    breq t15_ok1
    rjmp fail
t15_ok1:
    ldi r16, 0xBB
    out GPIOR0, r16
    in r17, GPIOR0
    cpi r17, 0xBB
    breq t15_ok2
    rjmp fail
t15_ok2:
    ldi r31, 0xCC
    out GPIOR0, r31
    in r18, GPIOR0
    cpi r18, 0xCC
    breq t15_ok3
    rjmp fail
t15_ok3:
    rcall inc_case
    rjmp test16_start

; ============================================================
; TEST 16: OUT after IN (verify no interference)
; ============================================================
test16_start:
    ldi r16, 0x12
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0x12
    breq t16_ok1
    rjmp fail
t16_ok1:
    ldi r18, 0x34
    out GPIOR0, r18
    
    in r19, GPIOR0
    cpi r19, 0x34
    breq t16_ok2
    rjmp fail
t16_ok2:
    rcall inc_case
    rjmp test17_start

; ============================================================
; TEST 17: OUT with value 0x01
; ============================================================
test17_start:
    ldi r16, 0x01
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0x01
    breq t17_ok
    rjmp fail
t17_ok:
    rcall inc_case
    rjmp test18_start

; ============================================================
; TEST 18: OUT with value 0x80 (MSB set)
; ============================================================
test18_start:
    ldi r16, 0x80
    out GPIOR0, r16
    
    in r17, GPIOR0
    cpi r17, 0x80
    breq t18_ok
    rjmp fail
t18_ok:
    rcall inc_case
    rjmp test19_start

; ============================================================
; TEST 19: OUT inside a loop
; ============================================================
test19_start:
    ldi r16, 0
    ldi r17, 5
test19_loop:
    out GPIOR0, r16
    inc r16
    dec r17
    brne test19_loop
    
    in r18, GPIOR0
    cpi r18, 4
    breq t19_ok
    rjmp fail
t19_ok:
    rcall inc_case
    rjmp test20_start

; ============================================================
; TEST 20: OUT then conditional branch
; ============================================================
test20_start:
    ldi r16, 0x00
    out GPIOR0, r16
    in r17, GPIOR0
    tst r17
    breq out_zero_ok20
    rjmp fail
out_zero_ok20:
    
    ldi r16, 0x01
    out GPIOR0, r16
    in r17, GPIOR0
    tst r17
    brne out_nonzero_ok20
    rjmp fail
out_nonzero_ok20:
    
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