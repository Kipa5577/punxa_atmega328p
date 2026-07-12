; ============================================================
; STD instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; STD Y+q, Rr / STD Z+q, Rr : Store byte from Rr to (Y/Z + q)
; Updates: None.
; ============================================================
; -------------------------
; SRAM variables
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ data_buffer  = 0x0200    ; Memory area to write into
.equ SPH = 0x3E
.equ SPL = 0x3D
; -------------------------
; Reset
; -------------------------
reset:
    ; Initialize stack pointer to 0x08FF (required before any RCALL/PUSH/POP)
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16

    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16
; ============================================================
; TEST 1: Store with Z pointer, 0 displacement
; ============================================================
test1:
    ldi r30, low(data_buffer)
    ldi r31, high(data_buffer)
    ldi r16, 0xAA
    std Z+0, r16          ; Store 0xAA at 0x0200
    lds r17, data_buffer  ; Verify via STS
    cpi r17, 0xAA
    brne fail
    rcall inc_case
; ============================================================
; TEST 2: Store with Z pointer, 1 displacement
; ============================================================
test2:
    ldi r30, low(data_buffer)
    ldi r31, high(data_buffer)
    ldi r16, 0x55
    std Z+1, r16          ; Store 0x55 at 0x0201
    lds r17, data_buffer + 1
    cpi r17, 0x55
    brne fail
    rcall inc_case
; ============================================================
; TEST 3: Store with Y pointer, displacement
; ============================================================
test3:
    ldi r28, low(data_buffer)
    ldi r29, high(data_buffer)
    ldi r16, 0xFF
    std Y+63, r16         ; Max displacement test (0x0200 + 63)
    lds r17, data_buffer + 63
    cpi r17, 0xFF
    brne fail
    rcall inc_case
; ============================================================
; TEST 4: Store from low register (r0)
; ============================================================
test4:
    ldi r30, low(data_buffer)
    ldi r31, high(data_buffer)
    ldi r16, 0x12          ; LDI can't target r0 directly; stage in r16
    mov r0, r16            ; then move into r0, the actual source under test
    std Z+2, r0
    lds r17, data_buffer + 2
    cpi r17, 0x12
    brne fail
    rcall inc_case
; ============================================================
; TEST 5: Verify Flags are not affected
; Operation that sets Zero flag, then perform STD
; ============================================================
test5:
    ldi r16, 0
    tst r16               ; Set Z flag
    ldi r17, 0x00
    std Z+3, r17          ; STD should not touch Z
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