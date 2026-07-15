import os
import matplotlib.pyplot as plt
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.Memory import StackPointer

# 1. Define the Test Program
program_Test = '''
main:
    ; --- 1. INITIALIZE STACK POINTER ---
    ; ATmega328P RAM ends at 0x08FF
    LDI R16, 0x08
    OUT 0x3E, R16   ; Write 0x08 to SPH (I/O address 0x3E)
    LDI R16, 0xFF
    OUT 0x3D, R16   ; Write 0xFF to SPL (I/O address 0x3D)

; --- Zero out RAM (0x0100 to 0x08FF) ---
    LDI R28, 0x00    ; Y-pointer low
    LDI R29, 0x01    ; Y-pointer high (start of SRAM)
    LDI R16, 0x00    ; Value to write
clear_loop:
    ST Y+, R16       ; Write 0, increment Y
    CPI R28, 0x00    ; Check if we reached the end (0x0900)
    CPI R29, 0x09
    BRNE clear_loop
    
    ; ---  START TESTS ---
    JMP Sequancer

arithmetic:
    LDI R24,120
    LDI R25,40
    ADD R24,R25
    ; (Truncated for brevity, but all your arithmetic instructions run here)
    RET

memory:
    LDI R24,120
    MOV R5,R24
    ; (Truncated for brevity)
    RET

branch: 
    LDI R24,6
    LDI R25,6
    CP R24,R25 
    BREQ equal1
equal1:
    RET

Sequancer:
    CALL arithmetic
    CALL branch 
    CALL memory

asm_function:
    ; --- 3. SAFE HALT ---
halt:
    RJMP halt 
'''

# 2. Wrapper for Multicycle Processor to easily track performance CSRs
class MulticycleCpuWrapper:
    def __init__(self, cpu):
        self._cpu = cpu

    @property
    def pc(self):
        return self._cpu.children['RomHandler'].PC

    def get_retired_instructions(self):
        # Accessing the instruction count from the ControlBox FSM
        try:
            return self._cpu.control.main_fsm.instret_count
        except AttributeError:
            return 0 # Fallback if not tracked

# 3. CPU Setup Function
def prepare_cpu(cpu_type, program_words):
    global hw
    hw = py4hw.HWSystem()
    dw = 8 
    aw = 16
    
    # Setup Memory Interfaces
    data_p = punxa.MemoryInterface(hw, 'data_mem', dw, aw)
    ins_p = punxa.MemoryInterface(hw, 'ins_mem', 16, 14)
    gpio_p = punxa.MemoryInterface(hw, 'gpio', dw, 5)       
    reg_p = punxa.MemoryInterface(hw, 'reg', dw, 7)         
    usart_p = punxa.MemoryInterface(hw, 'usart', dw, 3)     
    sp_p = punxa.MemoryInterface(hw, 'sp_port', dw, 2)      
    mem_p = punxa.MemoryInterface(hw, 'mem', dw, 11)        
    
    # Multiplexed Bus Setup
    punxa.MultiplexedBus(hw, 'bus', data_p, 
                         [(reg_p, 0x0, 0x20),
                          (gpio_p, 0x20, 0x10),
                          (sp_p, 0x5D, 0x02),
                          (usart_p, 0xC0), 
                          (mem_p, 0x100)])
    
    # Initialize Memory Blocks
    reg = punxa.Ram_Memory(hw, 'reg', dw, 7, reg_p)                 
    mem = punxa.Ram_Memory(hw, 'men', dw, 11, mem_p)                
    ins_mem = punxa.Ram_Memory(hw, 'ins_men', 16, 14, ins_p)        
    usart = punxa.VirtualUSART(hw, 'usart', usart_p)
    gpio = punxa.VirtualGPIO(hw, 'gpio', gpio_p)
    sp_component = StackPointer(hw, 'stack_pointer', sp_p)
    
    # Load program into Instruction Memory
    for i, b in enumerate(program_words):
        ins_mem.writeWord(i, b)

    if cpu_type == 'single':
        cpu = punxa.SingleCycleATmega328P(hw, 'cpu', ins_p, data_p, reset_address=0)
        return hw, cpu, None
    elif cpu_type == 'multi':
        interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
        interrupt_wire.put(0)
        reset_wire = py4hw.Wire(hw, 'Reset_Line', 1)
        reset_wire.put(0)
        
        cpu = punxa.multicycleProcessor(hw, 'cpu', Interrupt=interrupt_wire, ins_mem=ins_p, memory=data_p, reset=reset_wire, reset_address=0)
        wrapped_cpu = MulticycleCpuWrapper(cpu)
        return hw, cpu, wrapped_cpu

