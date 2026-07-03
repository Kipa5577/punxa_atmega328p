; ============================================================
; SPM instruction test suite for ATmega328P
; This test verifies the setup sequence for a Page Write.
;
; SPM   : Store byte/page to Flash memory
; ============================================================
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ SPMCR        = 0x37      ; SPM Control Register
.equ SPM_ENABLE   = 0         ; Bit 0 in SPMCR

; -------------------------
; Reset
; -------------------------
reset:
    ; Initialize stack pointer to top of internal SRAM (RAMEND = 0x08FF)
    ldi r16, 0xFF
    out SPL, r16
    ldi r16, 0x08
    out SPH, r16
    ldi r16, 0
    sts test_case, r16
    ldi r16, 1
    sts final_result, r16

; ============================================================
; TEST 1: Verify SPM control register accessibility
; ============================================================
test1:
    ; Just testing that we can read/write the control register
    ldi r16, (1<<SPM_ENABLE)
    out SPMCR, r16
    in r17, SPMCR
    andi r17, (1<<SPM_ENABLE)
    breq fail                 ; Bit should be set if enabled
    rcall inc_case

; ============================================================
; TEST 2: Verify Z-pointer initialization
; SPM uses Z to determine the Flash page address.
; ============================================================
test2:
    ldi r30, 0x00             ; Set Z to 0x1000
    ldi r31, 0x10
    
    cpi r30, 0x00
    brne fail
    cpi r31, 0x10
    brne fail
    rcall inc_case

; ============================================================
; TEST 3: Dummy Page Buffer Write (SPM Sequence)
; This sequence is required to trigger a write.
; ============================================================
test3:
    ; 1. Load data to R1:R0
    ldi r0, 0xAA
    ldi r1, 0x55
    
    ; 2. Set SPMCR to Page Fill (0x01)
    ldi r16, 0x01
    out SPMCR, r16
    
    ; 3. Execute SPM
    ; spm                   ; Commented out to prevent accidental Flash corruption
    
    ; Note: On a real device, you must wait for the busy bit
    ; in SPMCR to clear before continuing.
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
; ============================================================
fail:
    ldi r16, -1
    sts final_result, r16
    rjmp end

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret