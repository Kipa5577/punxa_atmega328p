; ============================================================
; CLR instruction test suite for ATmega328P
; test_case      -> SRAM location tracking current test
; final_result   -> 1 = OK, -1 = FAIL
;
; CLR Rd  :  Rd = 0   (Effectively EOR Rd, Rd)
; Works on ALL registers r0..r31
; Updates: Z (Set), N (Cleared), V (Cleared), S (Cleared).
; ============================================================
; -------------------------
; SRAM variables & Defines
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ SPH          = 0x3E
.equ SPL          = 0x3D
.equ SREG         = 0x3F
; -------------------------
; Reset
; -------------------------
reset:
; init stack
    ldi r16, 0x08
    out SPH, r16
    ldi r16, 0xFF
    out SPL, r16
; init state
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Clear a positive non-zero value
; r16 = 0x55 -> CLR -> r16 = 0x00
; ============================================================
test1:
    ldi r16, 0x55
    clr r16
    cpi r16, 0x00
    breq skip_1
    rjmp fail
skip_1:
    rcall inc_case

; ============================================================
; TEST 2: Clear a negative value (MSB set)
; r16 = 0xFF -> CLR -> r16 = 0x00
; ============================================================
test2:
    ldi r16, 0xFF
    clr r16
    cpi r16, 0x00
    breq skip_2
    rjmp fail
skip_2:
    rcall inc_case

; ============================================================
; TEST 3: Clear an already zero value
; r16 = 0x00 -> CLR -> r16 = 0x00
; ============================================================
test3:
    ldi r16, 0x00
    clr r16
    cpi r16, 0x00
    breq skip_3
    rjmp fail
skip_3:
    rcall inc_case

; ============================================================
; TEST 4: Verify Zero (Z) flag is set and Negative (N) is cleared
; ============================================================
test4:
    ldi r16, 0xAA
    clr r16
    brne fail             ; Fail if Zero flag (Z) is NOT set
    brmi fail             ; Fail if Negative flag (N) IS set
    rcall inc_case

; ============================================================
; TEST 5: Verify Overflow (V) flag is cleared
; Set V manually, run CLR, check that V becomes 0.
; ============================================================
test5:
    ; Manually set V flag in SREG (Bit 3)
    in r16, SREG
    ori r16, 0x08         ; Set Bit 3
    out SREG, r16
    
    ; Run CLR
    ldi r17, 0x11
    clr r17               ; This should force V to 0
    
    ; Verify V is cleared
    in r16, SREG
    sbrc r16, 3           ; Skip next instruction if Bit 3 (V) is 0
    rjmp fail             ; Fail if Bit 3 is still 1
    rcall inc_case

; ============================================================
; TEST 6: Test on a lower register (r0)
; Unlike SBCI/ANDI/ORI, CLR works on r0-r15.
; ============================================================
test6:
    ; We can't use LDI on r0, so we copy a value into it
    ldi r16, 0x77
    mov r0, r16           ; r0 = 0x77
    
    clr r0                ; r0 should now be 0x00
    
    ; We can't use CPI on r0 either, so we move it back to r16 to check
    mov r16, r0
    cpi r16, 0x00
    breq skip_6
    rjmp fail
skip_6:
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
; final_result = -1, stop execution
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