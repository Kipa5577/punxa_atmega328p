# -*- coding: utf-8 -*-
"""
PeerUART -- a standalone external UART peer used only for testing USART0.

This is test infrastructure only. It watches the DUT's TXD wire and
drives the DUT's RXD wire, emulating an external UART partner in both
asynchronous and synchronous USART modes.
"""
import py4hw


class PeerUART(py4hw.Logic):
    def __init__(self, parent, name, RXD_out, TXD_in, ubrr=103, nbBits=8,
                 parity='Disabled', nbStopBits=1, ticks_per_bit=16, echo=False,
                 USART_CLK=None, usart=None):
        super().__init__(parent, name)

        self.RXD_out = self.addOut('RXD_out', RXD_out)
        self.TXD_in = self.addIn('TXD_in', TXD_in)
        self.clk_in = self.addIn('USART_CLK', USART_CLK) if USART_CLK is not None else None

        self.ubrr = ubrr
        self.nbBits = nbBits
        self.parity = parity
        self.nbStopBits = nbStopBits
        self.ticks_per_bit = ticks_per_bit
        self.echo = echo

        self.usart = usart
        self.UCPOL = 0
        self.sync_mode = False

        self.tick_counter = 0
        self.baud_tick = False
        self.prev_clk = 0

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

    def update_config(self):
        if self.usart is None:
            return

        if hasattr(self.usart, 'UBRR0'):
            self.ubrr = self.usart.UBRR0
        else:
            self.ubrr = ((getattr(self.usart, 'UBRR0H', 0) << 8) |
                         getattr(self.usart, 'UBRR0L', 0))

        self.nbBits = getattr(self.usart, 'nbBits',
                              getattr(self.usart, 'CharSize', self.nbBits))
        self.parity = getattr(self.usart, 'ParityMode',
                              getattr(self.usart, 'parity', self.parity))
        self.nbStopBits = getattr(self.usart, 'nbStopBits',
                                  getattr(self.usart, 'StopBits', self.nbStopBits))
        self.sync_mode = getattr(self.usart, 'opp_mode', 'Asynchronous') != 'Asynchronous'
        self.UCPOL = getattr(self.usart, 'UCPOL0', 0)

        if self.sync_mode:
            self.ticks_per_bit = 1
        else:
            self.ticks_per_bit = 8 if getattr(self.usart, 'U2X0', 0) else 16

    def _build_frame(self, data, ninth_bit=0):
        if self.sync_mode:
            bits = []
            for i in range(self.nbBits):
                bits.append((data >> i) & 1 if i < 8 else (ninth_bit & 1))
            if self.parity != 'Disabled':
                mask = (1 << min(self.nbBits, 8)) - 1
                ones = bin(data & mask).count('1')
                if self.nbBits == 9 and ninth_bit:
                    ones += 1
                p = ones & 1
                bits.append(p if self.parity == 'even' else p ^ 1)
            return bits

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
        frame = self._build_frame(byte, ninth_bit)
        if frame:
            frame[-1] = 0
        self.send_queue.append(frame)

    def send_bad_parity(self, byte, ninth_bit=0):
        frame = self._build_frame(byte, ninth_bit)
        if self.parity != 'Disabled':
            parity_index = 1 + self.nbBits
            if parity_index < len(frame):
                frame[parity_index] ^= 1
        self.send_queue.append(frame)

    def send_break(self, length_bits=None):
        if length_bits is None:
            length_bits = (self.nbBits +
                           (1 if self.parity != 'Disabled' else 0) +
                           self.nbStopBits)
        self.send_queue.append([0] * length_bits)

    def send_raw_frame(self, bits):
        self.send_queue.append(list(bits))

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
        self.tx_index = 0
        self.RXD_val = self.tx_frame[self.tx_index]
        self.tx_index += 1

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
        value = 0
        for i, b in enumerate(self.rx_samples[:nb]):
            value |= (b << i)

        upe = 0
        if self.parity != 'Disabled':
            pbit = self.rx_samples[nb]
            mask = (1 << min(nb, 8)) - 1
            ones = bin(value & mask).count('1')
            if nb == 9 and ((value >> 8) & 1):
                ones += 1
            expected = ones & 1
            if self.parity == 'odd':
                expected ^= 1
            if pbit != expected:
                upe = 1

        stop_bits = self.rx_samples[nb + (0 if self.parity == 'Disabled' else 1):]
        fe = 1 if (stop_bits and stop_bits[0] != 1) else 0

        self.received.append({
            'data': value & 0xFF,
            'rxb8': (value >> 8) & 1 if nb == 9 else 0,
            'fe': fe,
            'upe': upe,
        })

        if self.echo:
            ninth = (value >> 8) & 1 if nb == 9 else 0
            self.send_queue.append(self._build_frame(value & 0xFF, ninth))

    def clock(self):
        self.update_config()

        if self.sync_mode and self.clk_in is not None:
            clk = self.clk_in.get() & 1
            if clk != self.prev_clk:
                self.prev_clk = clk
                self.baud_tick = True
            else:
                self.baud_tick = False
        else:
            self._clock_gen()

        if self.baud_tick:
            self._tx_step()
            self._rx_step()
        self.RXD_out.prepare(self.RXD_val)
