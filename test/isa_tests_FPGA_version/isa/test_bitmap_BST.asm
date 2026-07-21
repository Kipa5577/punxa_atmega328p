; ============================================================
; BST (Bit Store) instruction test suite
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
; TEST 1: Store Bit 0 into T flag
; R16 = 0x01 (00000001), store bit 0 -> T = 1
; ============================================================
test1:
    ldi r16, 0x01
    bst r16, 0          ; Move bit 0 to T flag
    
    ; Verification: We use BLD to bring it back to a register
    ; so we can check if it worked.
    ldi r17, 0x00
    bld r17, 0          ; Load T into bit 0 of R17
    
    cpi r17, 1
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Store Bit 7 into T flag
; R16 = 0x80 (10000000), store bit 7 -> T = 1
; ============================================================
test2:
    ldi r16, 0x80
    bst r16, 7          ; Move bit 7 to T flag
    
    ldi r17, 0x00
    bld r17, 0          ; Move T back to bit 0 of R17
    
    cpi r17, 1
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Store a 0 bit into T flag
; R16 = 0xFE (11111110), store bit 0 -> T = 0
; ============================================================
test3:
    ldi r16, 0xFE
    clr r17             ; Clear R17 completely (R17 = 0x00) so bits 1-7 are guaranteed 0
    
    set                 ; Force T = 1 first. This proves that a subsequent BST 
                        ; actually changes the flag to 0, rather than just leaving it at a default 0.

    bst r16, 0          ; Bit 0 of R16 is 0. This should clear the T flag (T = 0).
    
    bld r17, 0          ; Copy the T flag into bit 0 of R17. 
                        ; If BST worked, R17 bit 0 becomes 0. Since bits 1-7 were already 0, R17 should be 0x00.
    
    cpi r17, 0
    brne fail           ; Branch if Not Equal: Fail if R17 is not exactly 0 (meaning T stayed 1 or R17 had dirty bits)
    
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