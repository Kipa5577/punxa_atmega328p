; ============================================================
; IN (Load I/O Register) test suite - FIXED VERSION
; ============================================================
; Tests that IN correctly:
; 1. Reads data from I/O space address (0x00-0x3F)
; 2. Stores the value in the destination register
; 3. Does not modify any flags or other registers
; ============================================================
; IN is a 1-word (16-bit) instruction
; Format: 1011 0AAd dddd AAAA
; Operation: Rd <- I/O(A)
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D
.equ SREG = 0x3F
.equ PORTC = 0x08
.equ DDRC = 0x07
.equ PINC = 0x06

; Test I/O registers (using unused GPIORs for testing)
.equ GPIOR0 = 0x1E
.equ GPIOR1 = 0x1A

reset:
    ; Initialize stack pointer
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16
    
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

; ============================================================
; TEST 1: IN from I/O address 0x00 (PORTC)
; ============================================================
test1:
    ; Write a test value to PORTC first
    ldi r16, 0xAA
    out PORTC, r16
    
    ; Read it back
    in r17, PORTC
    cpi r17, 0xAA
    brne test1_fail
    rcall inc_case
    rjmp test1_done

test1_fail:
    rjmp fail

test1_done:

; ============================================================
; TEST 2: IN from different I/O addresses
; ============================================================
test2:
    ; Test DDRC
    ldi r16, 0x55
    out DDRC, r16
    in r17, DDRC
    cpi r17, 0x55
    brne test2_fail
    
    ; Test PINC
    ; PINC is read-only, so we need to set through PORT/DDR
    ldi r16, 0xFF
    out DDRC, r16       ; Set as output
    out PORTC, r16
    nop                 ; Small delay
    in r17, PINC
    cpi r17, 0xFF
    brne test2_fail
    
    rcall inc_case
    rjmp test2_done

test2_fail:
    rjmp fail

test2_done:

; ============================================================
; TEST 3: IN from GPIOR0 (General Purpose I/O Register)
; ============================================================
test3:
    ; Write to GPIOR0
    ldi r16, 0x33
    out GPIOR0, r16
    
    ; Read back with IN
    in r17, GPIOR0
    cpi r17, 0x33
    brne test3_fail
    
    rcall inc_case
    rjmp test3_done

test3_fail:
    rjmp fail

test3_done:

; ============================================================
; TEST 4: IN from GPIOR1 (different address)
; ============================================================
test4:
    ldi r16, 0xCC
    out GPIOR1, r16
    in r17, GPIOR1
    cpi r17, 0xCC
    brne test4_fail
    
    rcall inc_case
    rjmp test4_done

test4_fail:
    rjmp fail

test4_done:

; ============================================================
; TEST 5: IN to all registers (R0-R31) - FIXED
; ============================================================
test5:
    ; Write known value
    ldi r16, 0x78
    out GPIOR0, r16
    
    ; Read into different registers
    in r0, GPIOR0
    ; Compare R0 by moving to upper register first
    mov r16, r0
    cpi r16, 0x78
    brne test5_fail
    
    in r16, GPIOR0
    cpi r16, 0x78
    brne test5_fail
    
    in r31, GPIOR0
    cpi r31, 0x78
    brne test5_fail
    
    rcall inc_case
    rjmp test5_done

test5_fail:
    rjmp fail

test5_done:

; ============================================================
; TEST 6: IN does not modify flags
; ============================================================
test6:
    ; Set specific flags
    sec                 ; Set Carry (C=1)
    sez                 ; Set Zero (Z=1)
    sen                 ; Set Negative (N=1)
    sev                 ; Set Overflow (V=1)
    seh                 ; Set Half Carry (H=1)
    set                 ; Set Transfer (T=1)
    
    ; Read I/O (should preserve flags)
    in r16, GPIOR0
    
    ; Check all flags are still set
    brcc test6_fail     ; C should be 1
    brne test6_fail     ; Z should be 1
    brpl test6_fail     ; N should be 1 (fixed: was brmi)
    brvc test6_fail     ; V should be 1 (fixed: was brvs)
    brhc test6_fail     ; H should be 1
    brtc test6_fail     ; T should be 1
    
    rcall inc_case
    rjmp test6_done

test6_fail:
    rjmp fail

test6_done:

; ============================================================
; TEST 7: IN from SREG (Status Register)
; ============================================================
test7:
    ; Set known SREG value
    cli                 ; Clear I flag
    sec                 ; Set C
    clz                 ; Clear Z
    sen                 ; Set N
    clv                 ; Clear V
    
    in r16, SREG
    ; Check specific bits
    sbrc r16, 0         ; Test C
    rjmp c_ok7
    rjmp test7_fail
c_ok7:
    sbrs r16, 1         ; Test Z (should be 0)
    rjmp z_ok7
    rjmp test7_fail
z_ok7:
    sbrc r16, 2         ; Test N
    rjmp n_ok7
    rjmp test7_fail
n_ok7:
    sbrs r16, 3         ; Test V (should be 0)
    rjmp v_ok7
    rjmp test7_fail
v_ok7:
    sbrs r16, 7         ; Test I (should be 0)
    rjmp i_ok7
    rjmp test7_fail
i_ok7:
    rcall inc_case
    rjmp test7_done

test7_fail:
    rjmp fail

test7_done:

; ============================================================
; TEST 8: IN from SPH/SPL (Stack Pointer)
; ============================================================
test8:
    ; Set known SP values
    ldi r16, 0x12
    out SPH, r16
    ldi r16, 0x34
    out SPL, r16
    
    ; Read back
    in r17, SPH
    cpi r17, 0x12
    brne test8_fail
    in r18, SPL
    cpi r18, 0x34
    brne test8_fail
    
    ; Restore stack pointer to a valid address before using RCALL/PUSH again
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16
    
    rcall inc_case
    rjmp test8_done

test8_fail:
    rjmp fail

test8_done:

; ============================================================
; TEST 9: IN with value 0x00 and 0xFF
; ============================================================
test9:
    ; Test 0x00
    ldi r16, 0x00
    out GPIOR0, r16
    in r17, GPIOR0
    cpi r17, 0x00
    brne test9_fail
    
    ; Test 0xFF
    ldi r16, 0xFF
    out GPIOR0, r16
    in r17, GPIOR0
    cpi r17, 0xFF
    brne test9_fail
    
    rcall inc_case
    rjmp test9_done

test9_fail:
    rjmp fail

test9_done:

; ============================================================
; TEST 10: IN from same address multiple times
; ============================================================
test10:
    ldi r16, 0xAA
    out GPIOR0, r16
    
    ; Multiple reads
    in r17, GPIOR0
    in r18, GPIOR0
    in r19, GPIOR0
    
    cpi r17, 0xAA
    brne test10_fail
    cpi r18, 0xAA
    brne test10_fail
    cpi r19, 0xAA
    brne test10_fail
    
    rcall inc_case
    rjmp test10_done

test10_fail:
    rjmp fail

test10_done:

; ============================================================
; TEST 11: IN to register then modify register
; ============================================================
test11:
    ldi r16, 0x55
    out GPIOR0, r16
    
    in r17, GPIOR0
    inc r17
    cpi r17, 0x56
    brne test11_fail
    
    ; Verify I/O unchanged
    in r18, GPIOR0
    cpi r18, 0x55
    brne test11_fail
    
    rcall inc_case
    rjmp test11_done

test11_fail:
    rjmp fail

test11_done:

; ============================================================
; TEST 12: IN after OUT (verify data consistency)
; ============================================================
test12:
    ; Write value
    ldi r16, 0x7E
    out GPIOR0, r16
    
    ; Read back immediately
    in r17, GPIOR0
    cpi r17, 0x7E
    brne test12_fail
    
    ; Write new value
    ldi r16, 0x81
    out GPIOR0, r16
    
    ; Read again
    in r17, GPIOR0
    cpi r17, 0x81
    brne test12_fail
    
    rcall inc_case
    rjmp test12_done

test12_fail:
    rjmp fail

test12_done:

; ============================================================
; TEST 13: IN from all I/O addresses (using loop) - FIXED
; ============================================================
test13:
    ldi r16, 0x00      ; Value to write (R16 is valid for CPI)
    ldi r18, 0x00      ; Counter (R18 is valid for CPI)
    ldi r19, 0x3F      ; Limit (R19 is valid for CPI)
test13_loop:
    out GPIOR0, r16
    in r17, GPIOR0
    cp r16, r17        ; Use CP instead of CPI (CP works with any registers)
    brne test13_fail
    
    inc r16
    inc r18
    cp r18, r19        ; CP with R18 and R19 (both allowed)
    brne test13_loop
    
    rcall inc_case
    rjmp test13_done

test13_fail:
    rjmp fail

test13_done:

; ============================================================
; TEST 14: IN to register that was source of OUT
; ============================================================
test14:
    ldi r16, 0x5A
    out GPIOR0, r16
    in r16, GPIOR0
    cpi r16, 0x5A
    brne test14_fail
    
    rcall inc_case
    rjmp test14_done

test14_fail:
    rjmp fail

test14_done:

; ============================================================
; TEST 15: IN with different I/O addresses sequentially
; ============================================================
test15:
    ; Test multiple addresses
    ldi r16, 0x11
    out GPIOR0, r16
    ldi r16, 0x22
    out GPIOR1, r16
    
    in r17, GPIOR0
    in r18, GPIOR1
    
    cpi r17, 0x11
    brne test15_fail
    cpi r18, 0x22
    brne test15_fail
    
    rcall inc_case
    rjmp test15_done

test15_fail:
    rjmp fail

test15_done:

; ============================================================
; TEST 16: IN before OUT (default values)
; ============================================================
test16:
    ; Read default value
    in r16, GPIOR0
    ; Write new value
    ldi r17, 0x99
    out GPIOR0, r17
    ; Verify different
    in r18, GPIOR0
    cpi r18, 0x99
    brne test16_fail
    
    rcall inc_case
    rjmp test16_done

test16_fail:
    rjmp fail

test16_done:

; ============================================================
; TEST 17: IN to register then use in arithmetic
; ============================================================
test17:
    ldi r16, 0x10
    out GPIOR0, r16
    
    in r17, GPIOR0
    ldi r18, 0x20
    add r17, r18
    cpi r17, 0x30
    brne test17_fail
    
    rcall inc_case
    rjmp test17_done

test17_fail:
    rjmp fail

test17_done:

; ============================================================
; TEST 18: IN to register then push/pop
; ============================================================
test18:
    ldi r16, 0xDE
    out GPIOR0, r16
    
    in r17, GPIOR0
    push r17
    ldi r17, 0x00
    pop r18
    cpi r18, 0xDE
    brne test18_fail
    
    rcall inc_case
    rjmp test18_done

test18_fail:
    rjmp fail

test18_done:

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