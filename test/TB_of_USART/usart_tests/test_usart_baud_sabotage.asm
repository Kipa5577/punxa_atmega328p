; ============================================================
; USART0 Mid-Frame Baud Rate Sabotage Test
; ============================================================
; Validates that the internal baud rate generator down-counter 
; updates immediately upon writing to UBRR0L, corrupting the 
; timing of the currently active transmission.
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - The AVR will start sending 0x55 at UBRR0=10.
; - Roughly halfway through the frame, UBRR0 is shifted to 200.
; - The testbench MUST verify that the bit timing stretches 
;   mid-frame, causing a framing error (FE0) or corrupted byte.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ TXC0_BIT  = 6
.equ UDRE0_BIT = 5
.equ FE0_BIT   = 4      ; Frame Error Flag

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

    ; --- USART0 Initial Config: UBRR0=10, 8N1 ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    
    ldi r16, 0x06           ; 8 data bits, 1 stop bit
    sts UCSR0C, r16
    
    ; Enable TX and RX
    ldi r16, 0x18
    sts UCSR0B, r16

    rjmp test_mid_frame_baud

; ============================================================
; TEST 1: Change Baud Rate during Active TX
; ============================================================
test_mid_frame_baud:
wait_udre:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp wait_udre

    ; Clear TXC0 (write-1-to-clear)
    ldi r16, (1 << TXC0_BIT)
    sts UCSR0A, r16

    ; 1. Start transmission. 0x55 (01010101) is ideal for 
    ; observing timing shifts due to its alternating bit pattern.
    ldi r16, 0x55
    sts UDR0, r16

    ; 2. Delay for ~880 CPU cycles. 
    ; At UBRR0=10, 1 bit = 176 cycles. 880 cycles is exactly 5 bits.
    ; A 4-cycle loop running 220 times = 880 cycles.
    ldi r20, 220
delay_loop:
    nop                     ; 1 cycle
    dec r20                 ; 1 cycle
    brne delay_loop         ; 2 cycles (when branching)

    ; 3. THE SABOTAGE: Overwrite UBRR0L mid-transmission
    ; Shift UBRR0 from 10 to 200. The remaining bits will be 
    ; stretched drastically, causing a massive timing fault.
    ldi r16, 200
    sts UBRR0L, r16

    ; 4. Wait for the corrupted frame to finally finish transmitting.
    ; This proves the state machine still exits normally despite the fault.
wait_txc:
    lds r16, UCSR0A
    sbrs r16, TXC0_BIT
    rjmp wait_txc

    ; 5. Optional verification depending on loopback nature.
    ; If the python loopback perfectly mirrors the bad timing, 
    ; reading UCSR0A might show a Frame Error (FE0). 
    ; We'll clear the receive buffer just to be safe.
    lds r16, UCSR0A
    lds r17, UDR0

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