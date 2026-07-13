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
    "STATE_CALL_PUSH_H","STATE_CALL_PUSH_L",
    "STATE_RET_POP_L","STATE_RET_POP_H",
    # Indirect load/store , LPM
    "STATE_INDIRECT_LOAD","STATE_INDIRECT_STORE",
    "STATE_LPM_REQ","STATE_LPM_WAIT",
    "STATE_SPM_WRITE_REQ","STATE_SPM_WRITE_WAIT",
    # I/O bit read-modify-write
    "STATE_IO_BIT_READ","STATE_IO_BIT_WRITE",
    # SKIP
    "STATE_SKIP_FETCH_REQ","STATE_SKIP_FETCH_WAIT"
]

# The only real two-word (32 bit) AVR instructions.
TWO_WORD_OPS = {"JMP", "CALL", "LDS", "STS"}

# ptr register (X/Y/Z) -> index of its LOW byte in the register file
PTR_LOW = {'X': 26, 'Y': 28, 'Z': 30}

# opcode -> (pointer register, addressing mode, direction)
#   mode: 'none' | 'post_inc' | 'pre_dec' | 'offset_q'
#   direction: 'load' | 'store'
INDIRECT_TABLE = {
    'LDX':  ('X', 'none',     'load'),
    'LDX+': ('X', 'post_inc', 'load'),
    'LD-X': ('X', 'pre_dec',  'load'),
    'LDY':  ('Y', 'none',     'load'),
    'LDY+': ('Y', 'post_inc', 'load'),
    'LD-Y': ('Y', 'pre_dec',  'load'),
    'LDDY': ('Y', 'offset_q', 'load'),
    'LDZ':  ('Z', 'none',     'load'),
    'LDZ+': ('Z', 'post_inc', 'load'),
    'LD-Z': ('Z', 'pre_dec',  'load'),
    'LDDZ': ('Z', 'offset_q', 'load'),

    'STX':  ('X', 'none',     'store'),
    'STX+': ('X', 'post_inc', 'store'),
    'ST-X': ('X', 'pre_dec',  'store'),
    'STY':  ('Y', 'none',     'store'),
    'STY+': ('Y', 'post_inc', 'store'),
    'ST-Y': ('Y', 'pre_dec',  'store'),
    'STDY': ('Y', 'offset_q', 'store'),
    'STZ':  ('Z', 'none',     'store'),
    'STZ+': ('Z', 'post_inc', 'store'),
    'ST-Z': ('Z', 'pre_dec',  'store'),
    'STDZ': ('Z', 'offset_q', 'store'),
}


