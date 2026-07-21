; ============================================================
; FMULS instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; FMULS Rd, Rr  :  r1:r0 = (Rd * Rr) << 1
; Both operands are SIGNED 8-bit integers (treated as fractions).
; Updates: Z (Set if result is 0x0000), C (Set if bit 15 of unshifted result is 1)
; STRICT RESTRICTION: Only works on registers r16..r23.
; ============================================================
; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SPH          = 0x3E
.equ SPL          = 0x3D
; -------------------------
; Reset
; -------------------------
reset:
; init stack
    ldi r16, 0x08
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16
; init state
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Positive * Positive
; 0x20 (32) * 0x20 (32) = 0x0400 (1024)
; Shifted left by 1: 0x0800. Carry = 0.
; ============================================================
test1:
    ldi r16, 0x20
    ldi r17, 0x20
    fmuls r16, r17
    
    mov r18, r0               ; Move low byte to checkable register
    mov r19, r1               ; Move high byte to checkable register
    
    cpi r18, 0x00
    brne fail1
    cpi r19, 0x08
    breq skip_1
fail1:
    rjmp fail
skip_1:
    rcall inc_case

; ============================================================
; TEST 2: Positive * Negative
; 0x20 (32) * 0xE0 (-32) = 0xFC00 (-1024)
; Shifted left by 1: 0xF800. Carry = 1.
; ============================================================
test2:
    ldi r16, 0x20
    ldi r17, 0xE0             ; -32 signed
    fmuls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail2
    cpi r19, 0xF8
    breq skip_2
fail2:
    rjmp fail
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Negative * Negative
; 0xE0 (-32) * 0xE0 (-32) = 0x0400 (1024)
; Shifted left by 1: 0x0800. Carry = 0.
; ============================================================
test3:
    ldi r16, 0xE0
    ldi r17, 0xE0
    fmuls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail3
    cpi r19, 0x08
    breq skip_3
fail3:
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: Max Positive * Max Positive
; 0x7F (127) * 0x7F (127) = 0x3F01 (16129)
; Shifted left by 1: 0x7E02.
; ============================================================
test4:
    ldi r16, 0x7F
    ldi r17, 0x7F
    fmuls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x02
    brne fail4
    cpi r19, 0x7E
    breq skip_4
fail4:
    rjmp fail
skip_4:
    rcall inc_case

; ============================================================
; TEST 5: Min Negative * Min Negative
; 0x80 (-128) * 0x80 (-128) = 0x4000 (16384)
; Shifted left by 1: 0x8000. Carry = 0 (Product is positive).
; ============================================================
test5:
    ldi r16, 0x80
    ldi r17, 0x80
    fmuls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail5
    cpi r19, 0x80
    breq skip_5
fail5:
    rjmp fail
skip_5:
    rcall inc_case

; ============================================================
; TEST 6: Multiply by Zero
; 0x7F (127) * 0x00 (0) = 0x0000. Shifted left by 1 = 0x0000.
; ============================================================
test6:
    ldi r16, 0x7F
    ldi r17, 0x00
    fmuls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail6
    cpi r19, 0x00
    breq skip_6
fail6:
    rjmp fail
skip_6:
    rcall inc_case

; ============================================================
; TEST 7: Negative One * Max Positive
; 0xFF (-1) * 0x7F (127) = 0xFF81 (-127)
; Shifted left by 1: 0xFF02. Carry = 1.
; ============================================================
test7:
    ldi r16, 0xFF
    ldi r17, 0x7F
    fmuls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x02
    brne fail7
    cpi r19, 0xFF
    breq skip_7
fail7:
    rjmp fail
skip_7:
    rcall inc_case

; ============================================================
; TEST 8: Verify Carry (C) Flag is SET on Negative Result
; Using values from Test 7 where result is negative.
; ============================================================
test8:
    clc                       ; Clear carry manually first
    ldi r16, 0xFF             ; -1
    ldi r17, 0x7F             ; 127
    fmuls r16, r17            ; Result is negative
    
    brcc fail8                ; Branch if C is NOT set (Fail)
    rjmp skip_8
fail8:
    rjmp fail
skip_8:
    rcall inc_case

; ============================================================
; TEST 9: Verify Carry (C) Flag is CLEARED on Positive Result
; ============================================================
test9:
    sec                       ; Set carry manually first
    ldi r16, 0x20             ; 32
    ldi r17, 0x20             ; 32
    fmuls r16, r17            ; Result is positive
    
    brcs fail9                ; Branch if C is still SET (Fail)
    rjmp skip_9
fail9:
    rjmp fail
skip_9:
    rcall inc_case

; ============================================================
; TEST 10: Verify Zero (Z) Flag is SET on 0x0000 Result
; ============================================================
test10:
    ldi r16, 0x00
    ldi r17, 0x80
    fmuls r16, r17            ; Result is 0, Z should be SET
    
    brne fail10               ; Branch if Z is NOT set
    rjmp skip_10
fail10:
    rjmp fail
skip_10:
    rcall inc_case

; ============================================================
; SUCCESS
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end

; ============================================================
; FAILURE
; final_result = -1, stop execution
; ============================================================
fail:
    ldi r16, -1
    sts final_result, r16
    rjmp end

; ============================================================
; increment test_case
; ============================================================
inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret