from .SmallFSMS.INSTRUCTION_FSM_BOX import *
from .SmallFSMS.MainFSM import *



class control_Box(py4hw.Logic):
    """
    Top-level control wrapper that integrates MainFSM and INSTRUCTION_FSM_BOX.
    
    Internal Wiring:
        * w_run: Driven by MainFSM, enables INSTRUCTION_FSM_BOX execution.
        * done:  Driven by INSTRUCTION_FSM_BOX, loops back to MainFSM to signal completion,
                 while remaining accessible as an external output.
    """

    def __init__(self, parent, name,
                 # ── Inputs ───────────────────────────────────────────
                 CB_Instruction,            # Decoded instruction opcode/code from Instruction_decoder, used to drive the FSM's control decisions
                 CB_Resp,                   # Memory handshake response from MemoryInterfaceHandler, tells ControlBox the SRAM access has completed
                 CB_Branch,                 # Branch condition result from the ALU (e.g. zero/carry flag check), tells ControlBox whether a conditional branch should be taken
                 CB_Skip,                   # Skip condition result from the ALU, tells ControlBox whether a skip instruction (SBRC/SBRS/SBIC/SBIS) should skip the next instruction
                 CB_Interrupt,              # Interrupt request line, signals ControlBox that an interrupt needs to be serviced
                 CB_Instruction_fetched,    # Handshake from RomHandler indicating a new instruction word has been fetched and is ready to decode
                 CB_Instruction_decoded,    # Handshake from Instruction_decoder indicating the decoded fields for the current instruction are valid/stable
                 CB_Executed_Jump,          # Handshake from RomHandler confirming a jump/branch/call target has been committed to the PC this cycle
                 
                 # ── Outputs ──────────────────────────────────────────
                 CB_LoadSelectMux,          # To MemoryInterfaceHandler: selects which displacement/offset source feeds the address-generation MUX
                 CB_LoadingMux,             # To MemoryInterfaceHandler: selects which internal pointer byte (XL/XH/YL/YH/ZL/ZH/SPL/SPH) gets loaded when WE is asserted
                 CB_Input_Select,           # To MemoryInterfaceHandler: selects the data source MUX for writes to memory (ALU result, K constant, ROM value, pointer byte, etc.)
                 CB_WE_MEMORY,              # To MemoryInterfaceHandler: write-enable for loading data into the internal X/Y/Z/SP pointer registers
                 CB_Read_Write,             # To MemoryInterfaceHandler: selects memory read (0) vs memory write (1) for the current SRAM access
                 CB_mem_instr,              # To MemoryInterfaceHandler: selects which addressing mode/pointer (X, Y, Z, SP, Rd, Rr, A5/A6, etc.) generates the SRAM address
                 CB_IncDec,                 # To MemoryInterfaceHandler: controls pointer auto-increment/pre-decrement behavior (none / post-increment / pre-decrement)
                 CB_InputSelect,            # To OperandBuffer: selects whether the Rr0 latch loads from the data bus or from the decoded K constant
                 CB_WE_Buffer,            # To OperandBuffer: write-enable selecting which operand latch (Rd0/Rd1/Rr0/Rr1/IO) is updated this cycle
                 CB_Load_Z,                 # To RomHandler: triggers an indirect jump/call (IJMP/ICALL) using the Z register as the new PC
                 CB_Load_K,                 # To RomHandler: triggers a conditional branch (BRxx/SBxx) using the K7 offset
                 CB_Load_Jump,              # To RomHandler: triggers an unconditional jump/call (RJMP/RCALL/JMP/CALL) using the K12/K7_22 offset/address
                 CB_relative_Absolute,      # To RomHandler: selects whether the pending jump is relative (PC += K) or absolute (PC = K)
                 CB_Load_Byte,              # To RomHandler: triggers a Store Program Memory (SPM) write of WriteVal into instruction ROM
                 CB_Fetch_next_instruction, # To RomHandler: releases the FSM from STOP/single-step trap to fetch the next instruction
                 CB_Fetch_Address,          # To RomHandler: requests fetching the next ROM word as a raw address/data value (e.g. second word of LDS/STS/JMP/CALL)
                 CB_WB_Addr,                # To MemoryInterfaceHandler: explicit write-back register address (e.g. Rd+1 for ADIW/MOVW, R0/R1 for MUL) overriding Rd/Rr
                 CB_JumpWidth,              # To RomHandler: tells it how much to advance the PC for the next instruction (0 = PC+1, 1 = PC+2 for two-word instructions)
                 CB_LOAD_PCL,               # To RomHandler: enables loading the low byte of the Program Counter from PCL_LOAD_VAL (e.g. POP PC during RET)
                 CB_LOAD_PCH,               # To RomHandler: enables loading the high byte of the Program Counter from PCH_LOAD_VAL (e.g. POP PC during RET)
                 ):
        super().__init__(parent, name)

        # ==============================================================
        # EXTERNAL PINS (Matching your instantiation list)
        # ==============================================================
        self.CB_Instruction         = self.addIn('CB_Instruction', CB_Instruction)                  # Decoded instruction opcode/code, drives the FSM's control decisions
        self.CB_Resp                = self.addIn('CB_Resp', CB_Resp)                                # Memory handshake response from MemoryInterfaceHandler
        self.CB_Branch              = self.addIn('CB_Branch', CB_Branch)                            # Branch condition result from the ALU
        self.CB_Skip                = self.addIn('CB_Skip', CB_Skip)                                # Skip condition result from the ALU
        self.CB_Interrupt           = self.addIn('CB_Interrupt', CB_Interrupt)                      # Interrupt request line
        self.CB_Instruction_fetched = self.addIn('CB_Instruction_fetched', CB_Instruction_fetched)  # Handshake: new instruction word fetched and ready to decode
        self.CB_Instruction_decoded = self.addIn('CB_Instruction_decoded', CB_Instruction_decoded)  # Handshake: decoded instruction fields are valid/stable
        self.CB_Executed_Jump       = self.addIn('CB_Executed_Jump', CB_Executed_Jump)              # Handshake: jump/branch/call target committed to PC this cycle

        self.CB_LoadSelectMux          = self.addOut('CB_LoadSelectMux', CB_LoadSelectMux)                            # Selects the displacement/offset source for address generation
        self.CB_LoadingMux             = self.addOut('CB_LoadingMux', CB_LoadingMux)                                  # Selects which internal pointer byte gets loaded
        self.CB_Input_Select           = self.addOut('CB_Input_Select', CB_Input_Select)                              # Selects the data source MUX for memory writes
        self.CB_WE_MEMORY              = self.addOut('CB_WE_MEMORY', CB_WE_MEMORY)                                    # Write-enable for the internal X/Y/Z/SP pointer registers
        self.CB_Read_Write             = self.addOut('CB_Read_Write', CB_Read_Write)                                  # Selects memory read (0) vs memory write (1)
        self.CB_mem_instr              = self.addOut('CB_mem_instr', CB_mem_instr)                                    # Selects the addressing mode/pointer used to generate the SRAM address
        self.CB_IncDec                 = self.addOut('CB_IncDec', CB_IncDec)                                          # Controls pointer auto-increment/pre-decrement behavior
        self.CB_InputSelect            = self.addOut('CB_InputSelect', CB_InputSelect)                                # Selects data bus vs K constant for the Rr0 latch
        self.CB_WE_Buffer              = self.addOut('CB_WE_Buffer', CB_WE_Buffer)                              # Write-enable gating data transfer into OperandBuffer latches
        self.CB_Load_Z                 = self.addOut('CB_Load_Z', CB_Load_Z)                                          # Triggers an indirect jump/call (IJMP/ICALL) via the Z register
        self.CB_Load_K                 = self.addOut('CB_Load_K', CB_Load_K)                                          # Triggers a conditional branch (BRxx/SBxx) using K7
        self.CB_Load_Jump              = self.addOut('CB_Load_Jump', CB_Load_Jump)                                    # Triggers an unconditional jump/call (RJMP/RCALL/JMP/CALL)
        self.CB_relative_Absolute      = self.addOut('CB_relative_Absolute', CB_relative_Absolute)                    # Selects relative (PC += K) vs absolute (PC = K) jump
        self.CB_Load_Byte              = self.addOut('CB_Load_Byte', CB_Load_Byte)                                    # Triggers an SPM write of WriteVal into instruction ROM
        self.CB_Fetch_next_instruction = self.addOut('CB_Fetch_next_instruction', CB_Fetch_next_instruction)         # Releases the RomHandler FSM to fetch the next instruction
        self.CB_Fetch_Address          = self.addOut('CB_Fetch_Address', CB_Fetch_Address)                            # Requests fetching the next ROM word as a raw address/data value
        self.CB_WB_Addr                = self.addOut('CB_WB_Addr', CB_WB_Addr)                                        # Explicit write-back register address (e.g. Rd+1, R0/R1) overriding Rd/Rr
        self.CB_JumpWidth              = self.addOut('CB_JumpWidth',CB_JumpWidth)                                     # Tells RomHandler how much to advance the PC (PC+1 or PC+2)
        self.CB_LOAD_PCL               = self.addOut('CB_LOAD_PCL',CB_LOAD_PCL)                                        # Enables loading the low byte of the Program Counter
        self.CB_LOAD_PCH               = self.addOut('CB_LOAD_PCH',CB_LOAD_PCH)                                        # Enables loading the high byte of the Program Counter

        # ==============================================================
        # INTERNAL WIRES
        # ==============================================================
        # Bridging MainFSM 'run' output to INSTRUCTION_FSM_BOX 'run' input
        self.w_run = py4hw.Wire(self, 'w_run', 1)
        
        # Bridging INSTRUCTION_FSM_BOX 'done' output back to MainFSM 'done' input
        self.w_done = py4hw.Wire(self, 'w_done', 1)

        # ==============================================================
        # SUB-COMPONENTS
        # ==============================================================
        
        # 1. Main State Machine
        self.main_fsm = MainFSM( ##NotExecute to here  ## Note Jump Width should be here 
            self, 'MainFSM',
            MAIN_Skip=self.CB_Skip,
            MAIN_Interrupt=self.CB_Interrupt,
            MAIN_Instruction_fetched=self.CB_Instruction_fetched,
            MAIN_Instruction_decoded=self.CB_Instruction_decoded,
            MAIN_DONE=self.w_done,       # Reads the internal done wire
            MAIN_RUN=self.w_run,          # Drives the internal run wire
            MAIN_JumpWidth=self.CB_JumpWidth,
            MAIN_Fetch_next_instruction=self.CB_Fetch_next_instruction
        )

        # 2. Instruction Execution Box
        self.instruction_box = INSTRUCTION_FSM_BOX(
            self, 'INSTRUCTION_FSM_BOX',
            IFB_RUN=self.w_run,         # Reads from the internal run wire
            IFB_Instruction=self.CB_Instruction,
            IFB_Resp=self.CB_Resp,
            IFB_Branch=self.CB_Branch,
            IFB_Executed_Jump=self.CB_Executed_Jump,
            

            IFB_DONE = self.w_done,
            IFB_LoadSelectMux=self.CB_LoadSelectMux,
            IFB_LoadingMux=self.CB_LoadingMux,
            IFB_Input_Select=self.CB_Input_Select,
            IFB_WE_MEMORY=self.CB_WE_MEMORY,
            IFB_Read_Write=self.CB_Read_Write,
            IFB_Mem_Instruction=self.CB_mem_instr,
            IFB_IncDec=self.CB_IncDec,
            IFB_InputSelect=self.CB_InputSelect,
            IFB_WE_Buffer=self.CB_WE_Buffer,
            IFB_Load_Z=self.CB_Load_Z,
            IFB_Load_K=self.CB_Load_K,
            IFB_Load_Jump=self.CB_Load_Jump,
            IFB_relative_Absolute=self.CB_relative_Absolute,
            IFB_Load_Byte=self.CB_Load_Byte,
            IFB_Fetch_Address=self.CB_Fetch_Address,
            IFB_WB_Addr=self.CB_WB_Addr,
            IFB_JumpWidth=self.CB_JumpWidth,
            IFB_LOAD_PCL=self.CB_LOAD_PCL,
            IFB_LOAD_PCH=self.CB_LOAD_PCH,
        )