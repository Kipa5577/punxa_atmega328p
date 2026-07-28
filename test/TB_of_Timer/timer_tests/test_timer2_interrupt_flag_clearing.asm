; Timer2, CTC mode, OCR2A=200 (long period vs. the few
; instructions needed to clear+verify). Confirms OCF2A latches,
; clears via write-1-to-clear, and can set again on a later
; match.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR2A = 0xb0
.equ TCCR2B = 0xb1
.equ TCNT2 = 0xb2
.equ OCR2A = 0xb3
.equ OCR2B = 0xb4
.equ TIMSK2 = 0x70
.equ TIFR2 = 0x37

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 200
    sts OCR2A, r16
    ldi r16, 0x02        ; CTC
    sts TCCR2A, r16
    ldi r16, 0x01
    sts TCCR2B, r16
    ldi r16, 0x02
    sts TIMSK2, r16

    ldi r18, 0
poll_1:
    lds r17, TIFR2
    sbrc r17, 1
    rjmp seen_1
    inc r18
    cpi r18, 250
    brne poll_1
    rjmp fail
seen_1:
    rcall inc_case

    ldi r16, 0x02
    sts TIFR2, r16
    lds r17, TIFR2
    sbrc r17, 1
    rjmp fail
    rcall inc_case

    ldi r18, 0
poll_2:
    lds r17, TIFR2
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
