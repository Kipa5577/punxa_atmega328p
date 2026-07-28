; Timer2, Normal mode, COM2B=11 (set, bits5:4). Same FOC strobe
; proof as force_output_compare_a.asm, for the B channel.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR2A = 0xb0
.equ TCCR2B = 0xb1
.equ TCNT2 = 0xb2
.equ OCR2A = 0xb3
.equ OCR2B = 0xb4
.equ TIMSK2 = 0x70
.equ TIFR2 = 0x37

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x30        ; COM2B=11 (bits5:4), COM2A=00, WGM21:20=00
    sts TCCR2A, r16
    ldi r16, 0x80
    sts TCNT2, r16
    ldi r16, 0x04        ; OCIE2B=1
    sts TIMSK2, r16
    ldi r16, 0x40        ; FOC2B=1 (bit6), CS22:20=000 (clock off)
    sts TCCR2B, r16

    ldi r18, 0
settle_loop:
    nop
    inc r18
    cpi r18, 40
    brne settle_loop
    rcall inc_case

    lds r17, TIFR2
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
