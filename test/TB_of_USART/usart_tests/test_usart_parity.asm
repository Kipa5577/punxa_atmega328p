; ============================================================
; USART0 Parity Generation and Checking Test (UPE0)
; ============================================================
; Validates the Even Parity hardware logic.
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - TEST 1 uses standard loopback (valid even parity echoed).
; - TEST 2 sends 0xFF as a trigger. The testbench MUST intercept
;   this byte and reply with a byte framed with ODD parity 
;   (an intentional error) to trip the AVR's UPE0 flag.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ RXC0_BIT  = 7
.equ UDRE0_BIT = 5
.equ UPE0_BIT  = 2      ; Parity Error Flag

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

    ; --- USART0 config: UBRR0=10 ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16

    ; --- Enable Even Parity ---
    ; UPM01=1, UPM00=0 (Even Parity)
    ; UCSZ01=1, UCSZ00=1 (8 data bits)
    ; Binary: 0010 0110 = 0x26
    ldi r16, 0x26
    sts UCSR0C, r16

    ; Enable RX and TX
    ldi r16, 0x18
    sts UCSR0B, r16

    rjmp test_parity_clean

; ============================================================
; TEST 1: Valid Frame (No Parity Error)
; ============================================================
test_parity_clean:
    ; Send an arbitrary byte. The loopback testbench should 
    ; echo it back cleanly with the correct Even parity bit.
    ldi r18, 0x33
    rcall send_byte

wait_rxc_1:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_1

    ; MUST read UCSR0A to check UPE0 *before* reading UDR0.
    ; Reading UDR0 advances the FIFO and invalidates the error flags.
    lds r16, UCSR0A
    sbrc r16, UPE0_BIT
    rjmp fail               ; Fail if Parity Error (UPE0) is set

    ; Read the payload
    lds r17, UDR0
    cpi r17, 0x33
    brne fail               ; Fail if the payload is corrupted

    rcall inc_case

; ============================================================
; TEST 2: Invalid Frame (Parity Error Triggered)
; ============================================================
test_parity_error:
    ; Send a trigger byte to notify the testbench. 
    ; The python harness must respond by sending a byte with 
    ; incorrect (Odd) parity.
    ldi r18, 0xFF
    rcall send_byte

wait_rxc_2:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_2

    ; Check UCSR0A for the parity error flag
    lds r16, UCSR0A
    sbrs r16, UPE0_BIT
    rjmp fail               ; Fail if Parity Error (UPE0) is NOT set

    ; Read UDR0 to clear the receive buffer and flag
    lds r17, UDR0

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