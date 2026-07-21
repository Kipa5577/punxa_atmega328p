; ============================================================
; BRVS instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; BRVS k  : Branch to k if Overflow Flag (V) is set (V=1).
; ============================================================
; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SPH          = 0x3E
.equ SPL          = 0x3D
.equ SREG         = 0x3F
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
; TEST 1: Overflow Set (V=1)
; Adding 0x7F (127) + 0x01 (1) = 0x80 (-128 signed).
; This causes a sign overflow, so V=1.
; ============================================================
test1:
    ldi r16, 0x7F
    ldi r17, 0x01
    add r16, r17          ; Result 0x80, V=1
    brvs branch1          ; Should branch
    rjmp fail
branch1:
    rcall inc_case

; ============================================================
; TEST 2: Overflow Clear (V=0)
; 0x7F (127) + 0x00 (0) = 0x7F (127 signed). No overflow.
; ============================================================
test2:
    ldi r16, 0x7F
    ldi r17, 0x00
    add r16, r17          ; Result 0x7F, V=0
    brvs fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 3: Manual SREG manipulation
; Manually set V flag (bit 3 in SREG)
; ============================================================
test3:
    in r16, SREG
    ori r16, 0x08         ; Set bit 3 (V)
    out SREG, r16
    
    brvs branch3          ; Should branch
    rjmp fail
branch3:
    rcall inc_case

; ============================================================
; TEST 4: Manual SREG manipulation
; Manually clear V flag
; ============================================================
test4:
    in r16, SREG
    andi r16, ~0x08       ; Clear bit 3 (V)
    out SREG, r16
    
    brvs fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 5: Verify branch distance (Forward)
; ============================================================
test5:
    ldi r16, 0x7F
    ldi r17, 0x01
    add r16, r17          ; V=1
    brvs jump_fwd
    rjmp fail
jump_fwd:
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