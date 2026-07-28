; Timer0, Normal mode (TOP=0xFF, unrelated to OCR0A). OCR0A is
; set far from the wrap point (5) with OCIE0A=1 but no prescaler
; started yet -- TCNT0 is manually walked across a real overflow
; (0xFF -> 0x00) via CS=001 while OCR0A stays at 5 (never equal
; to TCNT0 during the wrap itself). Confirms OCF0A is NOT forced
; by the overflow event alone (a real bug found and fixed in
; Other_modes_Increment() while writing this test -- see that
; method's comment in Timers.py: it used to set OCF0A
; unconditionally on every TOP-wrap, regardless of OCR0A).
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
    ldi r16, 0x00        ; Normal mode
    sts TCCR0A, r16
    ldi r16, 0xFD        ; two ticks from wrapping
    sts TCNT0, r16
    ldi r16, 0x01        ; CS02:00=001 (no prescale) -- starts the clock
    sts TCCR0B, r16
    ldi r16, 0x01        ; TOIE0=1 only -- OCIE0A left OFF here so we can
    sts TIMSK0, r16      ; isolate "does the wrap alone set OCF0A" from
                         ; "did we just get a real, coincidental match"

    ldi r18, 0
poll_wrap:
    lds r17, TIFR0
    sbrc r17, 0
    rjmp wrapped
    inc r18
    cpi r18, 250
    brne poll_wrap
    rjmp fail
wrapped:
    rcall inc_case

    ; TOV0 fired as expected; OCF0A must NOT have (OCR0A=5, TCNT0 just
    ; wrapped to 0 and hasn't reached 5 yet this pass).
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
