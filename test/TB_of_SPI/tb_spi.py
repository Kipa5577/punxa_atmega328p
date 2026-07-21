# -*- coding: utf-8 -*-
"""
SPI CPU-integration test bench.

Separate from the ISA suite (tb_ISA_test_Multicycle_Rewrite.py /
isa/test_*.asm) and from the raw-register spi_tests/ Python suite
(spi_test_harness.py) on purpose: this exercises SPI through the real
CPU running real assembled .asm programs, the same way tb_usart.py
does for USART0 -- not general ISA correctness, and not a
register-poke-level unit check either. Its test programs live in
spi_tests/ *.asm (a sibling directory of this file's parent, see
`ex_dir` below) -- the raw-register Python spi_tests/*.py files from
the earlier unit-test pass stay where they are and keep doing their
own, faster, CPU-free job; this suite is the additional, slower,
end-to-end layer on top.

Structurally this is the same pattern as tb_usart.py -- same
MulticycleCpuWrapper/_find_child compatibility shim, same
runTest/computeAllTests/runAllTests/asciiProgressBar shape, same
"python -i tb_spi.py" interactive workflow -- with the differences
that follow from SPI being clock-*master*-driven instead of UART's
independent-baud-on-both-ends:

1. SPI replaces nothing at a dedicated bus window the way USART0 sits
   at 0xC0 -- SPCR/SPSR/SPDR (0x2C-0x2E) fall *inside* the same
   [0x20,0x3F] block GPIO already owns wholesale in this project's
   coarse per-peripheral bus-window convention. Rather than shrinking
   gpio_p's window (which would diverge from the ISA/USART harnesses'
   memory map) or moving SPI to a non-real address (which would
   diverge from real ATmega328P register addresses, and from SPI.py's
   own SPCR_addr_LS=0x2C etc.), `spi_p` is listed *after* `gpio_p` in
   MultiplexedBus's slave list below: MultiplexedBus.propagate() does
   not `break` on the first matching range, so for any address that
   falls in both windows (only 0x2C-0x2E does), gpio_p is asked first
   and NAKs it (no register of its own lives there -- confirmed
   against GPIO.py: its real registers in this range are 0x23-0x2B),
   then spi_p is asked and answers, overwriting gpio_p's non-response
   on the shared master lines. Every other address in gpio_p's window
   is untouched by this (spi_p simply never claims it).
2. SPI's own !SS pin is Master-mode-fault detection only (see SPI.py)
   -- it is not a chip-select output, so unlike USART0<->PeerUART
   there's no "wire crossing" for a select line: PeerSPI just watches
   CLK/MOSI directly (see peer_spi.py's docstring for why no !SS
   modeling is even needed for that).
3. Bus_Passthrough_Ranges: reuses the same (0x20, 0x36) range
   tb_usart.py already needs for GPIO -- 0x2C-0x2E falls inside it, so
   nothing extra is required there for SPI to be reachable via real
   STS/LDS/IN/OUT.

Run interactively: `python3 -i tb_spi.py`, then e.g. `runAllTests()`.
"""
import os
import sys
import math
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.Memory import *
from punxa_atmega328p.Interrupt_Unit import *

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peer_spi import PeerSPI


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
# Baud convention every spi_tests/*.asm program is expected to configure
# the DUT with unless overridden: SPR1:0=00, SPI2X=0 (prescaler /4),
# Mode 0 (CPOL=0,CPHA=0), MSB-first (DORD=0) -- and PeerSPI below is
# pre-configured to match. A test that needs different settings should
# either reconfigure `peer` directly after prepareTest() returns it, or
# (for the common case of "the DUT's own CPOL/CPHA/DORD changes mid-run
# and the peer should just follow along") get a TEST_PEER_KWARGS entry
# with track_format=True below -- see peer_spi.py's docstring.

# Per-test PeerSPI overrides, keyed by filename. Only needed for tests
# whose DUT-side config isn't the suite's Mode-0/MSB-first default --
# most tests need nothing here. Same role as tb_usart.py's
# TEST_PEER_KWARGS.
TEST_PEER_KWARGS = {
    # Sweeps all 4 CPOL/CPHA combinations in one run. The peer's clock
    # edge interpretation must track the DUT's live SPCR bits after
    # each change, or its sample/setup edges fall out of sync with
    # what the DUT is actually doing -- see PeerSPI's track_format
    # docstring.
    'test_spi_clock_modes.asm': dict(track_format=True),
    # Sweeps DORD 0 then 1. Same tracking need as clock_modes, above.
    'test_spi_data_order.asm': dict(track_format=True),
    # Mode-fault test needs the peer wired to the DUT's own !SS input
    # (see assert_ss_dut() in peer_spi.py) -- constructed in
    # prepareTest() below whenever this filename is running.
    'test_spi_mode_fault.asm': dict(),
}

