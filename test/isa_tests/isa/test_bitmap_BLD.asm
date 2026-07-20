; ============================================================
; BLD (Bit Load) instruction test suite
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ stack_start = 0x08FF
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
; TEST 1: Load 1 into Bit 0
; T flag must be set to 1 first
; ============================================================
test1:
    set                 ; Set T flag to 1
    ldi r16, 0x00
    bld r16, 0          ; Copy T (1) into Bit 0 of R16
                        ; R16 should now be 0x01

    cpi r16, 0x01
    brne fail
    rcall inc_case

; ============================================================
; TEST 2: Load 0 into Bit 7
; T flag must be cleared to 0 first
; ============================================================
test2:
    clt                 ; Clear T flag to 0
    ldi r16, 0xFF
    bld r16, 7          ; Copy T (0) into Bit 7 of R16
                        ; R16 should now be 0x7F

    cpi r16, 0x7F
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Preserve other bits (ensure no corruption)
; 0xAA (10101010), load 1 into bit 0
; ============================================================
test3:
    set                 ; Set T flag to 1
    ldi r16, 0xAA       ; 10101010
    bld r16, 0          ; Load T into bit 0 -> 10101011 (0xAB)

    cpi r16, 0xAB
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