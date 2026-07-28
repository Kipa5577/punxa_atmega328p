; Single-conversion mode, channel 0. Peer drives 0x2AA (682/1023) onto
; ADC0 (see TEST_PEER_KWARGS in tb_adc_tests.py). Enable the ADC and
; start a conversion in one write, poll ADIF, then read ADCL before
; ADCH (the correct order) and reconstruct the 10-bit result.
;
; ADPS2:0 = 011 (/8 prescaler) keeps the wait bounded and fast for a
; test while still exercising a real multi-cycle conversion (25 ADC
; clocks for this first conversion * 8 = 200 system-clock cycles).
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ ADCL   = 0x78
.equ ADCH   = 0x79
.equ ADCSRA = 0x7A
.equ ADMUX  = 0x7C

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00          ; REFS=00, ADLAR=0, MUX=0000 (ADC0)
    sts ADMUX, r16

    ldi r16, 0xC3           ; ADEN=1 ADSC=1 ADATE=0 ADIF=0 ADIE=0 ADPS=011
    sts ADCSRA, r16

    ldi r18, 0
poll_loop:
    lds r17, ADCSRA
    sbrc r17, 4              ; ADIF
    rjmp conv_done
    inc r18
    cpi r18, 255
    brne poll_loop
    rjmp fail

conv_done:
    lds r20, ADCL            ; low byte first (real read order)
    lds r21, ADCH
    ; result = (r21<<8) | r20 -- compare against 0x2AA (682) as two bytes
    cpi r20, 0xAA
    brne fail
    cpi r21, 0x02
    brne fail
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
