; ============================================================
; PUSH (Push Register to Stack) test suite
; ============================================================
; Tests that PUSH correctly:
; 1. Writes data from register to memory at SP address
; 2. Decrements the Stack Pointer (SP)
; 3. Does not modify the source register
; 4. Does not modify status flags
; ============================================================
; PUSH is a 1-word (16-bit) instruction
; Format: 1001 001d dddd 1111
; Operation: STACK <- Rr; SP <- SP - 1
; ============================================================
.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D

reset:
    ; Initialize stack pointer to 0x08FF
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16
    rjmp test1_start

; ============================================================
; TEST 1: Basic PUSH and verification via direct memory access
; ============================================================
test1_start:
    ldi r16, 0x55
    push r16
    ; Verify stack memory: SP was at 0x08FF, now 0x08FE
    ; We manually check memory to ensure the write happened
    lds r17, 0x08FF
    cpi r17, 0x55
    brne fail
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: PUSH does not modify source register
; ============================================================
test2_start:
    ldi r16, 0xAA
    push r16
    cpi r16, 0xAA
    brne fail
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: PUSH decrements Stack Pointer
; ============================================================
test3_start:
    in r17, SPL     ; Read low byte of SP
    push r16
    in r18, SPL     ; Read again
    ; Compare: r18 should be r17 - 1
    subi r17, 1
    cp r17, r18
    brne fail
    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4: PUSH does not modify flags
; ============================================================
test4_start:
    ; Set Carry and Zero flags
    sec
    sez
    ldi r16, 0x01
    push r16
    ; Verify flags remain set
    brcc fail
    brne fail
    rcall inc_case
    rjmp test5_start

; ============================================================
; TEST 5: PUSH sequence (multiple registers)
; ============================================================
test5_start:
    ; Restore SP to a known value (0x08FF) so the hardcoded
    ; addresses checked below (0x08FE / 0x08FF) are valid.
    ; SP has drifted down from tests 1-4's pushes otherwise.
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16

    ldi r16, 0x11
    ldi r17, 0x22
    push r16
    push r17
    ; Stack top (0x08FE) should have 0x22, below (0x08FF) 0x11
    lds r18, 0x08FE
    cpi r18, 0x22
    brne fail
    lds r18, 0x08FF
    cpi r18, 0x11
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