# Tests that need SS_dut_out wired up (see TEST_PEER_KWARGS comment
# above and peer_spi.py's assert_ss_dut()).
TESTS_NEEDING_SS_DUT = {'test_spi_mode_fault.asm'}


# -----------------------------------------------------------------------
# Per-test custom peer drivers, keyed by filename. Same role as
# tb_usart.py's TEST_DRIVERS: each entry is a function(peer) that
# configures peer.on_byte_received to react to a specific trigger byte
# from the DUT instead of the default echo. Called once, right after
# the peer is constructed in prepareTest().
# -----------------------------------------------------------------------
def _driver_mode_fault(peer):
    def on_byte(peer, entry):
        if entry['data'] == 0xF0:
            # Trigger byte: instead of echoing it, assert the DUT's
            # own !SS input low for a few ticks -- simulates another
            # master grabbing the bus, which SPI.py's SS_logic should
            # react to by clearing MSTR and setting SPIF.
            peer.assert_ss_dut()
            return True
        return False
    peer.on_byte_received = on_byte


TEST_DRIVERS = {
    'test_spi_mode_fault.asm': _driver_mode_fault,
}


# -----------------------------------------------------------------------
# Per-test post-run Python-side checks, keyed by filename. Same role as
# tb_usart.py's TEST_POST_CHECKS: function(peer, cpu, mem), called
# once after the main step loop finishes (and after confirming
# final_result != 255); raise an Exception to fail the test.
# -----------------------------------------------------------------------
def _check_interrupt_line_followed_flags(peer, cpu, mem):
    # test_spi_interrupt.asm can't observe the STC interrupt *line*
    # itself from inside the CPU (it can only see SPIE/SPIF, the two
    # register bits that are supposed to combine into it) -- the wire
    # is exactly the thing this check is for. `spi_stc_wire` is set as
    # a module global by prepareTest() below, the same way `peer`/
    # `cpu`/`mem` already are.
    if spi_stc_wire.get() != 0:
        raise Exception(
            f'test_spi_interrupt: STC line should have settled back to 0 by '
            f'end-of-test (SPIF was cleared before the program reached its '
            f'end: label), but read {spi_stc_wire.get()}'
        )


TEST_POST_CHECKS = {
    'test_spi_interrupt.asm': _check_interrupt_line_followed_flags,
}

TEST_STEP_LIMITS = {
    # Prescaler sweep includes the slowest divider (/128); generous
    # headroom for several back-to-back 8-bit transfers at that speed
    # plus normal CPU polling overhead.
    'test_spi_prescaler.asm': 400_000,
}


