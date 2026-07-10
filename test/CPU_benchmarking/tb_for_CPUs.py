import os
from collections import Counter
import matplotlib.pyplot as plt
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.Memory import StackPointer
from punxa_atmega328p.instruction_decode import MEMORY_INSTRUCTIONS  # authoritative memory-op set

# --- Opcode categorization (for the cycle/instruction breakdown) ---
CONTROL_FLOW_INSTRUCTIONS = {
    'RJMP', 'JMP', 'RCALL', 'CALL', 'RET', 'RETI', 'IJMP', 'ICALL',
    'BRBC', 'BRBS', 'BRGE', 'BRLT', 'CPSE', 'SBRC', 'SBRS', 'SBIC', 'SBIS',
}
IO_INSTRUCTIONS = {'IN', 'OUT', 'SBI', 'CBI'}
STACK_INSTRUCTIONS = {'PUSH', 'POP'}

def categorize_opcode(opp):
    if opp in MEMORY_INSTRUCTIONS:
        return 'Memory'
    if opp in STACK_INSTRUCTIONS:
        return 'Stack'
    if opp in CONTROL_FLOW_INSTRUCTIONS:
        return 'Branch/Control'
    if opp in IO_INSTRUCTIONS:
        return 'I/O'
    return 'ALU/Other'

CATEGORY_COLORS = {
    'Memory': '#e74c3c',
    'Stack': '#9b59b6',
    'Branch/Control': '#f39c12',
    'I/O': '#3498db',
    'ALU/Other': '#2ecc71',
}

# Assumed real hardware clock for the "estimated wall-clock time" metric.
# Standard Arduino Uno / ATmega328P runs at 16 MHz.
CLOCK_HZ = 16_000_000

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
        return self._cpu.rom.PC

    def get_retired_instructions(self):
        # Accessing the instruction count from the ControlBox FSM
        try:
            return self._cpu.control.main_fsm.instret_count
        except AttributeError:
            return 0 # Fallback if not tracked

# 3. CPU Setup Function
def prepare_cpu(cpu_type, program_words):
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
        
        cpu = punxa.multicycleProcessor(
            parent=hw, 
            name='cpu', 
            Interrupt=interrupt_wire, 
            ins_mem=ins_p, 
            memory=data_p, 
            reset=reset_wire, 
            reset_address=0
        )
        wrapped_cpu = MulticycleCpuWrapper(cpu)
        return hw, cpu, wrapped_cpu

