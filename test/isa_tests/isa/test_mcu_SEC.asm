; ============================================================
; SEC (Set Carry Flag) test suite
; ============================================================
; Tests that SEC correctly:
; 1. Sets the Carry flag (bit 0 of SREG) to 1
; 2. Does not affect other bits in SREG
; ============================================================
; SEC is a 1-word (16-bit) instruction
; Format: 1001 0100 0000 1000
; Operation: C <- 1
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SREG = 0x3F

reset:
    ; === Initialize Stack Pointer ===
    ldi r16, 0x08        ; SPH for ATmega328P (RAMEND is typically 0x08FF)
    out 0x3E, r16
    ldi r16, 0xFF        ; SPL for ATmega328P
    out 0x3D, r16
    ; ================================

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    rjmp test1_start

; ============================================================
; TEST 1: Basic SEC verification
; ============================================================
test1_start:
    clc                 ; Ensure Carry is 0 first
    sec                 ; Perform the test instruction
    
    ; Use brcs (Branch if Carry Set) to verify
    brcs test1_pass     ; If C=1, proceed
    rjmp fail
test1_pass:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: SEC preserves other flags
; ============================================================
test2_start:
    ; Set the Zero flag (Z=1), then run SEC
    sez
    sec
    
    ; If SEC works correctly, Z should still be 1
    brne fail           ; If Z=0, brne branches (fail)
    
    rcall inc_case
    rjmp success

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