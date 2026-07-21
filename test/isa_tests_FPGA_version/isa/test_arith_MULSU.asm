; ============================================================
; MULSU instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; MULSU Rd, Rr  :  r1:r0 = Rd * Rr
; Rd is a SIGNED 8-bit integer. Rr is an UNSIGNED 8-bit integer.
; Result is a signed 16-bit integer.
; Updates: Z (Set if result is 0x0000), C (Set if bit 15 is set)
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
; TEST 1: Positive (signed) * Positive (unsigned)
; 10 * 5 = 50 (0x0032)
; ============================================================
test1:
    ldi r16, 10               ; Signed operand
    ldi r17, 5                ; Unsigned operand
    mulsu r16, r17
    
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
; TEST 2: Negative (signed) * Positive (unsigned)
; -10 * 5 = -50 (0xFFCE)
; ============================================================
test2:
    ldi r16, -10              ; 0xF6 (Signed)
    ldi r17, 5                ; 0x05 (Unsigned)
    mulsu r16, r17
    
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
; TEST 3: Max Positive (signed) * Max (unsigned)
; 127 * 255 = 32385 (0x7E81)
; ============================================================
test3:
    ldi r16, 127              ; 0x7F (Max positive signed)
    ldi r17, 255              ; 0xFF (Max unsigned)
    mulsu r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x81
    brne fail3
    cpi r19, 0x7E
    breq skip_3
fail3:
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: Min Negative (signed) * Max (unsigned)
; -128 * 255 = -32640 (0x8080)
; ============================================================
test4:
    ldi r16, 128              ; 0x80 (-128 signed)
    ldi r17, 255              ; 0xFF (Max unsigned)
    mulsu r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x80
    brne fail4
    cpi r19, 0x80
    breq skip_4
fail4:
    rjmp fail
skip_4:
    rcall inc_case

; ============================================================
; TEST 5: Negative One * Max (unsigned)
; -1 * 255 = -255 (0xFF01)
; ============================================================
test5:
    ldi r16, -1               ; 0xFF (Signed -1)
    ldi r17, 255              ; 0xFF (Unsigned 255)
    mulsu r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x01
    brne fail5
    cpi r19, 0xFF
    breq skip_5
fail5:
    rjmp fail
skip_5:
    rcall inc_case

; ============================================================
; TEST 6: Multiply by Zero (unsigned)
; 127 * 0 = 0 (0x0000)
; ============================================================
test6:
    ldi r16, 127
    ldi r17, 0
    mulsu r16, r17
    
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
; TEST 7: Multiply by Zero (signed)
; 0 * 255 = 0 (0x0000)
; ============================================================
test7:
    ldi r16, 0
    ldi r17, 255
    mulsu r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail7
    cpi r19, 0x00
    breq skip_7
fail7:
    rjmp fail
skip_7:
    rcall inc_case

; ============================================================
; TEST 8: Verify Zero (Z) Flag is Set on Zero Result
; ============================================================
test8:
    ldi r16, 0
    ldi r17, 100
    mulsu r16, r17            ; Result is 0, Z should be SET
    
    brne fail8                ; Branch if Z is NOT set
    rjmp skip_8
fail8:
    rjmp fail
skip_8:
    rcall inc_case

; ============================================================
; TEST 9: Verify Carry (C) Flag is Set on Negative Result
; In MULSU, C is set if bit 15 of the 16-bit result is 1.
; -2 * 2 = -4 (0xFFFC) -> Bit 15 is 1, so C should be SET.
; ============================================================
test9:
    ldi r16, -2
    ldi r17, 2
    mulsu r16, r17            ; Result is negative, C should be SET
    
    brcc fail9                ; Branch if C is NOT set
    rjmp skip_9
fail9:
    rjmp fail
skip_9:
    rcall inc_case

; ============================================================
; TEST 10: Verify Carry (C) Flag is Cleared on Positive Result
; 127 * 2 = 254 (0x00FE) -> Bit 15 is 0, so C should be CLEARED.
; ============================================================
test10:
    sec                       ; Manually set carry flag
    
    ldi r16, 127
    ldi r17, 2
    mulsu r16, r17            ; Result is positive, C should be CLEARED
    
    brcs fail10               ; Branch if C is still SET
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