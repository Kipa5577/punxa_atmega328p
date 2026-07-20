; ============================================================
; USART0 Dynamic Baud Rate Change Test
; ============================================================
; Validates that changing UBRR0 mid-execution correctly updates
; the internal baud rate generator without requiring a reset.
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - The Python harness must be capable of either auto-detecting
;   the baud rate change or explicitly expecting a shift from 
;   UBRR0=10 to UBRR0=20 after the first byte is successfully 
;   echoed back.
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

    ; --- USART0 config: Initial Baud Rate UBRR0=10 ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    
    ldi r16, 0x06           ; 8N1 Data Frame
    sts UCSR0C, r16
    ldi r16, 0x18           ; Enable RX and TX
    sts UCSR0B, r16

    rjmp test_baud_10

; ============================================================
; TEST 1: Loopback at UBRR0 = 10
; ============================================================
test_baud_10:
    ldi r18, 0xAA
    rcall send_byte

wait_rxc_1:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_1

    lds r17, UDR0
    cpi r17, 0xAA
    brne fail

    rcall inc_case

; ============================================================
; TEST 2: Loopback at UBRR0 = 20
; ============================================================
test_baud_20:
    ; CRITICAL: Before changing the baud rate, we must ensure the 
    ; shift register is completely empty, otherwise we will corrupt 
    ; the end of the previous frame. Wait for TXC0.
wait_txc_safe:
    lds r16, UCSR0A
    sbrs r16, TXC0_BIT
    rjmp wait_txc_safe

    ; Clear TXC0 (write-1-to-clear) so it is ready for future checks
    ldi r16, (1 << TXC0_BIT)
    sts UCSR0A, r16

    ; --- Change Baud Rate to UBRR0=20 ---
    ldi r16, 20
    sts UBRR0L, r16

    ; Send a new byte at the new baud rate
    ldi r18, 0x55
    rcall send_byte

wait_rxc_2:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_2

    lds r17, UDR0
    cpi r17, 0x55
    brne fail

    rcall inc_case
    rjmp success

; ============================================================
; Helpers
; ============================================================
send_byte:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp send_byte
    sts UDR0, r18
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