#!/usr/bin/env python3
"""
Execute X cycles of the ATmega328P multicycle processor simulation.
Usage: python run_cycles.py <num_cycles> [--log]
"""

import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
import json
import sys
from datetime import datetime


# =============================================================================
# CONFIGURATION
# =============================================================================
NUM_CYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
ENABLE_LOGGING = "--log" in sys.argv
LOG_FILE = "cpu_wire_trace.jsonl"


# =============================================================================
# ASSEMBLY PROGRAM
# =============================================================================
program = '''
; Bare-metal, linear sequence for ATmega328P (16 MHz clock, 9600 Baud)

; 1. Initialize USART0 Baud Rate (UBRR = 103)
LDI R16, 0
STS 0xC5, R16        ; UBRRH0 <- 0
LDI R16, 103
STS 0xC4, R16        ; UBRRL0 <- 103

; 2. Enable USART0 Transmitter
LDI R16, 8
STS 0xC1, R16        ; UCSR0B <- 0x08 (TXEN0 enabled)

; 3. Set Frame Format (8 data bits, 1 stop bit)
LDI R16, 6
STS 0xC2, R16        ; UCSR0C <- 0x06 (UCSZ01 and UCSZ00 enabled)

; 4. Sequential Transmission (Poll buffer state, then push literal ASCII value)

; --- Byte 1: 'H' (0x48) ---
LDS R16, 0xC0        ; Read UCSR0A
SBRS R16, 5          ; Check UDRE0 bit. If set, skip next line
RJMP -4              ; Jump back to LDS command if buffer is busy
LDI R17, 0x48        ; Load 'H'
STS 0xC6, R17        ; Push to UDR0

; --- Byte 2: 'e' (0x65) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x65        ; Load 'e'
STS 0xC6, R17

; --- Byte 3: 'l' (0x6C) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6C        ; Load 'l'
STS 0xC6, R17

; --- Byte 4: 'l' (0x6C) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6C        ; Load 'l'
STS 0xC6, R17

; --- Byte 5: 'o' (0x6F) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6F        ; Load 'o'
STS 0xC6, R17

; --- Byte 6: ',' (0x2C) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x2C        ; Load ','
STS 0xC6, R17

; --- Byte 7: ' ' (0x20) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x20        ; Load space
STS 0xC6, R17

; --- Byte 8: 'W' (0x57) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x57        ; Load 'W'
STS 0xC6, R17

; --- Byte 9: 'o' (0x6F) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6F        ; Load 'o'
STS 0xC6, R17

; --- Byte 10: 'r' (0x72) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x72        ; Load 'r'
STS 0xC6, R17

; --- Byte 11: 'l' (0x6C) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x6C        ; Load 'l'
STS 0xC6, R17

; --- Byte 12: 'd' (0x64) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x64        ; Load 'd'
STS 0xC6, R17

; --- Byte 13: '!' (0x21) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x21        ; Load '!'
STS 0xC6, R17

; --- Byte 14: Carriage Return (0x0D) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x0D        ; Load CR
STS 0xC6, R17

; --- Byte 15: Line Feed (0x0A) ---
LDS R16, 0xC0
SBRS R16, 5
RJMP -4
LDI R17, 0x0A        ; Load LF
STS 0xC6, R17

; 5. Catch-trap
RJMP -1              ; Infinite self-loop
'''


# =============================================================================
# WIRE SNAPSHOT HELPER
# =============================================================================
def safe_get(wire):
    """Read a py4hw Wire value; return None if not yet driven."""
    try:
        return int(wire.get())
    except Exception:
        return None


