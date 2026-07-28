# -*- coding: utf-8 -*-
"""
USART0 CPU-integration test bench.

Separate from the ISA suite (tb_ISA_test_Multicycle_Rewrite.py /
isa/test_*.asm) on purpose: this exercises one peripheral (USART0)
through the real CPU, not general ISA correctness, and its test
programs live in usart_tests/ instead of isa/.

Structurally this is the same pattern as the ISA harness -- same
MulticycleCpuWrapper/_find_child compatibility shim, same
runTest/computeAllTests/runAllTests/asciiProgressBar shape, same
"python -i tb_usart.py" interactive workflow -- with two differences:

1. USART0 replaces VirtualUSART at the 0xC0 bus window, and its RXD/TXD
   pins are wired to a PeerUART (peer_uart.py) instead of dangling --
   that peer is the thing actually exercising USART0's wire-level
   protocol from outside, the same way a real external device would.
2. Bus_Passthrough_Ranges must include (0xC0, 0xC7) here. Without it,
   MemoryInterfaceHandler swallows STS/LDS/IN/OUT to that whole window
   into its inert io_scratch fallback before the bus/USART0 ever sees
   it -- worth flagging explicitly: this is true of the *existing* ISA
   harness's VirtualUSART wiring too (its Bus_Passthrough_Ranges never
   included 0xC0-0xC6 either), so as shipped, no assembled AVR program
   running through that harness could ever actually reach the USART
   peripheral via real STS/LDS instructions.

Run interactively: `python3 -i tb_usart.py`, then e.g. `runAllTests()`.
"""
import os
import sys
import math
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.Memory import *
from punxa_atmega328p.Interrupt_Unit import *
from peer_uart import PeerUART


# =============================================================================
# COMPATIBILITY WRAPPER (identical approach to tb_ISA_test_Multicycle_Rewrite.py)
# =============================================================================
def _find_child(root, name):
    if name in root.children:
        return root.children[name]
    for c in root.children.values():
        r = _find_child(c, name)
        if r is not None:
            return r
    return None


class MulticycleCpuWrapper:
    def __init__(self, cpu):
        self._cpu = cpu
        self._pc_reg = _find_child(cpu, 'PC')
        self._sreg_bits = {b: _find_child(cpu, f'SREG_{b}') for b in 'CZNVSHTI'}
        self._main_fsm = _find_child(cpu, 'MainFSM')

    @property
    def pc(self):
        return self._pc_reg.q.get()

    @property
    def sreg(self):
        order = ['C', 'Z', 'N', 'V', 'S', 'H', 'T', 'I']
        val = 0
        for i, b in enumerate(order):
            reg = self._sreg_bits[b]
            if reg is not None:
                val |= (reg.q.get() & 1) << i
        return val

    def __getattr__(self, name):
        return getattr(self._cpu, name)


def silence_debug(root, seen=None):
    if seen is None:
        seen = set()
    if id(root) in seen:
        return
    seen.add(id(root))
    if hasattr(root, 'debug'):
        root.debug = 0
    for c in root.children.values():
        silence_debug(c, seen)


# =============================================================================
# TEST PREPARATION
# =============================================================================
# Baud convention every usart_tests/*.asm program is expected to configure
# the DUT with, and that PeerUART below is pre-configured to match:
# UBRR0 = 10, 8N1, no parity (ticks_per_bit = 16, async normal speed).
# A test that needs different settings should reconfigure `peer` directly
# after prepareTest() returns it (see the docstring in usart_tests/ files).
DEFAULT_UBRR0 = 10
DEFAULT_TICKS_PER_BIT = 16

