; ============================================================
; OR instruction test suite for ATmega328P
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ldi r16, 0x08
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Basic logical OR
; 0b00001111 OR 0b11110000 = 0b11111111 (0xFF)
; ============================================================
test1:
    ldi r16, 0x0F
    ldi r17, 0xF0
    or r16, r17

    cpi r16, 0xFF
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: OR with zero (Identity)
; 0x55 OR 0x00 = 0x55
; ============================================================
test2:
    ldi r16, 0x55
    ldi r17, 0x00
    or r16, r17

    cpi r16, 0x55
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: OR with all ones (Setting all bits)
; 0x33 OR 0xFF = 0xFF
; ============================================================
test3:
    ldi r16, 0x33
    ldi r17, 0xFF
    or r16, r17

    cpi r16, 0xFF
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Partial bit setting
; 0b10100000 OR 0b00001010 = 0b10101010 (0xAA)
; ============================================================
test4:
    ldi r16, 0xA0
    ldi r17, 0x0A
    or r16, r17

    cpi r16, 0xAA
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: Idempotency (X OR X = X)
; 0x77 OR 0x77 = 0x77
; ============================================================
test5:
    ldi r16, 0x77
    or r16, r16

    cpi r16, 0x77
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