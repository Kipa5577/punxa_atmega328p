; ============================================================
; BRBS (Branch if Bit Set) test suite
; ============================================================
; Tests that BRBS correctly branches when SREG bits = 1
; and does NOT branch when SREG bits = 0
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
    sts final_result, r16

; ============================================================
; TEST 1: Branch if Zero Flag is SET (Z=1)
; ============================================================
test1:
    ; Set Z flag to 1 by making result zero
    ldi r16, 0
    tst r16             ; Result is 0, so Z=1
    
    brbs 1, branch1_ok  ; If Z is 1, branch to label
    rjmp fail           ; Should NOT execute (Z=1, so branch taken)
branch1_ok:
    rcall inc_case

; ============================================================
; TEST 2: Do NOT Branch if Zero Flag is CLEAR (Z=0)
; ============================================================
test2:
    ; Set Z flag to 0 by making result non-zero
    ldi r16, 1
    tst r16             ; Result is 1, so Z=0
    
    brbs 1, fail        ; If Z=0, this should NOT branch
    rcall inc_case      ; Should execute (Z=0, no branch)

; ============================================================
; TEST 3: Branch if Carry Flag is SET (C=1)
; ============================================================
test3:
    ; Set Carry flag by adding with overflow
    ldi r16, 0xFF
    ldi r17, 1
    add r16, r17        ; 0xFF + 1 = 0x100, so C=1
    
    brbs 0, branch3_ok  ; If C=1, branch
    rjmp fail
branch3_ok:
    rcall inc_case

; ============================================================
; TEST 4: Do NOT Branch if Carry Flag is CLEAR (C=0)
; ============================================================
test4:
    ; Clear Carry flag
    clc                 ; C=0
    
    brbs 0, fail        ; If C=0, this should NOT branch
    rcall inc_case      ; Should execute (C=0, no branch)

; ============================================================
; TEST 5: Branch if Negative Flag is SET (N=1)
; ============================================================
test5:
    ; Set N flag (make result negative)
    ldi r16, 0x80       ; 0x80 = -128 in signed
    tst r16             ; Bit 7 = 1, so N=1
    
    brbs 2, branch5_ok  ; If N=1, branch
    rjmp fail
branch5_ok:
    rcall inc_case

; ============================================================
; TEST 6: Do NOT Branch if Negative Flag is CLEAR (N=0)
; ============================================================
test6:
    ; Clear N flag (make result positive)
    ldi r16, 0x7F       ; 0x7F = +127
    tst r16             ; Bit 7 = 0, so N=0
    
    brbs 2, fail        ; If N=0, this should NOT branch
    rcall inc_case      ; Should execute (N=0, no branch)

; ============================================================
; TEST 7: Branch if Overflow Flag is SET (V=1)
; ============================================================
test7:
    ; Set V flag (signed overflow)
    ldi r16, 0x7F       ; +127
    ldi r17, 1
    add r16, r17        ; 127 + 1 = 128 (-128 in signed), overflow occurs
    
    brbs 3, branch7_ok  ; If V=1, branch
    rjmp fail
branch7_ok:
    rcall inc_case

; ============================================================
; TEST 8: Do NOT Branch if Overflow Flag is CLEAR (V=0)
; ============================================================
test8:
    ; Clear V flag (no overflow)
    ldi r16, 0x10
    ldi r17, 0x20
    add r16, r17        ; 16 + 32 = 48, no overflow
    
    brbs 3, fail        ; If V=0, this should NOT branch
    rcall inc_case      ; Should execute (V=0, no branch)

; ============================================================
; TEST 9: Branch if Interrupt Flag is SET (I=1)
; ============================================================
test9:
    ; Set I flag
    sei                 ; I=1
    
    brbs 7, branch9_ok  ; If I=1, branch
    rjmp fail
branch9_ok:
    rcall inc_case

; ============================================================
; TEST 10: Do NOT Branch if Interrupt Flag is CLEAR (I=0)
; ============================================================
test10:
    ; Clear I flag
    cli                 ; I=0
    
    brbs 7, fail        ; If I=0, this should NOT branch
    rcall inc_case      ; Should execute (I=0, no branch)

; ============================================================
; TEST 11: Branch if Sign Flag is SET (S=1)
; ============================================================
test11:
    ; Set S flag (negative result with no overflow)
    ; S = N ⊕ V = 1 ⊕ 0 = 1
    ldi r16, 0xF0       ; -16 in signed
    ldi r17, 0x10
    sub r16, r17        ; Negative result, no overflow
    
    brbs 4, branch11_ok ; If S=1, branch
    rjmp fail
branch11_ok:
    rcall inc_case

; ============================================================
; TEST 12: Do NOT Branch if Sign Flag is CLEAR (S=0)
; ============================================================
test12:
    ; Clear S flag (positive result)
    ldi r16, 0x10
    subi r16, 0x05      ; 16 - 5 = 11, positive, no overflow
    
    brbs 4, fail        ; If S=0, this should NOT branch
    rcall inc_case      ; Should execute (S=0, no branch)

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