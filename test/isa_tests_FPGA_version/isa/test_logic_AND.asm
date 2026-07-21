; ============================================================
; AND instruction test suite for ATmega328P
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ldi r16, 0x03
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16

    ldi r16, 1 ; Start at test 1 (adjust if index starts at 0)
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Basic logical AND
; 0b10101010 AND 0b01010101 = 0b00000000
; ============================================================
test1:
    ldi r16, 0xAA
    ldi r17, 0x55
    and r16, r17            ; r16 = 0

    cpi r16, 0
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Identity (AND with 0xFF)
; 0b11001100 AND 0xFF = 0b11001100
; ============================================================
test2:
    ldi r16, 0xCC
    ldi r17, 0xFF
    and r16, r17            ; r16 = 0xCC

    cpi r16, 0xCC
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Masking bits
; 0b11110000 AND 0b00001111 = 0b00000000
; ============================================================
test3:
    ldi r16, 0xF0
    ldi r17, 0x0F
    and r16, r17

    cpi r16, 0
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Partial bit preservation
; 0b10101010 AND 0b11110000 = 0b10100000 (0xA0)
; ============================================================
test4:
    ldi r16, 0xAA
    ldi r17, 0xF0
    and r16, r17

    cpi r16, 0xA0
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: Self AND (Idempotent property: X AND X = X)
; 0b01011010 AND 0b01011010 = 0b01011010
; ============================================================
test5:
    ldi r16, 0x5A
    and r16, r16            ; r16 should remain 0x5A

    cpi r16, 0x5A
    brne fail
    rcall inc_case

; ============================================================
; SUCCESS and FAILURE logic
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end

fail:
    ldi r16, 255            ; Result 255 signals failure in your script
    sts final_result, r16
    rjmp end

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret