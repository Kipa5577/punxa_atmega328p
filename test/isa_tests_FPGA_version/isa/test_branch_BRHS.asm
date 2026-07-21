; ============================================================
; BRHS instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; BRHS k  : Branch to k if Half Carry Flag (H) is set.
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
; TEST 1: Half Carry Set (H=1)
; Adding 0x08 + 0x08 causes a carry from bit 3 to 4.
; ============================================================
test1:
    ldi r16, 0x08
    ldi r17, 0x08
    add r16, r17          ; 0x08+0x08 = 0x10, H=1
    brhs branch1          ; Should branch
    rjmp fail
branch1:
    rcall inc_case

; ============================================================
; TEST 2: Half Carry Clear (H=0)
; Adding 0x01 + 0x01 does not cause a carry from bit 3.
; ============================================================
test2:
    ldi r16, 0x01
    ldi r17, 0x01
    add r16, r17          ; 0x01+0x01 = 0x02, H=0
    brhs fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 3: Manual SREG manipulation
; Manually set H flag (bit 5 in SREG)
; ============================================================
test3:
    in r16, SREG
    ori r16, 0x20         ; Set bit 5 (H)
    out SREG, r16
    
    brhs branch3          ; Should branch
    rjmp fail
branch3:
    rcall inc_case

; ============================================================
; TEST 4: Manual SREG manipulation
; Manually clear H flag
; ============================================================
test4:
    in r16, SREG
    andi r16, ~0x20       ; Clear bit 5 (H)
    out SREG, r16
    
    brhs fail             ; Should NOT branch
    rcall inc_case

; ============================================================
; TEST 5: Verify branch distance (Forward)
; ============================================================
test5:
    ldi r16, 0x08
    ldi r17, 0x08
    add r16, r17          ; H=1
    brhs jump_fwd
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