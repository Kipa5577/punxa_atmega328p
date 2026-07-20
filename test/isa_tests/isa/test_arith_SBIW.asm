; ============================================================
; SBIW (Subtract Immediate from Word) test suite
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D

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
; TEST 1: Simple 16-bit subtraction
; Y = 0x0100, Y - 1 = 0x00FF
; ============================================================
test1:
    ldi r28, 0x00           ; YL
    ldi r29, 0x01           ; YH
    sbiw r28, 1             ; Subtract 1 from Y-pair

    cpi r28, 0xFF
    brne fail
    cpi r29, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Subtracting maximum immediate (63)
; Z = 0x0064 (100), 100 - 63 = 37 (0x25)
; ============================================================
test2:
    ldi r30, 0x64           ; ZL
    ldi r31, 0x00           ; ZH
    sbiw r30, 63            ; Subtract 63

    cpi r30, 0x25
    brne fail
    cpi r31, 0x00
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Zero check
; X = 0x000A, X - 10 = 0
; ============================================================
test3:
    ldi r26, 10             ; XL
    ldi r27, 0              ; XH
    sbiw r26, 10
    
    ; Should set the Zero flag
    brne fail
    cpi r26, 0
    brne fail
    cpi r27, 0
    brne fail
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
    ret