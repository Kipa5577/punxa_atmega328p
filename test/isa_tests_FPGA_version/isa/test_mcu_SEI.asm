; ============================================================
; SEI (Set Global Interrupt Flag) test suite
; ============================================================
; Tests that SEI correctly:
; 1. Enables global interrupts by setting SREG bit 7
; 2. Allows a pending interrupt to execute
;
; NOTE: the test harness (tb_ISA_tests.py) only wires up the
; TIMER0_OVF interrupt source - INT0/EIMSK have no simulated
; hardware signal in this environment, so this test uses the
; Timer0 overflow interrupt to exercise SEI instead.
; ============================================================
; SEI is a 1-word (16-bit) instruction
; Format: 1001 0100 0111 1000
; Operation: I <- 1
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

; ============================================================
; INTERRUPT VECTOR TABLE
; ============================================================
.org 0x0000
    rjmp reset

; SimpleInterruptUnit maps TIMER0_OVF to JUMPto = 0x020
.org 0x0020
    rjmp timer0_isr

; ============================================================
; INITIALIZATION (placed safely after the vector table)
; ============================================================
.org 0x0030
reset:
    ldi r16, 0xFF
    out SPL, r16
    ldi r16, 0x08
    out SPH, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    cli                 ; Ensure interrupts are disabled at start
    ldi r16, 0
    sts isr_flag, r16

; ============================================================
; TEST 1: SEI enables interrupts
; ============================================================
test1_start:
    ; Arm the timer so it will overflow shortly, but interrupts
    ; are still globally disabled (I=0) at this point.
    ldi r16, 0xFE
    sts TCNT0, r16      ; overflow in ~2 cycles
    ldi r16, 0x01
    sts TIMSK0, r16     ; enable Timer0 overflow interrupt
    sts TCCR0B, r16     ; start timer, prescaler = 1

    ; At this point, I-bit is 0. The interrupt condition can become
    ; pending, but must NOT be serviced until SEI runs.
    sei
    ; If SEI works, the CPU should take the pending interrupt at
    ; the next instruction boundary and jump to the ISR below.

wait_isr:
    lds r16, isr_flag
    cpi r16, 0xAA
    brne wait_isr       ; spins briefly until the ISR sets the flag

    cli
    ldi r16, 0
    sts TCCR0B, r16     ; stop the timer
    rcall inc_case
    rjmp success

; ============================================================
; Timer0 Overflow Interrupt Service Routine
; ============================================================
timer0_isr:
    push r16
    ldi r16, 0xAA
    sts isr_flag, r16   ; Set flag in SRAM

    ldi r16, 1
    sts TIFR0, r16      ; clear TOV0 so it doesn't refire
    pop r16
    reti

; ============================================================
; SUCCESS / FAILURE logic
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end

fail:
    ldi r16, 255
    sts final_result, r16
    rjmp end

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret