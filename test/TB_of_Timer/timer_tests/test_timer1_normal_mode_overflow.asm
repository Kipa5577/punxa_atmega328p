; Timer1 (16-bit), Normal mode, no prescaling: preload TCNT1H/L near
; 0xFFFF and confirm TOV1 (TIFR1 bit0) latches once it wraps. Same
; TOIE1-gates-the-flag caveat as Timer0's TOIE0 (see that test's
; comment) applies here via TOIE1.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR1A = 0x80
.equ TCCR1B = 0x81
.equ TCNT1L = 0x84
.equ TCNT1H = 0x85
.equ TIMSK1 = 0x6F
.equ TIFR1  = 0x36

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00        ; WGM11:10 = 00, COM1A = 00
    sts TCCR1A, r16
    ldi r16, 0x01        ; WGM13:12 = 00 (Normal), CS12:10 = 001
    sts TCCR1B, r16
    ldi r16, 0x01        ; TOIE1 = 1
    sts TIMSK1, r16
    ldi r16, 0xFF
    sts TCNT1H, r16
    ldi r16, 0xFE
    sts TCNT1L, r16

    ldi r18, 0
poll_loop:
    lds r17, TIFR1
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
