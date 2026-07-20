; ============================================================
; BREAK instruction test suite
; ============================================================
; Note: This test verifies that the CPU treats BREAK as a 
; NOP when no debugger is attached.
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101

reset:
    ldi r16, 0xFF
    out SPL, r16
    ldi r16, 0x08
    out SPH, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16
    rjmp test1_start

; ============================================================
; TEST 1: Verify BREAK acts as NOP (no hang/crash)
; ============================================================
test1_start:
    ldi r16, 0xAA
    
    ; The BREAK instruction:
    break
    
    ; If no debugger is present, the CPU will simply 
    ; continue to the next instruction.
    cpi r16, 0xAA
    brne fail           ; Should still be 0xAA
    
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