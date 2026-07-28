; Timer2, CTC mode, OC2A set to toggle on compare match (COM2A=01).
; Same shape as test_timer0_ctc_compare_match_toggle.asm -- pin
; toggling is confirmed after the fact via PeerTimer2 (see
; tb_timer_tests.py's PEER_PIN_CHECKS table).
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TCCR2A = 0xB0
.equ TCCR2B = 0xB1
.equ OCR2A  = 0xB3
.equ TIMSK2 = 0x70

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 5
    sts OCR2A, r16
    ldi r16, 0x42        ; COM2A=01 (toggle), WGM21=1 (CTC)
    sts TCCR2A, r16
    ldi r16, 0x01        ; CS22:20 = 001 -> no prescaling
    sts TCCR2B, r16
    ldi r16, 0x02        ; OCIE2A = 1
    sts TIMSK2, r16

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
