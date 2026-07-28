; DDRB/DDRC/DDRD write + read-back, including the DDRD bit that was
; previously unreachable dead code (see GPIO.py's class docstring).
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ DDRB  = 0x24
.equ DDRC  = 0x27
.equ DDRD  = 0x2A

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0xAA
    sts DDRB, r16
    lds r17, DDRB
    cp r17, r16
    brne fail
    rcall inc_case

    ldi r16, 0x55
    sts DDRC, r16
    lds r17, DDRC
    cp r17, r16
    brne fail
    rcall inc_case

    ; DDRD specifically -- this write was silently dropped before the
    ; GPIO.py fix (impossible instype==0 AND instype==1 condition).
    ldi r16, 0xF0
    sts DDRD, r16
    lds r17, DDRD
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
