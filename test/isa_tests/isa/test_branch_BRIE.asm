; ============================================================
; Global Interrupt Enable (I-flag) test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; The I-flag is Bit 7 of the SREG register.
; ============================================================
; -------------------------
; SRAM variables & Defines
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
; TEST 1: Check Interrupts Enabled (I=1)
; We use CLI (Clear) and SEI (Set) to toggle the flag.
; ============================================================
test1:
    sei                   ; Set Global Interrupt Enable (I=1)
    in r16, SREG
    sbrs r16, 7           ; Skip next if bit 7 is set
    rjmp fail             ; Fail if I is 0
    rcall inc_case

; ============================================================
; TEST 2: Check Interrupts Disabled (I=0)
; ============================================================
test2:
    cli                   ; Clear Global Interrupt Enable (I=0)
    in r16, SREG
    sbrc r16, 7           ; Skip next if bit 7 is cleared
    rjmp fail             ; Fail if I is 1
    rcall inc_case

; ============================================================
; TEST 3: Branching based on I-flag
; We can use a combination of reading SREG and branching.
; ============================================================
test3:
    sei
    in r16, SREG
    sbrs r16, 7           ; Check if I is set
    rjmp fail             ; Should not happen
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