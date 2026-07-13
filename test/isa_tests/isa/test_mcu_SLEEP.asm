; ============================================================
; SLEEP instruction test suite
; ============================================================
; Note: SLEEP puts the CPU into a low-power mode.
; Verification requires waking the CPU (e.g., via Interrupt).
;
; NOTE: originally written against INT0 (EIMSK/EICRA), but the
; test harness (tb_ISA_tests.py) only wires up the TIMER0_OVF
; interrupt source into SimpleInterruptUnit - INT0 has no
; simulated hardware signal here, so it can never fire, and
; EIMSK/EICRA aren't implemented as real registers either
; (their addresses land unmapped, which hangs the bus on write -
; see VirtualGPIO/SimpleTimer). This version exercises the same
; SLEEP behavior using the Timer0 overflow interrupt instead.
; ============================================================
; SLEEP is a 1-word (16-bit) instruction
; Format: 1001 0101 1000 1000
; ============================================================

.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ isr_flag     = 0x0102
.equ TCCR0B       = 0x45
.equ TCNT0        = 0x46
.equ TIMSK0       = 0x6E
.equ TIFR0        = 0x47
.equ SPH          = 0x3E
.equ SPL          = 0x3D

; -------------------------
; Vector Table
; -------------------------
.org 0x0000             ; Reset Vector
    rjmp reset

.org 0x0020              ; TIMER0_OVF vector (SimpleInterruptUnit maps it here)
    rjmp timer0_isr

; -------------------------
; Main Code
; -------------------------
.org 0x0030
reset:
    ldi r16, 0xFF
    out SPL, r16
    ldi r16, 0x08
    out SPH, r16

; Initialize test tracking variables
    ldi r16, 1
    sts test_case, r16     ; test_case = 1
    ldi r16, 0
    sts final_result, r16  ; Start with final_result = 0
    ldi r16, 0
    sts isr_flag, r16

; 1. Arm the Timer0 overflow interrupt to wake us from sleep
    ldi r16, 0xFE
    sts TCNT0, r16          ; overflow in ~2 cycles
    ldi r16, 0x01
    sts TIMSK0, r16         ; enable Timer0 overflow interrupt
    sts TCCR0B, r16         ; start timer, prescaler = 1

    sei                     ; Enable global interrupts

; 2. Perform the SLEEP instruction
    sleep
; The CPU will halt here until the Timer0 overflow interrupt fires.
; Execution continues immediately following the SLEEP instruction,
; once the ISR has run and RETI has returned.

; 3. Verify we actually woke up via the ISR (not just fell through)
    lds r16, isr_flag
    cpi r16, 0xAA
    brne fail

    cli
    ldi r16, 0
    sts TCCR0B, r16         ; stop the timer
    rjmp success

; ============================================================
; Timer0 Overflow Interrupt Service Routine
; ============================================================
timer0_isr:
    push r16
    ldi r16, 0xAA
    sts isr_flag, r16       ; Set flag in SRAM so main code can confirm wake
    ldi r16, 1
    sts TIFR0, r16          ; clear TOV0 so it doesn't refire
    pop r16
    reti

; ============================================================
; SUCCESS / FAILURE logic
; ============================================================
success:
; If we reach here, we successfully entered and exited sleep
    ldi r16, 1
    sts final_result, r16     ; final_result = 1
end:
    rjmp end

fail:
    ldi r16, 255
    sts final_result, r16
    rjmp end