; ============================================================
; USART0 Receiver Data Overrun (DOR0) Test
; ============================================================
; Validates the FIFO constraints of the USART receiver.
; Runs via tb_usart.py using the default loopback config.
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
.equ DOR0_BIT  = 3

.equ test_case = 0x0100
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

    ; --- USART0 config: UBRR0=10, 8N1, TXEN0+RXEN0 ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    ldi r16, 0x06           ; async, no parity, 1 stop, 8 data bits
    sts UCSR0C, r16
    ldi r16, 0x18           ; RXEN0 | TXEN0
    sts UCSR0B, r16

    rjmp test_dor0_start

; ============================================================
; TEST 1: Force DOR0 flag and verify clearance
; ============================================================
test_dor0_start:
    ; 1. Send 3 bytes back-to-back from the AVR to the Python loopback
    ldi r18, 0x11
    rcall send_byte
    ldi r18, 0x22
    rcall send_byte
    ldi r18, 0x33
    rcall send_byte

    ; Wait for the TX phase to complete entirely, ensuring the 
    ; Python harness has echoed everything back to our RX pin.
wait_txc:
    lds r16, UCSR0A
    sbrs r16, TXC0_BIT
    rjmp wait_txc

    ; Add a small delay to ensure the RX shifting engine 
    ; has fully processed the echoed bytes before we check flags.
    ldi r20, 255
delay_loop:
    dec r20
    brne delay_loop

    ; 2. Deliberately do not read UDR0 yet.
    ; Read UCSR0A and assert that the Data Overrun (DOR0) flag is set to 1.
    lds r16, UCSR0A
    sbrs r16, DOR0_BIT
    rjmp fail               ; Fail if DOR0 is NOT set

    ; 3. Read UDR0 to clear the buffer.
    ; The first byte in the FIFO should be 0x11.
    lds r17, UDR0
    cpi r17, 0x11
    brne fail

    ; The second byte in the FIFO should be 0x22.
    lds r17, UDR0
    cpi r17, 0x22
    brne fail

    ; Read a third time. Depending on simulator specifics, 0x33 
    ; is either discarded or pulled from the shift register.
    lds r17, UDR0

    ; 4. Check if the overrun flag clears properly.
    ; After reading out UDR0, the error flags are updated. DOR0 should now be 0.
    lds r16, UCSR0A
    sbrc r16, DOR0_BIT
    rjmp fail               ; Fail if DOR0 is STILL set

    rcall inc_case
    rjmp success

; ============================================================
; Helpers
; ============================================================
send_byte:                   ; byte to send in r18[cite: 1]
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