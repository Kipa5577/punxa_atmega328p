; Timer1, CTC mode with TOP = OCR1A (WGM13:10 = 0100 -> WGM=4). Confirms
; OCF1A (TIFR1 bit1) latches once TCNT1 reaches OCR1A and wraps.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR1A = 0x80
.equ TCCR1B = 0x81
.equ OCR1AH = 0x89
.equ OCR1AL = 0x88
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

    ldi r16, 0
    sts OCR1AH, r16
    ldi r16, 5
    sts OCR1AL, r16
    ldi r16, 0x00
    sts TCCR1A, r16
    ldi r16, 0x09        ; WGM12 = 1 (CTC, top=OCR1A), CS12:10 = 001
    sts TCCR1B, r16
    ldi r16, 0x02        ; OCIE1A = 1
    sts TIMSK1, r16

    ldi r18, 0
poll_loop:
    lds r17, TIFR1
    sbrc r17, 1
    rjmp match_seen
    inc r18
    cpi r18, 255
    brne poll_loop
    rjmp fail
match_seen:
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
