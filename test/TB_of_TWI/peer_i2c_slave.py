# -*- coding: utf-8 -*-
"""
PeerI2CSlave -- a standalone external peer that plays the role of a
simple I2C slave device, used only for testing TWI0 (punxa_atmega328p/TWI.py).
Same category as peer_uart.py / peer_timer.py: test infrastructure, not
part of the CPU package. TWI0 only ever implements master mode (see its
docstring), so this peer is the only "other end of the wire" available --
without it, TWI0's ACK/NACK and data phases would have nothing to talk to.

This peer never stretches the clock and never initiates anything itself
-- it purely reacts to the master's (TWI0's) SCL edges, watching for:

- START condition: SDA falls while SCL is held high.
- STOP condition: SDA rises while SCL is held high.
- Address + R/W byte: 8 bits sampled on SCL rising edges, MSB first.
  ACKs (pulls SDA low during the 9th clock) only if the 7-bit address
  matches `slave_addr`; otherwise stays silent (released/NACK) exactly
  like a real, non-matching I2C device.
- Write (master-transmit) data bytes: sampled the same way, ACKed every
  time (this peer never NACKs an incoming byte); each received byte is
  appended to `self.received_bytes` for the test to assert against.
- Read (master-receive) data bytes: drives `self.read_bytes` (a list
  configured before the test runs, consumed one byte per request, 0xFF
  once exhausted) out on SCL falling-edge-to-rising-edge boundaries,
  then samples the master's own ACK/NACK on the 9th clock to decide
  whether it would keep supplying bytes (informational only -- this
  peer doesn't need to act differently either way, since TWI0 always
  follows a NACK with STOP).
"""
import py4hw


class PeerI2CSlave(py4hw.Logic):
    def __init__(self, parent, name, SCL_drive, SCL_sense, SDA_drive, SDA_sense,
                 slave_addr=0x20, read_bytes=None):
        super().__init__(parent, name)

        self.SCL_drive = self.addOut('SCL_drive', SCL_drive)
        self.SCL_sense = self.addIn('SCL_sense', SCL_sense)
        self.SDA_drive = self.addOut('SDA_drive', SDA_drive)
        self.SDA_sense = self.addIn('SDA_sense', SDA_sense)

        self.slave_addr = slave_addr & 0x7F
        self.read_bytes = list(read_bytes) if read_bytes else []
        self._read_pos = 0

        self.received_bytes = []
        self.last_rw = None  # True = master wants to read, False = write

        self._prev_scl = 1
        self._prev_sda = 1
        self._sda_out = 1  # this peer never drives SCL

        self.state = 'WAIT_START'
        self.bit_index = 0
        self.shift_reg = 0
        self.matched = False

    def _current_read_byte(self):
        if self._read_pos < len(self.read_bytes):
            b = self.read_bytes[self._read_pos]
        else:
            b = 0xFF
        return b

    def clock(self):
        scl = self.SCL_sense.get() & 1
        sda = self.SDA_sense.get() & 1

        held_high = (scl == 1) and (self._prev_scl == 1)
        if held_high and sda != self._prev_sda:
            if self._prev_sda == 1 and sda == 0:
                # START (or repeated START)
                self.state = 'ADDR_BITS'
                self.bit_index = 0
                self.shift_reg = 0
                self._sda_out = 1
            elif self._prev_sda == 0 and sda == 1:
                # STOP
                self.state = 'WAIT_START'
                self._sda_out = 1

        rising = (scl == 1) and (self._prev_scl == 0)
        falling = (scl == 0) and (self._prev_scl == 1)

        if self.state == 'ADDR_BITS':
            if rising and self.bit_index < 8:
                self.shift_reg = ((self.shift_reg << 1) | sda) & 0xFF
                self.bit_index += 1
            elif falling and self.bit_index == 8:
                addr = (self.shift_reg >> 1) & 0x7F
                rw = self.shift_reg & 1
                self.matched = (addr == self.slave_addr)
                self.last_rw = bool(rw)
                self.state = 'ADDR_ACK'
        elif self.state == 'ADDR_ACK':
            # Drive the ACK bit (low) for the duration this 9th clock
            # is asserted, only if our address matched.
            self._sda_out = 0 if self.matched else 1
            if falling:
                if not self.matched:
                    self.state = 'WAIT_START'
                elif self.last_rw:
                    self.state = 'TX_BIT'
                    self.bit_index = 0
                    self._read_pos_byte = self._current_read_byte()
                else:
                    self.state = 'RX_BITS'
                    self.bit_index = 0
                    self.shift_reg = 0
        elif self.state == 'RX_BITS':
            self._sda_out = 1  # release; master drives
            if rising and self.bit_index < 8:
                self.shift_reg = ((self.shift_reg << 1) | sda) & 0xFF
                self.bit_index += 1
            elif falling and self.bit_index == 8:
                self.received_bytes.append(self.shift_reg)
                self.state = 'RX_ACK'
        elif self.state == 'RX_ACK':
            self._sda_out = 0  # this peer always ACKs a received byte
            if falling:
                self.state = 'RX_BITS'
                self.bit_index = 0
                self.shift_reg = 0
        elif self.state == 'TX_BIT':
            byte = getattr(self, '_read_pos_byte', 0xFF)
            if self.bit_index < 8:
                bit_val = (byte >> (7 - self.bit_index)) & 1
                self._sda_out = bit_val
                if rising:
                    pass  # master samples on this edge; nothing to do here
                if falling:
                    self.bit_index += 1
            else:
                self._sda_out = 1  # release for master's ACK/NACK
                if falling:
                    self._read_pos += 1
                    self.state = 'TX_WAIT_NEXT'
        elif self.state == 'TX_WAIT_NEXT':
            # Master will either request another byte (plain data-phase
            # trigger again) or STOP -- both are handled by the
            # start/stop edge-detection and address/data state resets
            # above; a subsequent byte simply re-enters TX_BIT the same
            # way ADDR_ACK does, driven by the master issuing another
            # data-phase operation. For this peer, staying here (SDA
            # released) until the next START/STOP/edge is sufficient.
            self._sda_out = 1
            if falling:
                self.state = 'TX_BIT'
                self.bit_index = 0
                self._read_pos_byte = self._current_read_byte()

        self._prev_scl = scl
        self._prev_sda = sda

        # This peer never drives SCL (no clock stretching implemented).
        self.SCL_drive.prepare(1)
        self.SDA_drive.prepare(self._sda_out)
