; ============================================================
; CLT (Clear T-Flag) instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; CLT  : Clear T-Flag in Status Register
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
; Set T-flag, then use CLT to clear it.
; ============================================================
test1:
    set                   ; Set T-flag
    clt                   ; Clear T-flag
    in r16, SREG
    sbrc r16, 6           ; Bit 6 is T-flag
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 2: Clear T-flag when already cleared
; ============================================================
test2:
    out SREG, r0          ; Ensure all flags are 0
    clt                   ; Clear T-flag
    in r16, SREG
    sbrc r16, 6           ; Fail if bit 6 is set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 3: Verify CLT does not affect other flags
; Set Carry (C=bit 0) and T-flag, clear T, check C.
; ============================================================
test3:
    out SREG, r0
    sec                   ; Set C (bit 0)
    set                   ; Set T (bit 6)
    clt                   ; Clear T
    
    in r16, SREG
    sbrc r16, 6           ; Fail if T is still set
    rjmp fail
    sbrs r16, 0           ; Fail if Carry is NOT set
    rjmp fail
    rcall inc_case

; ============================================================
; TEST 4: Branching after CLT
; Use BRTC to verify the flag was correctly cleared.
; ============================================================
test4:
    out SREG, r0
    set
    clt
    brtc branch4          ; Should branch
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