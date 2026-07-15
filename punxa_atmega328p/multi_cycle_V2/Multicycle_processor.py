import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.instruction_decode import ins_to_str
from punxa_atmega328p.instruction_decode import TWO_CYCLE_INSRUCTIONS
from punxa_atmega328p.instruction_decode import MEMORY_INSTRUCTIONS
from punxa_atmega328p.Memory import *

from punxa_atmega328p.csr import *
from deprecated import deprecated

## *_IO = IN and OUT instruction address
## *_LS =  LD LDS ST STS instruction address

#0x0000 to 0x3FFF flash memory range 

#Start of Sram : 0x0100 | End of Sram : 0x08FF
#pointer registers
# R26 X-register Low Byte 
# R27 X-register High Byte
# R28 Y-register Low Byte
# R29 Y-register High Byte
# R30 Z-register Low Byte 
# R31 Z-register High Byte
 
# interupt wires to add: INT0, INT1, PCINT0, PCINT1, PCINT2, WDT, TIMER2 COMPA, TIMER2 COMPB, TIMER2 OVF, TIMER1 CAPT, TIMER1 COMPA, TIMER1 COMPB, TIMER1 OVF, TIMER0 COMPA, TIMER0 COMPB, TIMER0 OVF, SPI/STC , USART/RX , USART/UDRE , USART/TX , ADC , EE READY , ANALOG COMP, TWI, SPM READY.
 

# ---------------------------------------------------------------------------
# Full multicycle FSM implementation.
#
# Top level flow:
#   STATE_RESET
#     -> FETCH_INSTRUCTION            (request word @ pc from instruction ROM)
#     -> WAIT_FETCH_INSTRUCTION       (wait for resp, decode opcode)
#          - if opcode is a 2-word instruction (JMP/CALL/LDS/STS):
#                -> STATE_FETCH_OP2_REQ  (request word @ pc+1)
#                -> STATE_FETCH_OP2_WAIT (wait for resp, capture 2nd word)
#          -> STATE_DECODE_EXEC
#     -> STATE_DECODE_EXEC           (calls execute(), which either finishes the
#                                      instruction in this same cycle - simple
#                                      register/ALU/branch ops - or hands off to
#                                      one of the dedicated multicycle engines
#                                      below by setting self.state itself)
#
# Dedicated multicycle engines (all reachable only through execute()):
#   STATE_FETCH_REQ / STATE_MEM_WAIT           - generic 1 byte data-memory
#                                                 read or write (IN, OUT, LDS,
#                                                 STS, and the back-end of the
#                                                 indirect LD/ST engine)
#   STATE_INDIRECT_LOAD / STATE_INDIRECT_STORE - pointer (X/Y/Z) address
#                                                 computation for all LD*/ST*
#                                                 addressing modes, then
#                                                 delegates the byte transfer
#                                                 to STATE_FETCH_REQ
#   STATE_CALL_PUSH_H / STATE_CALL_PUSH_L      - 1 or 2 byte push engine used
#                                                 by CALL/RCALL/ICALL/PUSH
#   STATE_RET_POP_H / STATE_RET_POP_L          - 1 or 2 byte pop engine used
#                                                 by RET/RETI/POP
#   STATE_LPM_REQ / STATE_LPM_WAIT             - LPM / LPM Rd,Z / LPM Rd,Z+
#   STATE_IO_BIT_READ / STATE_IO_BIT_WRITE     - SBI/CBI (read-modify-write)
#                                                 and SBIC/SBIS (read + test)
#   STATE_SKIP_FETCH_REQ / STATE_SKIP_FETCH_WAIT - CPSE/SBRC/SBRS/SBIC/SBIS:
#                                                 fetch the instruction being
#                                                 skipped over just to find out
#                                                 whether it is 1 or 2 words
#                                                 long, so pc can be advanced
#                                                 correctly.
# ---------------------------------------------------------------------------

STATES = [
    "STATE_RESET",
    "FETCH_INSTRUCTION","WAIT_FETCH_INSTRUCTION","STATE_DECODE_EXEC",
    "STATE_FETCH_OP2_REQ", "STATE_FETCH_OP2_WAIT",
    "STATE_FETCH_REQ","STATE_MEM_WAIT",
    # CALL/RET
    "STATE_CALL_PUSH_H_REQ","STATE_CALL_PUSH_H","STATE_CALL_PUSH_L",
    "STATE_RET_POP_L_REQ","STATE_RET_POP_L","STATE_RET_POP_H",
    # Indirect load/store , LPM
    "STATE_INDIRECT_LOAD","STATE_INDIRECT_STORE",
    "STATE_LPM_REQ","STATE_LPM_WAIT",
    "STATE_SPM_WRITE_REQ","STATE_SPM_WRITE_WAIT",
    # I/O bit read-modify-write
    "STATE_IO_BIT_READ","STATE_IO_BIT_WRITE_REQ","STATE_IO_BIT_WRITE",
    # SKIP
    "STATE_SKIP_FETCH_REQ","STATE_SKIP_FETCH_WAIT"
]

# The only real two-word (32 bit) AVR instructions.
TWO_WORD_OPS = {"JMP", "CALL", "LDS", "STS"}

# ptr register (X/Y/Z) -> index of its LOW byte in the register file
PTR_LOW = {'X': 26, 'Y': 28, 'Z': 30}


