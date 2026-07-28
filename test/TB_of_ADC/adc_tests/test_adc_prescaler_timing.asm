; Confirms the first conversion after ADEN (25 ADC clocks) genuinely
; takes longer than a subsequent one (13 ADC clocks) -- a relative
; comparison (poll-iteration count), robust to exact instruction-timing
; details rather than asserting a specific cycle number.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ ADCSRA = 0x7A
.equ ADMUX  = 0x7C
.equ iter1  = 0x0102
.equ iter2  = 0x0103

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00
    sts ADMUX, r16

    ldi r16, 0xC5              ; ADEN=1 ADSC=1 ADPS=101 (/32)
    sts ADCSRA, r16
    rcall count_wait
    sts iter1, r18
    lds r16, ADCSRA
    ori r16, 0x10
    sts ADCSRA, r16
    rcall inc_case

    ldi r16, 0xC5               ; second conversion, same prescaler
    sts ADCSRA, r16
    rcall count_wait
    sts iter2, r18
    rcall inc_case

    lds r20, iter1
    lds r21, iter2
    cp r20, r21
    brlo fail                   ; iter1 must be >= iter2 (first is longer)
    breq fail                   ; and strictly greater, not equal
    rcall inc_case

    rjmp success

count_wait:
    ldi r18, 0
wait_loop:
    lds r17, ADCSRA
    sbrc r17, 4
    ret
    inc r18
    brne wait_loop
    rjmp fail

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
