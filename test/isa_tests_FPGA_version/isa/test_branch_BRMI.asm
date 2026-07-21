; ============================================================
; BRMI instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; BRMI k  : Branch to k if Negative Flag (N) is set.
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
    ldi r16, 0x08
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Negative result (N=1)
; 0x80 (10000000) is negative. BRMI should jump.
; ============================================================
test1:
    ldi r16, 0x80
    tst r16               ; Sets N=1
    brmi branch1          ; Should branch
    rjmp fail
branch1:
    rcall inc_case

; ============================================================
; TEST 2: Positive result (N=0)
; 0x7F (01111111) is positive. BRMI should NOT jump.
; ============================================================
test2:
    ldi r16, 0x7F
    tst r16               ; Sets N=0
    brmi fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 3: Zero result (N=0)
; 0x00 is not negative. BRMI should NOT jump.
; ============================================================
test3:
    ldi r16, 0x00
    tst r16               ; Sets N=0
    brmi fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 4: Underflow resulting in negative (N=1)
; 10 - 20 = 246 (0xF6). MSB is 1, so N=1. BRMI should jump.
; ============================================================
test4:
    ldi r16, 10
    subi r16, 20          ; Result 246, N=1
    brmi branch4          ; Should branch
    rjmp fail
branch4:
    rcall inc_case

; ============================================================
; TEST 5: Verify BRMI branch distance (Forward)
; ============================================================
test5:
    ldi r16, 0x80
    tst r16
    brmi jump_fwd
    rjmp fail
jump_fwd:
    rcall inc_case

; ============================================================
; TEST 6: Branch NOT taken with complex logic
; 0x7F + 0x01 = 0x80. If we use ANDI to mask, 
; 0x7F & 0x01 = 0x01 (Positive). Should not jump.
; ============================================================
test6:
    ldi r16, 0x7F
    andi r16, 0x01        ; Result 0x01, N=0
    brmi fail             ; Should NOT branch
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