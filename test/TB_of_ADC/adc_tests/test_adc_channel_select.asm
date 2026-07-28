; MUX selection: convert channel 0 (peer=0x100), channel 3 (peer=0x300),
; channel 7 (peer=0x3FF) in sequence, confirming each selects the right
; physical input rather than a stale/adjacent one.
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

    ; --- channel 0: expect 0x100 (256) ---
    ldi r16, 0x00
    sts ADMUX, r16
    ldi r16, 0xC7            ; ADEN=1 ADSC=1 ADPS=111 (/128, fast enough)
    sts ADCSRA, r16
    rcall wait_adif
    lds r20, ADCL
    lds r21, ADCH
    cpi r20, 0x00
    brne fail
    cpi r21, 0x01
    brne fail
    ldi r16, 0x10             ; clear ADIF (write-1-to-clear)
    sts ADCSRA, r16
    rcall inc_case

    ; --- channel 3: expect 0x300 (768) ---
    ldi r16, 0x03
    sts ADMUX, r16
    ldi r16, 0xC7
    sts ADCSRA, r16
    rcall wait_adif
    lds r20, ADCL
    lds r21, ADCH
    cpi r20, 0x00
    brne fail
    cpi r21, 0x03
    brne fail
    ldi r16, 0x10
    sts ADCSRA, r16
    rcall inc_case

    ; --- channel 7: expect 0x3FF (1023, full scale) ---
    ldi r16, 0x07
    sts ADMUX, r16
    ldi r16, 0xC7
    sts ADCSRA, r16
    rcall wait_adif
    lds r20, ADCL
    lds r21, ADCH
    cpi r20, 0xFF
    brne fail
    cpi r21, 0x03
    brne fail
    rcall inc_case

    rjmp success

wait_adif:
    ldi r19, 0
wait_loop:
    lds r17, ADCSRA
    sbrc r17, 4
    ret
    inc r19
    cpi r19, 255
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
