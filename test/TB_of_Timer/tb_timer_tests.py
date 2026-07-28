# -*- coding: utf-8 -*-
"""
Timer0/1/2 CPU-integration test bench -- tb_timers.py rewritten to match
tb_ISA_tests_Multicycle_rewrite.py's shape (MulticycleCpuWrapper,
runTest/computeAllTests/runAllTests, `python3 -i tb_timer_tests.py`
interactive workflow, and process-pool parallel execution) instead of
the old single-timer, sequential-only version.

What changed from the old tb_timers.py:

1. **All three real timers, not just Timer0.** TimerCounter0,
   TimerCounter1 (16-bit), and TimerCounter2 (8-bit, async-capable) are
   all instantiated and driven through the real CPU in every test run,
   via TimerBusRouter (timer_bus_router.py) -- see that file's docstring
   for why a plain punxa.MultiplexedBus slave entry per timer doesn't
   work once there's more than one (their real register addresses are
   scattered across the same 0x00-0xFF span and don't survive
   MultiplexedBus's no-break, last-match-wins arbitration with three
   overlapping full-width windows).

2. **A peer per timer** (peer_timer.py's PeerTimer, reused three times --
   its T0_out/OC0A_in/OC0B_in port names are just labels, structurally
   identical for any of the three timers' clock-in/compare-out pin
   trio), so OC0A/OC0B/OC1A/OC1B/OC2A/OC2B toggling can be confirmed from
   outside, the same way PeerUART confirms USART0's TXD.

3. **Parallel execution.** computeAllTests(num_threads) /
   runAllTests(num_threads) match tb_ISA_test_Multicycle_Rewrite.py's
   ProcessPoolExecutor-based design exactly (see that file's docstring
   for why processes, not threads: py4hw.Wire's prepared/dirty state is
   class-level, shared and racy across threads in one process, but not
   across separate OS processes).

4. **Two real CPU-core bugs found and fixed while building this** (see
   HANDOFF.md's fix history and this file's own commit trail for the
   full detail): MemoryInterfaceHandler.py never drove the external
   `instype` signal (declared as an output, never `.prepare()`'d), and
   Bus.py's MultiplexedBus never forwarded `instype` to any slave at
   all. Together these meant the *real* GPIO/TimerCounter0/1/2/ADC
   classes -- as opposed to the mocks (VirtualGPIO/SimpleTimer/
   VirtualUSART) the ISA suite wires up, none of which check instype --
   could never respond through the real CPU; every transaction to them
   would hang forever waiting for a `resp` that would never come. Fixed
   in both files; re-verified the 111-test ISA suite is still 111/111
   after each fix (both changes are purely additive / only make
   previously-dead signals live).

Run interactively: `python3 -i tb_timer_tests.py`, then e.g.
`runAllTests(num_threads=8)`.
"""
import os
import sys
import io
import math
import contextlib
import time
import concurrent.futures
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.Memory import *
from punxa_atmega328p.Interrupt_Unit import *
from peer_timer import PeerTimer
from timer_bus_router import TimerBusRouter


# =============================================================================
# COMPATIBILITY WRAPPER (identical approach to tb_usart.py / the ISA harness)
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
# Default free-running external clock period (in simulator cycles) each
# timer_tests/*.asm program can rely on without extra Python setup, same
# spirit as the old single-timer harness's DEFAULT_T0_PERIOD.
DEFAULT_EXT_CLK_PERIOD = 6


