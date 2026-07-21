; ============================================================
; CBI (Clear Bit in I/O Register) test suite
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

; Define a test I/O register (e.g., PortB is usually at 0x05)
.equ PORTB = 0x05

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Clear bit 0 of PORTB
; Initial: 0xFF, After CBI: 0xFE
; ============================================================
test1:
    ldi r16, 0xFF
    out PORTB, r16      ; Write 0xFF to PORTB
    cbi PORTB, 0        ; Clear bit 0 of PORTB

    in r16, PORTB       ; Read back to verify
    cpi r16, 0xFE
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Clear bit 7 of PORTB
; Initial: 0x80, After CBI: 0x00
; ============================================================
test2:
    ldi r16, 0x80
    out PORTB, r16
    cbi PORTB, 7        ; Clear bit 7

    in r16, PORTB
    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; SUCCESS / FAILURE logic
; ============================================================
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