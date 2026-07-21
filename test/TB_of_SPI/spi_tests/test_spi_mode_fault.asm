; ============================================================
; SPI Mode Fault Test
; ============================================================
; Configures Master mode, then sends a sentinel byte (0xF0) to the
; peer. tb_spi.py's _driver_mode_fault (see TEST_DRIVERS) recognizes
; that byte and, instead of echoing it, pulls the DUT's own !SS
; input low for a few ticks -- simulating another master grabbing
; the bus. The DUT should react by clearing MSTR and setting SPIF
; (see SPI.py's SS_logic).
; ============================================================

.equ SPCR = 0x2C
.equ SPSR = 0x2D
.equ SPDR = 0x2E

.equ SPE_BIT  = 6
.equ MSTR_BIT = 4
.equ SPIF_BIT = 7

.equ test_case    = 0x0100
.equ final_result = 0x0101

.org 0x0000
reset:
    ldi r16, high(0x08FF)
    out 0x3E, r16
    ldi r16, low(0x08FF)
    out 0x3D, r16

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT)
    sts SPCR, r16

; ============================================================
; TEST 1: send the sentinel byte that triggers the peer's
; mode-fault driver
; ============================================================
    ldi r16, 0xF0
    sts SPDR, r16
wait_sentinel:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_sentinel

    rcall inc_case

; ============================================================
; TEST 2: give the peer's already-armed !SS pulse (queued the
; moment it decoded the sentinel byte) a chance to actually reach
; the DUT and register as a mode fault, then confirm MSTR cleared
; and SPIF set. Deliberately does NOT touch SPDR here -- SPDR was
; already loaded with the sentinel byte during TEST 1's own
; SPSR-polling loop (which armed the flag-clear sequence), so any
; further SPDR access right now would clear SPIF before it's been
; checked, without a fresh transfer ever being able to set it again
; (MSTR is 0 by this point, and a disabled/non-master SPDR write
; doesn't start one).
; ============================================================
    ldi r18, low(50)
    ldi r19, high(50)
mf_delay_loop:
    subi r18, 1
    sbci r19, 0
    brne mf_delay_loop

    lds r18, SPCR
    sbrc r18, MSTR_BIT
    rjmp fail                  ; MSTR should have been cleared by the fault

    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp fail                  ; SPIF should be set (from the sentinel transfer and/or the fault)

    rcall inc_case
    rjmp success

; ============================================================
; Helpers
; ============================================================
inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret

; ============================================================
; SUCCESS / FAILURE
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
