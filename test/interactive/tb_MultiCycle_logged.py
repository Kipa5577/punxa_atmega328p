import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.assembly import assemble_program
import json
import os
import sys
import traceback
from datetime import datetime

# =============================================================================
# WIRE STATE LOGGER
# Captures every wire defined in MulticycleProcessor at every clock cycle and
# writes a structured JSON-lines log that an AI agent can read to diagnose
# processor misbehaviour.
#
# Log format (one JSON object per line):
# {
#   "cycle":     <int>,          -- simulation clock cycle (0-based)
#   "phase":     "rising"|"falling",
#   "pc":        <int>,          -- current ROM address (w_rom_address)
#   "instruction": <int>,        -- raw 16-bit instruction word (w_instruction)
#   "decoded_code": <int>,       -- opcode after decode (w_code)
#   "wires": {
#     "<wire_name>": <int>,      -- current integer value of every CPU wire
#     ...
#   },
#   "events": [<str>, ...]       -- human-readable annotations for this cycle
# }
# =============================================================================

LOG_FILE = "cpu_wire_trace.jsonl"
MAX_CYCLES = 5000          # hard cap; increase if your program needs more
LOG_EVERY_N_CYCLES = 1     # set > 1 to thin the log for long runs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_get(wire):
    """Read a py4hw Wire value; return None if not yet driven."""
    try:
        v = wire.get()
        return int(v)
    except Exception:
        return None


def collect_wire_snapshot(cpu):
    """
    Return a flat dict {name: value} for every wire on the CPU object.
    All wires listed in MulticycleProcessor.__init__ are covered explicitly
    so the names stay stable across py4hw versions.
    """
    wires = {
        # ---- Instruction fetch / decode path ----
        "w_instruction":           safe_get(cpu.w_instruction),
        "w_rom_address":           safe_get(cpu.w_rom_address),
        "W_CODE":                  safe_get(cpu.W_CODE),
        "W_Rd":                    safe_get(cpu.W_Rd),
        "W_Rr":                    safe_get(cpu.W_Rr),
        "W_K":                     safe_get(cpu.W_K),
        "W_K_ADDR":                safe_get(cpu.W_K_ADDR),
        "W_b":                     safe_get(cpu.W_b),
        "W_A":                     safe_get(cpu.W_A),
        "W_q":                     safe_get(cpu.W_q),
        "W_Instruction_decoded":   safe_get(cpu.W_Instruction_decoded),
        "W_Instruction_fetched":   safe_get(cpu.W_Instruction_fetched),

        # ---- Program counter / jump control ----
        "W_LOAD_Z":                safe_get(cpu.W_LOAD_Z),
        "W_LOAD_K":                safe_get(cpu.W_LOAD_K),
        "W_LOAD_JUMP":             safe_get(cpu.W_LOAD_JUMP),
        "W_Relative_Absolute":     safe_get(cpu.W_Relative_Absolute),
        "W_Load_byte":             safe_get(cpu.W_Load_byte),
        "W_LOAD_PCL":              safe_get(cpu.W_LOAD_PCL),
        "W_LOAD_PCH":              safe_get(cpu.W_LOAD_PCH),
        "W_JumpWidth":             safe_get(cpu.W_JumpWidth),
        "W_Executed_Jump":         safe_get(cpu.W_Executed_Jump),
        "W_Fetch_next_instruction":safe_get(cpu.W_Fetch_next_instruction),
        "W_Pc_valL":               safe_get(cpu.W_Pc_valL),
        "W_Pc_valH":               safe_get(cpu.W_Pc_valH),
        "W_PCL_LOAD_VAL":          safe_get(cpu.W_PCL_LOAD_VAL),
        "W_PCH_LOAD_VAL":          safe_get(cpu.W_PCH_LOAD_VAL),

        # ---- ALU operands ----
        "W_ALU_ImputRegA0":        safe_get(cpu.W_ALU_ImputRegA0),
        "W_ALU_ImputRegA1":        safe_get(cpu.W_ALU_ImputRegA1),
        "W_ALU_ImputRegB0":        safe_get(cpu.W_ALU_ImputRegB0),
        "W_ALU_ImputRegB1":        safe_get(cpu.W_ALU_ImputRegB1),
        "W_OUTPUTByte0":           safe_get(cpu.W_OUTPUTByte0),
        "W_OUTPUTByte1":           safe_get(cpu.W_OUTPUTByte1),

        # ---- ALU / SREG ----
        "W_ALU_SREG_IN":           safe_get(cpu.W_ALU_SREG_IN),
        "W_ALU_ESREG_OUT":         safe_get(cpu.W_ALU_ESREG_OUT),
        "W_ALU_SREG_OUT":          safe_get(cpu.W_ALU_SREG_OUT),
        "W_ALU_IO":                safe_get(cpu.W_ALU_IO),
        "w_branch":                safe_get(cpu.w_branch),
        "w_skip":                  safe_get(cpu.w_skip),
        "w_resp":                  safe_get(cpu.w_resp),

        # ---- Operand buffer / write path ----
        "w_operand_data":          safe_get(cpu.w_operand_data),
        "w_operand_we":            safe_get(cpu.w_operand_we),
        "w_input_select":          safe_get(cpu.w_input_select),
        "w_write_enbale":          safe_get(cpu.w_write_enbale),

        # ---- ControlBox outputs ----
        "W_NotExecute":            safe_get(cpu.W_NotExecute),
        "W_LoadSelect_MUX":        safe_get(cpu.W_LoadSelect_MUX),
        "W_Loading_MUX":           safe_get(cpu.W_Loading_MUX),
        "W_Input_Select":          safe_get(cpu.W_Input_Select),
        "W_WE":                    safe_get(cpu.W_WE),
        "W_read_write":            safe_get(cpu.W_read_write),

        # ---- Memory / address paths ----
        "w_mem_incdec":            safe_get(cpu.w_mem_incdec),
        "w_mem_instr":             safe_get(cpu.w_mem_instr),
        "w_address_ZL":            safe_get(cpu.w_address_ZL),
        "w_address_ZH":            safe_get(cpu.w_address_ZH),
        "w_wb_addr":               safe_get(cpu.w_wb_addr),
        "w_EnableRead":            safe_get(cpu.w_EnableRead),
        "W_LoadL":                 safe_get(cpu.W_LoadL),
        "W_LoadH":                 safe_get(cpu.W_LoadH),
        "W_LOAD_Z":                safe_get(cpu.W_LOAD_Z),
    }
    return wires


def annotate_cycle(snap):
    """
    Generate human-readable event strings for a cycle snapshot.
    These help an AI agent quickly spot interesting moments.
    """
    events = []

    instr = snap.get("w_instruction")
    if instr is not None:
        events.append(f"INSTR=0x{instr:04X}")

    code = snap.get("W_CODE")
    if code is not None:
        events.append(f"OPCODE=0x{code:04X}")

    pc = snap.get("w_rom_address")
    if pc is not None:
        events.append(f"PC=0x{pc:02X}")

    if snap.get("W_Instruction_fetched") == 1:
        events.append("FETCH_DONE")
    if snap.get("W_Instruction_decoded") == 1:
        events.append("DECODE_DONE")
    if snap.get("W_Executed_Jump") == 1:
        events.append("JUMP_EXECUTED")
    if snap.get("W_Fetch_next_instruction") == 1:
        events.append("FETCH_NEXT")
    if snap.get("w_branch") == 1:
        events.append("BRANCH_TAKEN")
    if snap.get("w_skip") == 1:
        events.append("SKIP_NEXT")
    if snap.get("W_NotExecute") == 1:
        events.append("NOT_EXECUTE")
    if snap.get("W_LOAD_JUMP") == 1:
        events.append("LOAD_JUMP")
    if snap.get("W_LOAD_Z") == 1:
        events.append("LOAD_Z")
    if snap.get("W_LOAD_K") == 1:
        events.append("LOAD_K")
    if snap.get("W_LOAD_PCL") == 1:
        events.append("LOAD_PCL")
    if snap.get("W_LOAD_PCH") == 1:
        events.append("LOAD_PCH")

    we = snap.get("W_WE")
    if we is not None and we != 0:
        events.append(f"WE=0b{we:06b}")

    rw = snap.get("W_read_write")
    if rw == 1:
        events.append("MEM_READ")
    elif rw == 2:
        events.append("MEM_WRITE")
    elif rw == 3:
        events.append("MEM_READ+WRITE")

    rd = snap.get("W_Rd")
    rr = snap.get("W_Rr")
    if rd is not None:
        events.append(f"Rd=R{rd}")
    if rr is not None:
        events.append(f"Rr=R{rr}")

    k = snap.get("W_K")
    if k is not None and k != 0:
        events.append(f"K=0x{k:02X}")

    sreg = snap.get("W_ALU_SREG_OUT")
    if sreg is not None:
        # decode SREG bits: I T H S V N Z C
        flags = ""
        flags += "I" if (sreg >> 7) & 1 else "."
        flags += "T" if (sreg >> 6) & 1 else "."
        flags += "H" if (sreg >> 5) & 1 else "."
        flags += "S" if (sreg >> 4) & 1 else "."
        flags += "V" if (sreg >> 3) & 1 else "."
        flags += "N" if (sreg >> 2) & 1 else "."
        flags += "Z" if (sreg >> 1) & 1 else "."
        flags += "C" if (sreg >> 0) & 1 else "."
        events.append(f"SREG={flags}")

    return events