# 4. Simulation Execution
def run_simulation(cpu_type, program_words, halt_pc):
    global cpu
    hw, cpu, wrapped_cpu = prepare_cpu(cpu_type, program_words)
    
    step_limit = 20000
    cycles = 0
    instructions = 0
    mem_wait_cycles = 0
    fetch_cycles = 0
    
    print(f"--- Running {cpu_type.upper()}-CYCLE CPU Simulation ---")
    
    while cycles < step_limit:
        hw.getSimulator().clk(1)
        cycles += 1
        
        # CPU Specific Metric Extraction
        if cpu_type == 'single':
            current_pc = cpu.pc
            instructions = cpu.getCSR(punxa.csr.CSR_INSTRET)
            # Single cycle accesses memory/fetches in 1 tick ideally
            fetch_cycles += 1
            if cpu.opp in ['LD', 'ST', 'LDS', 'STS', 'LDX', 'LDY', 'LDZ', 'STX', 'STY', 'STZ']:
                mem_wait_cycles += 1 
        else:
            current_pc = wrapped_cpu.pc
            instructions = wrapped_cpu.get_retired_instructions()
            # FSM Approximations for Multicycle (Extracting signals if available)
            # Assuming main_fsm tracks state (0 = FETCH, 3 = MEM_WAIT, etc. based on typical AVR designs)
            try:
                fsm_state = cpu.control.main_fsm.state.get()
                if fsm_state == 0:  # FETCH state
                    fetch_cycles += 1
                elif fsm_state == 3: # MEMORY READ/WRITE wait state
                    mem_wait_cycles += 1
            except AttributeError:
                pass # Skip if your FSM doesn't expose these directly
                
        # Break if we hit the Halt trap
        if current_pc == halt_pc:
            break

    print(f"Finished {cpu_type.upper()} CPU in {cycles} cycles.")
    
    # Calculate IPC
    ipc = instructions / cycles if cycles > 0 else 0
    
    return {
        "cycles": cycles,
        "instructions": instructions,
        "ipc": ipc,
        "fetch_cycles": fetch_cycles,
        "mem_wait_cycles": mem_wait_cycles
    }

# 5. Graph Generation
def generate_graphs(results_single, results_multi):
    labels = ['Single-Cycle', 'Multi-Cycle']
    
    # Graph 1: Average Instructions Per Cycle (IPC)
    ipc_values = [results_single['ipc'], results_multi['ipc']]
    
    # Graph 2: Fetch Cycles
    fetch_values = [results_single['fetch_cycles'], results_multi['fetch_cycles']]
    
    # Graph 3: Memory Wait Cycles
    mem_values = [results_single['mem_wait_cycles'], results_multi['mem_wait_cycles']]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('ATmega328P Architecture Comparison')

    # IPC Plot
    axes[0].bar(labels, ipc_values, color=['skyblue', 'lightcoral'])
    axes[0].set_title('Average Instructions Per Cycle (IPC)')
    axes[0].set_ylabel('IPC')
    for i, v in enumerate(ipc_values):
        axes[0].text(i, v + 0.02, f"{v:.2f}", ha='center')

    # Fetch Cycles Plot
    axes[1].bar(labels, fetch_values, color=['skyblue', 'lightcoral'])
    axes[1].set_title('Total Instruction Fetch Cycles')
    axes[1].set_ylabel('Cycles')
    for i, v in enumerate(fetch_values):
        axes[1].text(i, v + (max(fetch_values)*0.02), str(v), ha='center')

    # Memory Wait Plot
    axes[2].bar(labels, mem_values, color=['skyblue', 'lightcoral'])
    axes[2].set_title('Cycles Waiting for Memory')
    axes[2].set_ylabel('Cycles')
    for i, v in enumerate(mem_values):
        axes[2].text(i, v + (max(mem_values)*0.02), str(v), ha='center')

    plt.tight_layout()
    plt.savefig('cpu_comparison_graphs.png')
    plt.show()

if __name__ == "__main__":
    # Assemble the program to get the machine code and symbols
    words, symbols = assemble_program(program_Test)
    
    # The halt trap is designated as 'halt' in the assembly
    halt_address = symbols.get('halt', -1)
    
    if halt_address == -1:
        print("Warning: 'halt' label not found. Using instruction limit instead.")
        halt_address = len(words) - 1

    # Run simulations
    res_single = run_simulation('single', words, halt_address)
    res_multi = run_simulation('multi', words, halt_address)
    
    # Generate the comparison graphs
    #generate_graphs(res_single, res_multi)
    
    rtlgen = py4hw.VerilogGenerator(hw)
    
    rtl = rtlgen.getVerilogForHierarchy(cpu)
    print(rtl)
