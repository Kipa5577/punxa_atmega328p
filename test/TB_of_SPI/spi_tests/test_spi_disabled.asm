; ============================================================
; SPI Disabled (SPE=0) Test
; ============================================================
; With SPE=0, writing SPDR should just load the register (no
; transfer, no SCK activity, SPIF never sets). Confirmed via a
; bounded polling loop (a counted delay, not an unbounded wait --
; unbounded would hang forever if this were ever wrong) followed by
; checking SPIF is still clear and SPDR still holds what was written.
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

    ; MSTR=1 but SPE=0 -- disabled.
    ldi r16, (1 << MSTR_BIT)
    sts SPCR, r16

    ldi r16, 0xAA
    sts SPDR, r16

    ; Bounded busy-wait standing in for "give it plenty of time to
    ; have started a transfer, if it were going to" -- 100 iterations
    ; of a decrementing 16-bit counter, comfortably more than the
    ; ~34 cycles/bit-edge a real (enabled) /4-prescaler transfer would
    ; need, without needlessly stretching out this (slow, simulated)
    ; multicycle CPU's runtime.
    ldi r18, low(100)
    ldi r19, high(100)
delay_loop:
    subi r18, 1
    sbci r19, 0
    brne delay_loop

; ============================================================
; TEST 1: SPIF must still be clear
; ============================================================
    lds r17, SPSR
    sbrc r17, SPIF_BIT
    rjmp fail

    rcall inc_case

; ============================================================
; TEST 2: SPDR must still read back exactly what was written
; ============================================================
    lds r18, SPDR
    cpi r18, 0xAA
    brne fail

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
