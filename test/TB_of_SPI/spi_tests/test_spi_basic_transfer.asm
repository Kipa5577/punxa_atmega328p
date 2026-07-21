; ============================================================
; SPI Basic Master Transfer Test
; ============================================================
; Validates a basic full-duplex SPI Master transfer: SPE=1,
; MSTR=1, Mode 0 (CPOL=0,CPHA=0), MSB-first, prescaler /4.
;
; PeerSPI (tb_spi.py) echoes every byte it receives back on the
; *next* transfer (one-transfer latency -- see peer_spi.py's
; docstring), so: transfer #1 sends 0xA5 (reply is whatever was
; queued before -- ignored), transfer #2 sends a dummy byte and
; should receive 0xA5 back in SPDR.
;
; Also checks the classic AVR SPIF clear sequence: read SPSR
; (with SPIF set), then access SPDR -- both halves required.
; ============================================================

.equ SPCR = 0x2C
.equ SPSR = 0x2D
.equ SPDR = 0x2E

.equ SPIE_BIT = 7
.equ SPE_BIT  = 6
.equ DORD_BIT = 5
.equ MSTR_BIT = 4
.equ CPOL_BIT = 3
.equ CPHA_BIT = 2

.equ SPIF_BIT = 7
.equ WCOL_BIT = 6

.equ test_case    = 0x0100
.equ final_result = 0x0101

.org 0x0000
reset:
    ldi r16, high(0x08FF)
    out 0x3E, r16          ; SPH
    ldi r16, low(0x08FF)
    out 0x3D, r16           ; SPL

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ; --- SPI config: SPE=1, MSTR=1, Mode 0, MSB-first, /4 ---
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT)
    sts SPCR, r16

; ============================================================
; TEST 1: first transfer (reply is a don't-care)
; ============================================================
    ldi r16, 0xA5
    sts SPDR, r16

wait_spif_1:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_spif_1

    ; SPIF is set. Access SPDR to complete the clear sequence
    ; before starting the next transfer (a fresh SPDR *write* also
    ; counts as the required SPDR access here).
    rcall inc_case

; ============================================================
; TEST 2: second transfer -- SPDR should now hold the peer's
; echo of the first byte (0xA5)
; ============================================================
    ldi r16, 0x00
    sts SPDR, r16

wait_spif_2:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_spif_2

    lds r18, SPDR
    cpi r18, 0xA5
    brne fail

    rcall inc_case

; ============================================================
; TEST 3: SPIF actually clears via read-SPSR-then-access-SPDR
; ============================================================
; Fresh transfer first -- test 2's own SPDR read (right after its
; SPSR-polling loop) already completed *that* clear sequence, so
; SPIF is already 0 by this point; a clean transfer is needed to
; observe the set->clear transition properly.
    ldi r16, 0x00
    sts SPDR, r16

wait_spif_3:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_spif_3

    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp fail                  ; should still be set (only armed the clear, not completed it yet)

    lds r19, SPDR               ; the "access SPDR" half of the clear sequence

    lds r17, SPSR
    sbrc r17, SPIF_BIT
    rjmp fail                   ; should be clear now

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
