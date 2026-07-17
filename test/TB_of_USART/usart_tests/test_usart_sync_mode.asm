; ============================================================
; USART0 Synchronous Mode Test (Master & Slave)
; ============================================================
; Validates UMSEL00=1 synchronous transmission and reception.
;
; NOTE FOR TESTBENCH (tb_usart.py):
; - During TEST 1 (Master), the testbench must verify that a 
;   clock signal is generated on the XCK0 pin (PD4) while data
;   is shifted out on TXD0.
; - During TEST 2 (Slave), the testbench must actively drive 
;   the XCK0 pin with 8 clock cycles while shifting data into 
;   RXD0 to trigger the RXC0 flag.
; ============================================================

.equ UCSR0A = 0xC0
.equ UCSR0B = 0xC1
.equ UCSR0C = 0xC2
.equ UBRR0L = 0xC4
.equ UBRR0H = 0xC5
.equ UDR0   = 0xC6

; Port D Data Direction Register (Memory Mapped Address)
.equ DDRD   = 0x2A  

.equ RXC0_BIT  = 7
.equ TXC0_BIT  = 6
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

    ; --- USART0 config: UBRR0=10 ---
    ldi r16, 10
    sts UBRR0L, r16
    ldi r16, 0
    sts UBRR0H, r16

    ; Configure Synchronous Mode: UMSEL01=0, UMSEL00=1
    ; 8N1 Data Frame: UCSZ01=1, UCSZ00=1
    ; Binary: 0100 0110 = 0x46
    ldi r16, 0x46           
    sts UCSR0C, r16

    rjmp test_sync_master

; ============================================================
; TEST 1: Synchronous Master Mode (Transmit)
; ============================================================
test_sync_master:
    ; 1. Configure XCK0 (PD4) as OUTPUT for Master Mode
    lds r16, DDRD
    ori r16, (1 << XCK0_BIT)
    sts DDRD, r16

    ; 2. Enable Transmitter
    ldi r16, (1 << TXEN0_BIT)
    sts UCSR0B, r16

wait_udre_master:
    lds r16, UCSR0A
    sbrs r16, UDRE0_BIT
    rjmp wait_udre_master

    ; 3. Write data to UDR0. The hardware will now generate 
    ; the clock on XCK0 and shift out 0xA5.
    ldi r16, 0xA5
    sts UDR0, r16

wait_txc_master:
    lds r16, UCSR0A
    sbrs r16, TXC0_BIT
    rjmp wait_txc_master

    ; Clear TXC0 (write-1-to-clear)
    ldi r17, (1 << TXC0_BIT)
    sts UCSR0A, r17

    rcall inc_case

; ============================================================
; TEST 2: Synchronous Slave Mode (Receive)
; ============================================================
test_sync_slave:
    ; 1. Configure XCK0 (PD4) as INPUT for Slave Mode
    lds r16, DDRD
    andi r16, ~(1 << XCK0_BIT)
    sts DDRD, r16

    ; 2. Disable Transmitter, Enable Receiver
    ldi r16, (1 << RXEN0_BIT)
    sts UCSR0B, r16

    ; 3. Wait for RXC0. 
    ; The Python testbench MUST drive XCK0 to clock data into RXD0.
    ; Without external clocking, this loop will block forever.
wait_rxc_slave:
    lds r16, UCSR0A
    sbrs r16, RXC0_BIT
    rjmp wait_rxc_slave

    ; 4. Verify the byte clocked in by the testbench (expecting 0x5A)
    lds r17, UDR0
    cpi r17, 0x5A
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