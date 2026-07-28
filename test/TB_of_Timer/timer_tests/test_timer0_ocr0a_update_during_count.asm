; Timer0, Normal mode, OCIE0A=1. Confirms a live OCR0A update
; while TCNT0 is actively counting takes effect for the *next*
; match target -- this model has no OCR0A double-buffering at
; all (Memory_access stores directly to self.OCR0A, read live by
; the per-cycle compare in handle_normal_mode()), so this is a
; straightforward correctness check on that live-read behavior,
; not a test of real hardware's PWM-mode buffering (which this
; project doesn't implement for any mode).
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

    ldi r16, 10
    sts OCR0A, r16
    ldi r16, 0x00
    sts TCCR0A, r16
    ldi r16, 0x01        ; CS=001
    sts TCCR0B, r16
    ldi r16, 0x02        ; OCIE0A=1
    sts TIMSK0, r16

    ldi r18, 0
poll_first:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp seen_first
    inc r18
    cpi r18, 250
    brne poll_first
    rjmp fail
seen_first:
    rcall inc_case

    ; Clear the flag, then move the target further out while TCNT0
    ; keeps counting (it's well past 10 by now).
    ldi r16, 0x02
    sts TIFR0, r16
    lds r17, TCNT0
    subi r17, -20         ; r17 = TCNT0 + 20 (a reachable near target)
    sts OCR0A, r17
    rcall inc_case

    ldi r18, 0
poll_second:
    lds r17, TIFR0
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