def collect_wire_snapshot(cpu):
    """Return a flat dict {name: value} for every CPU wire."""
    return {
        # Instruction fetch / decode
        "w_instruction":            safe_get(cpu.w_instruction),
        "w_rom_address":            safe_get(cpu.w_rom_address),
        "W_CODE":                   safe_get(cpu.W_CODE),
        "W_Rd":                     safe_get(cpu.W_Rd),
        "W_Rr":                     safe_get(cpu.W_Rr),
        "W_K":                      safe_get(cpu.W_K),
        "W_K_ADDR":                 safe_get(cpu.W_K_ADDR),
        "W_b":                      safe_get(cpu.W_b),
        "W_A":                      safe_get(cpu.W_A),
        "W_q":                      safe_get(cpu.W_q),
        "W_Instruction_decoded":    safe_get(cpu.W_Instruction_decoded),
        "W_Instruction_fetched":    safe_get(cpu.W_Instruction_fetched),
        
        # Program counter / jump control
        "W_LOAD_Z":                 safe_get(cpu.W_LOAD_Z),
        "W_LOAD_K":                 safe_get(cpu.W_LOAD_K),
        "W_LOAD_JUMP":              safe_get(cpu.W_LOAD_JUMP),
        "W_Relative_Absolute":      safe_get(cpu.W_Relative_Absolute),
        "W_Load_byte":              safe_get(cpu.W_Load_byte),
        "W_LOAD_PCL":               safe_get(cpu.W_LOAD_PCL),
        "W_LOAD_PCH":               safe_get(cpu.W_LOAD_PCH),
        "W_JumpWidth":              safe_get(cpu.W_JumpWidth),
        "W_Executed_Jump":          safe_get(cpu.W_Executed_Jump),
        "W_Fetch_next_instruction": safe_get(cpu.W_Fetch_next_instruction),
        "W_Pc_valL":                safe_get(cpu.W_Pc_valL),
        "W_Pc_valH":                safe_get(cpu.W_Pc_valH),
        "W_PCL_LOAD_VAL":           safe_get(cpu.W_PCL_LOAD_VAL),
        "W_PCH_LOAD_VAL":           safe_get(cpu.W_PCH_LOAD_VAL),
        
        # ALU operands
        "W_ALU_ImputRegA0":         safe_get(cpu.W_ALU_ImputRegA0),
        "W_ALU_ImputRegA1":         safe_get(cpu.W_ALU_ImputRegA1),
        "W_ALU_ImputRegB0":         safe_get(cpu.W_ALU_ImputRegB0),
        "W_ALU_ImputRegB1":         safe_get(cpu.W_ALU_ImputRegB1),
        "W_OUTPUTByte0":            safe_get(cpu.W_OUTPUTByte0),
        "W_OUTPUTByte1":            safe_get(cpu.W_OUTPUTByte1),
        
        # ALU / SREG
        "W_ALU_SREG_IN":            safe_get(cpu.W_ALU_SREG_IN),
        "W_ALU_ESREG_OUT":          safe_get(cpu.W_ALU_ESREG_OUT),
        "W_ALU_SREG_OUT":           safe_get(cpu.W_ALU_SREG_OUT),
        "W_ALU_IO":                 safe_get(cpu.W_ALU_IO),
        "w_branch":                 safe_get(cpu.w_branch),
        "w_skip":                   safe_get(cpu.w_skip),
        "w_resp":                   safe_get(cpu.w_resp),
        
        # Operand buffer / write path
        "w_operand_data":           safe_get(cpu.w_operand_data),
        "w_operand_we":             safe_get(cpu.w_operand_we),
        "w_input_select":           safe_get(cpu.w_input_select),
        "w_write_enbale":           safe_get(cpu.w_write_enbale),
        
        # ControlBox outputs
        "W_NotExecute":             safe_get(cpu.W_NotExecute),
        "W_LoadSelect_MUX":         safe_get(cpu.W_LoadSelect_MUX),
        "W_Loading_MUX":            safe_get(cpu.W_Loading_MUX),
        "W_Input_Select":           safe_get(cpu.W_Input_Select),
        "W_WE":                     safe_get(cpu.W_WE),
        "W_read_write":             safe_get(cpu.W_read_write),
        
        # Memory / address paths
        "w_mem_incdec":             safe_get(cpu.w_mem_incdec),
        "w_mem_instr":              safe_get(cpu.w_mem_instr),
        "w_address_ZL":             safe_get(cpu.w_address_ZL),
        "w_address_ZH":             safe_get(cpu.w_address_ZH),
        "w_wb_addr":                safe_get(cpu.w_wb_addr),
        "w_EnableRead":             safe_get(cpu.w_EnableRead),
        "W_LoadL":                  safe_get(cpu.W_LoadL),
        "W_LoadH":                  safe_get(cpu.W_LoadH),
    }


def format_sreg(sreg):
    """Format SREG as ITHS VNZC string."""
    if sreg is None:
        return "........"
    flags = ""
    flags += "I" if (sreg >> 7) & 1 else "."
    flags += "T" if (sreg >> 6) & 1 else "."
    flags += "H" if (sreg >> 5) & 1 else "."
    flags += "S" if (sreg >> 4) & 1 else "."
    flags += "V" if (sreg >> 3) & 1 else "."
    flags += "N" if (sreg >> 2) & 1 else "."
    flags += "Z" if (sreg >> 1) & 1 else "."
    flags += "C" if (sreg >> 0) & 1 else "."
    return flags


