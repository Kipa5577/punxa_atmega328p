; ============================================================
; SBI instruction test suite for ATmega328P
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D

.equ PORTB = 0x05
.equ DDRB  = 0x04

reset:
    ldi r16, 0x03
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Set bit 0 on PORTB
; ============================================================
test1:
    ldi r16, 0x00
    out PORTB, r16

    sbi PORTB, 0

    in r16, PORTB
    cpi r16, 0x01
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Set bit 3 on PORTB
; ============================================================
test2:
    ldi r16, 0x00
    out PORTB, r16

    sbi PORTB, 3

    in r16, PORTB
    cpi r16, 0x08
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Set bit already set (idempotence)
; ============================================================
test3:
    ldi r16, 0x08
    out PORTB, r16

    sbi PORTB, 3

    in r16, PORTB
    cpi r16, 0x08
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Multiple bit accumulation
; ============================================================
test4:
    ldi r16, 0x00
    out PORTB, r16

    sbi PORTB, 1
    sbi PORTB, 4

    in r16, PORTB
    cpi r16, 0x12
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: Different I/O register (DDRB)
; ============================================================
test5:
    ldi r16, 0x00
    out DDRB, r16

    sbi DDRB, 7

    in r16, DDRB
    cpi r16, 0x80
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