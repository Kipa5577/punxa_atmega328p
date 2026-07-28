; ADLAR=1: result 0x2AA (682) should land as ADCH=0xAA, ADCL bits7:6=10
; (0x80), bits5:0=0.
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

    ldi r16, 0x20             ; ADLAR=1, MUX=0000
    sts ADMUX, r16
    ldi r16, 0xC7
    sts ADCSRA, r16
    rcall wait_adif
    lds r20, ADCL
    lds r21, ADCH
    cpi r21, 0xAA
    brne fail
    cpi r20, 0x80
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
