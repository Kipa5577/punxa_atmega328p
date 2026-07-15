import py4hw

"""
=============================================================================
InterruptFSM
=============================================================================
Two independent jobs, one FSM instance:

1. INTERRUPT ENTRANCE (triggered by `Entrance`, a direct pulse from
   MainFSM.Interrupt_Entrance -- NOT dispatched through FSM_SELECTOR/`run`,
   since there is no decoded instruction to dispatch on at that point):
       a. Force-clear the I flag (SREG bit 7) directly, bypassing the
          normal ALU/SEI/CLI path.
       b. Push the current PC onto the stack (same push mechanics CALL
          uses: PCH then PCL, via MEM_SP + post-decrement).
       c. Read the two interrupt-vector bytes the external InterruptUnit
          peripheral has waiting at fixed bus addresses 0x00FE (low) and
          0x00FF (high), and load them into PC.
       d. Pulse `Interrupt_Done` for one cycle -- consumed directly by
          MainFSM (see MainFSM.INTERRUPT_ENTRY), not the shared `done`
          line every other sub-FSM uses.

2. RETI (triggered by `Run` + `Instruction == RETI`, exactly like every
   other sub-FSM dispatched via FSM_SELECTOR -- see FSM_SELECTOR.py, where
   opcode 36 has been deliberately excluded from CALLRET_FSM_INS so
   CallRetFSM never also reacts to it):
       a. Pop PC off the stack (identical mechanics to RET in
          CallRetFSM: PCL then PCH, via MEM_SP + pre-increment).
       b. Force-set the I flag back to 1.
       c. Pulse the shared `done` output, exactly like every other
          sub-FSM, so MainFSM's normal WAIT_OPP_DONE handshake completes.

This FSM is wired as a SIBLING of INSTRUCTION_FSM_BOX inside ControlBox,
not one of the FSMs merged inside it -- it needs its own always-live
`Entrance` trigger that has to work even when INSTRUCTION_FSM_BOX's `run`
is 0 (which it always is while MainFSM is parked in INTERRUPT_ENTRY).
ControlBox OR-merges the handful of bus-control signals below with
INSTRUCTION_FSM_BOX's own merged outputs before they reach RomHandler /
MemoryInterfaceHandler.
"""

# --- Addressing modes (must match MemoryInterfaceHandler's constants) ---
MEM_SP = 7
MEM_INT_VECTOR_L = 19   # fixed address 0x00FE
MEM_INT_VECTOR_H = 20   # fixed address 0x00FF

# --- InputSelectMemory sources (must match MemoryInterfaceHandler's constants) ---
INPUT_PCL = 14
INPUT_PCH = 15

# --- IncDec modes (must match MemoryInterfaceHandler's constants) ---
INC_NONE = 0
INC_POST_DEC = 3   # push: decrement SP after writing (post-decrement)
INC_PRE_INC = 4    # pop:  increment SP before reading (pre-increment)

READ = 2
WRITE = 1

OPCODE_RETI = 36

# Every state that's part of the interrupt-entrance sequence (from the
# moment I is cleared through the vector-load finishing). I_Force_WE is
# held HIGH across every one of these, not just CLEAR_I's first cycle --
# see the note in clock() below for why a one-shot pulse isn't enough.
ENTRANCE_STATES = {
    'CLEAR_I',
    'PUSH_H_ISSUE', 'PUSH_H_WAIT', 'PUSH_L_ISSUE', 'PUSH_L_WAIT',
    'FETCH_VEC_L_ISSUE', 'FETCH_VEC_L_WAIT', 'FETCH_VEC_L_LATCH', 'FETCH_VEC_L_STORE',
    'FETCH_VEC_H_ISSUE', 'FETCH_VEC_H_WAIT', 'FETCH_VEC_H_LATCH', 'FETCH_VEC_H_STORE',
    'SIGNAL_DONE',
}


