; ============================================================
; BRTS instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; BRTS k  : Branch to k if T-flag in SREG is set (T=1).
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
; TEST 1: T-flag Set (T=1)
; BST sets T-flag based on a bit in a register.
; ============================================================
test1:
    ldi r16, 0x01
    bst r16, 0            ; Bit 0 of r16 is 1, so T=1
    brts branch1          ; Should branch
    rjmp fail
branch1:
    rcall inc_case

; ============================================================
; TEST 2: T-flag Clear (T=0)
; BST sets T-flag based on a bit in a register.
; ============================================================
test2:
    ldi r16, 0x00
    bst r16, 0            ; Bit 0 of r16 is 0, so T=0
    brts fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 3: Direct Set T-flag instruction (SET)
; ============================================================
test3:
    set                   ; Sets T-flag
    brts branch3          ; Should branch
    rjmp fail
branch3:
    rcall inc_case

; ============================================================
; TEST 4: Direct Clear T-flag instruction (CLT)
; ============================================================
test4:
    clt                   ; Clears T-flag
    brts fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 5: Verify branch distance (Forward)
; ============================================================
test5:
    set
    brts jump_fwd
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