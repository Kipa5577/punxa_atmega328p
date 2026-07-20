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
    gpio_p = punxa.MemoryInterface(hw, 'gpio', dw, 5)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)

    # USART0 <-> PeerUART wires
    rxd_wire = py4hw.Wire(hw, 'usart_rxd', 1); rxd_wire.put(1)
    txd_wire = py4hw.Wire(hw, 'usart_txd', 1); txd_wire.put(1)
    usart_clk_wire = py4hw.Wire(hw, 'usart_clk', 1); usart_clk_wire.put(0)
    usart_rxc_wire = py4hw.Wire(hw, 'usart_rxc_int', 1); usart_rxc_wire.put(0)
    usart_txc_wire = py4hw.Wire(hw, 'usart_txc_int', 1); usart_txc_wire.put(0)
    usart_udre_wire = py4hw.Wire(hw, 'usart_udre_int', 1); usart_udre_wire.put(0)

    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(reg_p, 0x0, 0x20),
                          (gpio_p, 0x20, 0x20),
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
    gpio = punxa.VirtualGPIO(hw, 'gpio', gpio_p)

    usart = punxa.USART0(hw, 'usart0', usart_p,
                          RXD=rxd_wire, TXD=txd_wire, USART_CLK=usart_clk_wire,
                          RXC_INT=usart_rxc_wire, TXC_INT=usart_txc_wire,
                          UDRE_INT=usart_udre_wire)

    pk = dict(ubrr=DEFAULT_UBRR0, nbBits=8, parity='Disabled', nbStopBits=1,
              ticks_per_bit=DEFAULT_TICKS_PER_BIT, echo=True, dut=usart)
    if peer_kwargs:
        pk.update(peer_kwargs)
    # peer.RXD_out drives the DUT's RXD pin; peer.TXD_in samples the
    # DUT's TXD pin -- i.e. crossed relative to the DUT's own naming,
    # exactly like connecting two real UARTs together.
    peer = PeerUART(hw, 'peer', RXD_out=rxd_wire, TXD_in=txd_wire, **pk)

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
