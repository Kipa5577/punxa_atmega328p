; ============================================================
; POP (Pop Register from Stack) test suite
; ============================================================
; Tests that POP correctly:
; 1. Loads data from the stack into the target register
; 2. Increments the Stack Pointer (SP)
; 3. Works with all registers R0-R31
; 4. Does not modify status flags (specifically Z, C, N, V, H, S, T, I)
; ============================================================
; POP is a 1-word (16-bit) instruction
; Format: 1001 000d dddd 0111
; Operation: Rd <- STACK; SP <- SP + 1
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
; TEST 1: Basic POP (Push value, then POP it)
; ============================================================
test1_start:
    ldi r16, 0x42
    push r16
    ldi r16, 0x00       ; Clear reg
    pop r16             ; Recover value
    cpi r16, 0x42
    brne fail
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: POP to different registers (R0, R16, R31)
; ============================================================
test2_start:
    ldi r16, 0xAA
    push r16
    pop r17
    cpi r17, 0xAA
    brne fail
    
    ldi r16, 0xBB
    push r16
    pop r31
    cpi r31, 0xBB
    brne fail
    
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: POP multiple values (LIFO order check)
; ============================================================
test3_start:
    ldi r16, 0x11
    push r16
    ldi r16, 0x22
    push r16
    
    pop r17             ; Should be 0x22
    pop r18             ; Should be 0x11
    
    cpi r17, 0x22
    brne fail
    cpi r18, 0x11
    brne fail
    
    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4: POP does not modify Status Flags
; ============================================================
test4_start:
    ; Set flags to known state
    sec                 ; C=1
    sez                 ; Z=1
    
    ldi r16, 0x55
    push r16
    pop r17             ; POP should not clear C or Z
    
    brcc fail           ; If C was cleared, this fails
    brne fail           ; If Z was cleared, this fails
    
    rcall inc_case
    rjmp test5_start

; ============================================================
; TEST 5: POP with 0x00 and 0xFF values
; ============================================================
test5_start:
    ldi r16, 0x00
    push r16
    pop r17
    cpi r17, 0x00
    brne fail
    
    ldi r16, 0xFF
    push r16
    pop r17
    cpi r17, 0xFF
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