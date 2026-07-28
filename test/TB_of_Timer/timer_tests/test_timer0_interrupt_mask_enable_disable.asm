; Timer0, CTC mode. Documents this model's known deviation from
; real hardware (see HANDOFF.md / existing overflow tests'
; comments): OCIE0A/TOIE0 gate the *flag itself*, not just the
; interrupt request. So with OCIE0A=0, a real compare match must
; NOT set OCF0A at all; only after OCIE0A is enabled does the
; *next* match set it.
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

    ldi r16, 5
    sts OCR0A, r16
    ldi r16, 0x02        ; WGM01:00=10 (CTC)
    sts TCCR0A, r16
    ldi r16, 0x01        ; CS=001
    sts TCCR0B, r16
    ldi r16, 0x00        ; OCIE0A=0 (masked)
    sts TIMSK0, r16

    ldi r18, 0
mask_wait:
    nop
    nop
    inc r18
    cpi r18, 60
    brne mask_wait
    rcall inc_case

    ; Several matches have occurred by now (OCR0A=5, no prescale) --
    ; OCF0A must still read 0 with the mask disabled.
    lds r17, TIFR0
    sbrc r17, 1
    rjmp fail
    rcall inc_case

    ; Enable the mask; the next match must set OCF0A.
    ldi r16, 0x02
    sts TIMSK0, r16
    ldi r18, 0
poll_enabled:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp seen
    inc r18
    cpi r18, 250
    brne poll_enabled
    rjmp fail
seen:
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