class MultyCycleATmega328P_V2(py4hw.Logic):
    def __init__(self,parent, name:str , ins_mem:MemoryInterface,memory:MemoryInterface, reset_address, Interrupt=None, reset=None):
        super().__init__(parent,name)

        assert(ins_mem.read_data.getWidth() == 16)
        assert(memory.read_data.getWidth() == 8)
        
        self.ins_mem = self.addInterfaceSource('ins', ins_mem)
        self.mem = self.addInterfaceSource('data', memory)
        self.pc = reset_address
        self.reg = [0]*32

        # Optional wires - not yet driving interrupt/async-reset logic, just
        # accepted so a testbench can hook them up ahead of that feature.
        self.interrupt_wire = Interrupt
        self.reset_wire = reset



        
        self.next_cycle = False #varible to indicate that data is ready to read from ram/memeory
        self.ins = 0
        self.ins2 = 0          # second word of a 2-word instruction (JMP/CALL/LDS/STS)
        self.opp = 'NOP'
        self.Rr = 0
        self.Rd = 0
        self.res = 0
        self.K = 0
        self.FirstBoot = True #is this actuatly odable ?
        self.BOOTRST = 1
        self.databyteNb = 0
        self.FSM = 'Begin' 

        self.A = 0
        self.q = 0
        self.high = 0
        self.low = 0

        #registers
        self.SREG = 0 # b7: I b6: T b5: H b4: S b3: V b2: N b1: Z b0: C 
        self.SREG_addr_IO = 0x3F
        self.SREG_addr_LS = 0x5F

        self.MCUCR = 0
        self.MCUCR_addr_IO = 0x35
        self.MCUCR_addr_LS = 0x55

        #Stack Pointer
        self.SPH = 0x08
        self.SPH_addr_IO = 0x3E
        self.SPH_addr_LS = 0x5E

        self.SPL = 0xFF
        self.SPL_addr_IO = 0x3D
        self.SPL_addr_LS = 0x5D

        self.MCUSR = 0x02 # Power-on Reset  or it can be 0x02 External Reset
        self.MCUSR_addr_IO = 0x34
        self.MCUSR_addr_LS = 0x54

        #Warchdog Timer Configruation
        self.WDTCSR = 0
        self.WDTCSR_addr_LS = 0x60

        #SPMCSR - Store Program Memory Control and Status Register
        self.SPMCSR = 0 
        self.SPMCSR_addr_IO = 0x37
        self.SPMCSR_addr_LS = 0x57


        self.skip_next_instruction = False

        self.gotToGoFast = False

        self.insFiniteStateMachine = 'START'

        self.PAGE_SIZE_WORDS = 64
        
        self.temp_page_buffer = [0xFFFF] * self.PAGE_SIZE_WORDS     

        self.last_pc = 0

        # ---- multicycle FSM bookkeeping ----
        self.state = "STATE_RESET"
        self.reset_address = reset_address

        # generic data-memory engine context (shared by the STATE_FETCH_REQ /
        # STATE_MEM_WAIT bus-transaction states in clock(); each memory
        # instruction's case in execute() fills these fields directly)
        self.mem_dir = None
        self.mem_addr = 0
        self.mem_wdata = 0
        self.mem_dest_reg = None
        self.mem_words = 1
        self.mem_next_state = "FETCH_INSTRUCTION"
        self.mem_on_complete = None

        # push/pop engine context (shared by the STATE_CALL_PUSH_* /
        # STATE_RET_POP_* states in clock(); each instruction's case in
        # execute() fills these fields directly)
        self.push_lo = 0
        self.push_hi = 0
        self.push_two_bytes = False
        self.push_sp = 0
        self.push_next_state = "FETCH_INSTRUCTION"
        self.push_after_pc = None

        self.pop_num_bytes = 1
        self.pop_dest_reg = None
        self.pop_dest_is_pc = False
        self.pop_next_state = "FETCH_INSTRUCTION"
        self.pop_extra = None
        self.pop_base_sp = 0
        self.pop_count = 0
        self.pop_byte1 = 0

        # LPM engine context
        self.lpm_addr = 0
        self.lpm_dest = 0
        self.lpm_postinc = False

        # SPM write-engine context (page erase / page write to program memory)
        self.spm_base = 0      # first word address of the page being written
        self.spm_idx = 0       # word index within the page (0..PAGE_SIZE_WORDS-1)
        self.spm_mode = None   # 'erase' -> write 0xFFFF, 'write' -> write temp buffer

        # SBI/CBI/SBIC/SBIS engine context
        self.io_addr = 0
        self.io_bit = 0
        self.io_op = None
        self.io_val = 0

    # -----------------------------------------------------------------
    # Master multicycle FSM
    # -----------------------------------------------------------------
    def clock(self):

        match self.state:

            case "STATE_RESET":
                self.pc = self.reset_address
                self.databyteNb = 0
                self.state = "FETCH_INSTRUCTION"

            # ---------------- FETCH ----------------
            case "FETCH_INSTRUCTION":
                self.ins_mem.read.prepare(1)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.pc)
                self.state = "WAIT_FETCH_INSTRUCTION"

            case "WAIT_FETCH_INSTRUCTION":
                self.ins_mem.read.prepare(1)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.pc)
                if self.ins_mem.resp.get() == 1:
                    self.ins = self.ins_mem.read_data.get()
                    self.opp = ins_to_str(self.ins)
                    self.last_pc = self.pc
                    if self.opp in TWO_WORD_OPS:
                        self.state = "STATE_FETCH_OP2_REQ"
                    else:
                        self.state = "STATE_DECODE_EXEC"

            case "STATE_FETCH_OP2_REQ":
                self.ins_mem.read.prepare(1)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.pc + 1)
                self.state = "STATE_FETCH_OP2_WAIT"

            case "STATE_FETCH_OP2_WAIT":
                self.ins_mem.read.prepare(1)
                self.ins_mem.address.prepare(self.pc + 1)
                if self.ins_mem.resp.get() == 1:
                    self.ins2 = self.ins_mem.read_data.get()
                    self.state = "STATE_DECODE_EXEC"

            # ---------------- DECODE / EXECUTE ----------------
            case "STATE_DECODE_EXEC":
                self.execute()
                # Simple (single cycle) instructions leave self.state untouched;
                # multicycle instructions redirect self.state themselves inside
                # execute() (to STATE_FETCH_REQ, STATE_CALL_PUSH_L, etc.) and
                # must not be overridden here.
                if self.state == "STATE_DECODE_EXEC":
                    self.state = "FETCH_INSTRUCTION"

            # ---------------- GENERIC 1-BYTE DATA MEMORY ENGINE ----------------
            case "STATE_FETCH_REQ":
                if self.mem_dir == 'read':
                    self.mem.read.prepare(1)
                    self.mem.write.prepare(0)
                else:
                    self.mem.read.prepare(0)
                    self.mem.write.prepare(1)
                    self.mem.write_data.prepare(self.mem_wdata)
                self.mem.address.prepare(self.mem_addr)
                self.mem.instype.prepare(1)
                self.state = "STATE_MEM_WAIT"

            case "STATE_MEM_WAIT":
                self.mem.address.prepare(self.mem_addr)
                if self.mem_dir == 'read':
                    self.mem.read.prepare(1)
                    self.mem.write.prepare(0)
                else:
                    self.mem.write.prepare(1)
                    self.mem.read.prepare(0)
                    self.mem.write_data.prepare(self.mem_wdata)

                if self.mem.resp.get() == 1:
                    if self.mem_dir == 'read':
                        data = self.mem.read_data.get()
                        if self.mem_dest_reg is not None:
                            self.reg[self.mem_dest_reg] = data & 0xFF
                    self.mem.read.prepare(0)
                    self.mem.write.prepare(0)
                    self.mem.instype.prepare(0)

                    self.pc += self.mem_words

                    if self.mem_on_complete is not None:
                        self.mem_on_complete()

                    self.state = self.mem_next_state

            # ---------------- INDIRECT LD/ST ADDRESS PHASE ----------------
            case "STATE_INDIRECT_LOAD" | "STATE_INDIRECT_STORE":
                # Address computation happens synchronously inside execute()
                # right before entering this state; this state simply hands
                # off to the generic byte engine. Kept as a distinct named
                # state so the pointer-register side effects (pre-dec /
                # post-inc / +q offset) are visibly a separate FSM phase.
                self.state = "STATE_FETCH_REQ"

            # ---------------- PUSH ENGINE (CALL/RCALL/ICALL/PUSH) ----------------
            case "STATE_CALL_PUSH_L":
                self.mem.write.prepare(1)
                self.mem.read.prepare(0)
                self.mem.address.prepare(self.push_sp)
                self.mem.write_data.prepare(self.push_lo)
                if self.mem.resp.get() == 1:
                    if self.push_two_bytes:
                        # settle cycle: the address/write-data change from the
                        # low-byte write to the high-byte write, so give the
                        # bus a dedicated request-only cycle before sampling
                        # resp again - checking resp in the same cycle the
                        # address changes would still reflect the low-byte
                        # write's (stale) response.
                        self.state = "STATE_CALL_PUSH_H_REQ"
                    else:
                        self.mem.write.prepare(0)
                        newSP = (self.push_sp - 1) & 0xFFFF
                        self.SPH = (newSP >> 8) & 0xFF
                        self.SPL = newSP & 0xFF
                        if self.push_after_pc is not None:
                            self.pc = self.push_after_pc
                        self.state = self.push_next_state

            case "STATE_CALL_PUSH_H_REQ":
                addr = (self.push_sp - 1) & 0xFFFF
                self.mem.write.prepare(1)
                self.mem.read.prepare(0)
                self.mem.address.prepare(addr)
                self.mem.write_data.prepare(self.push_hi)
                self.state = "STATE_CALL_PUSH_H"

            case "STATE_CALL_PUSH_H":
                addr = (self.push_sp - 1) & 0xFFFF
                self.mem.write.prepare(1)
                self.mem.read.prepare(0)
                self.mem.address.prepare(addr)
                self.mem.write_data.prepare(self.push_hi)
                if self.mem.resp.get() == 1:
                    self.mem.write.prepare(0)
                    newSP = (self.push_sp - 2) & 0xFFFF
                    self.SPH = (newSP >> 8) & 0xFF
                    self.SPL = newSP & 0xFF
                    if self.push_after_pc is not None:
                        self.pc = self.push_after_pc
                    self.state = self.push_next_state

            # ---------------- POP ENGINE (RET/RETI/POP) ----------------
            case "STATE_RET_POP_H":
                addr = (self.pop_base_sp + self.pop_count + 1) & 0xFFFF
                self.mem.read.prepare(1)
                self.mem.write.prepare(0)
                self.mem.address.prepare(addr)
                if self.mem.resp.get() == 1:
                    data = self.mem.read_data.get()
                    self.pop_count += 1
                    if self.pop_num_bytes == 1:
                        # ---- inlined single-byte pop finish (POP Rd) ----
                        self.mem.read.prepare(0)
                        new_sp = (self.pop_base_sp + self.pop_count) & 0xFFFF
                        self.SPH = (new_sp >> 8) & 0xFF
                        self.SPL = new_sp & 0xFF
                        if self.pop_dest_reg is not None:
                            self.reg[self.pop_dest_reg] = data & 0xFF
                        self.pc += 1
                        if self.pop_extra is not None:
                            self.pop_extra()
                        self.state = self.pop_next_state
                    else:
                        self.pop_byte1 = data
                        # settle cycle: same reasoning as STATE_CALL_PUSH_H_REQ
                        # above - the address is about to change from the
                        # high-byte to the low-byte location, so give the bus
                        # a dedicated request-only cycle first.
                        self.state = "STATE_RET_POP_L_REQ"

            case "STATE_RET_POP_L_REQ":
                addr = (self.pop_base_sp + self.pop_count + 1) & 0xFFFF
                self.mem.read.prepare(1)
                self.mem.write.prepare(0)
                self.mem.address.prepare(addr)
                self.state = "STATE_RET_POP_L"

            case "STATE_RET_POP_L":
                addr = (self.pop_base_sp + self.pop_count + 1) & 0xFFFF
                self.mem.read.prepare(1)
                self.mem.write.prepare(0)
                self.mem.address.prepare(addr)
                if self.mem.resp.get() == 1:
                    data = self.mem.read_data.get()
                    self.pop_count += 1
                    # ---- inlined two-byte pop finish (RET/RETI) ----
                    self.mem.read.prepare(0)
                    new_sp = (self.pop_base_sp + self.pop_count) & 0xFFFF
                    self.SPH = (new_sp >> 8) & 0xFF
                    self.SPL = new_sp & 0xFF
                    if self.pop_dest_is_pc:
                        self.pc = ((self.pop_byte1 & 0xFF) << 8) | (data & 0xFF)
                    else:
                        if self.pop_dest_reg is not None:
                            self.reg[self.pop_dest_reg] = self.pop_byte1 & 0xFF
                        self.pc += 1
                    if self.pop_extra is not None:
                        self.pop_extra()
                    self.state = self.pop_next_state

            # ---------------- LPM ENGINE ----------------
            case "STATE_LPM_REQ":
                # program memory is behind the ins_mem interface; issue a
                # word read at the byte address >> 1, exactly like a fetch
                self.ins_mem.read.prepare(1)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.lpm_addr >> 1)
                self.state = "STATE_LPM_WAIT"

            case "STATE_LPM_WAIT":
                self.ins_mem.read.prepare(1)
                self.ins_mem.address.prepare(self.lpm_addr >> 1)
                if self.ins_mem.resp.get() == 1:
                    word = self.ins_mem.read_data.get()
                    if self.lpm_addr & 0b1:
                        self.reg[self.lpm_dest] = (word >> 8) & 0xFF
                    else:
                        self.reg[self.lpm_dest] = word & 0xFF

                    if self.lpm_postinc:
                        newaddr = (self.lpm_addr + 1) & 0xFFFF
                        self.reg[30] = newaddr & 0xFF
                        self.reg[31] = (newaddr >> 8) & 0xFF

                    self.ins_mem.read.prepare(0)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    suffix = '+' if self.lpm_postinc else ''
                    print(f'LPM R{self.lpm_dest}, Z{suffix}\t\tR{self.lpm_dest}={self.reg[self.lpm_dest]:02X} [Z]={self.lpm_addr:04X}')

            # ---------------- SPM WRITE ENGINE (page erase / page write) ----------------
            # Writes one word per REQ/WAIT pair to program memory over the
            # ins_mem interface, PAGE_SIZE_WORDS times.
            #   'erase' mode writes 0xFFFF, 'write' mode writes the temp buffer.
            case "STATE_SPM_WRITE_REQ":
                self.ins_mem.write.prepare(1)
                self.ins_mem.read.prepare(0)
                self.ins_mem.address.prepare(self.spm_base + self.spm_idx)
                if self.spm_mode == 'erase':
                    self.ins_mem.write_data.prepare(0xFFFF)
                else:
                    self.ins_mem.write_data.prepare(self.temp_page_buffer[self.spm_idx])
                self.state = "STATE_SPM_WRITE_WAIT"

            case "STATE_SPM_WRITE_WAIT":
                self.ins_mem.write.prepare(1)
                self.ins_mem.read.prepare(0)
                self.ins_mem.address.prepare(self.spm_base + self.spm_idx)
                if self.spm_mode == 'erase':
                    self.ins_mem.write_data.prepare(0xFFFF)
                else:
                    self.ins_mem.write_data.prepare(self.temp_page_buffer[self.spm_idx])
                if self.ins_mem.resp.get() == 1:
                    self.spm_idx += 1
                    if self.spm_idx < self.PAGE_SIZE_WORDS:
                        self.state = "STATE_SPM_WRITE_REQ"
                    else:
                        self.ins_mem.write.prepare(0)
                        if self.spm_mode == 'write':
                            # hardware auto-erases the temp buffer after Page Write
                            self.temp_page_buffer = [0xFFFF] * self.PAGE_SIZE_WORDS
                        self.pc += 1
                        self.state = "FETCH_INSTRUCTION"

            # ---------------- I/O BIT READ-MODIFY-WRITE / TEST ----------------
            case "STATE_IO_BIT_READ":
                self.mem.read.prepare(1)
                self.mem.write.prepare(0)
                self.mem.address.prepare(self.io_addr)
                if self.mem.resp.get() == 1:
                    val = self.mem.read_data.get()
                    bitval = (val >> self.io_bit) & 0b1

                    if self.io_op == 'SBI':
                        self.mem.read.prepare(0)
                        self.io_val = val | (1 << self.io_bit)
                        self.state = "STATE_IO_BIT_WRITE_REQ"
                        print(f'SBI {self.io_addr:02X}, {self.io_bit}\t\t[{self.io_addr:04X}]={self.io_val & 0xFF:02X}')
                    elif self.io_op == 'CBI':
                        self.mem.read.prepare(0)
                        self.io_val = val & ~(1 << self.io_bit)
                        self.state = "STATE_IO_BIT_WRITE_REQ"
                        print(f'CBI {self.io_addr:02X}, {self.io_bit}\t\t[{self.io_addr:04X}]={self.io_val & 0xFF:02X}')
                    elif self.io_op == 'SBIC':
                        self.mem.read.prepare(0)
                        if bitval == 0:
                            self.state = "STATE_SKIP_FETCH_REQ"
                        else:
                            self.pc += 1
                            self.state = "FETCH_INSTRUCTION"
                        print(f'SBIC {self.io_addr:02X}, {self.io_bit}\t\tskip={bitval == 0}')
                    elif self.io_op == 'SBIS':
                        self.mem.read.prepare(0)
                        if bitval == 1:
                            self.state = "STATE_SKIP_FETCH_REQ"
                        else:
                            self.pc += 1
                            self.state = "FETCH_INSTRUCTION"
                        print(f'SBIS {self.io_addr:02X}, {self.io_bit}\t\tskip={bitval == 1}')

            case "STATE_IO_BIT_WRITE_REQ":
                self.mem.write.prepare(1)
                self.mem.read.prepare(0)
                self.mem.address.prepare(self.io_addr)
                self.mem.write_data.prepare(self.io_val & 0xFF)
                self.state = "STATE_IO_BIT_WRITE"

            case "STATE_IO_BIT_WRITE":
                self.mem.write.prepare(1)
                self.mem.read.prepare(0)
                self.mem.address.prepare(self.io_addr)
                self.mem.write_data.prepare(self.io_val & 0xFF)
                if self.mem.resp.get() == 1:
                    self.mem.write.prepare(0)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"

            # ---------------- SKIP LOOKAHEAD (CPSE/SBRC/SBRS/SBIC/SBIS) ----------------
            case "STATE_SKIP_FETCH_REQ":
                self.ins_mem.read.prepare(1)
                self.ins_mem.write.prepare(0)
                self.ins_mem.address.prepare(self.pc + 1)
                self.state = "STATE_SKIP_FETCH_WAIT"

            case "STATE_SKIP_FETCH_WAIT":
                self.ins_mem.read.prepare(1)
                self.ins_mem.address.prepare(self.pc + 1)
                if self.ins_mem.resp.get() == 1:
                    next_ins = ins_to_str(self.ins_mem.read_data.get())
                    if next_ins in TWO_WORD_OPS:
                        self.pc += 3  # skip a 2-word instruction
                    else:
                        self.pc += 2  # skip a 1-word instruction
                    self.state = "FETCH_INSTRUCTION"

    # -----------------------------------------------------------------
    # data-space address (LS view) -> internal attribute name, for the
    # CPU-internal I/O registers that are serviced without a bus transaction
    # -----------------------------------------------------------------
    INTERNAL_IO_REGS = {
        0x54: 'MCUSR',
        0x55: 'MCUCR',
        0x57: 'SPMCSR',
        0x5D: 'SPL',
        0x5E: 'SPH',
        0x5F: 'SREG',
        0x60: 'WDTCSR',
    }

    def execute(self):
        # self.opp was already decoded in WAIT_FETCH_INSTRUCTION
        match self.opp: 
            case 'ADD':
                self.Rr = ((self.ins>>8)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>9)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res = (self.reg[self.Rd] + self.reg[self.Rr]) &0xFF

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if (Rd7 & Rr7 )|( Rr7 & (not R7))|((not R7) & Rd7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & Rr7 & (not R7)) | ((not Rd7) & (not Rr7) & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if (Rd3 & Rr3)|(Rr3 & (not R3))|((not R3) & Rd3):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                
                self.reg[self.Rd] =  self.res

                self.pc += 1
                print(f'ADD R{self.Rd}, R{self.Rr}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'ADC': # there may be a problem with this but I don't know what is the problem

                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>4) & 0x1F)
                Rd7 = (self.reg[self.Rd]>>7)&0b1
                Rr7 = (self.reg[self.Rr]>>7)&0b1

                self.res =  (self.reg[self.Rd] + self.reg[self.Rr] + (self.SREG & 0b1)) &0xFF
                Rd3 = (self.reg[self.Rd]>>3)&0b1
                Rr3 = (self.reg[self.Rr]>>3)&0b1

                R7  = (self.res>>7)&0b1
                R3  = (self.res>>3)&0b1

                #H
                if ((Rd3 & Rr3)|(Rr3 & (1 - R3))|(Rd3 & (1 - R3))):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)
                
                #self.SREG &= ~(1<<5) # This is a bipas 

                #C
                if (Rd7 & Rr7 )|( Rr7 & (not R7))|((not R7) & Rd7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)

                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                #V
                V = ((Rd7 & Rr7 & (not R7)) | ((not Rd7) & (not Rr7) & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] = self.res & 0xFF

                self.pc += 1
                print(f'ADC R{self.Rd}, R{self.Rr}\t\tR{self.Rd}={self.reg[self.Rd]:02X}\t{self.SREG:08b}')
            case 'ADIW':
                self.K = (((self.ins>>6)&0b11)<<4)|(self.ins & 0xF)
                self.Rd = 24 + (((self.ins >> 4) & 0b11) * 2)
                self.res =  ((self.reg[self.Rd+1]<<8|self.reg[self.Rd])  +  self.K) & 0xFFFF

                Rdh7 = ((self.reg[self.Rd+1]>>7)&0b1)
                R15 = ((self.res>>15)&0b1)

                #C
                if (not R15) & Rdh7:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z
                N = (self.res == 0)
                if N == 1:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R15 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = (not Rdh7) & R15
                if V == 1 :
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if (N)^(V):
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] =  self.res & 0xFF
                self.reg[self.Rd+1] =  (self.res>>8) & 0xFF

                self.pc += 1
                print(f'ADIW R{self.Rd+1}:R{self.Rd}, {self.K}\t\tR{self.Rd+1}:R{self.Rd}={self.res & 0xFFFF:04X}\t{self.SREG:08b}')
            case 'SUB':

                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  (self.reg[self.Rd] - self.reg[self.Rr]) & 0xFF


                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #C
                if ((not Rd7) & Rr7 )|( Rr7 & R7)|( R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & (not Rr7) & (not R7)) | ((not Rd7) & Rr7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1

                if ((not Rd3) & Rr3)|(Rr3 & R3)|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res & 0xFF

                self.pc += 1
                print(f'SUB R{self.Rd}, R{self.Rr}\t\tR{self.Rd}={self.reg[self.Rd]:02X}\t{self.SREG:08b}')
            case 'SUBI':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = 16 + ((self.ins >> 4) & 0xF)
                self.res = self.reg[self.Rd] - self.K

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                K7= ((self.K&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #C
                if ((not Rd7) & K7 )|( K7 & R7)|( R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & (not K7) & (not R7)) | ((not Rd7) & K7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                K3= ((self.K&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1

                if ((not Rd3) & K3)|(K3 & R3)|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)



                self.reg[self.Rd] =  self.res & 0xFF

                self.pc += 1
                print(f'SUBI R{self.Rd}, {self.K}\t\tR{self.Rd}={self.reg[self.Rd]:02X}\t{self.SREG:08b}')
            case 'SBC':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] - self.reg[self.Rr] - (self.SREG & 0b1)

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #C
                if ((not Rd7) & Rr7 )|( Rr7 & R7)|( R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                current_Z = (self.SREG >> 1) & 0b1
                if (self.res&0xFF == 0) and current_Z == 1:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & (not Rr7) & (not R7)) | ((not Rd7) & Rr7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1

                if ((not Rd3) & Rr3)|(Rr3 & R3)|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res & 0xFF
                self.pc += 1
                print(f'SBC R{self.Rd}, R{self.Rr}\t\tR{self.Rd}={self.reg[self.Rd]:02X}\t{self.SREG:08b}')
            case 'SBCI':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] - self.K - (self.SREG & 0b1)

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                K7= ((self.K&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #C
                if ((not Rd7) & K7 )|( K7 & R7)|( R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                current_Z = (self.SREG >> 1) & 0b1
                if (self.res&0xFF == 0) and current_Z == 1:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & (not K7) & (not R7)) | ((not Rd7) & K7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                K3= ((self.K&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1

                if ((not Rd3) & K3)|(K3 & R3)|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res & 0xFF
                self.pc += 1
                print(f'SBCI R{self.Rd}, {self.K}\t\tR{self.Rd}={self.reg[self.Rd]:02X}\t{self.SREG:08b}')
            case 'SBIW':
                self.K = (((self.ins>>6)&0b11)<<4)|(self.ins & 0xF)
                self.Rd = 24 + (((self.ins>>4)&0b11) * 2)
                self.res =  ((self.reg[self.Rd+1]<<8|self.reg[self.Rd]) -  self.K) & 0xFFFF

                Rdh7= ((self.reg[self.Rd+1]&0xFF)>>7)&0b1
                R15 = ((self.res>>15)&0b1)

                #C
                if R15 & (not Rdh7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if (self.res == 0):
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R15 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V

                V = (not R15) & Rdh7 
                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R15:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)


                self.reg[self.Rd] =  self.res&0xFF
                self.reg[self.Rd+1] = (self.res>>8)&0xFF 

                self.pc += 1
                print(f'SBIW R{self.Rd+1}:R{self.Rd}, {self.K}\t\tR{self.Rd+1}:R{self.Rd}={self.res & 0xFFFF:04X}\t{self.SREG:08b}')
            case 'AND':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] & self.reg[self.Rr]


                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res

                self.pc += 1
                print(f'AND R{self.Rd}, R{self.Rr}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'ANDI':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] & self.K 

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  


                self.reg[self.Rd] =  self.res
                self.pc += 1
                print(f'ANDI R{self.Rd}, {self.K}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'OR':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] | self.reg[self.Rr]

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  



                self.reg[self.Rd] =  self.res

                self.pc += 1
                print(f'OR R{self.Rd}, R{self.Rr}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'ORI':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] | self.K 

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res
                self.pc += 1
                print(f'ORI R{self.Rd}, {self.K}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'EOR':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] ^ self.reg[self.Rr]

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res

                self.pc += 1
                print(f'EOR R{self.Rd}, R{self.Rr}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'COM':
                self.Rd = ((self.ins>>4) & 0x1F)
                self.res = 0xFF - self.reg[self.Rd] 

                R7 =  ((self.res&0xFF)>>7)&0b1
                self.SREG |= (1<<0) #flag C to 1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res

                self.pc += 1
                print(f'COM R{self.Rd}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'NEG':
                self.Rd = ((self.ins>>4) & 0x1F)
                self.res = (0x00 - self.reg[self.Rd]) & 0xFF 

                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if self.res != 0:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                
                #V
                V = (self.res == 0x80)
                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd])>>3)&0b1
                R3 = (self.res>>3)&0b1
                if (1- Rd3) | R3 :
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res
                self.pc += 1
                print(f'NEG R{self.Rd}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'SBR':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] | self.K 

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                N = (R7 == 1)
                if N == 1 : 
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                self.SREG &= ~(1<<3) #flag V to 0

                #S 
                if N == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)  

                self.reg[self.Rd] =  self.res
                self.pc += 1
                print(f'SBR R{self.Rd}, {self.K}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'CBR':
                self.K =  ((self.ins>>4)&0xF0)|(self.ins&0xF)
                self.Rd = ((self.ins>>4) & 0xF) + 16
                self.res =  self.reg[self.Rd] & ((~self.K) & 0xFF)

                R7 = ((self.res&0xFF)>>7)&0b1
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                self.SREG &= ~(1<<3)
                #S = N ^ V = N
                if R7 == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] =  self.res 
                self.pc += 1
                print(f'CBR R{self.Rd}, {self.K}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'INC':
                self.Rd = ((self.ins>>4) & 0x1F)
                self.res = (self.reg[self.Rd] + 1) & 0xFF
                
                R7 =  ((self.res&0xFF)>>7)&0b1

                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                
                #V
                V = (self.res == 0x80)
                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)



                self.reg[self.Rd] =  self.res 
                self.pc += 1
                print(f'INC R{self.Rd}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'DEC':
                self.Rd = ((self.ins>>4) & 0x1F)
                self.res = (self.reg[self.Rd] - 1) & 0xFF

                R7 =  ((self.res&0xFF)>>7)&0b1
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                
                #V
                V = (self.res == 0x7F)
                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] =  self.res
                self.pc += 1
                print(f'DEC R{self.Rd}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'SER':
                self.Rd = ((self.ins>>4)&0b1111) + 16
                self.reg[self.Rd] = 0xFF
        

                self.pc +=1 
                print(f'SER R{self.Rd}\t\tR{self.Rd}={self.reg[self.Rd]:02X}\t{self.SREG:08b}')
            case 'MUL':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] * self.reg[self.Rr]

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1] = (self.res>>8) &0xFF
                self.reg[0] = self.res & 0xFF

                self.pc += 1
                print(f'MUL R{self.Rd}, R{self.Rr}\t\tR1:R0={self.res & 0xFFFF:04X}\t{self.SREG:08b}')
            case 'MULS': 
                self.Rr = (self.ins & 0xF) + 16
                self.Rd = ((self.ins>>4) & 0xF) + 16

                val_Rd = self.reg[self.Rd] & 0xFF
                val_Rr = self.reg[self.Rr] & 0xFF

                if val_Rd >= 128:
                    val_Rd -=256
                if val_Rr >= 128:
                    val_Rr -=256

                self.res =  (val_Rd * val_Rr) & 0xFFFF

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= (self.res>>8) & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
                print(f'MULS R{self.Rd}, R{self.Rr}\t\tR1:R0={self.res & 0xFFFF:04X}\t{self.SREG:08b}')
            case 'MULSU':
                self.Rr = (self.ins & 0b111) + 16
                self.Rd = ((self.ins>>4) & 0b111) + 16

                val_Rd = self.reg[self.Rd] & 0xFF
                val_Rr = self.reg[self.Rr] & 0xFF   # unsigned

                if val_Rd >= 128:
                    val_Rd -=256

                self.res =  (val_Rd * val_Rr) & 0xFFFF

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= self.res>>8 & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
                print(f'MULSU R{self.Rd}, R{self.Rr}\t\tR1:R0={self.res & 0xFFFF:04X}\t{self.SREG:08b}')
            case 'FMUL':
                self.Rr = (self.ins & 0b111) + 16
                self.Rd = ((self.ins>>4) & 0b111) + 16
                self.res =  (self.reg[self.Rd]&0xFF) * (self.reg[self.Rr]&0xFF)

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                self.res = (self.res <<1) &0xFFFF

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= self.res>>8 & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
                print(f'FMUL R{self.Rd}, R{self.Rr}\t\tR1:R0={self.res & 0xFFFF:04X}\t{self.SREG:08b}')
            case 'FMULS': 
                self.Rr = (self.ins & 0b111) + 16
                self.Rd = ((self.ins>>4) & 0b111) + 16
                val_Rd = self.reg[self.Rd] & 0xFF
                val_Rr = self.reg[self.Rr] & 0xFF

                if val_Rd >= 128:
                    val_Rd -=256
                if val_Rr >= 128:
                    val_Rr -=256

                self.res =  (val_Rd * val_Rr) & 0xFFFF

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                self.res = (self.res <<1) &0xFFFF

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= (self.res>>8) & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
                print(f'FMULS R{self.Rd}, R{self.Rr}\t\tR1:R0={self.res & 0xFFFF:04X}\t{self.SREG:08b}')
            case 'FMULSU':
                self.Rr = (self.ins & 0b111) + 16 
                self.Rd = ((self.ins>>4) & 0b111) + 16

                val_Rd = self.reg[self.Rd] & 0xFF
                val_Rr = self.reg[self.Rr] & 0xFF   # unsigned

                if val_Rd >= 128:
                    val_Rd -=256

                self.res =  (val_Rd * val_Rr) & 0xFFFF

                R15 = (self.res>>15) & 0b1

                if R15 == 1:
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0) 

                self.res = (self.res <<1) &0xFFFF

                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.reg[1]= (self.res>>8) & 0xFF
                self.reg[0]= self.res & 0xFF

                self.pc += 1
                print(f'FMULSU R{self.Rd}, R{self.Rr}\t\tR1:R0={self.res & 0xFFFF:04X}\t{self.SREG:08b}')
            case 'RJMP':
                self.K = self.ins & 0xFFF
                if self.K & 0x800:
                    self.K -= 0x1000   # sign-extend 12-bit two's complement
                self.pc = (self.pc + self.K + 1) & 0xFFFF
                soff = self.K
                print(f'RJMP {soff}')
            case 'IJMP':
                self.pc  = (self.reg[30]&0xFF) | ((self.reg[31]&0xFF)<<8)
                print(f'IJMP {self.pc:04X}')
            case 'JMP':
                self.K = (((self.ins>>4)&0x1F)<<17)|((self.ins&0b1)<<16)|self.ins2
                self.pc = self.K
                add = self.K
                print(f'JMP {add:04X}')
            case 'RCALL':
                self.K = self.ins&0xFFF
                #handeling negative K numbers
                if self.K>>11 == 1:
                    self.K = -(((~self.K)&0xFFF) + 1)

                ret_addr = (self.pc + 1) & 0xFFFF
                target = (self.pc + self.K + 1) & 0xFFFF

                # ---- inlined push_start(value16=ret_addr, after_push_pc=target) ----
                SP = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
                self.push_sp = SP
                self.push_next_state = "FETCH_INSTRUCTION"
                self.push_after_pc = target
                self.push_lo = ret_addr & 0xFF
                self.push_hi = (ret_addr >> 8) & 0xFF
                self.push_two_bytes = True
                self.state = "STATE_CALL_PUSH_L"

                K = self.ins & 0xFFF
                ra = ret_addr
                self.SP = (SP - 2) & 0xFFFF
                print(f'RCALL {K:03X}\t\t[{(self.SP+2)&0xFFFF:04X}]={(ra>>8):02X} [{(self.SP+1)&0xFFFF:04X}]={ra&0xFF:02X}')
            case 'ICALL':
                target = (self.reg[30]&0xFF) | ((self.reg[31]&0xFF)<<8)
                ret_addr = (self.pc + 1) & 0xFFFF

                # ---- inlined push_start(value16=ret_addr, after_push_pc=target) ----
                SP = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
                self.push_sp = SP
                self.push_next_state = "FETCH_INSTRUCTION"
                self.push_after_pc = target
                self.push_lo = ret_addr & 0xFF
                self.push_hi = (ret_addr >> 8) & 0xFF
                self.push_two_bytes = True
                self.state = "STATE_CALL_PUSH_L"

                ra = ret_addr
                self.SP = (SP - 2) & 0xFFFF
                print(f'ICALL\t\t\t[{(self.SP+2)&0xFFFF:04X}]={(ra>>8):02X} [{(self.SP+1)&0xFFFF:04X}]={ra&0xFF:02X}')
            case 'CALL':
                target = (((self.ins>>4)&0x1F)<<17)|((self.ins&0b1)<<16)|self.ins2
                ret_addr = (self.pc + 2) & 0xFFFF

                # ---- inlined push_start(value16=ret_addr, after_push_pc=target) ----
                SP = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
                self.push_sp = SP
                self.push_next_state = "FETCH_INSTRUCTION"
                self.push_after_pc = target
                self.push_lo = ret_addr & 0xFF
                self.push_hi = (ret_addr >> 8) & 0xFF
                self.push_two_bytes = True
                self.state = "STATE_CALL_PUSH_L"

                add = target
                ra = ret_addr
                self.SP = (SP - 2) & 0xFFFF
                print(f'CALL {add:04X}\t\t[{(self.SP+2)&0xFFFF:04X}]={(ra>>8):02X} [{(self.SP+1)&0xFFFF:04X}]={ra&0xFF:02X}')
            case 'RET':
                # ---- inlined pop_start(num_bytes=2, dest_is_pc=True) ----
                self.pop_num_bytes = 2
                self.pop_dest_reg = None
                self.pop_dest_is_pc = True
                self.pop_next_state = "FETCH_INSTRUCTION"
                self.pop_extra = None
                self.pop_base_sp = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
                self.pop_count = 0
                self.state = "STATE_RET_POP_H"

                self.SP = (self.pop_base_sp + 2) & 0xFFFF
                print(f'RET\t\t\t\t[{self.SPH_addr_LS:04X}]={(self.SP>>8):02X} [{self.SPL_addr_LS:04X}]={(self.SP & 0xFF):02X}')
            case 'RETI':## return from interrupt 
                def _set_interrupt_flag():
                    self.SREG |= (1<<7)

                # ---- inlined pop_start(num_bytes=2, dest_is_pc=True, extra_on_complete=_set_interrupt_flag) ----
                self.pop_num_bytes = 2
                self.pop_dest_reg = None
                self.pop_dest_is_pc = True
                self.pop_next_state = "FETCH_INSTRUCTION"
                self.pop_extra = _set_interrupt_flag
                self.pop_base_sp = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
                self.pop_count = 0
                self.state = "STATE_RET_POP_H"

                self.SP = (self.pop_base_sp + 2) & 0xFFFF
                print(f'RETI\t\t\t[{self.SPH_addr_LS:04X}]={(self.SP>>8):02X} [{self.SPL_addr_LS:04X}]={(self.SP & 0xFF):02X}')
            case 'CPSE':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)

                if self.reg[self.Rr] == self.reg[self.Rd]:
                    self.state = "STATE_SKIP_FETCH_REQ"
                else:
                    self.pc += 1
                print(f'CPSE R{self.Rd}, R{self.Rr}\t\tskip={self.reg[self.Rr] == self.reg[self.Rd]}')
            case 'CP':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  self.reg[self.Rd] - self.reg[self.Rr] 

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if ((not Rd7) & Rr7 )|( Rr7 & R7)|(R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)

                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                #V
                V = ((Rd7 & (not Rr7) & (not R7)) | ((not Rd7) & Rr7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if ((not Rd3) & Rr3)|(Rr3 & (not R3))|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.pc += 1
                print(f'CP R{self.Rd}, R{self.Rr}\t\t{self.SREG:08b}')
            case 'CPC':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  (self.reg[self.Rd] - self.reg[self.Rr] - (self.SREG & 0b1)) & 0xFF

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if ((not Rd7) & Rr7 )|( Rr7 & R7)|(R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)

                #Z 
                if (self.res == 0) and (((self.SREG>>1)&0b1)) :
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)

                #V
                V = ((Rd7 & (not Rr7) & (not R7)) | ((not Rd7) & Rr7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)

                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if ((not Rd3) & Rr3)|(Rr3 & R3 )|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.pc += 1
                print(f'CPC R{self.Rd}, R{self.Rr}\t\t{self.SREG:08b}')
            case 'CPI':
                
                self.K = (self.ins&0xF)|(((self.ins>>8)&0xF)<<4)
                self.Rd = ((self.ins>>4)&0xF) + 16
                self.res = (self.reg[self.Rd]-self.K) & 0xFF


                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                K7= ((self.K&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1


                #C
                if ((not Rd7) & K7 )|( K7 & R7)|(R7 & (not Rd7)):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)


                #Z 
                if (self.res == 0):
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)


                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)


                #V
                V = ((Rd7 & (not K7) & (not R7)) | ((not Rd7) & K7 & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)


                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)


                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                K3= ((self.K&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1


                if ((not Rd3) & K3)|(K3 & R3 )|(R3 & (not Rd3)):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)


                self.pc+=1
                print(f'CPI R{self.Rd}, {self.K:02X}\t\t{self.SREG:08b}')
            case 'SBRC':
                b = self.ins&0b111
                self.A = (self.ins>>4)&0b11111
                if (self.reg[self.A]>>b)&1 == 0:
                    self.state = "STATE_SKIP_FETCH_REQ"
                else:
                    self.pc += 1
                print(f'SBRC R{self.A}, {b}\t\tskip={(self.reg[self.A]>>b)&1 == 0}')
            case 'SBRS':
                b = self.ins&0b111
                self.A = (self.ins>>4)&0b11111
                if (self.reg[self.A]>>b)&1 == 1:
                    self.state = "STATE_SKIP_FETCH_REQ"
                else:
                    self.pc += 1
                print(f'SBRS R{self.A}, {b}\t\tskip={(self.reg[self.A]>>b)&1 == 1}')
            case 'SBIC':
                self.io_addr = ((self.ins>>3)&0b11111) + 0x20
                self.io_bit = self.ins&0b111
                self.io_op = 'SBIC'
                self.state = "STATE_IO_BIT_READ"
            case 'SBIS':
                self.io_addr = ((self.ins>>3)&0b11111) + 0x20
                self.io_bit = self.ins&0b111
                self.io_op = 'SBIS'
                self.state = "STATE_IO_BIT_READ"
            case 'BRBS' | 'BREQ' | 'BRCS' | 'BRMI' | 'BRVS' | 'BRLT' | 'BRHS' | 'BRTS' | 'BRIE':
                # BRBS and its named aliases (BREQ=Z, BRCS=C, BRMI=N, BRVS=V,
                # BRLT=S, BRHS=H, BRTS=T, BRIE=I) are all the exact same
                # encoding - "branch if SREG bit S is set" - just given a
                # friendlier mnemonic by the disassembler/assembler. The bit
                # index S to test is already encoded in the instruction word
                # regardless of which name it decoded to, so all of them are
                # serviced by this single case.
                self.K =  (self.ins>>3)&0b1111111 
                S =  self.ins&0b111

                if (self.K & 0x40):
                    self.K = self.K - 128
                
                if(self.SREG>>S)&1 == 1:
                    self.pc +=  self.K +1
                else:
                    self.pc += 1 
                print(f'{self.opp} {self.K}\t\ttaken={(self.SREG>>S)&1 == 1}')
            case 'BRBC' | 'BRNE' | 'BRCC' | 'BRPL' | 'BRVC' | 'BRGE' | 'BRHC' | 'BRTC' | 'BRID':
                # BRBC and its named aliases (BRNE=Z, BRCC=C, BRPL=N, BRVC=V,
                # BRGE=S, BRHC=H, BRTC=T, BRID=I) - "branch if SREG bit S is
                # clear". Same reasoning as the BRBS group above.
                self.K =  (self.ins>>3)&0b1111111 
                S =  self.ins&0b111

                if (self.K & 0x40):
                    self.K = self.K - 128

                if(self.SREG>>S)&1 == 0:
                    self.pc += self.K + 1
                else:
                    self.pc += 1 
                print(f'{self.opp} {self.K}\t\ttaken={(self.SREG>>S)&1 == 0}')
            case 'SBI': ## set bit in I/O register (read-modify-write)
                self.io_bit = (self.ins & 0b111)
                self.io_addr = ((self.ins>>3)&0x1F) + 0x20
                self.io_op = 'SBI'
                self.state = "STATE_IO_BIT_READ"
            case 'CBI': ## clear bit in I/O register (read-modify-write)
                self.io_bit = (self.ins & 0b111)
                self.io_addr = ((self.ins>>3)&0x1F) + 0x20
                self.io_op = 'CBI'
                self.state = "STATE_IO_BIT_READ"
            case 'LSL':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res = (self.reg[self.Rd] + self.reg[self.Rr]) &0xFF

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if (Rd7 & Rr7 )|( Rr7 & (not R7))|((not R7) & Rd7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & Rr7 & (not R7)) | ((not Rd7) & (not Rr7) & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if (Rd3 & Rr3)|(Rr3 & (not R3))|((not R3) & Rd3):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                
                self.reg[self.Rd] =  self.res

                self.pc += 1
                print(f'LSL R{self.Rd}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'LSR':

                self.Rd =  (self.ins>>4)&0x1F
                
                #C 
                C = self.reg[self.Rd] & 0b1

                if C == 1:
                    self.SREG |= (1 << 0)
                else:
                    self.SREG &= ~(1 << 0)

                self.res = (self.reg[self.Rd]>>1)&0xFF
                
                #Z
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)

                self.SREG &= ~(1<<2) # N is set to 0

                #V
                V = ((self.SREG&0b1)^0)
                if V == 1 :
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                
                #S
                if V == 1:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)


                self.reg[self.Rd] = self.res
                self.pc += 1
                print(f'LSR R{self.Rd}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'ROL':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.res =  (self.reg[self.Rd] + self.reg[self.Rr] + (self.SREG & 0b1)) &0xFF

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                Rr7= ((self.reg[self.Rr]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1
                #C
                if (Rd7 & Rr7 )|( Rr7 & (not R7))|((not R7) & Rd7):
                    self.SREG |= (1<<0)
                else:
                    self.SREG &= ~(1<<0)
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = ((Rd7 & Rr7 & (not R7)) | ((not Rd7) & (not Rr7) & R7))&0b1

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                #H
                Rd3= ((self.reg[self.Rd]&0xFF)>>3)&0b1
                Rr3= ((self.reg[self.Rr]&0xFF)>>3)&0b1
                R3 = ((self.res&0xFF)>>3)&0b1
                if (Rd3 & Rr3)|(Rr3 & (not R3))|((not R3) & Rd3):
                    self.SREG |= (1<<5)
                else:
                    self.SREG &= ~(1<<5)

                self.reg[self.Rd] =  self.res

                self.pc += 1
                print(f'ROL R{self.Rd}\t\tR{self.Rd}={self.res:02X}\t{self.SREG:08b}')
            case 'ROR':
                self.Rd =  (self.ins>>4)&0x1F

                #C 
                C = self.reg[self.Rd] & 0b1

                self.res = (self.reg[self.Rd]>>1 & 0xFF) | (self.SREG&0b1)<<7

                if C == 1:
                    self.SREG |= (1 << 0)
                else:
                    self.SREG &= ~(1 << 0)

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                R7 = ((self.res&0xFF)>>7)&0b1

                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = R7^C

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] = self.res & 0xFF

                self.pc += 1
                print(f'ROR R{self.Rd}\t\tR{self.Rd}={self.reg[self.Rd]:02X}\t{self.SREG:08b}')
            case 'ASR':
                self.Rd =  (self.ins>>4)&0x1F

                #C 
                C = self.reg[self.Rd] & 0b1
                if C == 1:
                    self.SREG |= (1 << 0)
                else:
                    self.SREG &= ~(1 << 0)

                Rd7= ((self.reg[self.Rd]&0xFF)>>7)&0b1
                
                self.res = (self.reg[self.Rd]>>1 & 0xFF) | (Rd7)<<7

                R7 = ((self.res&0xFF)>>7)&0b1
                #Z 
                if self.res == 0:
                    self.SREG |= (1<<1)
                else:
                    self.SREG &= ~(1<<1)
                #N
                if R7 == 1:
                    self.SREG |= (1<<2)
                else:
                    self.SREG &= ~(1<<2)
                #V
                V = R7^C

                if V == 1:
                    self.SREG |= (1<<3)
                else:
                    self.SREG &= ~(1<<3)
                #S
                if V^R7:
                    self.SREG |= (1<<4)
                else:
                    self.SREG &= ~(1<<4)

                self.reg[self.Rd] = self.res & 0xFF

                self.pc += 1
                print(f'ASR R{self.Rd}\t\tR{self.Rd}={self.reg[self.Rd]:02X}\t{self.SREG:08b}')
            case 'SWAP':
                self.Rd = (self.ins>>4)&0x1F
                self.reg[self.Rd]= ((self.reg[self.Rd]&0xF)<<4) | ((self.reg[self.Rd]&0xF0)>>4)

                self.pc += 1
                print(f'SWAP R{self.Rd}\t\tR{self.Rd}={self.reg[self.Rd]:02X}')
            case 'BSET' | 'SEC' | 'SEZ' | 'SEN' | 'SEV' | 'SES' | 'SEH' | 'SET' | 'SEI':
                # BSET and its named single-flag aliases (SEC=C, SEZ=Z,
                # SEN=N, SEV=V, SES=S, SEH=H, SET=T, SEI=I) are the same
                # encoding with the bit index already baked into the word.
                s = (self.ins>>4)&0b111
                self.SREG |=(1<<s) 

                self.pc += 1
                print(f'{self.opp}\t\tSREG={self.SREG:08b}')
            case 'BCLR' | 'CLC' | 'CLZ' | 'CLN' | 'CLV' | 'CLS' | 'CLH' | 'CLT' | 'CLI':
                # BCLR and its named single-flag aliases (CLC=C, CLZ=Z,
                # CLN=N, CLV=V, CLS=S, CLH=H, CLT=T, CLI=I).
                s = (self.ins>>4)&0b111
                self.SREG &= ~(1<<s) 

                self.pc += 1
                print(f'{self.opp}\t\tSREG={self.SREG:08b}')
            case 'BST':
                b = self.ins&0b111
                self.Rd = (self.ins>>4)&0x1F
                bit = (self.reg[self.Rd]>>b)&1

                if bit:
                    self.SREG |= (1<<6)
                else:
                    self.SREG &= ~(1<<6)
 
                self.pc += 1
                print(f'BST R{self.Rd}, {b}\t\tT={bit}')
            case 'BLD':
                b = self.ins&0b111
                self.Rd = (self.ins>>4)&0x1F
                self.reg[self.Rd] &= ~(0b1<<b)
                self.reg[self.Rd] |= ((self.SREG>>6)&1)<<b

                self.pc += 1
                print(f'BLD R{self.Rd}, {b}\t\tR{self.Rd}={self.reg[self.Rd]:02X}')


            case 'MOV':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[self.Rd] =  self.reg[self.Rr]

                self.pc += 1
                print(f'MOV R{self.Rd}, R{self.Rr}\t\tR{self.Rd}={self.reg[self.Rd]:02X}')
            case 'MOVW':
                self.Rr = (self.ins & 0xF) << 1
                self.Rd = ((self.ins>>4) & 0xF) << 1

                self.reg[self.Rd+1] = self.reg[self.Rr+1]
                self.reg[self.Rd] =  self.reg[self.Rr]

                self.pc += 1
                print(f'MOVW R{self.Rd}, R{self.Rr}\t\tR{self.Rd+1}:R{self.Rd}={self.reg[self.Rd+1]:02X}{self.reg[self.Rd]:02X}')
            case 'LDI':
            
                self.Rd = ((self.ins>>4)&0xF)+16
                self.K = (self.ins&0xF)|((((self.ins)>>8)&0xF)<<4)

                self.reg[self.Rd] = self.K 
                self.pc += 1
                print(f'LDI R{self.Rd}, {self.K:02X}\t\tR{self.Rd}={self.reg[self.Rd]:02X}')

            # ---------------------------------------------------------------
            # Indirect LD/ST family - one distinct case per instruction.
            # Each case computes its own effective address (applying
            # pre-decrement / +q offset immediately, as real AVR hardware
            # does) and then services the transfer itself: CPU-internal I/O
            # registers and the register file (address < 32) are resolved in
            # a single cycle, everything else starts the generic bus engine
            # (STATE_FETCH_REQ / STATE_MEM_WAIT) via STATE_INDIRECT_LOAD /
            # STATE_INDIRECT_STORE.
            # ---------------------------------------------------------------
            case 'LDX':
                Rd = (self.ins>>4)&0x1F
                addr = (self.reg[26] & 0xFF) | ((self.reg[27] & 0xFF) << 8)
                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDX R{Rd}, X\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDX R{Rd}, X\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')
                else:
                    def _ldx_print(Rd=Rd, addr=addr):
                        print(f'LDX R{Rd}, X\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldx_print
            case 'LDX+':
                Rd = (self.ins>>4)&0x1F
                addr = (self.reg[26] & 0xFF) | ((self.reg[27] & 0xFF) << 8)

                def _ldx_postinc(addr=addr):
                    newaddr = (addr + 1) & 0xFFFF
                    self.reg[26] = newaddr & 0xFF
                    self.reg[27] = (newaddr >> 8) & 0xFF

                def _ldx_postinc_print(Rd=Rd, addr=addr):
                    _ldx_postinc(addr)
                    print(f'LDX+ R{Rd}, X+\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')

                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    _ldx_postinc()
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDX+ R{Rd}, X+\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    _ldx_postinc()
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDX+ R{Rd}, X+\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')
                else:
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldx_postinc_print
            case 'LD-X':
                Rd = (self.ins>>4)&0x1F
                addr = (((self.reg[26] & 0xFF) | ((self.reg[27] & 0xFF) << 8)) - 1) & 0xFFFF
                self.reg[26] = addr & 0xFF
                self.reg[27] = (addr >> 8) & 0xFF

                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LD-X R{Rd}, -X\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LD-X R{Rd}, -X\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')
                else:
                    def _ldmx_print(Rd=Rd, addr=addr):
                        print(f'LD-X R{Rd}, -X\t\tR{Rd}={self.reg[Rd]:02X} [X]={addr:04X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldmx_print
            case 'LDY':
                Rd = (self.ins>>4)&0x1F
                addr = (self.reg[28] & 0xFF) | ((self.reg[29] & 0xFF) << 8)
                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDY R{Rd}, Y\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDY R{Rd}, Y\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')
                else:
                    def _ldy_print(Rd=Rd, addr=addr):
                        print(f'LDY R{Rd}, Y\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldy_print
            case 'LDY+':
                Rd = (self.ins>>4)&0x1F
                addr = (self.reg[28] & 0xFF) | ((self.reg[29] & 0xFF) << 8)

                def _ldy_postinc(addr=addr):
                    newaddr = (addr + 1) & 0xFFFF
                    self.reg[28] = newaddr & 0xFF
                    self.reg[29] = (newaddr >> 8) & 0xFF

                def _ldy_postinc_print(Rd=Rd, addr=addr):
                    _ldy_postinc(addr)
                    print(f'LDY+ R{Rd}, Y+\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')

                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    _ldy_postinc()
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDY+ R{Rd}, Y+\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    _ldy_postinc()
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDY+ R{Rd}, Y+\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')
                else:
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldy_postinc_print
            case 'LD-Y':
                Rd = (self.ins>>4)&0x1F
                addr = (((self.reg[28] & 0xFF) | ((self.reg[29] & 0xFF) << 8)) - 1) & 0xFFFF
                self.reg[28] = addr & 0xFF
                self.reg[29] = (addr >> 8) & 0xFF

                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LD-Y R{Rd}, -Y\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LD-Y R{Rd}, -Y\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')
                else:
                    def _ldmy_print(Rd=Rd, addr=addr):
                        print(f'LD-Y R{Rd}, -Y\t\tR{Rd}={self.reg[Rd]:02X} [Y]={addr:04X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldmy_print
            case 'LDDY':
                Rd = (self.ins>>4)&0x1F
                q = (self.ins & 0b111) | (((self.ins >> 10) & 0b11) << 3) | (((self.ins >> 13) & 0b1) << 5)
                addr = (((self.reg[28] & 0xFF) | ((self.reg[29] & 0xFF) << 8)) + q) & 0xFFFF

                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDD R{Rd}, Y+{q}\t\tR{Rd}={self.reg[Rd]:02X} [Y+{q}]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDD R{Rd}, Y+{q}\t\tR{Rd}={self.reg[Rd]:02X} [Y+{q}]={addr:04X}')
                else:
                    def _lddy_print(Rd=Rd, addr=addr, q=q):
                        print(f'LDD R{Rd}, Y+{q}\t\tR{Rd}={self.reg[Rd]:02X} [Y+{q}]={addr:04X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _lddy_print
            case 'LDZ':
                Rd = (self.ins>>4)&0x1F
                addr = (self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)
                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDZ R{Rd}, Z\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDZ R{Rd}, Z\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')
                else:
                    def _ldz_print(Rd=Rd, addr=addr):
                        print(f'LDZ R{Rd}, Z\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldz_print
            case 'LDZ+':
                Rd = (self.ins>>4)&0x1F
                addr = (self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)

                def _ldz_postinc(addr=addr):
                    newaddr = (addr + 1) & 0xFFFF
                    self.reg[30] = newaddr & 0xFF
                    self.reg[31] = (newaddr >> 8) & 0xFF

                def _ldz_postinc_print(Rd=Rd, addr=addr):
                    _ldz_postinc(addr)
                    print(f'LDZ+ R{Rd}, Z+\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')

                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    _ldz_postinc()
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDZ+ R{Rd}, Z+\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    _ldz_postinc()
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDZ+ R{Rd}, Z+\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')
                else:
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldz_postinc_print
            case 'LD-Z':
                Rd = (self.ins>>4)&0x1F
                addr = (((self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)) - 1) & 0xFFFF
                self.reg[30] = addr & 0xFF
                self.reg[31] = (addr >> 8) & 0xFF

                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LD-Z R{Rd}, -Z\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LD-Z R{Rd}, -Z\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')
                else:
                    def _ldmz_print(Rd=Rd, addr=addr):
                        print(f'LD-Z R{Rd}, -Z\t\tR{Rd}={self.reg[Rd]:02X} [Z]={addr:04X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _ldmz_print
            case 'LDDZ':
                Rd = (self.ins>>4)&0x1F
                q = (self.ins & 0b111) | (((self.ins >> 10) & 0b11) << 3) | (((self.ins >> 13) & 0b1) << 5)
                addr = (((self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)) + q) & 0xFFFF

                self.state = "STATE_INDIRECT_LOAD"
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDD R{Rd}, Z+{q}\t\tR{Rd}={self.reg[Rd]:02X} [Z+{q}]={addr:04X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDD R{Rd}, Z+{q}\t\tR{Rd}={self.reg[Rd]:02X} [Z+{q}]={addr:04X}')
                else:
                    def _lddz_print(Rd=Rd, addr=addr, q=q):
                        print(f'LDD R{Rd}, Z+{q}\t\tR{Rd}={self.reg[Rd]:02X} [Z+{q}]={addr:04X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _lddz_print
            case 'STX':
                Rr = (self.ins>>4)&0x1F
                addr = (self.reg[26] & 0xFF) | ((self.reg[27] & 0xFF) << 8)
                data = self.reg[Rr] & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                print(f'STX X, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'STX+':
                Rr = (self.ins>>4)&0x1F
                addr = (self.reg[26] & 0xFF) | ((self.reg[27] & 0xFF) << 8)
                data = self.reg[Rr] & 0xFF

                def _stx_postinc(addr=addr):
                    newaddr = (addr + 1) & 0xFFFF
                    self.reg[26] = newaddr & 0xFF
                    self.reg[27] = (newaddr >> 8) & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    _stx_postinc()
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    _stx_postinc()
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _stx_postinc
                print(f'STX+ X+, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'ST-X':
                Rr = (self.ins>>4)&0x1F
                addr = (((self.reg[26] & 0xFF) | ((self.reg[27] & 0xFF) << 8)) - 1) & 0xFFFF
                self.reg[26] = addr & 0xFF
                self.reg[27] = (addr >> 8) & 0xFF
                data = self.reg[Rr] & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                print(f'ST-X -X, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'STY':
                Rr = (self.ins>>4)&0x1F
                addr = (self.reg[28] & 0xFF) | ((self.reg[29] & 0xFF) << 8)
                data = self.reg[Rr] & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                print(f'STY Y, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'STY+':
                Rr = (self.ins>>4)&0x1F
                addr = (self.reg[28] & 0xFF) | ((self.reg[29] & 0xFF) << 8)
                data = self.reg[Rr] & 0xFF

                def _sty_postinc(addr=addr):
                    newaddr = (addr + 1) & 0xFFFF
                    self.reg[28] = newaddr & 0xFF
                    self.reg[29] = (newaddr >> 8) & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    _sty_postinc()
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    _sty_postinc()
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _sty_postinc
                print(f'STY+ Y+, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'ST-Y':
                Rr = (self.ins>>4)&0x1F
                addr = (((self.reg[28] & 0xFF) | ((self.reg[29] & 0xFF) << 8)) - 1) & 0xFFFF
                self.reg[28] = addr & 0xFF
                self.reg[29] = (addr >> 8) & 0xFF
                data = self.reg[Rr] & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                print(f'ST-Y -Y, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'STDY':
                Rr = (self.ins>>4)&0x1F
                q = (self.ins & 0b111) | (((self.ins >> 10) & 0b11) << 3) | (((self.ins >> 13) & 0b1) << 5)
                addr = (((self.reg[28] & 0xFF) | ((self.reg[29] & 0xFF) << 8)) + q) & 0xFFFF
                data = self.reg[Rr] & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                print(f'STD Y+{q}, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'STZ':
                Rr = (self.ins>>4)&0x1F
                addr = (self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)
                data = self.reg[Rr] & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                print(f'STZ Z, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'STZ+':
                Rr = (self.ins>>4)&0x1F
                addr = (self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)
                data = self.reg[Rr] & 0xFF

                def _stz_postinc(addr=addr):
                    newaddr = (addr + 1) & 0xFFFF
                    self.reg[30] = newaddr & 0xFF
                    self.reg[31] = (newaddr >> 8) & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    _stz_postinc()
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    _stz_postinc()
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _stz_postinc
                print(f'STZ+ Z+, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'ST-Z':
                Rr = (self.ins>>4)&0x1F
                addr = (((self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)) - 1) & 0xFFFF
                self.reg[30] = addr & 0xFF
                self.reg[31] = (addr >> 8) & 0xFF
                data = self.reg[Rr] & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                print(f'ST-Z -Z, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'STDZ':
                Rr = (self.ins>>4)&0x1F
                q = (self.ins & 0b111) | (((self.ins >> 10) & 0b11) << 3) | (((self.ins >> 13) & 0b1) << 5)
                addr = (((self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)) + q) & 0xFFFF
                data = self.reg[Rr] & 0xFF

                self.state = "STATE_INDIRECT_STORE"
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                print(f'STD Z+{q}, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'LDS':#k  Load direct from sram
                Rd = (self.ins>>4)&0x1F
                addr = self.ins2 & 0xFFFF
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 2
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDS R{Rd}, {addr:04X}\t\tR{Rd}={self.reg[Rd]:02X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 2
                    self.state = "FETCH_INSTRUCTION"
                    print(f'LDS R{Rd}, {addr:04X}\t\tR{Rd}={self.reg[Rd]:02X}')
                else:
                    def _lds_print(Rd=Rd, addr=addr):
                        print(f'LDS R{Rd}, {addr:04X}\t\tR{Rd}={self.reg[Rd]:02X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 2
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _lds_print
                    self.state = "STATE_FETCH_REQ"
            case 'STS':#k
                Rr = (self.ins>>4)&0x1F
                addr = self.ins2 & 0xFFFF
                data = self.reg[Rr] & 0xFF
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 2
                    self.state = "FETCH_INSTRUCTION"
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 2
                    self.state = "FETCH_INSTRUCTION"
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 2
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                    self.state = "STATE_FETCH_REQ"
                print(f'STS {addr:04X}, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'LPM': #R0 implied
                self.lpm_addr = (self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8)
                self.lpm_dest = 0
                self.lpm_postinc = False
                self.state = "STATE_LPM_REQ"
            case 'LPMZ': #Z
                self.lpm_addr = (self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8)
                self.lpm_dest = ((self.ins>>4)&0x1F)
                self.lpm_postinc = False
                self.state = "STATE_LPM_REQ"
            case 'LPMZ+': #Z+
                self.lpm_addr = (self.reg[30]&0xFF)|((self.reg[31]&0xFF)<<8)
                self.lpm_dest = ((self.ins>>4)&0x1F)
                self.lpm_postinc = True
                self.state = "STATE_LPM_REQ"
            case 'SPM':
                # must use SPMCSR
                SELFPRGEN = self.SPMCSR & 0b1
                PGERS = (self.SPMCSR >> 1) & 0b1
                PGWRT = (self.SPMCSR >> 2) & 0b1
                BLBSET = (self.SPMCSR >> 3) & 0b1

                self.Z = (self.reg[30] & 0xFF) | ((self.reg[31] & 0xFF) << 8)
                word_addr = self.Z >> 1
                page_offset = word_addr % self.PAGE_SIZE_WORDS
                page_base_addr = word_addr - page_offset

                if SELFPRGEN == 1: # SPM operation is enabled
                    # Hardware auto-clears the SPM enable bit after execution
                    self.SPMCSR &= ~0b1

                    # --- 1. PAGE ERASE ---
                    if (PGERS == 1) and (PGWRT == 0):
                        self.spm_base = page_base_addr
                        self.spm_idx = 0
                        self.spm_mode = 'erase'
                        self.state = "STATE_SPM_WRITE_REQ"
                        print(f'SPM\t\t\terase page @{page_base_addr:04X}')

                    # --- 2. PAGE WRITE ---
                    elif (PGERS == 0) and (PGWRT == 1):
                        self.spm_base = page_base_addr
                        self.spm_idx = 0
                        self.spm_mode = 'write'
                        self.state = "STATE_SPM_WRITE_REQ"
                        print(f'SPM\t\t\twrite page @{page_base_addr:04X}')

                    # --- 3. FILL TEMPORARY BUFFER ---
                    elif (PGERS == 0) and (PGWRT == 0) and (BLBSET == 0):
                        # Load the data word from R1:R0 (R0 is LSB, R1 is MSB)
                        data_word = (self.reg[0] & 0xFF) | ((self.reg[1] & 0xFF) << 8)
                        self.temp_page_buffer[page_offset] = data_word
                        self.pc += 1
                        print(f'SPM\t\t\tbuffer[{page_offset}]={data_word:04X}')
                    else:
                        self.pc += 1
                        print(f'SPM\t\t\t(no-op)')
                else:
                    self.pc += 1
                    print(f'SPM\t\t\t(disabled)')

            case 'IN':
                Rd = (self.ins>>4)&0b11111
                A = ((self.ins)&0xF) | ((((self.ins)>>9)&0b11)<<4)
                addr = (A + 0x20) & 0xFFFF
                # I/O address A maps to data-space address A + 0x20.
                # CPU-internal registers (SREG, SPL/SPH, MCUSR, ...) are
                # serviced without a bus transaction.
                if addr in self.INTERNAL_IO_REGS:
                    self.reg[Rd] = getattr(self, self.INTERNAL_IO_REGS[addr]) & 0xFF
                    self.pc += 1
                    print(f'IN R{Rd}, {A:02X}\t\tR{Rd}={self.reg[Rd]:02X}')
                elif addr < 32:
                    self.reg[Rd] = self.reg[addr] & 0xFF
                    self.pc += 1
                    print(f'IN R{Rd}, {A:02X}\t\tR{Rd}={self.reg[Rd]:02X}')
                else:
                    def _in_print(Rd=Rd, A=A):
                        print(f'IN R{Rd}, {A:02X}\t\tR{Rd}={self.reg[Rd]:02X}')
                    self.mem_dir = 'read'
                    self.mem_addr = addr
                    self.mem_dest_reg = Rd
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = _in_print
                    self.state = "STATE_FETCH_REQ"
            case 'OUT':
                Rr = (self.ins>>4)&0b11111
                A = ((self.ins)&0xF) | ((((self.ins)>>9)&0b11)<<4)
                addr = (A + 0x20) & 0xFFFF
                data = self.reg[Rr] & 0xFF
                if addr in self.INTERNAL_IO_REGS:
                    setattr(self, self.INTERNAL_IO_REGS[addr], data)
                    self.pc += 1
                elif addr < 32:
                    self.reg[addr] = data
                    self.pc += 1
                else:
                    self.mem_dir = 'write'
                    self.mem_addr = addr
                    self.mem_wdata = data
                    self.mem_dest_reg = None
                    self.mem_words = 1
                    self.mem_next_state = "FETCH_INSTRUCTION"
                    self.mem_on_complete = None
                    self.state = "STATE_FETCH_REQ"
                print(f'OUT {A:02X}, R{Rr}\t\t[{addr:04X}]={data:02X}')
            case 'PUSH':
                Rr = (self.ins>>4)&0x1F
                value8 = self.reg[Rr] & 0xFF

                # ---- inlined push_start(value8=value8) ----
                SP = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
                self.push_sp = SP
                self.push_next_state = "FETCH_INSTRUCTION"
                self.push_after_pc = None
                self.push_lo = value8
                self.push_two_bytes = False
                self.state = "STATE_CALL_PUSH_L"
                print(f'PUSH R{Rr}\t\t[{(SP)&0xFFFF:04X}]={value8:02X}')
            case 'POP':
                Rd = (self.ins>>4)&0x1F

                def _pop_print(Rd=Rd):
                    print(f'POP R{Rd}\t\tR{Rd}={self.reg[Rd]:02X}')

                # ---- inlined pop_start(num_bytes=1, dest_reg=Rd) ----
                self.pop_num_bytes = 1
                self.pop_dest_reg = Rd
                self.pop_dest_is_pc = False
                self.pop_next_state = "FETCH_INSTRUCTION"
                self.pop_extra = _pop_print
                self.pop_base_sp = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
                self.pop_count = 0
                self.state = "STATE_RET_POP_H"
            case 'NOP':
                self.pc += 1 
                print('NOP')
            case 'SLEEP':
                ##activation of SLEEP MODE
                self.pc += 1
                print('SLEEP')
            case 'WDR' :
                ## Watchdog Reset
                self.pc +=1
                print('WDR')
            case 'BREAK' : 
                ## Sould enter debug mode
                self.pc += 1
                print('BREAK')
            case 'invalid': #basicaly a nop
                self.pc += 1
                print(f'invalid opcode @ PC {self.last_pc:04X}')
            case _:
                # Unhandled opcode: warn and treat as NOP so the CPU does
                # not spin forever refetching the same instruction.
                print(f"WARNING: unimplemented opcode '{self.opp}' at PC {self.last_pc:04X} - treated as NOP")
                self.pc += 1