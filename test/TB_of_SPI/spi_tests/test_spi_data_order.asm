; ============================================================
; SPI Data Order (DORD) Test
; ============================================================
; DORD=0 (MSB-first) then DORD=1 (LSB-first). tb_spi.py's
; TEST_PEER_KWARGS gives the peer track_format=True for this file.
; Uses a non-bit-palindromic byte so a DORD mismatch would actually
; be observable (see spi_tests/test_spi_data_order.py for the same
; idea at the register-poke level).
; ============================================================

.equ SPCR = 0x2C
.equ SPSR = 0x2D
.equ SPDR = 0x2E

.equ SPE_BIT  = 6
.equ MSTR_BIT = 4
.equ DORD_BIT = 5
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
; MSB-first (DORD=0)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT)
    sts SPCR, r16
    ldi r20, 0b00010111
    rcall do_transfer_pair
    rcall inc_case

; ============================================================
; LSB-first (DORD=1)
; ============================================================
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT) | (1 << DORD_BIT)
    sts SPCR, r16
    ldi r20, 0b00010111
    rcall do_transfer_pair
    rcall inc_case

    rjmp success

; ============================================================
; do_transfer_pair: sends r20, then a dummy transfer, and confirms
; the echoed byte in SPDR matches r20 (the peer mirrors whatever
; DORD the DUT is currently using, so a correct round trip here
; doesn't by itself prove DORD changed anything -- see the Python
; suite's test_dord_actually_reverses_bit_order for that proof --
; but it does confirm the DUT's own shift logic is internally
; consistent for both settings). Trashes r16-r18.
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
