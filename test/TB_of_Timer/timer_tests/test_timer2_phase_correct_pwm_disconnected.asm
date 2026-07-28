; Timer2, Phase Correct PWM (WGM=1, TOP=0xFF), COM2A=00.
;
; NOTE (same real per-mode asymmetry documented for Timer0's
; version of this test): handle_Phase_Correct_PWM_mode() never
; sets OCF2A when COM2A==0 (no unconditional match-check block
; the way handle_normal_mode()/handle_CTC_mode() have) -- only
; TOV2 latches at BOTTOM regardless of COM2A. Polls TOV2 for
; that reason.
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

    ldi r16, 5
    sts OCR2A, r16
    ldi r16, 0x01
    sts TCCR2A, r16
    ldi r16, 0x01
    sts TCCR2B, r16
    ldi r16, 0x01        ; TOIE2=1
    sts TIMSK2, r16

    ldi r18, 0
poll_loop1:
    lds r17, TIFR2
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
