; Timer0, Phase Correct PWM (WGM=1, TOP=0xFF), COM0A=00 (disconnected).
;
; NOTE (real model behavior found while writing this test): unlike
; handle_normal_mode()/handle_CTC_mode(), which both set OCF0A
; unconditionally on a compare match in a separate block *after* the
; COM0A if/elif chain (independent of pin routing),
; handle_Phase_Correct_PWM_mode() only sets OCF0A *inside* the
; COM0A==2/COM0A==3 branches (and the COM0A==1-with-WGM==5 toggle
; case) -- there is no such unconditional block for COM0A==0. So with
; the pin disconnected in this mode, OCF0A never latches at all, only
; TOV0 does (set at BOTTOM in Phase_Correct_PWM_Increment(),
; independent of COM0A). This test polls TOV0 instead of OCF0A for
; that reason -- a real, worth-knowing model asymmetry between modes,
; not a bug this round fixes.
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
    ldi r16, 0x01        ; COM0A=00, WGM01:00=01
    sts TCCR0A, r16
    ldi r16, 0x01        ; WGM02=0 (WGM=1), CS=001
    sts TCCR0B, r16
    ldi r16, 0x01        ; TOIE0=1 (see note below on why TOV0, not OCF0A)
    sts TIMSK0, r16

    ldi r18, 0
poll_loop1:
    lds r17, TIFR0
    sbrc r17, 0
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
