; Timer0, CTC mode: confirm OCF0A (1) latches on a real match,
; (2) clears via the standard write-1-to-clear idiom without
; disturbing TOV0, and (3) can set again on the *next* match
; after being cleared (proves the clear didn't leave it stuck).
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

    ldi r16, 200
    sts OCR0A, r16
    ldi r16, 0x02        ; WGM01:00=10 (CTC)
    sts TCCR0A, r16
    ldi r16, 0x01        ; CS=001
    sts TCCR0B, r16
    ldi r16, 0x02        ; OCIE0A=1
    sts TIMSK0, r16

    ldi r18, 0
poll_1:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp seen_1
    inc r18
    cpi r18, 250
    brne poll_1
    rjmp fail
seen_1:
    rcall inc_case

    ; Clear only OCF0A (bit1); TOV0 (bit0) must be unaffected by this.
    ldi r16, 0x02
    sts TIFR0, r16
    lds r17, TIFR0
    sbrc r17, 1
    rjmp fail
    rcall inc_case

    ; Confirm it can set again on a later match (not stuck cleared).
    ldi r18, 0
poll_2:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp seen_2
    inc r18
    cpi r18, 250
    brne poll_2
    rjmp fail
seen_2:
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
