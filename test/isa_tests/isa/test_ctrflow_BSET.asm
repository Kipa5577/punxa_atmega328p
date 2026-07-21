; ============================================================
; BSET instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; BSET s  : Set bit s in Status Register (SREG)
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
; TEST 1: Set Carry Flag (C = bit 0)
; ============================================================
test1:
    bset 0
    in r16, SREG
    sbrs r16, 0           ; Skip next if bit 0 is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 2: Set Zero Flag (Z = bit 1)
; ============================================================
test2:
    bset 1
    in r16, SREG
    sbrs r16, 1           ; Skip next if bit 1 is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 3: Set Global Interrupt Enable (I = bit 7)
; ============================================================
test3:
    bset 7
    in r16, SREG
    sbrs r16, 7           ; Skip next if bit 7 is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 4: Verify BSET does not affect other bits
; Reset SREG, set bit 2 (N), check bits 1 and 0 are still 0.
; ============================================================
test4:
    out SREG, r0          ; Clear all flags
    bset 2                ; Set Negative Flag
    in r16, SREG
    sbrc r16, 0           ; Fail if bit 0 is set
    rjmp fail
    sbrc r16, 1           ; Fail if bit 1 is set
    rjmp fail
    sbrs r16, 2           ; Fail if bit 2 is NOT set
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