; Timer0, Normal mode, clock already running (CS=001). A direct
; software write to TCNT0 while it's actively counting must take
; effect immediately (the model has no write-buffering/blocked-
; write-while-running behavior -- Memory_access's TCNT0 write
; branch is unconditional).
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
    ldi r16, 0x01
    sts TCCR0B, r16

    ldi r18, 0
run_a_bit:
    nop
    nop
    inc r18
    cpi r18, 30
    brne run_a_bit
    rcall inc_case

    ldi r16, 200
    sts TCNT0, r16
    lds r17, TCNT0
    cpi r17, 200
    brlo fail            ; must read back >= 200 immediately (it may
                          ; have ticked a couple more since the write)
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
