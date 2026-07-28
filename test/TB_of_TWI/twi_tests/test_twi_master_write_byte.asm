; TWI0 master-transmit: START, SLA+W to slave 0x20, send data byte 0x42,
; STOP. Checked two ways: the TWSR status code sequence a real firmware
; driver polls for (0x08 -> 0x18 -> 0x28), and (after the fact, by
; tb_twi_tests.py's PEER_RX_CHECKS) that PeerI2CSlave actually received
; 0x42 on the wire.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TWSR = 0xB9
.equ TWDR = 0xBB
.equ TWCR = 0xBC

reset:
    ldi r16, high(stack_start)
    out SPH, r16
    ldi r16, low(stack_start)
    out SPL, r16
    ldi r16, 1
    sts test_case, r16
    sts final_result, r16

    ldi r16, 0xA4        ; TWINT|TWSTA|TWEN -> request START
    sts TWCR, r16
wait_start:
    lds r17, TWCR
    sbrs r17, 7
    rjmp wait_start
    lds r17, TWSR
    andi r17, 0xF8
    cpi r17, 0x08
    brne fail

    ldi r16, 0x40        ; SLA+W for address 0x20 (0x20<<1 | 0)
    sts TWDR, r16
    ldi r16, 0x84        ; TWINT|TWEN -> send address
    sts TWCR, r16
wait_addr:
    lds r17, TWCR
    sbrs r17, 7
    rjmp wait_addr
    lds r17, TWSR
    andi r17, 0xF8
    cpi r17, 0x18        ; SLA+W transmitted, ACK received
    brne fail

    ldi r16, 0x42
    sts TWDR, r16
    ldi r16, 0x84
    sts TWCR, r16
wait_data:
    lds r17, TWCR
    sbrs r17, 7
    rjmp wait_data
    lds r17, TWSR
    andi r17, 0xF8
    cpi r17, 0x28        ; data byte transmitted, ACK received
    brne fail

    ldi r16, 0x94        ; TWINT|TWSTO|TWEN -> request STOP
    sts TWCR, r16

    rcall inc_case
    rjmp success

success:
    ldi r16, 1
    sts final_result, r16
end:
    rjmp end
fail:
    ldi r16, 255
    sts final_result, r16
    rjmp end
inc_case:
    lds r16, test_case
    inc r16
    sts test_case, r16
    ret