# Per-test PeerUART overrides, keyed by filename. Only needed for tests
# whose DUT-side config isn't the suite's 8N1/no-parity default -- most
# tests need nothing here. Consulted by both runTest() (when the caller
# didn't pass explicit peer_kwargs) and computeAllTests()/runAllTests(),
# so a test is fully self-configuring just by being listed once here;
# no per-test Python driver script needed for the ones that only need a
# different static PeerUART shape (nbBits/parity/nbStopBits/echo).
TEST_PEER_KWARGS = {
    # 9-bit character mode (UCSZ02+UCSZ01+UCSZ00=111): the peer must
    # frame/decode 9 data bits too, or its echo would silently truncate
    # the 9th bit (TXB80/RXB80) the test depends on.
    'test_usart_9bit_mode.asm': dict(nbBits=9),
    # Sweeps 5/6/7-bit character sizes in one run (UCSZ changes three
    # times). The peer's frame width must track the DUT's live UCSZ
    # config after each change, or its echo frame length falls out of
    # sync with what the DUT is actually shifting -- see PeerUART's
    # track_format docstring in peer_uart.py.
    'test_usart_char_size_mask.asm': dict(track_format=True),
    # Changes UBRR0 from 10 to 20 mid-run (only between frames, after
    # confirming TXC0). The peer must follow that change or its own
    # fixed-baud assumption desyncs from the DUT's new bit timing --
    # see PeerUART's track_baud docstring. Deliberately NOT applied to
    # test_usart_baud_sabotage.asm, which wants the opposite behavior.
    'test_usart_dynamic_baud.asm': dict(track_baud=True),
    # Sweeps UBRR0 across its full range (0, 10, 255, 4095) in one run.
    # Same track_baud need as dynamic_baud, above.
    'test_usart_baud_sweep.asm': dict(track_baud=True),
    # Even parity throughout (set once, never changed) -- the peer
    # must generate/check the same parity or its default-echo test
    # (test 1) would never come back clean.
    'test_usart_parity.asm': dict(parity='even'),
    # 9-bit frames needed to carry the MPCM address-mark bit.
    'test_usart_mpcm_filtering.asm': dict(nbBits=9),
}


# -----------------------------------------------------------------------
# Per-test custom peer drivers, keyed by filename. Each entry is a
# function(peer) that configures peer.on_frame_received (see
# PeerUART's docstring in peer_uart.py) to react to a specific
# trigger byte from the DUT instead of the default echo -- for tests
# whose whole point is to exercise something the DUT does in response
# to a deliberately malformed or otherwise-not-a-clean-echo frame.
# Called once, right after the peer is constructed in prepareTest().
# -----------------------------------------------------------------------
def _driver_break_condition(peer):
    def on_frame(peer, entry):
        if entry['data'] == 0xBB:
            # Trigger byte: instead of echoing it, hold RXD low long
            # enough to fill exactly one bad (break) frame -- see
            # PeerUART.send_break's docstring for why *exactly* one
            # frame's worth and not "a bit more for safety".
            peer.send_break()
            return True   # suppress the default echo for this frame
        return False       # let 0xCC (the recovery byte) echo normally
    peer.on_frame_received = on_frame


def _driver_mpcm_filtering(peer):
    # Unlike the other TEST_DRIVERS, the DUT here never transmits first
    # -- it's purely a receiver waiting on two frames the peer must send
    # unprompted, and neither can simply be queued at construction time:
    #
    # - Frame 1 (data, must be filtered) can't be sent at cycle 0: the
    #   CPU's own setup code (UBRR0/UCSR0C/UCSR0B writes, then the
    #   read-modify-write that sets MPCM0) doesn't actually enable MPCM0
    #   until ~cycle 357 (measured), but a 9-bit frame only takes ~176
    #   cycles to arrive -- sent immediately, frame 1 would complete
    #   *before* filtering is even turned on, and get received normally
    #   (incorrectly setting RXC0, but for an unrelated reason: not a
    #   real filtering failure, just a race against the DUT's own init).
    # - Frame 2 (address, must be accepted) can't be sent immediately
    #   after frame 1 either: this multicycle CPU takes ~11,000 cycles
    #   to work through its 255-iteration delay loop before TEST 1
    #   checks RXC0, far longer than either frame's transmission time,
    #   so an eagerly-queued frame 2 would already be sitting in the
    #   FIFO by the time TEST 1 checks that RXC0 is still clear.
    #
    # PeerUART has no built-in "send after N cycles" primitive, so both
    # sends are driven by a small per-cycle scheduler wrapping
    # peer.clock (measured cycle counts above have generous margin on
    # both sides).
    peer._mpcm_schedule = [(500, (0x11, 0)), (15000, (0x22, 1))]
    orig_clock = peer.clock

    def scheduled_clock():
        orig_clock()
        remaining = []
        for cycle, (data, ninth) in peer._mpcm_schedule:
            cycle -= 1
            if cycle <= 0:
                peer.send9(data, ninth)
            else:
                remaining.append((cycle, (data, ninth)))
        peer._mpcm_schedule = remaining

    peer.clock = scheduled_clock


def _driver_parity(peer):
    def on_frame(peer, entry):
        if entry['data'] == 0xFF:
            # Trigger byte: reply with a deliberately wrong-parity
            # frame instead of a clean echo, to exercise the DUT's
            # UPE0 detection. Payload value doesn't matter to the
            # test (it only reads UDR0 to drain the buffer after
            # checking UPE0), so any byte works.
            peer.send_bad_parity(0x5A)
            return True
        return False
    peer.on_frame_received = on_frame


TEST_DRIVERS = {
    'test_usart_break_condition.asm': _driver_break_condition,
    'test_usart_parity.asm': _driver_parity,
    'test_usart_mpcm_filtering.asm': _driver_mpcm_filtering,
}


# -----------------------------------------------------------------------
# Per-test post-run Python-side checks, keyed by filename. For tests
# that can't be fully self-checking through the CPU-visible
# test_case/final_result convention alone. Each entry is a
# function(peer, cpu, mem) called once after the main step loop
# finishes (and after confirming final_result != 255); raise an
# Exception to fail the test, same as final_result==255 does.
# -----------------------------------------------------------------------
def _check_baud_sabotage(peer, cpu, mem):
    # test_usart_baud_sabotage.asm deliberately rewrites UBRR0
    # mid-transmission. The DUT's own registers can't tell us whether
    # that actually corrupted anything -- it's the transmitter here,
    # not the receiver -- so the only place to observe the effect is
    # the peer's independent, fixed-baud (UBRR0=10 the whole time,
    # since this test is deliberately absent from TEST_PEER_KWARGS'
    # track_baud entries) decode of what actually appeared on the wire.
    #
    # A severe enough mismatch (here, UBRR0 10->200) can make the peer
    # decode the single, now-badly-stretched DUT transmission as
    # several spurious frames rather than one obviously-broken one, so
    # checking only the last entry isn't reliable -- instead, confirm
    # a *clean* 0x55 never shows up anywhere in what the peer decoded.
    if not peer.received:
        raise Exception('baud_sabotage: peer never decoded anything off TXD at all')
    if any(r['data'] == 0x55 and r['fe'] == 0 for r in peer.received):
        raise Exception(
            f"baud_sabotage: expected the mid-frame UBRR0 rewrite to corrupt "
            f"the transmission (framing error or wrong data byte) in every "
            f"frame the peer decoded, but a clean 0x55 with fe=0 showed up -- "
            f"either the sabotage had no effect (unexpected: real AVR's baud "
            f"generator has no double-buffering, so this should have desynced "
            f"the remaining bits) or it landed too early/late to matter. "
            f"Got: {peer.received}"
        )


TEST_POST_CHECKS = {
    'test_usart_baud_sabotage.asm': _check_baud_sabotage,
}

# Per-test step_limit overrides, keyed by filename. Only needed for
# tests whose own timing genuinely exceeds the suite's normal headroom
# -- most tests don't need an entry here. test_usart_baud_sweep.asm's
# slowest sub-test (UBRR0=4095, the 12-bit maximum) needs roughly
# (4095+1) ticks/bit-count * 16 ticks/bit * 10 bits ~= 655,360 cycles
# for *one* byte's round trip alone (transmit + echo), on top of the
# other three sub-tests and normal CPU polling overhead -- three orders
# of magnitude past the default 200,000-cycle budget, so it gets its
# own much larger limit rather than inflating the default for every
# other test.
TEST_STEP_LIMITS = {
    'test_usart_baud_sweep.asm': 3_000_000,
}


