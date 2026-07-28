; Timer0, WGM=4 and WGM=6 (both 'Reserved' per update_wave_gen_
; mode()'s case list) leave self.opMode at whatever it was
; previously set to (no case matches, so opMode/TOP are simply
; not updated that cycle -- confirmed here by setting a real
; mode first, switching to WGM=4, and confirming the counter
; keeps running rather than hanging or corrupting state).
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

    ldi r16, 0x00        ; Normal mode first (WGM=0)
    sts TCCR0A, r16
    ldi r16, 0x01
    sts TCCR0B, r16
    ldi r18, 0
warm_up:
    nop
    inc r18
    cpi r18, 20
    brne warm_up
    rcall inc_case

    ldi r16, 0x00        ; WGM01:00=00, WGM02=1 -> WGM=4 (Reserved)
    sts TCCR0A, r16
    ldi r16, 0x09        ; WGM02=1, CS=001
    sts TCCR0B, r16

    lds r19, TCNT0
    ldi r18, 0
still_running:
    nop
    inc r18
    cpi r18, 40
    brne still_running
    rcall inc_case

    lds r17, TCNT0
    cp r17, r19
    breq fail             ; must not have frozen in the reserved mode
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
