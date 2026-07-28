; Timer0, CTC mode, OC0A set to toggle on compare match (COM0A=01).
; No CPU-visible way to read OC0A back, so this test just runs long
; enough for several matches to occur and reach 'end' normally --
; tb_timer_tests.py's PEER_PIN_CHECKS table asserts (after the fact,
; via PeerTimer0 wired to OC0A) that the pin actually toggled >= 3
; times, since the model computes the toggle unconditionally in
; handle_CTC_mode() regardless of OCIE0A (only the TIFR0 flag bit is
; gated by OCIE0A, not the pin).
.equ test_case   = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ TCCR0A = 0x44
.equ TCCR0B = 0x45
.equ OCR0A  = 0x47
.equ TIMSK0 = 0x6E

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 5
    sts OCR0A, r16
    ldi r16, 0x42        ; COM0A=01 (toggle), WGM01=1 (CTC)
    sts TCCR0A, r16
    ldi r16, 0x01        ; CS02:00 = 001 -> no prescaling
    sts TCCR0B, r16
    ldi r16, 0x02        ; OCIE0A = 1
    sts TIMSK0, r16

    ldi r18, 0
delay_loop:
    nop
    nop
    nop
    inc r18
    cpi r18, 200
    brne delay_loop

    rcall inc_case
    rjmp success

success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end
inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret
