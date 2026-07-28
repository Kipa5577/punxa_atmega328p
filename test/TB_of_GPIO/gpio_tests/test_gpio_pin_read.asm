; Configure PORTB fully as input (DDRB=0), peer drives 0x5A onto all 8
; pins (see TEST_PEER_KWARGS in tb_gpio_tests.py). PINB should read back
; exactly what the peer is driving -- a genuine pin-level check, since
; nothing in this program ever writes 0x5A anywhere itself.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ DDRB  = 0x24
.equ PINB  = 0x23

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00        ; PORTB all input
    sts DDRB, r16

    lds r17, PINB
    cpi r17, 0x5A
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
