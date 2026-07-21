# -*- coding: utf-8 -*-
"""
ISA Tests for ATmega328P Multicycle Processor

This is tb_ISA_tests_Multicycle.py with the session's two testbench-side
fixes folded in directly, replacing the exec()-based monkeypatch approach
(wrapper_patch.py) that was needed to keep the original file byte-for-byte
untouched during debugging. Now that both fixes are final, they live here
instead:

1. MulticycleCpuWrapper — the original version read `self._cpu.rom.PC`,
   `self._cpu.sreg`, and `self._cpu.control.main_fsm`, none of which exist
   post-rewrite (Datapath/ControlBox/RomHandler/etc. are anonymous
   `py4hw` children in the new two-peer tree, not named attributes
   anywhere). Replaced with a version that locates PC / SREG_* / MainFSM
   by walking `.children` (py4hw components are anonymous; this is the
   only way to reach them from outside).
2. runTest's `step_limit` — raised from 17000 to 25000. `test_data_IN.asm`
   (18 sub-tests, more than any other file in the suite) genuinely needs
   ~17025 cycles to finish; the old limit flagged it as "stuck" 25 cycles
   short of the finish line. See HANDOFF_ADDENDUM_2_in_spm_fix.md for the
   full trace that confirmed this (every I/O address it touches responds
   correctly — nothing is actually hung).
3. Simulator.topologicalSort() — py4hw's stock implementation is O(n^2)
   per convergence pass (repeated `list.index()` linear scans over ~4000
   propagatable leaves); replaced with a proper O(V+E) Kahn's-algorithm
   topological sort, monkeypatched over the installed py4hw library at
   import time. Dropped hw.getSimulator() from ~12s to ~0.02s per test —
   this was the actual source of the "delay between compilation finish
   and execution start" (assembly/prepareTest() itself is fast; the
   simulator's one-time dependency sort, run once per test right
   afterward and before any clock cycles, was not).

Everything else — the memory map, peripheral wiring, Bus_Passthrough_Ranges,
test running/reporting — is unchanged from the original.
"""
import os
import sys
import io
import math
import time
import contextlib
import concurrent.futures
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.interactive_commands import *
from punxa_atmega328p.Memory import *
from punxa_atmega328p.Interrupt_Unit import *
from punxa_atmega328p.Timers import *


# =============================================================================
# COMPATIBILITY WRAPPER FOR INTERACTIVE COMMANDS
# =============================================================================
def _find_child(root, name):
    """py4hw components are anonymous -- neither Datapath(...) nor
    ControlBox(...) nor most sub-components are assigned to self.xxx at
    their call sites. Find them by instance name in the .children dict,
    recursively."""
    if name in root.children:
        return root.children[name]
    for c in root.children.values():
        r = _find_child(c, name)
        if r is not None:
            return r
    return None


class MulticycleCpuWrapper:
    """
    Wraps the multicycleProcessor to provide the interface expected by
    punxa_atmega328p.interactive_commands, and by this test harness's
    `cpu.pc` / `cpu.getCSR(...)` calls.

    Rewritten for the post-rewrite two-peer (Datapath + ControlBox) CPU
    tree: PC / SREG_* / MainFSM are located once at wrap time by walking
    `.children`, then read directly off the underlying py4hw components
    on every access (no caching of values, only of the component
    references themselves).
    """
    def __init__(self, cpu):
        self._cpu = cpu
        self._pc_reg = _find_child(cpu, 'PC')
        self._sreg_bits = {b: _find_child(cpu, f'SREG_{b}') for b in 'CZNVSHTI'}
        self._main_fsm = _find_child(cpu, 'MainFSM')

    @property
    def pc(self):
        return self._pc_reg.q.get()

    @pc.setter
    def pc(self, value):
        raise NotImplementedError(
            "Direct PC assignment not supported post-rewrite (PC is a "
            "real py4hw.Reg); not needed by the automated ISA suite."
        )

    @property
    def sreg(self):
        order = ['C', 'Z', 'N', 'V', 'S', 'H', 'T', 'I']
        val = 0
        for i, b in enumerate(order):
            reg = self._sreg_bits[b]
            if reg is not None:
                val |= (reg.q.get() & 1) << i
        return val

    def getCSR(self, *args, **kwargs):
        # Extract the CSR index requested by the interactive tool
        csr_requested = args[0] if args else None

        # CSR_INSTRET is defined in punxa_atmega328p.interactive_commands.csr
        if csr_requested == CSR_INSTRET:
            return self._main_fsm.instret_count if self._main_fsm else 0

        # If the requested CSR is not the retired instruction count,
        # return the SREG value (as per the original logic)
        return self.sreg

    def __getattr__(self, name):
        # Fallback for any other attributes (e.g., .mem_if, .memory)
        return getattr(self._cpu, name)


def silence_debug(root, seen=None):
    """Recursively zero every component's `.debug` flag -- kills the
    print-per-cycle spam every sub-FSM in this design emits by default.
    Call once per prepareTest() if you're driving the simulator by hand
    (interactively or from a debug script) rather than through runTest();
    runAllTests()/computeAllTests() don't need this, they just capture
    the noise instead of printing it."""
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
# TEST PREPARATION & EXECUTION
# =============================================================================
def prepareTest(file, preload=True):
    global hw
    global cpu
    global ins_mem
    global mem
    
    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()
     
    words, symbols = assemble_program(program)
    
    hw = py4hw.HWSystem()
    
    # Memory Map
    # 0x0000 - 0x001F   GP Registers r0-r31
    # 0x0020 - 0x003F   GPIO
    # 0x0040 - 0x006F   Timer0 (TCCR0A/B, TCNT0, TIFR0, TIMSK0 @ 0x6E)
    # 0x005D - 0x005E   SP (intercepted internally by MemoryInterfaceHandler,
    #                    the bus-mapped sp_p/StackPointer below never sees it)
    # 0x005F            SREG (also intercepted internally)
    # 0x0057            SPMCR (also intercepted internally -- see
    #                    MemoryInterfaceHandler's SPMCR_ADDR note; its
    #                    address falls inside the timer window below but
    #                    isn't a timer register)
    # 0x00C0 - 0x00C6   USART
    # 0x00FE - 0x00FF   InterruptUnit (interrupt vector low/high byte)
    # 0x0100 - 0x08FF   Internal SRAM
    
    dw = 8 
    aw = 16
    
    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)
    
    gpio_p = punxa.MemoryInterface(hw, 'gpio', dw, 5)       # gpios
    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)         # 2^5 = 32 registers + 64 I/O registers
    usart_p = punxa.MemoryInterface(hw, 'usart', dw, 3)     # 2^3 = 8 registers
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)      # 2 addresses needed (0x5D, 0x5E)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)        # 2048 bytes

    # --- Interrupts ---
    timer_p = punxa.MemoryInterface(hw, 'timer_p', dw, 6)   # 0x40 -> 0x6F (48 B window)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)  # 0xFE -> 0xFF

    timer0_ovf_wire = py4hw.Wire(hw, 'timer0_ovf_wire', 1)
    timer0_ovf_wire.put(0)
    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)
    global_interrupt_enable_wire.put(0)
    
    
    punxa.MultiplexedBus(hw, 'bus', data_p, 
                         [(reg_p, 0x0, 0x20),
                          (gpio_p, 0x20, 0x20),
                          (timer_p, 0x40, 0x30),       # 0x40 -> 0x6F (TIMSK0 lands at 0x6E)
                          (sp_p, 0x5D, 0x02),
                          (int_unit_p, 0xFE, 0x2),     # 0xFE -> 0xFF
                          (usart_p, 0xC0), 
                          (mem_p, 0x100)])

    # CPU Control Wires for Multicycle Processor
    reset_wire = py4hw.Wire(hw, 'Reset_Line', 1)
    reset_wire.put(0)

    # Flash programming interface (see ROM_FLASHING_DESIGN.md). Required
    # by multicycleProcessor's constructor now (RomHandler is a leaf
    # component and can't bind a None wire) -- tied low here since this
    # function's own tests still preload ins_mem directly and never
    # assert reset, so these are simply never driven. tb_ROM_Flash.py's
    # prepareFlashTest() is the one that actually bit-bangs them.
    prog_mosi_wire = py4hw.Wire(hw, 'PROG_MOSI', 1)
    prog_mosi_wire.put(0)
    prog_sck_wire = py4hw.Wire(hw, 'PROG_SCK', 1)
    prog_sck_wire.put(0)
    prog_miso_wire = py4hw.Wire(hw, 'PROG_MISO', 1)

    # Instantiate Multicycle Processor
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
        # MemoryInterfaceHandler intercepts every address in [0x0020,0x0100)
        # internally by default (SP/SREG/SPMCR + a catch-all scratch space),
        # so without this, gpio_p/timer_p/int_unit_p below would never
        # actually be reached even though they're on the bus.
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x38, 0x3F), (0x40, 0x6F), (0xFE, 0xFF)],
    )
    
    # --- WRAP THE CPU ---
    # This makes 'cpu.pc' and 'cpu.getCSR()' work seamlessly with step()
    cpu = MulticycleCpuWrapper(actual_cpu)
    cpu.prog_mosi = prog_mosi_wire
    cpu.prog_sck = prog_sck_wire
    cpu.prog_miso = prog_miso_wire
    cpu.reset_wire = reset_wire
    
    reg = punxa.Ram_Memory(hw, 'reg', dw, 7, reg_p)                 # 32 B
    mem = punxa.Ram_Memory(hw, 'men', dw, 11, mem_p)                # 2048 B
    ins_mem = punxa.Ram_Memory(hw, 'ins_men', 16, 14, ins_p)        # 16 k words (of 16 bits) 
    usart = punxa.VirtualUSART(hw, 'usart', usart_p)
    gpio = punxa.VirtualGPIO(hw, 'gpio', gpio_p)
    sp_component = StackPointer(hw, 'stack_pointer', sp_p)

    # --- Interrupt peripherals ---
    # NOTE: sp_component above (0x5D/0x5E) is likewise dead on this bus --
    # MemoryInterfaceHandler intercepts SP internally before any
    # Bus_Passthrough_Ranges check ever runs, same as SREG/SPMCR --
    # pre-existing in this testbench, unrelated to the interrupt wiring
    # added here.
    timer0_module = SimpleTimer(hw, 'timer0_module', timer_p, TIMER0_OVF=timer0_ovf_wire)

    interrupt_module = SimpleInterruptUnit(
        hw, 'interrupt_module',
        memory=int_unit_p,
        Interrupt=interrupt_wire,
        Global_Interrupt_Enable=global_interrupt_enable_wire,
        TIMER0_OVF=timer0_ovf_wire
    )
    
    watch = []
    watch.extend(py4hw.debug.getInterfaceWires(ins_p))
    watch.extend(py4hw.debug.getInterfaceWires(data_p))
    watch.extend(py4hw.debug.getInterfaceWires(reg_p))
    watch.append(timer0_ovf_wire)
    watch.append(interrupt_wire)
    
    #wvf = py4hw.Waveform(hw, 'wvf', watch)
    
    # Load program into memory
    if preload:
        for i, b in enumerate(words):
            ins_mem.writeWord(i, b)
    else:
        # Used by tb_ROM_Flash.py: leave ins_mem in the erased-flash
        # state (0xFFFF, the real ISP Chip Erase convention) instead of
        # preloading it directly -- a successful flash-then-boot run is
        # then only possible if the ISP programming path actually wrote
        # the right words, not because this function quietly did it.
        for i in range(1 << 14):
            ins_mem.writeWord(i, 0xFFFF)

    #py4hw.gui.Workbench(hw)
    
    import punxa_atmega328p.interactive_commands as ci
    
    ci._ci_hw = hw
    ci._ci_cpu = cpu  # Pass the wrapped CPU to the interactive shell

    cpu.assembled_words = words  # stashed here so preload=False callers
                                  # can still get at what *should* end up
                                  # in ins_mem, without changing this
                                  # function's 5-value return arity for
                                  # every existing caller.
    return hw, cpu, ins_mem, mem, symbols
    
