; Timer1, Normal mode, COM1A=11 (set). OCR1A left at 0, TCNT1
; parked at 0x1000 with the clock left OFF entirely so no real
; match can occur. FOC1A (TCCR1C bit7) forces OC1A high
; immediately (PEER_PIN_CHECKS) without setting OCF1A.
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

    ldi r16, 0xC0        ; COM1A=11 (set), WGM=0 (Normal)
    sts TCCR1A, r16
    ldi r16, 0x10
    sts TCNT1H, r16
    ldi r16, 0x00
    sts TCNT1L, r16
    ldi r16, 0x02        ; OCIE1A=1 (so we can prove FOC doesn't set it)
    sts TIMSK1, r16
    ldi r16, 0x00        ; CS=000 (clock off)
    sts TCCR1B, r16
    ldi r16, 0x80        ; FOC1A=1
    sts TCCR1C, r16

    ldi r18, 0
settle_loop:
    nop
    inc r18
    cpi r18, 40
    brne settle_loop
    rcall inc_case

    lds r17, TIFR1
    sbrc r17, 1
    rjmp fail
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
