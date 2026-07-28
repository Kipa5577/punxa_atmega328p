; Timer2, Normal mode: COM2B=01 (toggle, bits5:4), COM2A=00 --
; the mirror image of output_compare_a_only.asm.
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

    ldi r16, 5
    sts OCR2A, r16
    sts OCR2B, r16
    ldi r16, 0x10        ; COM2A=00, COM2B=01 (bits5:4)
    sts TCCR2A, r16
    ldi r16, 0x01
    sts TCCR2B, r16
    ldi r16, 0x06
    sts TIMSK2, r16

    ldi r18, 0
poll_b:
    lds r17, TIFR2
    sbrc r17, 2
    rjmp seen_b
    inc r18
    cpi r18, 250
    brne poll_b
    rjmp fail
seen_b:
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
