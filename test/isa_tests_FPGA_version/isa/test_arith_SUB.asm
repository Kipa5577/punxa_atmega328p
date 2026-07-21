; ============================================================
; SUB instruction test suite for ATmega328P (Fixed Flag Validation)
; SUB Rd, Rr  ->  Rd = Rd - Rr
;
; SREG Bit Map Reference:
;   Bit 7: I (Interrupt)
;   Bit 6: T (Bit Copy)
;   Bit 5: H (Half Carry)
;   Bit 4: S (Sign Bit, N XOR V)
;   Bit 3: V (Two's Complement Overflow)
;   Bit 2: N (Negative)
;   Bit 1: Z (Zero)
;   Bit 0: C (Carry)
; ============================================================

; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SREG         = 0x3F
.equ SPH          = 0x3E
.equ SPL          = 0x3D

; -------------------------
; Reset
; -------------------------
reset:
    ; init stack
    ldi r16, 0x03
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16
    ; init state
    ldi r16, 1
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: simple subtraction, positive result
; 30 - 10 = 20
; Expected SUB Flags: C=0, Z=0, N=0, V=0, S=0, H=0
; ============================================================
test1:
    ldi r16, 30
    ldi r17, 10
    sub r16, r17    
    in r15, SREG    ; Capture pristine SUB flags before CPI alters them

    ; -- Validate Math Result --
    cpi r16, 20
    brne fail1      ; Fail if math result is not exactly 20

    ; -- Validate Saved Flags (r15) --
    sbrc r15, 0     ; Skip if C (bit 0) is 0. Fail if C=1 (no unsigned borrow)
    rjmp fail1
    sbrc r15, 1     ; Skip if Z (bit 1) is 0. Fail if Z=1 (result is not zero)
    rjmp fail1
    sbrc r15, 2     ; Skip if N (bit 2) is 0. Fail if N=1 (result is positive)
    rjmp fail1
    sbrc r15, 3     ; Skip if V (bit 3) is 0. Fail if V=1 (no signed overflow)
    rjmp fail1
    sbrc r15, 4     ; Skip if S (bit 4) is 0. Fail if S=1 (N^V = 0)
    rjmp fail1
    sbrc r15, 5     ; Skip if H (bit 5) is 0. Fail if H=1 (no low nibble borrow)
    rjmp fail1

    rcall inc_case
    rjmp test2
fail1: 
    jmp fail

; ============================================================
; TEST 2: result is zero
; 42 - 42 = 0
; Expected SUB Flags: C=0, Z=1, N=0, V=0, S=0, H=0
; ============================================================
test2:
    ldi r16, 42
    ldi r17, 42
    
    ; Perform the operation
    sub r16, r17
    in r15, SREG

    ; -- Validate Math Result --
    cpi r16, 0
    brne fail2      ; Fail if math result is not exactly 0

    ; -- Validate Saved Flags (r15) --
    sbrc r15, 0     ; Skip if C is 0. Fail if C=1 (no borrow needed)
    rjmp fail2
    sbrs r15, 1     ; Skip if Z is 1. Fail if Z=0 (result IS zero, Z must be 1)
    rjmp fail2
    sbrc r15, 2     ; Skip if N is 0. Fail if N=1 (0 is not negative)
    rjmp fail2
    sbrc r15, 3     ; Skip if V is 0. Fail if V=1 (cannot overflow)
    rjmp fail2
    sbrc r15, 4     ; Skip if S is 0. Fail if S=1 (N^V = 0)
    rjmp fail2
    sbrc r15, 5     ; Skip if H is 0. Fail if H=1 (low nibbles match)
    rjmp fail2

    rcall inc_case
    rjmp test3

fail2: 
    jmp fail

; ============================================================
; TEST 3: unsigned borrow, carry set
; 10 - 20 = 246 (mod 256)
; Expected SUB Flags: C=1, Z=0, N=1, V=0, S=1, H=0
; ============================================================
test3:
    ldi r16, 10
    ldi r17, 20
    
    ; Perform the operation
    sub r16, r17
    in r15, SREG

    ; -- Validate Math Result --
    cpi r16, 246
    brne fail3      ; Fail if wraparound math result is not 246 (0xF6)

    ; -- Validate Saved Flags (r15) --
    sbrs r15, 0     ; Skip if C is 1. Fail if C=0 (10 < 20 requires an unsigned borrow)
    rjmp fail3
    sbrc r15, 1     ; Skip if Z is 0. Fail if Z=1 (246 != 0)
    rjmp fail3
    sbrs r15, 2     ; Skip if N is 1. Fail if N=0 (0xF6 has MSB=1, must be negative)
    rjmp fail3
    sbrc r15, 3     ; Skip if V is 0. Fail if V=1 (pos - pos staying within bounds is normal)
    rjmp fail3
    sbrs r15, 4     ; Skip if S is 1. Fail if S=0 (N^V = 1^0 = 1)
    rjmp fail3
    sbrc r15, 5     ; Skip if H is 0. Fail if H=1 (low nibble 0 >= 0, no lower borrow)
    rjmp fail3

    rcall inc_case
    rjmp test4

fail3: 
    jmp fail

; ============================================================
; TEST 4: half-carry (borrow from bit 3)
; 0x10 - 0x01 = 0x0F
; Expected SUB Flags: C=0, Z=0, N=0, V=0, S=0, H=1
; ============================================================
test4:
    ldi r16, 0x10
    ldi r17, 0x01
    
    ; Perform the operation
    sub r16, r17
    in r15, SREG

    ; -- Validate Math Result --
    cpi r16, 0x0F
    brne fail4      ; Fail if math result is not 0x0F

    ; -- Validate Saved Flags (r15) --
    sbrc r15, 0     ; Skip if C is 0. Fail if C=1 (0x10 >= 0x01 overall)
    rjmp fail4
    sbrc r15, 1     ; Skip if Z is 0. Fail if Z=1 (0x0F != 0)
    rjmp fail4
    sbrc r15, 2     ; Skip if N is 0. Fail if N=1 (MSB of 0x0F is 0)
    rjmp fail4
    sbrc r15, 3     ; Skip if V is 0. Fail if V=1 (no signed overflow)
    rjmp fail4
    sbrc r15, 4     ; Skip if S is 0. Fail if S=1 (N^V = 0)
    rjmp fail4
    sbrs r15, 5     ; Skip if H is 1. Fail if H=0 (low nibble 0 minus 1 forces a nibble borrow)
    rjmp fail4

    rcall inc_case
    rjmp test5

fail4:
    jmp fail

; ============================================================
; TEST 5: signed overflow, positive - negative = negative
; 0x70 (112) - 0x90 (-112 signed) = 0xE0 (-32 signed)
; Expected SUB Flags: C=1, Z=0, N=1, V=1, S=0, H=0
; ============================================================
test5:
    ldi r16, 0x70
    ldi r17, 0x90
    
    ; Perform the operation
    sub r16, r17
    in r15, SREG

    ; -- Validate Math Result --
    cpi r16, 0xE0
    brne fail5      ; Fail if math result is not 0xE0

    ; -- Validate Saved Flags (r15) --
    sbrs r15, 0     ; Skip if C is 1. Fail if C=0 (0x70 < 0x90 unsigned)
    rjmp fail5
    sbrc r15, 1     ; Skip if Z is 0. Fail if Z=1 (0xE0 != 0)
    rjmp fail5
    sbrs r15, 2     ; Skip if N is 1. Fail if N=0 (0xE0 has MSB=1)
    rjmp fail5
    sbrs r15, 3     ; Skip if V is 1. Fail if V=0 (pos - neg = neg is a signed overflow!)
    rjmp fail5
    sbrc r15, 4     ; Skip if S is 0. Fail if S=1 (N^V = 1^1 = 0)
    rjmp fail5
    sbrc r15, 5     ; Skip if H is 0. Fail if H=1 (low nibble 0 - 0 = 0)
    rjmp fail5

    rcall inc_case
    rjmp test6

fail5:
    jmp fail

; ============================================================
; TEST 6: signed overflow, negative - positive = positive
; 0x80 (-128) - 0x01 (1) = 0x7F (127)
; Expected SUB Flags: C=0, Z=0, N=0, V=1, S=1, H=1
; ============================================================
test6:
    ldi r16, 0x80
    ldi r17, 0x01
    
    ; Perform the operation
    sub r16, r17
    in r15, SREG

    ; -- Validate Math Result --
    cpi r16, 0x7F
    brne fail6      ; Fail if math result is not 0x7F

    ; -- Validate Saved Flags (r15) --
    sbrc r15, 0     ; Skip if C is 0. Fail if C=1 (0x80 >= 0x01 unsigned)
    rjmp fail6
    sbrc r15, 1     ; Skip if Z is 0. Fail if Z=1 (0x7F != 0)
    rjmp fail6
    sbrc r15, 2     ; Skip if N is 0. Fail if N=1 (0x7F has MSB=0)
    rjmp fail6
    sbrs r15, 3     ; Skip if V is 1. Fail if V=0 (neg - pos = pos is a signed overflow!)
    rjmp fail6
    sbrs r15, 4     ; Skip if S is 1. Fail if S=0 (N^V = 0^1 = 1)
    rjmp fail6
    sbrs r15, 5     ; Skip if H is 0. Fail if H=1 (Evaluated macro-state has H clean)
    rjmp fail6

    rcall inc_case
    rjmp test7

fail6: 
    jmp fail

; ============================================================
; TEST 7: subtract from self (all ones scenario)
; 0xFF - 0xFF = 0
; Expected SUB Flags: C=0, Z=1, N=0, V=0, S=0, H=0
; ============================================================
test7:
    ldi r16, 0xFF
    ldi r17, 0xFF
    
    ; Perform the operation
    sub r16, r17
    in r15, SREG

    ; -- Validate Math Result --
    cpi r16, 0
    brne fail7      ; Fail if math result is not exactly 0

    ; -- Validate Saved Flags (r15) --
    sbrc r15, 0     ; Skip if C is 0. Fail if C=1
    rjmp fail7
    sbrs r15, 1     ; Skip if Z is 1. Fail if Z=0
    rjmp fail7
    sbrc r15, 2     ; Skip if N is 0. Fail if N=1
    rjmp fail7
    sbrc r15, 3     ; Skip if V is 0. Fail if V=1
    rjmp fail7
    sbrc r15, 4     ; Skip if S is 0. Fail if S=1
    rjmp fail7
    sbrc r15, 5     ; Skip if H is 0. Fail if H=1
    rjmp fail7

    rcall inc_case
    rjmp test8

fail7: 
    jmp fail

; ============================================================
; TEST 8: half-carry with borrow chain
; 0x20 - 0x19 = 0x07
; Expected SUB Flags: C=0, Z=0, N=0, V=0, S=0, H=1
; ============================================================
test8:
    ldi r16, 0x20
    ldi r17, 0x19
    
    ; Perform the operation
    sub r16, r17
    in r15, SREG

    ; -- Validate Math Result --
    cpi r16, 0x07
    brne fail8      ; Fail if math result is not 0x07

    ; -- Validate Saved Flags (r15) --
    sbrc r15, 0     ; Skip if C is 0. Fail if C=1 (0x20 >= 0x19 overall)
    rjmp fail8
    sbrc r15, 1     ; Skip if Z is 0. Fail if Z=1 (0x07 != 0)
    rjmp fail8
    sbrc r15, 2     ; Skip if N is 0. Fail if N=1 (MSB of 0x07 is 0)
    rjmp fail8
    sbrc r15, 3     ; Skip if V is 0. Fail if V=1
    rjmp fail8
    sbrc r15, 4     ; Skip if S is 0. Fail if S=1
    rjmp fail8
    sbrs r15, 5     ; Skip if H is 1. Fail if H=0 (low nibble 0 minus 9 requires a borrow)
    rjmp fail8

    rcall inc_case
    rjmp success

fail8: 
    jmp fail

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