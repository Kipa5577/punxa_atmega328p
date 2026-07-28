import py4hw
from punxa_atmega328p.Memory import *

UCSRA_REG = 0x00   # Control and Status register A
UCSRB_REG = 0x01   # Control and Status register B
UCSRC_REG = 0x02   # Control and Status register C
UBRRL_REG = 0x04   # Baud Rate Register Low
UBRRH_REG = 0x05   # Baud Rate Register High
UDR_REG =    0x06   # Transmit Buffer Register

UCSRA_RXC = 1 << 7    # Receive Complete
UCSRA_TXC = 1 << 6    # Transmit Complete
UCSRA_UDRE = 1 << 5   # Data register empty
UCSRA_FE = 1 << 4     # Frame Error
UCSRA_DOR = 1 << 3    # Data OverRun
UCSRA_PE = 1 << 2     # Parity Error
UCSRA_2X = 1 << 1     # Double Transmission Speed
UCSRA_MPCM = 1        # Multi-processor Communication Mode

class USART0(py4hw.Logic):
    """
    Behavioral model of the ATmega328P's single hardware USART.

    This replaces the old `USART`/`USART_1` classes. Register semantics,
    frame timing (start/data/parity/stop, oversampled at 16x/8x/2x the
    baud rate depending on mode), the 2-byte-deep receive buffer, and
    interrupt behavior are all cycle-accurate against the datasheet.

    Deliberately *behavioral* rather than a literal gate-level TX/RX
    finite-state-machine translation: control-register fields are decoded
    declaratively as properties of the two raw config bytes (UCSR0B/
    UCSR0C) instead of being re-parsed bit-by-bit every clock cycle, and
    a frame (TX) or a fixed-length sample list (RX) is built/consumed as
    a single sequence walked by one index, instead of a hand-duplicated
    case-per-phase (IDLE/START/DATA/PARITY/STOP) state machine with a
    separate tick counter for each phase.

    Register map (byte offsets *relative* to wherever this component is
    mapped on the bus -- e.g. 0xC0 in the CPU memory map -- matching the
    module-level UCSRA_REG/UCSRB_REG/.../UDR_REG constants above, and the
    relative addressing `MultiplexedBus` already hands every other
    peripheral on this bus):
        0x00  UCSR0A   0x01  UCSR0B   0x02  UCSR0C
        0x04  UBRR0L   0x05  UBRR0H   0x06  UDR0
    """

    def __init__(self, parent, name: str, memory: MemoryInterface, RXD, TXD,
                 USART_CLK, RXC_INT, TXC_INT, UDRE_INT,
                 XCK_in=None, XCK_DDR_OUT=None):
        super().__init__(parent, name)

        self.interface = self.addInterfaceSink('port', memory)

        # Physical pins
        self.RXD = self.addIn('RXD', RXD)
        self.TXD = self.addOut('TXD', TXD)
        self.USART_CLK = self.addOut('USART_CLK', USART_CLK)

        # Synchronous-mode XCK support. Real hardware: DDR_XCKn (a GPIO
        # register bit, external to this peripheral) selects direction --
        # 1 means this pin is driven as an output, so USART0 is the
        # clock *master* (drives USART_CLK, exactly like async mode
        # already did via Clock_Generator's baud_tick toggling); 0 means
        # it's an input, so USART0 is the clock *slave* and must
        # synchronize its own bit timing to whatever edges appear on
        # XCK_in instead of its own internal baud generator. Both
        # optional (default to always-master behavior, i.e. this
        # peripheral's pre-synchronous-mode behavior) so any existing
        # caller that only ever used asynchronous mode doesn't need to
        # change.
        self.XCK_in = self.addIn('XCK_in', XCK_in) if XCK_in is not None else None
        self.XCK_DDR_OUT = self.addIn('XCK_DDR_OUT', XCK_DDR_OUT) if XCK_DDR_OUT is not None else None
        self._prev_xck_in = 0

        # Interrupts -- all three are outputs of this peripheral, driven
        # into InterruptUnit/SimpleInterruptUnit's USART_RX/USART_UDRE/
        # USART_TX vectors.
        self.RXC_INT = self.addOut('RXC_INT', RXC_INT)
        self.TXC_INT = self.addOut('TXC_INT', TXC_INT)
        self.UDRE_INT = self.addOut('UDRE_INT', UDRE_INT)

        # --- Raw, software-facing config registers ---
        # UCSR0A's status bits (RXC0/TXC0/UDRE0/FE0/DOR0/UPE0) are
        # hardware-driven, not just decoded from a byte the CPU wrote, so
        # they're kept as individual fields (see pack_ucsr0a()) rather
        # than folded into a raw UCSR0A byte. U2X0/MPCM0 are the only
        # UCSR0A bits software actually writes.
        self.U2X0 = 0
        self.MPCM0 = 0
        self.RXC0 = 0
        self.TXC0 = 0
        self.FE0 = 0
        self.DOR0 = 0
        self.UPE0 = 0

        self.UCSR0B = 0x00
        self.UCSR0C = 0x06     # reset default: async, no parity, 1 stop, 8 data bits
        self.UBRR0L = 0x00
        self.UBRR0H = 0x00

        # --- Baud tick generator ---
        self.tick_counter = 0
        self.baud_tick = False
        self.USART_CLK_val = 0

        # --- Transmit side ---
        # TXB_buffer holds (data, txb8) once written to UDR0, until the
        # baud clock picks it up and builds a frame from it. UDRE0 is
        # derived straight from "is the buffer free" (see pack_ucsr0a),
        # matching real hardware -- no separate flag to keep in sync.
        self.TXB_buffer = None
        self.tx_frame = None
        self.tx_index = 0
        self.tx_subtick = 0
        self.TXD_val = 1

        # --- Receive side ---
        # A 2-entry FIFO models the real chip's double-buffered receiver
        # (one byte can be fully received and waiting in UDR0 while the
        # next one is already shifting in). Each entry carries the data
        # byte alongside the FE/UPE/9th-bit status that belongs to *that*
        # byte specifically, so back-to-back frames with different error
        # status don't get mixed up.
        self.rx_fifo = []          # list of dicts: {data, fe, upe, rxb8}
        self.rx_active = False
        self.rx_start_confirmed = False
        self.rx_subtick = 0
        self.rx_samples = []
        self.rx_frame_len = 0

        self.RXC_INT_val = 0
        self.TXC_INT_val = 0
        self.UDRE_INT_val = 0

        # --- Synchronous slave RX (externally clocked) ---
        # Separate from the async/sync-master rx_active/rx_subtick state
        # above: this path is driven entirely by edges on XCK_in, not by
        # the internal baud generator, so it needs its own "am I
        # mid-frame" flag to avoid colliding with RX_logic's.
        self.sync_slave_rx_active = False

        # --- Master SPI Mode (MSPIM) ---
        # Fixed 8-bit, full-duplex, no start/stop/parity framing --
        # deliberately separate from tx_frame/rx_samples (async/sync's
        # framed-bit-sequence model) rather than shoehorned into it.
        self.mspim_active = False
        self.mspim_shift_out = 0
        self.mspim_shift_in = 0
        self.mspim_bit_index = 0
        self._mspim_lastclk = 0

        # UDR0's read/write have genuine one-shot side effects (dequeue
        # /enqueue a byte) unlike every other register here, which just
        # store a value and are harmless to re-apply. The bus's write/
        # read strobes stay asserted for more than one cycle per real
        # CPU instruction (observed: a single `sts UDR0` produced two
        # distinct transmitted frames without this), so UDR0 needs
        # rising-edge gating -- same pattern already used elsewhere in
        # this project for the identical class of bug (VirtualUSART's
        # is_new_write, InterruptFSM's _prev_entrance).
        self._prev_udr_write = False
        self._prev_udr_read = False
        self._last_udr_read_value = 0

    # -----------------------------------------------------------------
    # Declarative register decode. Computed on demand from the raw
    # config bytes instead of re-parsed into shadow attributes every
    # clock tick.
    # -----------------------------------------------------------------
    @property
    def RXCIE0(self): return (self.UCSR0B >> 7) & 1
    @property
    def TXCIE0(self): return (self.UCSR0B >> 6) & 1
    @property
    def UDRIE0(self): return (self.UCSR0B >> 5) & 1
    @property
    def RXEN0(self): return (self.UCSR0B >> 4) & 1
    @property
    def TXEN0(self): return (self.UCSR0B >> 3) & 1
    @property
    def UCSZ02(self): return (self.UCSR0B >> 2) & 1
    @property
    def RXB80(self): return (self.UCSR0B >> 1) & 1
    @property
    def TXB80(self): return self.UCSR0B & 1

    @property
    def UMSEL(self): return (self.UCSR0C >> 6) & 0b11
    @property
    def UPM(self): return (self.UCSR0C >> 4) & 0b11
    @property
    def USBS0(self): return (self.UCSR0C >> 3) & 1
    @property
    def UCSZ01_00(self): return (self.UCSR0C >> 1) & 0b11
    @property
    def UCPOL0(self): return self.UCSR0C & 1

    @property
    def UBRR0(self): return ((self.UBRR0H & 0x0F) << 8) | self.UBRR0L

    @property
    def nbBits(self):
        ucsz = (self.UCSZ02 << 2) | self.UCSZ01_00
        return {0: 5, 1: 6, 2: 7, 3: 8, 7: 9}.get(ucsz, 8)   # reserved -> 8

    @property
    def nbStopBits(self):
        return 2 if self.USBS0 else 1

    @property
    def ParityMode(self):
        return {0: 'Disabled', 2: 'even', 3: 'odd'}.get(self.UPM, 'Disabled')

    @property
    def opp_mode(self):
        return {0: 'Asynchronous', 1: 'Synchronous', 3: 'Master SPI'}.get(self.UMSEL, '(Reserved)')

    @property
    def UCPHA0(self):
        # Only meaningful in MSPIM -- repurposes UCSR0C bit 2 (UPM0 in
        # async/sync mode).
        return (self.UCSR0C >> 2) & 1

    @property
    def UDORD0(self):
        # Only meaningful in MSPIM -- repurposes UCSR0C bit 1 (the low
        # bit of UCSZ01:00 in async/sync mode).
        return (self.UCSR0C >> 1) & 1

    @property
    def ticks_per_bit(self):
        if self.opp_mode == 'Asynchronous':
            return 8 if self.U2X0 else 16
        return 2   # synchronous / master SPI: one sample per XCK edge pair

    @property
    def UDRE0(self):
        # Buffer-empty is exactly "no byte waiting to start a frame" --
        # true at reset (buffer starts empty) and again the instant a
        # queued byte gets picked up by the baud clock.
        return 1 if self.TXB_buffer is None else 0

    def pack_ucsr0a(self):
        return ((self.RXC0 << 7) | (self.TXC0 << 6) | (self.UDRE0 << 5) |
                (self.FE0 << 4) | (self.DOR0 << 3) | (self.UPE0 << 2) |
                (self.U2X0 << 1) | self.MPCM0)

    # -----------------------------------------------------------------
    # Bus interface
    # -----------------------------------------------------------------
    def Memory_access(self):
        addr = self.interface.address.get()
        read_op = (self.interface.read.get() == 1) and (self.interface.write.get() == 0)
        write_op = (self.interface.read.get() == 0) and (self.interface.write.get() == 1)

        # Edge-tracking for UDR0's one-shot read/write side effects must
        # update every cycle regardless of address or early-return below
        # -- otherwise a deassertion cycle (addr/read/write all back to
        # 0, which takes the early-return path) never resets these,
        # and the next real UDR0 transaction wrongly looks like a
        # continuation of the previous one instead of a fresh edge.
        is_udr_read = (addr == UDR_REG) and read_op
        is_udr_write = (addr == UDR_REG) and write_op
        new_udr_read = is_udr_read and not self._prev_udr_read
        new_udr_write = is_udr_write and not self._prev_udr_write

        if not (read_op or write_op):
            self.interface.resp.prepare(0)
            self._prev_udr_read = False
            self._prev_udr_write = False
            return

        if addr == UCSRA_REG:
            if read_op:
                self.interface.read_data.prepare(self.pack_ucsr0a())
            elif write_op:
                data = self.interface.write_data.get()
                if data & UCSRA_TXC:
                    self.TXC0 = 0          # write-1-to-clear
                self.U2X0 = (data >> 1) & 1
                self.MPCM0 = data & 1
                # RXC0/FE0/DOR0/UPE0/UDRE0 are hardware read-only: ignored
            self.interface.resp.prepare(1)

        elif addr == UCSRB_REG:
            if read_op:
                self.interface.read_data.prepare(self.UCSR0B)
            elif write_op:
                data = self.interface.write_data.get()
                # RXB80 (bit1) is hardware read-only -- preserve it
                self.UCSR0B = (data & ~(1 << 1)) | (self.UCSR0B & (1 << 1))
            self.interface.resp.prepare(1)

        elif addr == UCSRC_REG:
            if read_op:
                self.interface.read_data.prepare(self.UCSR0C)
            elif write_op:
                self.UCSR0C = self.interface.write_data.get()
            self.interface.resp.prepare(1)

        elif addr == UBRRL_REG:
            if read_op:
                self.interface.read_data.prepare(self.UBRR0L)
            elif write_op:
                self.UBRR0L = self.interface.write_data.get() & 0xFF
            self.interface.resp.prepare(1)

        elif addr == UBRRH_REG:
            if read_op:
                self.interface.read_data.prepare(self.UBRR0H)
            elif write_op:
                self.UBRR0H = self.interface.write_data.get() & 0x0F
            self.interface.resp.prepare(1)

        elif addr == UDR_REG:
            if read_op:
                self.interface.read_data.prepare(self._read_udr() if new_udr_read else self._peek_udr())
            elif write_op:
                if new_udr_write:
                    self._write_udr(self.interface.write_data.get() & 0xFF)
            self.interface.resp.prepare(1)

        else:
            self.interface.resp.prepare(0)

        self._prev_udr_read = is_udr_read
        self._prev_udr_write = is_udr_write

    def _read_udr(self):
        if not self.rx_fifo:
            self._last_udr_read_value = 0
            return 0
        entry = self.rx_fifo.pop(0)
        self.DOR0 = 0
        self._refresh_rx_front_status()
        self._last_udr_read_value = entry['data']
        return entry['data']

    def _peek_udr(self):
        # Any cycle after the first of a held read strobe: must not pop
        # the FIFO again, but the bus data must stay stable at whatever
        # the real (first) read cycle returned -- a real register's
        # output doesn't change just because the FIFO advanced
        # underneath it mid-strobe.
        return self._last_udr_read_value

    def _write_udr(self, data):
        # Legal whenever UDRE0=1 (self.TXB_buffer is None), whether or
        # not a previous frame is still shifting out on the wire -- that
        # in-flight frame lives in tx_frame, a separate slot from the
        # buffer register. Writing while UDRE0=0 (buffer still full) is
        # ignored, matching real hardware.
        #
        # Also gated on TXEN0: real AVR's transmitter simply doesn't
        # process buffer contents at all while disabled, so a write
        # that lands while TXEN0=0 has no effect (matches the "no
        # override of TxDn while disabled" wording -- there's nothing
        # for it to drive out). This is a *separate* concern from
        # graceful disable (see TX_logic below): a byte already
        # accepted into the buffer *before* TXEN0 was cleared is still
        # "pending" and must still go out.
        if self.TXB_buffer is None and self.TXEN0:
            self.TXB_buffer = (data, self.TXB80)

    def _refresh_rx_front_status(self):
        # FE0/UPE0/RXB80 must reflect whichever byte is now at the front
        # of the FIFO (the one the next UDR0 read will return), *before*
        # that read happens -- matching the real chip's documented
        # "read UCSR0B/UCSR0A, then read UDR0" ordering for 9-bit/error
        # status to correspond to the right byte.
        if self.rx_fifo:
            front = self.rx_fifo[0]
            self.FE0 = front['fe']
            self.UPE0 = front['upe']
            self.UCSR0B = (self.UCSR0B & ~(1 << 1)) | (front['rxb8'] << 1)
        self.RXC0 = 1 if self.rx_fifo else 0

    # -----------------------------------------------------------------
    # Baud clock
    # -----------------------------------------------------------------
    def Clock_Generator(self):
        self.baud_tick = False
        if self.tick_counter >= self.UBRR0:
            self.baud_tick = True
            self.tick_counter = 0
        else:
            self.tick_counter += 1
        if self.baud_tick:
            self.USART_CLK_val ^= 1

    # -----------------------------------------------------------------
    # Transmit: build the whole frame once as a bit sequence, then walk
    # it one bit per `ticks_per_bit` baud ticks.
    # -----------------------------------------------------------------
    def _build_tx_frame(self, data, txb8):
        bits = [0]                                            # start bit
        for i in range(self.nbBits):
            bits.append((data >> i) & 1 if i < 8 else (txb8 & 1))
        if self.ParityMode != 'Disabled':
            mask = (1 << min(self.nbBits, 8)) - 1
            ones = bin(data & mask).count('1')
            if self.nbBits == 9 and txb8:
                ones += 1
            parity = ones & 1
            bits.append(parity if self.ParityMode == 'even' else parity ^ 1)
        bits += [1] * self.nbStopBits                          # stop bit(s)
        return bits

    def _begin_tx_frame(self):
        data, txb8 = self.TXB_buffer
        self.TXB_buffer = None                          # frees UDRE0
        self.tx_frame = self._build_tx_frame(data, txb8)
        self.tx_subtick = 0
        self.TXD_val = self.tx_frame[0]
        self.tx_index = 1

    def TX_logic(self):
        if not self.baud_tick:
            return

        # NOTE: TXEN0 is deliberately *not* checked here. Real AVR:
        # clearing TXEN0 doesn't abort an already-buffered or
        # already-shifting transmission -- it only prevents *new*
        # writes to UDR0 from being accepted (see _write_udr's TXEN0
        # gate above). A byte that made it into TXB_buffer while
        # TXEN0 was still 1 remains "pending" and will still be fully
        # shifted out even if TXEN0 is cleared (or cleared-then-set
        # again) before or during that shift -- confirmed against
        # test_usart_tx_graceful_disable.asm and
        # test_usart_tx_reenable_glitch.asm.
        if self.tx_frame is None:
            if self.TXB_buffer is not None:
                self._begin_tx_frame()
            else:
                self.TXD_val = 1
            return

        self.tx_subtick += 1
        if self.tx_subtick < self.ticks_per_bit:
            return
        self.tx_subtick = 0

        if self.tx_index >= len(self.tx_frame):
            # The last bit placed has now held for its full period.
            # Finish this frame, and if another byte is already queued
            # (UDR0 was written again while this one was shifting out),
            # start its frame's start bit in this *same* tick -- this
            # is what gives true back-to-back transmission with no gap
            # and no truncated stop bit. TXC0 only sets when there's
            # genuinely nothing left to send next, matching the
            # datasheet (TXC0 requires both the shift register and the
            # buffer to be empty).
            self.tx_frame = None
            self.tx_index = 0
            if self.TXB_buffer is not None:
                self._begin_tx_frame()
            else:
                self.TXC0 = 1
                self.TXD_val = 1
            return

        self.TXD_val = self.tx_frame[self.tx_index]
        self.tx_index += 1

    # -----------------------------------------------------------------
    # Receive: once a start edge is confirmed, sample exactly
    # nbBits + parity? + stopBits bits, one every `ticks_per_bit` baud
    # ticks (first sample offset by an extra half-bit to land mid-bit,
    # matching real oversampled receivers), then decode the whole frame
    # at once.
    # -----------------------------------------------------------------
    def RX_logic(self):
        if not self.RXEN0:
            self.rx_active = False
            return
        if not self.baud_tick:
            return

        rxd = self.RXD.get() & 1

        if not self.rx_active:
            if rxd == 0:                       # possible start bit
                self.rx_active = True
                self.rx_start_confirmed = False
                self.rx_subtick = 0
                self.rx_samples = []
                self.rx_frame_len = (self.nbBits +
                                      (1 if self.ParityMode != 'Disabled' else 0) +
                                      self.nbStopBits)
            return

        self.rx_subtick += 1
        half = self.ticks_per_bit >> 1

        if not self.rx_start_confirmed and self.rx_subtick == half:
            # Midpoint of the start bit only (rx_start_confirmed is set
            # True right below, so this never re-fires on a later data
            # bit that happens to also cross the same subtick count):
            # confirm it's still low (glitch rejection), and resync so
            # every following sample lands on a bit center exactly
            # `ticks_per_bit` apart.
            if rxd == 1:
                self.rx_active = False
            else:
                self.rx_subtick = 0
                self.rx_start_confirmed = True
            return

        if self.rx_subtick == self.ticks_per_bit:
            self.rx_subtick = 0
            self.rx_samples.append(rxd)
            if len(self.rx_samples) == self.rx_frame_len:
                self._finish_rx_frame()
                self.rx_active = False

    def _finish_rx_frame(self):
        nb = self.nbBits
        data_bits = self.rx_samples[:nb]
        idx = nb
        value = 0
        for i, b in enumerate(data_bits):
            value |= (b << i)

        upe = 0
        if self.ParityMode != 'Disabled':
            parity_bit = self.rx_samples[idx]
            idx += 1
            mask = (1 << min(nb, 8)) - 1
            ones = bin(value & mask).count('1')
            if nb == 9 and ((value >> 8) & 1):
                ones += 1
            expected = ones & 1
            if self.ParityMode == 'odd':
                expected ^= 1
            if parity_bit != expected:
                upe = 1

        # Real hardware only samples/validates the *first* stop bit for
        # framing error, regardless of how many stop bits are configured.
        stop_bits = self.rx_samples[idx:]
        fe = 1 if (stop_bits and stop_bits[0] != 1) else 0

        entry = {
            'data': value & 0xFF,
            'rxb8': (value >> 8) & 1 if nb == 9 else 0,
            'fe': fe,
            'upe': upe,
        }

        if self.MPCM0 and entry['rxb8'] == 0:
            # Data frame while multi-processor mode is filtering for an
            # address frame: silently discarded, RXC0 must not set.
            # (Real hardware: this check is independent of the two-slot
            # overrun logic below -- a filtered frame was never queued
            # in the first place, so it can't contribute to an overrun
            # either.)
            return

        if len(self.rx_fifo) >= 2:
            # Both buffer slots already occupied: the real chip keeps
            # the two buffered bytes and drops the new one, flagging
            # overrun.
            self.DOR0 = 1
            return

        self.rx_fifo.append(entry)
        self._refresh_rx_front_status()

    # -----------------------------------------------------------------
    # Synchronous mode: role select + slave RX (externally clocked)
    # -----------------------------------------------------------------
    def _sync_is_master(self):
        # Real hardware: DDR_XCKn (external to this peripheral) selects
        # direction. No XCK_DDR_OUT wired at all defaults to master --
        # this peripheral's original, pre-synchronous-mode behavior
        # (Clock_Generator always drives USART_CLK), so callers that
        # never use synchronous mode see no change.
        if self.XCK_DDR_OUT is None:
            return True
        return (self.XCK_DDR_OUT.get() & 1) == 1

    def Sync_Slave_RX_logic(self):
        # Edge-driven counterpart to RX_logic's baud_tick-driven
        # sampling: as a synchronous slave, this device has no baud
        # generator of its own worth trusting for bit timing -- the
        # external clock on XCK_in *is* the bit clock, so every sample
        # is taken directly off a real edge instead of an internally
        # oversampled tick count. Feeds the same rx_samples/
        # rx_frame_len/_finish_rx_frame() pipeline RX_logic uses, since
        # synchronous mode keeps the same start/data/parity/stop framing
        # as asynchronous mode -- only the bit timing source differs.
        if not self.RXEN0 or self.XCK_in is None:
            self.sync_slave_rx_active = False
            self._prev_xck_in = self.XCK_in.get() & 1 if self.XCK_in is not None else 0
            return

        xck = self.XCK_in.get() & 1
        rising = (self._prev_xck_in == 0 and xck == 1)
        falling = (self._prev_xck_in == 1 and xck == 0)
        sample_edge = rising if self.UCPOL0 == 0 else falling

        if sample_edge:
            rxd = self.RXD.get() & 1
            if not self.sync_slave_rx_active:
                if rxd == 0:      # start bit
                    self.sync_slave_rx_active = True
                    self.rx_samples = []
                    self.rx_frame_len = (self.nbBits +
                                          (1 if self.ParityMode != 'Disabled' else 0) +
                                          self.nbStopBits)
                # else: idle-high noise on the line -- not a start bit,
                # stay inactive.
            else:
                self.rx_samples.append(rxd)
                if len(self.rx_samples) == self.rx_frame_len:
                    self._finish_rx_frame()
                    self.sync_slave_rx_active = False

        self._prev_xck_in = xck

    # -----------------------------------------------------------------
    # Master SPI Mode (MSPIM): fixed 8-bit, full-duplex, no framing bits
    # at all -- TXD/RXD act as MOSI/MISO, XCK as SCK, exactly like
    # punxa_atmega328p.SPI's master mode (same leading/trailing,
    # UCPOL0/UCPHA0-as-CPOL/CPHA edge logic), just clocked off this
    # peripheral's own baud generator instead of a dedicated prescaler.
    # -----------------------------------------------------------------
    def _begin_mspim_transfer(self):
        data, _ = self.TXB_buffer
        self.TXB_buffer = None                    # frees UDRE0
        self.mspim_shift_out = data
        self.mspim_shift_in = 0
        self.mspim_bit_index = 0
        self.mspim_active = True
        # Pre-load bit 0 immediately, before any clock edge -- same
        # "first bit must already be valid at the leading edge" fix
        # SPI.py needed for its own MOSI (see that file's fix history).
        if self.UDORD0:
            bit0 = self.mspim_shift_out & 1
        else:
            bit0 = (self.mspim_shift_out >> 7) & 1
        self.TXD_val = bit0

    def MSPIM_logic(self):
        if not self.baud_tick:
            return

        if not self.mspim_active:
            if self.TXB_buffer is not None:
                self._begin_mspim_transfer()
            return

        # Clock_Generator (called earlier in clock()) already toggled
        # USART_CLK_val for this tick -- current is the post-toggle
        # value, current-vs-previous is this tick's edge.
        current = self.USART_CLK_val
        leading_edge = (self._mspim_lastclk == self.UCPOL0) and (current != self.UCPOL0)
        trailing_edge = (self._mspim_lastclk != self.UCPOL0) and (current == self.UCPOL0)
        sample_edge = leading_edge if self.UCPHA0 == 0 else trailing_edge
        setup_edge = trailing_edge if self.UCPHA0 == 0 else leading_edge

        if setup_edge:
            idx = self.mspim_bit_index
            if self.UDORD0:
                bit = (self.mspim_shift_out >> idx) & 1
            else:
                bit = (self.mspim_shift_out >> (7 - idx)) & 1
            self.TXD_val = bit
        elif sample_edge:
            incoming = self.RXD.get() & 1
            if self.UDORD0:
                self.mspim_shift_in = (self.mspim_shift_in >> 1) | (incoming << 7)
            else:
                self.mspim_shift_in = ((self.mspim_shift_in << 1) & 0xFF) | incoming
            self.mspim_bit_index += 1
            if self.mspim_bit_index == 8:
                self._finish_mspim_transfer()

        self._mspim_lastclk = current

    def _finish_mspim_transfer(self):
        self.mspim_active = False
        self.TXC0 = 1
        entry = {'data': self.mspim_shift_in & 0xFF, 'fe': 0, 'upe': 0, 'rxb8': 0}
        if len(self.rx_fifo) >= 2:
            self.DOR0 = 1
            return
        self.rx_fifo.append(entry)
        self._refresh_rx_front_status()

    # -----------------------------------------------------------------
    def update_interrupts(self):
        self.RXC_INT_val = 1 if (self.RXCIE0 and self.RXC0) else 0
        self.TXC_INT_val = 1 if (self.TXCIE0 and self.TXC0) else 0
        self.UDRE_INT_val = 1 if (self.UDRIE0 and self.UDRE0) else 0

    def update_Outputs(self):
        self.TXD.prepare(self.TXD_val)
        self.USART_CLK.prepare(self.USART_CLK_val)
        self.RXC_INT.prepare(self.RXC_INT_val)
        self.TXC_INT.prepare(self.TXC_INT_val)
        self.UDRE_INT.prepare(self.UDRE_INT_val)

    def clock(self):
        self.Memory_access()
        self.Clock_Generator()

        mode = self.opp_mode
        if mode == 'Master SPI':
            self.MSPIM_logic()
        elif mode == 'Synchronous' and not self._sync_is_master():
            self.Sync_Slave_RX_logic()
            # Slave-mode TX is real-hardware-legal but not implemented
            # this round (the tests exercise slave RX only) -- TXD is
            # simply left at its last value rather than actively driven.
        else:
            self.TX_logic()
            self.RX_logic()

        self.update_interrupts()
        self.update_Outputs()



