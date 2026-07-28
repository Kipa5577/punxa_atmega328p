; All of PORTD configured as output, driven all-0s. Confirm PIND reads 0.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ DDRD  = 0x2A
.equ PORTD = 0x2B
.equ PIND  = 0x29

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0xFF
    sts DDRD, r16
    ldi r16, 0x00
    sts PORTD, r16

    lds r17, PIND
    cpi r17, 0x00
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
