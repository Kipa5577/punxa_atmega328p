# -*- coding: utf-8 -*-
"""
TWI0 -- ATmega328P Two-Wire (I2C-compatible) interface, master mode.

First round of implementation (TWI/I2C was previously entirely absent
from this project -- see HANDOFF.md's gap list). Scope of this round,
deliberately bounded the same way RomHandler's SPM path or USART0's
loopback-only testing were bounded in earlier rounds -- documented as a
known limitation rather than silently pretended-complete:

IMPLEMENTED: master mode only -- START/repeated-START, SLA+W and SLA+R
(7-bit addressing), master-transmit and master-receive data phases with
ACK/NACK (TWEA-controlled on receive), STOP, and the real AVR status
codes a firmware TWI driver actually polls TWSR for (0x08, 0x18/0x20,
0x28/0x30, 0x40/0x48, 0x50/0x58). Firmware-facing behavior (TWCR's
TWINT-write-triggers-next-operation idiom, TWDR read/write, TWWC
write-collision detection) matches real hardware's control flow.

NOT IMPLEMENTED (explicitly out of scope this round):
- Slave mode (this device only ever drives the bus as master; there is
  no TWAR-address-matching responder path here -- PeerI2CSlave, the test
  peer, plays that role externally instead, the same way PeerUART plays
  the "other end of the wire" for USART0 rather than USART0 modeling
  both directions itself).
- Multi-master arbitration (status code 0x38) and bus-busy detection.
- Clock stretching (SCL held low by a slave) -- SCL_sense is wired in
  and available for a future round to actually watch, but this round's
  FSM does not yet stall on it.
- General call address, 10-bit addressing, TWAMR address masking.
- Real SCL frequency from TWBR/TWPS -- bit timing is a fixed
  HALF_PERIOD (in simulator cycles) instead, the same kind of
  simplification RomHandler's ISP flashing already documents doing
  (~2 sim cycles/bit there; some fixed small number of cycles per SCL
  phase here) rather than deriving an accurate F_SCL.

Bus modeling: SCL and SDA are real open-drain wired-AND lines in
hardware (any device can pull low; the line reads high only if nothing
pulls it low). Two agents sharing a real py4hw.Wire can't both drive it,
so each agent (TWI0, PeerI2CSlave) gets its own private "intent" output
wire (1 = release/let float high, 0 = actively pull low), and a small
OpenDrainAnd combiner (this file) ANDs every agent's intent into the one
shared line both agents read back as their "sense" input -- see
tb_twi_tests.py for how these are wired together.
"""
import py4hw
from punxa_atmega328p.Memory import *


class OpenDrainAnd(py4hw.Logic):
    """Combines N agents' open-drain 'intent' wires (1=release, 0=pull
    low) into the one shared bus line every agent reads back. Test
    infrastructure pattern, but kept in the CPU package alongside TWI0
    since any future real TWI slave peripheral would need the same
    combiner to share a bus with TWI0."""
    def __init__(self, parent, name, drivers, line):
        super().__init__(parent, name)
        self.drivers = [self.addIn(f'drv{i}', d) for i, d in enumerate(drivers)]
        self.line = self.addOut('line', line)

    def propagate(self):
        v = 1
        for d in self.drivers:
            v &= (d.get() & 1)
        self.line.put(v)


