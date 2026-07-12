# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 11:33:21 2026

@author: dcr
"""

from .csr import *
import time

_ci_hw = None
_ci_cpu = None

# Internal state for the temporal breakpoint
_temporal_breakpoint = None

def list_commands():
    print('punxa interactive commands:')
    #print('  loadProgram - load a program (elf) in memory')
    #print('  checkpoint  - save the system state in a file')
    #print('  restore     - restore the system state from a file')
    print('  run         - run the system for a number of clock cycles')
    print('  step        - run an instruction step')
    print('  tbreak      - set a temporal breakpoint (PC address)')
    print('  go          - run until the temporal breakpoint is hit')
    print('  regs        - display the core registers of the processor')
    print('  reportCSR   - display the content of CSRs')
    print('  console     - display the content of the console')
    #print('  stack       - display the stack from [current] thread')
    print('  dump        - dump (hex) the content of data memory locations')

def step(steps = 1):
    sim = _ci_hw.getSimulator()
    sim.do_run = True
    count = 0
    last_instret = _ci_cpu.getCSR(CSR_INSTRET)
    inst_to_stop = last_instret + steps
    
    if (steps >= 100):
        t0 = time.time()
        clk0 = sim.total_clks        
        
    while (_ci_cpu.getCSR(CSR_INSTRET) < inst_to_stop and sim.do_run == True ):
        sim.clk(1)
        
        cur_instret = _ci_cpu.getCSR(CSR_INSTRET)
        if (cur_instret == last_instret):
            count += 1
            if (count > 100):
                raise Exception('Too many cycles waiting to complete instruction')
        else:
            last_instret = cur_instret
            count = 0
                    
    if (steps >= 100):
        tf = time.time()
        clkf = sim.total_clks
        
        if (tf != t0):    
            freq = (clkf-clk0)/(tf-t0)
        else:
            freq = '?'
        print('clks: {} time: {} simulation freq: {}'.format(clkf-clk0, tf-t0, freq))

def run(cycles = 1):
    """Runs the simulation for a specific number of CLOCK CYCLES (not instructions)."""
    sim = _ci_hw.getSimulator()
    sim.do_run = True
    sim.clk(cycles)
    print(f"Executed {cycles} clock cycles. Total clks: {sim.total_clks}")

def tbreak(pc_addr):
    """Sets a temporal breakpoint at a specific Program Counter address."""
    global _temporal_breakpoint
    _temporal_breakpoint = pc_addr
    print(f"Temporal breakpoint set at PC = 0x{pc_addr:04X}")

def go(max_cycles=10000):
    """Runs the processor until the PC matches the temporal breakpoint."""
    global _temporal_breakpoint
    if _temporal_breakpoint is None:
        print("No temporal breakpoint set. Use tbreak(address) first.")
        return
        
    sim = _ci_hw.getSimulator()
    sim.do_run = True
    count = 0
    
    print(f"Running until PC hits 0x{_temporal_breakpoint:04X}...")
    while _ci_cpu.pc != _temporal_breakpoint and sim.do_run == True:
        sim.clk(1)
        count += 1
        if count >= max_cycles:
            print(f"Stopped: Reached maximum cycle limit ({max_cycles}) without hitting breakpoint.")
            return

    print(f"Breakpoint hit! Stopped at PC = 0x{_ci_cpu.pc:04X} after {count} clock cycles.")
    _temporal_breakpoint = None  # Clear breakpoint after hitting it

def regs():
    """Displays the core state (PC, Status Register, X, Y, Z, and Stack Pointer)."""
    pc = _ci_cpu.pc
    sreg = _ci_cpu.sreg.SREG
    
    print("--- Core Registers ---")
    print(f"PC:   0x{pc:04X}")
    
    # SREG breakdown (I T H S V N Z C)
    c = (sreg >> 0) & 1
    z = (sreg >> 1) & 1
    n = (sreg >> 2) & 1
    v = (sreg >> 3) & 1
    s = (sreg >> 4) & 1
    h = (sreg >> 5) & 1
    t = (sreg >> 6) & 1
    i = (sreg >> 7) & 1
    print(f"SREG: 0x{sreg:02X} [I:{i} T:{t} H:{h} S:{s} V:{v} N:{n} Z:{z} C:{c}]")
    
    # Try fetching pointers from MemoryInterfaceHandler
    try:
        sp = _ci_cpu.mem_if.getSP()
        x = _ci_cpu.mem_if.getX()
        y = _ci_cpu.mem_if.getY()
        z_ptr = _ci_cpu.mem_if.getZ()
        print(f"SP:   0x{sp:04X}")
        print(f"X:    0x{x:04X}")
        print(f"Y:    0x{y:04X}")
        print(f"Z:    0x{z_ptr:04X}")
    except AttributeError:
        pass

def reportCSR():
    """Displays custom Control/Status Registers (like instructions retired)."""
    instret = _ci_cpu.getCSR(CSR_INSTRET)
    print("--- Control/Status Registers ---")
    print(f"Instructions Retired: {instret}")

def dump(start_addr, size=16):
    """Dumps a segment of Data Memory (SRAM) to the console."""
    try:
        # Assuming the CPU has a direct reference to the data memory array
        # You may need to tweak the path '.memory.mem' depending on your py4hw memory structure
        mem_array = _ci_cpu.memory.target.mem 
    except AttributeError:
        print("Could not locate memory array. Check memory component path.")
        return

    print(f"--- Memory Dump (0x{start_addr:04X} to 0x{start_addr+size-1:04X}) ---")
    for i in range(0, size, 8):
        row_addr = start_addr + i
        row_data = []
        for j in range(8):
            addr = row_addr + j
            if addr < len(mem_array):
                row_data.append(f"{mem_array[addr]:02X}")
            else:
                row_data.append("--")
        print(f"0x{row_addr:04X}: " + " ".join(row_data))