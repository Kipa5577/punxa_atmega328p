; Writing PORTB must not disturb PORTC/PORTD (or their DDR/PIN), and
; vice versa -- three ports sharing one GPIO component's clock() is
; exactly the kind of thing a copy-paste bug across the PORTB/C/D
; branches could silently break.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
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

    ; establish known baseline on C and D
    ldi r16, 0x33
    sts DDRC, r16
    ldi r16, 0x44
    sts PORTC, r16
    ldi r16, 0x55
    sts DDRD, r16
    ldi r16, 0x66
    sts PORTD, r16

    ; now hammer B
    ldi r16, 0xFF
    sts DDRB, r16
    ldi r16, 0xFF
    sts PORTB, r16
    ldi r16, 0x00
    sts DDRB, r16
    ldi r16, 0x00
    sts PORTB, r16

    ; confirm C/D untouched
    lds r17, DDRC
    cpi r17, 0x33
    brne fail
    lds r17, PORTC
    cpi r17, 0x44
    brne fail
    lds r17, DDRD
    cpi r17, 0x55
    brne fail
    lds r17, PORTD
    cpi r17, 0x66
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
