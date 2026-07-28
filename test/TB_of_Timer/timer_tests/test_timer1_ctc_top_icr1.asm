; Timer1, CTC mode with TOP=ICR1 (WGM13:10=1100 -> WGM=12).
; Confirms OCF1A latches once TCNT1 reaches ICR1 -- the ICR1-
; as-TOP sibling of the existing ctc_top_ocr1a.asm (WGM=4).
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
    ldi r16, 0x02        ; OCIE1A=1 (before starting the clock)
    sts TIMSK1, r16
    ldi r16, 0x00
    sts TCCR1A, r16
    ldi r16, 0x19        ; WGM13=1,WGM12=1 (-> WGM=12, TOP=ICR1), CS=001
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
