; ============================================================
; USART0 9-Bit Data Mode Test
; ============================================================
; Validates transmission and reception of 9-bit frames.
; In 9-bit mode, the 9th bit must be written to TXB80 before 
; writing UDR0, and read from RXB80 before reading UDR0.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ RXC0_BIT  = 7
.equ UDRE0_BIT = 5

.equ UCSZ02_BIT = 2
.equ RXB80_BIT  = 1
.equ TXB80_BIT  = 0

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

    ; --- USART0 config: UBRR0=10, 9-bit mode ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    
    ; UCSZ01=1 and UCSZ00=1 for the lower two bits of the size configuration
    ldi r16, 0x06           
    sts UCSR0C, r16
    
    ; Enable RX, TX, and set UCSZ02=1 for the 3rd bit of the size configuration (9-bit total)
    ldi r16, 0x1C           ; RXEN0 | TXEN0 | UCSZ02
    sts UCSR0B, r16

    rjmp test_9bit_high

; ============================================================
; TEST 1: 9th Bit = 1
; ============================================================
test_9bit_high:
wait_udre_1:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp wait_udre_1

    ; 1. Write the 9th bit (TXB80) BEFORE writing UDR0
    lds r16, UCSR0B
    ori r16, (1 << TXB80_BIT)  ; Set TXB80 to 1
    sts UCSR0B, r16

    ; 2. Write the 8 lower bits to UDR0
    ldi r16, 0xFF
    sts UDR0, r16

wait_rxc_1:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_1

    ; 3. Read the 9th bit (RXB80) BEFORE reading UDR0
    lds r16, UCSR0B
    sbrs r16, RXB80_BIT        ; Skip next instruction if RXB80 is set (1)
    rjmp fail                  ; Fail if RXB80 is 0

    ; 4. Read the 8 lower bits from UDR0
    lds r17, UDR0
    cpi r17, 0xFF
    brne fail

    rcall inc_case

; ============================================================
; TEST 2: 9th Bit = 0
; ============================================================
test_9bit_low:
wait_udre_2:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp wait_udre_2

    ; 1. Write the 9th bit (TXB80) BEFORE writing UDR0
    lds r16, UCSR0B
    andi r16, ~(1 << TXB80_BIT) ; Clear TXB80 to 0
    sts UCSR0B, r16

    ; 2. Write the 8 lower bits to UDR0
    ldi r16, 0x55
    sts UDR0, r16

wait_rxc_2:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_2

    ; 3. Read the 9th bit (RXB80) BEFORE reading UDR0
    lds r16, UCSR0B
    sbrc r16, RXB80_BIT        ; Skip next instruction if RXB80 is clear (0)
    rjmp fail                  ; Fail if RXB80 is 1

    ; 4. Read the 8 lower bits from UDR0
    lds r17, UDR0
    cpi r17, 0x55
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