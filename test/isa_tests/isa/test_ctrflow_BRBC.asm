; ============================================================
; BRBC (Branch if Bit Cleared) test suite
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
    sts final_result, r16

; ============================================================
; TEST 1: Branch if Zero Flag is Cleared (Z=0)
; ============================================================
test1:
    ; Set Z flag to 0 by adding 1 to 0
    ldi r16, 0
    inc r16             ; Result is 1, so Z=0
    
    brbc 1, branch1_ok  ; If Z is 0, branch to label
    rjmp fail
branch1_ok:
    rcall inc_case

; ============================================================
; TEST 2: Do NOT Branch if Zero Flag is Set (Z=1)
; ============================================================
test2:
    ; Set Z flag to 1 by clearing r16
    ldi r16, 0
    ; A simple way to set Z=1 without affecting other logic
    tst r16             ; Sets Z flag
    
    brbc 1, fail        ; If Z=1, this should NOT branch
    rcall inc_case

; ============================================================
; TEST 3: Branch if Carry Flag is Cleared (C=0)
; ============================================================
test3:
    ; Clear Carry flag
    clc                 ; C = 0
    
    brbc 0, branch3_ok  ; If C=0, branch
    rjmp fail
branch3_ok:
    rcall inc_case

; ============================================================
; TEST 4: Branch if Negative Flag is Cleared (N=0)
; ============================================================
test4:
    ; Clear N flag
    ldi r16, 0x01
    tst r16             ; N=0 (because bit 7 is 0)
    
    brbc 2, branch4_ok  ; If N=0, branch
    rjmp fail
branch4_ok:
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