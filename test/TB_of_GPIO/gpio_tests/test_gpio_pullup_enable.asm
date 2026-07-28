; DDRB=0 (input), PORTB bit0=1 (pull-up enabled), nothing external
; driving (no peer_kwargs override -> peer defaults to fully floating,
; ext_oe=0x00). Per GPIO.py's pull-up semantics, a floating input bit
; with its PORT bit set reads back 1.
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

    ldi r16, 0x00        ; all input
    sts DDRB, r16
    ldi r16, 0x01        ; pull-up on bit 0 only
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
