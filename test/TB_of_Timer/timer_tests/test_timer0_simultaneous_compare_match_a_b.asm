; Timer0, Normal mode, OCR0A=OCR0B (both 5), COM0A=COM0B=01
; (toggle). Both OCF0A and OCF0B must latch on the very same
; TCNT0==5 cycle -- confirmed by requiring both bits set the
; first time either one is seen, not by two separate polls that
; could straddle different cycles.
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
    ldi r16, 0x50        ; COM0A=01, COM0B=01
    sts TCCR0A, r16
    ldi r16, 0x01
    sts TCCR0B, r16
    ldi r16, 0x06        ; OCIE0A=1, OCIE0B=1
    sts TIMSK0, r16

    ldi r18, 0
poll:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp a_seen
    inc r18
    cpi r18, 250
    brne poll
    rjmp fail
a_seen:
    rcall inc_case
    ; the same read that showed OCF0A must also already show OCF0B,
    ; since both channels compare against the same TCNT0 value.
    sbrs r17, 2
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