class GpioDdrBitProbe(py4hw.Logic):
    """Bridges a single GPIO DDRx bit into a wire USART0's XCK_DDR_OUT
    input can read -- GPIO doesn't expose DDRD as a py4hw port (it's a
    plain Python attribute, like every register in this project's
    peripherals), so this reaches into the already-constructed `gpio`
    object directly each cycle, the same "peek at another component's
    real Python state" pattern peer_uart.py's `dut`/`track_format` and
    peer_spi.py's `dut` already use, just from a tiny dedicated
    component instead of a peer. Real top-level chip integration would
    wire this from GPIO's real register bit the same way once GPIO
    exposes it as a proper output port; this is the test-harness-side
    equivalent in the meantime."""
    def __init__(self, parent, name, gpio, bit, out_wire):
        super().__init__(parent, name)
        self.gpio = gpio
        self.bit = bit
        self.out = self.addOut('out', out_wire)

    def propagate(self):
        self.out.put((self.gpio.DDRD >> self.bit) & 1)


class SyncSlaveDriver(py4hw.Logic):
    """Test-specific driver for test_usart_sync_mode.asm's TEST 2:
    drives XCK_in + RXD to clock a fixed byte into USART0 while it's
    configured as a synchronous slave receiver (UMSEL=Synchronous,
    XCK_DDR_OUT=0). Waits for the DUT to actually reach that state
    before bit-banging, since the .asm only gets there after TEST 1
    (master TX) finishes -- polls `usart.RXEN0`/`.opp_mode`/
    `._sync_is_master()` directly (same "reach into the DUT" pattern as
    GpioDdrBitProbe above)."""
    def __init__(self, parent, name, usart, xck_out, rxd_out, byte, period=4):
        super().__init__(parent, name)
        self.usart = usart
        self.xck_out = self.addOut('xck_out', xck_out)
        self.rxd_out = self.addOut('rxd_out', rxd_out)
        self.period = period
        self.byte = byte & 0xFF
        self.state = 'WAIT'
        self.phase = 0
        self.bit_index = 0
        self.frame = None
        self.xck_val = 0
        self.rxd_val = 1

    def clock(self):
        if self.state == 'WAIT':
            if (self.usart.RXEN0 and self.usart.opp_mode == 'Synchronous'
                    and not self.usart._sync_is_master()):
                self.frame = [0] + [(self.byte >> i) & 1 for i in range(8)] + [1]
                self.bit_index = 0
                self.phase = 0
                self.state = 'PRESENT'
        elif self.state == 'PRESENT':
            self.rxd_val = self.frame[self.bit_index]
            self.xck_val = 0
            self.phase += 1
            if self.phase >= self.period:
                self.phase = 0
                self.state = 'PULSE_HIGH'
        elif self.state == 'PULSE_HIGH':
            self.xck_val = 1
            self.phase += 1
            if self.phase >= self.period:
                self.phase = 0
                self.bit_index += 1
                if self.bit_index >= len(self.frame):
                    self.state = 'DONE'
                else:
                    self.state = 'PRESENT'
        elif self.state == 'DONE':
            self.xck_val = 0

        self.xck_out.prepare(self.xck_val)
        self.rxd_out.prepare(self.rxd_val)


class MspimSlaveDriver(py4hw.Logic):
    """Test-specific driver for test_usart_mspim.asm: plays the SPI
    'slave' side of Master SPI Mode -- USART0 always drives XCK in
    MSPIM (no MSPIM slave mode exists on real hardware), so this only
    ever senses XCK/TXD(MOSI) and drives RXD(MISO). SPI Mode 0
    (UCPOL0=0, UCPHA0=0, matching what the .asm configures): both sides
    present their next bit on the trailing (falling) edge and sample on
    the leading (rising) edge.

    Presents a pre-configured reply byte rather than a true same-
    transfer echo -- full-duplex means the master's byte isn't fully
    known until the same instant this peer would need to finish
    replying with it, so an actual echo needs a second transfer (the
    same one-transfer-latency constraint peer_spi.py's PeerSPI already
    documents for regular SPI). Known here in advance since the test
    harness controls both sides, the same way TWI's PeerI2CSlave is
    pre-loaded with `read_bytes` for a master-read test.
    """
    def __init__(self, parent, name, xck_in, mosi_in, miso_out, reply_byte):
        super().__init__(parent, name)
        self.xck_in = self.addIn('xck_in', xck_in)
        self.mosi_in = self.addIn('mosi_in', mosi_in)
        self.miso_out = self.addOut('miso_out', miso_out)
        self.reply = reply_byte & 0xFF
        self.bit_index = 0
        self.prev_xck = 0
        self.received = 0
        self.miso_val = (self.reply >> 7) & 1   # bit 0 pre-loaded, MSB first (UDORD0=0)

    def clock(self):
        xck = self.xck_in.get() & 1
        leading = (self.prev_xck == 0 and xck == 1)
        trailing = (self.prev_xck == 1 and xck == 0)

        if leading and self.bit_index < 8:
            bit = self.mosi_in.get() & 1
            self.received = ((self.received << 1) & 0xFF) | bit
            self.bit_index += 1
        if trailing and self.bit_index < 8:
            self.miso_val = (self.reply >> (7 - self.bit_index)) & 1

        self.prev_xck = xck
        self.miso_out.prepare(self.miso_val)


