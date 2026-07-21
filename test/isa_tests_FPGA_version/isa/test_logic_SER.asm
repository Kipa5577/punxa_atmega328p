; ============================================================
; SER instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; SER Rd  :  Rd = 0xFF   (Alias for LDI Rd, 0xFF)
; Only works on registers r16..r31.
; Updates: None (SREG is unaffected).
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
; TEST 1: Set a zeroed register
; r16 = 0x00 -> SER -> r16 = 0xFF
; ============================================================
test1:
    ldi r16, 0x00
    ser r16
    cpi r16, 0xFF
    breq skip_1
    rjmp fail
skip_1:
    rcall inc_case

; ============================================================
; TEST 2: Set an already set register
; r16 = 0xFF -> SER -> r16 = 0xFF
; ============================================================
test2:
    ldi r16, 0xFF
    ser r16
    cpi r16, 0xFF
    breq skip_2
    rjmp fail
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Set a register with a random bit pattern
; r16 = 0xAA -> SER -> r16 = 0xFF
; ============================================================
test3:
    ldi r16, 0xAA
    ser r16
    cpi r16, 0xFF
    breq skip_3
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: Verify operation on a higher register (r31)
; r31 = 0x00 -> SER -> r31 = 0xFF
; ============================================================
test4:
    ldi r31, 0x00
    ser r31
    cpi r31, 0xFF
    breq skip_4
    rjmp fail
skip_4:
    rcall inc_case

; ============================================================
; TEST 5: Verify Carry (C) flag is preserved when SET
; ============================================================
test5:
    ldi r16, 0x00
    sec                   ; Set Carry flag
    ser r16               ; Should not clear the Carry flag
    brcs skip_5           ; Branch if Carry is Set
    rjmp fail
skip_5:
    rcall inc_case

; ============================================================
; TEST 6: Verify Carry (C) flag is preserved when CLEARED
; ============================================================
test6:
    ldi r16, 0x00
    clc                   ; Clear Carry flag
    ser r16               ; Should not set the Carry flag
    brcc skip_6           ; Branch if Carry is Cleared
    rjmp fail
skip_6:
    rcall inc_case

; ============================================================
; TEST 7: Verify Zero (Z) flag is preserved when SET
; ============================================================
test7:
    ldi r16, 0x00
    clr r17               ; CLR sets the Zero flag
    ser r16               ; SER should NOT affect flags
    breq skip_7           ; Branch if Zero is Set
    rjmp fail
skip_7:
    rcall inc_case

; ============================================================
; TEST 8: Verify Zero (Z) flag is preserved when CLEARED
; ============================================================
test8:
    ldi r16, 0x00
    ldi r17, 0x01
    tst r17               ; TST on 0x01 clears the Zero flag
    ser r16               ; SER should NOT affect flags
    brne skip_8           ; Branch if Zero is Cleared
    rjmp fail
skip_8:
    rcall inc_case

; ============================================================
; TEST 9: Verify Negative (N) flag is preserved when SET
; ============================================================
test9:
    ldi r16, 0x00
    ldi r17, 0x80
    tst r17               ; TST on 0x80 sets the Negative flag
    ser r16               ; SER should NOT affect flags
    brmi skip_9           ; Branch if Negative is Set (Minus)
    rjmp fail
skip_9:
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