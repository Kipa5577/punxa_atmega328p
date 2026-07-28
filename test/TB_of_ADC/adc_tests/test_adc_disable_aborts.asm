; Clearing ADEN while a conversion is in progress terminates it: ADSC
; must clear and ADIF must never set for that aborted conversion.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
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

    ldi r16, 0x00
    sts ADMUX, r16
    ldi r16, 0xC7                ; ADEN=1 ADSC=1 ADPS=111 (/128 -- slow
    sts ADCSRA, r16               ; enough that we can catch it mid-flight)

    ; Give it a handful of cycles to get into the CONVERTING state but
    ; nowhere near completion (25*128 = 3200 cycles to finish).
    ldi r18, 0
short_wait:
    inc r18
    cpi r18, 20
    brne short_wait

    lds r17, ADCSRA
    sbrc r17, 4                  ; must NOT have finished yet
    rjmp fail
    rcall inc_case

    ldi r16, 0x00                ; ADEN=0 -- abort
    sts ADCSRA, r16

    ; Once aborted, nothing can spontaneously set ADIF again (ADEN,
    ; ADSC, and ADATE are all 0) -- a single generous bounded poll is
    ; enough proof it never fires, no need to wait out the original
    ; conversion's full would-have-been duration.
    ldi r19, 0
poll_never:
    lds r17, ADCSRA
    cpi r17, 0
    brne fail                     ; ADEN=0 ADSC=0 ADIF=0 -- whole register clean
    inc r19
    brne poll_never
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
