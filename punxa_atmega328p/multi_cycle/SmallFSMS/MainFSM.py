import py4hw

class MainFSM(py4hw.Logic):
    def __init__(self, parent, name,
                 MAIN_Skip,               # 1-bit: ALU skip condition met
                 MAIN_Interrupt,          # 1-bit: interrupt pending
                 MAIN_Instruction_fetched, # 1-bit: romHandler signal
                 MAIN_Instruction_decoded, # 1-bit: Instruction_decoder signal
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
        self.JumpWidth             = self.addIn('JumpWidth', MAIN_JumpWidth)
        self.done                  = self.addIn('Done',MAIN_DONE)
        self.run                   = self.addOut('run',MAIN_RUN)
        self.Fetch_next_instruction= self.addOut('Fetch_next_instruction', MAIN_Fetch_next_instruction)

        self.current_state = 'FETCH_INSTRUCTION'

    def clock(self):
        skip              = self.Skip.get()
        irq               = self.Interrupt.get()
        instr_fetched     = self.Instruction_fetched.get()
        instr_decoded     = self.Instruction_decoded.get()
        done              = self.done.get()

        run = 0
        Fetch_next_instruction = 0

        state = self.current_state
        next_state = state           # default: stay

        if state == 'FETCH_INSTRUCTION':
            Fetch_next_instruction = 1
            if instr_fetched == 1:                     # RomHandler signals fetch done
                next_state = 'DECODE_INSTRUCTION'

        elif state == 'DECODE_INSTRUCTION':
            if instr_decoded == 1:
                next_state = 'EXECUTION'

        elif state == 'EXECUTION':
            run = 1 
            if done == 1:
                # Fixed bug: Changed == to =
                # Fixed typo: 'FINISED...' -> 'FINISHED...'
                next_state = 'FINISHED_INSTRUCTION_EXECUTION' 

        elif state == 'FINISHED_INSTRUCTION_EXECUTION':
            next_state = 'FETCH_INSTRUCTION'

        print(f"Main FSM: {self.current_state} -> {next_state}")
        
        self.current_state = next_state
        
        self.Fetch_next_instruction.prepare(Fetch_next_instruction)
        self.run.prepare(run) # To activate the Instruction Execution FSM