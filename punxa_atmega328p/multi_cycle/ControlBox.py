from .SmallFSMS.INSTRUCTION_FSM_BOX import *
from .SmallFSMS.MainFSM import *
from .SmallFSMS.InterruptFSM import InterruptFSM


class _InterruptBusMerge(py4hw.Logic):
    """
    Tiny OR-merge, same principle as FSM_OutputMerger but scoped to just the
    handful of bus-control signals both INSTRUCTION_FSM_BOX (normal
    instruction execution) and InterruptFSM (interrupt entrance + RETI) can
    drive. Since InterruptFSM sits OUTSIDE INSTRUCTION_FSM_BOX (it needs an
    Entrance trigger that works even when INSTRUCTION_FSM_BOX's `run` is 0),
    its outputs never got included in FSM_OutputMerger's 6-way OR — this is
    the second, smaller merge stage that combines the two.

    Safe because the two are mutually exclusive in time: INSTRUCTION_FSM_BOX
    only drives non-zero here while MainFSM.run=1 (normal instruction
    execution), and InterruptFSM only drives non-zero during INTERRUPT_ENTRY
    (run=0) or while running RETI specifically (the one instruction
    INSTRUCTION_FSM_BOX's own FSM_SELECTOR no longer routes anywhere).
    """
    def __init__(self, parent, name,
                 ib_done, ib_read_write, ib_mem_instr, ib_input_select_mem,
                 ib_incdec, ib_load_pcl, ib_load_pch,
                 irq_done, irq_read_write, irq_mem_instr, irq_input_select_mem,
                 irq_incdec, irq_load_pcl, irq_load_pch,
                 out_done, out_read_write, out_mem_instr, out_input_select_mem,
                 out_incdec, out_load_pcl, out_load_pch):
        super().__init__(parent, name)
        self.ib_done              = self.addIn('ib_done', ib_done)
        self.ib_read_write        = self.addIn('ib_read_write', ib_read_write)
        self.ib_mem_instr         = self.addIn('ib_mem_instr', ib_mem_instr)
        self.ib_input_select_mem  = self.addIn('ib_input_select_mem', ib_input_select_mem)
        self.ib_incdec            = self.addIn('ib_incdec', ib_incdec)
        self.ib_load_pcl          = self.addIn('ib_load_pcl', ib_load_pcl)
        self.ib_load_pch          = self.addIn('ib_load_pch', ib_load_pch)

        self.irq_done             = self.addIn('irq_done', irq_done)
        self.irq_read_write       = self.addIn('irq_read_write', irq_read_write)
        self.irq_mem_instr        = self.addIn('irq_mem_instr', irq_mem_instr)
        self.irq_input_select_mem = self.addIn('irq_input_select_mem', irq_input_select_mem)
        self.irq_incdec           = self.addIn('irq_incdec', irq_incdec)
        self.irq_load_pcl         = self.addIn('irq_load_pcl', irq_load_pcl)
        self.irq_load_pch         = self.addIn('irq_load_pch', irq_load_pch)

        self.out_done             = self.addOut('out_done', out_done)
        self.out_read_write       = self.addOut('out_read_write', out_read_write)
        self.out_mem_instr        = self.addOut('out_mem_instr', out_mem_instr)
        self.out_input_select_mem = self.addOut('out_input_select_mem', out_input_select_mem)
        self.out_incdec           = self.addOut('out_incdec', out_incdec)
        self.out_load_pcl         = self.addOut('out_load_pcl', out_load_pcl)
        self.out_load_pch         = self.addOut('out_load_pch', out_load_pch)

    def propagate(self):
        self.out_done.put(self.ib_done.get() | self.irq_done.get())
        self.out_read_write.put(self.ib_read_write.get() | self.irq_read_write.get())
        self.out_mem_instr.put(self.ib_mem_instr.get() | self.irq_mem_instr.get())
        self.out_input_select_mem.put(self.ib_input_select_mem.get() | self.irq_input_select_mem.get())
        self.out_incdec.put(self.ib_incdec.get() | self.irq_incdec.get())
        self.out_load_pcl.put(self.ib_load_pcl.get() | self.irq_load_pcl.get())
        self.out_load_pch.put(self.ib_load_pch.get() | self.irq_load_pch.get())



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
                 CB_Address_fetched,        # Handshake from RomHandler confirming the 16-bit address word is ready
                 
                 # ── Outputs ──────────────────────────────────────────
                 CB_LoadSelectMux,          # To MemoryInterfaceHandler: selects which displacement/offset source feeds the address-generation MUX
                 CB_LoadingMux,             # To MemoryInterfaceHandler: selects which internal pointer byte (XL/XH/YL/YH/ZL/ZH/SPL/SPH) gets loaded when WE is asserted
                 CB_Input_Select,           # To MemoryInterfaceHandler: selects the data source MUX for writes to memory (ALU result, K constant, ROM value, pointer byte, etc.)
                 CB_WE_MEMORY,              # To MemoryInterfaceHandler: write-enable for loading data into the internal X/Y/Z/SP pointer registers
                 CB_Read_Write,             # To MemoryInterfaceHandler: selects memory read (0) vs memory write (1) for the current SRAM access
                 CB_mem_instr,              # To MemoryInterfaceHandler: selects which addressing mode/pointer (X, Y, Z, SP, Rd, Rr, A5/A6, etc.) generates the SRAM address
                 CB_IncDec,                 # To MemoryInterfaceHandler: controls pointer auto-increment/pre-decrement behavior (none / post-increment / pre-decrement)
                 CB_InputSelect,            # To OperandBuffer: selects whether the Rr0 latch loads from the data bus or from the decoded K constant
                 CB_WE_Buffer,              # To OperandBuffer: write-enable selecting which operand latch (Rd0/Rd1/Rr0/Rr1/IO) is updated this cycle
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
                 CB_K_Select,
                 CB_LPM_req,                # To RomHandler: enables loading of the program memory value
                 CB_SPM_req,                # To RomHandler: enables the storing of the value past to romHandler in to the program memory  1 = LMP | 2 = LMPZ | 3 = LMPZ+
                 CB_SPM_Done,               # From RomHandler: pulses one cycle when an SPM_req write has committed to ROM

                 # -- Interrupt entrance hook (see MainFSM) — always wired,
                 #    not optional. --
                 CB_Interrupt_Entrance,  # 1-bit OUT: mirrors MainFSM's Interrupt_Entrance, exposed for debug
                 # NOTE: CB_Interrupt_Done is intentionally NOT an external
                 # parameter anymore — it's now purely internal, driven by
                 # InterruptFSM.Interrupt_Done straight into MainFSM. No
                 # external caller should ever supply this signal.
                 CB_I_Force_WE,          # 1-bit OUT: InterruptFSM's direct SREG-I-flag write-enable, to MemoryInterfaceHandler
                 CB_I_Force_Value,       # 1-bit OUT: value to force I to when CB_I_Force_WE=1
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
        self.CB_Address_fetched     = self.addIn('CB_Address_fetched', CB_Address_fetched)          # Handshake for 16-bit address fetch
        self.CB_SPM_Done            = self.addIn('CB_SPM_Done', CB_SPM_Done)                        # From RomHandler: pulses when an SPM_req write has committed


        self.CB_LoadSelectMux          = self.addOut('CB_LoadSelectMux', CB_LoadSelectMux)                            # Selects the displacement/offset source for address generation
        self.CB_LoadingMux             = self.addOut('CB_LoadingMux', CB_LoadingMux)                                  # Selects which internal pointer byte gets loaded
        self.CB_Input_Select           = self.addOut('CB_Input_Select', CB_Input_Select)                              # Selects the data source MUX for memory writes
        self.CB_WE_MEMORY              = self.addOut('CB_WE_MEMORY', CB_WE_MEMORY)                                    # Write-enable for the internal X/Y/Z/SP pointer registers
        self.CB_Read_Write             = self.addOut('CB_Read_Write', CB_Read_Write)                                  # Selects memory read (0) vs memory write (1)
        self.CB_mem_instr              = self.addOut('CB_mem_instr', CB_mem_instr)                                    # Selects the addressing mode/pointer used to generate the SRAM address
        self.CB_IncDec                 = self.addOut('CB_IncDec', CB_IncDec)                                          # Controls pointer auto-increment/pre-decrement behavior
        self.CB_InputSelect            = self.addOut('CB_InputSelect', CB_InputSelect)                                # Selects data bus vs K constant for the Rr0 latch
        self.CB_WE_Buffer              = self.addOut('CB_WE_Buffer', CB_WE_Buffer)                                    # Write-enable gating data transfer into OperandBuffer latches
        self.CB_Load_Z                 = self.addOut('CB_Load_Z', CB_Load_Z)                                          # Triggers an indirect jump/call (IJMP/ICALL) via the Z register
        self.CB_Load_K                 = self.addOut('CB_Load_K', CB_Load_K)                                          # Triggers a conditional branch (BRxx/SBxx) using K7
        self.CB_Load_Jump              = self.addOut('CB_Load_Jump', CB_Load_Jump)                                    # Triggers an unconditional jump/call (RJMP/RCALL/JMP/CALL)
        self.CB_relative_Absolute      = self.addOut('CB_relative_Absolute', CB_relative_Absolute)                    # Selects relative (PC += K) vs absolute (PC = K) jump
        self.CB_Load_Byte              = self.addOut('CB_Load_Byte', CB_Load_Byte)                                    # Triggers an SPM write of WriteVal into instruction ROM
        self.CB_Fetch_next_instruction = self.addOut('CB_Fetch_next_instruction', CB_Fetch_next_instruction)          # Releases the RomHandler FSM to fetch the next instruction
        self.CB_Fetch_Address          = self.addOut('CB_Fetch_Address', CB_Fetch_Address)                            # Requests fetching the next ROM word as a raw address/data value
        self.CB_WB_Addr                = self.addOut('CB_WB_Addr', CB_WB_Addr)                                        # Explicit write-back register address (e.g. Rd+1, R0/R1) overriding Rd/Rr
        self.CB_JumpWidth              = self.addOut('CB_JumpWidth',CB_JumpWidth)                                     # Tells RomHandler how much to advance the PC (PC+1 or PC+2)
        self.CB_LOAD_PCL               = self.addOut('CB_LOAD_PCL',CB_LOAD_PCL)                                       # Enables loading the low byte of the Program Counter
        self.CB_LOAD_PCH               = self.addOut('CB_LOAD_PCH',CB_LOAD_PCH)                                       # Enables loading the high byte of the Program Counter
        self.CB_K_Select               = self.addOut('CB_K_Select',CB_K_Select)
        self.CB_LPM_req                = self.addOut('CB_LPM_req',CB_LPM_req)
        self.CB_SPM_req                = self.addOut('CB_SPM_req',CB_SPM_req)

        # Interrupt entrance hook — always wired, not optional.
        self.CB_Interrupt_Entrance     = self.addOut('CB_Interrupt_Entrance', CB_Interrupt_Entrance)
        self.CB_I_Force_WE             = self.addOut('CB_I_Force_WE', CB_I_Force_WE)
        self.CB_I_Force_Value          = self.addOut('CB_I_Force_Value', CB_I_Force_Value)

        # ==============================================================
        # INTERNAL WIRES
        # ==============================================================
        # Bridging MainFSM 'run' output to INSTRUCTION_FSM_BOX 'run' input
        self.w_run = py4hw.Wire(self, 'w_run', 1)

        # Bridging the merged 'done' back to MainFSM 'done' input
        self.w_done = py4hw.Wire(self, 'w_done', 1)

        # MainFSM.Interrupt_Done: purely internal now, driven by
        # InterruptFSM.Interrupt_Done directly (no external supplier).
        self.w_interrupt_done = py4hw.Wire(self, 'w_interrupt_done', 1)

        # Pre-merge wires: INSTRUCTION_FSM_BOX's own contribution to the
        # signals InterruptFSM also needs to drive (see _InterruptBusMerge).
        self.w_ib_done              = py4hw.Wire(self, 'w_ib_done', 1)
        self.w_ib_read_write        = py4hw.Wire(self, 'w_ib_read_write', 2)
        self.w_ib_mem_instr         = py4hw.Wire(self, 'w_ib_mem_instr', 5)
        self.w_ib_input_select_mem  = py4hw.Wire(self, 'w_ib_input_select_mem', 5)
        self.w_ib_incdec            = py4hw.Wire(self, 'w_ib_incdec', 3)
        self.w_ib_load_pcl          = py4hw.Wire(self, 'w_ib_load_pcl', 1)
        self.w_ib_load_pch          = py4hw.Wire(self, 'w_ib_load_pch', 1)

        # Pre-merge wires: InterruptFSM's own contribution to the same signals.
        self.w_irq_done              = py4hw.Wire(self, 'w_irq_done', 1)
        self.w_irq_read_write        = py4hw.Wire(self, 'w_irq_read_write', 2)
        self.w_irq_mem_instr         = py4hw.Wire(self, 'w_irq_mem_instr', 5)
        self.w_irq_input_select_mem  = py4hw.Wire(self, 'w_irq_input_select_mem', 5)
        self.w_irq_incdec            = py4hw.Wire(self, 'w_irq_incdec', 3)
        self.w_irq_load_pcl          = py4hw.Wire(self, 'w_irq_load_pcl', 1)
        self.w_irq_load_pch          = py4hw.Wire(self, 'w_irq_load_pch', 1)

        # ==============================================================
        # SUB-COMPONENTS
        # ==============================================================
        
        # 1. Main State Machine
        self.main_fsm = MainFSM( 
            self, 'MainFSM',
            MAIN_Skip=self.CB_Skip,
            MAIN_Interrupt=self.CB_Interrupt,
            MAIN_Instruction_fetched=self.CB_Instruction_fetched,
            MAIN_Instruction_decoded=self.CB_Instruction_decoded,
            MAIN_DONE=self.w_done,       # Reads the internal (merged) done wire
            MAIN_RUN=self.w_run,          # Drives the internal run wire
            MAIN_Instruction=self.CB_Instruction,      # instruction code (opcode), used to size JumpWidth
            MAIN_JumpWidth=self.CB_JumpWidth,
            MAIN_Fetch_next_instruction=self.CB_Fetch_next_instruction,
            MAIN_Interrupt_Entrance=self.CB_Interrupt_Entrance,
            MAIN_Interrupt_Done=self.w_interrupt_done
        )

        # 2. Instruction Execution Box (normal instruction dispatch — RETI
        #    excluded, see FSM_SELECTOR.CALLRET_FSM_INS). Its contribution
        #    to the 6 signals InterruptFSM also needs lands on the w_ib_*
        #    wires below instead of going straight to the CB_* ports, so
        #    _InterruptBusMerge can OR it with InterruptFSM's contribution.
        self.instruction_box = INSTRUCTION_FSM_BOX(
            self, 'INSTRUCTION_FSM_BOX',
            IFB_RUN=self.w_run,         # Reads from the internal run wire
            IFB_Instruction=self.CB_Instruction,
            IFB_Resp=self.CB_Resp,
            IFB_Branch=self.CB_Branch,
            IFB_Executed_Jump=self.CB_Executed_Jump,
            IFB_Address_fetched=self.CB_Address_fetched,
            
            IFB_DONE = self.w_ib_done,
            IFB_LoadSelectMux=self.CB_LoadSelectMux,
            IFB_LoadingMux=self.CB_LoadingMux,
            IFB_Input_Select=self.w_ib_input_select_mem,
            IFB_WE_MEMORY=self.CB_WE_MEMORY,
            IFB_Read_Write=self.w_ib_read_write,
            IFB_Mem_Instruction=self.w_ib_mem_instr,
            IFB_IncDec=self.w_ib_incdec,
            IFB_InputSelect=self.CB_InputSelect,
            IFB_WE_Buffer=self.CB_WE_Buffer,
            IFB_Load_Z=self.CB_Load_Z,
            IFB_Load_K=self.CB_Load_K,
            IFB_Load_Jump=self.CB_Load_Jump,
            IFB_relative_Absolute=self.CB_relative_Absolute,
            IFB_Load_Byte=self.CB_Load_Byte,
            IFB_Fetch_Address=self.CB_Fetch_Address,
            IFB_WB_Addr=self.CB_WB_Addr,
            IFB_LOAD_PCL=self.w_ib_load_pcl,
            IFB_LOAD_PCH=self.w_ib_load_pch,
            IFB_K_Select=self.CB_K_Select,
            IFB_LPM_req=self.CB_LPM_req,
            IFB_SPM_req=self.CB_SPM_req,
            IFB_SPM_Done=self.CB_SPM_Done,
        )

        # 3. InterruptFSM — sibling of INSTRUCTION_FSM_BOX, not inside it.
        #    Entrance is a direct pulse from MainFSM (works even though
        #    w_run stays 0 the whole time MainFSM is parked in
        #    INTERRUPT_ENTRY); Run+Instruction catch RETI exactly the way
        #    every other sub-FSM gets dispatched.
        self.interrupt_fsm = InterruptFSM(
            self, 'InterruptFSM',
            Run=self.w_run,
            Instruction=self.CB_Instruction,
            Entrance=self.CB_Interrupt_Entrance,
            Resp=self.CB_Resp,
            Done=self.w_irq_done,
            Read_Write=self.w_irq_read_write,
            Mem_Instruction=self.w_irq_mem_instr,
            InputSelectMemory=self.w_irq_input_select_mem,
            IncDec=self.w_irq_incdec,
            LOAD_PCL=self.w_irq_load_pcl,
            LOAD_PCH=self.w_irq_load_pch,
            Interrupt_Done=self.w_interrupt_done,
            I_Force_WE=self.CB_I_Force_WE,
            I_Force_Value=self.CB_I_Force_Value,
        )

        # 4. Merge INSTRUCTION_FSM_BOX's and InterruptFSM's contributions to
        #    the shared bus-control signals onto the real external ports.
        self.interrupt_bus_merge = _InterruptBusMerge(
            self, 'InterruptBusMerge',
            ib_done=self.w_ib_done,
            ib_read_write=self.w_ib_read_write,
            ib_mem_instr=self.w_ib_mem_instr,
            ib_input_select_mem=self.w_ib_input_select_mem,
            ib_incdec=self.w_ib_incdec,
            ib_load_pcl=self.w_ib_load_pcl,
            ib_load_pch=self.w_ib_load_pch,
            irq_done=self.w_irq_done,
            irq_read_write=self.w_irq_read_write,
            irq_mem_instr=self.w_irq_mem_instr,
            irq_input_select_mem=self.w_irq_input_select_mem,
            irq_incdec=self.w_irq_incdec,
            irq_load_pcl=self.w_irq_load_pcl,
            irq_load_pch=self.w_irq_load_pch,
            out_done=self.w_done,
            out_read_write=self.CB_Read_Write,
            out_mem_instr=self.CB_mem_instr,
            out_input_select_mem=self.CB_Input_Select,
            out_incdec=self.CB_IncDec,
            out_load_pcl=self.CB_LOAD_PCL,
            out_load_pch=self.CB_LOAD_PCH,
        )