# ---------------------------------------------------------------------------
# Custom simulation stepper with logging
# ---------------------------------------------------------------------------

class WireTraceLogger:
    """
    Wraps a py4hw HWSystem and steps it cycle by cycle, writing a JSON-lines
    trace file that an AI agent can parse to diagnose processor issues.
    """

    def __init__(self, hw, cpu, log_path=LOG_FILE, max_cycles=MAX_CYCLES,
                 log_every=LOG_EVERY_N_CYCLES):
        self.hw = hw
        self.cpu = cpu
        self.log_path = log_path
        self.max_cycles = max_cycles
        self.log_every = log_every
        self._cycle = 0
        self._prev_snap = None
        self._f = None

        # Per-signal change counters (for summary)
        self._change_counts = {}

    def _open(self):
        self._f = open(self.log_path, "w", buffering=1)   # line-buffered
        # Write a header comment (not valid JSON, but clearly labelled)
        header = {
            "_type": "trace_header",
            "generated": datetime.utcnow().isoformat() + "Z",
            "log_every_n_cycles": self.log_every,
            "max_cycles": self.max_cycles,
            "wire_legend": {
                "w_instruction":           "Raw 16-bit instruction word from ROM",
                "w_rom_address":           "Current PC / ROM word address (4-bit shown; actual wider inside RomHandler)",
                "W_CODE":                  "Decoded opcode passed to ControlBox and ALU",
                "W_Rd":                    "Destination register index (5 bits)",
                "W_Rr":                    "Source register index (5 bits)",
                "W_K":                     "8-bit immediate constant",
                "W_K_ADDR":                "22-bit address constant (CALL/JMP/LDS/STS)",
                "W_b":                     "Bit position operand (7 bits)",
                "W_A":                     "I/O address operand (5 bits)",
                "W_q":                     "6-bit displacement for Y/Z+q addressing",
                "W_Instruction_decoded":   "1 when decoder has finished (combinational done flag)",
                "W_Instruction_fetched":   "1 when ROM has placed a new word on w_instruction",
                "W_LOAD_Z":                "1 = load Z-register address into PC",
                "W_LOAD_K":                "1 = load K_ADDR constant into PC",
                "W_LOAD_JUMP":             "1 = commit a jump this cycle",
                "W_Relative_Absolute":     "0 = relative jump, 1 = absolute jump",
                "W_Load_byte":             "1 = load single byte into PC (RJMP short)",
                "W_LOAD_PCL":              "1 = load PCL_LOAD_VAL into PCL",
                "W_LOAD_PCH":              "1 = load PCH_LOAD_VAL into PCH",
                "W_JumpWidth":             "0 = 16-bit jump target, 1 = 22-bit",
                "W_Executed_Jump":         "1 = a jump was committed this cycle (feedback to decoder)",
                "W_Fetch_next_instruction":"1 = pipeline ready to fetch the next instruction",
                "W_Pc_valL":               "Low byte of current PC value (for CALL/RET push)",
                "W_Pc_valH":               "High byte of current PC value",
                "W_PCL_LOAD_VAL":          "Value to load into PCL on LOAD_PCL",
                "W_PCH_LOAD_VAL":          "Value to load into PCH on LOAD_PCH",
                "W_ALU_ImputRegA0":        "ALU A-operand byte 0 (Rd low)",
                "W_ALU_ImputRegA1":        "ALU A-operand byte 1 (Rd high, ADIW/MUL)",
                "W_ALU_ImputRegB0":        "ALU B-operand byte 0 (Rr low)",
                "W_ALU_ImputRegB1":        "ALU B-operand byte 1 (Rr high)",
                "W_OUTPUTByte0":           "ALU result byte 0 (written to Rd)",
                "W_OUTPUTByte1":           "ALU result byte 1 (Rd+1 for wide ops)",
                "W_ALU_SREG_IN":           "SREG value to be committed (from ALU)",
                "W_ALU_ESREG_OUT":         "Extended/masked SREG from ALU (for SREG_Logic)",
                "W_ALU_SREG_OUT":          "Current committed SREG (I.T.H.S.V.N.Z.C)",
                "W_ALU_IO":                "I/O register byte routed to ALU for IN/OUT/SBI/CBI",
                "w_branch":                "1 = conditional branch should be taken",
                "w_skip":                  "1 = SBRS/SBRC/SBIS/SBIC skip condition met",
                "w_resp":                  "Memory interface ready/response handshake",
                "w_operand_data":          "Data byte from register file into OperandBuffer",
                "w_operand_we":            "OperandBuffer write-enable: 1=A0 2=A1 3=B0 4=B1 (3-bit code)",
                "w_input_select":          "1 = OperandBuffer input comes from K, 0 = from register",
                "w_write_enbale":          "3-bit WE for write-back path into OperandBuffer",
                "W_NotExecute":            "1 = this instruction must NOT produce side-effects (stall/skip)",
                "W_LoadSelect_MUX":        "3-bit mux select for which source loads the register file",
                "W_Loading_MUX":           "3-bit mux select for register-file load data",
                "W_Input_Select":          "3-bit input select for MemoryInterfaceHandler data path",
                "W_WE":                    "6-bit write-enable bus for register file / memory",
                "W_read_write":            "2-bit memory direction: 0=idle 1=read 2=write 3=both",
                "w_mem_incdec":            "2-bit X/Y/Z pointer inc/dec for LD/ST addressing modes",
                "w_mem_instr":             "4-bit memory instruction code to MemoryInterfaceHandler",
                "w_address_ZL":            "Z-pointer low byte (used for indirect memory address)",
                "w_address_ZH":            "Z-pointer high byte",
                "w_wb_addr":               "5-bit explicit write-back register address (ADIW/MUL/MOVW)",
                "w_EnableRead":            "1 = enable read path in MemoryInterfaceHandler",
                "W_LoadL":                 "1 = load low byte latch in MemoryInterfaceHandler",
                "W_LoadH":                 "1 = load high byte latch in MemoryInterfaceHandler",
            }
        }
        self._f.write(json.dumps(header) + "\n")

    def _write(self, record):
        self._f.write(json.dumps(record) + "\n")

    def _detect_changes(self, snap):
        """Return list of (wire_name, old_val, new_val) tuples that changed."""
        if self._prev_snap is None:
            return []
        changes = []
        for k, v in snap.items():
            old = self._prev_snap.get(k)
            if old != v:
                changes.append((k, old, v))
                self._change_counts[k] = self._change_counts.get(k, 0) + 1
        return changes

    def run(self, cycles=None):
        """
        Step the simulation for `cycles` clocks (default = self.max_cycles).
        Each cycle is stepped twice: rising edge then falling edge, matching
        py4hw's clocked behaviour.
        """
        if cycles is None:
            cycles = self.max_cycles

        self._open()
        print(f"[WireTraceLogger] Starting trace → {self.log_path}")
        print(f"[WireTraceLogger] Logging every {self.log_every} cycle(s), max {cycles} cycles")

        try:
            for i in range(cycles):
                self._cycle = i

                # --- Rising edge ---
                self.hw.step()

                if i % self.log_every == 0:
                    snap = collect_wire_snapshot(self.cpu)
                    changes = self._detect_changes(snap)
                    events = annotate_cycle(snap)
                    if changes:
                        events.append("CHANGED:" + ",".join(
                            f"{n}:{ov}->{nv}" for n, ov, nv in changes
                        ))
                    record = {
                        "cycle":       i,
                        "phase":       "rising",
                        "pc":          snap.get("w_rom_address"),
                        "instruction": snap.get("w_instruction"),
                        "decoded_code":snap.get("W_CODE"),
                        "wires":       snap,
                        "events":      events,
                    }
                    self._write(record)
                    self._prev_snap = snap

        except KeyboardInterrupt:
            print(f"\n[WireTraceLogger] Interrupted at cycle {self._cycle}")
        except Exception as exc:
            err_record = {
                "cycle":   self._cycle,
                "phase":   "error",
                "_type":   "exception",
                "message": str(exc),
                "trace":   traceback.format_exc(),
            }
            self._write(err_record)
            print(f"[WireTraceLogger] Exception at cycle {self._cycle}: {exc}")
        finally:
            self._write_summary()
            self._f.close()
            print(f"[WireTraceLogger] Trace written to {self.log_path} "
                  f"({self._cycle + 1} cycles simulated)")

    def _write_summary(self):
        """Append a summary record showing which wires toggled most often."""
        summary = {
            "_type":           "trace_summary",
            "total_cycles":    self._cycle + 1,
            "signals_logged":  len(self._change_counts),
            "activity_counts": dict(
                sorted(self._change_counts.items(), key=lambda x: -x[1])
            ),
        }
        self._write(summary)


