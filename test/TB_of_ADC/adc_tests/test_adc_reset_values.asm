; ADMUX/ADCSRA/ADCSRB/ADCL/ADCH/DIDR0 should all read 0 immediately
; after reset, before any code touches them.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ ADCL   = 0x78
.equ ADCH   = 0x79
.equ ADCSRA = 0x7A
.equ ADCSRB = 0x7B
.equ ADMUX  = 0x7C
.equ DIDR0  = 0x7E

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    lds r17, ADMUX
    cpi r17, 0
    brne fail
    lds r17, ADCSRA
    cpi r17, 0
    brne fail
    lds r17, ADCSRB
    cpi r17, 0
    brne fail
    lds r17, ADCL
    cpi r17, 0
    brne fail
    lds r17, ADCH
    cpi r17, 0
    brne fail
    lds r17, DIDR0
    cpi r17, 0
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
