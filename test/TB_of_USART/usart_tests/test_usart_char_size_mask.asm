; ============================================================
; USART0 Character Size Masking Test (5, 6, 7-bit modes)
; ============================================================
; Validates that the receiver hardware correctly masks off 
; unused Most Significant Bits (MSBs) when configured for 
; character sizes smaller than 8 bits.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ RXC0_BIT  = 7
.equ UDRE0_BIT = 5
.equ TXC0_BIT  = 6

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

    ; --- Basic USART0 Config ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    
    ; Enable RXEN0 and TXEN0. 
    ; UCSZ02 is 0 for 5, 6, and 7-bit modes.
    ldi r16, 0x18           
    sts UCSR0B, r16

    rjmp test_5bit_mode

; ============================================================
; TEST 1: 5-Bit Character Size (Mask: 0x1F)
; ============================================================
test_5bit_mode:
    ; Configure UCSR0C for 5-bit mode (UCSZ01=0, UCSZ00=0)
    ; Async, no parity, 1 stop bit
    ldi r16, 0x00
    sts UCSR0C, r16

    ldi r18, 0xFF
    rcall send_byte

wait_rxc_5bit:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_5bit

    ; Read UDR0. The top 3 bits must be masked to 0 by hardware.
    ; Expecting 0x1F (0001 1111)
    lds r17, UDR0
    cpi r17, 0x1F
    brne fail

    rcall clear_txc
    rcall inc_case

; ============================================================
; TEST 2: 6-Bit Character Size (Mask: 0x3F)
; ============================================================
test_6bit_mode:
    ; Configure UCSR0C for 6-bit mode (UCSZ01=0, UCSZ00=1)
    ldi r16, 0x02
    sts UCSR0C, r16

    ldi r18, 0xFF
    rcall send_byte

wait_rxc_6bit:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_6bit

    ; Read UDR0. The top 2 bits must be masked to 0 by hardware.
    ; Expecting 0x3F (0011 1111)
    lds r17, UDR0
    cpi r17, 0x3F
    brne fail

    rcall clear_txc
    rcall inc_case

; ============================================================
; TEST 3: 7-Bit Character Size (Mask: 0x7F)
; ============================================================
test_7bit_mode:
    ; Configure UCSR0C for 7-bit mode (UCSZ01=1, UCSZ00=0)
    ldi r16, 0x04
    sts UCSR0C, r16

    ldi r18, 0xFF
    rcall send_byte

wait_rxc_7bit:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_7bit

    ; Read UDR0. The top 1 bit must be masked to 0 by hardware.
    ; Expecting 0x7F (0111 1111)
    lds r17, UDR0
    cpi r17, 0x7F
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

clear_txc:
    ; Wait for transmission to finish completely before 
    ; changing configuration for the next test.
wait_txc_safe:
    lds r16, UCSR0A
    sbrs r16, TXC0_BIT
    rjmp wait_txc_safe
    ; Clear TXC0 by writing a 1 to its bit location
    ldi r16, (1 << TXC0_BIT)
    sts UCSR0A, r16
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