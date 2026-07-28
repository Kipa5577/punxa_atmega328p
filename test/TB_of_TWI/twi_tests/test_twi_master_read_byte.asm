; TWI0 master-receive: START, SLA+R to slave 0x20, receive one data byte
; with TWEA=0 (NACK -- we only want one byte), STOP. PeerI2CSlave is
; configured (by tb_twi_tests.py's TEST_SLAVE_CONFIG) to supply 0xA5 as
; its first read byte.
.equ test_case    = 0x0100
.equ final_result = 0x0101
.equ stack_start  = 0x08FF
.equ TWSR = 0xB9
.equ TWDR = 0xBB
.equ TWCR = 0xBC
.equ RESULT_BYTE = 0x0200

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

    ldi r16, 0x41        ; SLA+R for address 0x20 (0x20<<1 | 1)
    sts TWDR, r16
    ldi r16, 0x84
    sts TWCR, r16
wait_addr:
    lds r17, TWCR
    sbrs r17, 7
    rjmp wait_addr
    lds r17, TWSR
    andi r17, 0xF8
    cpi r17, 0x40        ; SLA+R transmitted, ACK received
    brne fail

    ldi r16, 0x84        ; TWINT|TWEN, TWEA=0 -> receive + NACK (last byte)
    sts TWCR, r16
wait_data:
    lds r17, TWCR
    sbrs r17, 7
    rjmp wait_data
    lds r17, TWSR
    andi r17, 0xF8
    cpi r17, 0x58        ; data byte received, NACK returned
    brne fail

    lds r16, TWDR
    sts RESULT_BYTE, r16
    cpi r16, 0xA5
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
