# -*- coding: utf-8 -*-
"""
ADC CPU-integration test bench -- same shape as tb_gpio_tests.py/
tb_timer_tests.py (MulticycleCpuWrapper, prepareTest/runTest/
computeAllTests/runAllTests, `python3 -i tb_adc_tests.py` interactive
workflow, ProcessPoolExecutor-based parallel execution).

ADC is a single component (like GPIO, unlike Timer0/1/2) so it's wired
as one wide MultiplexedBus window over 0x00-0x100, same pattern as
gpio_p in tb_gpio_tests.py / timer_master_p in tb_timer_tests.py.

One peer, PeerADC (peer_adc.py), supplying the eight pre-quantized
channel codes and the six auto-trigger source pulses -- see ADC.py's own
class docstring and peer_adc.py's docstring for why input channels are
digital codes here rather than real analog voltages.

Run interactively: `python3 -i tb_adc_tests.py`, then e.g.
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
from punxa_atmega328p.ADC import ADC
from peer_adc import PeerADC


# =============================================================================
# COMPATIBILITY WRAPPER (identical approach to tb_gpio_tests.py / tb_timer_tests.py)
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
def prepareTest(file, preload=True, peer_kwargs=None):
    """peer_kwargs: optional dict forwarded to PeerADC's constructor,
    e.g. {'init_codes': {0: 512, 3: 1023}} to have channel ADC0 read
    512/1023 and ADC3 read full-scale from cycle 0."""
    global hw, cpu, ins_mem, mem, adc, peer

    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    words, symbols = assemble_program(program)

    hw = py4hw.HWSystem()

    dw = 8
    aw = 16

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)
    adc_p = punxa.MemoryInterface(hw, 'adc_port', dw, 8)
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)

    def _w1(nm, init=0):
        w = py4hw.Wire(hw, nm, 1)
        w.put(init)
        return w

    def _w10(nm, init=0):
        w = py4hw.Wire(hw, nm, 10)
        w.put(init)
        return w

    chan_wires = [_w10(f'adc{i}_pin') for i in range(8)]
    aco_w, int0_w = _w1('aco_pin'), _w1('int0_pin')
    t0ca_w, t0ovf_w = _w1('t0_compa_pin'), _w1('t0_ovf_pin')
    t1cb_w, t1ovf_w, t1capt_w = _w1('t1_compb_pin'), _w1('t1_ovf_pin'), _w1('t1_capt_pin')
    adc_irq_w = _w1('adc_irq_pin')

    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(adc_p, 0x0, 0x100),
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
        # Kept for interface-compatibility only -- the real gate is the
        # inline is_passthrough check in MemoryInterfaceHandler.clock(),
        # extended this round to cover 0x78-0x7E (ADCL/ADCH/ADCSRA/
        # ADCSRB/ADMUX/DIDR0) -- see that file's comment at the
        # is_passthrough assignment.
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x37, 0x37), (0x38, 0x3F),
                                 (0x40, 0x6F), (0x78, 0x7E), (0xFE, 0xFF)],
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

    adc = ADC(hw, 'adc', adc_p,
              ADC0=chan_wires[0], ADC1=chan_wires[1], ADC2=chan_wires[2], ADC3=chan_wires[3],
              ADC4=chan_wires[4], ADC5=chan_wires[5], ADC6=chan_wires[6], ADC7=chan_wires[7],
              ADC_IRQ=adc_irq_w,
              ACO_trig=aco_w, INT0_trig=int0_w,
              T0_COMPA_trig=t0ca_w, T0_OVF_trig=t0ovf_w,
              T1_COMPB_trig=t1cb_w, T1_OVF_trig=t1ovf_w, T1_CAPT_trig=t1capt_w)

    pk = dict(peer_kwargs or {})
    peer = PeerADC(hw, 'peer',
                   ADC0_out=chan_wires[0], ADC1_out=chan_wires[1],
                   ADC2_out=chan_wires[2], ADC3_out=chan_wires[3],
                   ADC4_out=chan_wires[4], ADC5_out=chan_wires[5],
                   ADC6_out=chan_wires[6], ADC7_out=chan_wires[7],
                   ACO_out=aco_w, INT0_out=int0_w,
                   T0_COMPA_out=t0ca_w, T0_OVF_out=t0ovf_w,
                   T1_COMPB_out=t1cb_w, T1_OVF_out=t1ovf_w, T1_CAPT_out=t1capt_w,
                   **pk)

    interrupt_module = SimpleInterruptUnit(
        hw, 'interrupt_module',
        memory=int_unit_p,
        Interrupt=interrupt_wire,
        Global_Interrupt_Enable=global_interrupt_enable_wire,
        ADC=adc_irq_w,
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
# Per-test default peer configuration (see peer_adc.py docstring) -- input
# channels can't be set from the .asm side, so tests that read a specific
# code from a channel need it supplied here, keyed by filename, same
# pattern as tb_gpio_tests.py's TEST_PEER_KWARGS.
# =============================================================================
TEST_PEER_KWARGS = {
    'test_adc_single_conversion.asm':   {'init_codes': {0: 0x2AA}},   # 682/1023
    'test_adc_channel_select.asm':      {'init_codes': {0: 0x100, 3: 0x300, 7: 0x3FF}},
    'test_adc_left_adjust.asm':         {'init_codes': {0: 0x2AA}},
    'test_adc_free_running.asm':        {'init_codes': {0: 0x111}},
    'test_adc_auto_trigger_t0ovf.asm':  {'init_codes': {0: 0x0AB},
                                          'autopulse': {'source': 'T0_OVF', 'period': 50}},
    'test_adc_prescaler_timing.asm':    {'init_codes': {0: 0x155}},
    'test_adc_interrupt.asm':           {'init_codes': {0: 0x0CC}},
    'test_adc_adcl_lock.asm':           {'init_codes': {0: 0x2AA, 1: 0x155}},
}

# ADC_IRQ is a wire the CPU itself can't read back (there's no vector-
# dispatch check here -- see test_adc_interrupt.asm's own comment for
# why that's out of scope for this round). Checked independently from
# the peer/harness side, same rationale and shape as tb_gpio_tests.py's
# PEER_EDGE_CHECKS. Keyed by filename -> expected level at test end.
IRQ_LEVEL_CHECKS = {
    'test_adc_interrupt.asm': 0,   # ADIE is cleared again before 'end' in this test
}


def runTest(file, peer_kwargs=None):
    if peer_kwargs is None:
        peer_kwargs = TEST_PEER_KWARGS.get(file)
    hw, cpu, ins_mem, mem, symbols = prepareTest(file, peer_kwargs=peer_kwargs)
    #silence_debug(cpu._cpu)

    step_limit = 50000
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

    if file in IRQ_LEVEL_CHECKS:
        expected = IRQ_LEVEL_CHECKS[file]
        actual = adc.ADC_IRQ.get()
        if actual != expected:
            raise Exception(f'ADC_IRQ wire = {actual}, expected {expected} '
                             f'(checked independently of CPU-visible state)')


# =============================================================================
# TEST SUITE CONFIGURATION & RUNNERS (same shape as tb_gpio_tests.py)
# =============================================================================
ex_dir = 'adc_tests/'
selected_prefixes = ['test_adc']


def _run_one_test_silent(f):
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
    start_time = time.time()
    nOK = 0
    nTotal = 0
    ret = computeAllTests(num_threads)

    if not ret:
        print(f'No test_adc_*.asm files found in {ex_dir}.')
        return

    for t in sorted(ret.keys()):
        nTotal += 1
        if (ret[t] == 'OK'):
            print('Test {:45} = {}'.format(t, ret[t]))
            nOK += 1
        else:
            print('Test {:45} = {} - {}'.format(t, ret[t][0], ret[t][1]))

    print('Total: {} Correct: {} ({:.1f} %)'.format(nTotal, nOK, nOK * 100 / nTotal if nTotal else 0))
    print(asciiProgressBar(nOK, nTotal if nTotal else 1))

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