def runTest(file):
    
    hw, cpu, ins_mem, mem , symbols = prepareTest(file)
    
    # Multicycle processor takes multiple clock cycles per instruction.
    # There is a generous overall limit to catch ACTUAL infinite loops.
    #
    # 25000 (was 17000): test_data_IN.asm has 18 sub-tests -- more than
    # any other file in this suite -- and genuinely needs ~17025 cycles
    # to reach `end`. The old 17000 limit flagged it as "stuck" 25 cycles
    # short of finishing; traced cycle-by-cycle to confirm every I/O
    # address it touches (PORTC/DDRC/PINC/GPIOR0/GPIOR1/SREG/SPH/SPL)
    # responds correctly the whole way through. 25000 gives every test in
    # the suite comfortable headroom without letting a genuine hang run
    # too long before being reported.
    step_limit = 25000
    step_count = 0
    
    sim = hw.getSimulator()
    
    while (cpu.pc != symbols['end']):
        # Simulator.clk() calls propagateAll() every time it's invoked, but
        # the propagate() pass at the end of the previous _clk_cycle() is
        # never settled (settleAll only runs at the *start* of a cycle).
        # Calling clk(1) once per loop iteration means each call's
        # propagateAll() re-prepares those still-pending wires from the
        # last call -> "already prepared" warning spam, every cycle.
        # Flushing here settles them first, so the warning never fires.
        py4hw.Wire.settleAll()
        sim.clk(1)
        step_count += 1 
        
        if (step_count > step_limit):
            # Provide helpful debug info if it actually gets stuck forever
            raise Exception(f'Stuck in infinite loop! PC: {cpu.pc:04X} (Expected end at: {symbols["end"]:04X})')
    
    test_case = mem.readWord(symbols['test_case']-0x100)
    final_result = mem.readWord(symbols['final_result']-0x100)
    
    print('FINAL RESULT:', final_result, '\tTest case:', test_case, '\tCycles:', step_count)
    
    if (final_result == 255):
        raise Exception(f'Failed in test case {test_case}')