def prepareTest(file, preload=True, peer_kwargs=None):
    global hw, cpu, ins_mem, mem, usart, peer

    if peer_kwargs is None:
        peer_kwargs = TEST_PEER_KWARGS.get(file)

    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    words, symbols = assemble_program(program)

    hw = py4hw.HWSystem()

    dw = 8
    aw = 16

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)
    usart_p = punxa.MemoryInterface(hw, 'usart', dw, 3)
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)
    gpio_p = punxa.MemoryInterface(hw, 'gpio', dw, 8)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)

    # USART0 <-> PeerUART wires
    rxd_wire = py4hw.Wire(hw, 'usart_rxd', 1); rxd_wire.put(1)
    txd_wire = py4hw.Wire(hw, 'usart_txd', 1); txd_wire.put(1)
    usart_clk_wire = py4hw.Wire(hw, 'usart_clk', 1); usart_clk_wire.put(0)
    xck_in_wire = py4hw.Wire(hw, 'usart_xck_in', 1); xck_in_wire.put(0)
    xck_ddr_wire = py4hw.Wire(hw, 'usart_xck_ddr', 1); xck_ddr_wire.put(1)
    usart_rxc_wire = py4hw.Wire(hw, 'usart_rxc_int', 1); usart_rxc_wire.put(0)
    usart_txc_wire = py4hw.Wire(hw, 'usart_txc_int', 1); usart_txc_wire.put(0)
    usart_udre_wire = py4hw.Wire(hw, 'usart_udre_int', 1); usart_udre_wire.put(0)

    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(gpio_p, 0x0, 0x100),
                          (reg_p, 0x0, 0x20),
                          (sp_p, 0x5D, 0x02),
                          (int_unit_p, 0xFE, 0x2),
                          (usart_p, 0xC0, 0x8),
                          (mem_p, 0x100)])

    reset_wire = py4hw.Wire(hw, 'Reset_Line', 1)
    reset_wire.put(0)
    prog_mosi_wire = py4hw.Wire(hw, 'PROG_MOSI', 1)
    prog_mosi_wire.put(0)
    prog_sck_wire = py4hw.Wire(hw, 'PROG_SCK', 1)
    prog_sck_wire.put(0)
    prog_miso_wire = py4hw.Wire(hw, 'PROG_MISO', 1)

    actual_cpu = punxa.multicycleProcessor(
        parent=hw,
        name='cpu',
        Interrupt=interrupt_wire,
        Interrupt_Enable=global_interrupt_enable_wire,
        ins_mem=ins_p,
        memory=data_p,
        reset=reset_wire,
        PROG_MOSI=prog_mosi_wire,
        PROG_SCK=prog_sck_wire,
        PROG_MISO=prog_miso_wire,
        reset_address=0,
        # (0xC0, 0xC7) is the one that matters for this harness -- see
        # the module docstring above for why it must be listed here
        # explicitly or USART0 is unreachable from real STS/LDS/IN/OUT.
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x38, 0x3F), (0xC0, 0xC7), (0xFE, 0xFF)],
    )

    cpu = MulticycleCpuWrapper(actual_cpu)
    cpu.prog_mosi = prog_mosi_wire
    cpu.prog_sck = prog_sck_wire
    cpu.prog_miso = prog_miso_wire
    cpu.reset_wire = reset_wire

    reg = punxa.Ram_Memory(hw, 'reg', dw, 7, reg_p)
    mem = punxa.Ram_Memory(hw, 'men', dw, 11, mem_p)
    ins_mem = punxa.Ram_Memory(hw, 'ins_men', 16, 14, ins_p)
    sp_component = StackPointer(hw, 'stack_pointer', sp_p)
    gpio = punxa.GPIO(hw, 'gpio', gpio_p)

    usart = punxa.USART0(hw, 'usart0', usart_p,
                          RXD=rxd_wire, TXD=txd_wire, USART_CLK=usart_clk_wire,
                          RXC_INT=usart_rxc_wire, TXC_INT=usart_txc_wire,
                          UDRE_INT=usart_udre_wire,
                          XCK_in=xck_in_wire, XCK_DDR_OUT=xck_ddr_wire)

    GpioDdrBitProbe(hw, 'xck_ddr_probe', gpio, 4, xck_ddr_wire)

    if file == 'test_usart_sync_mode.asm':
        SyncSlaveDriver(hw, 'sync_slave_driver', usart, xck_in_wire, rxd_wire, 0x5A)
    elif file == 'test_usart_mspim.asm':
        MspimSlaveDriver(hw, 'mspim_slave_driver', usart_clk_wire, txd_wire, rxd_wire, 0xC3)

    pk = dict(ubrr=DEFAULT_UBRR0, nbBits=8, parity='Disabled', nbStopBits=1,
              ticks_per_bit=DEFAULT_TICKS_PER_BIT, echo=True, dut=usart)
    if peer_kwargs:
        pk.update(peer_kwargs)
    # peer.RXD_out drives the DUT's RXD pin; peer.TXD_in samples the
    # DUT's TXD pin -- i.e. crossed relative to the DUT's own naming,
    # exactly like connecting two real UARTs together.
    # test_usart_sync_mode.asm / test_usart_mspim.asm need
    # SyncSlaveDriver/MspimSlaveDriver to be the *only* thing driving
    # rxd_wire (both peers writing the same wire every cycle would
    # silently race) -- PeerUART is still constructed (its TXD_in side
    # is harmless/unused by these tests), just pointed at a wire nothing
    # reads instead of the DUT's real RXD.
    peer_rxd_target = rxd_wire
    if file in ('test_usart_sync_mode.asm', 'test_usart_mspim.asm'):
        peer_rxd_target = py4hw.Wire(hw, 'unused_peer_rxd', 1)
    peer = PeerUART(hw, 'peer', RXD_out=peer_rxd_target, TXD_in=txd_wire, **pk)

    driver_setup = TEST_DRIVERS.get(file)
    if driver_setup is not None:
        driver_setup(peer)

    interrupt_module = SimpleInterruptUnit(
        hw, 'interrupt_module',
        memory=int_unit_p,
        Interrupt=interrupt_wire,
        Global_Interrupt_Enable=global_interrupt_enable_wire,
        USART_RX=usart_rxc_wire,
        USART_UDRE=usart_udre_wire,
        USART_TX=usart_txc_wire,
    )

    if preload:
        for i, b in enumerate(words):
            ins_mem.writeWord(i, b)
    else:
        for i in range(1 << 14):
            ins_mem.writeWord(i, 0xFFFF)

    cpu.assembled_words = words
    return hw, cpu, ins_mem, mem, symbols


