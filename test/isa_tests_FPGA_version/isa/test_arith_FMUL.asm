; ============================================================
; FMUL instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; FMUL Rd, Rr  :  r1:r0 = (Rd * Rr) << 1
; Both operands are UNSIGNED 8-bit integers (treated as fractions).
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
; TEST 1: Small values
; 0x40 (64) * 0x40 (64) = 0x1000 (4096)
; Shifted left by 1: 0x2000. Carry = 0.
; ============================================================
test1:
    ldi r16, 0x40
    ldi r17, 0x40
    fmul r16, r17
    
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
; TEST 2: Mid-range fractional (0.5 * 0.5)
; 0x80 (128) * 0x80 (128) = 0x4000 (16384)
; Shifted left by 1: 0x8000. Carry = 0.
; ============================================================
test2:
    ldi r16, 0x80
    ldi r17, 0x80
    fmul r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x00
    brne fail2
    cpi r19, 0x80
    breq skip_2
fail2:
    rjmp fail
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Minimum values
; 0x01 (1) * 0x01 (1) = 0x0001 (1)
; Shifted left by 1: 0x0002. Carry = 0.
; ============================================================
test3:
    ldi r16, 0x01
    ldi r17, 0x01
    fmul r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x02
    brne fail3
    cpi r19, 0x00
    breq skip_3
fail3:
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: Max unsigned values (Triggers Carry)
; 0xFF (255) * 0xFF (255) = 0xFE01 (65025)
; Shifted left by 1: 0xFC02. 
; The highest bit (1) is pushed to the Carry flag. Carry = 1.
; ============================================================
test4:
    ldi r16, 0xFF
    ldi r17, 0xFF
    fmul r16, r17
    
    mov r18, r0
    mov r19, r1
    
    cpi r18, 0x02
    brne fail4
    cpi r19, 0xFC
    breq skip_4
fail4:
    rjmp fail
skip_4:
    rcall inc_case

; ============================================================
; TEST 5: Verify Carry (C) Flag is SET when MSB of result is 1
; 0xC0 (192) * 0xC0 (192) = 0x9000 (36864)
; Shifted left by 1: 0x2000. Carry = 1.
; ============================================================
test5:
    clc                       ; Clear carry manually first
    ldi r16, 0xC0
    ldi r17, 0xC0
    fmul r16, r17             
    
    brcc fail5                ; Branch if C is NOT set (Fail)
    
    mov r18, r0
    mov r19, r1
    cpi r18, 0x00
    brne fail5
    cpi r19, 0x20
    breq skip_5
fail5:
    rjmp fail
skip_5:
    rcall inc_case

; ============================================================
; TEST 6: Verify Carry (C) Flag is CLEARED when MSB of result is 0
; ============================================================
test6:
    sec                       ; Set carry manually first
    ldi r16, 0x40
    ldi r17, 0x40
    fmul r16, r17             
    
    brcs fail6                ; Branch if C is still SET (Fail)
    rjmp skip_6
fail6:
    rjmp fail
skip_6:
    rcall inc_case

; ============================================================
; TEST 7: Multiply by Zero
; 0x00 * 0xFF = 0x0000. Shifted left by 1 = 0x0000.
; ============================================================
test7:
    ldi r16, 0x00
    ldi r17, 0xFF
    fmul r16, r17
    
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
; TEST 8: Verify Zero (Z) Flag is SET on 0x0000 Result
; ============================================================
test8:
    ldi r16, 0x00
    ldi r17, 0xAA
    fmul r16, r17             ; Result is 0, Z should be SET
    
    brne fail8                ; Branch if Z is NOT set
    rjmp skip_8
fail8:
    rjmp fail
skip_8:
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