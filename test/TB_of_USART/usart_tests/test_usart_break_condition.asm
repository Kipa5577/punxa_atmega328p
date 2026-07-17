; ============================================================
; USART0 Break Condition Detection Test
; ============================================================
; Validates that holding the RX line dominant (LOW) for longer
; than a frame triggers a Frame Error (FE0) and reads as 0x00.
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - TEST 1: The AVR sends a trigger byte (0xBB).
; - The harness MUST intercept 0xBB, avoid echoing it, and 
;   instead drive the AVR's RXD pin LOW for >= 12 bit times, 
;   then release it HIGH.
; - TEST 2: The AVR sends a recovery byte (0xCC). The harness 
;   must resume standard echo behavior (echoing 0xCC back)[cite: 1].
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

.equ RXC0_BIT  = 7
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

    ; --- USART0 Config: UBRR0=10, 8N1 ---[cite: 1]
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16
    
    ldi r16, 0x06           ; 8 data bits, 1 stop bit[cite: 1]
    sts UCSR0C, r16
    
    ; Enable TX and RX[cite: 1]
    ldi r16, 0x18
    sts UCSR0B, r16

    rjmp test_break_condition

; ============================================================
; TEST 1: Trigger and Detect Break Condition
; ============================================================
test_break_condition:
    ; Send trigger byte to the Python harness
    ldi r18, 0xBB
    rcall send_byte

wait_rxc_break:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_break

    ; 1. Assertion 1: Read UCSR0A *before* UDR0 and assert FE0 is 1
    lds r16, UCSR0A
    sbrs r16, FE0_BIT
    rjmp fail               ; Fail if Frame Error is NOT set

    ; 2. Assertion 2: Read UDR0 and assert the payload is exactly 0x00
    lds r17, UDR0
    cpi r17, 0x00
    brne fail               ; Fail if the payload is not completely empty

    rcall inc_case

; ============================================================
; TEST 2: Verify Recovery (Next Frame)
; ============================================================
test_recovery:
    ; Send a normal byte to verify the receiver state machine 
    ; recovered automatically after the break condition ended.
    ldi r18, 0xCC
    rcall send_byte

wait_rxc_recovery:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_recovery

    ; Assert FE0 is cleared for the new valid frame
    lds r16, UCSR0A
    sbrc r16, FE0_BIT
    rjmp fail               ; Fail if Frame Error is STILL set

    ; Assert the data matches the expected echo[cite: 1]
    lds r17, UDR0
    cpi r17, 0xCC
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