def prepareTest(file, preload=True, peer_kwargs=None):
    """peer_kwargs: optional dict of {'timer0': {...}, 'timer1': {...},
    'timer2': {...}} to override that timer's PeerTimer construction
    (e.g. {'timer0': {'t0_enabled': False}} to leave Timer0's external
    clock idle for a test that only exercises Timer1)."""
    global hw, cpu, ins_mem, mem, timer0, timer1, timer2, peer0, peer1, peer2

    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    words, symbols = assemble_program(program)

    hw = py4hw.HWSystem()

    dw = 8
    aw = 16

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)
    # One wide window for the router (see timer_bus_router.py) instead of
    # one window per timer -- the router does the real per-register
    # dispatch internally.
    timer_master_p = punxa.MemoryInterface(hw, 'timer_master', dw, 8)
    timer0_p = punxa.MemoryInterface(hw, 'timer0_port', dw, 8)
    timer1_p = punxa.MemoryInterface(hw, 'timer1_port', dw, 8)
    timer2_p = punxa.MemoryInterface(hw, 'timer2_port', dw, 8)
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)

    # --- Timer0 <-> PeerTimer0 wires ---
    t0_wire = py4hw.Wire(hw, 't0_pin', 1); t0_wire.put(0)
    oc0a_wire = py4hw.Wire(hw, 'oc0a_pin', 1); oc0a_wire.put(0)
    oc0b_wire = py4hw.Wire(hw, 'oc0b_pin', 1); oc0b_wire.put(0)
    ocf0a_wire = py4hw.Wire(hw, 'ocf0a_int', 1); ocf0a_wire.put(0)
    ocf0b_wire = py4hw.Wire(hw, 'ocf0b_int', 1); ocf0b_wire.put(0)
    tov0_wire = py4hw.Wire(hw, 'tov0_int', 1); tov0_wire.put(0)

    # --- Timer1 <-> PeerTimer1 wires ---
    t1_wire = py4hw.Wire(hw, 't1_pin', 1); t1_wire.put(0)
    oc1a_wire = py4hw.Wire(hw, 'oc1a_pin', 1); oc1a_wire.put(0)
    oc1b_wire = py4hw.Wire(hw, 'oc1b_pin', 1); oc1b_wire.put(0)
    ocf1a_wire = py4hw.Wire(hw, 'ocf1a_int', 1); ocf1a_wire.put(0)
    ocf1b_wire = py4hw.Wire(hw, 'ocf1b_int', 1); ocf1b_wire.put(0)
    tov1_wire = py4hw.Wire(hw, 'tov1_int', 1); tov1_wire.put(0)
    icf1_wire = py4hw.Wire(hw, 'icf1_int', 1); icf1_wire.put(0)

    # --- Timer2 <-> PeerTimer2 wires ---
    t2_wire = py4hw.Wire(hw, 't2_pin', 1); t2_wire.put(0)
    oc2a_wire = py4hw.Wire(hw, 'oc2a_pin', 1); oc2a_wire.put(0)
    oc2b_wire = py4hw.Wire(hw, 'oc2b_pin', 1); oc2b_wire.put(0)
    ocf2a_wire = py4hw.Wire(hw, 'ocf2a_int', 1); ocf2a_wire.put(0)
    ocf2b_wire = py4hw.Wire(hw, 'ocf2b_int', 1); ocf2b_wire.put(0)
    tov2_wire = py4hw.Wire(hw, 'tov2_int', 1); tov2_wire.put(0)

    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(timer_master_p, 0x0, 0x100),
                          (reg_p, 0x0, 0x20),
                          (sp_p, 0x5D, 0x02),
                          (int_unit_p, 0xFE, 0x2),
                          (mem_p, 0x100)])

    TimerBusRouter(hw, 'timer_router', timer_master_p, timer0_p, timer1_p, timer2_p)

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
        # This constructor parameter is kept for interface-compatibility
        # with the ISA harness, but the *real* gating is now an inline
        # check in MemoryInterfaceHandler.clock() (extended to cover
        # 0x37/0x70/0x80-0x8B/0xB0-0xB4 for Timer1/Timer2 -- see that
        # file's comment at the is_passthrough assignment). This value
        # is not read at runtime; it's passed anyway so a future fix
        # that makes MemoryInterfaceHandler actually honor this
        # parameter doesn't silently break this harness.
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x37, 0x37), (0x38, 0x3F),
                                 (0x40, 0x6F), (0x70, 0x8B), (0xB0, 0xB4),
                                 (0xFE, 0xFF)],
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

    timer0 = punxa.TimerCounter0(hw, 'timer0', timer0_p,
                                  OC0B=oc0b_wire, OC0A=oc0a_wire, T0=t0_wire,
                                  OCF0B=ocf0b_wire, OCF0A=ocf0a_wire, TOV0=tov0_wire)
    timer1 = punxa.TimerCounter1(hw, 'timer1', timer1_p,
                                  OC1B=oc1b_wire, OC1A=oc1a_wire, T1=t1_wire,
                                  OCF1B=ocf1b_wire, OCF1A=ocf1a_wire, TOV1=tov1_wire,
                                  ICF1=icf1_wire)
    timer2 = punxa.TimerCounter2(hw, 'timer2', timer2_p,
                                  OC2B=oc2b_wire, OC2A=oc2a_wire, T2=t2_wire,
                                  OCF2B=ocf2b_wire, OCF2A=ocf2a_wire, TOV2=tov2_wire)

    pk = peer_kwargs or {}
    p0 = dict(t0_enabled=True, t0_period=DEFAULT_EXT_CLK_PERIOD)
    p0.update(pk.get('timer0', {}))
    p1 = dict(t0_enabled=True, t0_period=DEFAULT_EXT_CLK_PERIOD)
    p1.update(pk.get('timer1', {}))
    p2 = dict(t0_enabled=True, t0_period=DEFAULT_EXT_CLK_PERIOD)
    p2.update(pk.get('timer2', {}))

    peer0 = PeerTimer(hw, 'peer0', T0_out=t0_wire, OC0A_in=oc0a_wire, OC0B_in=oc0b_wire, **p0)
    peer1 = PeerTimer(hw, 'peer1', T0_out=t1_wire, OC0A_in=oc1a_wire, OC0B_in=oc1b_wire, **p1)
    peer2 = PeerTimer(hw, 'peer2', T0_out=t2_wire, OC0A_in=oc2a_wire, OC0B_in=oc2b_wire, **p2)

    interrupt_module = SimpleInterruptUnit(
        hw, 'interrupt_module',
        memory=int_unit_p,
        Interrupt=interrupt_wire,
        Global_Interrupt_Enable=global_interrupt_enable_wire,
        TIMER0_COMPA=ocf0a_wire, TIMER0_COMPB=ocf0b_wire, TIMER0_OVF=tov0_wire,
        TIMER1_COMPA=ocf1a_wire, TIMER1_COMPB=ocf1b_wire, TIMER1_OVF=tov1_wire,
        TIMER1_CAPT=icf1_wire,
        TIMER2_COMPA=ocf2a_wire, TIMER2_COMPB=ocf2b_wire, TIMER2_OVF=tov2_wire,
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
# Optional wire-level checks: OC pin toggling can't be confirmed from
# CPU-visible state alone, only from the pins -- keyed by test filename ->
# minimum edge counts expected by the time the test reaches 'end'. Absent
# entries mean no pin check for that test.
# =============================================================================
PEER_PIN_CHECKS = {
    'test_timer0_ctc_compare_match_toggle.asm': {'oc0a_min_edges': 3},
    'test_timer2_ctc_compare_match_toggle.asm': {'oc2a_min_edges': 3},
    'test_timer0_fast_pwm_toggle_oc0a.asm': {'oc0a_min_edges': 3},
    'test_timer0_fast_pwm_non_inverting.asm': {'oc0a_min_edges': 2},
    'test_timer0_fast_pwm_inverting.asm': {'oc0a_min_edges': 2},
    'test_timer0_phase_correct_pwm_toggle_oc0a.asm': {'oc0a_min_edges': 3},
    'test_timer0_phase_correct_pwm_non_inverting.asm': {'oc0a_min_edges': 2},
    'test_timer0_phase_correct_pwm_inverting.asm': {'oc0a_min_edges': 2},
    'test_timer0_force_output_compare_a.asm': {'oc0a_min_edges': 1},
    'test_timer0_force_output_compare_b.asm': {'oc0b_min_edges': 1},
    'test_timer0_output_compare_a_only.asm': {'oc0a_min_edges': 1, 'oc0b_max_edges': 0},
    'test_timer0_output_compare_b_only.asm': {'oc0b_min_edges': 1, 'oc0a_max_edges': 0},
    'test_timer0_simultaneous_compare_match_a_b.asm': {'oc0a_min_edges': 1, 'oc0b_min_edges': 1},
    'test_timer0_compare_output_state_after_reset.asm': {'oc0a_max_edges': 0, 'oc0b_max_edges': 0},
    'test_timer2_fast_pwm_toggle_oc2a.asm': {'oc2a_min_edges': 3},
    'test_timer2_fast_pwm_non_inverting.asm': {'oc2a_min_edges': 2},
    'test_timer2_fast_pwm_inverting.asm': {'oc2a_min_edges': 2},
    'test_timer2_phase_correct_pwm_toggle_oc2a.asm': {'oc2a_min_edges': 3},
    'test_timer2_phase_correct_pwm_non_inverting.asm': {'oc2a_min_edges': 2},
    'test_timer2_phase_correct_pwm_inverting.asm': {'oc2a_min_edges': 2},
    'test_timer2_force_output_compare_a.asm': {'oc2a_min_edges': 1},
    'test_timer2_force_output_compare_b.asm': {'oc2b_min_edges': 1},
    'test_timer2_output_compare_a_only.asm': {'oc2a_min_edges': 1, 'oc2b_max_edges': 0},
    'test_timer2_output_compare_b_only.asm': {'oc2b_min_edges': 1, 'oc2a_max_edges': 0},
    'test_timer1_fast_pwm_8bit_non_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_fast_pwm_8bit_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_phase_correct_pwm_8bit_non_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_phase_correct_pwm_8bit_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_fast_pwm_9bit_non_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_fast_pwm_9bit_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_phase_correct_pwm_9bit_non_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_phase_correct_pwm_9bit_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_fast_pwm_10bit_non_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_fast_pwm_10bit_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_phase_correct_pwm_10bit_non_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_phase_correct_pwm_10bit_inverting.asm': {'oc1a_min_edges': 2},
    'test_timer1_normal_mode_toggle.asm': {'oc1a_min_edges': 1},
    'test_timer1_fast_pwm_top_icr1.asm': {'oc1a_min_edges': 1},
    'test_timer1_fast_pwm_top_ocr1a.asm': {'oc1a_min_edges': 1},
    'test_timer1_phase_frequency_correct_pwm_top_icr1.asm': {'oc1a_min_edges': 1},
    'test_timer1_phase_frequency_correct_pwm_top_ocr1a.asm': {'oc1a_min_edges': 1},
    'test_timer1_force_output_compare_a.asm': {'oc1a_min_edges': 1},
    'test_timer1_force_output_compare_b.asm': {'oc1b_min_edges': 1},
    'test_timer1_output_compare_a_only.asm': {'oc1a_min_edges': 1, 'oc1b_max_edges': 0},
    'test_timer1_output_compare_b_only.asm': {'oc1b_min_edges': 1, 'oc1a_max_edges': 0},
}


def runTest(file, peer_kwargs=None):
    hw, cpu, ins_mem, mem, symbols = prepareTest(file, peer_kwargs=peer_kwargs)

    # Timer tests busy-wait on TIFR*/TCNT* polling loops -- generous
    # headroom to absorb prescaler waits and multicycle fetch/decode
    # overhead per poll, same spirit as tb_usart.py / the old
    # tb_timers.py's step_limit.
    step_limit = 300000
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
        peers = {'oc0a': peer0, 'oc0b': peer0, 'oc1a': peer1, 'oc1b': peer1,
                 'oc2a': peer2, 'oc2b': peer2}
        for key, bound in check.items():
            # key is '<pin>_min_edges' or '<pin>_max_edges'
            if key.endswith('_min_edges'):
                pin = key[:-len('_min_edges')]
                is_min = True
            else:
                pin = key[:-len('_max_edges')]
                is_min = False
            peer = peers[pin]
            attr = 'oc0a_edge_count' if pin.endswith('a') else 'oc0b_edge_count'
            count = getattr(peer, attr)
            if is_min and count < bound:
                raise Exception(f'{pin.upper()} pin never toggled as expected: saw {count} '
                                 f'edge(s), expected >= {bound}')
            if not is_min and count > bound:
                raise Exception(f'{pin.upper()} pin toggled unexpectedly: saw {count} '
                                 f'edge(s), expected <= {bound}')


# =============================================================================
# TEST SUITE CONFIGURATION & RUNNERS (same shape as the ISA harness)
# =============================================================================
ex_dir = 'timer_tests/'
selected_prefixes = ['test_timer0', 'test_timer1', 'test_timer2']


def _run_one_test_silent(f):
    """Same rationale as tb_ISA_test_Multicycle_Rewrite.py's function of the
    same name: a separate OS process per worker, not a thread, because
    py4hw.Wire's prepared/dirty bookkeeping is class-level and shared
    (and therefore racy) across threads in one process."""
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            runTest(f)
            return f, 'OK'
        except Exception as e:
            return f, ('FAILED', e)


def computeAllTests(num_threads=1):
    files = os.listdir(ex_dir)
    files = [name for name in files if any(name.startswith(prefix) for prefix in selected_prefixes)]
    files = [name for name in files if name[-4:].lower() == '.asm']

    ret = {}

    if num_threads is None or num_threads <= 1:
        for f in files:
            print('Run test', f, end=' ')
            try:
                runTest(f)
                print('PASSED')
                ret[f] = 'OK'
            except Exception as e:
                print('FAILED')
                ret[f] = ('FAILED', e)
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(_run_one_test_silent, f): f for f in files}
            done_count = 0
            total = len(futures)
            for future in concurrent.futures.as_completed(futures):
                filename, result = future.result()
                ret[filename] = result
                done_count += 1
                status = 'PASSED' if result == 'OK' else 'FAILED'
                print('[{}/{}] {} {}'.format(done_count, total, filename, status))

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


