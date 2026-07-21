; ============================================================
; SBR instruction test suite for ATmega328P
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16

    ldi r16, 1
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Identity
; 0x55 SBR 0x00 = 0x55
; ============================================================
test1:
    ldi r16, 0x55
    sbr r16, 0x00

    cpi r16, 0x55
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Set all bits
; 0x33 SBR 0xFF = 0xFF
; ============================================================
test2:
    ldi r16, 0x33
    sbr r16, 0xFF

    cpi r16, 0xFF
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Partial bit setting
; 0xA0 SBR 0x0A = 0xAA
; ============================================================
test3:
    ldi r16, 0xA0
    sbr r16, 0x0A

    cpi r16, 0xAA
    brne fail
    rcall inc_case

; ============================================================
; TEST 4: Bits already set
; 0xF0 SBR 0x30 = 0xF0
; ============================================================
test4:
    ldi r16, 0xF0
    sbr r16, 0x30

    cpi r16, 0xF0
    brne fail
    rcall inc_case

; ============================================================
; TEST 5: General mixed case
; 0x42 SBR 0x24 = 0x66
; ============================================================
test5:
    ldi r16, 0x42
    sbr r16, 0x24

    cpi r16, 0x66
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