; ============================================================
; ORI instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; ORI Rd, K   :  Rd = Rd | K   (K is an 8-bit immediate)
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
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Identity (OR with 0x00)
; 0xAA (10101010) | 0x00 (00000000) = 0xAA (10101010)
; ============================================================
test1:
    ldi r16, 0xAA
    ori r16, 0x00             ; r16 = 0xAA
    cpi r16, 0xAA
    breq skip_1
    rjmp fail
skip_1:
    rcall inc_case

; ============================================================
; TEST 2: Set all bits (OR with 0xFF)
; 0x55 (01010101) | 0xFF (11111111) = 0xFF
; ============================================================
test2:
    ldi r16, 0x55
    ori r16, 0xFF             ; r16 = 0xFF
    cpi r16, 0xFF
    breq skip_2
    rjmp fail
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Mutually exclusive bits
; 0xAA (10101010) | 0x55 (01010101) = 0xFF (11111111)
; ============================================================
test3:
    ldi r16, 0xAA
    ori r16, 0x55             ; r16 = 0xFF
    cpi r16, 0xFF
    breq skip_3
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: OR with self
; 0xC3 (11000011) | 0xC3 (11000011) = 0xC3
; ============================================================
test4:
    ldi r16, 0xC3
    ori r16, 0xC3             ; r16 = 0xC3
    cpi r16, 0xC3
    breq skip_4
    rjmp fail
skip_4:
    rcall inc_case

; ============================================================
; TEST 5: Set Most Significant Bit (MSB)
; 0x0F (00001111) | 0x80 (10000000) = 0x8F (10001111)
; ============================================================
test5:
    ldi r16, 0x0F
    ori r16, 0x80             ; r16 = 0x8F
    cpi r16, 0x8F
    breq skip_5
    rjmp fail
skip_5:
    rcall inc_case

; ============================================================
; TEST 6: Set Least Significant Bit (LSB)
; 0xF0 (11110000) | 0x01 (00000001) = 0xF1 (11110001)
; ============================================================
test6:
    ldi r16, 0xF0
    ori r16, 0x01             ; r16 = 0xF1
    cpi r16, 0xF1
    breq skip_6
    rjmp fail
skip_6:
    rcall inc_case

; ============================================================
; TEST 7: Overlapping bits
; 0x1C (00011100) | 0x38 (00111000) = 0x3C (00111100)
; ============================================================
test7:
    ldi r16, 0x1C
    ori r16, 0x38             ; r16 = 0x3C
    cpi r16, 0x3C
    breq skip_7
    rjmp fail
skip_7:
    rcall inc_case

; ============================================================
; TEST 8: Setting upper nibble
; 0x0B (00001011) | 0xF0 (11110000) = 0xFB (11111011)
; ============================================================
test8:
    ldi r16, 0x0B
    ori r16, 0xF0             ; r16 = 0xFB
    cpi r16, 0xFB
    breq skip_8
    rjmp fail
skip_8:
    rcall inc_case

; ============================================================
; TEST 9: Setting lower nibble
; 0xB0 (10110000) | 0x0F (00001111) = 0xBF (10111111)
; ============================================================
test9:
    ldi r16, 0xB0
    ori r16, 0x0F             ; r16 = 0xBF
    cpi r16, 0xBF
    breq skip_9
    rjmp fail
skip_9:
    rcall inc_case

; ============================================================
; TEST 10: Chained use — Independent registers
; Low byte:  r16 = 0x05, OR with 0x50 -> 0x55
; High byte: r17 = 0x50, OR with 0x05 -> 0x55
; ============================================================
test10:
    ldi r16, 0x05             
    ldi r17, 0x50             
    ori r16, 0x50             ; r16 result = 0x55
    ori r17, 0x05             ; r17 result = 0x55
    cpi r16, 0x55
    brne fail10
    cpi r17, 0x55
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