def runTest(file, peer_kwargs=None, step_limit=None):
    hw, cpu, ins_mem, mem, symbols = prepareTest(file, peer_kwargs=peer_kwargs)

    # USART tests are byte-serial, not just instruction-serial: one byte
    # at the default UBRR0=10/8N1 takes 10 bits * 16 ticks/bit * 11
    # cycles/tick ~= 1760 cycles, before any CPU polling overhead on top
    # of that. Generous headroom for a handful of bytes per test.
    if step_limit is None:
        step_limit = TEST_STEP_LIMITS.get(file, 200000)
    step_count = 0

    sim = hw.getSimulator()

    while (cpu.pc != symbols['end']):
        py4hw.Wire.settleAll()
        sim.clk(1)
        step_count += 1

        if (step_count > step_limit):
            raise Exception(f'Stuck in infinite loop! PC: {cpu.pc:04X} (Expected end at: {symbols["end"]:04X})')

    test_case = mem.readWord(symbols['test_case'] - 0x100)
    final_result = mem.readWord(symbols['final_result'] - 0x100)

    print('FINAL RESULT:', final_result, '\tTest case:', test_case, '\tCycles:', step_count)

    if (final_result == 255):
        raise Exception(f'Failed in test case {test_case}')

    # Some tests can't fully self-check through the CPU-visible
    # test_case/final_result convention alone -- e.g. baud_sabotage
    # deliberately corrupts its own transmission and only the peer's
    # independent, fixed-baud decode of the wire (not the DUT's own
    # registers, since the DUT is the transmitter here) can tell
    # whether that corruption actually happened. TEST_POST_CHECKS
    # covers exactly that class of test; raises on failure just like
    # the final_result==255 case above.
    post_check = TEST_POST_CHECKS.get(file)
    if post_check is not None:
        post_check(peer, cpu, mem)


