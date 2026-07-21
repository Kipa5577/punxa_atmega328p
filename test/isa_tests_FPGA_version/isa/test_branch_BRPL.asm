; ============================================================
; BRPL instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; BRPL k  : Branch to k if Negative Flag (N) is cleared (N=0).
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
; TEST 1: Positive result (N=0)
; 0x7F (01111111) is positive. BRPL should branch.
; ============================================================
test1:
    ldi r16, 0x7F
    tst r16               ; Sets N=0
    brpl branch1          ; Should branch
    rjmp fail
branch1:
    rcall inc_case

; ============================================================
; TEST 2: Negative result (N=1)
; 0x80 (10000000) is negative. BRPL should NOT branch.
; ============================================================
test2:
    ldi r16, 0x80
    tst r16               ; Sets N=1
    brpl fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 3: Zero result (N=0)
; 0x00 is not negative (it is positive/zero). BRPL should branch.
; ============================================================
test3:
    ldi r16, 0x00
    tst r16               ; Sets N=0
    brpl branch3          ; Should branch
    rjmp fail
branch3:
    rcall inc_case

; ============================================================
; TEST 4: Subtraction resulting in positive (N=0)
; 20 - 10 = 10 (0x0A). MSB is 0, so N=0. BRPL should branch.
; ============================================================
test4:
    ldi r16, 20
    subi r16, 10          ; Result 10, N=0
    brpl branch4          ; Should branch
    rjmp fail
branch4:
    rcall inc_case

; ============================================================
; TEST 5: Verify BRPL branch distance (Forward)
; ============================================================
test5:
    ldi r16, 0x01
    tst r16
    brpl jump_fwd
    rjmp fail
jump_fwd:
    rcall inc_case

; ============================================================
; TEST 6: Branch NOT taken with complex logic
; 0x01 | 0x80 = 0x81 (10000001). MSB is 1, so N=1.
; ============================================================
test6:
    ldi r16, 0x01
    ori r16, 0x80         ; Result 0x81, N=1
    brpl fail             ; Should NOT branch
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