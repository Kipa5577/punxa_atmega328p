; ============================================================
; CLN (Clear Negative Flag) test suite (TRAMPOLINE SAFE)
; ============================================================

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ SPH = 0x3E
.equ SPL = 0x3D
.equ SREG_ADDR = 0x3F    ; Changed to standard I/O address for safety
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
; TEST 1-2: CLN basic operation
; ============================================================

test1_start:
    sen
    cln
    brpl n_clear1
    rjmp fail
n_clear1:
    rcall inc_case
    rjmp test2_start

test2_start:
    cln
    cln
    brpl n_still_clear2
    rjmp fail
n_still_clear2:
    rcall inc_case
    rjmp test3_start

; ============================================================
; TEST 3: Flag preservation
; ============================================================

test3_start:
    sei
    set
    seh
    sev
    sez
    sec
    sen
    cln

    brpl t3_ok1
    rjmp fail
t3_ok1:

    brbs 7, t3_ok2       ; FIXED: brie does not exist natively
    rjmp fail
t3_ok2:

    brts t3_ok3
    rjmp fail
t3_ok3:

    brhs t3_ok4
    rjmp fail
t3_ok4:

    brvs t3_ok5
    rjmp fail
t3_ok5:

    breq t3_ok6
    rjmp fail
t3_ok6:

    brcs t3_ok7
    rjmp fail
t3_ok7:

    rcall inc_case
    rjmp test4_start

; ============================================================
; TEST 4-7: No side effects
; ============================================================

test4_start:
    ldi r16, 0xAA
    ldi r17, 0xBB
    cln

    cpi r16, 0xAA
    breq t4_ok1
    rjmp fail
t4_ok1:

    cpi r17, 0xBB
    breq t4_ok2
    rjmp fail
t4_ok2:

    rcall inc_case
    rjmp test5_start

test5_start:
    ldi r16, 0xDE
    sts 0x0200, r16
    cln
    lds r17, 0x0200

    cpi r17, 0xDE
    breq t5_ok
    rjmp fail
t5_ok:

    rcall inc_case
    rjmp test6_start

test6_start:
    ldi r16, 0xAD
    out GPIOR0, r16
    cln
    in r17, GPIOR0

    cpi r17, 0xAD
    breq t6_ok
    rjmp fail
t6_ok:

    rcall inc_case
    rjmp test7_start

test7_start:
    in r16, SPL
    in r17, SPH
    cln
    cln
    cln

    in r18, SPL
    in r19, SPH

    cp r16, r18
    breq t7_ok1
    rjmp fail
t7_ok1:

    cp r17, r19
    breq t7_ok2
    rjmp fail
t7_ok2:

    rcall inc_case
    rjmp test8_start

; ============================================================
; TEST 8-12: Logic and Flow
; ============================================================

test8_start:
    ldi r16, 0
    cln
    inc r16
    cln
    inc r16
    cln
    inc r16

    cpi r16, 3
    breq t8_ok
    rjmp fail
t8_ok:

    rcall inc_case
    rjmp test9_start

test9_start:
    cls                  ; FIXED: Explicitly clear S flag
    clv
    sen
    cln                  ; CLN does not recalculate S
    brge t9_ok1          ; Checks S == 0 (Validates CLN didn't alter S)
    rjmp fail
t9_ok1:

    ses                  ; FIXED: Explicitly set S flag
    sev
    sen
    cln                  ; CLN does not recalculate S
    brlt t9_ok2          ; Checks S == 1 (Validates CLN didn't alter S)
    rjmp fail
t9_ok2:

    rcall inc_case
    rjmp test10_start

test10_start:
    sen
    cln
    cln
    cln

    brpl t10_ok
    rjmp fail
t10_ok:

    rcall inc_case
    rjmp test11_start

test11_start:
    sen
    cln
    sen

    brmi t11_ok
    rjmp fail
t11_ok:

    rcall inc_case
    rjmp test12_start

test12_start:
    ldi r16, 0x80
    ldi r17, 0x01
    add r16, r17

    ; FIXED: Do ALU logic first so it doesn't overwrite our test
    cpi r16, 0x81
    breq t12_ok1
    rjmp fail
t12_ok1:

    sen                  ; Force N = 1
    cln                  ; Now test CLN
    brpl t12_ok2         ; Verify N = 0
    rjmp fail
t12_ok2:

    rcall inc_case
    rjmp test13_start

; ============================================================
; TEST 13-16: Advanced Scenarios
; ============================================================

test13_start:
    sen
    rcall cln_sub13

    brpl t13_ok
    rjmp fail
t13_ok:

    rcall inc_case
    rjmp test14_start

cln_sub13:
    cln
    ret

test14_start:
    sen
    cln
    sen
    cln

    brpl t14_ok
    rjmp fail
t14_ok:

    rcall inc_case
    rjmp test15_start

test15_start:
    ldi r16, 3
    ldi r17, 5
    sub r16, r17
    cln

    brpl t15_ok
    rjmp fail
t15_ok:

    rcall inc_case
    rjmp test16_start

test16_start:
    clv
    cln

    brvc t16_ok1
    rjmp fail
t16_ok1:

    sev
    cln

    brvs t16_ok2
    rjmp fail
t16_ok2:

    rcall inc_case
    rjmp success

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

inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret