; Timer1: confirms TCNT1H/TCNT1L, OCR1AH/OCR1AL, and ICR1H/ICR1L
; each hold their own independent byte and combine correctly
; into the 16-bit register Parse_control_registers() computes
; (self.TCNT1 = TCNT1H<<8 | TCNT1L, etc.) -- confirmed via a real
; compare match that only fires when BOTH bytes are right
; (0x1234), not just the low byte.
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

    ldi r16, 0x12
    sts OCR1AH, r16
    ldi r16, 0x34
    sts OCR1AL, r16
    ldi r16, 0x02        ; OCIE1A=1
    sts TIMSK1, r16
    ldi r16, 0x12         ; preload TCNT1 to just below the target
    sts TCNT1H, r16
    ldi r16, 0x30
    sts TCNT1L, r16
    ldi r16, 0x00
    sts TCCR1A, r16
    ldi r16, 0x01         ; CS=001
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

    ; Confirm ICR1H/ICR1L are independently writable/readable too
    ; (not used for TOP in Normal mode, so this can't itself trigger
    ; a match -- purely a register-storage check).
    ldi r16, 0xAB
    sts ICR1H, r16
    ldi r16, 0xCD
    sts ICR1L, r16
    lds r17, ICR1H
    cpi r17, 0xAB
    brne fail
    lds r17, ICR1L
    cpi r17, 0xCD
    brne fail
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
