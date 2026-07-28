; Timer2, Normal mode, no prescaling: preload TCNT2 near the top and
; confirm TOV2 (TIFR2 bit0) latches once it wraps. Same
; TOIE2-gates-the-flag caveat as Timer0/Timer1 applies here too.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR2A = 0xB0
.equ TCCR2B = 0xB1
.equ TCNT2  = 0xB2
.equ TIMSK2 = 0x70
.equ TIFR2  = 0x37

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00        ; WGM21:20 = 00 -> Normal
    sts TCCR2A, r16
    ldi r16, 0x01        ; CS22:20 = 001 -> no prescaling
    sts TCCR2B, r16
    ldi r16, 0x01        ; TOIE2 = 1
    sts TIMSK2, r16
    ldi r16, 0xFE
    sts TCNT2, r16

    ldi r18, 0
poll_loop:
    lds r17, TIFR2
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