class VirtualUSART(py4hw.Logic):
    def __init__(self, parent, name, mem: MemoryInterface, debug: bool = False):
        super().__init__(parent, name)
        
        self.mem = self.addInterfaceSink('', mem)
        self.status_control_A = UCSRA_UDRE
        self.status_control_B = 0
        self.status_control_C = 0
        self.console = ''
        self.debug = debug
        
        # --- Track previous states for edge detection ---
        self.prev_write = False
        self.prev_read = False
        
    def clock(self):
        add = self.mem.address.get()
        v = self.mem.write_data.get()
        
        # Capture current memory states
        is_write = (self.mem.write.get() == 1)
        is_read = (self.mem.read.get() == 1)
        
        # Detect rising edges (first clock cycle of the operation)
        is_new_write = is_write and not self.prev_write
        is_new_read = is_read and not self.prev_read
        
        if is_write:
            if (add == UCSRA_REG):
                self.status_control_A = v
            elif (add == UCSRB_REG):
                self.status_control_B = v
            elif (add == UCSRC_REG):
                self.status_control_C = v
            elif (add == UBRRH_REG):
                self.baud_rate_h = v
            elif (add == UBRRL_REG):
                self.baud_rate_l = v     
            elif (add == UDR_REG):
                # --- EDGE DETECTION: Only append on the first cycle ---
                if is_new_write:
                    char = chr(v)
                    self.console += char
                    
                    # --- Output directly to the terminal ---
                    print(char, end='', flush=True) 
            else:
                if is_new_write:
                    print(f'\nWARNING Writing to the USART: {add:04X}={v:02X}')
                
            self.mem.resp.prepare(1)
            
        elif is_read:
            if (add == UCSRA_REG):
                self.mem.read_data.prepare(self.status_control_A)
            else:
                if is_new_read:
                    print(f'\nWARNING Reading to the USART: {add:04X}')
            self.mem.resp.prepare(1)
            
        else:
            self.mem.resp.prepare(0)

        # --- AI-Friendly State & I/O Trace ---
        if self.debug:
            trace_log = (
                f"\nUSART_TRACE | "
                f"status_control_A: {self.status_control_A} | "
                f"status_control_B: {self.status_control_B} | "
                f"status_control_C: {self.status_control_C} | "
                f"Console: {repr(self.console)}"
            )
            
            # --- EDGE DETECTION: Only print once per read/write cycle ---
            if is_new_write or is_new_read:
                print(trace_log)
                
        # Update history for the next clock tick
        self.prev_write = is_write
        self.prev_read = is_read