; Timer0, Normal mode, COM0A=00 (disconnected). OCF0A must still
; latch on compare match even though the pin never moves --
; interrupt-flag path and pin-output path are logically separate
; in Timers.py (pin routing gated by COM0A, OCF0A latch is not).
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
    ldi r16, 0x0
    sts TCCR0A, r16
    ldi r16, 0x1        ; CS=001 no prescale (+ WGM02 bit if any)
    sts TCCR0B, r16
    ldi r16, 0x02        ; OCIE0A=1
    sts TIMSK0, r16

    ldi r18, 0
poll_loop1:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp seen1
    inc r18
    cpi r18, 250
    brne poll_loop1
    rjmp fail
seen1:
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
