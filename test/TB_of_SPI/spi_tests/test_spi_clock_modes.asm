; ============================================================
; SPI Clock Modes Test (Mode 0..3)
; ============================================================
; Sweeps all four CPOL/CPHA combinations. tb_spi.py's
; TEST_PEER_KWARGS gives the peer track_format=True for this file,
; so it always follows the DUT's live CPOL/CPHA/DORD -- see
; peer_spi.py's docstring.
;
; Each mode: configure SPCR, transfer a byte, transfer a dummy,
; verify the peer's one-transfer-delayed echo comes back correctly.
; ============================================================

.equ SPCR = 0x2C
.equ SPSR = 0x2D
.equ SPDR = 0x2E

.equ SPE_BIT  = 6
.equ MSTR_BIT = 4
.equ CPOL_BIT = 3
.equ CPHA_BIT = 2
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
; MODE 0 (CPOL=0, CPHA=0)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT)
    sts SPCR, r16
    ldi r20, 0x11
    rcall do_transfer_pair
    rcall inc_case

; ============================================================
; MODE 1 (CPOL=0, CPHA=1)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT) | (1 << CPHA_BIT)
    sts SPCR, r16
    ldi r20, 0x22
    rcall do_transfer_pair
    rcall inc_case

; ============================================================
; MODE 2 (CPOL=1, CPHA=0)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT) | (1 << CPOL_BIT)
    sts SPCR, r16
    ldi r20, 0x33
    rcall do_transfer_pair
    rcall inc_case

; ============================================================
; MODE 3 (CPOL=1, CPHA=1)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT) | (1 << CPOL_BIT) | (1 << CPHA_BIT)
    sts SPCR, r16
    ldi r20, 0x44
    rcall do_transfer_pair
    rcall inc_case

    rjmp success

; ============================================================
; do_transfer_pair: sends r20 as the first transfer, then a dummy
; transfer, and confirms the echoed byte in SPDR matches r20.
; Trashes r16-r18. Jumps to `fail` on mismatch.
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
