; ============================================================
; CLC (Clear Carry Flag) test suite
; ============================================================
; Tests that CLC correctly:
; 1. Clears the Carry flag (bit 0 of SREG) to 0
; 2. Does not affect other bits in SREG
; ============================================================
; CLC is a 1-word (16-bit) instruction
; Format: 1001 0100 1000 1000
; Operation: C <- 0
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
; TEST 1: Basic CLC verification
; ============================================================
test1_start:
    sec                 ; Set Carry first to ensure it's 1
    clc                 ; Perform the test instruction
    
    ; Use brcc (Branch if Carry Cleared) to verify
    brcc test1_pass     ; If C=0, proceed
    rjmp fail
test1_pass:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: CLC preserves other flags
; ============================================================
test2_start:
    ; Set the Zero flag (Z=1), then run CLC
    sez
    clc
    
    ; If CLC works correctly, Z should still be 1
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