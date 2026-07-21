; ============================================================
; LPM instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; LPM Rd, Z   : Load byte from Flash at address Z into Rd
; Updates: None.
; ============================================================

; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101

; -------------------------
; Entry Vector
; -------------------------
.org 0x0000                   ; Explicitly start code execution at 0x0000
    rjmp reset

reset:
    ; --- Initialize Stack Pointer ---
    ldi r16, low(RAMEND)
    out SPL, r16
    ldi r16, high(RAMEND)
    out SPH, r16

    ; --- Original init code ---
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Load first byte from Flash
; ============================================================
test1:
    ldi r30, low(test_data * 2) ; Byte address = word address * 2
    ldi r31, high(test_data * 2)
    lpm r16, Z
    
    cpi r16, 0xAA
    breq t1_ok
    rjmp fail
t1_ok:
    rcall inc_case

; ============================================================
; TEST 2: Load second byte from Flash
; ============================================================
test2:
    ldi r30, low(test_data * 2 + 1)
    ldi r31, high(test_data * 2 + 1)
    lpm r16, Z
    
    cpi r16, 0x55
    breq t2_ok
    rjmp fail
t2_ok:
    rcall inc_case

; ============================================================
; TEST 3: Load third byte (0xFF)
; ============================================================
test3:
    ldi r30, low(test_data * 2 + 2)
    ldi r31, high(test_data * 2 + 2)
    lpm r16, Z
    
    cpi r16, 0xFF
    breq t3_ok
    rjmp fail
t3_ok:
    rcall inc_case

; ============================================================
; TEST 4: Verify Flags are not affected
; Set Zero flag, execute LPM, check if Z flag is still set.
; ============================================================
test4:
    ldi r16, 0
    tst r16               ; Set Z flag
    
    ldi r30, low(test_data * 2)
    ldi r31, high(test_data * 2)
    lpm r16, Z            ; LPM should not change Z
    
    breq t4_ok            ; If Z is set, skip fail
    rjmp fail
t4_ok:
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

; ============================================================
; Flash Data
; ============================================================
.org 0x0100                   ; Data safely stored away from code flow
test_data:
.db 0xAA, 0x55, 0xFF, 0x00