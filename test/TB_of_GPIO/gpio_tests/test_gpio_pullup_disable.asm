; DDRB=0 (input), PORTB=0 (pull-up disabled), peer floating (see
; TEST_PEER_KWARGS -- explicit floating peer, same effective state as
; no peer at all, kept explicit for clarity). A floating input with no
; pull-up should read 0, not 1.
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

    ldi r16, 0x00
    sts DDRB, r16
    ldi r16, 0x00        ; no pull-up
    sts PORTB, r16

    lds r17, PINB
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
