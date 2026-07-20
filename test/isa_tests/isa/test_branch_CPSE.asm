; ============================================================
; CPSE instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; CPSE Rd, Rr :  Skip next instruction if Rd == Rr
; Works on all registers r0..r31
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
; TEST 1: Skip when equal
; 0x55 == 0x55. Should skip the rjmp fail instruction.
; ============================================================
test1:
    ldi r16, 0x55
    ldi r17, 0x55
    cpse r16, r17
    rjmp fail           ; Should be skipped
    rcall inc_case

; ============================================================
; TEST 2: Do NOT skip when unequal
; 0x55 != 0xAA. Should execute the next instruction.
; ============================================================
test2:
    ldi r16, 0x55
    ldi r17, 0xAA
    cpse r16, r17
    rjmp skip_2         ; Should NOT be skipped
    rjmp fail           ; Incorrectly skipped
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Zero values (Equal)
; 0x00 == 0x00. Should skip.
; ============================================================
test3:
    clr r16
    clr r17
    cpse r16, r17
    rjmp fail           ; Should be skipped
    rcall inc_case

; ============================================================
; TEST 4: Max values (Equal)
; 0xFF == 0xFF. Should skip.
; ============================================================
test4:
    ldi r16, 0xFF
    ldi r17, 0xFF
    cpse r16, r17
    rjmp fail           ; Should be skipped
    rcall inc_case

; ============================================================
; TEST 5: Verify registers are NOT modified
; Ensure registers retain values after CPSE
; ============================================================
test5:
    ldi r16, 0x12
    ldi r17, 0x34
    cpse r16, r17       ; No skip (unequal) -> falls through
    rjmp skip_5         ; Should NOT be skipped
    rjmp fail           ; Incorrectly skipped
skip_5:
    cpi r16, 0x12       ; Verify r16
    brne fail
    cpi r17, 0x34       ; Verify r17
    brne fail
    rcall inc_case

; ============================================================
; TEST 6: Works on lower registers (r0, r1)
; ============================================================
test6:
    ldi r16, 0x77
    mov r0, r16
    mov r1, r16
    
    cpse r0, r1
    rjmp fail           ; Should be skipped
    rcall inc_case

; ============================================================
; TEST 7: Chained CPSE
; Ensure skipping multiple times works
; ============================================================
test7:
    ldi r16, 0x01
    ldi r17, 0x01
    cpse r16, r17       ; Skip
    rjmp fail
    cpse r16, r17       ; Skip
    rjmp fail
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