# =============================================================================
# PROGRAM
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
# HARDWARE SETUP  (identical to original tb_MultiCycle.py)
# =============================================================================

hw = py4hw.HWSystem()

words, symbols = assemble_program(program)
print(f"Assembled {len(words)} instructions")
print(f"Symbols: {symbols}")

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

# Optional: also keep the standard py4hw waveform for GUI use
watch = []
watch.extend(py4hw.debug.getInterfaceWires(ins_p))
watch.extend(py4hw.debug.getInterfaceWires(data_p))
watch.extend(py4hw.debug.getInterfaceWires(reg_p))
watch.append(cpu.w_instruction)
watch.append(cpu.W_CODE)
watch.append(cpu.w_rom_address)
wvf = py4hw.Waveform(hw, 'wvf', watch)

# Load program
for i, b in enumerate(words):
    ins_mem.writeWord(i, b)

# =============================================================================
# CHOOSE RUN MODE
# Set HEADLESS=True (or pass --headless) to just produce the log without the
# GUI. Set HEADLESS=False to keep the interactive workbench and run the trace
# in the background.
# =============================================================================

HEADLESS = "--headless" in sys.argv or os.environ.get("HEADLESS", "0") == "1"

if HEADLESS:
    # -----------------------------------------------------------------------
    # Headless mode: run the simulation, write the trace, exit.
    # -----------------------------------------------------------------------
    logger = WireTraceLogger(
        hw=hw,
        cpu=cpu,
        log_path=LOG_FILE,
        max_cycles=MAX_CYCLES,
        log_every=LOG_EVERY_N_CYCLES,
    )
    logger.run()

