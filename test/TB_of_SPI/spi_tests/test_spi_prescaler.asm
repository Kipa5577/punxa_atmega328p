; ============================================================
; SPI Prescaler Sweep Test
; ============================================================
; Sweeps all 4 SPR1:0 combinations (SPI2X left at 0), confirming a
; transfer completes correctly (SPIF sets, correct byte echoed
; back) at every speed. Timing itself (that slower settings take
; genuinely longer) is covered at the register-poke level by
; spi_tests/test_spi_prescaler_timing.py -- this is the CPU-driven
; functional-correctness companion.
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

; ============================================================
; SPR1:0 = 00 (/4)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT)
    sts SPCR, r16
    ldi r20, 0x91
    rcall do_transfer_pair
    rcall inc_case

; ============================================================
; SPR1:0 = 01 (/16)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT) | 1
    sts SPCR, r16
    ldi r20, 0x92
    rcall do_transfer_pair
    rcall inc_case

; ============================================================
; SPR1:0 = 10 (/64)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT) | 2
    sts SPCR, r16
    ldi r20, 0x93
    rcall do_transfer_pair
    rcall inc_case

; ============================================================
; SPR1:0 = 11 (/128)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT) | 3
    sts SPCR, r16
    ldi r20, 0x94
    rcall do_transfer_pair
    rcall inc_case

    rjmp success

; ============================================================
; do_transfer_pair: sends r20, then a dummy transfer, and confirms
; the echoed byte in SPDR matches r20. Trashes r16-r18.
; ============================================================
do_transfer_pair:
    mov r16, r20
    sts SPDR, r16
wait_dtp_1:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_dtp_1

    ldi r16, 0x00
    sts SPDR, r16
wait_dtp_2:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_dtp_2

    lds r18, SPDR
    cp r18, r20
    brne fail
    ret

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
