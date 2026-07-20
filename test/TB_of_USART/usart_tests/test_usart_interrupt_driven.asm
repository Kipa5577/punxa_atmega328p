; ============================================================
; USART0 Interrupt-Driven TX/RX Test Suite
; ============================================================
; Validates both UDRIE0 and RXCIE0 vectors on the ATmega328P.
; Uses RAM buffering to pass data entirely via ISR logic.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ RXCIE0_BIT = 7
.equ UDRIE0_BIT = 5
.equ RXEN0_BIT  = 4
.equ TXEN0_BIT  = 3

.equ test_case    = 0x0100
.equ final_result = 0x0101

; Data buffers allocated in internal SRAM
.equ tx_buf_start = 0x0110
.equ rx_buf_start = 0x0115

; ============================================================
; Interrupt Vector Table
; ============================================================
; NOTE: this project's SimpleInterruptUnit (Interrupt_Unit.py) does not
; use the real ATmega328P's word-addressed vector numbers directly as
; jump targets -- it uses its own vector_table dict, whose values
; happen to equal the *real chip's byte address* for each vector
; (USART_RX=0x0024, USART_UDRE=0x0026, USART_TX=0x0028), and those
; values are loaded into PC as-is (this assembler's PC/.org is
; word-addressed, so numerically these ARE the correct .org targets
; for this project, even though they don't match the real chip's own
; word-address vector table, e.g. USART_RX=18/0x12 on real hardware).
; Verified empirically against a live run of this harness: placing
; ISRs at the real chip's word addresses (0x0012/0x0013) never fires
; -- the CPU spins in wait_loop until the step_limit timeout, exactly
; the failure mode this file's own comment warns about. 0x0024/0x0026
; is the address this project's interrupt controller actually jumps to.
.org 0x0000
    rjmp reset

.org 0x0024 ; USART_RX Complete vector, this project's convention
    rjmp usart_rx_isr

.org 0x0026 ; USART_UDRE Data Register Empty vector, this project's convention
    rjmp usart_udre_isr

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

    ; --- Seed Transmit Buffer ---
    ldi r16, 0xAA
    sts tx_buf_start, r16
    ldi r16, 0xBB
    sts tx_buf_start + 1, r16
    ldi r16, 0xCC
    sts tx_buf_start + 2, r16

    ; Clear ISR State Counters (Using global registers for simplicity)
    clr r20                 ; r20 will track bytes transmitted (0 to 3)
    clr r21                 ; r21 will track bytes received (0 to 3)

    ; --- USART0 hardware config: UBRR0=10, 8N1 ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    ldi r16, 0x06           ; Asynchronous, no parity, 1 stop bit, 8 data bits
    sts UCSR0C, r16

    ; Enable RX, TX, and the RX Complete Interrupt. 
    ; (Keep UDRIE0 off initially so it doesn't fire prematurely).
    ldi r16, (1 << RXEN0_BIT) | (1 << TXEN0_BIT) | (1 << RXCIE0_BIT)
    sts UCSR0B, r16

    ; Enable global interrupts
    sei

    ; --- Trigger Test Flow ---
    ; Manually turning on UDRIE0 fires the first UDRE interrupt immediately
    ; because the transmit buffer starts empty.
    lds r16, UCSR0B
    ori r16, (1 << UDRIE0_BIT)
    sts UCSR0B, r16

; ============================================================
; Main Idle Loop
; ============================================================
wait_loop:
    ; Spin passively. If interrupts are failing, this loop hangs, 
    ; causing the python testbench execution to timeout.
    cpi r21, 3
    brlo wait_loop

    ; Safeguard: Disable global interrupts before running verification
    cli

; ============================================================
; Verification Assertions
; ============================================================
verify_data:
    lds r16, rx_buf_start
    cpi r16, 0xAA
    brne fail_near

    lds r16, rx_buf_start + 1
    cpi r16, 0xBB
    brne fail_near

    lds r16, rx_buf_start + 2
    cpi r16, 0xCC
    brne fail_near

    rcall inc_case
    rjmp success

; `fail:` sits well past both ISRs below, out of range for a direct
; `brne` (AVR conditional branches are +-63 words); jmp has a 22-bit
; range so this local trampoline reaches it fine.
fail_near:
    jmp fail

; ============================================================
; Interrupt Service Routines (ISRs)
; ============================================================

; Data Register Empty ISR
usart_udre_isr:
    push r16
    push r30
    push r31
    in r16, 0x3F            ; Save Status Register (SREG)
    push r16

    cpi r20, 3
    brlo send_next_byte

    ; If all 3 bytes are queued up, turn off UDRIE0 to clear the interrupt source
    lds r16, UCSR0B
    andi r16, ~(1 << UDRIE0_BIT)
    sts UCSR0B, r16
    rjmp udre_exit

send_next_byte:
    ; Calculate dynamic memory offset: tx_buf_start + r20
    ldi r30, low(tx_buf_start)
    ldi r31, high(tx_buf_start)
    add r30, r20
    clr r16
    adc r31, r16

    ld r16, Z
    sts UDR0, r16           ; Write payload to transmit
    inc r20                 ; Increment tx index counter

udre_exit:
    pop r16
    out 0x3F, r16           ; Restore SREG
    pop r31
    pop r30
    pop r16
    reti

; RX Complete ISR
usart_rx_isr:
    push r16
    push r17
    push r30
    push r31
    in r16, 0x3F            ; Save Status Register (SREG)
    push r16

    lds r16, UDR0           ; Instantly pull data off hardware buffer

    cpi r21, 3              ; Bounds check safely
    brsh rx_exit

    ; Calculate dynamic memory offset: rx_buf_start + r21
    ldi r30, low(rx_buf_start)
    ldi r31, high(rx_buf_start)
    add r30, r21
    clr r17
    adc r31, r17

    st Z, r16               ; Push received byte to RAM
    inc r21                 ; Increment rx tracking index

rx_exit:
    pop r16
    out 0x3F, r16           ; Restore SREG
    pop r31
    pop r30
    pop r17
    pop r16
    reti

; ============================================================
; Test Bench Framework Mechanics
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