# 4. Simulation Execution
def run_simulation(cpu_type, program_words, halt_pc):
    hw, cpu, wrapped_cpu = prepare_cpu(cpu_type, program_words)

    # The "single-cycle" model still resolves every register/memory access as
    # its own multi-yield handshake, so a single instruction can cost well
    # over 1 clock. The RAM-clearing loop in the test program alone needs
    # ~50,000+ clocks before the real test code even starts, so the budget
    # has to be generous or the run times out before reaching `halt`.
    step_limit = 300000
    cycles = 0
    instructions = 0
    mem_wait_cycles = 0
    fetch_cycles = 0

    # --- New: per-opcode and per-category tracking ---
    seen_opcodes = set()
    opcode_counts = Counter()   # opcode -> number of times retired
    opcode_cycles = Counter()   # opcode -> total cycles attributed to it
    category_counts = Counter()
    category_cycles = Counter()
    prev_instret = 0
    cycles_since_retire = 0

    print(f"\n--- Running {cpu_type.upper()}-CYCLE CPU Simulation ---")
    
    while cycles < step_limit:
        hw.getSimulator().clk(1)
        cycles += 1
        cycles_since_retire += 1
        
        # CPU Specific Metric Extraction
        if cpu_type == 'single':
            current_pc = cpu.pc
            instructions = cpu.getCSR(punxa.csr.CSR_INSTRET)
            fetch_cycles += 1
            seen_opcodes.add(cpu.opp)
            if cpu.opp in MEMORY_INSTRUCTIONS:
                mem_wait_cycles += 1

            # An instruction just retired this clock. `cpu.opp` at this exact
            # moment still reflects the instruction that just finished (it
            # only gets overwritten once the *next* instruction's execute()
            # begins), so this is the one safe place to attribute cycles to
            # an opcode without over- or under-counting multi-clock instructions.
            if instructions > prev_instret:
                n_retired = instructions - prev_instret
                retired_opcode = cpu.opp
                cat = categorize_opcode(retired_opcode)
                opcode_counts[retired_opcode] += n_retired
                opcode_cycles[retired_opcode] += cycles_since_retire
                category_counts[cat] += n_retired
                category_cycles[cat] += cycles_since_retire
                prev_instret = instructions
                cycles_since_retire = 0
        else:
            current_pc = wrapped_cpu.pc
            instructions = wrapped_cpu.get_retired_instructions()
            
            try:
                fsm_state = cpu.control.main_fsm.state.get()
                if fsm_state == 0:  # FETCH state
                    fetch_cycles += 1
                elif fsm_state == 3: # MEMORY READ/WRITE wait state
                    mem_wait_cycles += 1
            except AttributeError:
                pass 
                
        if current_pc == halt_pc:
            break

    halted = (current_pc == halt_pc)
    print(f"Finished {cpu_type.upper()} CPU in {cycles} cycles.")
    if not halted:
        print(f"  WARNING: step_limit reached WITHOUT hitting halt_pc "
              f"(halt_pc=0x{halt_pc:04X}, final PC=0x{current_pc:04X}). "
              f"Metrics below are NOT representative of a completed run.")

    ipc = instructions / cycles if cycles > 0 else 0
    cpi = cycles / instructions if instructions > 0 else 0
    est_time_us = (cycles / CLOCK_HZ) * 1e6

    if cpu_type == 'single':
        print(f"  Distinct opcodes executed: {sorted(seen_opcodes)}")
        print(f"  Estimated run time @ {CLOCK_HZ/1e6:.0f} MHz: {est_time_us:.2f} us")
        print(f"  Program size: {len(program_words)} words")
        print(f"\n  Top opcodes by total cycle cost:")
        print(f"  {'Opcode':<10}{'Count':>8}{'TotalCyc':>10}{'Avg Cyc/Ins':>13}")
        for op, total_cyc in opcode_cycles.most_common(10):
            cnt = opcode_counts[op]
            avg = total_cyc / cnt if cnt else 0
            print(f"  {op:<10}{cnt:>8}{total_cyc:>10}{avg:>13.2f}")

    return {
        "cycles": cycles,
        "instructions": instructions,
        "ipc": ipc,
        "cpi": cpi,
        "fetch_cycles": fetch_cycles,
        "mem_wait_cycles": mem_wait_cycles,
        "halted": halted,
        "est_time_us": est_time_us,
        "code_size_words": len(program_words),
        "opcode_counts": opcode_counts,
        "opcode_cycles": opcode_cycles,
        "category_counts": category_counts,
        "category_cycles": category_cycles,
    }

