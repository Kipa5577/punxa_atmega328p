; ============================================================
; LDD instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; LDD Rd, Y+q / LDD Rd, Z+q : Load byte from (Y/Z + q)
; Updates: None.
; ============================================================
; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ data_block   = 0x0200    ; Starting point for test data
.equ SPH          = 0x3E
.equ SPL          = 0x3D
; -------------------------
; Reset
; -------------------------
reset:
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16

    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16
; Initialize some data at 0x0200 for testing
    ldi r16, 0xAA
    sts data_block + 0, r16
    ldi r16, 0x55
    sts data_block + 1, r16
    ldi r16, 0xFF
    sts data_block + 5, r16
; ============================================================
; TEST 1: Load with Z pointer, 0 displacement
; ============================================================
test1:
    ldi r30, low(data_block)
    ldi r31, high(data_block)
    ldd r16, Z+0          ; Should load 0xAA
    cpi r16, 0xAA
    brne fail
    rcall inc_case
; ============================================================
; TEST 2: Load with Z pointer, 1 displacement
; ============================================================
test2:
    ldi r30, low(data_block)
    ldi r31, high(data_block)
    ldd r16, Z+1          ; Should load 0x55
    cpi r16, 0x55
    brne fail
    rcall inc_case
; ============================================================
; TEST 3: Load with Y pointer
; ============================================================
test3:
    ldi r28, low(data_block)
    ldi r29, high(data_block)
    ldd r16, Y+5          ; Should load 0xFF
    cpi r16, 0xFF
    brne fail
    rcall inc_case
; ============================================================
; TEST 4: Load to low register (r0)
; ============================================================
test4:
    ldi r30, low(data_block)
    ldi r31, high(data_block)
    ldd r0, Z+0           ; Should load 0xAA into r0
                           ; CPI only works on r16+, so use mov/cpi
    mov r16, r0
    cpi r16, 0xAA
    brne fail
    rcall inc_case
; ============================================================
; TEST 5: Verify Flags are not affected
; Operation that sets Zero flag, then perform LDD
; ============================================================
test5:
    ldi r16, 0
    tst r16               ; Set Z flag
    ldd r17, Z+0          ; LDD should not touch Z
    brne fail             ; If Z was cleared, this fails
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
    ldi r16, 0xFF
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