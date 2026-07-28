; Timer1, Fast PWM 8-bit (WGM=5), COM1A=01. Per the real
; datasheet (and this model's own handle_FAST_PWM_mode gating,
; `WGM==14 or WGM==15` only), toggle is NOT a valid COM1A=01
; outcome for the fixed-8-bit-resolution Fast PWM modes --
; only the ICR1/OCR1A-top variants (WGM 14/15, see
; fast_pwm_top_icr1.asm / fast_pwm_top_ocr1a.asm) get real
; toggle behavior. Confirms the documented disconnected
; fallback plus OCF1A still latching.
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

    ldi r16, 5
    sts OCR1AL, r16
    ldi r16, 0
    sts OCR1AH, r16
    ldi r16, 0x41
    sts TCCR1A, r16
    ldi r16, 0x9
    sts TCCR1B, r16
    ldi r16, 0x02
    sts TIMSK1, r16

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
