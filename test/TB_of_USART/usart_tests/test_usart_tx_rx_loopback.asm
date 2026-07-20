; ============================================================
; USART0 TX/RX loopback test suite
; ============================================================
; Run via tb_usart.py (python -i tb_usart.py, then runAllTests()
; or runTest('test_usart_tx_rx_loopback.asm')).
;
; Assumes the harness's default PeerUART config: UBRR0=10, 8N1, no
; parity, echo=True (every byte the peer receives off TXD is queued
; straight back out on RXD) -- so a plain TX-then-poll-RX-then-compare
; sequence is enough to self-check purely through CPU-visible state,
; the same test_case/final_result convention every other test in this
; project uses.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ UDRE0_BIT = 5
.equ RXC0_BIT  = 7
.equ TXC0_BIT  = 6

.equ test_case = 0x0100
.equ final_result = 0x0101
.equ rx_byte = 0x0102

reset:
    ldi r16, high(0x08FF)
    out 0x3E, r16          ; SPH
    ldi r16, low(0x08FF)
    out 0x3D, r16          ; SPL

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ; --- USART0 config: UBRR0=10, 8N1, TXEN0+RXEN0 ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    ldi r16, 0x06           ; async, no parity, 1 stop, 8 data bits
    sts UCSR0C, r16
    ldi r16, 0x18           ; RXEN0 | TXEN0
    sts UCSR0B, r16

    rjmp test1_start

; ============================================================
; TEST 1: single byte round trip (0x41 'A')
; ============================================================
test1_start:
wait_udre_1:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp wait_udre_1

    ldi r16, 0x41
    sts UDR0, r16

wait_rxc_1:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_1

    lds r17, UDR0
    cpi r17, 0x41
    breq usart_ok_1
    rjmp fail
usart_ok_1:

    rcall inc_case

; ============================================================
; TEST 2: three bytes back-to-back, verify order preserved
; ============================================================
test2_start:
    ldi r18, 0x11           ; first byte to send
    rcall send_byte
    ldi r18, 0x22
    rcall send_byte
    ldi r18, 0x33
    rcall send_byte

    rcall recv_byte          ; -> r17
    cpi r17, 0x11
    breq usart_ok_2
    rjmp fail
usart_ok_2:

    rcall recv_byte
    cpi r17, 0x22
    breq usart_ok_3
    rjmp fail
usart_ok_3:

    rcall recv_byte
    cpi r17, 0x33
    breq usart_ok_4
    rjmp fail
usart_ok_4:

    rcall inc_case

; ============================================================
; TEST 3: TXC0 sets after the last frame finishes, and clears when
; software writes a 1 to it.
; ============================================================
test3_start:
    lds r16, UCSR0A
    ldi r17, (1 << TXC0_BIT)
    sts UCSR0A, r17          ; clear TXC0 first (write-1-to-clear)

    ldi r18, 0x55
    rcall send_byte

wait_txc_3:
    lds r16, UCSR0A
    sbrs r16, TXC0_BIT
    rjmp wait_txc_3

    ; consume the echoed byte so it doesn't interfere with anything else
    rcall recv_byte
    cpi r17, 0x55
    breq usart_ok_5
    rjmp fail
usart_ok_5:

    ; clear TXC0 and confirm it actually cleared
    ldi r17, (1 << TXC0_BIT)
    sts UCSR0A, r17
    lds r16, UCSR0A
    sbrc r16, TXC0_BIT
    rjmp fail

    rcall inc_case
    rjmp success

; ============================================================
; Helpers
; ============================================================
send_byte:                   ; byte to send in r18
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp send_byte
    sts UDR0, r18
    ret

recv_byte:                   ; returns received byte in r17
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp recv_byte
    lds r17, UDR0
    ret

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
