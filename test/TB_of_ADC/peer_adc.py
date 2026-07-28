# -*- coding: utf-8 -*-
"""
PeerADC -- a standalone external peer used to test the real ADC class
(ADC.py) at the pin level, same category as peer_timer.py/peer_gpio.py/
peer_i2c_slave.py: test infrastructure, not part of the CPU package.

ADC.py's own class docstring explains the scope decision this peer
exists to support: this is a digital HDL simulator with no analog front
end, so ADC0-ADC7 are wires carrying an already-quantized 10-bit code
(0-1023) rather than a real voltage -- PeerADC is what supplies that
code, standing in for "whatever the real ADC's sample-and-hold +
successive-approximation ladder would have produced" the same way
PeerUART supplies already-framed bits instead of simulating a real
serial line's electrical edges.

Two independent roles, mirroring PeerGPIO's val_in/ext_out split:

- `set_channel(ch, code)` (peer -> DUT): drive a fixed 10-bit code onto
  one of the eight ADC0-ADC7 wires. Static per test by default (set once
  before the CPU program runs, matching PeerTimer's t0_period/PeerGPIO's
  init_ext_out being fixed at construction) -- `set_channel()` can also
  be called from a running interactive session for a test that wants to
  change the input mid-run.

- `T0_COMPA`/`T0_OVF`/`T1_COMPB`/`T1_OVF`/`T1_CAPT`/`ACO`/`INT0` pulse
  helpers (peer -> DUT): drive a single-cycle rising edge onto one of
  ADC's six auto-trigger source wires (ADTS2:0 selects which one is
  live), for exercising ADATE=1 auto-trigger mode without needing the
  real Timer0/Timer1/Analog Comparator/INT0 peripherals wired in yet --
  exactly the kind of standalone, synthetic-source testing the project's
  own task list called for on the interrupt controller ("test standalone
  against synthetic interrupt-source wires").

Run through tb_adc_tests.py: `python3 -i tb_adc_tests.py`, then e.g.
`runAllTests()`.
"""
import py4hw


class PeerADC(py4hw.Logic):
    def __init__(self, parent, name,
                 ADC0_out, ADC1_out, ADC2_out, ADC3_out, ADC4_out,
                 ADC5_out, ADC6_out, ADC7_out,
                 ACO_out, INT0_out, T0_COMPA_out, T0_OVF_out,
                 T1_COMPB_out, T1_OVF_out, T1_CAPT_out,
                 init_codes=None, autopulse=None):
        super().__init__(parent, name)

        self._chan_wires = [
            self.addOut(f'ADC{i}_out', w)
            for i, w in enumerate([ADC0_out, ADC1_out, ADC2_out, ADC3_out,
                                    ADC4_out, ADC5_out, ADC6_out, ADC7_out])
        ]
        self._codes = [0] * 8
        if init_codes:
            for ch, code in init_codes.items():
                self._codes[ch] = code & 0x3FF

        self._trig_wires = {
            'ACO': self.addOut('ACO_out', ACO_out),
            'INT0': self.addOut('INT0_out', INT0_out),
            'T0_COMPA': self.addOut('T0_COMPA_out', T0_COMPA_out),
            'T0_OVF': self.addOut('T0_OVF_out', T0_OVF_out),
            'T1_COMPB': self.addOut('T1_COMPB_out', T1_COMPB_out),
            'T1_OVF': self.addOut('T1_OVF_out', T1_OVF_out),
            'T1_CAPT': self.addOut('T1_CAPT_out', T1_CAPT_out),
        }
        self._trig_levels = {k: 0 for k in self._trig_wires}
        # A pulse is high for exactly one clock() call then released --
        # queued as a countdown so multiple pulse() calls in the same
        # cycle don't clobber each other.
        self._pulse_hold = {k: 0 for k in self._trig_wires}

        # Free-running periodic pulse on one trigger source, for tests
        # that need a hardware-source auto-trigger firing repeatedly
        # without any Python-side mid-test synchronization -- the .asm
        # side just arms ADATE+ADTS and polls ADIF, same spirit as
        # PeerTimer's free-running T0_out clock. Static-per-test only
        # (set via peer_kwargs), same convention as everything else this
        # peer exposes.
        self._autopulse_source = autopulse['source'] if autopulse else None
        self._autopulse_period = autopulse['period'] if autopulse else 0
        self._autopulse_tick = 0

    # -----------------------------------------------------------------
    def set_channel(self, ch, code):
        """code: 0-1023, the digitized value this channel should read as."""
        self._codes[ch] = code & 0x3FF

    def pulse(self, source, hold_cycles=1):
        """Raise the named trigger source (see ADC.py's _trigger_wires
        keys: 'ACO','INT0','T0_COMPA','T0_OVF','T1_COMPB','T1_OVF',
        'T1_CAPT') for hold_cycles clock() calls, then release it."""
        self._pulse_hold[source] = hold_cycles

    # -----------------------------------------------------------------
    def clock(self):
        for i, wire in enumerate(self._chan_wires):
            wire.prepare(self._codes[i])

        if self._autopulse_source is not None and self._autopulse_period > 0:
            self._autopulse_tick += 1
            if self._autopulse_tick >= self._autopulse_period:
                self._autopulse_tick = 0
                self._pulse_hold[self._autopulse_source] = max(
                    self._pulse_hold[self._autopulse_source], 1)

        for name, wire in self._trig_wires.items():
            if self._pulse_hold[name] > 0:
                self._pulse_hold[name] -= 1
                level = 1
            else:
                level = 0
            wire.prepare(level)
            self._trig_levels[name] = level