def runAllTests(num_threads=1):
    global selected_prefixes
    start_time = time.time()
    nOK = 0
    nTotal = 0
    ret = computeAllTests(num_threads)

    if not ret:
        print(f'No {"/".join(p + "_*.asm" for p in selected_prefixes)} files found in {ex_dir}.')
        return

    groupResults = {}

    for prefix in selected_prefixes:
        nOKGroup = 0
        nTotalGroup = 0

        files = [name for name in ret.keys() if name.startswith(prefix)]
        for t in files:
            nTotal += 1
            nTotalGroup += 1
            if (ret[t] == 'OK'):
                print('Test {:40} = {}'.format(t, ret[t]))
                nOK += 1
                nOKGroup += 1
            else:
                print('Test {:40} = {} - {}'.format(t, ret[t][0], ret[t][1]))

        groupResults[prefix] = (nOKGroup, nTotalGroup)

    print('Total: {} Correct: {} ({:.1f} %)'.format(nTotal, nOK, nOK * 100 / nTotal))
    print(asciiProgressBar(nOK, nTotal))

    for prefix in selected_prefixes:
        nOKGroup, nTotalGroup = groupResults[prefix]
        if (nTotalGroup == 0):
            nTotalGroup = 1
        print('Group: {} Total: {} Correct: {} ({:.1f} %)'.format(prefix, nTotalGroup, nOKGroup, nOKGroup * 100 / nTotalGroup))

    for prefix in selected_prefixes:
        nOKGroup, nTotalGroup = groupResults[prefix]
        if (nTotalGroup == 0):
            nTotalGroup = 1
        print(f'{prefix:15}', asciiProgressBar(nOKGroup, nTotalGroup))

    elapsed_time = time.time() - start_time
    print('\n' + '=' * 60)
    print(f'Execution Time: {elapsed_time:.2f} seconds')
    print('=' * 60)


if __name__ == "__main__":
    print(sys.argv)

    if (len(sys.argv) > 1):
        if (sys.argv[1] == '-c'):
            eval(sys.argv[2])
            os._exit(0)
