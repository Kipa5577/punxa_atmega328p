; Timer0: confirms every register reads back its documented
; post-reset value (all zero) before any software write --
; matches this class's own __init__ initial values.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR0A = 0x44
.equ TCCR0B = 0x45
.equ TCNT0 = 0x46
.equ OCR0A = 0x47
.equ OCR0B = 0x48
.equ TIMSK0 = 0x6e
.equ TIFR0 = 0x35

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    lds r17, TCCR0A
    cpi r17, 0
    brne fail
    rcall inc_case
    lds r17, TCCR0B
    cpi r17, 0
    brne fail
    rcall inc_case
    lds r17, TCNT0
    cpi r17, 0
    brne fail
    rcall inc_case
    lds r17, OCR0A
    cpi r17, 0
    brne fail
    rcall inc_case
    lds r17, OCR0B
    cpi r17, 0
    brne fail
    rcall inc_case
    lds r17, TIMSK0
    cpi r17, 0
    brne fail
    rcall inc_case
    lds r17, TIFR0
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
