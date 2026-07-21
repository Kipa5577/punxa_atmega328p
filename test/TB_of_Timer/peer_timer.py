# -*- coding: utf-8 -*-
"""
PeerTimer -- a standalone external peer used only for testing TimerCounter0
(Timers.py). Same category as peer_uart.py / tb_usart.py: it is test
infrastructure, not part of the CPU package, and it never looks at
TimerCounter0's internal Python state, only at the T0/OC0A/OC0B wires --
so a test asserting against it is a genuine pin-level check of what
actually happens on the wire, not a check against the model's own
bookkeeping.

Two independent roles, mirroring PeerUART's RXD_out/TXD_in split:

- `T0_out` (peer -> DUT): a free-running external clock source the DUT's
  TimerCounter0 can be configured to count on (TCCR0B CS02:00 = 110 or
  111, "External clock on T0 pin"). Controlled with start_clock()/
  stop_clock()/pulse(n); on by default at construction so a CS=6/7 test
  can just poll TCNT0 without any extra setup, the same way usart_tests
  rely on the harness's default PeerUART baud config.

- `OC0A_in` / `OC0B_in` (DUT -> peer): sampled every tick like a logic
  analyzer probing the two output-compare pins. Every level change is
  recorded (tick index + new value) in self.oc0a_edges / self.oc0b_edges,
  since the CPU itself has no way to read those pins back through this
  project's register model -- unlike USART0's UDR0/UCSR0A, which give the
  CPU a legitimate way to self-check RX over the wire, OC0A/OC0B toggling
  can only be confirmed from outside, which is exactly what this peer is
  for.

Run through tb_timers.py: `python3 -i tb_timers.py`, then e.g.
`runAllTests()`.
"""
import py4hw


class PeerTimer(py4hw.Logic):
    def __init__(self, parent, name, T0_out, OC0A_in, OC0B_in,
                 t0_enabled=True, t0_period=6):
        super().__init__(parent, name)

        # From the DUT's point of view: this component's output drives
        # the DUT's T0 pin, and its inputs sample the DUT's OC0A/OC0B
        # pins.
        self.T0_out = self.addOut('T0_out', T0_out)
        self.OC0A_in = self.addIn('OC0A_in', OC0A_in)
        self.OC0B_in = self.addIn('OC0B_in', OC0B_in)

        # --- External clock generator (peer -> T0) ---
        # Free-running square wave: toggles every t0_period ticks while
        # enabled. t0_period is in units of this peer's own clock() calls
        # (i.e. simulator cycles), so CS=111 (rising edge) sees one count
        # every t0_period cycles and CS=110 (falling edge) the same,
        # half a period later.
        self.t0_enabled = t0_enabled
        self.t0_period = t0_period
        self._t0_val = 0
        self._t0_tick = 0

        # One-shot pulse queue, for tests that want exact edge counts
        # instead of (or on top of) the free-running generator. Each
        # entry is consumed on successive clock() calls, driving T0 low
        # then high then low again (one full pulse = one rising + one
        # falling edge), independent of t0_period.
        self._pulse_queue = []
        self._pulse_step = 0

        # --- Pin monitor (OC0A/OC0B -> peer) ---
        self._oc0a_prev = None
        self._oc0b_prev = None
        self.oc0a_edges = []   # list of (tick, new_value)
        self.oc0b_edges = []
        self._tick_count = 0

    # -----------------------------------------------------------------
    # T0 external clock control
    # -----------------------------------------------------------------
    def start_clock(self, period=None):
        if period is not None:
            self.t0_period = period
        self.t0_enabled = True

    def stop_clock(self):
        self.t0_enabled = False

    def pulse(self, n=1):
        """Queue n discrete 0->1->0 pulses on T0, independent of the
        free-running generator. Useful for exact-edge-count tests."""
        for _ in range(n):
            self._pulse_queue.append(1)
            self._pulse_queue.append(0)

    # -----------------------------------------------------------------
    # Pin sampling helpers
    # -----------------------------------------------------------------
    @property
    def oc0a_edge_count(self):
        return len(self.oc0a_edges)

    @property
    def oc0b_edge_count(self):
        return len(self.oc0b_edges)

    def reset_samples(self):
        self.oc0a_edges = []
        self.oc0b_edges = []
        self._oc0a_prev = None
        self._oc0b_prev = None

    # -----------------------------------------------------------------
    def clock(self):
        self._tick_count += 1

        # --- drive T0 ---
        if self._pulse_queue:
            self._t0_val = self._pulse_queue.pop(0)
        elif self.t0_enabled and self.t0_period > 0:
            self._t0_tick += 1
            if self._t0_tick >= self.t0_period:
                self._t0_tick = 0
                self._t0_val ^= 1
        self.T0_out.prepare(self._t0_val)

        # --- sample OC0A / OC0B ---
        oc0a = self.OC0A_in.get() & 1
        if self._oc0a_prev is not None and oc0a != self._oc0a_prev:
            self.oc0a_edges.append((self._tick_count, oc0a))
        self._oc0a_prev = oc0a

        oc0b = self.OC0B_in.get() & 1
        if self._oc0b_prev is not None and oc0b != self._oc0b_prev:
            self.oc0b_edges.append((self._tick_count, oc0b))
        self._oc0b_prev = oc0b
