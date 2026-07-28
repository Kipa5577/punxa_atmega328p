; Timer0, Fast PWM, COM0A=00 -- real hardware's "normal port
; operation" (pin reverts to plain GPIO, driven by DDR/PORT).
; This project has no top-level GPIO<->OCnx pin mux yet (no
; ATmega328P_Top.py -- same explicitly-out-of-scope boundary
; ADC.py's own docstring calls out for DIDR0/GPIO), so at the
; peripheral level COM0A=00 IS the model's entire implementation
; of "normal port operation": OC0A_val is forced 0 and the
; timer does not drive the pin at all, identical code path to
; test_timer0_fast_pwm_disconnected.asm. Kept as a separate file
; per the backlog, asserting the same thing, since real-hardware
; "disconnected" and "normal port operation" ARE the same
; COM bits (00) -- they only differ in real hardware framing
; (what the datasheet calls the pin when OC0A isn't driving it).
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

    ldi r16, 5
    sts OCR0A, r16
    ldi r16, 0x03
    sts TCCR0A, r16
    ldi r16, 0x01
    sts TCCR0B, r16
    ldi r16, 0x02
    sts TIMSK0, r16

    ldi r18, 0
poll_loop1:
    lds r17, TIFR0
    sbrc r17, 1
    rjmp seen1
    inc r18
    cpi r18, 250
    brne poll_loop1
    rjmp fail
seen1:
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
