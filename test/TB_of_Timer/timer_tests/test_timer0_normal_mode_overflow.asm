; Timer0, Normal mode, no prescaling: preload TCNT0 near the top and
; confirm TOV0 (TIFR0 bit0) latches once it wraps. TOIE0 must be set
; for TOV0 to latch at all (Timers.py gates the *flag*, not just the
; interrupt, on the TIMSK enable bit -- a real-hardware deviation worth
; knowing about, but this test exercises the model as it actually
; behaves today).
.equ test_case   = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ TCCR0A = 0x44
.equ TCCR0B = 0x45
.equ TCNT0  = 0x46
.equ TIMSK0 = 0x6E
.equ TIFR0  = 0x35

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00        ; WGM01:00 = 00 -> Normal
    sts TCCR0A, r16
    ldi r16, 0x01        ; CS02:00 = 001 -> no prescaling
    sts TCCR0B, r16
    ldi r16, 0x01        ; TOIE0 = 1
    sts TIMSK0, r16
    ldi r16, 0xFE        ; two ticks from wrapping
    sts TCNT0, r16

    ldi r18, 0
poll_loop:
    lds r17, TIFR0
    sbrc r17, 0
    rjmp overflow_seen
    inc r18
    cpi r18, 255
    brne poll_loop
    rjmp fail
overflow_seen:
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
