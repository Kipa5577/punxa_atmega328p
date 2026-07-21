; ============================================================
; CPC instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; CPC Rd, Rr  :  Rd - Rr - C  (Values are not modified)
; Works on all registers r0..r31
; Updates: Z, C, N, V, S, H
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
; TEST 1: Compare with Carry Clear (C=0)
; 50 - 50 - 0 = 0. Expect: Z=1, C=0
; ============================================================
test1:
    clc
    ldi r16, 50
    ldi r17, 50
    sez                    ; Prime Z=1: CPC's Z = Zprev AND (result==0),
                            ; by design (chains after a CP/CPI on a lower
                            ; byte) -- a standalone cpc needs Z primed to
                            ; behave like a normal compare. See HANDOFF.md.
    cpc r16, r17
    brne fail             ; Fail if Z is 0
    brcs fail             ; Fail if C is 1
    rcall inc_case

; ============================================================
; TEST 2: Compare with Carry Set (C=1)
; 50 - 50 - 1 = -1. Expect: Z=0, C=1
; ============================================================
test2:
    sec
    ldi r16, 50
    ldi r17, 50
    sez                    ; Prime Z=1 (see TEST 1 note)
    cpc r16, r17
    breq fail             ; Fail if Z is 1
    brcc fail             ; Fail if C is 0
    rcall inc_case

; ============================================================
; TEST 3: Multi-byte comparison (Low byte)
; Compare 0x0100 with 0x0100 (C=0)
; ============================================================
test3:
    clc
    ldi r16, 0x00         ; Low byte
    ldi r17, 0x00
    sez                    ; Prime Z=1 (see TEST 1 note)
    cpc r16, r17          ; 0x00 - 0x00 - 0 = 0 (Z=1, C=0)
    brne fail
    brcs fail
    rcall inc_case

; ============================================================
; TEST 4: Multi-byte comparison (High byte, Carry propagation)
; High byte of 0x0100 vs 0x0100
; ============================================================
test4:
    ldi r16, 0x01         ; High byte
    ldi r17, 0x01
    sez                    ; Prime Z=1 (see TEST 1 note)
    cpc r16, r17          ; 0x01 - 0x01 - 0 = 0 (Z=1, C=0)
    brne fail
    brcs fail
    rcall inc_case

; ============================================================
; TEST 5: Borrow propagation (16-bit)
; Compare 0x0100 (Rd) with 0x0101 (Rr)
; ============================================================
test5:
    ; Step 1: Low byte
    clc
    ldi r16, 0x00         ; Rd
    ldi r17, 0x01         ; Rr
    cpc r16, r17          ; 0x00 - 0x01 - 0 = 255 (Z=0, C=1)
    brcc fail             ; Fail if C is 0
    
    ; Step 2: High byte
    ldi r16, 0x01         ; Rd
    ldi r17, 0x01         ; Rr
    cpc r16, r17          ; 0x01 - 0x01 - 1(Carry) = 255 (Z=0, C=1)
    brcc fail             ; Fail if C is 0
    rcall inc_case

; ============================================================
; TEST 6: Verify registers are NOT modified
; ============================================================
test6:
    ldi r16, 0xAA
    ldi r17, 0x55
    cpc r16, r17
    cpi r16, 0xAA
    brne fail
    cpi r17, 0x55
    brne fail
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