# =============================================================================
# MAIN SIMULATION
# =============================================================================
def run_simulation(num_cycles, enable_logging=False):
    """Build hardware, load program, execute N cycles."""
    
    # -------------------------------------------------------------------
    # 1. HARDWARE SETUP
    # -------------------------------------------------------------------
    hw = py4hw.HWSystem()

    words, symbols = assemble_program(program)
    print(f"[SETUP] Assembled {len(words)} instruction words")
    if symbols:
        print(f"[SETUP] Symbols: {symbols}")

    dw = 8
    aw = 16

    data_p   = punxa.MemoryInterface(hw, 'data_mem',  dw, aw)
    ins_p    = punxa.MemoryInterface(hw, 'ins_mem',   16, 14)
    reg_p    = punxa.MemoryInterface(hw, 'reg_bus',   dw,  5)
    usart_p  = punxa.MemoryInterface(hw, 'usart_bus', dw,  3)
    mem_p    = punxa.MemoryInterface(hw, 'ram_bus',   dw, 11)

    punxa.MultiplexedBus(hw, 'bus', data_p,
                         [(reg_p, 0x0), (usart_p, 0xC0), (mem_p, 0x100)])

    reg      = punxa.Ram_Memory(hw, 'reg_mem',  dw,  5, reg_p)
    mem      = punxa.Ram_Memory(hw, 'ram_mem',  dw, 11, mem_p)
    ins_mem  = punxa.Ram_Memory(hw, 'ins_mem',  16, 14, ins_p)
    usart    = punxa.VirtualUSART(hw, 'usart_block', usart_p)

    interrupt_wire = py4hw.Wire(hw, 'Interrupt_Line', 1)
    interrupt_wire.put(0)

    reset_wire = py4hw.Wire(hw, 'Reset_Line', 1)
    reset_wire.put(0)

    cpu = punxa.multicycleProcessor(
        parent=hw,
        name='multicycle_cpu',
        Interrupt=interrupt_wire,
        ins_mem=ins_p,
        memory=data_p,
        reset=reset_wire,
        reset_address=0
    )

    # Load program into instruction memory
    for i, b in enumerate(words):
        ins_mem.writeWord(i, b)
    print(f"[SETUP] Program loaded into instruction memory")

    # -------------------------------------------------------------------
    # 2. CREATE CLOCK (Required for py4hw simulation)
    # -------------------------------------------------------------------
    clk = py4hw.clock(hw, 'clk')

    # -------------------------------------------------------------------
    # 3. OPEN LOG FILE (if enabled)
    # -------------------------------------------------------------------
    log_f = None
    if enable_logging:
        log_f = open(LOG_FILE, "w", buffering=1)
        header = {
            "_type": "trace_header",
            "generated": datetime.utcnow().isoformat() + "Z",
            "num_cycles": num_cycles,
        }
        log_f.write(json.dumps(header) + "\n")

    # -------------------------------------------------------------------
    # 4. EXECUTE CYCLES
    # -------------------------------------------------------------------
    print(f"\n[RUN] Executing {num_cycles} cycles...")
    print("-" * 80)
    
    prev_state = cpu.control.current_state
    instr_count = 0
    
    for cycle in range(num_cycles):
        # Advance simulation by exactly 1 clock cycle
        clk.clock(1)
        
        # Collect wire state
        snap = collect_wire_snapshot(cpu)
        curr_state = cpu.control.current_state
        
        # Detect instruction completion (state transition to FETCH_INSTRUION)
        if curr_state == 'FETCH_INSTRUION' and prev_state == 'FINISED_INSTRUCTION_EXECUTION':
            instr_count += 1
        
        prev_state = curr_state
        
        # Print cycle info every N cycles or on interesting events
        if cycle % 100 == 0 or snap.get("W_Instruction_fetched") == 1:
            pc = snap.get("w_rom_address", 0)
            instr = snap.get("w_instruction", 0)
            code = snap.get("W_CODE", 0)
            sreg = format_sreg(snap.get("W_ALU_SREG_OUT"))
            print(f"[{cycle:5d}] PC=0x{pc:04X} INSTR=0x{instr:04X} "
                  f"OP=0x{code:03X} SREG=[{sreg}] State={curr_state}")
        
        # Write to log file
        if enable_logging:
            record = {
                "cycle":        cycle,
                "pc":           snap.get("w_rom_address"),
                "instruction":  snap.get("w_instruction"),
                "decoded_code": snap.get("W_CODE"),
                "state":        curr_state,
                "wires":        snap,
            }
            log_f.write(json.dumps(record) + "\n")
    
    # -------------------------------------------------------------------
    # 5. SUMMARY
    # -------------------------------------------------------------------
    print("-" * 80)
    print(f"\n[Done] Completed {num_cycles} cycles")
    print(f"[Done] Approximate instructions executed: {instr_count}")
    print(f"[Done] Final state: {cpu.control.current_state}")
    print(f"[Done] Final PC: 0x{cpu.w_rom_address.get():04X}")
    print(f"[Done] Final SREG: [{format_sreg(cpu.W_ALU_SREG_OUT.get())}]")
    
    if enable_logging:
        log_f.close()
        print(f"[Done] Trace logged to: {LOG_FILE}")
    
    return hw, cpu


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("  ATmega328P Multicycle Processor - Cycle Executor")
    print("=" * 80)
    
    hw, cpu = run_simulation(NUM_CYCLES, ENABLE_LOGGING)