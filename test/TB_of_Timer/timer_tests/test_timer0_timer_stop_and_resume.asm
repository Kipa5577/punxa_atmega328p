; Timer0, Normal mode. Confirms CS02:00=000 truly halts TCNT0 (no
; drift while stopped) and that switching back to CS=001
; resumes counting from exactly where it left off (no reset,
; no lost prescaler state beyond the documented CS-change reset
; of prescalerCounter -- TCNT0 itself is never touched by a CS
; change).
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

    ldi r16, 0x00
    sts TCCR0A, r16
    ldi r16, 0
    sts TCNT0, r16
    ldi r16, 0x01        ; start running
    sts TCCR0B, r16

    ldi r18, 0
run1:
    nop
    nop
    inc r18
    cpi r18, 30
    brne run1
    rcall inc_case

    ldi r16, 0x00        ; stop
    sts TCCR0B, r16
    lds r19, TCNT0        ; snapshot value while stopped

    ldi r18, 0
stopped_wait:
    nop
    nop
    inc r18
    cpi r18, 30
    brne stopped_wait
    rcall inc_case

    lds r17, TCNT0
    cp r17, r19
    brne fail             ; must not have drifted while CS=000
    rcall inc_case

    ldi r16, 0x01         ; resume
    sts TCCR0B, r16
    ldi r18, 0
run2:
    nop
    nop
    inc r18
    cpi r18, 30
    brne run2
    rcall inc_case

    lds r17, TCNT0
    cp r17, r19
    brlo fail              ; must have advanced from the snapshot, not
                            ; reset to 0 or stayed put
    breq fail
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
