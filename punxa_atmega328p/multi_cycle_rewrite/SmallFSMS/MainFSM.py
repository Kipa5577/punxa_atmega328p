import py4hw

try:
    # Reuse the canonical opcode numbering so the 2-word set below can
    # never drift out of sync with FSM_SELECTOR's op_codes table.
    from .FSM_SELECTOR import op_codes
except ImportError:
    # Fallback for standalone use outside the package layout. Keep these
    # numeric codes in sync with FSM_SELECTOR.op_codes if it changes.
    op_codes = {'JMP': 31, 'CALL': 34, 'LDS': 107, 'STS': 119, 'SLEEP': 129}

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

SLEEP_OPCODE = op_codes['SLEEP']


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
                 MAIN_Fetch_next_instruction,
                 # -- Interrupt handshake (entrance only; the sub-FSM that
                 #    actually services the interrupt — pushes the PC,
                 #    reads the vector bytes from the InterruptUnit over
                 #    the bus, clears I, and jumps — is not implemented
                 #    yet. These two pins are the hook it will attach to. --
                 MAIN_Interrupt_Entrance,        # 1-bit OUT: high while MainFSM is parked waiting to hand off to the (future) InterruptFSM
                 MAIN_Interrupt_Done,            # 1-bit IN:  pulsed by the (future) InterruptFSM when it has finished servicing the interrupt
                 MAIN_Reset=None,                # 1-bit IN: synchronous reset -- new, part of the CPU-wide reset rollout
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

        # Interrupt entrance hook — always wired, not optional.
        self.Interrupt_Entrance     = self.addOut('Interrupt_Entrance', MAIN_Interrupt_Entrance)
        self.Interrupt_Done         = self.addIn('Interrupt_Done', MAIN_Interrupt_Done)
        self.reset = self.addIn('reset', MAIN_Reset) if MAIN_Reset is not None else None

        self.current_state = 'FETCH_INSTRUCTION'
        
        # Internal register to latch the skip impulse
        self.skip_flag = 0 

        # When set, the instruction currently sitting in the fetch stage
        # must be bypassed (fetched but not decoded/executed) because a
        # prior SBRC/SBRS/CPSE/SBIC/SBIS evaluated true.
        self._bypass_next_fetch = 0
        self._prev_instr_fetched = 0 

        # Interrupts are only sampled once per instruction boundary — the
        # very first cycle we arrive fresh at FETCH_INSTRUCTION — exactly
        # like real AVR hardware, which never interrupts a fetch/decode/
        # execute already in flight. This flag is cleared every time the
        # FSM (re)enters FETCH_INSTRUCTION and set the first time that
        # state does its one-shot IRQ check.
        self._boundary_checked = False

        self.debug = 1
        self.instret_count = 0 

    def clock(self):
        if self.reset is not None and self.reset.get():
            self.current_state = 'FETCH_INSTRUCTION'
            self.skip_flag = 0
            self._bypass_next_fetch = 0
            self._prev_instr_fetched = 0
            self._boundary_checked = False
            self.Fetch_next_instruction.prepare(0)
            self.run.prepare(0)
            self.JumpWidth.prepare(0)
            self.Interrupt_Entrance.prepare(0)
            return

        skip              = self.Skip.get()
        irq               = self.Interrupt.get()
        instr_fetched     = self.Instruction_fetched.get()
        instr_decoded     = self.Instruction_decoded.get()
        instruction       = self.Instruction.get()
        done              = self.done.get()

        # JumpWidth is purely a function of the current instruction's
        # opcode, not of the FSM state: 1 = this opcode is a 2-word
        # instruction (RomHandler should advance PC by 2), 0 = 1-word.
        # Forced to 0 while parked in INTERRUPT_ENTRY: `instruction` still
        # holds whatever opcode was last decoded (nothing new is being
        # decoded during interrupt entry), and this same JumpWidth signal
        # doubles as MemoryInterfaceHandler's PC_Offset for InterruptFSM's
        # PC push — a stale 2-word opcode here would silently corrupt the
        # pushed return address by +1.
        jump_width = 1 if (instruction in TWO_WORD_INS and self.current_state != 'INTERRUPT_ENTRY') else 0

        interrupt_done    = self.Interrupt_Done.get()

        run = 0
        Fetch_next_instruction = 0
        Interrupt_Entrance = 0

        state = self.current_state
        next_state = state           # default: stay

        if state == 'FETCH_INSTRUCTION':
            if (not self._boundary_checked) and irq == 1:
                # Instruction boundary: an interrupt is pending (already
                # gated by the I flag inside the external InterruptUnit —
                # see MulticycleProcessor's Interrupt_Enable tap). Park the
                # fetch and hand off to the interrupt entrance instead of
                # starting the next instruction fetch this cycle.
                self._boundary_checked = True
                next_state = 'INTERRUPT_ENTRY'
            else:
                self._boundary_checked = True
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

        elif state == 'INTERRUPT_ENTRY':
            # Hands off to InterruptFSM (see ControlBox — wired as a
            # sibling of INSTRUCTION_FSM_BOX, triggered directly by
            # Interrupt_Entrance below rather than through the normal
            # run/FSM_SELECTOR dispatch, since nothing is "decoded" here).
            # Parks the CPU (no fetch, no sub-FSM run) until InterruptFSM
            # pulses Interrupt_Done back.
            Interrupt_Entrance = 1
            if interrupt_done == 1:
                next_state = 'FETCH_INSTRUCTION'
                self._boundary_checked = False

        elif state == 'SKIP_FETCH_LOW':
            # Keep Fetch_next_instruction low for one cycle so RomHandler
            # completes WAIT_Fetch_next_instruction_LOW -> STOP; next
            # cycle FETCH_INSTRUCTION raises it again to fetch the
            # instruction that follows the skipped one.
            Fetch_next_instruction = 0
            if self.Instruction_fetched.get() == 0:        # wait for ack to drop
                next_state = 'FETCH_INSTRUCTION'
                self._boundary_checked = False

        elif state == 'DECODE_INSTRUCTION':
            if instr_decoded == 1:
                next_state = 'EXECUTION'

        elif state == 'EXECUTION':
            # Check if this is an MCU Control instruction (NOP, SLEEP, WDR, BREAK)
            # that takes no operands and is not routed to a sub-FSM.
            if instruction == SLEEP_OPCODE:
                # SLEEP retires immediately (matches real AVR: the
                # instruction itself completes, then the clock halts) and
                # parks the CPU in SLEEP_MODE instead of returning to
                # FETCH_INSTRUCTION. Skip is meaningless here (SLEEP is
                # never the target of SBRC/SBRS/CPSE/SBIC/SBIS skip logic
                # in any real program), so it's intentionally not handled.
                self.instret_count += 1
                next_state = 'SLEEP_MODE'
            elif instruction in {128, 130, 131}:
                # Advance directly without asserting RUN
                self.instret_count += 1
                if skip == 1:
                    self.skip_flag = 1
                    self._bypass_next_fetch = 1
                next_state = 'FETCH_INSTRUCTION'
                self._boundary_checked = False
            else:
                # Standard instructions: trigger a sub-FSM and wait for it
                run = 1
                next_state = 'WAIT_OPP_DONE'

        elif state == 'SLEEP_MODE':
            # CPU halted: no fetch, no sub-FSM run, nothing happens here
            # except waiting. The ONLY way out is a real interrupt request
            # from the external InterruptUnit -- and that request is
            # already gated on the I flag by the InterruptUnit itself (see
            # MulticycleProcessor.Interrupt_Enable / MemoryInterfaceHandler
            # .I_Flag_Out), so SLEEP doesn't need to re-check I here: if
            # I was cleared (or never set), the InterruptUnit simply never
            # asserts Interrupt and the CPU sleeps forever, exactly like
            # real hardware with interrupts disabled. Sampled every cycle
            # (not a one-shot boundary check like FETCH_INSTRUCTION's,
            # since nothing else is happening while asleep) and handed off
            # to the exact same INTERRUPT_ENTRY path a normal instruction-
            # boundary interrupt uses -- InterruptFSM pushes the PC (which
            # already points at the instruction after SLEEP) and jumps to
            # the vector exactly as it would otherwise.
            if irq == 1:
                next_state = 'INTERRUPT_ENTRY'

        elif state == 'WAIT_OPP_DONE':
            if done == 1:

                self.instret_count += 1

                if skip == 1:
                    self.skip_flag = 1
                    self._bypass_next_fetch = 1
                next_state = 'FETCH_INSTRUCTION'
                self._boundary_checked = False

        if self.debug == 1:
            print(f"Main FSM: {self.current_state} -> {next_state} | Skip: {skip} | IRQ: {irq} | Bypass_next: {self._bypass_next_fetch} | JumpWidth: {jump_width}")
        
        self.current_state = next_state
        
        self.Fetch_next_instruction.prepare(Fetch_next_instruction)
        self.run.prepare(run) # To activate the Instruction Execution FSM
        self.JumpWidth.prepare(jump_width)
        self.Interrupt_Entrance.prepare(Interrupt_Entrance)