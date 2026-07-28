; Timer2, CTC mode (TOP=OCR2A). Confirms a live OCR2A update
; while the timer is running takes effect for the *next* period
; -- this model has no OCR2A double-buffering (self.OCR2A is
; read live every cycle by update_wave_gen_mode()'s TOP
; assignment and by handle_CTC_mode()'s match check), so moving
; the TOP value mid-run is picked up on the very next compare
; check rather than waiting for a natural BOTTOM/buffered-update
; point.
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

    ldi r16, 10
    sts OCR2A, r16
    ldi r16, 0x02        ; CTC
    sts TCCR2A, r16
    ldi r16, 0x01
    sts TCCR2B, r16
    ldi r16, 0x02        ; OCIE2A=1
    sts TIMSK2, r16

    ldi r18, 0
poll_first:
    lds r17, TIFR2
    sbrc r17, 1
    rjmp seen_first
    inc r18
    cpi r18, 250
    brne poll_first
    rjmp fail
seen_first:
    rcall inc_case

    ldi r16, 0x02
    sts TIFR2, r16
    ldi r16, 50           ; move TOP much further out mid-run
    sts OCR2A, r16
    rcall inc_case

    ldi r18, 0
poll_second:
    lds r17, TIFR2
    sbrc r17, 1
    rjmp seen_second
    inc r18
    cpi r18, 250
    brne poll_second
    rjmp fail
seen_second:
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
