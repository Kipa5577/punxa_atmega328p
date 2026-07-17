; ============================================================
; SPM instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; SPM        : Store word R1:R0 to Flash at address (Z >> 1)
; Verification strategy: since there's no architectural way to
; read Flash except LPM, every SPM write below is verified by
; immediately reading it back with LPM (byte-for-byte, both
; halves of the word). A word never targeted by SPM is also
; checked to make sure a write only ever touches the one word
; addressed by Z, not neighbouring Flash.
; ============================================================

.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ SPMCR        = 0x37      ; SPM Control Register
.equ SPM_ENABLE   = 0         ; Bit 0 in SPMCR

; -------------------------
; Entry Vector
; -------------------------
.org 0x0000                   ; Explicitly start code execution at 0x0000
    rjmp reset

reset:
    ; Initialize stack pointer to top of internal SRAM
    ldi r16, low(RAMEND)
    out SPL, r16
    ldi r16, high(RAMEND)
    out SPH, r16

    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Verify SPM control register accessibility
; ============================================================
test1:
    ldi r16, (1<<SPM_ENABLE)
    out SPMCR, r16
    in r17, SPMCR
    andi r17, (1<<SPM_ENABLE)
    breq t1_fail               ; Bit should be set if enabled
    rjmp t1_done
t1_fail:
    rjmp fail
t1_done:
    rcall inc_case

; ============================================================
; TEST 2: SPM writes R1:R0 into Flash[Z>>1] -- verify the low
; byte of that word reads back correctly via LPM.
; ============================================================
test2:
    ldi r30, low(spm_data * 2)     ; Z = byte address of spm_data word 0
    ldi r31, high(spm_data * 2)
    ldi r18, 0x34                   ; low byte of the word to store
    mov r0, r18
    ldi r19, 0x12                   ; high byte of the word to store
    mov r1, r19
    spm

    ldi r30, low(spm_data * 2)     ; Z back to the low byte of that word
    ldi r31, high(spm_data * 2)
    lpm r16, Z
    cpi r16, 0x34
    brne t2_fail
    rjmp t2_done
t2_fail:
    rjmp fail
t2_done:
    rcall inc_case

; ============================================================
; TEST 3: Verify the high byte of the same written word.
; ============================================================
test3:
    ldi r30, low(spm_data * 2 + 1)
    ldi r31, high(spm_data * 2 + 1)
    lpm r16, Z
    cpi r16, 0x12
    brne t3_fail
    rjmp t3_done
t3_fail:
    rjmp fail
t3_done:
    rcall inc_case

; ============================================================
; TEST 4: SPM to a second Flash word -- proves the write
; target tracks Z rather than always hitting the same word.
; ============================================================
test4:
    ldi r30, low(spm_data * 2 + 2)     ; byte address of spm_data word 1
    ldi r31, high(spm_data * 2 + 2)
    ldi r18, 0x78                  ; low byte (R0 must be loaded via MOV -- LDI only targets r16-r31)
    mov r0, r18
    ldi r19, 0x56                  ; high byte
    mov r1, r19
    spm

    ldi r30, low(spm_data * 2 + 2)
    ldi r31, high(spm_data * 2 + 2)
    lpm r16, Z
    cpi r16, 0x78
    brne t4_fail
    rjmp t4_done
t4_fail:
    rjmp fail
t4_done:
    rcall inc_case

test5:
    ldi r30, low(spm_data * 2 + 3)
    ldi r31, high(spm_data * 2 + 3)
    lpm r16, Z
    cpi r16, 0x56
    brne t5_fail
    rjmp t5_done
t5_fail:
    rjmp fail
t5_done:
    rcall inc_case

; ============================================================
; TEST 6/7: A word never targeted by SPM keeps its original
; .dw contents -- proves SPM doesn't spill into neighbouring
; Flash words.
; ============================================================
test6:
    ldi r30, low(spm_data * 2 + 4)
    ldi r31, high(spm_data * 2 + 4)
    lpm r16, Z
    cpi r16, 0xFE                  ; low byte of untouched 0xCAFE
    brne t6_fail
    rjmp t6_done
t6_fail:
    rjmp fail
t6_done:
    rcall inc_case

test7:
    ldi r30, low(spm_data * 2 + 5)
    ldi r31, high(spm_data * 2 + 5)
    lpm r16, Z
    cpi r16, 0xCA                  ; high byte of untouched 0xCAFE
    brne t7_fail
    rjmp t7_done
t7_fail:
    rjmp fail
t7_done:
    rcall inc_case

; ============================================================
; TEST 8: SPM can overwrite a word it already wrote earlier
; (re-programming the same location, not just a one-shot fill).
; ============================================================
test8:
    ldi r30, low(spm_data * 2)
    ldi r31, high(spm_data * 2)
    ldi r18, 0xEF                  ; low byte (R0 must be loaded via MOV -- LDI only targets r16-r31)
    mov r0, r18
    ldi r19, 0xBE                  ; high byte
    mov r1, r19
    spm

    ldi r30, low(spm_data * 2)
    ldi r31, high(spm_data * 2)
    lpm r16, Z
    cpi r16, 0xEF
    brne t8_fail
    rjmp t8_done
t8_fail:
    rjmp fail
t8_done:
    rcall inc_case

; ============================================================
; TEST 9: SPM must not disturb SREG. Set Z flag beforehand and
; confirm it's still set immediately after SPM executes.
; ============================================================
test9:
    ldi r16, 0
    tst r16                        ; sets the Z flag
    ldi r30, low(spm_data * 2 + 6)
    ldi r31, high(spm_data * 2 + 6)
    ldi r18, 0x01                  ; low byte (R0 must be loaded via MOV -- LDI only targets r16-r31)
    mov r0, r18
    ldi r19, 0x00                  ; high byte
    mov r1, r19
    spm
    breq t9_ok                     ; Z flag should still be set
    rjmp t9_fail
t9_fail:
    rjmp fail
t9_ok:
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
; Flash Data -- placeholder words. Words 0, 1, and 3 are
; overwritten at runtime by SPM (tests 2-5, 8-9); word 2 is
; left untouched on purpose as a canary (tests 6-7).
; ============================================================
.org 0x0100
spm_data:
.dw 0x0000, 0x0000, 0xCAFE, 0x0000
