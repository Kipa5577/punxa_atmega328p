; PORTB/PORTC/PORTD write + read-back (data register, independent of DDR).
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ PORTB = 0x25
.equ PORTC = 0x28
.equ PORTD = 0x2B

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x3C
    sts PORTB, r16
    lds r17, PORTB
    cp r17, r16
    brne fail
    rcall inc_case

    ldi r16, 0xC3
    sts PORTC, r16
    lds r17, PORTC
    cp r17, r16
    brne fail
    rcall inc_case

    ldi r16, 0x0F
    sts PORTD, r16
    lds r17, PORTD
    cp r17, r16
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
