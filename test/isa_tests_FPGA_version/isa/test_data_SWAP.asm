; ============================================================
; SWAP instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; SWAP Rd     : Swap high nibble and low nibble of Rd
; Updates: None.
; ============================================================
; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
; -------------------------
; Reset
; -------------------------
reset:
    ldi r16, 0xFF
    out SPL, r16
    ldi r16, 0x08
    out SPH, r16
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Swap standard value 0xAB
; Expect 0xBA
; ============================================================
test1:
    ldi r16, 0xAB
    swap r16              ; r16 becomes 0xBA
    cpi r16, 0xBA
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Swap zero value 0x00
; Expect 0x00
; ============================================================
test2:
    ldi r16, 0x00
    swap r16
    cpi r16, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Swap nibble-symmetric value 0x55
; Expect 0x55
; ============================================================
test3:
    ldi r16, 0x55
    swap r16
    cpi r16, 0x55
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Swap max value 0xFF
; Expect 0xFF
; ============================================================
test4:
    ldi r16, 0xFF
    swap r16
    cpi r16, 0xFF
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: Verify status flags are not affected
; Perform a set operation (like CLC), swap, and check flag.
; ============================================================
test5:
    clc                   ; Clear Carry
    ldi r16, 0xF0
    swap r16              ; Should result in 0x0F
    
    brcs fail             ; If Carry was affected, this fails
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