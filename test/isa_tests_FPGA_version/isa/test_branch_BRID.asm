; ============================================================
; Global Interrupt Enable (I-flag) test suite for ATmega328P
; I-flag is Bit 7 of the Status Register (SREG).
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
; TEST 1: Interrupts Disabled (I=0)
; We use CLI to clear the I-flag. 
; ============================================================
test1:
    cli                   ; Clear Global Interrupt Enable (I=0)
    in r16, SREG
    sbrc r16, 7           ; Skip next if bit 7 (I) is cleared
    rjmp fail             ; Fail if I is 1
    rcall inc_case

; ============================================================
; TEST 2: Interrupts Enabled (I=1)
; We use SEI to set the I-flag.
; ============================================================
test2:
    sei                   ; Set Global Interrupt Enable (I=1)
    in r16, SREG
    sbrs r16, 7           ; Skip next if bit 7 (I) is set
    rjmp fail             ; Fail if I is 0
    rcall inc_case

; ============================================================
; TEST 3: Logic simulation of "Branch if Interrupts Disabled"
; Logic: If I==0, jump to target.
; ============================================================
test3:
    cli
    in r16, SREG
    sbrc r16, 7           ; Skip if bit 7 is 0
    rjmp fail             ; Fails if bit 7 is 1
    rjmp branch_success   ; Success path
    rjmp fail
branch_success:
    rcall inc_case

; ============================================================
; TEST 4: Logic simulation of "Branch if Interrupts Enabled"
; Logic: If I==1, jump to target.
; ============================================================
test4:
    sei
    in r16, SREG
    sbrs r16, 7           ; Skip if bit 7 is 1
    rjmp fail             ; Fails if bit 7 is 0
    rjmp branch_success_2 ; Success path
    rjmp fail
branch_success_2:
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