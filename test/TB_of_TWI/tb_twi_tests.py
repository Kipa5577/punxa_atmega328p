# -*- coding: utf-8 -*-
"""
TWI0 (I2C) CPU-integration test bench -- same shape as tb_timer_tests.py /
tb_ISA_test_Multicycle_Rewrite.py: MulticycleCpuWrapper, runTest/
computeAllTests/runAllTests with process-pool parallel execution,
`python3 -i tb_twi_tests.py` interactive workflow.

TWI0 is master-mode only (see punxa_atmega328p/TWI.py's docstring for
the full scope/limitations list), so PeerI2CSlave (peer_i2c_slave.py) is
wired in as the "other end of the wire" -- SCL/SDA are real open-drain
lines, modeled with TWI.py's OpenDrainAnd combiner ANDing both agents'
drive-intent wires into the one shared line both sense.

Run interactively: `python3 -i tb_twi_tests.py`, then e.g.
`runAllTests(num_threads=4)`.
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
from punxa_atmega328p.TWI import TWI0, OpenDrainAnd
from peer_i2c_slave import PeerI2CSlave


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


DEFAULT_SLAVE_ADDR = 0x20


def prepareTest(file, preload=True, slave_addr=DEFAULT_SLAVE_ADDR, slave_read_bytes=None):
    global hw, cpu, ins_mem, mem, twi, peer

    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    words, symbols = assemble_program(program)

    hw = py4hw.HWSystem()

    dw = 8
    aw = 16

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)
    twi_p = punxa.MemoryInterface(hw, 'twi_port', dw, 8)
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)
    twi_int_wire = py4hw.Wire(hw, 'twi_int', 1); twi_int_wire.put(0)

    # --- Open-drain SCL/SDA bus: each agent's private intent wire, ANDed
    # into the one shared line both agents sense. ---
    twi_scl_intent = py4hw.Wire(hw, 'twi_scl_intent', 1); twi_scl_intent.put(1)
    peer_scl_intent = py4hw.Wire(hw, 'peer_scl_intent', 1); peer_scl_intent.put(1)
    scl_line = py4hw.Wire(hw, 'scl_line', 1); scl_line.put(1)

    twi_sda_intent = py4hw.Wire(hw, 'twi_sda_intent', 1); twi_sda_intent.put(1)
    peer_sda_intent = py4hw.Wire(hw, 'peer_sda_intent', 1); peer_sda_intent.put(1)
    sda_line = py4hw.Wire(hw, 'sda_line', 1); sda_line.put(1)

    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(twi_p, 0x0, 0x100),
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
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x37, 0x37), (0x38, 0x3F),
                                 (0x40, 0x6F), (0x70, 0x8B), (0xB0, 0xB4),
                                 (0xB8, 0xBC), (0xFE, 0xFF)],
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

    twi = TWI0(hw, 'twi0', twi_p,
               SCL_drive=twi_scl_intent, SCL_sense=scl_line,
               SDA_drive=twi_sda_intent, SDA_sense=sda_line,
               TWI_INT=twi_int_wire)
    peer = PeerI2CSlave(hw, 'peer', SCL_drive=peer_scl_intent, SCL_sense=scl_line,
                         SDA_drive=peer_sda_intent, SDA_sense=sda_line,
                         slave_addr=slave_addr, read_bytes=slave_read_bytes)

    OpenDrainAnd(hw, 'scl_and', [twi_scl_intent, peer_scl_intent], scl_line)
    OpenDrainAnd(hw, 'sda_and', [twi_sda_intent, peer_sda_intent], sda_line)

    interrupt_module = SimpleInterruptUnit(
        hw, 'interrupt_module',
        memory=int_unit_p,
        Interrupt=interrupt_wire,
        Global_Interrupt_Enable=global_interrupt_enable_wire,
        TWI=twi_int_wire,
    )

    if preload:
        for i, b in enumerate(words):
            ins_mem.writeWord(i, b)
    else:
        for i in range(1 << 14):
            ins_mem.writeWord(i, 0xFFFF)

    cpu.assembled_words = words
    return hw, cpu, ins_mem, mem, symbols


def runTest(file, slave_addr=DEFAULT_SLAVE_ADDR, slave_read_bytes=None):
    hw, cpu, ins_mem, mem, symbols = prepareTest(file, slave_addr=slave_addr,
                                                  slave_read_bytes=slave_read_bytes)

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


# Per-test slave configuration, keyed by filename -- mirrors how
# tb_timer_tests.py's peer_kwargs works, just fixed per file here since
# these tests don't need per-run overrides.
TEST_SLAVE_CONFIG = {
    'test_twi_master_write_byte.asm': {'slave_addr': 0x20, 'slave_read_bytes': None},
    'test_twi_master_read_byte.asm': {'slave_addr': 0x20, 'slave_read_bytes': [0xA5]},
}

# Bytes the test's peer received during a write test -- checked after
# the fact, same spirit as tb_timer_tests.py's PEER_PIN_CHECKS.
PEER_RX_CHECKS = {
    'test_twi_master_write_byte.asm': [0x42],
}


def _run_one_test_silent(f):
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            cfg = TEST_SLAVE_CONFIG.get(f, {})
            runTest(f, **cfg)
            check = PEER_RX_CHECKS.get(f)
            if check is not None and peer.received_bytes != check:
                raise Exception(f'Peer received {peer.received_bytes!r}, expected {check!r}')
            return f, 'OK'
        except Exception as e:
            return f, ('FAILED', e)


def computeAllTests(num_threads=1):
    files = os.listdir(ex_dir)
    files = [name for name in files if name.startswith('test_twi') and name[-4:].lower() == '.asm']

    ret = {}

    if num_threads is None or num_threads <= 1:
        for f in files:
            print('Run test', f, end=' ')
            try:
                cfg = TEST_SLAVE_CONFIG.get(f, {})
                runTest(f, **cfg)
                check = PEER_RX_CHECKS.get(f)
                if check is not None and peer.received_bytes != check:
                    raise Exception(f'Peer received {peer.received_bytes!r}, expected {check!r}')
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
    ret = computeAllTests(num_threads)

    if not ret:
        print(f'No test_twi_*.asm files found in {ex_dir}.')
        return

    nTotal = len(ret)
    nOK = sum(1 for v in ret.values() if v == 'OK')

    for t, r in ret.items():
        if r == 'OK':
            print('Test {:40} = {}'.format(t, r))
        else:
            print('Test {:40} = {} - {}'.format(t, r[0], r[1]))

    print('Total: {} Correct: {} ({:.1f} %)'.format(nTotal, nOK, nOK * 100 / nTotal))
    print(asciiProgressBar(nOK, nTotal))

    elapsed_time = time.time() - start_time
    print('\n' + '=' * 60)
    print(f'Execution Time: {elapsed_time:.2f} seconds')
    print('=' * 60)


ex_dir = 'twi_tests/'

if __name__ == "__main__":
    print(sys.argv)

    if (len(sys.argv) > 1):
        if (sys.argv[1] == '-c'):
            eval(sys.argv[2])
            os._exit(0)
