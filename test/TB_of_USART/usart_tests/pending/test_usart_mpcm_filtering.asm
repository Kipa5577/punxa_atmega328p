; ============================================================
; USART0 Multi-Processor Communication Mode (MPCM) Test
; ============================================================
; Validates that setting MPCM0 causes the hardware to filter 
; incoming frames based on the 9th bit (RXB80).
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - TEST 1: Send a "Data" frame (9th bit = 0). The AVR should 
;   silently ignore it (RXC0 should not set).
; - TEST 2: Send an "Address" frame (9th bit = 1). The AVR 
;   should accept it (RXC0 must set).
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ RXC0_BIT  = 7
.equ MPCM0_BIT = 0
.equ RXB80_BIT = 1
.equ TXB80_BIT = 0

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

    ; --- USART0 Config: 9-bit mode ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0x06           ; 8 bits
    sts UCSR0C, r16
    ldi r16, 0x1C           ; RXEN0 | TXEN0 | UCSZ02 (for 9th bit)
    sts UCSR0B, r16

    ; --- Enable MPCM0 ---
    lds r16, UCSR0A
    ori r16, (1 << MPCM0_BIT)
    sts UCSR0A, r16

    rjmp test_mpcm_data

; ============================================================
; TEST 1: Data Frame (9th bit = 0) - Should be filtered
; ============================================================
test_mpcm_data:
    ; Tell the harness to send a frame with 9th bit = 0
    ; (Harness implementation detail)
    
    ; Wait a brief period to ensure the byte would have been
    ; received if filtering wasn't active.
    ldi r20, 255
delay_loop:
    dec r20
    brne delay_loop

    ; Assert that RXC0 is NOT set
    lds r16, UCSR0A
    sbrc r16, RXC0_BIT
    rjmp fail               ; Fail if data was accepted

    rcall inc_case

; ============================================================
; TEST 2: Address Frame (9th bit = 1) - Should be accepted
; ============================================================
test_mpcm_address:
    ; Tell the harness to send a frame with 9th bit = 1
    
wait_rxc:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc

    ; Assert RXB80 (9th bit) is 1
    lds r16, UCSR0B
    sbrs r16, RXB80_BIT
    rjmp fail

    ; Clear MPCM0 to accept subsequent data bytes
    lds r16, UCSR0A
    andi r16, ~(1 << MPCM0_BIT)
    sts UCSR0A, r16

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

success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end

fail:
    ldi r16, 255
    sts final_result, r16
    rjmp end