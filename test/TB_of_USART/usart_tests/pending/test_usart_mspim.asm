; ============================================================
; USART0 Master SPI Mode (MSPIM) Test
; ============================================================
; Validates UMSEL01=1 and UMSEL00=1 Master SPI configuration.
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - The harness must monitor the XCK0 pin (PD4) for the SPI clock.
; - TXD0 (PD1) acts as MOSI.
; - RXD0 (PD0) acts as MISO.
; - The harness must drive RXD0 synchronously with the XCK0 edges
;   according to SPI Mode 0 (UCPOL0=0, UCPHA0=0).
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

; Port D Data Direction Register
.equ DDRD   = 0x2A  

.equ RXC0_BIT  = 7
.equ UDRE0_BIT = 5

.equ RXEN0_BIT = 4
.equ TXEN0_BIT = 3
.equ XCK0_BIT  = 4      ; XCK0 is mapped to Port D, Pin 4 (PD4)

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

    ; --- 1. Set XCK0 (PD4) as Output ---
    ; In Master SPI Mode, the clock pin must be explicitly 
    ; configured as an output for the clock to be driven.
    lds r16, DDRD
    ori r16, (1 << XCK0_BIT)
    sts DDRD, r16

    ; --- 2. Configure MSPIM in UCSR0C ---
    ; UMSEL01=1, UMSEL00=1 (Master SPI Mode)
    ; UDORD0=0 (MSB transmitted first)
    ; UCPHA0=0, UCPOL0=0 (SPI Mode 0: Sample on leading rising edge)
    ; Binary: 1100 0000 = 0xC0
    ldi r16, 0xC0
    sts UCSR0C, r16

    ; --- 3. Set SPI Clock Frequency (UBRR0) ---
    ; Note: For MSPIM, UBRR0 acts as the SPI clock divider.
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16

    ; --- 4. Enable Transmitter and Receiver ---
    ldi r16, (1 << RXEN0_BIT) | (1 << TXEN0_BIT)
    sts UCSR0B, r16

    rjmp test_mspim_start

; ============================================================
; TEST 1: Full-Duplex SPI Transmission
; ============================================================
test_mspim_start:
wait_udre:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp wait_udre

    ; 1. Write data to UDR0 (Starts the SPI clock and MOSI shift)
    ldi r16, 0xC3
    sts UDR0, r16

    ; 2. Wait for RX Complete. 
    ; In MSPIM, the receiver shift register is clocked simultaneously 
    ; with the transmitter. Once transmission completes, RXC0 sets.
wait_rxc:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc

    ; 3. Read data from UDR0 (MISO).
    ; We expect the testbench to echo the 0xC3 byte back via MISO.
    lds r17, UDR0
    cpi r17, 0xC3
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