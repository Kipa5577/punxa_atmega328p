; ============================================================
; SPI Write Collision (WCOL) Test
; ============================================================
; Uses a slow prescaler (/128) so there's a wide window to hit
; mid-transfer, writes SPDR again immediately (no wait), and
; confirms WCOL sets and the in-flight byte (not the colliding
; write) is what the peer actually received.
; ============================================================

.equ SPCR = 0x2C
.equ SPSR = 0x2D
.equ SPDR = 0x2E

.equ SPE_BIT  = 6
.equ MSTR_BIT = 4
.equ SPIF_BIT = 7
.equ WCOL_BIT = 6

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

    ; SPE=1, MSTR=1, SPR1:0=11 (/128, slowest -- generous mid-transfer window)
    ldi r16, (1 << SPE_BIT) | (1 << MSTR_BIT) | 3
    sts SPCR, r16

; ============================================================
; TEST 1: start a transfer, immediately write again -> WCOL
; ============================================================
    ldi r16, 0x42
    sts SPDR, r16

    ldi r16, 0x99
    sts SPDR, r16          ; collides -- should be discarded, WCOL set

    lds r17, SPSR
    sbrs r17, WCOL_BIT
    rjmp fail

    rcall inc_case

; ============================================================
; TEST 2: wait for the (uncorrupted) transfer to finish, confirm
; the byte the peer got back matches the ORIGINAL write (0x42),
; not the colliding one (0x99) -- checked by transferring a dummy
; next and reading back the peer's echo.
; ============================================================
wait_wcol_done:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_wcol_done

    ldi r16, 0x00
    sts SPDR, r16
wait_echo:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_echo

    lds r18, SPDR
    cpi r18, 0x42
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
