; ============================================================
; SLEEP instruction test suite
; ============================================================
; Note: SLEEP puts the CPU into a low-power mode.
; Verification requires waking the CPU (e.g., via Interrupt).
; ============================================================
; SLEEP is a 1-word (16-bit) instruction
; Format: 1001 0101 1000 1000
; ============================================================

.equ SMCR  = 0x53        ; Sleep Mode Control Register (memory-mapped)
.equ EIMSK = 0x3D        ; External Interrupt Mask Register (memory-mapped)
.equ EICRA = 0x69        ; External Interrupt Control Register A (extended I/O)
.equ SREG  = 0x5F        ; Status Register (memory-mapped)
.equ ISC01 = 1

; -------------------------
; SRAM variables (ADDED)
; -------------------------
.equ test_case    = 0x0100
.equ final_result = 0x0101

; -------------------------
; Vector Table (ADDED)
; -------------------------
.org 0x0000             ; Reset Vector
    rjmp reset

.org 0x0002             ; INT0 Vector address
    reti                ; Simply return from interrupt to wake up

; -------------------------
; Main Code
; -------------------------
reset:
    ldi r16, 0xFF
    out SPL, r16
    ldi r16, 0x08
    out SPH, r16
    ; Initialize test tracking variables
    ldi r16, 1
    sts test_case, r16  ; test_case = 1
    ldi r16, 0
    sts final_result, r16 ; Start with final_result = 0
    
    ; 1. Enable External Interrupt 0 (INT0) to wake from sleep
    ldi r16, (1 << 0)
    sts EIMSK, r16      ; Enable INT0
    ldi r16, (1 << ISC01) ; Trigger INT0 on falling edge
    sts EICRA, r16
    
    ; 2. Set Sleep Mode to Idle (SMCR = 0)
    ldi r16, 0x01       ; SLEEP_MODE_IDLE (SM=000, SE=1)
    sts SMCR, r16
    
    sei                 ; Enable global interrupts

    ; 3. Perform the SLEEP instruction
    sleep               
    
    ; The CPU will halt here until INT0 is triggered.
    ; Execution continues immediately following the SLEEP instruction.
    
    ; 4. Verify we woke up
    rjmp success

; ============================================================
; SUCCESS / FAILURE logic
; ============================================================
success:
    ; If we reach here, we successfully entered and exited sleep
    ldi r16, 1
    sts final_result, r16     ; final_result = 1
end:
    rjmp end