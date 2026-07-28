; Reading ADCL locks ADCH/ADCL against being updated by a completing
; conversion until ADCH is subsequently read. Free-running mode is used
; so a conversion keeps completing in the background while the lock is
; held, giving something for the lock to actually block.
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

    ldi r16, 0x00                ; MUX=0 -> peer channel 0 = 0x2AA
    sts ADMUX, r16
    ldi r16, 0x00                ; free running
    sts ADCSRB, r16
    ldi r16, 0xE1                 ; ADEN=1 ADSC=1 ADATE=1 ADPS=001
    sts ADCSRA, r16

    rcall wait_adif                ; first conversion: result = 0x2AA
    lds r20, ADCL                  ; low = 0xAA -- this READ sets the lock
    cpi r20, 0xAA
    brne fail
    lds r16, ADCSRA
    andi r16, 0xE7                 ; clear ADIF, leave ADIF's write-bit 0
    sts ADCSRA, r16
    rcall inc_case

    ; Lock is now held. Switch MUX to channel 1 (peer = 0x155, a
    ; genuinely different value) -- free-running re-latches MUX at the
    ; start of every new conversion, so the *next* completed conversion
    ; really will be sampling a different channel. If the lock is
    ; broken, ADCL will visibly change to 0x55; if it's correct, ADCL
    ; must still read the original 0xAA from before the lock was taken.
    ldi r16, 0x01
    sts ADMUX, r16

    rcall wait_adif                 ; channel-1 conversion completes...
    lds r16, ADCSRA                 ; ...but must not reach ADCL/ADCH
    andi r16, 0xE7
    sts ADCSRA, r16

    lds r21, ADCL
    cp r20, r21
    brne fail                        ; would now read 0x55 if the lock leaked
    rcall inc_case

    ; Now read ADCH -- releases the lock.
    lds r22, ADCH
    cpi r22, 0x02                    ; still the channel-0 high byte
    brne fail
    rcall inc_case

    ; One more free-running conversion (channel 1 is still selected)
    ; should now be free to update the registers with the new value.
    rcall wait_adif
    lds r23, ADCL
    cpi r23, 0x55
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
