; Timer1, Normal mode, COM1B=11 (set, bits5:4). Same FOC strobe
; proof as force_output_compare_a.asm, for the B channel
; (FOC1B = TCCR1C bit6).
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

    ldi r16, 0x30        ; COM1B=11 (bits5:4), COM1A=00, WGM=0
    sts TCCR1A, r16
    ldi r16, 0x10
    sts TCNT1H, r16
    ldi r16, 0x00
    sts TCNT1L, r16
    ldi r16, 0x04        ; OCIE1B=1
    sts TIMSK1, r16
    ldi r16, 0x00        ; CS=000
    sts TCCR1B, r16
    ldi r16, 0x40        ; FOC1B=1
    sts TCCR1C, r16

    ldi r18, 0
settle_loop:
    nop
    inc r18
    cpi r18, 40
    brne settle_loop
    rcall inc_case

    lds r17, TIFR1
    sbrc r17, 2
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
