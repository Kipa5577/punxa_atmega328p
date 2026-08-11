# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 12:44:04 2026

@author: dcr
"""
import os
import sys
import math
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.interactive_commands import *




def prepareTest(file):
    global hw
    global cpu
    global ins_mem
    global mem
    
    with open(os.path.join(ex_dir, file), 'r') as f:
        program = f.read()

    # Smart Detection: If the file doesn't define the Reset Vector, it's a legacy test
    inject_vectors = (file == 'test_ctrflow_RETI.asm')   

    words, symbols = assemble_program(program)
    
    hw = py4hw.HWSystem()
    
    dw = 8 
    aw = 16
    
    # --- Interrupts ---
    timer0_ovf_wire = py4hw.Wire(hw, 'timer0_ovf_wire', 1)
    cpu_interrupt_wire = py4hw.Wire(hw, 'cpu_interrupt_wire', 1)
    global_interrupt_enable_wire = py4hw.Wire(hw, 'global_interrupt_enable_wire', 1)

    # --- Memory Interfaces ----
    # Size window is 0x30 (48 bytes), so an address width of 6 bits (2^6 = 64) is perfect!
    timer_p = punxa.MemoryInterface(hw, 'timer_p', dw, 6)
    int_unit_p = punxa.MemoryInterface(hw, 'int_unit_p', dw, 1)

    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)

    gpio_p = punxa.MemoryInterface(hw, 'gpio', dw, 5)       # 0x20 to 0x3F
    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)         # General Registers
    usart_p = punxa.MemoryInterface(hw, 'usart', dw, 3)     
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)        

    # --- Clean Bus Configuration (No overlaps) ---
    punxa.MultiplexedBus(hw, 'bus', data_p, 
                        [(reg_p, 0x0, 0x20),
                         (gpio_p, 0x20, 0x20),        # 0x20 -> 0x3F
                         (timer_p, 0x40, 0x30),       # 0x40 -> 0x6F (Captures TIMSK0 at 0x6E!)
                         (int_unit_p, 0xFE, 0x2),     # 0xFE -> 0xFF
                         (usart_p, 0xC0), 
                         (mem_p, 0x100)])
    
    # --- Instantiate the CPU ---
    cpu = punxa.SingleCycleATmega328P(hw, 'cpu', ins_p, data_p, 0, cpu_interrupt_wire, global_interrupt_enable_wire)

    # --- Instantiate core memory blocks ---
    reg = punxa.Ram_Memory(hw, 'reg', dw, 7, reg_p)                 
    mem = punxa.Ram_Memory(hw, 'men', dw, 11, mem_p)                
    ins_mem = punxa.Ram_Memory(hw, 'ins_men', 16, 14, ins_p)        
    usart = punxa.VirtualUSART(hw, 'usart', usart_p)
    gpio = punxa.VirtualGPIO(hw, 'gpio', gpio_p)
    
    # ----------------------------------------------------------------
    # --- NEW: Instantiate your custom modules so they exist in HW ---
    # ----------------------------------------------------------------
    timer0_module = punxa.SimpleTimer(hw, 'timer0_module', timer_p, TIMER0_OVF=timer0_ovf_wire)
    
    interrupt_module = punxa.SimpleInterruptUnit(
        hw, 'interrupt_module', 
        memory=int_unit_p, 
        Interrupt=cpu_interrupt_wire, 
        Global_Interrupt_Enable=global_interrupt_enable_wire,
        TIMER0_OVF=timer0_ovf_wire
    )
    # ----------------------------------------------------------------

    watch = []
    watch.extend(py4hw.debug.getInterfaceWires(ins_p))
    watch.extend(py4hw.debug.getInterfaceWires(data_p))
    watch.extend(py4hw.debug.getInterfaceWires(reg_p))
    watch.append(timer0_ovf_wire)
    watch.append(cpu_interrupt_wire)
    
    # Load program into memory
    for i, b in enumerate(words):
        ins_mem.writeWord(i, b)
        
    import punxa_atmega328p.interactive_commands as ci
    ci._ci_hw = hw
    ci._ci_cpu = cpu

    return hw, cpu, ins_mem, mem, symbols
    
def runTest(file):
    
    hw, cpu, ins_mem, mem , symbols = prepareTest(file)
    
    step_limit = 1000
    step_count = 0
    
    while (cpu.pc != symbols['end']):
        step()
        step_count += 1 
        if (step_count > step_limit):
            raise Exception('Step count > limit')
    
    test_case = mem.readWord(symbols['test_case']-0x100)
    final_result = mem.readWord(symbols['final_result']-0x100)
    
    print('FINAL RESULT:', final_result, '\tTest case:', test_case)
    
    if (final_result == 255):
        raise Exception(f'Failed in test case {test_case}')


ex_dir = 'isa/'
selected_prefixes = ['test_arith', 'test_bitmap', 'test_branch', 'test_logic', 'test_ctrflow', 'test_data', 'test_mcu']

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