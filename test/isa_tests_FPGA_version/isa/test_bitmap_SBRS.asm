; ============================================================
; SBRS (Skip if Bit in Register Set) test suite
; ============================================================
.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ; Initialize stack pointer
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16

    ; Initialize state
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    rjmp test1

; ============================================================
; TEST 1: Skip when bit is 1
; ============================================================
test1:
    ldi r17, 1              ; Bit 0 is 1
    sbrs r17, 0             ; If bit 0 is 1, skip the next instruction
    rjmp fail               ; This should be skipped
    rcall inc_case
    rjmp test2

; ============================================================
; TEST 2: Do NOT skip when bit is 0
; ============================================================
test2:
    ldi r17, 0xFE           ; Bit 0 is 0
    sbrs r17, 0             ; Bit is 0, so do NOT skip
    rjmp test2_continue     ; Should execute this
    rjmp fail               ; If it skips, we land here (Fail)
test2_continue:
    rcall inc_case
    rjmp test3

; ============================================================
; TEST 3: Check multiple bits (Bit 7)
; ============================================================
test3:
    ldi r17, 0x80           ; Bit 7 is 1
    sbrs r17, 7             ; Skip if 1
    rjmp fail
    rcall inc_case
    rjmp test4

; ============================================================
; TEST 4: Bit manipulation interaction
; ============================================================
test4:
    ldi r17, 0x00
    ori r17, 0x10         ; Set bit 4 (R17 is now 0x10)
    sbrs r17, 4             ; Bit 4 is 1, so skip
    rjmp fail
    rcall inc_case
    rjmp success

; ============================================================
; SUCCESS / FAILURE logic
; ============================================================
success:
    ldi r16, 1
    sts final_result, r16
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

end:
    rjmp end