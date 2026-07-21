; ============================================================
; CLZ (Clear Zero Flag) test suite
; ============================================================
; Tests that CLZ correctly:
; 1. Clears the Zero flag (bit 1 of SREG) to 0
; 2. Does not affect other bits in SREG
; ============================================================
; CLZ is a 1-word (16-bit) instruction
; Format: 1001 0100 1001 1000
; Operation: Z <- 0
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SREG = 0x3F

reset:
    ; === Add this Stack Pointer initialization ===
    ldi r16, 0x08        ; SPH (RAMEND high byte)
    out 0x3E, r16
    ldi r16, 0xFF        ; SPL (RAMEND low byte)
    out 0x3D, r16
    ; =============================================

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    rjmp test1_start

; ============================================================
; TEST 1: Basic CLZ verification
; ============================================================
test1_start:
    sez                 ; Ensure Zero is 1 first
    clz                 ; Perform the test instruction
    
    ; Use brne (Branch if Not Equal) to verify.
    ; If Z=0, brne should branch.
    brne test1_pass     ; If Z=0, branch to pass
    rjmp fail
test1_pass:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: CLZ preserves other flags
; ============================================================
test2_start:
    ; Set the Carry flag (C=1), then run CLZ
    sec
    clz
    
    ; If CLZ works correctly, C should still be 1
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