# -*- coding: utf-8 -*-
"""
GPIO CPU-integration test bench -- same shape as tb_timer_tests.py/
tb_twi_tests.py (MulticycleCpuWrapper, prepareTest/runTest/
computeAllTests/runAllTests, `python3 -i tb_gpio_tests.py` interactive
workflow, ProcessPoolExecutor-based parallel execution).

GPIO doesn't need a bus router the way Timer0/1/2 did -- it's a single
component whose own clock() already dispatches PORTB/DDRB/PINB/PORTC/
DDRC/PINC/PORTD/DDRD/PIND/GPIOR0-2 internally by exact address, so it's
wired as one MultiplexedBus slave over the full 0x00-0x100 low I/O
window, same pattern as timer_master_p in tb_timer_tests.py -- placed
first in the slave list so the narrower reg/sp/int_unit windows placed
after it still win on their own addresses (MultiplexedBus is
last-match-wins, not break-on-first-match; see timer_bus_router.py's
docstring for the underlying reason this matters).

One peer, PeerGPIO (peer_gpio.py), wired to all three ports' physical
pins at once -- unlike Timer0/1/2 needing three separate PeerTimer
instances (three independent clock-in/compare-out trios), GPIO's ports
are independent from the peer's point of view too, so this harness
instantiates one PeerGPIO per port (peer_b/peer_c/peer_d) rather than
one peer juggling all 24 pins, keeping each test's per-port peer calls
readable (e.g. `peer_b.drive(0xAA, 0xFF)`).

Round (GPIO pin-level pass): built alongside the GPIO.py fixes (resp
polarity inversion, missing resp.prepare on several write branches, the
DDRD dead-write bug, and the new physical pin wires themselves -- see
GPIO.py's class docstring for full detail). This is GPIO's first real
CPU-integration testbench; the old TB_of_GPIO/TB_of_GPIO.py is stale --
it calls `GPIO(sys, 'GPIO', Interface, instype)` with an extra
positional `instype` argument that no longer matches GPIO.__init__'s
signature (instype has been read from the interface itself,
`self.interface.instype.get()`, for as long as this class has existed
in this archive -- that testbench predates even that and was never
updated), and it only ever pokes the bus directly with py4hw.Sequence,
never through the real CPU or against physical pins. Left in place for
now as a reference for the register address tables it hardcodes, but
superseded by this file + gpio_tests/*.asm.

Run interactively: `python3 -i tb_gpio_tests.py`, then e.g.
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
from peer_gpio import PeerGPIO


# =============================================================================
# COMPATIBILITY WRAPPER (identical approach to tb_timer_tests.py / tb_usart.py)
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
    """peer_kwargs: optional dict of {'b': {...}, 'c': {...}, 'd': {...}}
    to override that port's PeerGPIO construction (e.g.
    {'b': {'init_ext_out': 0xAA, 'init_ext_oe': 0xFF}} to have the peer
    drive all 8 PORTB pins with a fixed pattern from cycle 0)."""
    global hw, cpu, ins_mem, mem, gpio, peer_b, peer_c, peer_d

    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    words, symbols = assemble_program(program)

    hw = py4hw.HWSystem()

    dw = 8
    aw = 16

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)
    gpio_p = punxa.MemoryInterface(hw, 'gpio_port', dw, 8)
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)

    # --- GPIO <-> PeerGPIO pin wires, one quartet per port ---
    def _pin_quartet(prefix):
        val = py4hw.Wire(hw, f'{prefix}_val', 8); val.put(0)
        oe = py4hw.Wire(hw, f'{prefix}_oe', 8); oe.put(0)
        ext_in = py4hw.Wire(hw, f'{prefix}_ext_in', 8); ext_in.put(0)
        ext_oe = py4hw.Wire(hw, f'{prefix}_ext_oe', 8); ext_oe.put(0)
        return val, oe, ext_in, ext_oe

    b_val, b_oe, b_ext_in, b_ext_oe = _pin_quartet('portb')
    c_val, c_oe, c_ext_in, c_ext_oe = _pin_quartet('portc')
    d_val, d_oe, d_ext_in, d_ext_oe = _pin_quartet('portd')

    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(gpio_p, 0x0, 0x100),
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
        # Kept for interface-compatibility only -- see the note in
        # tb_timer_tests.py's prepareTest: the real gate is the inline
        # is_passthrough check in MemoryInterfaceHandler.clock(), which
        # already covers 0x20-0x36 (all of GPIO's PORTx/DDRx/PINx
        # addresses) and 0x38-0x3F/0x40-0x6F (GPIOR0/1/2's addresses)
        # with no changes needed for this harness.
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x37, 0x37), (0x38, 0x3F),
                                 (0x40, 0x6F), (0xFE, 0xFF)],
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

    gpio = punxa.GPIO(hw, 'gpio', gpio_p,
                       PORTB_val=b_val, PORTB_oe=b_oe, PORTB_ext_in=b_ext_in, PORTB_ext_oe=b_ext_oe,
                       PORTC_val=c_val, PORTC_oe=c_oe, PORTC_ext_in=c_ext_in, PORTC_ext_oe=c_ext_oe,
                       PORTD_val=d_val, PORTD_oe=d_oe, PORTD_ext_in=d_ext_in, PORTD_ext_oe=d_ext_oe)

    pk = peer_kwargs or {}
    kb = dict(init_ext_out=0x00, init_ext_oe=0x00); kb.update(pk.get('b', {}))
    kc = dict(init_ext_out=0x00, init_ext_oe=0x00); kc.update(pk.get('c', {}))
    kd = dict(init_ext_out=0x00, init_ext_oe=0x00); kd.update(pk.get('d', {}))

    peer_b = PeerGPIO(hw, 'peer_b', val_in=b_val, oe_in=b_oe, ext_out=b_ext_in, ext_oe_out=b_ext_oe, **kb)
    peer_c = PeerGPIO(hw, 'peer_c', val_in=c_val, oe_in=c_oe, ext_out=c_ext_in, ext_oe_out=c_ext_oe, **kc)
    peer_d = PeerGPIO(hw, 'peer_d', val_in=d_val, oe_in=d_oe, ext_out=d_ext_in, ext_oe_out=d_ext_oe, **kd)

    interrupt_module = SimpleInterruptUnit(
        hw, 'interrupt_module',
        memory=int_unit_p,
        Interrupt=interrupt_wire,
        Global_Interrupt_Enable=global_interrupt_enable_wire,
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
# Per-test default peer configuration: tests that need the peer driving a
# fixed pattern onto a port's pins *before* the CPU code runs (e.g. an
# input/pull-up test) can't set that up from the .asm side -- PeerGPIO's
# ext drive is static-per-test by construction (see peer_gpio.py's
# docstring), same as PeerTimer's t0_period being fixed at construction
# in tb_timer_tests.py. Keyed by filename; used automatically by
# runTest/computeAllTests when no explicit peer_kwargs is passed.
# =============================================================================
TEST_PEER_KWARGS = {
    'test_gpio_pin_read.asm':            {'b': {'init_ext_out': 0x5A, 'init_ext_oe': 0xFF}},
    'test_gpio_single_pin_input.asm':    {'b': {'init_ext_out': 0x01, 'init_ext_oe': 0x01}},
    'test_gpio_input_with_pullup.asm':   {'b': {'init_ext_out': 0x00, 'init_ext_oe': 0x00}},
    'test_gpio_pullup_disable.asm':      {'b': {'init_ext_out': 0x00, 'init_ext_oe': 0x00}},
}

# Pin toggling on an output can't be confirmed from CPU-visible state
# alone (GPIO.PORTx readback tells you what was written, not that it
# ever reached a pin) -- same rationale as tb_timer_tests.py's
# PEER_PIN_CHECKS for OC0A/OC0B. Keyed by filename -> {port: min edges}.
PEER_EDGE_CHECKS = {
    'test_gpio_output_toggle.asm': {'b': 4},
}


def runTest(file, peer_kwargs=None):
    if peer_kwargs is None:
        peer_kwargs = TEST_PEER_KWARGS.get(file)
    hw, cpu, ins_mem, mem, symbols = prepareTest(file, peer_kwargs=peer_kwargs)
    silence_debug(cpu._cpu)

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

    check = PEER_EDGE_CHECKS.get(file)
    if check:
        peers = {'b': peer_b, 'c': peer_c, 'd': peer_d}
        for port, minimum in check.items():
            peer = peers[port]
            if peer.edge_count < minimum:
                raise Exception(f'PORT{port.upper()} pins never toggled as expected '
                                 f'(observed via PeerGPIO, not GPIO\'s own bookkeeping): '
                                 f'saw {peer.edge_count} edge(s), expected >= {minimum}')


# =============================================================================
# TEST SUITE CONFIGURATION & RUNNERS (same shape as tb_timer_tests.py)
# =============================================================================
ex_dir = 'gpio_tests/'
selected_prefixes = ['test_gpio']


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
        print(f'No test_gpio_*.asm files found in {ex_dir}.')
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
