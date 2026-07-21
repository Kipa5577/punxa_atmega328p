; ============================================================
; MUL (Multiply) instruction test suite for ATmega328P
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
; TEST 1: Simple multiplication
; 10 * 5 = 50 (0x32)
; ============================================================
test1:
    ldi r16, 10
    ldi r17, 5
    mul r16, r17            ; Result in R1:R0

    ; Workaround for CPI limitation:
    mov r16, r0             ; Copy result to high register
    cpi r16, 50             ; Now we can use CPI
    brne fail
    
    mov r16, r1             ; Copy high byte to high register
    cpi r16, 0
    brne fail
    
    rcall inc_case
    rjmp test2

; ============================================================
; TEST 2: Identity (Multiplication by 1)
; 200 * 1 = 200 (0xC8)
; ============================================================
test2:
    ldi r16, 200
    ldi r17, 1
    mul r16, r17

    ; Result is in R1:R0. Must move to R16+ to use CPI.
    mov r18, r0
    cpi r18, 200            ; Now works: R18 is >= R16
    brne fail
    
    mov r18, r1
    cpi r18, 0
    brne fail
    rcall inc_case
    rjmp test3
    
; ============================================================
; TEST 3: Multiplication by 0
; 123 * 0 = 0
; ============================================================
test3:
    ldi r16, 123
    ldi r17, 0
    mul r16, r17

    mov r18, r0
    cpi r18, 0
    brne fail
    
    mov r18, r1
    cpi r18, 0
    brne fail
    rcall inc_case
    rjmp test4

; ============================================================
; TEST 4: Max range (255 * 255 = 65025)
; 0xFF * 0xFF = 0xFE01
; ============================================================
test4:
    ldi r16, 255
    ldi r17, 255
    mul r16, r17

    mov r16, r0
    cpi r16, 0x01           ; Low byte
    brne fail
    
    mov r16, r1
    cpi r16, 0xFE           ; High byte
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