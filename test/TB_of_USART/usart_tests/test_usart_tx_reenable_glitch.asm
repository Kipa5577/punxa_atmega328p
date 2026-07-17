; ============================================================
; USART0 Transmitter Re-enable Glitch Test
; ============================================================
; Validates that clearing TXEN0 and then quickly re-enabling 
; it mid-transmission does not corrupt the active frame or 
; prematurely release the TXD0 pin override.
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - The harness should observe the full 0x42 byte arriving intact.
; - The harness should verify that PD1 (TXD0) remains in USART 
;   override mode (driven HIGH during idle) after the stop bit, 
;   rather than reverting to the PORTD1 driven LOW state.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ PORTD  = 0x2B
.equ DDRD   = 0x2A

.equ RXC0_BIT  = 7
.equ TXC0_BIT  = 6
.equ UDRE0_BIT = 5

.equ RXEN0_BIT = 4
.equ TXEN0_BIT = 3
.equ TXD0_BIT  = 1      ; TXD0 is mapped to Port D, Pin 1 (PD1)

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

    ; --- 1. Configure Underlying Port D1 ---
    ; Set PD1 (TXD) as an output, and drive it LOW. 
    ; The USART overrides this when TXEN0 is set.
    lds r16, DDRD
    ori r16, (1 << TXD0_BIT)
    sts DDRD, r16
    
    lds r16, PORTD
    andi r16, ~(1 << TXD0_BIT)
    sts PORTD, r16

    ; --- 2. USART0 Config: UBRR0=10, 8N1 ---[cite: 1]
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    
    ldi r16, 0x06           ; 8 data bits
    sts UCSR0C, r16
    
    ; Enable RX and TX
    ldi r16, (1 << RXEN0_BIT) | (1 << TXEN0_BIT)
    sts UCSR0B, r16

    rjmp test_reenable_glitch

; ============================================================
; TEST 1: Disable and immediately Re-enable TX mid-transmission
; ============================================================
test_reenable_glitch:
wait_udre:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp wait_udre

    ; Clear TXC0 (write-1-to-clear) before we begin
    ldi r16, (1 << TXC0_BIT)
    sts UCSR0A, r16

    ; 1. Write the payload to UDR0 to begin transmission.
    ldi r16, 0x42
    sts UDR0, r16

    ; 2. Clear TXEN0 to initiate the graceful exit.
    lds r16, UCSR0B
    andi r16, ~(1 << TXEN0_BIT)
    sts UCSR0B, r16

    ; 3. Wait a few clock cycles. We use a short loop to ensure 
    ; we are well within the timeframe of the first bit shifting out, 
    ; but long enough to guarantee the state machine registered the 0.
    ldi r20, 10
delay_loop:
    dec r20
    brne delay_loop

    ; 4. Re-enable TXEN0 before the frame finishes.
    lds r16, UCSR0B
    ori r16, (1 << TXEN0_BIT)
    sts UCSR0B, r16

    ; 5. Wait for the Transmit Complete (TXC0) flag.
wait_txc:
    lds r16, UCSR0A
    sbrs r16, TXC0_BIT
    rjmp wait_txc

    ; 6. Check the Loopback Receiver. 
    ; If the transmitter logic is solid, the Python harness 
    ; received the full 0x42 byte and echoed it back.[cite: 1]
wait_rxc:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc

    lds r17, UDR0
    cpi r17, 0x42
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