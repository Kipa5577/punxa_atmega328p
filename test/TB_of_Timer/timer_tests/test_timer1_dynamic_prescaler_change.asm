; Timer1, Normal mode. CS12:10=000 must hold TCNT1 still;
; switching to CS=001 must start it advancing immediately.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR1A = 0x80
.equ TCCR1B = 0x81
.equ TCCR1C = 0x82
.equ TCNT1L = 0x84
.equ TCNT1H = 0x85
.equ ICR1L = 0x86
.equ ICR1H = 0x87
.equ OCR1AL = 0x88
.equ OCR1AH = 0x89
.equ OCR1BL = 0x8a
.equ OCR1BH = 0x8b
.equ TIMSK1 = 0x6f
.equ TIFR1 = 0x36

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00
    sts TCCR1A, r16
    ldi r16, 0
    sts TCNT1H, r16
    sts TCNT1L, r16
    ldi r16, 0x00        ; CS=000 (no clock source)
    sts TCCR1B, r16

    ldi r18, 0
idle_wait:
    nop
    nop
    inc r18
    cpi r18, 60
    brne idle_wait
    rcall inc_case

    lds r17, TCNT1L
    cpi r17, 0
    brne fail
    lds r17, TCNT1H
    cpi r17, 0
    brne fail
    rcall inc_case

    ldi r16, 0x01         ; CS=001 -> running
    sts TCCR1B, r16
    ldi r18, 0
run_wait:
    nop
    nop
    inc r18
    cpi r18, 60
    brne run_wait
    rcall inc_case

    lds r17, TCNT1L
    cpi r17, 0
    breq check_high
    rjmp advanced
check_high:
    lds r17, TCNT1H
    cpi r17, 0
    breq fail
advanced:
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
