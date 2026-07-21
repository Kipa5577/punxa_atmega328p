; ============================================================
; ADD instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
; ============================================================


; -------------------------
; SRAM variables
; -------------------------
.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

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
    ldi r16, 0
    sts test_case, r16

    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: simple addition
; 10 + 20 = 30
; ============================================================
test1:
    ldi r16, 10
    ldi r17, 20
    add r16, r17              ; r16 = 30

    cpi r16, 30
    brne fail

    rcall inc_case

; ============================================================
; TEST 2: zero identity
; 55 + 0 = 55
; ============================================================
test2:
    ldi r16, 55
    ldi r17, 0
    add r16, r17

    cpi r16, 55
    brne fail

    rcall inc_case

; ============================================================
; TEST 3: overflow wrap-around
; 200 + 100 = 44 (mod 256)
; ============================================================
test3:
    ldi r16, 200
    ldi r17, 100
    add r16, r17

    cpi r16, 44
    brne fail

    rcall inc_case

; ============================================================
; TEST 4: maximum unsigned overflow
; 255 + 1 = 0
; ============================================================
test4:
    ldi r16, 255
    ldi r17, 1
    add r16, r17

    cpi r16, 0
    brne fail

    rcall inc_case

; ============================================================
; TEST 5: carry generation check (value correctness only)
; 128 + 128 = 0
; ============================================================
test5:
    ldi r16, 128
    ldi r17, 128
    add r16, r17

    cpi r16, 0
    brne fail

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