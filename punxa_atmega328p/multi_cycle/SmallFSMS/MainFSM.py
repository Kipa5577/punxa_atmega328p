import py4hw

try:
    # Reuse the canonical opcode numbering so the 2-word set below can
    # never drift out of sync with FSM_SELECTOR's op_codes table.
    from .FSM_SELECTOR import op_codes
except ImportError:
    # Fallback for standalone use outside the package layout. Keep these
    # numeric codes in sync with FSM_SELECTOR.op_codes if it changes.
    op_codes = {'JMP': 31, 'CALL': 34, 'LDS': 107, 'STS': 119}

# Real 2-word (32-bit) AVR instructions: absolute JMP/CALL (22-bit address)
# and direct-address LDS/STS. Each of these needs a second program-memory
# word, so RomHandler must advance PC by 2 instead of 1 once one of them
# has been fetched. Every other opcode in this ISA is a single word.
TWO_WORD_INS = {
    op_codes['JMP'],
    op_codes['CALL'],
    op_codes['LDS'],
    op_codes['STS'],
}


class MainFSM(py4hw.Logic):
    def __init__(self, parent, name,
                 MAIN_Skip,               # 1-bit: ALU skip condition met
                 MAIN_Interrupt,          # 1-bit: interrupt pending
                 MAIN_Instruction_fetched, # 1-bit: romHandler signal
                 MAIN_Instruction_decoded, # 1-bit: Instruction_decoder signal
                 MAIN_Instruction,        # instruction code (opcode), used to size JumpWidth
                 MAIN_DONE,
                 MAIN_RUN,
                 MAIN_JumpWidth,
                 MAIN_Fetch_next_instruction
                ):
        super().__init__(parent, name)
        self.Skip                  = self.addIn('Skip',                  MAIN_Skip)
        self.Interrupt             = self.addIn('Interrupt',             MAIN_Interrupt)
        self.Instruction_fetched   = self.addIn('Instruction_fetched',   MAIN_Instruction_fetched)
        self.Instruction_decoded   = self.addIn('Instruction_decoded',   MAIN_Instruction_decoded)
        self.Instruction           = self.addIn('Instruction',           MAIN_Instruction)
        self.done                  = self.addIn('Done',MAIN_DONE)
        self.run                   = self.addOut('run',MAIN_RUN)
        self.Fetch_next_instruction= self.addOut('Fetch_next_instruction', MAIN_Fetch_next_instruction)
        self.JumpWidth             = self.addOut('JumpWidth', MAIN_JumpWidth)

        self.current_state = 'FETCH_INSTRUCTION'
        
        # Internal register to latch the skip impulse
        self.skip_flag = 0 

        # When set, the instruction currently sitting in the fetch stage
        # must be bypassed (fetched but not decoded/executed) because a
        # prior SBRC/SBRS/CPSE/SBIC/SBIS evaluated true.
        self._bypass_next_fetch = 0
        self._prev_instr_fetched = 0 

        self.debug = 1
        self.instret_count = 0 

    def clock(self):
        skip              = self.Skip.get()
        irq               = self.Interrupt.get()
        instr_fetched     = self.Instruction_fetched.get()
        instr_decoded     = self.Instruction_decoded.get()
        instruction       = self.Instruction.get()
        done              = self.done.get()

        # JumpWidth is purely a function of the current instruction's
        # opcode, not of the FSM state: 1 = this opcode is a 2-word
        # instruction (RomHandler should advance PC by 2), 0 = 1-word.
        jump_width = 1 if instruction in TWO_WORD_INS else 0

        run = 0
        Fetch_next_instruction = 0

        state = self.current_state
        next_state = state           # default: stay

        if state == 'FETCH_INSTRUCTION':
            Fetch_next_instruction = 1
            if instr_fetched == 1 and self._prev_instr_fetched == 0:   # rising edge
                self._prev_instr_fetched = 1
                if self._bypass_next_fetch == 1:
                    # SKIP: the instruction that was just fetched must be
                    # discarded without being decoded/executed. Go pulse
                    # Fetch_next_instruction low for a cycle (required by
                    # RomHandler's edge-triggered handshake) before
                    # re-fetching the instruction that follows it.
                    self._bypass_next_fetch = 0
                    next_state = 'SKIP_FETCH_LOW'
                else:
                    next_state = 'DECODE_INSTRUCTION'
            else:
                self._prev_instr_fetched = 0
        elif state == 'SKIP_FETCH_LOW':
            # Keep Fetch_next_instruction low for one cycle so RomHandler
            # completes WAIT_Fetch_next_instruction_LOW -> STOP; next
            # cycle FETCH_INSTRUCTION raises it again to fetch the
            # instruction that follows the skipped one.
            Fetch_next_instruction = 0
            if self.Instruction_fetched.get() == 0:        # wait for ack to drop
                next_state = 'FETCH_INSTRUCTION'

        elif state == 'DECODE_INSTRUCTION':
            if instr_decoded == 1:
                next_state = 'EXECUTION'

        elif state == 'EXECUTION':
            run = 1
            next_state = 'WAIT_OPP_DONE'

        elif state == 'WAIT_OPP_DONE':
            if done == 1:

                self.instret_count += 1

                if skip == 1:
                    self.skip_flag = 1
                    self._bypass_next_fetch = 1
                next_state = 'FETCH_INSTRUCTION'

        if self.debug == 1:
            print(f"Main FSM: {self.current_state} -> {next_state} | Skip: {skip} | Bypass_next: {self._bypass_next_fetch} | JumpWidth: {jump_width}")
        
        self.current_state = next_state
        
        self.Fetch_next_instruction.prepare(Fetch_next_instruction)
        self.run.prepare(run) # To activate the Instruction Execution FSM
        self.JumpWidth.prepare(jump_width)