; ============================================================
; SEZ (Set Zero Flag) test suite
; ============================================================
; Tests that SEZ correctly:
; 1. Sets the Zero flag (bit 1 of SREG) to 1
; 2. Does not affect other bits in SREG
; ============================================================
; SEZ is a 1-word (16-bit) instruction
; Format: 1001 0100 0001 1000
; Operation: Z <- 1
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
; TEST 1: Basic SEZ verification
; ============================================================
test1_start:
    clz                 ; Ensure Zero is 0 first
    sez                 ; Perform the test instruction
    
    ; Use brne (Branch if Not Equal, which is equivalent to
    ; checking if Z=0) to verify. If Z=1, brne should NOT trigger.
    brne fail           ; If Z=0, branch to fail
    
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: SEZ preserves other flags
; ============================================================
test2_start:
    ; Set the Carry flag (C=1), then run SEZ
    sec
    sez
    
    ; If SEZ works correctly, C should still be 1
    brcc fail           ; If C=0, brcc branches (fail)
    
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