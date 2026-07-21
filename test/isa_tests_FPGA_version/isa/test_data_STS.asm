; ============================================================
; STS (Store Direct to SRAM) test suite
; ============================================================
; AVR5-safe version (no R0 usage)
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ target_mem = 0x0850

reset:
    ldi r16, high(RAMEND)
    out 0x3E, r16        ; SPH (0x3E is standard for ATMega328P)
    ldi r16, low(RAMEND)
    out 0x3D, r16        ; SPL (0x3D is standard for ATMega328P)
    ; ---------------------------------------------
    
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16
    rjmp test1_start

; ============================================================
; TEST 1: Basic STS to a defined memory location
; ============================================================
test1_start:
    ldi r16, 0xAF
    sts target_mem, r16

    lds r17, target_mem
    cpi r17, 0xAF
    brne fail

    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: STS does not modify source register
; ============================================================
test2_start:
    ldi r16, 0x55
    sts target_mem, r16
    cpi r16, 0x55
    brne fail

    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: STS does not modify flags
; ============================================================
test3_start:
    sec
    sez

    ldi r16, 0x77
    sts target_mem, r16

    brcc fail
    brne fail

    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4: STS across different registers (NO R0 usage)
; ============================================================
test4_start:
    ldi r18, 0x11     ; was r0 (forbidden)
    ldi r31, 0xEE

    sts 0x0840, r18
    sts 0x0841, r31

    lds r16, 0x0840
    cpi r16, 0x11
    brne fail

    lds r16, 0x0841
    cpi r16, 0xEE
    brne fail

    rcall inc_case
    rjmp success

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
    ret