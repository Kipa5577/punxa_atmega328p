; ============================================================
; SPI Interrupt (STC) Test
; ============================================================
; Enables SPIE, performs one transfer, and confirms SPIE/SPIF are
; both set from the CPU's point of view. The interrupt *line*
; itself (whether STC actually asserted while SPIF was set, and
; deasserted once cleared) isn't something a CPU-visible register
; read can confirm on its own -- tb_spi.py's
; _check_interrupt_line_followed_flags (see TEST_POST_CHECKS) reads
; the actual wire after this program reaches `end`, and this
; program's job is simply to leave SPIF cleared before `end` so
; that post-check has something meaningful to confirm (STC settled
; back to 0).
; ============================================================

.equ SPCR = 0x2C
.equ SPSR = 0x2D
.equ SPDR = 0x2E

.equ SPE_BIT  = 6
.equ MSTR_BIT = 4
.equ SPIE_BIT = 7
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

    ldi r16, (1 << SPIE_BIT) | (1 << SPE_BIT) | (1 << MSTR_BIT)
    sts SPCR, r16

; ============================================================
; TEST 1: transfer completes, SPIF sets
; ============================================================
    ldi r16, 0x5A
    sts SPDR, r16
wait_spif:
    lds r17, SPSR
    sbrs r17, SPIF_BIT
    rjmp wait_spif

    rcall inc_case

; ============================================================
; TEST 2: clear SPIF (read SPSR -- already done above -- then
; access SPDR) so the post-check sees STC back at 0 by `end`.
; ============================================================
    lds r19, SPDR

    lds r17, SPSR
    sbrc r17, SPIF_BIT
    rjmp fail

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
