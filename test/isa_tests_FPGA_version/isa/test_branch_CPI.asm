; ============================================================
; CPI instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; CPI Rd, K   :  Rd - K   (Rd is r16..r31, K is 8-bit immediate)
; Values are not modified. Updates: Z, C, N, V, S, H
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
    ldi r16, 0x08
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Equal values (30 == 30)
; Expect: Z=1, C=0
; ============================================================
test1:
    ldi r16, 30
    cpi r16, 30
    brne fail           ; Fail if Z is 0
    brcs fail           ; Fail if C is 1
    cpi r16, 30         ; Verify register not modified
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Rd > K (30 > 20)
; Expect: Z=0, C=0
; ============================================================
test2:
    ldi r16, 30
    cpi r16, 20
    breq fail           ; Fail if Z is 1
    brcs fail           ; Fail if C is 1
    rcall inc_case

; ============================================================
; TEST 3: Rd < K (20 < 30)
; Expect: Z=0, C=1 (Borrow generated)
; ============================================================
test3:
    ldi r16, 20
    cpi r16, 30
    breq fail           ; Fail if Z is 1
    brcc fail           ; Fail if C is 0
    rcall inc_case

; ============================================================
; TEST 4: Boundary check (0 < 1)
; Expect: Z=0, C=1
; ============================================================
test4:
    ldi r16, 0
    cpi r16, 1
    brcc fail
    rcall inc_case

; ============================================================
; TEST 5: Compare against 0 (77 != 0)
; Expect: Z=0, C=0
; ============================================================
test5:
    ldi r16, 77
    cpi r16, 0
    breq fail
    rcall inc_case

; ============================================================
; TEST 6: Compare max value against max (255 == 255)
; Expect: Z=1
; ============================================================
test6:
    ldi r16, 255
    cpi r16, 255
    brne fail
    rcall inc_case

; ============================================================
; TEST 7: Compare max value against 0 (255 > 0)
; Expect: Z=0, C=0
; ============================================================
test7:
    ldi r16, 255
    cpi r16, 0
    breq fail
    brcs fail
    rcall inc_case

; ============================================================
; TEST 8: Verify CPI ignores incoming Carry flag
; 10 == 10. Even if C=1, 10-10 = 0 (CPI does not subtract C)
; ============================================================
test8:
    sec
    ldi r16, 10
    cpi r16, 10
    brne fail           ; Should still result in Zero flag set
    rcall inc_case

; ============================================================
; SUCCESS
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end

fail:
    ldi r16, -1
    sts final_result, r16
    rjmp end

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret