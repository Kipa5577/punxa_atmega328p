; Timer0, Normal mode, COM0B=11 (set). Same FOC strobe proof as
; force_output_compare_a.asm, for the B channel (FOC0B = TCCR0B
; bit6).
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

    ldi r16, 0x30        ; COM0B=11 (set, bits5:4), COM0A=00, WGM01:00=00
    sts TCCR0A, r16
    ldi r16, 0x80
    sts TCNT0, r16
    ldi r16, 0x04        ; OCIE0B=1
    sts TIMSK0, r16
    ldi r16, 0x40        ; FOC0B=1 (bit6), CS02:00=000 (clock off, same
    sts TCCR0B, r16      ; no-coincidental-match rationale as force_a)

    ldi r18, 0
settle_loop:
    nop
    inc r18
    cpi r18, 40
    brne settle_loop
    rcall inc_case

    lds r17, TIFR0
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