def prepareTest(file, preload=True, peer_kwargs=None):
    global hw, cpu, ins_mem, mem, spi, peer, spi_stc_wire

    if peer_kwargs is None:
        peer_kwargs = TEST_PEER_KWARGS.get(file, {})

    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    words, symbols = assemble_program(program)

    hw = py4hw.HWSystem()

    dw = 8
    aw = 16

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)
    gpio_p = punxa.MemoryInterface(hw, 'gpio', dw, 5)
    spi_p = punxa.MemoryInterface(hw, 'spi', dw, 2)   # 4 addresses, only 0x2C-0x2E used
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)

    # SPI <-> PeerSPI wires
    ss_wire = py4hw.Wire(hw, 'spi_nss_in', 1); ss_wire.put(1)   # own !SS input, idle high (no fault)
    miso_wire = py4hw.Wire(hw, 'spi_miso', 1); miso_wire.put(0)
    mosi_wire = py4hw.Wire(hw, 'spi_mosi', 1); mosi_wire.put(0)
    clk_wire = py4hw.Wire(hw, 'spi_sck', 1); clk_wire.put(0)
    spi_stc_wire = py4hw.Wire(hw, 'spi_stc_int', 1); spi_stc_wire.put(0)

    # spi_p is listed AFTER gpio_p on purpose -- see this module's
    # docstring, point 1, for why that's what makes 0x2C-0x2E resolve
    # to SPI instead of being silently NAK'd by GPIO.
    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(reg_p, 0x0, 0x20),
                          (gpio_p, 0x20, 0x20),
                          (sp_p, 0x5D, 0x02),
                          (int_unit_p, 0xFE, 0x2),
                          (spi_p, 0x2C, 0x03),
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
        # (0x20, 0x36) is the one that matters for this harness -- see
        # the module docstring above, point 3.
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x38, 0x3F), (0xFE, 0xFF)],
    )

    cpu = MulticycleCpuWrapper(actual_cpu)
    silence_debug(hw)
    cpu.prog_mosi = prog_mosi_wire
    cpu.prog_sck = prog_sck_wire
    cpu.prog_miso = prog_miso_wire
    cpu.reset_wire = reset_wire

    reg = punxa.Ram_Memory(hw, 'reg', dw, 7, reg_p)
    mem = punxa.Ram_Memory(hw, 'men', dw, 11, mem_p)
    ins_mem = punxa.Ram_Memory(hw, 'ins_men', 16, 14, ins_p)
    sp_component = StackPointer(hw, 'stack_pointer', sp_p)
    gpio = punxa.VirtualGPIO(hw, 'gpio', gpio_p)

    spi = punxa.SPI(hw, 'spi0', spi_p,
                     SS=ss_wire, MISO=miso_wire, MOSI=mosi_wire,
                     STC=spi_stc_wire, CLK=clk_wire)

    # MultiplexedBus.propagate() delivers each slave a *window-relative*
    # address (global_addr - window_start, see Bus.py) -- but SPI.py's
    # SPCR_addr_LS/SPSR_addr_LS/SPDR_addr_LS are the real, global
    # ATmega328P addresses (0x2C/0x2D/0x2E), which is exactly what's
    # needed for spi_tests/*.py's standalone harness (no Bus in
    # between, so what SPI sees IS the global address). Through this
    # particular Bus, though, SPI only ever sees local 0/1/2 for that
    # 0x2C-0x2E window -- rebase just for this instance so both usages
    # stay correct without changing SPI.py's public address contract.
    # (SPCR_addr_IO isn't touched: MemoryInterfaceHandler always
    # normalizes IN/OUT's I/O address to the equivalent SRAM address
    # -- A_6bit + 0x20 -- before it ever reaches the external bus, so
    # only the LS-form constants are ever compared against here.)
    _spi_window_start = 0x2C
    spi.SPCR_addr_LS -= _spi_window_start
    spi.SPSR_addr_LS -= _spi_window_start
    spi.SPDR_addr_LS -= _spi_window_start
    # MemoryInterfaceHandler declares memory_instype as an output port
    # but never actually calls .prepare() on it anywhere -- it stays 0
    # for every real STS/LDS/IN/OUT this CPU issues, so SPI.py's
    # instype==0 ("IO address") branch is the only one reachable
    # through this harness. Rebase it the same way so it matches too.
    spi.SPCR_addr_IO = spi.SPCR_addr_LS
    spi.SPSR_addr_IO = spi.SPSR_addr_LS
    spi.SPDR_addr_IO = spi.SPDR_addr_LS

    pk = dict(CPOL=0, CPHA=0, DORD=0, echo=True, dut=spi)
    pk.update(peer_kwargs)
    if file in TESTS_NEEDING_SS_DUT:
        pk['SS_dut_out'] = ss_wire
    # peer.MISO_out drives the DUT's MISO pin; peer.CLK_in/MOSI_in
    # sample the DUT's SCK/MOSI outputs -- crossed relative to the
    # DUT's own naming, same convention as USART0<->PeerUART.
    peer = PeerSPI(hw, 'peer', CLK_in=clk_wire, MOSI_in=mosi_wire, MISO_out=miso_wire, **pk)

    driver_setup = TEST_DRIVERS.get(file)
    if driver_setup is not None:
        driver_setup(peer)

    interrupt_module = SimpleInterruptUnit(
        hw, 'interrupt_module',
        memory=int_unit_p,
        Interrupt=interrupt_wire,
        Global_Interrupt_Enable=global_interrupt_enable_wire,
        SPI_STC=spi_stc_wire,
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

    if step_limit is None:
        step_limit = TEST_STEP_LIMITS.get(file, 100_000)
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

    post_check = TEST_POST_CHECKS.get(file)
    if post_check is not None:
        post_check(peer, cpu, mem)


# =============================================================================
# TEST SUITE CONFIGURATION & RUNNERS (same shape as tb_usart.py / tb_ISA_test_Multicycle_Rewrite.py)
# =============================================================================
ex_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'spi_tests') + os.sep
selected_prefixes = ['test_spi']


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
        print('No spi_tests/test_spi_*.asm files found.')
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
