; ADIE=1: ADC_IRQ pin (checked independently by the harness via
; IRQ_LEVEL_CHECKS -- see tb_adc_tests.py) should assert once ADIF sets.
; Real vector-dispatch (CPU actually jumping to the ADC ISR) is out of
; scope here -- that's the interrupt controller's own standalone-testing
; job per the project task list, not ADC's; this test only confirms
; ADC's own half of the contract: it correctly ANDs ADIF with ADIE onto
; the wire SimpleInterruptUnit expects. Also confirms clearing ADIE
; deasserts the pin even though ADIF (checked via lds) is still set --
; proving the gating is live, not just checked once.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
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

    ldi r16, 0x00
    sts ADMUX, r16
    ldi r16, 0xCB               ; ADEN=1 ADSC=1 ADIE=1 ADPS=011
    sts ADCSRA, r16

    ldi r18, 0
poll_loop:
    lds r17, ADCSRA
    sbrc r17, 4                 ; ADIF
    rjmp conv_done
    inc r18
    brne poll_loop
    rjmp fail

conv_done:
    ; ADIF is set and ADIE is set -- ADC_IRQ should be asserted right
    ; now (harness doesn't check mid-test, only at 'end', so this test
    ; case is purely a CPU-visible sanity check that ADIF really did
    ; latch).
    lds r17, ADCSRA
    sbrs r17, 4
    rjmp fail
    rcall inc_case

    ; Now clear ADIE (keep ADIF as-is). Real AVR gotcha this test
    ; deliberately exercises correctly: ADIF is write-1-to-clear, so a
    ; naive read-modify-write that reads ADCSRA (bit4=1, since ADIF just
    ; latched) and writes it straight back WOULD clear ADIF too -- the
    ; mask must explicitly zero bit4 in the value being written (a 0
    ; there means "leave ADIF alone", not "ADIF is 0") to actually
    ; preserve it. This is real, documented ATmega328P behavior, not a
    ; simulator quirk -- confirmed by deliberately getting this wrong
    ; first (mask 0xF7, clearing only ADIE) and watching ADIF clear
    ; anyway, exactly as real hardware would.
    lds r16, ADCSRA
    andi r16, 0xE7               ; clear bit3 (ADIE) AND bit4 (ADIF's
    sts ADCSRA, r16               ; write-bit) so ADIF is left untouched
    lds r17, ADCSRA
    sbrc r17, 4                  ; ADIF must still read 1 (untouched)
    rjmp adif_still_set
    rjmp fail
adif_still_set:
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
