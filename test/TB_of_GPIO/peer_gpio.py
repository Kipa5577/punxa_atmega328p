# -*- coding: utf-8 -*-
"""
PeerGPIO -- a standalone external peer used to test the real GPIO class
(GPIO.py) at the pin level, same category as peer_timer.py/peer_uart.py/
peer_i2c_slave.py: test infrastructure, not part of the CPU package. It
never touches GPIO's internal Python state (PORTx/DDRx ints) directly --
only the four physical pin wires per port GPIO.py now exposes
(<P>_val/<P>_oe out, <P>_ext_in/<P>_ext_oe in) -- so a test asserting
against it is a genuine pin-level check, not a check against the model's
own bookkeeping.

Two independent roles per port (B/C/D), mirroring PeerTimer's
T0_out/OC0A_in split and PeerUART's RXD_out/TXD_in split:

- `<P>_val_in` / `<P>_oe_in` (DUT -> peer): what GPIO is actually
  driving on that port's 8 pins right now, and which bits it's actually
  driving (oe=1) vs leaving as inputs (oe=0). Every change is recorded
  (tick, new masked value) in self.<p>_edges, since the CPU itself has
  no way to read this back (PORTx readback tells you what was written,
  not what's on the physical pin -- GPIO.PINx already folds that back
  in for output bits, but a peer watching from outside is the only way
  to independently confirm the *drive*, not just GPIO's own bookkeeping
  of its drive).

- `<P>_ext_out` / `<P>_ext_oe_out` (peer -> DUT): the peer's own drive
  onto that port's pins, and which bits it's actively driving. Static
  per test by default (set once via drive()/float_bits() before the
  test runs, matching PeerTimer's t0_period being fixed at construction
  and PeerUART's baud being fixed at construction) -- dynamic mid-test
  redriving is possible via the same methods if a future test needs it,
  same spirit as PeerTimer's start_clock()/stop_clock()/pulse().

Bit convention: all values are 8-bit ints, bit i corresponds to pin i of
that port (PORTB bit 0 = PB0, etc.) -- matches the real AVR register
layout GPIO.py already uses for PORTx/DDRx/PINx.

Run through tb_gpio_tests.py: `python3 -i tb_gpio_tests.py`, then e.g.
`runAllTests()`.
"""
import py4hw


class PeerGPIO(py4hw.Logic):
    def __init__(self, parent, name,
                 val_in, oe_in, ext_out, ext_oe_out,
                 init_ext_out=0x00, init_ext_oe=0x00):
        super().__init__(parent, name)

        # From the DUT's point of view: these two inputs sample what
        # GPIO is driving; these two outputs are what the peer drives
        # onto GPIO's ext_in/ext_oe input pins.
        self.val_in = self.addIn('val_in', val_in)
        self.oe_in = self.addIn('oe_in', oe_in)
        self.ext_out = self.addOut('ext_out', ext_out)
        self.ext_oe_out = self.addOut('ext_oe_out', ext_oe_out)

        self._ext_val = init_ext_out & 0xFF
        self._ext_oe = init_ext_oe & 0xFF

        self._prev_masked = None
        self.edges = []          # list of (tick, masked_value, oe)
        self._tick_count = 0

    # -----------------------------------------------------------------
    # Peer -> DUT: drive / float individual bits or the whole byte
    # -----------------------------------------------------------------
    def drive(self, value, oe_mask=0xFF):
        """Drive `value` onto the bits selected by oe_mask; bits not in
        oe_mask are left floating (matches whatever they were before)."""
        value &= 0xFF
        oe_mask &= 0xFF
        self._ext_val = (self._ext_val & ~oe_mask) | (value & oe_mask)
        self._ext_oe = self._ext_oe | oe_mask

    def drive_bit(self, bit, value):
        mask = 1 << bit
        if value:
            self._ext_val |= mask
        else:
            self._ext_val &= ~mask & 0xFF
        self._ext_oe |= mask

    def float_bits(self, mask):
        """Stop driving the bits in mask -- they become floating (subject
        to GPIO's own pull-up per the PIN-read semantics in GPIO.py)."""
        self._ext_oe &= ~mask & 0xFF

    def float_all(self):
        self._ext_oe = 0x00

    # -----------------------------------------------------------------
    # DUT -> peer: observed drive
    # -----------------------------------------------------------------
    @property
    def edge_count(self):
        return len(self.edges)

    @property
    def last_driven(self):
        """(value, oe) as last sampled -- value bits are only meaningful
        where the corresponding oe bit is 1."""
        if self._prev_masked is None:
            return (0, 0)
        return self._prev_masked

    def reset_samples(self):
        self.edges = []
        self._prev_masked = None

    # -----------------------------------------------------------------
    def clock(self):
        self._tick_count += 1

        # --- drive onto GPIO's ext_in/ext_oe ---
        self.ext_out.prepare(self._ext_val)
        self.ext_oe_out.prepare(self._ext_oe)

        # --- sample what GPIO is driving ---
        val = self.val_in.get() & 0xFF
        oe = self.oe_in.get() & 0xFF
        masked = (val & oe, oe)
        if self._prev_masked is not None and masked != self._prev_masked:
            self.edges.append((self._tick_count, masked[0], masked[1]))
        self._prev_masked = masked