# 5. Graph Generation
def generate_graphs(results_single, results_multi):
    labels = []
    ipc_values = []
    cpi_values = []
    fetch_values = []
    mem_values = []
    time_values = []
    colors = []

    # Dynamically build the lists based on what was run
    for label, res, color in [('Single-Cycle', results_single, 'skyblue'),
                              ('Multi-Cycle', results_multi, 'lightcoral')]:
        if res:
            labels.append(label)
            ipc_values.append(res['ipc'])
            cpi_values.append(res['cpi'])
            fetch_values.append(res['fetch_cycles'])
            mem_values.append(res['mem_wait_cycles'])
            time_values.append(res['est_time_us'])
            colors.append(color)

    if not labels:
        print("No results to graph.")
        return

    fig, axes = plt.subplots(2, 3, figsize=(17, 9))
    fig.suptitle('ATmega328P Execution Metrics')

    def bar_with_labels(ax, vals, title, ylabel, fmt="{:.2f}"):
        ax.bar(labels, vals, color=colors)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        top = max(vals + [0.001]) * 0.02
        for i, v in enumerate(vals):
            ax.text(i, v + top, fmt.format(v), ha='center')

    bar_with_labels(axes[0, 0], ipc_values, 'Average IPC', 'IPC', "{:.3f}")
    bar_with_labels(axes[0, 1], cpi_values, 'Average Cycles Per Instruction (CPI)', 'CPI', "{:.2f}")
    bar_with_labels(axes[0, 2], time_values, f'Estimated Run Time @ {CLOCK_HZ/1e6:.0f} MHz', 'microseconds', "{:.1f}")
    bar_with_labels(axes[1, 0], fetch_values, 'Total Instruction Fetch Cycles', 'Cycles', "{:.0f}")
    bar_with_labels(axes[1, 1], mem_values, 'Cycles Waiting for Memory', 'Cycles', "{:.0f}")

    # Category cycle breakdown (stacked bar), using whichever result has data
    ax = axes[1, 2]
    cat_source = results_single or results_multi
    if cat_source and cat_source.get('category_cycles'):
        all_cats = ['ALU/Other', 'Memory', 'Branch/Control', 'Stack', 'I/O']
        bottoms = [0] * len(labels)
        for cat in all_cats:
            vals = []
            for res in [results_single, results_multi]:
                if res:
                    vals.append(res['category_cycles'].get(cat, 0))
            if any(vals):
                ax.bar(labels, vals, bottom=bottoms, label=cat, color=CATEGORY_COLORS.get(cat))
                bottoms = [b + v for b, v in zip(bottoms, vals)]
        ax.set_title('Cycles by Instruction Category')
        ax.set_ylabel('Cycles')
        ax.legend(fontsize=8)
    else:
        ax.axis('off')
        ax.set_title('Cycles by Instruction Category (n/a)')

    plt.tight_layout()
    plt.savefig('cpu_comparison_graphs.png')
    plt.show()

    # Separate figure: opcode frequency for whichever run has opcode data
    freq_source = results_single or results_multi
    if freq_source and freq_source.get('opcode_counts'):
        top_ops = freq_source['opcode_counts'].most_common(12)
        if top_ops:
            names = [o for o, _ in top_ops]
            counts = [c for _, c in top_ops]
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            ax2.bar(names, counts, color='mediumseagreen')
            ax2.set_title('Most Frequent Opcodes Retired')
            ax2.set_ylabel('Times Executed')
            ax2.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            plt.savefig('cpu_opcode_frequency.png')
            plt.show()

if __name__ == "__main__":
    # --- CONFIGURATION FLAGS ---
    # Change these to True or False to select which CPU to test
    TEST_SINGLE_CYCLE = True
    TEST_MULTI_CYCLE = False
    # ---------------------------

    # Assemble the program
    words, symbols = assemble_program(program_Test)
    halt_address = symbols.get('halt', -1)
    
    if halt_address == -1:
        print("Warning: 'halt' label not found. Using instruction limit instead.")
        halt_address = len(words) - 1

    res_single = None
    res_multi = None

    # Run selected simulations
    if TEST_SINGLE_CYCLE:
        try:
            res_single = run_simulation('single', words, halt_address)
        except Exception as e:
            print(f"Error during Single-Cycle simulation: {e}")

    if TEST_MULTI_CYCLE:
        try:
            res_multi = run_simulation('multi', words, halt_address)
        except Exception as e:
            print(f"Error during Multi-Cycle simulation: {e}")
            print("Note: Skipping multicycle graph data due to crash.")
    
    # Generate the graphs based on whatever succeeded
    generate_graphs(res_single, res_multi)