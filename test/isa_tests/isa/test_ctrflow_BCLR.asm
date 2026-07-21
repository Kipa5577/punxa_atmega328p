; ============================================================
; BCLR instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; BCLR s  : Clear bit s in Status Register (SREG)
; s is a value 0-7 (SREG bit index)
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
; TEST 1: Clear Carry Flag (C = bit 0)
; ============================================================
test1:
    sec                   ; Set C first
    bclr 0                ; Clear Carry
    in r16, SREG
    sbrc r16, 0           ; Fail if bit 0 is still set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 2: Clear Zero Flag (Z = bit 1)
; ============================================================
test2:
    bset 1                ; Set Z
    bclr 1                ; Clear Zero
    in r16, SREG
    sbrc r16, 1           ; Fail if bit 1 is still set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 3: Clear Global Interrupt Enable (I = bit 7)
; ============================================================
test3:
    sei                   ; Set I
    bclr 7                ; Clear Global Interrupt
    in r16, SREG
    sbrc r16, 7           ; Fail if bit 7 is still set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 4: Verify BCLR does not affect other bits
; Set Carry and Zero, clear only Carry, check Zero is still set.
; ============================================================
test4:
    out SREG, r0          ; Clear SREG
    bset 0                ; Set C
    bset 1                ; Set Z
    bclr 0                ; Clear C
    
    in r16, SREG
    sbrc r16, 0           ; Fail if C is still set
    rjmp fail
    sbrs r16, 1           ; Fail if Z is NOT set
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