class InterruptFSM(py4hw.Logic):
    def __init__(self, parent, name,
                 # -- Inputs --------------------------------------------
                 Run,          # 1-bit: shared MainFSM.run wire (same one INSTRUCTION_FSM_BOX gets) -- used only to catch RETI
                 Instruction,  # decoded opcode -- checked against RETI when Run fires
                 Entrance,     # 1-bit: MainFSM.Interrupt_Entrance, direct pulse
                 Resp,         # 1-bit: MemoryInterfaceHandler memory-op-complete

                 # -- Outputs (OR-merged with INSTRUCTION_FSM_BOX's outputs in ControlBox) --
                 Done,               # RETI completion -> shared `done` -> MainFSM.WAIT_OPP_DONE
                 Read_Write,
                 Mem_Instruction,
                 InputSelectMemory,
                 IncDec,
                 LOAD_PCL,
                 LOAD_PCH,

                 # -- Outputs (direct, not merged with anything else) --
                 Interrupt_Done,   # -> MainFSM.Interrupt_Done directly
                 I_Force_WE,       # -> MemoryInterfaceHandler.I_Force_WE directly
                 I_Force_Value,    # -> MemoryInterfaceHandler.I_Force_Value directly
                 ):
        super().__init__(parent, name)

        self.Run           = self.addIn('Run', Run)
        self.Instruction   = self.addIn('Instruction', Instruction)
        self.Entrance      = self.addIn('Entrance', Entrance)
        self.Resp          = self.addIn('Resp', Resp)

        self.Done               = self.addOut('Done', Done)
        self.Read_Write          = self.addOut('Read_Write', Read_Write)
        self.Mem_Instruction     = self.addOut('Mem_Instruction', Mem_Instruction)
        self.InputSelectMemory   = self.addOut('InputSelectMemory', InputSelectMemory)
        self.IncDec              = self.addOut('IncDec', IncDec)
        self.LOAD_PCL            = self.addOut('LOAD_PCL', LOAD_PCL)
        self.LOAD_PCH            = self.addOut('LOAD_PCH', LOAD_PCH)

        self.Interrupt_Done = self.addOut('Interrupt_Done', Interrupt_Done)
        self.I_Force_WE      = self.addOut('I_Force_WE', I_Force_WE)
        self.I_Force_Value   = self.addOut('I_Force_Value', I_Force_Value)

        self.current_state = 'STOP'
        self.debug = 1

    def clock(self):
        run         = self.Run.get()
        instruction = self.Instruction.get()
        entrance    = self.Entrance.get()
        resp        = self.Resp.get()

        # Defaults every cycle
        Read_Write = 0
        Mem_Instruction = 0
        InputSelectMemory = 0
        IncDec = 0
        LOAD_PCL = 0
        LOAD_PCH = 0
        Done = 0
        Interrupt_Done = 0
        I_Force_WE = 0
        I_Force_Value = 0

        state = self.current_state
        next_state = state

        # Hold the I-flag clear for the WHOLE entrance sequence, not just
        # CLEAR_I's one cycle. Reason: the ALU's SREG-flag logic in this
        # design is combinational on whatever instruction is currently
        # decoded -- it doesn't pulse once, it keeps re-asserting eSREG/
        # SREG_VAL every cycle for as long as that instruction sits
        # decoded. MainFSM never advances fetch/decode while parked in
        # INTERRUPT_ENTRY, so the SEI (or whatever) that triggered this
        # stays decoded the entire time we're running -- a one-shot clear
        # in CLEAR_I alone gets silently undone by that still-decoded SEI
        # on every subsequent cycle, I flickers back to 1, and if the
        # interrupt source is still level-asserted when we finish,
        # MainFSM sees Interrupt still high and immediately re-enters
        # INTERRUPT_ENTRY forever without ever fetching again.
        if state in ENTRANCE_STATES:
            I_Force_WE = 1
            I_Force_Value = 0

        # ================================================================
        if state == 'STOP':
            if entrance == 1:
                next_state = 'CLEAR_I'
            elif run == 1 and instruction == OPCODE_RETI:
                next_state = 'RETI_POP_L_ISSUE'

        # ----------------------------------------------------------------
        # INTERRUPT ENTRANCE
        # ----------------------------------------------------------------
        elif state == 'CLEAR_I':
            # I_Force_WE/Value already asserted by the ENTRANCE_STATES
            # default above (redundant here, kept for clarity).
            I_Force_WE = 1
            I_Force_Value = 0
            next_state = 'PUSH_H_ISSUE'

        elif state == 'PUSH_H_ISSUE':
            Read_Write = WRITE
            Mem_Instruction = MEM_SP
            InputSelectMemory = INPUT_PCH
            IncDec = INC_POST_DEC
            next_state = 'PUSH_H_WAIT'

        elif state == 'PUSH_H_WAIT':
            Read_Write = WRITE
            Mem_Instruction = MEM_SP
            InputSelectMemory = INPUT_PCH
            if resp == 1:
                next_state = 'PUSH_L_ISSUE'

        elif state == 'PUSH_L_ISSUE':
            Read_Write = WRITE
            Mem_Instruction = MEM_SP
            InputSelectMemory = INPUT_PCL
            IncDec = INC_POST_DEC
            next_state = 'PUSH_L_WAIT'

        elif state == 'PUSH_L_WAIT':
            Read_Write = WRITE
            Mem_Instruction = MEM_SP
            InputSelectMemory = INPUT_PCL
            if resp == 1:
                next_state = 'FETCH_VEC_L_ISSUE'

        elif state == 'FETCH_VEC_L_ISSUE':
            Read_Write = READ
            Mem_Instruction = MEM_INT_VECTOR_L
            next_state = 'FETCH_VEC_L_WAIT'

        elif state == 'FETCH_VEC_L_WAIT':
            Read_Write = READ
            Mem_Instruction = MEM_INT_VECTOR_L
            if resp == 1:
                next_state = 'FETCH_VEC_L_LATCH'

        elif state == 'FETCH_VEC_L_LATCH':
            next_state = 'FETCH_VEC_L_STORE'

        elif state == 'FETCH_VEC_L_STORE':
            LOAD_PCL = 1
            next_state = 'FETCH_VEC_H_ISSUE'

        elif state == 'FETCH_VEC_H_ISSUE':
            Read_Write = READ
            Mem_Instruction = MEM_INT_VECTOR_H
            next_state = 'FETCH_VEC_H_WAIT'

        elif state == 'FETCH_VEC_H_WAIT':
            Read_Write = READ
            Mem_Instruction = MEM_INT_VECTOR_H
            if resp == 1:
                next_state = 'FETCH_VEC_H_LATCH'

        elif state == 'FETCH_VEC_H_LATCH':
            next_state = 'FETCH_VEC_H_STORE'

        elif state == 'FETCH_VEC_H_STORE':
            LOAD_PCH = 1
            next_state = 'SIGNAL_DONE'

        elif state == 'SIGNAL_DONE':
            Interrupt_Done = 1
            next_state = 'STOP'

        # ----------------------------------------------------------------
        # RETI
        # ----------------------------------------------------------------
        elif state == 'RETI_POP_L_ISSUE':
            Read_Write = READ
            Mem_Instruction = MEM_SP
            IncDec = INC_PRE_INC
            next_state = 'RETI_POP_L_WAIT'

        elif state == 'RETI_POP_L_WAIT':
            Read_Write = READ
            Mem_Instruction = MEM_SP
            if resp == 1:
                next_state = 'RETI_POP_L_LATCH'

        elif state == 'RETI_POP_L_LATCH':
            next_state = 'RETI_POP_L_STORE'

        elif state == 'RETI_POP_L_STORE':
            LOAD_PCL = 1
            next_state = 'RETI_POP_H_ISSUE'

        elif state == 'RETI_POP_H_ISSUE':
            Read_Write = READ
            Mem_Instruction = MEM_SP
            IncDec = INC_PRE_INC
            next_state = 'RETI_POP_H_WAIT'

        elif state == 'RETI_POP_H_WAIT':
            Read_Write = READ
            Mem_Instruction = MEM_SP
            if resp == 1:
                next_state = 'RETI_POP_H_LATCH'

        elif state == 'RETI_POP_H_LATCH':
            next_state = 'RETI_POP_H_STORE'

        elif state == 'RETI_POP_H_STORE':
            LOAD_PCH = 1
            next_state = 'RETI_ENABLE_I'

        elif state == 'RETI_ENABLE_I':
            I_Force_WE = 1
            I_Force_Value = 1
            Done = 1
            next_state = 'STOP'

        # ================================================================
        if self.debug and self.current_state != 'STOP':
            print(f"INTERRUPT_FSM | {self.current_state} -> {next_state} | "
                  f"RW:{Read_Write} MemInstr:{Mem_Instruction} Resp:{resp} "
                  f"Done:{Done} IntDone:{Interrupt_Done}")

        self.current_state = next_state

        self.Read_Write.prepare(Read_Write)
        self.Mem_Instruction.prepare(Mem_Instruction)
        self.InputSelectMemory.prepare(InputSelectMemory)
        self.IncDec.prepare(IncDec)
        self.LOAD_PCL.prepare(LOAD_PCL)
        self.LOAD_PCH.prepare(LOAD_PCH)
        self.Done.prepare(Done)
        self.Interrupt_Done.prepare(Interrupt_Done)
        self.I_Force_WE.prepare(I_Force_WE)
        self.I_Force_Value.prepare(I_Force_Value)