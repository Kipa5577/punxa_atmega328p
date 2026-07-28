; GPIO reset values: PORTx/DDRx should read 0 immediately after reset,
; before any code touches them. PINx (with nothing external driving and
; DDR=0 everywhere) should also read 0, since PIN[i] falls back to
; PORT[i] when floating (see GPIO.py's pull-up semantics) and PORT
; starts at 0.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ PORTB = 0x25
.equ DDRB  = 0x24
.equ PINB  = 0x23
.equ PORTC = 0x28
.equ DDRC  = 0x27
.equ PINC  = 0x26
.equ PORTD = 0x2B
.equ DDRD  = 0x2A
.equ PIND  = 0x29

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ; test 1: PORTB/DDRB/PINB all 0
    lds r17, PORTB
    cpi r17, 0
    brne fail
    lds r17, DDRB
    cpi r17, 0
    brne fail
    lds r17, PINB
    cpi r17, 0
    brne fail
    rcall inc_case

    ; test 2: PORTC/DDRC/PINC all 0
    lds r17, PORTC
    cpi r17, 0
    brne fail
    lds r17, DDRC
    cpi r17, 0
    brne fail
    lds r17, PINC
    cpi r17, 0
    brne fail
    rcall inc_case

    ; test 3: PORTD/DDRD/PIND all 0
    lds r17, PORTD
    cpi r17, 0
    brne fail
    lds r17, DDRD
    cpi r17, 0
    brne fail
    lds r17, PIND
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
