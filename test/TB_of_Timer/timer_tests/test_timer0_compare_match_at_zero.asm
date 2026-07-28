; Timer0, CTC mode, OCR0A=0 -- TOP=BOTTOM=0, the degenerate case
; where every single tick is simultaneously a compare match. Just
; confirms OCF0A latches promptly and repeatedly rather than the
; TOP=0 edge case hanging or never matching.
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

    ldi r16, 0
    sts OCR0A, r16
    ldi r16, 0x02        ; CTC
    sts TCCR0A, r16
    ldi r16, 0x01
    sts TCCR0B, r16
    ldi r16, 0x02
    sts TIMSK0, r16

    ldi r18, 0
poll_1:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp seen_1
    inc r18
    cpi r18, 250
    brne poll_1
    rjmp fail
seen_1:
    rcall inc_case

    ldi r16, 0x02
    sts TIFR0, r16
    ldi r18, 0
poll_2:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp seen_2
    inc r18
    cpi r18, 250
    brne poll_2
    rjmp fail
seen_2:
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
