; Only bit 0 configured as input (rest output, driven low), peer drives
; PB0=1 (oe mask 0x01 -- see TEST_PEER_KWARGS). Confirm PINB reads 0x01:
; bit 0 from the peer, all other (output) bits reflecting the 0 this
; program drives on them.
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

    ldi r16, 0xFE        ; DDB0 = input, DDB1..7 = output
    sts DDRB, r16
    ldi r16, 0x00        ; drive all output bits low
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
