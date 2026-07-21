; ============================================================
; CLS (Clear S-Flag) instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; Instruction used: BCLR 4 (Clears S-Flag)
; S-Flag is bit 4 of the Status Register (SREG).
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
; TEST 1: Clear S-Flag when already cleared (S=0)
; ============================================================
test1:
    out SREG, r0          ; Ensure all flags are 0
    bclr 4                ; Clear S-Flag
    in r16, SREG
    sbrc r16, 4           ; Fail if bit 4 is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 2: Clear S-Flag after setting it
; ============================================================
test2:
    bset 4                ; Set S-Flag
    bclr 4                ; Clear S-Flag
    in r16, SREG
    sbrc r16, 4           ; Fail if bit 4 is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 3: Verify BCLR 4 does not affect other bits
; Set Carry (C=bit 0) and S-Flag, clear S-Flag, check C.
; ============================================================
test3:
    out SREG, r0
    bset 0                ; Set Carry
    bset 4                ; Set S-Flag
    bclr 4                ; Clear S-Flag
    
    in r16, SREG
    sbrc r16, 4           ; Fail if S-flag is still set
    rjmp fail
    sbrs r16, 0           ; Fail if Carry is NOT set
    rjmp fail
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