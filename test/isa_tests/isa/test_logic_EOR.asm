; ============================================================
; EOR instruction test suite for ATmega328P
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D

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
; TEST 1: XOR with zero (Identity)
; 0x55 XOR 0x00 = 0x55
; ============================================================
test1:
    ldi r16, 0x55
    ldi r17, 0x00
    eor r16, r17

    cpi r16, 0x55
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: XOR with itself
; 0x77 XOR 0x77 = 0x00
; ============================================================
test2:
    ldi r16, 0x77
    eor r16, r16

    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Complement generation
; 0x33 XOR 0xFF = 0xCC
; ============================================================
test3:
    ldi r16, 0x33
    ldi r17, 0xFF
    eor r16, r17

    cpi r16, 0xCC
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Alternating patterns
; 0xAA XOR 0x55 = 0xFF
; ============================================================
test4:
    ldi r16, 0xAA
    ldi r17, 0x55
    eor r16, r17

    cpi r16, 0xFF
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: General mixed values
; 0x96 XOR 0x3C = 0xAA
; ============================================================
test5:
    ldi r16, 0x96
    ldi r17, 0x3C
    eor r16, r17

    cpi r16, 0xAA
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