; ADATE=1, ADTS=000 (free running): started once via ADSC, should keep
; reconverting automatically with no further register writes. Confirms
; two successive completions without ever re-writing ADSC.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ ADCSRA = 0x7A
.equ ADCSRB = 0x7B
.equ ADMUX  = 0x7C

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
    ldi r16, 0x00              ; ADTS=000 (free running)
    sts ADCSRB, r16
    ldi r16, 0xEF               ; ADEN=1 ADSC=1 ADATE=1 ADPS=111
    sts ADCSRA, r16

    rcall wait_adif
    lds r16, ADCSRA
    ori r16, 0x10               ; clear ADIF (write-1-to-clear) without
    sts ADCSRA, r16              ; disturbing ADEN/ADSC/ADATE/ADPS
    lds r17, ADCSRA
    sbrs r17, 6                  ; ADSC must still read 1 -- free running
    rjmp fail                    ; never stops on its own
    rcall inc_case

    rcall wait_adif               ; second completion, no ADSC rewrite
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
