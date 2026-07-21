; ============================================================
; FMULSU instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; FMULSU Rd, Rr  :  r1:r0 = (Rd * Rr) << 1
; Rd is SIGNED, Rr is UNSIGNED (both treated as fractions).
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
; TEST 1: Positive Signed * Positive Unsigned
; 0x40 (64) * 0x40 (64) = 0x1000 (4096)
; Shifted left by 1: 0x2000. Carry = 0.
; ============================================================
test1:
    ldi r16, 0x40             ; Signed positive
    ldi r17, 0x40             ; Unsigned positive
    fmulsu r16, r17
    
    mov r18, r0               ; Move low byte to checkable register
    mov r19, r1               ; Move high byte to checkable register
    
    cpi r18, 0x00
    brne fail1
    cpi r19, 0x20
    breq skip_1
fail1:
    rjmp fail
skip_1:
    rcall inc_case

; ============================================================
; TEST 2: Negative Signed * Positive Unsigned
; 0xC0 (-64) * 0x40 (64) = 0xF000 (-4096)
; Shifted left by 1: 0xE000. Carry = 1.
; ============================================================
test2:
    ldi r16, 0xC0             ; Signed negative
    ldi r17, 0x40             ; Unsigned positive
    fmulsu r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail2
    cpi r19, 0xE0
    breq skip_2
fail2:
    rjmp fail
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Max Positive Signed * Max Unsigned
; 0x7F (127) * 0xFF (255) = 0x7E81 (32385)
; Shifted left by 1: 0xFD02. Carry = 0.
; ============================================================
test3:
    ldi r16, 0x7F             ; Max signed positive
    ldi r17, 0xFF             ; Max unsigned
    fmulsu r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x02
    brne fail3
    cpi r19, 0xFD
    breq skip_3
fail3:
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: Min Negative Signed * Max Unsigned
; 0x80 (-128) * 0xFF (255) = 0x8080 (-32640)
; Shifted left by 1: 0x0100. Carry = 1.
; ============================================================
test4:
    ldi r16, 0x80             ; Min signed negative
    ldi r17, 0xFF             ; Max unsigned
    fmulsu r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail4
    cpi r19, 0x01
    breq skip_4
fail4:
    rjmp fail
skip_4:
    rcall inc_case

; ============================================================
; TEST 5: Multiply by Zero (Signed Operand)
; 0x00 * 0xFF = 0x0000. Shifted left by 1: 0x0000.
; ============================================================
test5:
    ldi r16, 0x00
    ldi r17, 0xFF
    fmulsu r16, r17
    
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
; TEST 6: Multiply by Zero (Unsigned Operand)
; 0xFF (-1) * 0x00 = 0x0000. Shifted left by 1: 0x0000.
; ============================================================
test6:
    ldi r16, 0xFF
    ldi r17, 0x00
    fmulsu r16, r17
    
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
; TEST 7: Verify Zero (Z) Flag is SET on Zero Result
; ============================================================
test7:
    ldi r16, 0x00
    ldi r17, 0x80
    fmulsu r16, r17           ; Result is 0, Z should be SET
    
    brne fail7                ; Branch if Z is NOT set
    rjmp skip_7
fail7:
    rjmp fail
skip_7:
    rcall inc_case

; ============================================================
; TEST 8: Verify Zero (Z) Flag is CLEARED on Non-Zero Result
; 0x01 * 0x01 = 0x0001 -> Shifted = 0x0002
; ============================================================
test8:
    ldi r16, 0x01
    ldi r17, 0x01
    fmulsu r16, r17           ; Result is non-zero, Z should be CLEARED
    
    breq fail8                ; Branch if Z is SET
    rjmp skip_8
fail8:
    rjmp fail
skip_8:
    rcall inc_case

; ============================================================
; TEST 9: Verify Carry (C) Flag is SET on Negative Unshifted Result
; 0xFF (-1) * 0x01 (1) = 0xFFFF (-1). 
; Bit 15 is 1, so Carry should be SET. Shifted result = 0xFFFE.
; ============================================================
test9:
    clc                       ; Clear carry manually first
    ldi r16, 0xFF             ; -1 (Signed)
    ldi r17, 0x01             ; 1 (Unsigned)
    fmulsu r16, r17           
    
    brcc fail9                ; Branch if C is NOT set
    rjmp skip_9
fail9:
    rjmp fail
skip_9:
    rcall inc_case

; ============================================================
; TEST 10: Verify Carry (C) Flag is CLEARED on Positive Unshifted Result
; 0x01 (1) * 0xFF (255) = 0x00FF (255). 
; Bit 15 is 0, so Carry should be CLEARED. Shifted result = 0x01FE.
; ============================================================
test10:
    sec                       ; Set carry manually first
    ldi r16, 0x01             ; 1 (Signed)
    ldi r17, 0xFF             ; 255 (Unsigned)
    fmulsu r16, r17           
    
    brcs fail10               ; Branch if C is SET
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