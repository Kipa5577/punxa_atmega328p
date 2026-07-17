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


def prepareTest(file, preload=True, peer_kwargs=None):
    global hw, cpu, ins_mem, mem, usart, peer

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

    usart = punxa.USART0(hw, 'usart0', usart_p,
                          RXD=rxd_wire, TXD=txd_wire, USART_CLK=usart_clk_wire,
                          RXC_INT=usart_rxc_wire, TXC_INT=usart_txc_wire,
                          UDRE_INT=usart_udre_wire)

    pk = dict(ubrr=DEFAULT_UBRR0, nbBits=8, parity='Disabled', nbStopBits=1,
              ticks_per_bit=DEFAULT_TICKS_PER_BIT, echo=True)
    if peer_kwargs:
        pk.update(peer_kwargs)
    # peer.RXD_out drives the DUT's RXD pin; peer.TXD_in samples the
    # DUT's TXD pin -- i.e. crossed relative to the DUT's own naming,
    # exactly like connecting two real UARTs together.
    peer = PeerUART(hw, 'peer', RXD_out=rxd_wire, TXD_in=txd_wire, **pk)

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


def runTest(file, peer_kwargs=None):
    hw, cpu, ins_mem, mem, symbols = prepareTest(file, peer_kwargs=peer_kwargs)

    # USART tests are byte-serial, not just instruction-serial: one byte
    # at the default UBRR0=10/8N1 takes 10 bits * 16 ticks/bit * 11
    # cycles/tick ~= 1760 cycles, before any CPU polling overhead on top
    # of that. Generous headroom for a handful of bytes per test.
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
