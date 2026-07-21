; ============================================================
; SEH instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; SEH  : Set Half Carry Flag (H) in Status Register
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
; TEST 1: Basic Set
; Ensure SEH sets bit 5 in SREG
; ============================================================
test1:
    out SREG, r0          ; Ensure all flags are 0
    seh                   ; Set H-flag
    in r16, SREG
    sbrs r16, 5           ; Bit 5 is H-flag
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 2: Verify SEH does not affect other flags
; Set Carry (C=bit 0) then call SEH
; ============================================================
test2:
    out SREG, r0
    sec                   ; Set C (bit 0)
    seh                   ; Set H (bit 5)
    in r16, SREG
    sbrs r16, 0           ; Ensure C is still set
    rjmp fail
    sbrs r16, 5           ; Ensure H is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 3: Verify H-flag state
; Logic: H-flag is used by DAA/DAS equivalent logic in AVR.
; ============================================================
test3:
    out SREG, r0
    seh
    in r16, SREG
    andi r16, 0x20        ; Mask bit 5 (0x20)
    breq fail             ; Should not be zero
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