; PB0 configured as output, toggled 5 times via consecutive writes to
; PORTB (in-register toggle, not PINx-write-toggles-PORTx -- that AVR
; quirk isn't implemented yet, see GPIO.py). Confirms via CPU-visible
; PINB readback after each toggle AND (post-hoc, from tb_gpio_tests.py's
; PEER_EDGE_CHECKS) via PeerGPIO's independently observed edge count on
; the physical pin -- the same two-layer check tb_timer_tests.py uses
; for OC0A/OC0B.
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

    ldi r16, 0x01
    sts DDRB, r16

    ldi r16, 0x01
    sts PORTB, r16
    lds r17, PINB
    cpi r17, 0x01
    brne fail

    ldi r16, 0x00
    sts PORTB, r16
    lds r17, PINB
    cpi r17, 0x00
    brne fail

    ldi r16, 0x01
    sts PORTB, r16
    lds r17, PINB
    cpi r17, 0x01
    brne fail

    ldi r16, 0x00
    sts PORTB, r16
    lds r17, PINB
    cpi r17, 0x00
    brne fail

    ldi r16, 0x01
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
