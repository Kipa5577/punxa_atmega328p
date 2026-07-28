; Timer1, Phase-and-Frequency-Correct PWM, TOP=ICR1 (WGM=8).
; COM1A=10 (clear-on-match-while-counting-up / set-while-
; counting-down) -- WGM=8 does NOT get real toggle support (only
; WGM=9 does, see handle_Phase_Correct_And_Frequency_PWM_mode's
; `WGM==9` check), so this uses the non-inverting duty-cycle COM
; setting instead, confirmed via PEER_PIN_CHECKS.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR1A = 0x80
.equ TCCR1B = 0x81
.equ TCCR1C = 0x82
.equ TCNT1L = 0x84
.equ TCNT1H = 0x85
.equ ICR1L = 0x86
.equ ICR1H = 0x87
.equ OCR1AL = 0x88
.equ OCR1AH = 0x89
.equ OCR1BL = 0x8a
.equ OCR1BH = 0x8b
.equ TIMSK1 = 0x6f
.equ TIFR1 = 0x36

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0
    sts ICR1H, r16
    ldi r16, 5
    sts ICR1L, r16
    ldi r16, 0
    sts OCR1AH, r16
    ldi r16, 5
    sts OCR1AL, r16
    ldi r16, 0x02        ; OCIE1A=1
    sts TIMSK1, r16
    ldi r16, 0x80        ; COM1A=10
    sts TCCR1A, r16
    ldi r16, 0x11        ; WGM13=1,WGM12=0 (-> WGM=8, TOP=ICR1), CS=001
    sts TCCR1B, r16

    ldi r18, 0
poll_loop1:
    lds r17, TIFR1
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