# =============================================================================
# TEST SUITE CONFIGURATION & RUNNERS (same shape as tb_ISA_test_Multicycle_Rewrite.py)
# =============================================================================
ex_dir = 'usart_tests/'
selected_prefixes = ['test_usart']


def computeAllTests():
    files = os.listdir(ex_dir)
    ret = {}

    files = [name for name in files if any(name.startswith(prefix) for prefix in selected_prefixes)]

    for f in files:
        if (f[-4:].lower() == '.asm'):
            print('Run test', f, end=' ')
            try:
                runTest(f)
                print('PASSED')
                ret[f] = ('OK')
            except Exception as e:
                print('FAILED')
                ret[f] = ('FAILED', e)
        else:
            pass

    return ret


def asciiProgressBar(n, t):
    p = n * 100 / t
    pl = 45
    pok = math.ceil(pl * n / t)
    pko = pl - pok
    sok = '█' * pok
    sko = '░' * pko
    sp = '{:.1f} %'.format(p)
    s = '{:8} |{}{}|'.format(sp, sok, sko)
    return s


def runAllTests():
    global selected_prefixes
    nOK = 0
    nTotal = 0
    ret = computeAllTests()

    groupResults = {}

    for prefix in selected_prefixes:
        nOKGroup = 0
        nTotalGroup = 0

        files = [name for name in ret.keys() if name.startswith(prefix)]
        for t in files:
            nTotal += 1
            nTotalGroup += 1
            if (ret[t] == 'OK'):
                print('Test {:30} = {}'.format(t, ret[t]))
                nOK += 1
                nOKGroup += 1
            else:
                print('Test {:30} = {} - {}'.format(t, ret[t][0], ret[t][1]))

        groupResults[prefix] = (nOKGroup, nTotalGroup)

    if nTotal == 0:
        print('No usart_tests/test_usart_*.asm files found.')
        return

    print('Total: {} Correct: {} ({:.1f} %)'.format(nTotal, nOK, nOK * 100 / nTotal))
    print(asciiProgressBar(nOK, nTotal))

    for prefix in selected_prefixes:
        nOKGroup = groupResults[prefix][0]
        nTotalGroup = groupResults[prefix][1]
        if (nTotalGroup == 0):
            nTotalGroup = 1
        print('Group: {} Total: {} Correct: {} ({:.1f} %)'.format(prefix, nTotalGroup, nOKGroup, nOKGroup * 100 / nTotalGroup))

    for prefix in selected_prefixes:
        nOKGroup = groupResults[prefix][0]
        nTotalGroup = groupResults[prefix][1]
        if (nTotalGroup == 0):
            nTotalGroup = 1
        print(f'{prefix:15}', asciiProgressBar(nOKGroup, nTotalGroup))


if __name__ == "__main__":
    print(sys.argv)

    if (len(sys.argv) > 1):
        if (sys.argv[1] == '-c'):
            eval(sys.argv[2])
            os._exit(0)
