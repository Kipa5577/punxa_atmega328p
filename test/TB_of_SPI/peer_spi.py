# -*- coding: utf-8 -*-
"""
PeerSPI -- a standalone external SPI peer used only for testing SPI
(punxa_atmega328p.SPI). It is test infrastructure, not part of the CPU
package (same category as tb_spi.py itself): it never looks at SPI's
internal Python state (unless a test explicitly opts into `dut`/
`track_format`, exactly like PeerUART's equivalent knobs), only at the
CLK/MOSI/MISO wires, so a test asserting against it is a genuine
protocol-level check of what actually appeared on the wire.

Unlike UART, SPI has no independent baud generator on the peer side --
the DUT (when it's Master, the only mode this SPI class can actually
drive) *is* the clock source, so this peer is purely edge-reactive: it
has no `clock_gen`/`baud_tick` of its own, it just watches CLK and
samples/drives on the correct edge for whatever CPOL/CPHA it's
configured with. It also needs no chip-select modeling: this SPI class
always shifts exactly 8 bits per SPDR write and parks SCK back at idle
between transfers (see SPI.py), so a plain byte-boundary bit counter
that resets after every 8 bits stays in sync with the DUT without a
separate !SS line -- one real difference from a bus with multiple
slaves, where CS is what tells each slave whether the bytes in flight
are meant for it at all.

- `peer.queue_reply(byte)` queues a byte to be shifted out on MISO
  during the *next* transfer (SPI has no separate "queue many bytes
  ahead of time" framing step the way UART does -- each byte is
  shifted out only once a DUT transfer actually consumes it).
- `peer.received` accumulates one dict per byte independently sampled
  and decoded off the DUT's MOSI pin: {'data': ...}.
- `peer.echo = True` makes every received byte automatically become
  the queued reply for the *following* transfer (one-transfer
  latency, inherent to SPI: the peer can't magically already know
  what the master is about to send before it's shifted in) -- lets a
  plain .asm test do transfer-then-transfer-and-compare and be
  entirely self-checking through the normal test_case/final_result
  convention, no test-specific Python needed, the same role `echo`
  plays in PeerUART.
- `peer.on_byte_received(peer, entry) -> bool` is the same escape
  hatch as PeerUART's `on_frame_received`: called right after a byte
  is decoded, return True to suppress the automatic echo and drive
  something else instead (e.g. `test_spi_mode_fault.asm` uses this to
  recognize a sentinel byte and then assert the DUT's own !SS input
  low via `assert_ss_dut()`).
"""
import py4hw


class PeerSPI(py4hw.Logic):
    def __init__(self, parent, name, CLK_in, MOSI_in, MISO_out,
                 CPOL=0, CPHA=0, DORD=0, echo=False, idle_byte=0x00,
                 dut=None, track_format=False,
                 on_byte_received=None,
                 SS_dut_out=None):
        super().__init__(parent, name)

        # From the DUT's point of view: this component samples the
        # DUT's SCK/MOSI outputs and drives the DUT's MISO input --
        # crossed relative to the DUT's own naming, same convention
        # PeerUART uses for RXD/TXD.
        self.CLK = self.addIn('CLK_in', CLK_in)
        self.MOSI = self.addIn('MOSI_in', MOSI_in)
        self.MISO = self.addOut('MISO_out', MISO_out)

        # Optional: drives the DUT's own !SS *input* pin (used only
        # for Master-mode-fault detection -- see SS_logic in SPI.py).
        # None (the default) means this peer never touches it, and the
        # testbench is expected to tie it high itself, same as a real
        # unused NSS pin left pulled up. Only wired up for tests that
        # actually exercise mode fault (see assert_ss_dut() below).
        self.SS_dut_out = self.addOut('SS_dut_out', SS_dut_out) if SS_dut_out is not None else None
        self._ss_dut_countdown = 0

        self.CPOL = CPOL
        self.CPHA = CPHA
        self.DORD = DORD
        self.echo = echo
        self.idle_byte = idle_byte & 0xFF

        # See PeerUART's identical dut/track_format rationale: some
        # tests reconfigure the DUT's CPOL/CPHA/DORD mid-run (sweeping
        # all 4 clock modes, or DORD 0/1) and the point is to check the
        # DUT's own shift logic against each configuration, not to
        # hand-roll a second parallel "what did the test just poke into
        # SPCR" tracker. Off by default; a test enables it explicitly.
        self.dut = dut
        self.track_format = track_format

        # Same role as PeerUART's on_frame_received: called right after
        # a byte is decoded off MOSI, entry is the dict just appended
        # to self.received. Return True to suppress the automatic echo
        # for *this* byte (the callback is responsible for queueing
        # whatever it wants via queue_reply/assert_ss_dut/etc.); return
        # False/None to let the normal echo (if self.echo) handle it.
        self.on_byte_received = on_byte_received

        self.send_queue = []            # bytes queued for future transfers
        self.received = []              # list of dicts: {'data': ...}

        self.shift_reg = 0
        self.bit_counter = 0
        self.current_tx_byte = self.send_queue.pop(0) if self.send_queue else self.idle_byte

        self.lastCLK = CPOL
        self.MISO_val = 0
        self._present_bit()             # pre-load bit 0, for CPHA==0's
                                         # setup-before-first-edge

    # -----------------------------------------------------------------
    # Test-facing API
    # -----------------------------------------------------------------
    def queue_reply(self, byte):
        """Queue a byte to be shifted out on MISO during a future
        transfer (consumed in FIFO order, one byte per DUT transfer)."""
        self.send_queue.append(byte & 0xFF)

    def set_immediate_reply(self, byte):
        """Overrides what will be shifted out on MISO during the very
        *next* transfer (the one already loaded, ahead of anything in
        send_queue) -- useful right after construction, before any
        clock cycles have run, to seed the first transfer's reply
        without waiting a full extra round-trip through the queue."""
        self.current_tx_byte = byte & 0xFF
        self.bit_counter = 0
        self._present_bit()

    def assert_ss_dut(self, cycles=4):
        """Pulls the DUT's own !SS input low for `cycles` ticks, then
        releases it back high -- simulates another master contending
        for the bus, for exercising SPI's mode-fault detection. Needs
        SS_dut_out to have been wired at construction time."""
        if self.SS_dut_out is None:
            raise Exception('PeerSPI: SS_dut_out was not wired -- pass SS_dut_out= at construction to use assert_ss_dut()')
        self._ss_dut_countdown = cycles

    # -----------------------------------------------------------------
    def _present_bit(self):
        idx = self.bit_counter
        if self.DORD == 1:
            bit = (self.current_tx_byte >> idx) & 1
        else:
            bit = (self.current_tx_byte >> (7 - idx)) & 1
        self.MISO_val = bit

    def _finish_byte(self):
        byte = self.shift_reg & 0xFF
        entry = {'data': byte}
        self.received.append(entry)

        handled = False
        if self.on_byte_received is not None:
            handled = bool(self.on_byte_received(self, entry))

        if self.echo and not handled:
            self.send_queue.append(byte)

        self.bit_counter = 0
        self.shift_reg = 0
        self.current_tx_byte = self.send_queue.pop(0) if self.send_queue else self.idle_byte
        # Present bit 0 of the next byte right away: harmless for
        # CPHA==1 (its own leading edge will overwrite this before
        # it's ever sampled) and required for CPHA==0 (data must be
        # valid *before* that mode's first edge, and there's no !SS
        # transition here to hook a "just got selected" moment onto).
        self._present_bit()

    def clock(self):
        if self.track_format and self.dut is not None:
            # Safe every cycle, same reasoning as PeerUART's
            # track_format: CPOL/CPHA/DORD are only ever consumed at a
            # bit-edge boundary (_present_bit/the sample branch below),
            # so this can't tear a transfer already in progress as long
            # as the test itself doesn't change SPCR mid-transfer (none
            # of the tests that use this do).
            self.CPOL = self.dut.CPOL
            self.CPHA = self.dut.CPHA
            self.DORD = self.dut.DORD

        if self._ss_dut_countdown > 0:
            self._ss_dut_countdown -= 1
            if self.SS_dut_out is not None:
                self.SS_dut_out.prepare(0)
        elif self.SS_dut_out is not None:
            self.SS_dut_out.prepare(1)

        clk_level = self.CLK.get() & 1

        leading_edge = (self.lastCLK == self.CPOL) and (clk_level != self.CPOL)
        trailing_edge = (self.lastCLK != self.CPOL) and (clk_level == self.CPOL)

        sample_edge = leading_edge if self.CPHA == 0 else trailing_edge
        setup_edge = trailing_edge if self.CPHA == 0 else leading_edge

        if sample_edge and self.bit_counter < 8:
            incoming_bit = self.MOSI.get() & 1
            if self.DORD == 1:
                self.shift_reg = (self.shift_reg >> 1) | (incoming_bit << 7)
            else:
                self.shift_reg = ((self.shift_reg << 1) & 0xFF) | incoming_bit
            self.bit_counter += 1
            if self.bit_counter == 8:
                self._finish_byte()

        if setup_edge and self.bit_counter < 8:
            self._present_bit()

        self.lastCLK = clk_level
        self.MISO.prepare(self.MISO_val)
