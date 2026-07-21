; ============================================================
; TST instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; TST Rd  :  Rd = Rd & Rd   (Test for Zero or Minus)
; Updates: Z (Set if 0), N (Set if MSB is 1), V (Always cleared), 
;          S (N XOR V). C is unaffected.
; ============================================================
; -------------------------
; SRAM variables & Defines
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SPH          = 0x3E
.equ SPL          = 0x3D
.equ SREG         = 0x3F      ; Define SREG I/O address directly
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
; TEST 1: Positive non-zero value
; Value = 0x55. Expect: Z=0, N=0, Value unchanged.
; ============================================================
test1:
    ldi r16, 0x55
    tst r16
    breq fail             ; Fail if Zero flag (Z) is set
    brmi fail             ; Fail if Negative flag (N) is set
    cpi r16, 0x55         ; Ensure value wasn't mutated
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Zero value
; Value = 0x00. Expect: Z=1, N=0, Value unchanged.
; ============================================================
test2:
    ldi r16, 0x00
    tst r16
    brne fail             ; Fail if Zero flag (Z) is cleared (should be 1)
    brmi fail             ; Fail if Negative flag (N) is set
    cpi r16, 0x00         ; Ensure value wasn't mutated
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Negative value (MSB set)
; Value = 0x80. Expect: Z=0, N=1, Value unchanged.
; ============================================================
test3:
    ldi r16, 0x80
    tst r16
    breq fail             ; Fail if Zero flag (Z) is set
    brpl fail             ; Fail if Negative flag (N) is cleared (should be 1)
    cpi r16, 0x80         ; Ensure value wasn't mutated
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Verify TST clears the Overflow (V) flag
; Set V manually, run TST, and check that V becomes 0.
; ============================================================
test4:
    ; Manually set V flag in SREG (Bit 3)
    in r16, SREG
    ori r16, 0x08         ; Set Bit 3
    out SREG, r16
    
    ; Run TST
    ldi r17, 0x11
    tst r17               ; This should force V to 0
    
    ; Verify V is cleared
    in r16, SREG
    sbrc r16, 3           ; Skip next instruction if Bit 3 (V) is 0
    rjmp fail             ; Fail if Bit 3 is still 1
    rcall inc_case

; ============================================================
; TEST 5: Verify S flag logic (S = N XOR V)
; Since V is cleared, S should equal N. With a negative 
; number, S should become 1.
; ============================================================
test5:
    ldi r17, 0xFF         ; Negative number
    tst r17               ; N=1, V=0  =>  S should be 1
    
    ; Verify S flag in SREG (Bit 4)
    in r16, SREG
    sbrs r16, 4           ; Skip next instruction if Bit 4 (S) is 1
    rjmp fail             ; Fail if Bit 4 is 0
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