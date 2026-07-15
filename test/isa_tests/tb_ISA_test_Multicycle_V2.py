# -*- coding: utf-8 -*-
"""
ISA Tests for the ATmega328P Multicycle Processor (V2)

Adapted from the original ISA test bench to target
`punxa.MultyCycleATmega328P_V2` (Multicycle_processor.py) instead of the
older `punxa.multicycleProcessor`.

Key differences from the reference test bench this was adapted from:

  * V2's register file lives INSIDE the CPU (`cpu.reg`, a plain Python list),
    not on the external data bus. LD/ST/LDS/STS whose effective address is
    0-31 are resolved internally by the CPU, so there is no `reg_p` bus
    component anymore -- it has simply been removed from the memory map.
  * V2 exposes `pc`, `reg` and `SREG` directly as plain attributes (not
    nested under `.rom`, `.sreg`, `.control.main_fsm`, etc.), so no
    compatibility wrapper class is required: the CPU object can be handed
    straight to `runTest()` and to the interactive shell.
  * `getCSR(CSR_INSTRET)` isn't implemented by V2, so instruction-retired
    counts aren't available via that path. The test bench instead reports
    raw clock-cycle counts (`step_count`), which is what's actually being
    limited/measured anyway.
"""
import os
import sys
import math
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.interactive_commands import *
from punxa_atmega328p.Memory import *


# =============================================================================
# TEST PREPARATION & EXECUTION
# =============================================================================
def prepareTest(file):
    global hw
    global cpu
    global ins_mem
    global mem

    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    words, symbols = assemble_program(program)

    hw = py4hw.HWSystem()

    # --- Memory Map ---
    # 0x0000 - 0x001F   GP Registers r0-r31  -> internal to the CPU (cpu.reg),
    #                   NOT memory-mapped. LD/LDS/ST/STS targeting this range
    #                   are serviced inside the CPU itself.
    # 0x0020 - 0x003F   GPIO / I/O registers
    # 0x005D - 0x005E   Stack Pointer (SPL/SPH)
    # 0x00C0 - 0x00C6   USART registers
    # 0x0100 - 0x08FF   Internal SRAM

    dw = 8
    aw = 16

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    gpio_p = punxa.MemoryInterface(hw, 'gpio', dw, 5)       # gpios
    usart_p = punxa.MemoryInterface(hw, 'usart', dw, 3)     # 2^3 = 8 registers
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)      # 2 addresses needed (0x5D, 0x5E)
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)        # 2048 bytes

    # No reg_p entry here anymore - the register file no longer lives on the
    # bus for V2; it's serviced internally by the CPU.
    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(gpio_p, 0x20, 0x20),
                          (sp_p, 0x5D, 0x02),
                          (usart_p, 0xC0),
                          (mem_p, 0x100)])

    # CPU Control Wires for Multicycle Processor
    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)

    reset_wire = py4hw.Wire(hw, 'Reset_Line', 1)
    reset_wire.put(0)

    # --- Instantiate Multicycle Processor V2 ---
    # Register file is internal to the CPU (cpu.reg); LD/ST/LDS/STS
    # instructions whose effective address falls in 0-31 are resolved
    # against it directly by the CPU instead of issuing a bus transaction.
    cpu = punxa.MultyCycleATmega328P_V2(
        parent=hw,
        name='cpu',
        ins_mem=ins_p,
        memory=data_p,
        reset_address=0,
        Interrupt=interrupt_wire,
        reset=reset_wire,
    )

    # No wrapper needed: V2 already exposes .pc, .reg and .SREG directly.

    reg = None  # kept for symmetry with reference test bench; unused now
    mem = punxa.Ram_Memory(hw, 'men', dw, 11, mem_p)                # 2048 B
    ins_mem = punxa.Ram_Memory(hw, 'ins_men', 16, 14, ins_p)        # 16 k words (16-bit)
    usart = punxa.VirtualUSART(hw, 'usart', usart_p)
    gpio = punxa.VirtualGPIO(hw, 'gpio', gpio_p)
    sp_component = StackPointer(hw, 'stack_pointer', sp_p)

    watch = []
    watch.extend(py4hw.debug.getInterfaceWires(ins_p))
    watch.extend(py4hw.debug.getInterfaceWires(data_p))

    #wvf = py4hw.Waveform(hw, 'wvf', watch)

    # Load program into memory
    for i, b in enumerate(words):
        ins_mem.writeWord(i, b)

    #py4hw.gui.Workbench(hw)

    import punxa_atmega328p.interactive_commands as ci

    ci._ci_hw = hw
    ci._ci_cpu = cpu

    return hw, cpu, ins_mem, mem, symbols


def runTest(file):

    hw, cpu, ins_mem, mem, symbols = prepareTest(file)

    # Multicycle processor takes multiple clock cycles per instruction.
    # Use a generous overall limit to catch ACTUAL infinite loops.
    step_limit = 1000
    step_count = 0

    while (cpu.pc != symbols['end']):
        hw.getSimulator().clk(1)
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
selected_prefixes = ['test_arith', 'test_bitmap', 'test_logic', 'test_ctrflow', 'test_data', 'test_mcu']

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
    p = n*100/t
    pl = 45
    pok = math.ceil(pl*n/t)
    pko = pl - pok
    sok = '█' * pok
    sko = '░' * pko
    sp = '{:.1f} %'.format(p)
    s = '{:8} |{}{}|'.format(sp,sok,sko)
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

if __name__ == "__main__":
    print(sys.argv)

    if (len(sys.argv) > 1):
        if (sys.argv[1] == '-c'):
            eval(sys.argv[2])
            os._exit(0)