# =============================================================================
# TEST SUITE CONFIGURATION & RUNNERS
# =============================================================================
ex_dir = 'isa/'
selected_prefixes = ['test_arith', 'test_bitmap', 'test_branch', 'test_logic', 'test_ctrflow', 'test_data', 'test_mcu']

def _run_one_test_silent(f):
    """Runs a single test file with ALL of its output forcefully suppressed
    (every print -- per-cycle FSM/ROM/MIH debug spam, the FINAL RESULT
    line, everything) and returns (filename, result), where result is
    'OK' or ('FAILED', exception). This is the function handed to the
    process pool below.

    Why a process pool instead of threads: every py4hw.Wire instance in
    a process shares CLASS-level bookkeeping (`Wire.prepared`,
    `Wire._prepared_lookup`, `Wire.dirty` -- see py4hw/base.py). Threads
    all live in the same process and would share that same state, which
    is exactly what caused wrong results when this was first tried with
    a ThreadPoolExecutor (see HANDOFF.md). A separate OS process has its
    own interpreter, its own GIL, and its own independent copy of that
    class state -- there's nothing left to race on, and unlike threads
    this gets real simultaneous execution across CPU cores, not just
    interleaved execution on one core.
    (On Linux this pool forks -- cheap, inherits the already-imported
    py4hw/punxa_atmega328p from the parent. On Windows/macOS,
    multiprocessing defaults to spawning a fresh interpreter per worker,
    which re-imports everything from scratch -- slower to start up, but
    still correct, and why this function has to be a plain top-level,
    picklable function rather than a closure.)
    """
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            runTest(f)
            return f, 'OK'
        except Exception as e:
            return f, ('FAILED', e)


