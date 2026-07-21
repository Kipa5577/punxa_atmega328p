# -*- coding: utf-8 -*-
"""
TimerCounter0 (Timer/Counter0, the ATmega328P's 8-bit timer) CPU-integration
test bench.

Separate from the ISA suite (tb_ISA_test_Multicycle_Rewrite.py / isa/test_*.asm)
and from tb_usart.py on purpose: this exercises one peripheral (Timer0)
through the real CPU, using the full behavioral model (TimerCounter0 in
Timers.py), not the simplified mock (SimpleTimer) the ISA suite wires up
for its own unrelated purposes.

Structurally this is the same pattern as tb_usart.py: same
MulticycleCpuWrapper/_find_child compatibility shim, same
runTest/computeAllTests/runAllTests/asciiProgressBar shape, same
"python -i tb_timers.py" interactive workflow -- with the peripheral and
its peer swapped out:

1. TimerCounter0 replaces SimpleTimer/VirtualUSART at the low I/O window,
   and its T0 (external clock input) / OC0A / OC0B (output compare) pins
   are wired to a PeerTimer (peer_timer.py) instead of dangling -- that
   peer plays two roles at once: it's the external clock source a CS=6/7
   program counts on, and it's a logic-analyzer-style pin monitor for
   OC0A/OC0B, the only way to confirm those actually toggled since this
   project's register model gives the CPU no way to read them back.

2. Unlike USART0 (which decodes addresses *relative* to wherever it's
   mapped on the bus), TimerCounter0's register-address constants
   (TCCR0A_addr_LS=0x44, TIFR0_addr_LS=0x35, TIMSK0_addr_LS=0x6E, ...)
   are baked in as *absolute* SRAM/I-O addresses. So timer_p is given a
   window starting at 0 spanning the whole low address space (0x00-0xFF)
   -- unlike a normal peripheral window, this is intentionally wide and
   overlaps reg_p/sp_p/int_unit_p's own (narrower) windows. That's safe
   because (a) TimerCounter0 only ever asserts resp=1 for its own six
   addresses and no-ops (resp=0) for everything else, and (b) timer_p is
   listed *first* in the MultiplexedBus slave list below, so reg_p/sp_p/
   int_unit_p -- listed after it -- always get the last (and therefore
   winning) word for the addresses they actually own. See Bus.py's
   propagate(): later slaves in the list overwrite master.resp/read_data
   for any address multiple slaves' windows cover.

Run interactively: `python3 -i tb_timers.py`, then e.g. `runAllTests()`.
"""
import os
import sys
import math
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.Memory import *
from punxa_atmega328p.Interrupt_Unit import *
from peer_timer import PeerTimer


# =============================================================================
# COMPATIBILITY WRAPPER (identical approach to tb_usart.py / tb_ISA_test_Multicycle_Rewrite.py)
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
# Default PeerTimer config every timer_tests/*.asm program can rely on
# without extra Python setup: a free-running external clock on T0 that
# toggles every 6 simulator cycles (peer_kwargs can override this, e.g.
# for a test that wants a specific pulse count via peer.pulse(n) instead).
DEFAULT_T0_PERIOD = 6


