; ============================================================
; SBIC instruction test suite for ATmega328P
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
; TEST 1: bit = 0 → should SKIP
; PORTB = 0x00, SBIC PORTB,0
; ============================================================
test1:
    ldi r16, 0x00
    out PORTB, r16

    ldi r17, 0x11
    sbic PORTB, 0
    ldi r17, 0x22     ; should be skipped

    cpi r17, 0x11
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: bit = 1 → should NOT skip
; PORTB = 0x00, SBIC PORTB,1
; ============================================================
test2:
    ldi r16, 0x00
    out PORTB, r16

    ldi r17, 0x11
    sbic PORTB, 1
    ldi r17, 0x22     ; should execute

    cpi r17, 0x11
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: bit = 1 set → should NOT skip
; PORTB = 0x02
; ============================================================
test3:
    ldi r16, 0x02
    out PORTB, r16

    ldi r17, 0x11
    sbic PORTB, 1
    ldi r17, 0x22

    cpi r17, 0x22
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: bit = 0 set → should NOT skip
; ============================================================
test4:
    ldi r16, 0x01
    out PORTB, r16

    ldi r17, 0x11
    sbic PORTB, 0
    ldi r17, 0x22

    cpi r17, 0x22
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: different I/O register (DDRB)
; ============================================================
test5:
    ldi r16, 0x00
    out DDRB, r16

    ldi r17, 0x11
    sbic DDRB, 7
    ldi r17, 0x22     ; should skip if bit 7 = 0

    cpi r17, 0x11
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