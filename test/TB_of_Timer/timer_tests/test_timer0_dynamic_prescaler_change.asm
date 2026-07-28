; Timer0, Normal mode. CS02:00=000 (no clock source) must hold
; TCNT0 completely still; switching to CS02:00=001 must start it
; advancing immediately -- a direct test of update_prescaler()'s
; CS-change detection (self.prevCS tracking) taking effect on the
; very next register write, not needing a restart.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR0A = 0x44
.equ TCCR0B = 0x45
.equ TCNT0 = 0x46
.equ OCR0A = 0x47
.equ OCR0B = 0x48
.equ TIMSK0 = 0x6e
.equ TIFR0 = 0x35

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00        ; Normal mode
    sts TCCR0A, r16
    ldi r16, 0
    sts TCNT0, r16
    ldi r16, 0x00        ; CS=000 (no clock source)
    sts TCCR0B, r16

    ldi r18, 0
idle_wait:
    nop
    nop
    inc r18
    cpi r18, 60
    brne idle_wait
    rcall inc_case

    lds r17, TCNT0
    cpi r17, 0
    brne fail             ; must not have moved with no clock source
    rcall inc_case

    ldi r16, 0x01         ; CS=001 -> clock now running
    sts TCCR0B, r16
    ldi r18, 0
run_wait:
    nop
    nop
    inc r18
    cpi r18, 60
    brne run_wait
    rcall inc_case

    lds r17, TCNT0
    cpi r17, 0
    breq fail             ; must have advanced now
    rcall inc_case

    rjmp success

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
