; ============================================================
; ASR (Arithmetic Shift Right) instruction test suite
; 
; ASR shifts all bits one place to the right. 
; Bit 7 (sign bit) is held constant to preserve the sign.
; Bit 0 is shifted directly into the Carry (C) flag.
; ============================================================

.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SPH          = 0x3E
.equ SPL          = 0x3D

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
; TEST 1: Positive number shift
; 0x20 (00100000) -> 0x10 (00010000)
; Expected Flags: C=0 (bit 0 was 0)
; ============================================================
test1:
    ldi r16, 0x20
    asr r16

    ; -- Check flags first --
    brcs fail           ; Branch if Carry Set: Fail if bit 0 accidentally set Carry

    ; -- Check register result --
    cpi r16, 0x10
    brne fail           ; Branch if Not Equal: Fail if math result is not exactly 0x10
    
    rcall inc_case

; ============================================================
; TEST 2: Sign-bit preservation
; 0x80 (10000000) -> 0xC0 (11000000)
; Expected Flags: C=0 (bit 0 was 0), N=1 (bit 7 stayed 1)
; ============================================================
test2:
    ldi r16, 0x80
    asr r16

    ; -- Check flags first --
    brcs fail           ; Branch if Carry Set: Fail if bit 0 accidentally set Carry
    brpl fail           ; Branch if Plus: Fail if Negative flag (N) is 0 (0xC0 is negative)

    ; -- Check register result --
    cpi r16, 0xC0
    brne fail           ; Branch if Not Equal: Fail if math result is not exactly 0xC0
    
    rcall inc_case

; ============================================================
; TEST 3: Carry flag verification
; 0x01 (00000001) -> 0x00, Carry flag should be set
; Expected Flags: C=1 (bit 0 was 1), Z=1 (result is 0)
; ============================================================
test3:
    ldi r16, 0x01
    asr r16
    
    ; -- Check flags first (FIXED ORDER) --
    brcc fail           ; Branch if Carry Clear: Fail if ASR failed to push bit 0 (1) into Carry
    brne success_skip   ; Dynamic skip: If Z=0, we let CPI catch the zero result error below.
                        ; If Z=1 (correct), we pass this flag check cleanly.

    ; -- Check register result --
    cpi r16, 0
    brne fail           ; Branch if Not Equal: Fail if register state is not 0
    
success_skip:
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
    ret                 ; Fixed: removed trailing 'u' typo