else:
    # -----------------------------------------------------------------------
    # Interactive mode: launch the GUI AND simultaneously run the tracer in
    # a background thread so you can step through the GUI while the log
    # accumulates.
    # -----------------------------------------------------------------------
    import threading

    logger = WireTraceLogger(
        hw=hw,
        cpu=cpu,
        log_path=LOG_FILE,
        max_cycles=MAX_CYCLES,
        log_every=LOG_EVERY_N_CYCLES,
    )

    trace_thread = threading.Thread(target=logger.run, daemon=True,
                                    name="WireTraceLogger")
    trace_thread.start()

    import punxa_atmega328p.interactive_commands as ci
    ci._ci_hw  = hw
    ci._ci_cpu = cpu
    from punxa_atmega328p.interactive_commands import *

    banner = '''
██████╗ ██╗   ██╗███╗   ██╗██╗  ██╗ █████╗
██╔══██╗██║   ██║████╗  ██║╚██╗██╔╝██╔══██╗      _   _                        __ __  __
██████╔╝██║   ██║██╔██╗ ██║ ╚███╔╝ ███████║     /_\ | |_ _ __  ___ ___   __    _) _)(__) __
██╔═══╝ ██║   ██║██║╚██╗██║ ██╔██╗ ██╔══██║    / _ \\| '_| '  \\/ -_) _ \\ / _`| __)/_ (__) |_)
██║     ╚██████╔╝██║ ╚████║██╔╝ ██╗██║  ██║   /_/ \\_\\_| |_|_|_\\___\\__, \\__,_|            |
╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝                       |___/                

             The Atmega328p Multicycle System Simulator
    [Wire trace logging to: cpu_wire_trace.jsonl]
'''
    print(banner)
    py4hw.gui.Workbench(hw)