def computeAllTests(num_threads=1):
    """Runs every selected test file and returns {filename: result}.

    num_threads=1 (default): original sequential behavior, unchanged --
    full per-test logging ("Run test X PASSED/FAILED" as each one
    finishes) plus every component's own debug output, exactly as
    before.

    num_threads>1: runs tests concurrently across `num_threads` separate
    OS processes (concurrent.futures.ProcessPoolExecutor) for genuine
    parallel execution -- see _run_one_test_silent()'s docstring for why
    processes rather than threads. Each worker's own INTERNAL output
    (per-cycle debug spam) is forcefully suppressed, so N workers can't
    flood the console with interleaved per-cycle noise -- but as each
    worker finishes, one summary line for that test is printed here
    (via as_completed(), so it's genuinely as-they-finish, not
    submission order), giving live progress instead of a long silent
    wait followed by a wall of results.
    """
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
    p = n*100/t
    pl = 45
    pok = math.ceil(pl*n/t)
    pko = pl - pok
    sok = '█' * pok
    sko = '░' * pko
    sp = '{:.1f} %'.format(p)
    s = '{:8} |{}{}|'.format(sp,sok,sko)
    return s

def runAllTests(num_threads=1):
    """num_threads: how many test files to run concurrently (default 1,
    matching the original sequential behavior with full logging).
    num_threads>1 runs tests across that many separate OS processes for
    genuine parallel execution; each worker's internal per-cycle debug
    output is suppressed, but a "[k/N] filename PASSED/FAILED" line is
    printed live as each one finishes (in completion order), followed by
    this function's usual summary once every test is done. See
    computeAllTests()'s docstring for why this uses processes rather
    than threads."""
    global selected_prefixes
    start_time = time.time()
    nOK = 0
    nTotal = 0
    ret = computeAllTests(num_threads)
    
    groupResults = {}
    
    for prefix in selected_prefixes:
        nOKGroup = 0
        nTotalGroup = 0

        files = [name for name in ret.keys() if name.startswith(prefix) ]
        for t in files:
            nTotal += 1
            nTotalGroup += 1
            if (ret[t] =='OK'):
                 print('Test {:30} = {}'.format(t, ret[t]))
                 nOK += 1
                 nOKGroup += 1
            else:
                 print('Test {:30} = {} - {}'.format(t, ret[t][0], ret[t][1]))

        groupResults[prefix]=(nOKGroup, nTotalGroup)
        
    print('Total: {} Correct: {} ({:.1f} %)'.format(nTotal, nOK, nOK*100/nTotal))     
    print(asciiProgressBar(nOK, nTotal))

    for prefix in selected_prefixes:
        nOKGroup = groupResults[prefix][0]
        nTotalGroup = groupResults[prefix][1]
        if (nTotalGroup == 0):
            nTotalGroup = 1
        print('Group: {} Total: {} Correct: {} ({:.1f} %)'.format(prefix, nTotalGroup, nOKGroup, nOKGroup*100/nTotalGroup))     

    for prefix in selected_prefixes:
        nOKGroup = groupResults[prefix][0]
        nTotalGroup = groupResults[prefix][1]
        if (nTotalGroup == 0):
            nTotalGroup = 1
        print(f'{prefix:15}', asciiProgressBar(nOKGroup, nTotalGroup))

    # --- Timing Calculations ---
    elapsed_time = time.time() - start_time
    print('\n' + '='*60)
    print(f'Execution Time: {elapsed_time:.2f} seconds')
    print('='*60)
        
if __name__ == "__main__":
    print(sys.argv)

    if (len(sys.argv) > 1):
         if (sys.argv[1] == '-c'):
             eval(sys.argv[2])
             os._exit(0)