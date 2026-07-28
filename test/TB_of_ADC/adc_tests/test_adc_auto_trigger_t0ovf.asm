; ADATE=1, ADTS=100 (Timer0 overflow). Peer autonomously pulses T0_OVF
; every 50 cycles (see TEST_PEER_KWARGS's 'autopulse' in tb_adc_tests.py)
; -- this program never writes ADSC at all, purely arms the trigger and
; waits for hardware to start the conversion on its own.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ ADCL   = 0x78
.equ ADCH   = 0x79
.equ ADCSRA = 0x7A
.equ ADCSRB = 0x7B
.equ ADMUX  = 0x7C

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x00
    sts ADMUX, r16
    ldi r16, 0x04              ; ADTS=100 (Timer0 Overflow)
    sts ADCSRB, r16
    ldi r16, 0xA0              ; ADEN=1 ADSC=0 ADATE=1 ADPS=000
    sts ADCSRA, r16

    ldi r18, 0
    ldi r19, 0
poll_loop:
    lds r17, ADCSRA
    sbrc r17, 4
    rjmp conv_done
    inc r18
    brne poll_loop          ; loops until r18 wraps 255->0 (256 iters/round)
    inc r19
    cpi r19, 20              ; ~20 rounds of headroom before giving up
    brne poll_loop
    rjmp fail

conv_done:
    lds r20, ADCL
    lds r21, ADCH
    cpi r20, 0xAB
    brne fail
    cpi r21, 0x00
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
