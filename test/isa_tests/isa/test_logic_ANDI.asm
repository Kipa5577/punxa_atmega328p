; ============================================================
; ANDI instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; ANDI Rd, K  :  Rd = Rd & K   (K is an 8-bit immediate)
; Only works on registers r16..r31
; ============================================================
; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SPH          = 0x3E
.equ SPL          = 0x3D
; -------------------------
; Reset
; -------------------------
reset:
; init stack
    ldi r16, 0x08
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16
; init state
    ldi r16, 1
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Masking upper nibble
; 0xAA (10101010) & 0x0F (00001111) = 0x0A (00001010)
; ============================================================
test1:
    ldi r16, 0xAA
    andi r16, 0x0F            ; r16 = 0x0A
    cpi r16, 0x0A
    breq skip_1
    rjmp fail
skip_1:
    rcall inc_case

; ============================================================
; TEST 2: Identity (AND with 0xFF)
; 0x55 (01010101) & 0xFF (11111111) = 0x55 (01010101)
; ============================================================
test2:
    ldi r16, 0x55
    andi r16, 0xFF            ; r16 = 0x55
    cpi r16, 0x55
    breq skip_2
    rjmp fail
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Clear all bits (AND with 0x00)
; 0x55 (01010101) & 0x00 (00000000) = 0x00
; ============================================================
test3:
    ldi r16, 0x55
    andi r16, 0x00            ; r16 = 0x00
    cpi r16, 0x00
    breq skip_3
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: Mutually exclusive bits
; 0xAA (10101010) & 0x55 (01010101) = 0x00
; ============================================================
test4:
    ldi r16, 0xAA
    andi r16, 0x55            ; r16 = 0x00
    cpi r16, 0x00
    breq skip_4
    rjmp fail
skip_4:
    rcall inc_case

; ============================================================
; TEST 5: All bits set
; 0xFF (11111111) & 0xFF (11111111) = 0xFF
; ============================================================
test5:
    ldi r16, 0xFF
    andi r16, 0xFF            ; r16 = 0xFF
    cpi r16, 0xFF
    breq skip_5
    rjmp fail
skip_5:
    rcall inc_case

; ============================================================
; TEST 6: Isolate Most Significant Bit (MSB)
; 0xC3 (11000011) & 0x80 (10000000) = 0x80
; ============================================================
test6:
    ldi r16, 0xC3
    andi r16, 0x80            ; r16 = 0x80
    cpi r16, 0x80
    breq skip_6
    rjmp fail
skip_6:
    rcall inc_case

; ============================================================
; TEST 7: Isolate Least Significant Bit (LSB)
; 0xC3 (11000011) & 0x01 (00000001) = 0x01
; ============================================================
test7:
    ldi r16, 0xC3
    andi r16, 0x01            ; r16 = 0x01
    cpi r16, 0x01
    breq skip_7
    rjmp fail
skip_7:
    rcall inc_case

; ============================================================
; TEST 8: Middle bits overlap
; 0xF0 (11110000) & 0x3C (00111100) = 0x30 (00110000)
; ============================================================
test8:
    ldi r16, 0xF0
    andi r16, 0x3C            ; r16 = 0x30
    cpi r16, 0x30
    breq skip_8
    rjmp fail
skip_8:
    rcall inc_case

; ============================================================
; TEST 9: Masking lower nibble
; 0xAA (10101010) & 0xF0 (11110000) = 0xA0 (10100000)
; ============================================================
test9:
    ldi r16, 0xAA
    andi r16, 0xF0            ; r16 = 0xA0
    cpi r16, 0xA0
    breq skip_9
    rjmp fail
skip_9:
    rcall inc_case

; ============================================================
; TEST 10: Chained use — isolating inner bits of 16-bit value
; High byte: r17 = 0x5A, AND with 0x0F -> 0x0A
; Low byte:  r16 = 0xA5, AND with 0xF0 -> 0xA0
; ============================================================
test10:
    ldi r16, 0xA5             ; low byte
    ldi r17, 0x5A             ; high byte
    andi r16, 0xF0            ; low byte result = 0xA0
    andi r17, 0x0F            ; high byte result = 0x0A
    cpi r16, 0xA0
    brne fail10
    cpi r17, 0x0A
    breq skip_10
fail10:
    rjmp fail
skip_10:
    rcall inc_case

; ============================================================
; SUCCESS
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end

; ============================================================
; FAILURE
; final_result = -1, stop execution
; ============================================================
fail:
    ldi r16, -1
    sts final_result, r16
    rjmp end

; ============================================================
; increment test_case
; ============================================================
inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret