; Only bit 0 of PORTB configured as output and driven high; the rest of
; DDRB stays 0 (input). Confirm PINB reads exactly 0x01 -- if the output
; drive or the DDR masking were wrong, other bits (or bit 0 itself via
; the wrong path) would leak into the read.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ DDRB  = 0x24
.equ PORTB = 0x25
.equ PINB  = 0x23

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x01        ; DDB0 = output, rest input
    sts DDRB, r16
    ldi r16, 0x01        ; PORTB0 = 1
    sts PORTB, r16

    lds r17, PINB
    cpi r17, 0x01
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
