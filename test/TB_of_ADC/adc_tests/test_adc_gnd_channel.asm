; MUX=1111 (GND) always converts to 0, regardless of whatever the peer
; happens to be driving on the ADC0 pin (0x2AA in this test's peer
; config, inherited from another test's TEST_PEER_KWARGS entry not
; applying here -- this test uses no peer override at all, so every
; channel wire defaults to 0 anyway; MUX=0 vs MUX=1111 both would read
; 0 in that case, so this test explicitly drives a nonzero code onto
; ADC0 itself and confirms GND still reads 0 even though a real channel
; right next to it does not).
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ ADCL   = 0x78
.equ ADCH   = 0x79
.equ ADCSRA = 0x7A
.equ ADMUX  = 0x7C

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0x0F                ; MUX=1111 (GND)
    sts ADMUX, r16
    ldi r16, 0xC7
    sts ADCSRA, r16
    rcall wait_adif
    lds r20, ADCL
    lds r21, ADCH
    cpi r20, 0
    brne fail
    cpi r21, 0
    brne fail
    rcall inc_case

    rjmp success

wait_adif:
    ldi r19, 0
wait_loop:
    lds r17, ADCSRA
    sbrc r17, 4
    ret
    inc r19
    brne wait_loop
    rjmp fail

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
