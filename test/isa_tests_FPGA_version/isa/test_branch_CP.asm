; ============================================================
; CP instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; CP Rd, Rr   :  Rd - Rr  (Values are not modified)
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
; TEST 1: Equal values
; 50 == 50. Expect: Z=1, C=0, r16=50
; ============================================================
test1:
    ldi r16, 50
    ldi r17, 50
    cp r16, r17

    brne fail_t1          ; Fail if Z is 0 (Not Equal)
    brcs fail_t1          ; Fail if C is 1 (Carry/Borrow)

    cpi r16, 50           ; Ensure r16 wasn't modified!
    brne fail_t1
    rjmp test1_ok
fail_t1: jmp fail
test1_ok:
    rcall inc_case

; ============================================================
; TEST 2: Rd > Rr
; 100 > 50. Expect: Z=0, C=0, r16=100
; ============================================================
test2:
    ldi r16, 100
    ldi r17, 50
    cp r16, r17

    breq fail_t2          ; Fail if Z is 1
    brcs fail_t2          ; Fail if C is 1

    cpi r16, 100          ; Ensure r16 wasn't modified
    brne fail_t2
    rjmp test2_ok
fail_t2: jmp fail
test2_ok:
    rcall inc_case

; ============================================================
; TEST 3: Rd < Rr (Triggers Carry/Borrow)
; 50 < 100. Expect: Z=0, C=1, r16=50
; ============================================================
test3:
    ldi r16, 50
    ldi r17, 100
    cp r16, r17

    breq fail_t3          ; Fail if Z is 1
    brcc fail_t3          ; Fail if C is 0 (Needs Carry/Borrow)

    cpi r16, 50           ; Ensure r16 wasn't modified
    brne fail_t3
    rjmp test3_ok
fail_t3: jmp fail
test3_ok:
    rcall inc_case

; ============================================================
; TEST 4: Negative Result Check
; 50 - 100 = -50. Expect: N=1 (Negative Flag Set)
; ============================================================
test4:
    ldi r16, 50
    ldi r17, 100
    cp r16, r17

    brpl fail_t4          ; Fail if N is 0 (Plus/Positive)
    rjmp test4_ok
fail_t4: jmp fail
test4_ok:
    rcall inc_case

; ============================================================
; TEST 5: Compare zeros
; 0 == 0. Expect: Z=1, C=0
; ============================================================
test5:
    ldi r16, 0
    ldi r17, 0
    cp r16, r17

    brne fail_t5          ; Fail if Z is 0
    brcs fail_t5          ; Fail if C is 1
    rjmp test5_ok
fail_t5: jmp fail
test5_ok:
    rcall inc_case

; ============================================================
; TEST 6: Minimum underflow (0 < 1)
; 0 < 1. Expect: Z=0, C=1
; ============================================================
test6:
    ldi r16, 0
    ldi r17, 1
    cp r16, r17

    breq fail_t6          ; Fail if Z is 1
    brcc fail_t6          ; Fail if C is 0
    rjmp test6_ok
fail_t6: jmp fail
test6_ok:
    rcall inc_case

; ============================================================
; TEST 7: Works on lower registers (r0, r1)
; Since LDI doesn't work on r0/r1, we copy values in first.
; ============================================================
test7:
    ldi r16, 0xAA
    ldi r17, 0xAA
    mov r0, r16
    mov r1, r17

    cp r0, r1             ; 0xAA == 0xAA

    brne fail_t7          ; Fail if Z is 0
    brcs fail_t7          ; Fail if C is 1
    rjmp test7_ok
fail_t7: jmp fail
test7_ok:
    rcall inc_case

; ============================================================
; TEST 8: Ignores incoming Carry flag
; CP should just do Rd - Rr, not Rd - Rr - C.
; ============================================================
test8:
    sec                   ; Set carry flag beforehand
    ldi r16, 10
    ldi r17, 10
    cp r16, r17           ; 10 - 10 = 0. (If it used C, 10 - 10 - 1 = -1)

    brne fail_t8          ; Fail if Z is 0 (meaning it subtracted the carry)
    rjmp test8_ok
fail_t8: jmp fail
test8_ok:
    rcall inc_case

; ============================================================
; TEST 9: Compare Max Values
; 255 == 255. Expect Z=1
; ============================================================
test9:
    ldi r16, 255
    ldi r17, 255
    cp r16, r17

    brne fail_t9
    rjmp test9_ok
fail_t9: jmp fail
test9_ok:
    rcall inc_case

; ============================================================
; TEST 10: 255 > 254
; Expect Z=0, C=0
; ============================================================
test10:
    ldi r16, 255
    ldi r17, 254
    cp r16, r17

    breq fail_t10
    brcs fail_t10
    rjmp test10_ok
fail_t10: jmp fail
test10_ok:
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
