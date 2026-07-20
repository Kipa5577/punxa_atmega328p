# -*- coding: utf-8 -*-
"""
PeerUART -- a standalone external UART peer used only for testing
USART0. It is test infrastructure, not part of the CPU package (same
category as tb_usart.py itself): it never looks at USART0's internal
Python state, only at the RXD/TXD wires, so a test asserting against it
is a genuine protocol-level check of what actually appeared on the wire.

- `peer.send(byte)` / `peer.send9(byte, ninth_bit)` queue a frame to be
  bit-banged out onto the DUT's RXD pin.
- `peer.send_bad_stop(byte)` / `peer.send_bad_parity(byte)` queue
  deliberately malformed frames, for exercising the DUT's FE0/UPE0
  detection from the outside.
- `peer.received` accumulates one dict per frame independently sampled
  and decoded off the DUT's TXD pin: {'data', 'rxb8', 'fe', 'upe'}.

Configure `ubrr`/`nbBits`/`parity`/`nbStopBits`/`ticks_per_bit` to match
whatever the assembly test under `usart_tests/` configures the DUT with
(same UBRR0/UCSR0C semantics, just as plain Python attributes here since
this peer has no CPU of its own to program it through registers).
"""
import py4hw


class PeerUART(py4hw.Logic):
    def __init__(self, parent, name, RXD_out, TXD_in, ubrr=103, nbBits=8,
                 parity='Disabled', nbStopBits=1, ticks_per_bit=16, echo=False,
                 dut=None, track_format=False, track_baud=False,
                 on_frame_received=None):
        super().__init__(parent, name)

        # When True, every byte the peer receives off the DUT's TXD is
        # automatically queued straight back out to the DUT's RXD. Lets
        # a plain .asm test do TX-then-RX-and-compare and be entirely
        # self-checking through the normal test_case/final_result
        # convention, with no test-specific Python needed.
        self.echo = echo

        # From the DUT's point of view: this component's output drives
        # the DUT's RXD pin, and its input samples the DUT's TXD pin.
        self.RXD_out = self.addOut('RXD_out', RXD_out)
        self.TXD_in = self.addIn('TXD_in', TXD_in)

        self.ubrr = ubrr
        self.nbBits = nbBits
        self.parity = parity
        self.nbStopBits = nbStopBits
        self.ticks_per_bit = ticks_per_bit

        # A real external UART peer has no way to "read" the DUT's
        # config registers -- both ends just have to already agree on
        # the frame format out of band (which is exactly what
        # ubrr/nbBits/parity/nbStopBits above are: this Python object's
        # side of that prior agreement). But a handful of tests
        # deliberately reconfigure the DUT's UCSZ/UPM/USBS (or its baud
        # rate) mid-run (e.g. test_usart_char_size_mask.asm sweeping
        # 5/6/7-bit frames, test_usart_dynamic_baud.asm / baud_sweep
        # changing UBRR0), and the whole point there is to check the
        # DUT's own framing/baud logic against each configuration --
        # not to hand-roll a second, parallel bit-exact model of
        # exactly when each register write takes effect. `dut` +
        # `track_format`/`track_baud` let this peer mirror the DUT's
        # live frame shape / baud rate every cycle instead: both
        # default off, and deliberately independent of each other so a
        # test like baud_sabotage (which specifically wants the peer
        # to *not* follow the DUT's baud rate, to catch the resulting
        # mismatch) isn't affected by enabling only `track_format`
        # elsewhere.
        self.dut = dut
        self.track_format = track_format
        self.track_baud = track_baud

        # Optional callback: on_frame_received(peer, entry) -> bool,
        # invoked right after a completed RX frame is decoded and
        # appended to self.received (entry is that same dict). Lets a
        # test-specific driver intercept a particular frame (e.g. a
        # sentinel/trigger byte) and do something other than the
        # default echo -- reply with deliberately bad framing, hold
        # the line low to simulate a break, etc. -- without needing a
        # second, parallel echo-suppression mechanism. Return True to
        # suppress the automatic echo for *this* frame (the callback
        # is responsible for queueing whatever response it wants via
        # send/send9/send_bad_parity/send_bad_stop/send_break);
        # return False (or None) to let the normal echo (if self.echo)
        # handle it as usual. Not called at all if left None (the
        # default) -- every prior test's behavior is unaffected.
        self.on_frame_received = on_frame_received

        self.tick_counter = 0
        self.baud_tick = False

        self.RXD_val = 1                # idle high

        self.send_queue = []            # list of prebuilt bit-frames
        self.tx_frame = None
        self.tx_index = 0
        self.tx_subtick = 0

        self.received = []              # list of dicts: data/rxb8/fe/upe
        self.rx_active = False
        self.rx_start_confirmed = False
        self.rx_subtick = 0
        self.rx_samples = []
        self.rx_frame_len = 0

    # -----------------------------------------------------------------
    # Queueing outbound frames (peer -> DUT.RXD)
    # -----------------------------------------------------------------
    def _build_frame(self, data, ninth_bit=0):
        bits = [0]
        for i in range(self.nbBits):
            bits.append((data >> i) & 1 if i < 8 else (ninth_bit & 1))
        if self.parity != 'Disabled':
            mask = (1 << min(self.nbBits, 8)) - 1
            ones = bin(data & mask).count('1')
            if self.nbBits == 9 and ninth_bit:
                ones += 1
            p = ones & 1
            bits.append(p if self.parity == 'even' else p ^ 1)
        bits += [1] * self.nbStopBits
        return bits

    def send(self, byte, ninth_bit=0):
        self.send_queue.append(self._build_frame(byte, ninth_bit))

    def send9(self, byte, ninth_bit):
        self.send(byte, ninth_bit)

    def send_bad_stop(self, byte, ninth_bit=0):
        """Corrupt the final stop bit -> should trigger the DUT's FE0."""
        frame = self._build_frame(byte, ninth_bit)
        frame[-1] = 0
        self.send_queue.append(frame)

    def send_bad_parity(self, byte, ninth_bit=0):
        """Flip the parity bit -> should trigger the DUT's UPE0. Only
        meaningful if self.parity != 'Disabled'."""
        frame = self._build_frame(byte, ninth_bit)
        parity_index = 1 + self.nbBits
        if self.parity != 'Disabled':
            frame[parity_index] ^= 1
        self.send_queue.append(frame)

    def send_break(self, bit_times=None):
        """Hold RXD low for `bit_times` bit periods (no start/stop
        framing at all -- just a raw run of dominant/0 bits), then
        release back to idle-high. Used to simulate a real break
        condition from the outside.

        Defaults to exactly the number of bit-periods the DUT's own
        configured frame needs (1 start + nbBits + parity? + stop
        bits, from `self.dut` if given, else the plain 8N1 default of
        10) -- deliberately not a single bit-period more. Any amount of
        low signal *beyond* what the DUT's receiver consumes for one
        full (bad) frame leaves it sitting on a still-low line the
        instant it goes back to idle, which its start-bit detector
        reads as the start of a *second* frame and keeps consuming
        break time frame-by-frame for as long as the line stays low --
        real UART behavior, not a bug, but not what this helper is for
        (a single, cleanly-bounded break frame with nothing left over).
        """
        if bit_times is None:
            if self.dut is not None:
                nb = self.dut.nbBits
                has_parity = self.dut.ParityMode != 'Disabled'
                stop = self.dut.nbStopBits
            else:
                nb, has_parity, stop = 8, False, 1
            bit_times = 1 + nb + (1 if has_parity else 0) + stop
        self.send_queue.append([0] * bit_times)

    # -----------------------------------------------------------------
    def _clock_gen(self):
        self.baud_tick = False
        if self.tick_counter >= self.ubrr:
            self.baud_tick = True
            self.tick_counter = 0
        else:
            self.tick_counter += 1

    def _begin_next_frame(self):
        self.tx_frame = self.send_queue.pop(0)
        self.tx_subtick = 0
        self.RXD_val = self.tx_frame[0]
        self.tx_index = 1

    def _tx_step(self):
        if self.tx_frame is None:
            if self.send_queue:
                self._begin_next_frame()
            else:
                self.RXD_val = 1
            return

        self.tx_subtick += 1
        if self.tx_subtick < self.ticks_per_bit:
            return
        self.tx_subtick = 0

        if self.tx_index >= len(self.tx_frame):
            # Same fix as USART0.TX_logic: merge finish + start-next
            # into one tick so back-to-back frames don't truncate the
            # previous frame's stop bit.
            self.tx_frame = None
            self.tx_index = 0
            if self.send_queue:
                self._begin_next_frame()
            else:
                self.RXD_val = 1
            return

        self.RXD_val = self.tx_frame[self.tx_index]
        self.tx_index += 1

    def _rx_step(self):
        txd = self.TXD_in.get() & 1

        if not self.rx_active:
            if txd == 0:
                self.rx_active = True
                self.rx_start_confirmed = False
                self.rx_subtick = 0
                self.rx_samples = []
                self.rx_frame_len = (self.nbBits +
                                      (1 if self.parity != 'Disabled' else 0) +
                                      self.nbStopBits)
            return

        self.rx_subtick += 1
        half = self.ticks_per_bit >> 1

        if not self.rx_start_confirmed and self.rx_subtick == half:
            if txd == 1:
                self.rx_active = False
            else:
                self.rx_subtick = 0
                self.rx_start_confirmed = True
            return

        if self.rx_subtick == self.ticks_per_bit:
            self.rx_subtick = 0
            self.rx_samples.append(txd)
            if len(self.rx_samples) == self.rx_frame_len:
                self._finish_rx()
                self.rx_active = False

    def _finish_rx(self):
        nb = self.nbBits
        data_bits = self.rx_samples[:nb]
        idx = nb
        value = 0
        for i, b in enumerate(data_bits):
            value |= (b << i)

        upe = 0
        if self.parity != 'Disabled':
            pbit = self.rx_samples[idx]
            idx += 1
            mask = (1 << min(nb, 8)) - 1
            ones = bin(value & mask).count('1')
            if nb == 9 and ((value >> 8) & 1):
                ones += 1
            expected = ones & 1
            if self.parity == 'odd':
                expected ^= 1
            if pbit != expected:
                upe = 1

        stop_bits = self.rx_samples[idx:]
        fe = 1 if (stop_bits and stop_bits[0] != 1) else 0

        self.received.append({
            'data': value & 0xFF,
            'rxb8': (value >> 8) & 1 if nb == 9 else 0,
            'fe': fe,
            'upe': upe,
        })
        entry = self.received[-1]

        handled = False
        if self.on_frame_received is not None:
            handled = bool(self.on_frame_received(self, entry))

        if self.echo and not handled:
            ninth = (value >> 8) & 1 if nb == 9 else 0
            self.send_queue.append(self._build_frame(value & 0xFF, ninth))

    def clock(self):
        if self.track_format and self.dut is not None:
            # Mirror the DUT's *current* frame shape. Safe to do every
            # cycle unconditionally: nbBits/parity/nbStopBits are only
            # ever actually consumed at the instant a new frame begins
            # (_begin_next_frame / the start-bit branch in _rx_step),
            # so as long as the test itself doesn't change the DUT's
            # UCSZ/UPM/USBS *while* a frame is mid-flight (none of the
            # tests that use this do), this can't tear a frame already
            # in progress.
            self.nbBits = self.dut.nbBits
            self.parity = self.dut.ParityMode
            self.nbStopBits = self.dut.nbStopBits

        if self.track_baud and self.dut is not None:
            # Same idea, for the baud rate: mirror UBRR0/ticks_per_bit
            # (the latter covers U2X0) every cycle. `self.tick_counter`
            # is just compared against the (possibly new) `self.ubrr`
            # on the very next `_clock_gen()` call below, so this is
            # inherently safe the same way the DUT's *own* baud
            # generator has no double-buffering either (see
            # test_usart_baud_sabotage.asm) -- as long as the test only
            # changes UBRR0 between frames (every test using this flag
            # does), there's nothing to tear.
            self.ubrr = self.dut.UBRR0
            self.ticks_per_bit = self.dut.ticks_per_bit

        self._clock_gen()
        if self.baud_tick:
            self._tx_step()
            self._rx_step()
        self.RXD_out.prepare(self.RXD_val)
