; ============================================================
; MULS instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; MULS Rd, Rr  :  r1:r0 = Rd * Rr (Signed multiplication)
; Both operands are signed 8-bit integers.
; Result is a signed 16-bit integer.
; Updates: Z (Set if result is 0x0000), C (Set if bit 15 is set)
; Only works on registers r16..r31.
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
; TEST 1: Two positive numbers
; 10 * 5 = 50 (0x0032)
; ============================================================
test1:
    ldi r16, 10
    ldi r17, 5
    muls r16, r17
    
    mov r18, r0               ; Move low byte to checkable register
    mov r19, r1               ; Move high byte to checkable register
    
    cpi r18, 0x32
    brne fail1
    cpi r19, 0x00
    breq skip_1
fail1:
    rjmp fail
skip_1:
    rcall inc_case

; ============================================================
; TEST 2: Positive * Negative
; 10 * -5 = -50 (0xFFCE)
; ============================================================
test2:
    ldi r16, 10
    ldi r17, -5               ; 0xFB
    muls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0xCE             ; Low byte of -50
    brne fail2
    cpi r19, 0xFF             ; High byte of -50
    breq skip_2
fail2:
    rjmp fail
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Negative * Positive
; -10 * 5 = -50 (0xFFCE)
; ============================================================
test3:
    ldi r16, -10              ; 0xF6
    ldi r17, 5
    muls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0xCE
    brne fail3
    cpi r19, 0xFF
    breq skip_3
fail3:
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: Negative * Negative
; -10 * -5 = 50 (0x0032)
; ============================================================
test4:
    ldi r16, -10
    ldi r17, -5
    muls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x32
    brne fail4
    cpi r19, 0x00
    breq skip_4
fail4:
    rjmp fail
skip_4:
    rcall inc_case

; ============================================================
; TEST 5: Multiply by Zero
; 127 * 0 = 0 (0x0000)
; ============================================================
test5:
    ldi r16, 127
    ldi r17, 0
    muls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail5
    cpi r19, 0x00
    breq skip_5
fail5:
    rjmp fail
skip_5:
    rcall inc_case

; ============================================================
; TEST 6: Max Positive * Max Positive
; 127 * 127 = 16129 (0x3F01)
; ============================================================
test6:
    ldi r16, 127              ; 0x7F
    ldi r17, 127              ; 0x7F
    muls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x01
    brne fail6
    cpi r19, 0x3F
    breq skip_6
fail6:
    rjmp fail
skip_6:
    rcall inc_case

; ============================================================
; TEST 7: Min Negative * Min Negative
; -128 * -128 = 16384 (0x4000)
; ============================================================
test7:
    ldi r16, 128              ; 0x80 (-128 signed)
    ldi r17, 128              ; 0x80 (-128 signed)
    muls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail7
    cpi r19, 0x40
    breq skip_7
fail7:
    rjmp fail
skip_7:
    rcall inc_case

; ============================================================
; TEST 8: Max Positive * Min Negative
; 127 * -128 = -16256 (0xC080)
; ============================================================
test8:
    ldi r16, 127              ; 0x7F
    ldi r17, 128              ; 0x80 (-128)
    muls r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x80
    brne fail8
    cpi r19, 0xC0
    breq skip_8
fail8:
    rjmp fail
skip_8:
    rcall inc_case

; ============================================================
; TEST 9: Verify Zero (Z) Flag is Set on Zero Result
; ============================================================
test9:
    ldi r16, 0
    ldi r17, -55
    muls r16, r17             ; Result is 0, Z should be SET
    
    brne fail9                ; Branch if Z is NOT set
    rjmp skip_9
fail9:
    rjmp fail
skip_9:
    rcall inc_case

; ============================================================
; TEST 10: Verify Carry (C) Flag is Set on Negative Result
; In MULS, C is set if bit 15 of the 16-bit result is 1.
; 10 * -10 = -100 (0xFF9C) -> Bit 15 is 1, so C should be SET.
; ============================================================
test10:
    ldi r16, 10
    ldi r17, -10
    muls r16, r17             ; Result is negative, C should be SET
    
    brcc fail10               ; Branch if C is NOT set
    rjmp skip_10
fail10:
    rjmp fail
skip_10:
    rcall inc_case

; ============================================================
; TEST 11: Verify Carry (C) Flag is Cleared on Positive Result
; -5 * -5 = 25 (0x0019) -> Bit 15 is 0, so C should be CLEARED.
; ============================================================
test11:
    ; Manually set carry flag to ensure MULS clears it
    sec                       
    
    ldi r16, -5
    ldi r17, -5
    muls r16, r17             ; Result is positive, C should be CLEARED
    
    brcs fail11               ; Branch if C is still SET
    rjmp skip_11
fail11:
    rjmp fail
skip_11:
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