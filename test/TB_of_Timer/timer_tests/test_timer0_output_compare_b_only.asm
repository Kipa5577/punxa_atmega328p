; Timer0, Normal mode: COM0B=01 (toggle), COM0A=00 (disconnected)
; -- the mirror image of output_compare_a_only.asm.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR0A = 0x44
.equ TCCR0B = 0x45
.equ TCNT0 = 0x46
.equ OCR0A = 0x47
.equ OCR0B = 0x48
.equ TIMSK0 = 0x6e
.equ TIFR0 = 0x35

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 5
    sts OCR0A, r16
    sts OCR0B, r16
    ldi r16, 0x10        ; COM0A=00, COM0B=01
    sts TCCR0A, r16
    ldi r16, 0x01
    sts TCCR0B, r16
    ldi r16, 0x06
    sts TIMSK0, r16

    ldi r18, 0
poll_b:
    lds r17, TIFR0
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
