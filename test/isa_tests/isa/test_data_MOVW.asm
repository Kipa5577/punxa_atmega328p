; ============================================================
; MOVW instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; MOVW Rd, Rr : Rd+1:Rd = Rr+1:Rr
; Operands must be even registers (r0, r2, ..., r30).
; Updates: None.
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
; TEST 1: Basic move (r25:r24 <- r1:r0)
; ============================================================
test1:
    ldi r16, 0xAA
    mov r0, r16
    ldi r16, 0xBB
    mov r1, r16
    
    movw r30, r0          ; Destination is r31:r30
    
    cpi r30, 0xAA         ; Checking r30
    brne fail
    cpi r31, 0xBB         ; Checking r31
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Move zero values
; ============================================================
test2:
    clr r16
    clr r17
    movw r24, r16
    
    cpi r24, 0
    brne fail
    cpi r25, 0
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Move maximum values
; ============================================================
test3:
    ser r16
    ser r17
    movw r24, r16
    
    cpi r24, 0xFF
    brne fail
    cpi r25, 0xFF
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Overlapping register pairs (Self-copy)
; Copying r2:r3 to r2:r3 should result in no change.
; ============================================================
test4:
    ; Route values through r16 to get them into r2 and r3
    ldi r16, 0x12
    mov r2, r16
    ldi r16, 0x34
    mov r3, r16
    
    movw r2, r2           ; Should not affect values
    
    ; Verify r2
    ldi r16, 0x12         ; Load expected value into upper register
    cp r2, r16            ; CP works on ALL registers
    brne fail
    
    ; Verify r3
    ldi r16, 0x34         ; Load expected value into upper register
    cp r3, r16            ; CP works on ALL registers
    brne fail
    
    rcall inc_case

; ============================================================
; TEST 5: Verify flags are NOT affected
; Perform an operation, move, and check if flag is still set.
; ============================================================
test5:
    ldi r16, 0
    tst r16               ; Sets Z flag
    brne fail             ; Should not be skipped
    
    movw r24, r16         ; MOVW should not affect Z flag
    
    brne fail             ; If MOVW cleared Z, this branch would fail
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