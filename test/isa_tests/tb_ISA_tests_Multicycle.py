# -*- coding: utf-8 -*-
"""
ISA Tests for ATmega328P Multicycle Processor
"""
import os
import sys
import math
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
class MulticycleCpuWrapper:
    """
    Wraps the multicycleProcessor to provide the interface expected by 
    punxa_atmega328p.interactive_commands.
    """
    def __init__(self, cpu):
        self._cpu = cpu

    @property
    def pc(self):
        # Accesses the PC inside the RomHandler submodule
        return self._cpu.rom.PC

    @pc.setter
    def pc(self, value):
        self._cpu.rom.PC = value

    @property
    def sreg(self):
        # Explicit property for SREG to allow direct access by regs() command
        return self._cpu.sreg

    def getCSR(self, *args, **kwargs):
        # Extract the CSR index requested by the interactive tool
        csr_requested = args[0] if args else None
        
        # CSR_INSTRET is defined in your interactive_commands/csr.py
        if csr_requested == CSR_INSTRET:
            # Navigate to the MainFSM inside the ControlBox
            # If this throws an AttributeError, check if your ControlBox 
            # uses a different name than 'fsm'
            return self._cpu.control.main_fsm.instret_count
            
        # If the requested CSR is not the retired instruction count, 
        # return the SREG value (as per your existing logic)
        return self._cpu.sreg.SREG

    def __getattr__(self, name):
        # Fallback for any other attributes (e.g., .mem_if, .memory)
        return getattr(self._cpu, name)


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
    
    # Memory Map
    # 0x0000 - 0x001F   GP Registers r0-r31
    # 0x0020 - 0x003F   GPIO
    # 0x0040 - 0x006F   Timer0 (TCCR0A/B, TCNT0, TIFR0, TIMSK0 @ 0x6E)
    # 0x005D - 0x005E   SP (intercepted internally by MemoryInterfaceHandler,
    #                    the bus-mapped sp_p/StackPointer below never sees it)
    # 0x005F            SREG (also intercepted internally)
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
    
    # Instantiate Multicycle Processor
    actual_cpu = punxa.multicycleProcessor(
        parent=hw, 
        name='cpu', 
        Interrupt=interrupt_wire, 
        Interrupt_Enable=global_interrupt_enable_wire,
        ins_mem=ins_p, 
        memory=data_p, 
        reset=reset_wire, 
        reset_address=0,
        # MemoryInterfaceHandler intercepts every address in [0x0020,0x0100)
        # internally by default (SP/SREG + a catch-all scratch space), so
        # without this, gpio_p/timer_p/int_unit_p below would never
        # actually be reached even though they're on the bus.
        Bus_Passthrough_Ranges=[(0x20, 0x36), (0x38, 0x3F), (0x40, 0x6F), (0xFE, 0xFF)],
    )
    
    # --- WRAP THE CPU ---
    # This makes 'cpu.pc' and 'cpu.getCSR()' work seamlessly with step()
    cpu = MulticycleCpuWrapper(actual_cpu)
    
    reg = punxa.Ram_Memory(hw, 'reg', dw, 7, reg_p)                 # 32 B
    mem = punxa.Ram_Memory(hw, 'men', dw, 11, mem_p)                # 2048 B
    ins_mem = punxa.Ram_Memory(hw, 'ins_men', 16, 14, ins_p)        # 16 k words (of 16 bits) 
    usart = punxa.VirtualUSART(hw, 'usart', usart_p)
    gpio = punxa.VirtualGPIO(hw, 'gpio', gpio_p)
    sp_component = StackPointer(hw, 'stack_pointer', sp_p)

    # --- Interrupt peripherals ---
    # NOTE: sp_component above (0x5D/0x5E) is likewise dead on this bus --
    # MemoryInterfaceHandler intercepts SP internally before any
    # Bus_Passthrough_Ranges check ever runs, same as SREG -- pre-existing
    # in this testbench, unrelated to the interrupt wiring added here.
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
    for i, b in enumerate(words):
        ins_mem.writeWord(i, b)
        
    #py4hw.gui.Workbench(hw)
    
    import punxa_atmega328p.interactive_commands as ci
    
    ci._ci_hw = hw
    ci._ci_cpu = cpu  # Pass the wrapped CPU to the interactive shell

    return hw, cpu, ins_mem, mem, symbols
    
def runTest(file):
    
    hw, cpu, ins_mem, mem , symbols = prepareTest(file)
    
    # Multicycle processor takes multiple clock cycles per instruction.
    # There is a generous overall limit to catch ACTUAL infinite loops.
    step_limit = 17000
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
selected_prefixes = ['test_arith', 'test_bitmap', 'test_logic', 'test_ctrflow', 'test_data', 'test_mcu']

def computeAllTests():
    files = os.listdir(ex_dir)
    ret = {}

    files = [name for name in files if  any(name.startswith(prefix) for prefix in selected_prefixes)]
    #files = [name for name in files]

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
        
if __name__ == "__main__":
    print(sys.argv)

    if (len(sys.argv) > 1):
         if (sys.argv[1] == '-c'):
             eval(sys.argv[2])
             os._exit(0)