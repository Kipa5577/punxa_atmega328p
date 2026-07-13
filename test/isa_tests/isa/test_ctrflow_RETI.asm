; ============================================================
; HARDWARE RETI (Return from Interrupt) test suite
; Adapted for SimpleTimer and SimpleInterruptUnit
; ============================================================

; Memory Mapped Registers for Timer0 (Absolute Addresses on Bus)
.equ TCCR0B = 0x45
.equ TCNT0  = 0x46
.equ TIMSK0 = 0x8E
.equ TIFR0 = 0x47
; Standard Constants
.equ test_case = 0x0100
.equ final_result = 0x0101
.equ isr_flag = 0x0102       ; Flag to tell main loop the ISR fired
.equ stack_start = 0x08FF
.equ SREG_ADDR = 0x5F
.equ SPH = 0x3E
.equ SPL = 0x3D

; ============================================================
; INTERRUPT VECTOR TABLE
; ============================================================
.org 0x0000
    rjmp reset

; SimpleInterruptUnit maps TIMER0_OVF to JUMPto = 0x020
.org 0x0020
    rjmp timer0_isr_dispatcher

; ============================================================
; INITIALIZATION
; ============================================================
.org 0x0030
reset:
    ; Init stack[cite: 1]
    ldi r16, 0x03
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

; ============================================================
; TEST 1: Simple RETI from Hardware Timer Interrupt
; ============================================================
test1:
    cli
    ; Reset ISR Flag
    ldi r16, 0
    sts isr_flag, r16

    ; Configure Timer to overflow in exactly 2 cycles
    ldi r16, 0xFE
    sts TCNT0, r16
    
    ; Enable Timer0 OVF Interrupt
    ldi r16, 0x01
    sts TIMSK0, r16
    
    ; Start Timer (Prescaler = 1)
    ldi r16, 0x01
    sts TCCR0B, r16

    sei                     ; Enable Global Interrupts

wait1:
    lds r16, isr_flag
    cpi r16, 1
    brne wait1              ; CPU spins here until Hardware Interrupt fires!

    ; Test Passed! Stop Timer.
    cli
    ldi r16, 0
    sts TCCR0B, r16
    rcall inc_case
    rjmp test2

test1_fail: 
    rjmp fail

; ============================================================
; TEST 2: RETI re-enables interrupts (sets I flag automatically)
; ============================================================
test2:
    cli
    ldi r16, 0
    sts isr_flag, r16

    ldi r16, 0xFE
    sts TCNT0, r16
    ldi r16, 0x01
    sts TIMSK0, r16
    sts TCCR0B, r16
    sei

wait2:
    lds r16, isr_flag
    cpi r16, 1
    brne wait2

    ; The ISR returned. RETI should have re-enabled the I flag[cite: 1].
    brbs 7, test2_passed
    rjmp test2_fail

test2_passed:
    cli
    ldi r16, 0
    sts TCCR0B, r16
    rcall inc_case
    rjmp test3

test2_fail: 
    rjmp fail

; ============================================================
; TEST 3: Verify stack pointer behavior with hardware interrupt
; ============================================================
test3:
    cli
    ldi r16, 0
    sts isr_flag, r16

    ; Record SP before interrupt[cite: 1]
    in r19, SPL
    in r20, SPH

    ldi r16, 0xFE
    sts TCNT0, r16
    ldi r16, 0x01
    sts TIMSK0, r16
    sts TCCR0B, r16
    sei

wait3:
    lds r16, isr_flag
    cpi r16, 1
    brne wait3

    ; Check if SP restored perfectly after RETI[cite: 1]
    in r21, SPL
    in r22, SPH
    cp r19, r21
    brne test3_fail
    cp r20, r22
    brne test3_fail

    cli
    ldi r16, 0
    sts TCCR0B, r16
    rcall inc_case
    rjmp test4

test3_fail: 
    rjmp fail

; ============================================================
; TEST 4: RETI preserves all other flags[cite: 1]
; ============================================================
test4:
    cli
    ldi r16, 0
    sts isr_flag, r16

    ldi r16, 0xFE
    sts TCNT0, r16
    ldi r16, 0x01
    sts TIMSK0, r16
    sts TCCR0B, r16

    ; Set all flags[cite: 1]
    sec
    sez
    sen
    sev
    seh
    set
    
    sei

wait4:
    lds r16, isr_flag
    cpi r16, 1
    brne wait4

    ; Verify flags were untouched by the jump/return sequence[cite: 1]
    brcc test4_fail      ; C should be 1[cite: 1]
    brne test4_fail      ; Z should be 1[cite: 1]
    brpl test4_fail      ; N should be 1[cite: 1]
    brvc test4_fail      ; V should be 1[cite: 1]
    brhc test4_fail      ; H should be 1[cite: 1]
    brtc test4_fail      ; T should be 1[cite: 1]

    cli
    ldi r16, 0
    sts TCCR0B, r16
    rcall inc_case
    rjmp success

test4_fail: 
    rjmp fail

; ============================================================
; MASTER ISR DISPATCHER
; ============================================================
timer0_isr_dispatcher:
    push r27
    lds r27, test_case

    cpi r27, 1
    breq isr_general
    cpi r27, 2
    breq isr_general
    cpi r27, 3
    breq isr_general
    cpi r27, 4
    breq isr_general

isr_general:
    ; Flag that the ISR executed successfully
    ldi r27, 1
    sts isr_flag, r27
    
    ; Clear the hardware interrupt flag by writing 1 to TOV0 bit
    ; This explicitly drops the interrupt wire so it doesn't refire instantly
    ldi r27, 1
    sts TIFR0, r27 
    
    pop r27
    reti

; ============================================================
; SUCCESS / FAILURE logic[cite: 1]
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