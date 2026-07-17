; ============================================================
; USART0 Baud Rate Sweep Test
; ============================================================
; Validates the 12-bit UBRR0 register across extreme boundaries 
; to ensure the baud rate generator scales correctly.
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - The harness must dynamically track or auto-baud the changes
;   in communication speed. The AVR changes UBRR0 after every
;   successfully echoed byte.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ RXC0_BIT  = 7
.equ TXC0_BIT  = 6
.equ UDRE0_BIT = 5

.equ test_case    = 0x0100
.equ final_result = 0x0101

.org 0x0000
reset:
    ldi r16, high(0x08FF)
    out 0x3E, r16          ; SPH
    ldi r16, low(0x08FF)
    out 0x3D, r16          ; SPL

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ; --- Base USART0 Config: 8N1 ---[cite: 1]
    ldi r16, 0x06           
    sts UCSR0C, r16
    ldi r16, 0x18           ; Enable RX and TX
    sts UCSR0B, r16

    rjmp test_baud_max

; ============================================================
; TEST 1: Maximum Speed (UBRR0 = 0)
; ============================================================
test_baud_max:
    ldi r16, 0
    sts UBRR0H, r16
    sts UBRR0L, r16

    ldi r18, 0x11
    rcall send_and_verify_byte

; ============================================================
; TEST 2: Standard Speed (UBRR0 = 10)
; ============================================================
test_baud_std:
    ldi r16, 0
    sts UBRR0H, r16
    ldi r16, 10
    sts UBRR0L, r16

    ldi r18, 0x22
    rcall send_and_verify_byte

; ============================================================
; TEST 3: 8-Bit Boundary (UBRR0 = 255)
; ============================================================
test_baud_8bit_bound:
    ldi r16, 0
    sts UBRR0H, r16
    ldi r16, 255
    sts UBRR0L, r16

    ldi r18, 0x33
    rcall send_and_verify_byte

; ============================================================
; TEST 4: Minimum Speed / 12-Bit Maximum (UBRR0 = 4095 / 0x0FFF)
; ============================================================
test_baud_min:
    ldi r16, 0x0F          ; High nibble
    sts UBRR0H, r16
    ldi r16, 0xFF          ; Low byte
    sts UBRR0L, r16

    ldi r18, 0x44
    rcall send_and_verify_byte

    rjmp success

; ============================================================
; Core Loopback Helper
; ============================================================
send_and_verify_byte:
wait_udre:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp wait_udre

    ; Clear TXC0 before sending to ensure we can wait on it safely
    ldi r16, (1 << TXC0_BIT)
    sts UCSR0A, r16

    ; Transmit
    sts UDR0, r18

wait_rxc:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc

    ; Verify the received byte[cite: 1]
    lds r17, UDR0
    cp r17, r18
    brne fail

    ; MUST wait for transmission to completely finish before 
    ; returning so the next test can safely alter the baud rate.
wait_txc_safe:
    lds r16, UCSR0A
    sbrs r16, TXC0_BIT
    rjmp wait_txc_safe

    rcall inc_case
    ret

; ============================================================
; Framework Mechanics[cite: 1]
; ============================================================
inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret

success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end

fail:
    ldi r16, 255
    sts final_result, r16
    rjmp end