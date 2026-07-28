; Timer2, Normal mode, COM2A=11 (set). OCR2A left at 0, TCNT2
; parked at 0x80 with the clock source left OFF entirely (CS=000)
; so no real match/wrap can ever occur. FOC2A (TCCR2B bit7)
; forces OC2A high immediately (PEER_PIN_CHECKS) without setting
; OCF2A.
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

    ldi r16, 0xC0        ; COM2A=11 (set), WGM21:20=00 (Normal)
    sts TCCR2A, r16
    ldi r16, 0x80
    sts TCNT2, r16
    ldi r16, 0x02        ; OCIE2A=1
    sts TIMSK2, r16
    ldi r16, 0x80        ; FOC2A=1, CS22:20=000 (clock off)
    sts TCCR2B, r16

    ldi r18, 0
settle_loop:
    nop
    inc r18
    cpi r18, 40
    brne settle_loop
    rcall inc_case

    lds r17, TIFR2
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
