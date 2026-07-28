; Timer1, Fast PWM (WGM=14, TOP=ICR1). Same live-update proof as
; ocr1a_buffer_update_fast_pwm.asm, for ICR1 defining TOP
; (checked via TOV1, which fires at the TOP wrap).
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
    ldi r16, 20
    sts ICR1L, r16
    ldi r16, 0x01        ; TOIE1=1
    sts TIMSK1, r16
    ldi r16, 0x02        ; WGM11:10=10
    sts TCCR1A, r16
    ldi r16, 0x19        ; WGM13=1,WGM12=1 (-> WGM=14, TOP=ICR1), CS=001
    sts TCCR1B, r16

    ldi r18, 0
poll_first:
    lds r17, TIFR1
    sbrc r17, 0
    rjmp seen_first
    inc r18
    cpi r18, 250
    brne poll_first
    rjmp fail
seen_first:
    rcall inc_case

    ldi r16, 0x01
    sts TIFR1, r16
    ldi r16, 60
    sts ICR1L, r16
    rcall inc_case

    ldi r18, 0
poll_second:
    lds r17, TIFR1
    sbrc r17, 0
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
