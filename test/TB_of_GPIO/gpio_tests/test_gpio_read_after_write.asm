; Every register this component owns (GPIOR0-2, PORTx/DDRx for B/C/D)
; read back exactly what was last written, in one pass -- a broad
; regression net for the resp-polarity / missing-resp.prepare bugs
; fixed in GPIO.py (a wrong resp there would have hung this test, not
; just returned a wrong value, so reaching 'end' at all is already part
; of the check).
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ GPIOR0 = 0x3E
.equ GPIOR1 = 0x4A
.equ GPIOR2 = 0x4B
.equ DDRB  = 0x24
.equ PORTB = 0x25
.equ DDRC  = 0x27
.equ PORTC = 0x28
.equ DDRD  = 0x2A
.equ PORTD = 0x2B

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x11
    sts GPIOR0, r16
    lds r17, GPIOR0
    cp r17, r16
    brne fail_t1
    rcall inc_case

    ldi r16, 0x22
    sts GPIOR1, r16
    lds r17, GPIOR1
    cp r17, r16
    brne fail_t2
    rcall inc_case

    ldi r16, 0x33
    sts GPIOR2, r16
    lds r17, GPIOR2
    cp r17, r16
    brne fail_t3
    rcall inc_case

    ldi r16, 0xA1
    sts DDRB, r16
    lds r17, DDRB
    cp r17, r16
    brne fail_t4
    ldi r16, 0xA2
    sts PORTB, r16
    lds r17, PORTB
    cp r17, r16
    brne fail_t5
    rcall inc_case

    ldi r16, 0xB1
    sts DDRC, r16
    lds r17, DDRC
    cp r17, r16
    brne fail_t6
    ldi r16, 0xB2
    sts PORTC, r16
    lds r17, PORTC
    cp r17, r16
    brne fail_t7
    rcall inc_case

    ldi r16, 0xC1
    sts DDRD, r16
    lds r17, DDRD
    cp r17, r16
    brne fail_t8
    ldi r16, 0xC2
    sts PORTD, r16
    lds r17, PORTD
    cp r17, r16
    brne fail_t9
    rcall inc_case

    rjmp success

fail_t1: jmp fail
fail_t2: jmp fail
fail_t3: jmp fail
fail_t4: jmp fail
fail_t5: jmp fail
fail_t6: jmp fail
fail_t7: jmp fail
fail_t8: jmp fail
fail_t9: jmp fail
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