class TWI0(py4hw.Logic):
    HALF_PERIOD = 3  # sim cycles per SCL half-phase -- see module docstring

    def __init__(self, parent, name, port: MemoryInterface,
                 SCL_drive, SCL_sense, SDA_drive, SDA_sense, TWI_INT):
        super().__init__(parent, name)

        self.port0 = self.addInterfaceSink('port', port)
        self.SCL_drive = self.addOut('SCL_drive', SCL_drive)
        self.SCL_sense = self.addIn('SCL_sense', SCL_sense)
        self.SDA_drive = self.addOut('SDA_drive', SDA_drive)
        self.SDA_sense = self.addIn('SDA_sense', SDA_sense)
        self.TWI_INT = self.addOut('TWI_INT', TWI_INT)

        self.TWBR = 0
        self.TWBR_addr_LS = 0xB8
        self.TWSR = 0xF8  # status=0xF8 (idle/no relevant state), TWPS=00
        self.TWSR_addr_LS = 0xB9
        self.TWAR = 0
        self.TWAR_addr_LS = 0xBA
        self.TWDR = 0xFF
        self.TWDR_addr_LS = 0xBB
        self.TWCR = 0
        self.TWCR_addr_LS = 0xBC

        # TWCR bit fields (parsed each cycle from self.TWCR)
        self.TWINT = 0
        self.TWEA = 0
        self.TWSTA = 0
        self.TWSTO = 0
        self.TWWC = 0
        self.TWEN = 0
        self.TWIE = 0

        self._sda_out = 1
        self._scl_out = 1

        self.state = 'IDLE'      # IDLE / START / DATA / STOP (which
                                  # operation is currently executing)
        self.substate = None
        self.phase_timer = 0
        self.bit_index = 0
        self.shift_reg = 0
        self.op_mode = None      # None (no address sent yet) / 'MT' / 'MR'
        self.busy = False

    # -----------------------------------------------------------------
    def Memory_access(self):
        addr = self.port0.address.get()
        read_op = (self.port0.read.get() == 1) and (self.port0.write.get() == 0)
        write_op = (self.port0.read.get() == 0) and (self.port0.write.get() == 1)

        if (addr == self.TWBR_addr_LS) and (self.port0.instype.get() == 1):
            if read_op:
                self.port0.read_data.prepare(self.TWBR)
                self.port0.resp.prepare(1)
            elif write_op:
                self.TWBR = self.port0.write_data.get() & 0xFF
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif (addr == self.TWSR_addr_LS) and (self.port0.instype.get() == 1):
            if read_op:
                self.port0.read_data.prepare(self.TWSR)
                self.port0.resp.prepare(1)
            elif write_op:
                # Only TWPS1:0 (bits 1:0) are writable; the status bits
                # (7:3) are hardware-set, bit 2 is reserved/read-as-0.
                self.TWSR = (self.TWSR & 0xF8) | (self.port0.write_data.get() & 0x03)
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif (addr == self.TWAR_addr_LS) and (self.port0.instype.get() == 1):
            if read_op:
                self.port0.read_data.prepare(self.TWAR)
                self.port0.resp.prepare(1)
            elif write_op:
                self.TWAR = self.port0.write_data.get() & 0xFF
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif (addr == self.TWDR_addr_LS) and (self.port0.instype.get() == 1):
            if read_op:
                self.port0.read_data.prepare(self.TWDR)
                self.port0.resp.prepare(1)
            elif write_op:
                # Real hardware: a TWDR write while TWINT=0 (an operation
                # is in progress) is a write collision -- the write is
                # ignored and TWWC latches instead.
                if self.busy:
                    self.TWCR |= 0x08  # TWWC
                else:
                    self.TWDR = self.port0.write_data.get() & 0xFF
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif (addr == self.TWCR_addr_LS) and (self.port0.instype.get() == 1):
            if read_op:
                self.port0.read_data.prepare(self.TWCR)
                self.port0.resp.prepare(1)
            elif write_op:
                self._handle_twcr_write(self.port0.write_data.get() & 0xFF)
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        else:
            self.port0.resp.prepare(0)

    def _handle_twcr_write(self, value):
        # Writing TWINT=1 clears the flag (busy) and -- if TWEN is also
        # set and we're not already mid-operation -- kicks off whichever
        # operation the other bits (TWSTA/TWSTO, or plain data-phase if
        # neither) request. TWWC (bit3) is read-only/hardware-cleared by
        # any TWCR write, matching SPIF/WCOL-style flags elsewhere in
        # this project.
        twint_requested = (value >> 7) & 1
        self.TWEA = (value >> 6) & 1
        self.TWSTA = (value >> 5) & 1
        self.TWSTO = (value >> 4) & 1
        self.TWEN = (value >> 2) & 1
        self.TWIE = value & 1
        self.TWCR = value & 0b01110101  # TWINT/TWWC live in self.TWINT/self.busy-derived state, not TWCR's own bit copy

        if not self.TWEN:
            self.busy = False
            self.state = 'IDLE'
            self.op_mode = None
            return

        if twint_requested and not self.busy:
            self.busy = True
            self.phase_timer = 0
            self.bit_index = 0
            if self.TWSTA:
                self.state = 'START'
                self.substate = 'SDA_LOW'
            elif self.TWSTO:
                self.state = 'STOP'
                self.substate = 'SDA_LOW'
            else:
                self.state = 'DATA'
                self.shift_reg = self.TWDR
                self.substate = 'BIT_LOW'

    # -----------------------------------------------------------------
    def _advance_phase(self):
        """Returns True exactly once, on the cycle a HALF_PERIOD-length
        phase completes, and resets the timer."""
        self.phase_timer += 1
        if self.phase_timer >= self.HALF_PERIOD:
            self.phase_timer = 0
            return True
        return False

    def _complete_op(self, status):
        self.TWSR = (status & 0xF8) | (self.TWSR & 0x03)
        self.busy = False
        self.state = 'IDLE'
        self.TWCR |= 0x80  # TWINT (the flag half; write-1-to-clear semantics live in Memory_access via the busy check above)

    def _run_fsm(self):
        if self.state == 'IDLE':
            return

        if self.state == 'START':
            if self.substate == 'SDA_LOW':
                self._sda_out = 0
                self._scl_out = 1
                if self._advance_phase():
                    self.substate = 'SCL_LOW'
            elif self.substate == 'SCL_LOW':
                self._scl_out = 0
                if self._advance_phase():
                    self.op_mode = None  # fresh address phase follows
                    self._complete_op(0x08)

        elif self.state == 'STOP':
            if self.substate == 'SDA_LOW':
                self._scl_out = 0
                self._sda_out = 0
                if self._advance_phase():
                    self.substate = 'SCL_HIGH'
            elif self.substate == 'SCL_HIGH':
                self._scl_out = 1
                if self._advance_phase():
                    self.substate = 'SDA_HIGH'
            elif self.substate == 'SDA_HIGH':
                self._sda_out = 1
                if self._advance_phase():
                    self.TWSTO = 0  # self-clears on real hardware
                    self.busy = False
                    self.state = 'IDLE'
                    self.op_mode = None
                    # No TWINT/interrupt after a plain STOP, matching
                    # real hardware.

        elif self.state == 'DATA':
            transmitting = (self.op_mode in (None, 'MT'))
            if self.bit_index < 8:
                if self.substate == 'BIT_LOW':
                    self._scl_out = 0
                    if transmitting:
                        bit_val = (self.shift_reg >> (7 - self.bit_index)) & 1
                        self._sda_out = bit_val
                    else:
                        self._sda_out = 1  # release SDA for the slave to drive
                    if self._advance_phase():
                        self.substate = 'BIT_HIGH'
                elif self.substate == 'BIT_HIGH':
                    self._scl_out = 1
                    if not transmitting and self.phase_timer == 0:
                        sampled = self.SDA_sense.get() & 1
                        self.shift_reg = ((self.shift_reg << 1) | sampled) & 0xFF
                    if self._advance_phase():
                        self.bit_index += 1
                        self.substate = 'BIT_LOW'
            else:
                # 9th clock: ACK/NACK
                if self.substate == 'BIT_LOW':
                    self._scl_out = 0
                    if transmitting:
                        self._sda_out = 1  # release; slave pulls low to ACK
                    else:
                        self._sda_out = 0 if self.TWEA else 1  # ack/nack the byte we just received
                    if self._advance_phase():
                        self.substate = 'BIT_HIGH'
                elif self.substate == 'BIT_HIGH':
                    self._scl_out = 1
                    if self._advance_phase():
                        self._finish_data_byte(transmitting)

    def _finish_data_byte(self, transmitting):
        if transmitting:
            acked = (self.SDA_sense.get() & 1) == 0
            byte_sent = self.shift_reg
            if self.op_mode is None:
                # This byte was SLA+RW.
                is_read = byte_sent & 1
                self.op_mode = 'MR' if is_read else 'MT'
                if is_read:
                    status = 0x40 if acked else 0x48
                else:
                    status = 0x18 if acked else 0x20
            else:
                status = 0x28 if acked else 0x30
            self._complete_op(status)
        else:
            self.TWDR = self.shift_reg
            acked_by_us = bool(self.TWEA)
            status = 0x50 if acked_by_us else 0x58
            self._complete_op(status)

    # -----------------------------------------------------------------
    def clock(self):
        self.Memory_access()

        if not self.TWEN:
            self._sda_out = 1
            self._scl_out = 1
        else:
            self._run_fsm()

        self.SCL_drive.prepare(self._scl_out)
        self.SDA_drive.prepare(self._sda_out)
        self.TWI_INT.prepare(1 if (self.TWIE and (self.TWCR & 0x80)) else 0)
