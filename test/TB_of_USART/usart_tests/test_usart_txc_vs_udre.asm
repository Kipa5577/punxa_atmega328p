; ============================================================
; USART0 TXCIE0 vs UDRIE0 Timing Test
; ============================================================
; Validates the critical timing distinction between the Data
; Register Empty interrupt (fires when the buffer can take 
; a new byte) and the Transmit Complete interrupt (fires only 
; when the shift register is completely empty and idle).
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ TXCIE0_BIT = 6
.equ UDRIE0_BIT = 5
.equ TXEN0_BIT  = 3

.equ test_case    = 0x0100
.equ final_result = 0x0101

; ============================================================
; Interrupt Vector Table (ATmega328P Byte Addresses)
; ============================================================
.org 0x0000
    rjmp reset

.org 0x0026 ; USART_UDRE Data Register Empty Vector
    rjmp isr_udre

.org 0x0028 ; USART_TX Transmit Complete Vector
    rjmp isr_txc

; ============================================================
; Initialization
; ============================================================
.org 0x0030
reset:
    ; Initialize Stack Pointer
    ldi r16, high(0x08FF)
    out 0x3E, r16          ; SPH
    ldi r16, low(0x08FF)
    out 0x3D, r16          ; SPL

    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ; Initialize tracking registers
    clr r20                 ; udre_fired_flag
    clr r21                 ; txc_fired_flag
    clr r22                 ; main_loop_counter (delay tracker)

    ; --- USART0 config: UBRR0=10, 8N1 ---[cite: 1]
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    ldi r16, 0x06           
    sts UCSR0C, r16

    ; Clear TXC0 (write-1-to-clear) to ensure a clean slate
    ldi r16, (1 << 6)       ; TXC0 is bit 6 in UCSR0A
    sts UCSR0A, r16

    ; Enable the Transmitter[cite: 1]
    ldi r16, (1 << TXEN0_BIT)
    sts UCSR0B, r16

    ; Enable Global Interrupts first
    sei

    ; Enable both UDRIE0 and TXCIE0. 
    ; Because the transmit buffer is currently empty, the UDRE 
    ; interrupt will vector immediately after this instruction.
    lds r16, UCSR0B
    ori r16, (1 << UDRIE0_BIT) | (1 << TXCIE0_BIT)
    sts UCSR0B, r16

; ============================================================
; Main Loop (Delay Tracker)
; ============================================================
wait_loop:
    ; Increment our loop counter. This proves that CPU cycles 
    ; are executing between the UDRE and TXC events.
    inc r22
    
    ; Check if the TXC interrupt has fired yet
    cpi r21, 1
    brne wait_loop

    ; Once TXC fires, disable interrupts to run assertions safely
    cli

; ============================================================
; Verification Assertions
; ============================================================
verify_logic:
    ; Assertion 1: Did UDRE fire? (r20 must equal 1)
    ; This ensures the ISR sequencing was correct.
    cpi r20, 1
    brne fail

    ; Assertion 2: Did time pass between UDRE and TXC?
    ; If the emulator is buggy and fires TXC instantly, r22 will be 0 or 1.
    ; At UBRR0=10, shifting out 10 bits takes hundreds of CPU cycles, 
    ; so r22 will easily wrap around or be very large. We'll just assert 
    ; that it counted up to at least 10 to prove a delay occurred.
    cpi r22, 10
    brlo fail

    rcall inc_case
    rjmp success

; ============================================================
; Interrupt Service Routines (ISRs)
; ============================================================

; Data Register Empty ISR
isr_udre:
    push r16
    in r16, 0x3F            ; Save Status Register (SREG)
    push r16

    ldi r20, 1              ; Set udre_fired_flag

    ; Write a byte to UDR0 to begin transmission
    ldi r16, 0x55
    sts UDR0, r16

    ; Crucial: Disable UDRIE0 so it doesn't fire endlessly while 
    ; the byte is shifting out.
    lds r16, UCSR0B
    andi r16, ~(1 << UDRIE0_BIT)
    sts UCSR0B, r16

    pop r16
    out 0x3F, r16           ; Restore SREG
    pop r16
    reti

; Transmit Complete ISR
isr_txc:
    push r16
    in r16, 0x3F            ; Save SREG
    push r16

    ldi r21, 1              ; Set txc_fired_flag

    pop r16
    out 0x3F, r16           ; Restore SREG
    pop r16
    reti

; ============================================================
; Test Bench Framework Mechanics[cite: 1]
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