class MultyCycleATmega328P_V2(py4hw.Logic):
    def __init__(self,parent, name:str , ins_mem:MemoryInterface,memory:MemoryInterface, reset_address, Interrupt=None, reset=None):#INT0,INT1,PCINT0,PCINT1,PCINT2,WDT,TIMER2_COMPA,TIMER2_COMPB,TIMER2_OVF,TIMER1_CAPT,TIMER1_COMPA,TIMER1_COMPB,TIMER1_OVF,TIMER0_COMPA,TIMER0_COMPB,TIMER0_OVF,SPI_STC,USART_RX,USART_UDRE,USART_TX,ADC,EE_READY,ANALOG_COMP,TWI,SPM_READY):
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

        # generic data-memory engine context
        self.mem_dir = None
        self.mem_addr = 0
        self.mem_wdata = 0
        self.mem_dest_reg = None
        self.mem_words = 1
        self.mem_next_state = "FETCH_INSTRUCTION"
        self.mem_on_complete = None

        # push/pop engine context
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
                        self.state = "STATE_CALL_PUSH_H"
                    else:
                        newSP = (self.push_sp - 1) & 0xFFFF
                        self.SPH = (newSP >> 8) & 0xFF
                        self.SPL = newSP & 0xFF
                        if self.push_after_pc is not None:
                            self.pc = self.push_after_pc
                        self.state = self.push_next_state

            case "STATE_CALL_PUSH_H":
                addr = (self.push_sp - 1) & 0xFFFF
                self.mem.write.prepare(1)
                self.mem.read.prepare(0)
                self.mem.address.prepare(addr)
                self.mem.write_data.prepare(self.push_hi)
                if self.mem.resp.get() == 1:
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
                        self._pop_finish(data, None)
                    else:
                        self.pop_byte1 = data
                        self.state = "STATE_RET_POP_L"

            case "STATE_RET_POP_L":
                addr = (self.pop_base_sp + self.pop_count + 1) & 0xFFFF
                self.mem.read.prepare(1)
                self.mem.write.prepare(0)
                self.mem.address.prepare(addr)
                if self.mem.resp.get() == 1:
                    data = self.mem.read_data.get()
                    self.pop_count += 1
                    self._pop_finish(self.pop_byte1, data)

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

                    self.pc += 1
                    self.state = "FETCH_INSTRUCTION"

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
                        self.io_val = val | (1 << self.io_bit)
                        self.state = "STATE_IO_BIT_WRITE"
                    elif self.io_op == 'CBI':
                        self.io_val = val & ~(1 << self.io_bit)
                        self.state = "STATE_IO_BIT_WRITE"
                    elif self.io_op == 'SBIC':
                        if bitval == 0:
                            self.state = "STATE_SKIP_FETCH_REQ"
                        else:
                            self.pc += 1
                            self.state = "FETCH_INSTRUCTION"
                    elif self.io_op == 'SBIS':
                        if bitval == 1:
                            self.state = "STATE_SKIP_FETCH_REQ"
                        else:
                            self.pc += 1
                            self.state = "FETCH_INSTRUCTION"

            case "STATE_IO_BIT_WRITE":
                self.mem.write.prepare(1)
                self.mem.read.prepare(0)
                self.mem.address.prepare(self.io_addr)
                self.mem.write_data.prepare(self.io_val & 0xFF)
                if self.mem.resp.get() == 1:
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
    # Generic engine helpers - called from inside execute()
    # -----------------------------------------------------------------
    # data-space address (LS view) -> internal attribute name
    INTERNAL_IO_REGS = {
        0x54: 'MCUSR',
        0x55: 'MCUCR',
        0x57: 'SPMCSR',
        0x5D: 'SPL',
        0x5E: 'SPH',
        0x5F: 'SREG',
        0x60: 'WDTCSR',
    }

    def mem_read_start(self, address, dest_reg, words=1, next_state="FETCH_INSTRUCTION", on_complete=None):
        address &= 0xFFFF

        # CPU-internal I/O registers: service without a bus transaction.
        if address in self.INTERNAL_IO_REGS:
            if dest_reg is not None:
                self.reg[dest_reg] = getattr(self, self.INTERNAL_IO_REGS[address]) & 0xFF
            self.pc += words
            if on_complete is not None:
                on_complete()
            self.state = next_state
            return

        # Addresses 0-31 alias the CPU's own register file (R0-R31). The
        # register file lives inside the CPU (self.reg), not on the external
        # data bus, so LD/LDS/etc. targeting this range are serviced
        # internally in a single cycle instead of starting a bus transaction.
        if address < 32:
            if dest_reg is not None:
                self.reg[dest_reg] = self.reg[address] & 0xFF
            self.pc += words
            if on_complete is not None:
                on_complete()
            self.state = next_state
            return

        self.mem_dir = 'read'
        self.mem_addr = address
        self.mem_dest_reg = dest_reg
        self.mem_words = words
        self.mem_next_state = next_state
        self.mem_on_complete = on_complete
        self.state = "STATE_FETCH_REQ"

    def mem_write_start(self, address, data, words=1, next_state="FETCH_INSTRUCTION", on_complete=None):
        address &= 0xFFFF

        # CPU-internal I/O registers: service without a bus transaction.
        if address in self.INTERNAL_IO_REGS:
            setattr(self, self.INTERNAL_IO_REGS[address], data & 0xFF)
            self.pc += words
            if on_complete is not None:
                on_complete()
            self.state = next_state
            return

        # Same short-circuit as mem_read_start, for ST/STS/etc. writes that
        # target the register file instead of external SRAM.
        if address < 32:
            self.reg[address] = data & 0xFF
            self.pc += words
            if on_complete is not None:
                on_complete()
            self.state = next_state
            return

        self.mem_dir = 'write'
        self.mem_addr = address
        self.mem_wdata = data & 0xFF
        self.mem_dest_reg = None
        self.mem_words = words
        self.mem_next_state = next_state
        self.mem_on_complete = on_complete
        self.state = "STATE_FETCH_REQ"

    def indirect_start(self, ptr, mode, direction, reg_idx):
        """Compute the effective address for a LD*/ST* indirect addressing
        mode (pre-decrement / post-increment / +q offset), apply any
        pre-decrement immediately (as real AVR hardware does), then hand the
        actual byte transfer off to the generic memory engine. Post-increment
        is applied as an on_complete callback once the transfer finishes."""
        lo = PTR_LOW[ptr]
        hi = lo + 1
        addr = (self.reg[lo] & 0xFF) | ((self.reg[hi] & 0xFF) << 8)

        if mode == 'pre_dec':
            addr = (addr - 1) & 0xFFFF
            self.reg[lo] = addr & 0xFF
            self.reg[hi] = (addr >> 8) & 0xFF
        elif mode == 'offset_q':
            q = (self.ins & 0b111) | (((self.ins >> 10) & 0b11) << 3) | (((self.ins >> 13) & 0b1) << 5)
            addr = (addr + q) & 0xFFFF

        def post_inc():
            if mode == 'post_inc':
                newaddr = (addr + 1) & 0xFFFF
                self.reg[lo] = newaddr & 0xFF
                self.reg[hi] = (newaddr >> 8) & 0xFF

        if direction == 'load':
            self.state = "STATE_INDIRECT_LOAD"
            self.mem_read_start(addr, dest_reg=reg_idx, on_complete=post_inc)
        else:
            self.state = "STATE_INDIRECT_STORE"
            self.mem_write_start(addr, self.reg[reg_idx] & 0xFF, on_complete=post_inc)

    def push_start(self, value16=None, value8=None, next_state="FETCH_INSTRUCTION", after_push_pc=None):
        """1 byte push (PUSH Rr) or 2 byte push (return address for
        CALL/RCALL/ICALL). Mirrors real AVR ordering: low byte stored first
        at SP, high byte stored second at SP-1, SP -= 2 at the end."""
        SP = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
        self.push_sp = SP
        self.push_next_state = next_state
        self.push_after_pc = after_push_pc
        if value16 is not None:
            self.push_lo = value16 & 0xFF
            self.push_hi = (value16 >> 8) & 0xFF
            self.push_two_bytes = True
        else:
            self.push_lo = value8 & 0xFF
            self.push_two_bytes = False
        self.state = "STATE_CALL_PUSH_L"

    def pop_start(self, num_bytes, dest_reg=None, dest_is_pc=False, next_state="FETCH_INSTRUCTION", extra_on_complete=None):
        """1 byte pop (POP Rd) or 2 byte pop (return address for RET/RETI).
        Mirrors real AVR ordering: first byte read is the "high" part
        (SP+1), second byte read is the "low" part (SP+2); SP += num_bytes
        at the end."""
        self.pop_num_bytes = num_bytes
        self.pop_dest_reg = dest_reg
        self.pop_dest_is_pc = dest_is_pc
        self.pop_next_state = next_state
        self.pop_extra = extra_on_complete
        self.pop_base_sp = ((self.SPH & 0xFF) << 8) | (self.SPL & 0xFF)
        self.pop_count = 0
        self.state = "STATE_RET_POP_H"

    def _pop_finish(self, byte1, byte2):
        new_sp = (self.pop_base_sp + self.pop_count) & 0xFFFF
        self.SPH = (new_sp >> 8) & 0xFF
        self.SPL = new_sp & 0xFF

        if self.pop_dest_is_pc:
            self.pc = ((byte1 & 0xFF) << 8) | (byte2 & 0xFF)
        else:
            if self.pop_dest_reg is not None:
                self.reg[self.pop_dest_reg] = byte1 & 0xFF
            self.pc += 1

        if self.pop_extra is not None:
            self.pop_extra()

        self.state = self.pop_next_state

    def execute(self):
        # self.opp was already decoded in WAIT_FETCH_INSTRUCTION
        match self.opp: 
            case 'ADD':
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
            case 'SER':
                self.Rd = ((self.ins>>4)&0b1111) + 16
                self.reg[self.Rd] = 0xFF
        

                self.pc +=1 
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
            case 'RJMP':
                self.K = self.ins & 0xFFF
                if self.K & 0x800:
                    self.K -= 0x1000   # sign-extend 12-bit two's complement
                self.pc = (self.pc + self.K + 1) & 0xFFFF
            case 'IJMP':
                self.pc  = (self.reg[30]&0xFF) | ((self.reg[31]&0xFF)<<8)
            case 'JMP':
                self.K = (((self.ins>>4)&0x1F)<<17)|((self.ins&0b1)<<16)|self.ins2
                self.pc = self.K
            case 'RCALL':
                self.K = self.ins&0xFFF
                #handeling negative K numbers
                if self.K>>11 == 1:
                    self.K = -(((~self.K)&0xFFF) + 1)

                ret_addr = (self.pc + 1) & 0xFFFF
                target = (self.pc + self.K + 1) & 0xFFFF
                self.push_start(value16=ret_addr, after_push_pc=target)
            case 'ICALL':
                target = (self.reg[30]&0xFF) | ((self.reg[31]&0xFF)<<8)
                ret_addr = (self.pc + 1) & 0xFFFF
                self.push_start(value16=ret_addr, after_push_pc=target)
            case 'CALL':
                target = (((self.ins>>4)&0x1F)<<17)|((self.ins&0b1)<<16)|self.ins2
                ret_addr = (self.pc + 2) & 0xFFFF
                self.push_start(value16=ret_addr, after_push_pc=target)
            case 'RET':
                self.pop_start(num_bytes=2, dest_is_pc=True)
            case 'RETI':## return from interrupt 
                def _set_interrupt_flag():
                    self.SREG |= (1<<7)
                self.pop_start(num_bytes=2, dest_is_pc=True, extra_on_complete=_set_interrupt_flag)
            case 'CPSE':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)

                if self.reg[self.Rr] == self.reg[self.Rd]:
                    self.state = "STATE_SKIP_FETCH_REQ"
                else:
                    self.pc += 1
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
            case 'SBRC':
                b = self.ins&0b111
                self.A = (self.ins>>4)&0b11111
                if (self.reg[self.A]>>b)&1 == 0:
                    self.state = "STATE_SKIP_FETCH_REQ"
                else:
                    self.pc += 1
            case 'SBRS':
                b = self.ins&0b111
                self.A = (self.ins>>4)&0b11111
                if (self.reg[self.A]>>b)&1 == 1:
                    self.state = "STATE_SKIP_FETCH_REQ"
                else:
                    self.pc += 1
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
            case 'BRBS':
                self.K =  (self.ins>>3)&0b1111111 
                S =  self.ins&0b111

                if (self.K & 0x40):
                    self.K = self.K - 128
                
                if(self.SREG>>S)&1 == 1:
                    self.pc +=  self.K +1
                else:
                    self.pc += 1 
            case 'BRBC':
                self.K =  (self.ins>>3)&0b1111111 
                S =  self.ins&0b111

                if (self.K & 0x40):
                    self.K = self.K - 128

                if(self.SREG>>S)&1 == 0:
                    self.pc += self.K + 1
                else:
                    self.pc += 1 
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
            case 'SWAP':
                self.Rd = (self.ins>>4)&0x1F
                self.reg[self.Rd]= ((self.reg[self.Rd]&0xF)<<4) | ((self.reg[self.Rd]&0xF0)>>4)

                self.pc += 1
            case 'BSET':
                s = (self.ins>>4)&0b111
                self.SREG |=(1<<s) 

                self.pc += 1
            case 'BCLR':
                s = (self.ins>>4)&0b111
                self.SREG &= ~(1<<s) 

                self.pc += 1
            case 'BST':
                b = self.ins&0b111
                self.Rd = (self.ins>>4)&0x1F
                bit = (self.reg[self.Rd]>>b)&1

                if bit:
                    self.SREG |= (1<<6)
                else:
                    self.SREG &= ~(1<<6)
 
                self.pc += 1
            case 'BLD':
                b = self.ins&0b111
                self.Rd = (self.ins>>4)&0x1F
                self.reg[self.Rd] &= ~(0b1<<b)
                self.reg[self.Rd] |= ((self.SREG>>6)&1)<<b

                self.pc += 1


            case 'MOV':
                self.Rr = ((self.ins>>9)&0b1)<<4|(self.ins & 0xF)
                self.Rd = ((self.ins>>8)&0b1)<<4|((self.ins>>4) & 0xF)
                self.reg[self.Rd] =  self.reg[self.Rr]

                self.pc += 1
            case 'MOVW':
                self.Rr = (self.ins & 0xF) << 1
                self.Rd = ((self.ins>>4) & 0xF) << 1

                self.reg[self.Rd+1] = self.reg[self.Rr+1]
                self.reg[self.Rd] =  self.reg[self.Rr]

                self.pc += 1
            case 'LDI':
            
                self.Rd = ((self.ins>>4)&0xF)+16
                self.K = (self.ins&0xF)|((((self.ins)>>8)&0xF)<<4)

                self.reg[self.Rd] = self.K 
                self.pc += 1
            case 'LDX' | 'LDX+' | 'LD-X' | 'LDY' | 'LDY+' | 'LD-Y' | 'LDDY' | \
                 'LDZ' | 'LDZ+' | 'LD-Z' | 'LDDZ' | \
                 'STX' | 'STX+' | 'ST-X' | 'STY' | 'STY+' | 'ST-Y' | 'STDY' | \
                 'STZ' | 'STZ+' | 'ST-Z' | 'STDZ':
                ptr, mode, direction = INDIRECT_TABLE[self.opp]
                reg_idx = (self.ins>>4)&0x1F
                self.indirect_start(ptr, mode, direction, reg_idx)
            case 'LDS':#k  Load direct from sram
                Rd = (self.ins>>4)&0x1F
                self.mem_read_start(self.ins2, dest_reg=Rd, words=2)
            case 'STS':#k
                Rr = (self.ins>>4)&0x1F
                self.mem_write_start(self.ins2, self.reg[Rr]&0xFF, words=2)
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

                    # --- 2. PAGE WRITE ---
                    elif (PGERS == 0) and (PGWRT == 1):
                        self.spm_base = page_base_addr
                        self.spm_idx = 0
                        self.spm_mode = 'write'
                        self.state = "STATE_SPM_WRITE_REQ"

                    # --- 3. FILL TEMPORARY BUFFER ---
                    elif (PGERS == 0) and (PGWRT == 0) and (BLBSET == 0):
                        # Load the data word from R1:R0 (R0 is LSB, R1 is MSB)
                        data_word = (self.reg[0] & 0xFF) | ((self.reg[1] & 0xFF) << 8)
                        self.temp_page_buffer[page_offset] = data_word
                        self.pc += 1
                    else:
                        self.pc += 1
                else:
                    self.pc += 1

            case 'IN':
                Rd = (self.ins>>4)&0b11111
                A = ((self.ins)&0xF) | ((((self.ins)>>9)&0b11)<<4)
                # I/O address A maps to data-space address A + 0x20.
                # CPU-internal registers (SREG, SPL/SPH, MCUSR, ...) are
                # intercepted inside mem_read_start.
                self.mem_read_start(A + 0x20, dest_reg=Rd)
            case 'OUT':
                Rr = (self.ins>>4)&0b11111
                A = ((self.ins)&0xF) | ((((self.ins)>>9)&0b11)<<4)
                self.mem_write_start(A + 0x20, self.reg[Rr]&0xFF)
            case 'PUSH':
                Rr = (self.ins>>4)&0x1F
                self.push_start(value8=self.reg[Rr]&0xFF)
            case 'POP':
                Rd = (self.ins>>4)&0x1F
                self.pop_start(num_bytes=1, dest_reg=Rd)
            case 'NOP':
                self.pc += 1 
            case 'SLEEP':
                ##activation of SLEEP MODE
                self.pc += 1
            case 'WDR' :
                ## Watchdog Reset
                self.pc +=1
            case 'BREAK' : 
                ## Sould enter debug mode
                self.pc += 1
            case 'invalid': #basicaly a nop
                self.pc += 1
            case _:
                # Unhandled opcode: warn and treat as NOP so the CPU does
                # not spin forever refetching the same instruction.
                print(f"WARNING: unimplemented opcode '{self.opp}' at PC {self.last_pc:04X} - treated as NOP")
                self.pc += 1