def prepareTest(file, preload=True, peer_kwargs=None):
    global hw, cpu, ins_mem, mem, timer0, peer

    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    words, symbols = assemble_program(program)

    hw = py4hw.HWSystem()

    dw = 8
    aw = 16

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)
    timer_p = punxa.MemoryInterface(hw, 'timer0', dw, 8)   # 0x00-0xFF, see module docstring
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)

    # TimerCounter0 <-> PeerTimer wires
    t0_wire = py4hw.Wire(hw, 'timer0_t0', 1); t0_wire.put(0)
    oc0a_wire = py4hw.Wire(hw, 'timer0_oc0a', 1); oc0a_wire.put(0)
    oc0b_wire = py4hw.Wire(hw, 'timer0_oc0b', 1); oc0b_wire.put(0)
    ocf0a_wire = py4hw.Wire(hw, 'timer0_ocf0a_int', 1); ocf0a_wire.put(0)
    ocf0b_wire = py4hw.Wire(hw, 'timer0_ocf0b_int', 1); ocf0b_wire.put(0)
    tov0_wire = py4hw.Wire(hw, 'timer0_tov0_int', 1); tov0_wire.put(0)

    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(timer_p, 0x0, 0x100),
                          (reg_p, 0x0, 0x20),
                          (sp_p, 0x5D, 0x02),
                          (int_unit_p, 0xFE, 0x2),
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
        # (0x20, 0x36) covers TIFR0 (0x35); (0x40, 0x6F) covers
        # TCCR0A/TCCR0B/TCNT0/OCR0A/OCR0B (0x44-0x48) and TIMSK0 (0x6E) --
        # without these, MemoryInterfaceHandler swallows STS/LDS/IN/OUT to
        # those addresses into its inert io_scratch fallback before the
        # bus/TimerCounter0 ever sees them (same caveat tb_usart.py's
        # docstring flags for the USART window).
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x38, 0x3F), (0x40, 0x6F), (0xFE, 0xFF)],
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

    timer0 = punxa.TimerCounter0(hw, 'timer0', timer_p,
                                  OC0B=oc0b_wire, OC0A=oc0a_wire, T0=t0_wire,
                                  OCF0B=ocf0b_wire, OCF0A=ocf0a_wire, TOV0=tov0_wire)

    pk = dict(t0_enabled=True, t0_period=DEFAULT_T0_PERIOD)
    if peer_kwargs:
        pk.update(peer_kwargs)
    # peer.T0_out drives the DUT's T0 pin; peer.OC0A_in/OC0B_in sample the
    # DUT's OC0A/OC0B pins -- i.e. crossed relative to the DUT's own
    # naming, exactly like connecting a real external clock source /
    # logic analyzer to those pins.
    peer = PeerTimer(hw, 'peer', T0_out=t0_wire, OC0A_in=oc0a_wire, OC0B_in=oc0b_wire, **pk)

    interrupt_module = SimpleInterruptUnit(
        hw, 'interrupt_module',
        memory=int_unit_p,
        Interrupt=interrupt_wire,
        Global_Interrupt_Enable=global_interrupt_enable_wire,
        TIMER0_COMPA=ocf0a_wire,
        TIMER0_COMPB=ocf0b_wire,
        TIMER0_OVF=tov0_wire,
    )

    if preload:
        for i, b in enumerate(words):
            ins_mem.writeWord(i, b)
    else:
        for i in range(1 << 14):
            ins_mem.writeWord(i, 0xFFFF)

    cpu.assembled_words = words
    return hw, cpu, ins_mem, mem, symbols


# =============================================================================
# Optional wire-level checks (see peer_timer.py's docstring): OC0A/OC0B
# toggling can't be confirmed from CPU-visible state, only from the pins.
# Keyed by test filename -> minimum edge counts expected on that pin by
# the time the test reaches 'end'. Absent entries mean "no pin check for
# this test", so ordinary register-only tests are unaffected.
# =============================================================================
PEER_PIN_CHECKS = {
    'test_timer_pwm_fast_toggle.asm': {'oc0a_min_edges': 3},
}


def runTest(file, peer_kwargs=None):
    hw, cpu, ins_mem, mem, symbols = prepareTest(file, peer_kwargs=peer_kwargs)

    # Timer tests busy-wait on TIFR0/TCNT0 polling loops, so there's no
    # fixed cycle budget per test the way a straight-line ISA test has --
    # generous headroom to absorb prescaler waits and multicycle
    # fetch/decode overhead per poll, same spirit as tb_usart.py's
    # step_limit.
    step_limit = 200000
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

    check = PEER_PIN_CHECKS.get(file)
    if check:
        if 'oc0a_min_edges' in check and peer.oc0a_edge_count < check['oc0a_min_edges']:
            raise Exception(f'OC0A pin never toggled as expected: saw {peer.oc0a_edge_count} '
                             f'edge(s), expected >= {check["oc0a_min_edges"]}')
        if 'oc0b_min_edges' in check and peer.oc0b_edge_count < check['oc0b_min_edges']:
            raise Exception(f'OC0B pin never toggled as expected: saw {peer.oc0b_edge_count} '
                             f'edge(s), expected >= {check["oc0b_min_edges"]}')


# =============================================================================
# TEST SUITE CONFIGURATION & RUNNERS (same shape as tb_usart.py)
# =============================================================================
ex_dir = 'timer_tests/'
selected_prefixes = ['test_timer']


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
        print('No timer_tests/test_timer_*.asm files found.')
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
