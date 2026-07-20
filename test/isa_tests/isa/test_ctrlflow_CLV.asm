; ============================================================
; CLV instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; CLV  : Clear Overflow Flag (V) in Status Register
; ============================================================
; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SPH          = 0x3E
.equ SPL          = 0x3D
.equ SREG         = 0x3F      ; SREG I/O address
; -------------------------
; Reset
; -------------------------
reset:
    ; init stack (missing in the original file -- SP defaults to 0x0000
    ; at reset, so the first push/rcall/interrupt would hang forever
    ; waiting on a memory response that never comes; see HANDOFF.md)
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16

    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Basic Clear
; Set V flag, then use CLV to clear it.
; ============================================================
test1:
    sev                   ; Set V flag
    clv                   ; Clear Overflow Flag
    in r16, SREG
    sbrc r16, 3           ; Fail if bit 3 (V) is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 2: Clear V flag when already cleared (V=0)
; ============================================================
test2:
    out SREG, r0          ; Ensure all flags are 0
    clv                   ; Clear Overflow Flag
    in r16, SREG
    sbrc r16, 3           ; Fail if bit 3 is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 3: Verify CLV does not affect other flags
; Set Carry (C=bit 0) and V flag, clear V, check C.
; ============================================================
test3:
    out SREG, r0
    sec                   ; Set C (bit 0)
    sev                   ; Set V (bit 3)
    clv                   ; Clear V
    
    in r16, SREG
    sbrc r16, 3           ; Fail if V is still set
    rjmp fail
    sbrs r16, 0           ; Fail if Carry is NOT set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 4: Branching after CLV
; Use BRVC to verify the flag was correctly cleared.
; ============================================================
test4:
    out SREG, r0
    sev
    clv
    brvc branch4          ; Should branch
    rjmp fail
branch4:
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