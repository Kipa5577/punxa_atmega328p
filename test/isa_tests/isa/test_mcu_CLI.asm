; ============================================================
; CLI (Clear Global Interrupt Flag) test suite with trampolines
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D
.equ SREG_ADDR = 0x3F      ; FIXED: I/O memory address instead of SRAM address
.equ GPIOR0 = 0x1E

reset:
    ldi r16, high(0x08FF)
    out SPH, r16
    ldi r16, low(0x08FF)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16
    rjmp test1_start

; ============================================================
; TEST 1: CLI clears the I flag
; ============================================================
test1_start:
    sei
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp i_clear1
    rjmp fail
i_clear1:
    rcall inc_case
    rjmp test2_start

; ============================================================
; TEST 2: CLI has no effect when I already 0
; ============================================================
test2_start:
    cli
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp i_still_clear2
    rjmp fail
i_still_clear2:
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: CLI preserves other SREG flags
; ============================================================
test3_start:
    cli
    sec
    sez
    sen
    sev
    seh
    set
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp i_ok3
    rjmp fail

i_ok3:
    brcs test3_c_ok
    rjmp fail
test3_c_ok:

    breq test3_z_ok
    rjmp fail
test3_z_ok:

    brmi test3_n_ok        ; FIXED: Branch if Minus (N=1)
    rjmp fail
test3_n_ok:

    brvs test3_v_ok        ; FIXED: Branch if Overflow Set (V=1)
    rjmp fail
test3_v_ok:

    brhs test3_h_ok
    rjmp fail
test3_h_ok:

    brts test3_t_ok
    rjmp fail
test3_t_ok:

    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4-6: No side effects on registers/memory/IO
; ============================================================
test4_start:
    ldi r16, 0xAA
    ldi r17, 0xBB
    ldi r18, 0xCC
    ldi r19, 0xDD
    cli

    cpi r16, 0xAA
    breq test4_r16_ok
    rjmp fail
test4_r16_ok:

    cpi r17, 0xBB
    breq test4_r17_ok
    rjmp fail
test4_r17_ok:

    cpi r18, 0xCC
    breq test4_r18_ok
    rjmp fail
test4_r18_ok:

    cpi r19, 0xDD
    breq test4_r19_ok
    rjmp fail
test4_r19_ok:

    rcall inc_case
    rjmp test5_start

test5_start:
    ldi r16, 0xDE
    sts 0x0200, r16
    cli
    lds r17, 0x0200

    cpi r17, 0xDE
    breq test5_ok
    rjmp fail
test5_ok:

    rcall inc_case
    rjmp test6_start

test6_start:
    ldi r16, 0xAD
    out GPIOR0, r16
    cli
    in r17, GPIOR0

    cpi r17, 0xAD
    breq test6_ok
    rjmp fail
test6_ok:

    rcall inc_case
    rjmp test7_start

; ============================================================
; TEST 7: No effect on Stack Pointer
; ============================================================
test7_start:
    in r16, SPL
    in r17, SPH
    cli
    cli
    cli
    in r18, SPL
    in r19, SPH

    cp r16, r18
    breq test7_spl_ok
    rjmp fail
test7_spl_ok:

    cp r17, r19
    breq test7_sph_ok
    rjmp fail
test7_sph_ok:

    rcall inc_case
    rjmp test8_start

; ============================================================
; TEST 8-12: Interrupt masking and toggling
; ============================================================
test8_start:
    sei
    cli
    ldi r16, 0x55
    in r18, SREG_ADDR
    sbrs r18, 7
    rjmp critical_ok8
    rjmp fail
critical_ok8:
    rcall inc_case
    rjmp test9_start

test9_start:
    cli
    sei
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp final_clear9
    rjmp fail
final_clear9:
    rcall inc_case
    rjmp test10_start

test10_start:
    sei
    cli
    cli
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp multi_clear_ok10
    rjmp fail
multi_clear_ok10:
    rcall inc_case
    rjmp test11_start

test11_start:
    ldi r16, 0
    cli
    inc r16
    cli
    inc r16
    cli
    inc r16

    cpi r16, 3
    breq test11_ok
    rjmp fail
test11_ok:

    rcall inc_case
    rjmp test12_start

test12_start:
    sei
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp masked_ok12
    rjmp fail
masked_ok12:
    rcall inc_case
    rjmp test13_start

; ============================================================
; TEST 13-16: Arithmetic and Flag preservation
; ============================================================
test13_start:
    ldi r16, 0x7F
    ldi r17, 0x01
    add r16, r17
    cli

    brmi n_ok13
    rjmp fail
n_ok13:

    brvs v_ok13
    rjmp fail
v_ok13:

    brcc c_ok13
    rjmp fail
c_ok13:

    brne z_ok13
    rjmp fail
z_ok13:

    brhs h_ok13
    rjmp fail
h_ok13:

    rcall inc_case
    rjmp test14_start

test14_start:
    sei
    rcall cli_sub14
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp sub_ok14
    rjmp fail
sub_ok14:
    rcall inc_case
    rjmp test15_start

cli_sub14:
    cli
    ret

test15_start:
    sei
    push r16
    cli
    pop r16
    in r17, SREG_ADDR
    sbrs r17, 7
    rjmp pop_no_restore15
    rjmp fail
pop_no_restore15:
    rcall inc_case
    rjmp test16_start

test16_start:
    cli
    nop
    sei
    nop
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp toggle_ok16
    rjmp fail
toggle_ok16:
    rcall inc_case
    rjmp test17_start

; ============================================================
; TEST 17-20: Final verification
; ============================================================
test17_start:
    sei
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp encode_ok17
    rjmp fail
encode_ok17:
    rcall inc_case
    rjmp test18_start

test18_start:
    sei
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp isr_masked18
    rjmp fail
isr_masked18:
    rcall inc_case
    rjmp test19_start

test19_start:
    sei
    cli
    in r16, SREG_ADDR
    sbrs r16, 7
    rjmp sleep_ok19
    rjmp fail
sleep_ok19:
    rcall inc_case
    rjmp test20_start

test20_start:
    cli
    ldi r16, 0xF0
    tst r16
    cli

    brlt s_ok20
    rjmp fail
s_ok20:

    ldi r16, 0x10
    tst r16
    cli

    brge s_zero_ok20
    rjmp fail
s_zero_ok20:

    rcall inc_case
    rjmp success

; ============================================================
; SUCCESS / FAILURE logic
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

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret