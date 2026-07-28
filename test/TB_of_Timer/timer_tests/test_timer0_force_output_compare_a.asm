; Timer0, Normal mode, COM0A=11 (set). OCR0A left at reset value 0,
; TCNT0 starts at 0x80 so a real compare match cannot occur during
; the test window. FOC0A (TCCR0B bit7) is written together with
; CS02:00 in a single sts -- forces OC0A high immediately (checked
; via PEER_PIN_CHECKS) without ever setting OCF0A.
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

    ldi r16, 0xC0        ; COM0A=11 (set), WGM01:00=00 (Normal)
    sts TCCR0A, r16
    ldi r16, 0x80
    sts TCNT0, r16
    ldi r16, 0x02        ; OCIE0A=1 (so we can prove FOC doesn't set it)
    sts TIMSK0, r16
    ldi r16, 0x80        ; FOC0A=1 (bit7), CS02:00=000 (clock left OFF
    sts TCCR0B, r16      ; entirely so TCNT0 can never coincidentally
                         ; wrap around to match OCR0A=0 during the test)

    ldi r18, 0
settle_loop:
    nop
    inc r18
    cpi r18, 40
    brne settle_loop
    rcall inc_case

    ; FOC0A must not have set OCF0A (no real match occurred: OCR0A=0,
    ; TCNT0 started at 0x80 and has only advanced a few counts).
    lds r17, TIFR0
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
