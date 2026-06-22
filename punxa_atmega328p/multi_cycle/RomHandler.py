import py4hw


"""
=============================================================================
AI Agent Component Reference: RomHandler (PC & Fetch Unit)
=============================================================================

Description:
This class acts as the Program Counter (PC) and Instruction Fetch Unit for an 
ATmega328P-like architecture in py4hw. It utilizes an internal FSM to manage 
a 2-cycle handshake (Request/Response) with an external Instruction Memory module.
It supports sequential execution, relative/absolute jumps, conditional branches, 
indirect Z-register jumps, and ROM writing (SPM). All PC operations are masked 
to a 14-bit address space (0x3FFF).

Memory Interface (Master/Source):
- Drives: `read`, `write`, `write_data`, `address`, `instype`
- Reads: `read_data`, `resp`

Inputs (Control Signals):
- Enable (1-bit): Pauses/resumes the FSM. Used by external ControlBoxes for single-stepping.
- Load_Z (1-bit): High to trigger an indirect jump (IJMP/ICALL).
- address_ZL / address_ZH (8-bit): The lower/upper bytes of the Z register.
- Load_Jump (1-bit): High to trigger an unconditional jump or call.
- relative_Absolute (1-bit): 0 = Relative Jump (adds K to PC+1), 1 = Absolute Jump (PC = K).
- Load_K (1-bit): High to trigger a conditional branch (BRxx/SBxx).
- K (Variable width): Offset or absolute address. Treated as a 7-bit signed offset for branches, 
  a 12-bit signed offset for relative jumps, or an absolute address.
- Load_Byte (1-bit): High to initiate a Memory Write transaction (SPM instruction).
- WriteVal (Variable width): The data to be written into the Instruction Memory during SPM.

Outputs:
- instructionOut (16-bit/32-bit): The latched instruction fetched from memory.
- Address_Out (14-bit): The current value of the Program Counter (PC).

FSM States:
- STOP: Halts until Enable == 1.
- FETCH_REQ: Asserts memory read (or write if Load_Byte == 1) and address.
- FETCH_WAIT: Waits for memory `resp` == 1. Latches instruction and calculates the next PC.
- WRITE_WAIT: Waits for memory `resp` == 1 during an SPM operation.
- WAIT_ENABLE_LOW: Single-step trap; freezes execution until Enable is pulled back to 0.
=============================================================================
"""

"""
    STATE MACHINE 

    +------+
    | STOP |<--------------------------------|
    +------+                                 |
        |                                    |
    Fetch_next_instruction == 1              |
        |                                    |
    +----------+                             |
    | FETCH_REQ|                             |
    +----------+                             |
        |                                    |
    ONE CLOCK                       Fetch_next_instruction == 0
        |                                    |
    +----------+                             |
    |WRITE_WAIT|                             |
    +----------+                             |
        |                                    |
    ONE CLOCK                                |
        |                                    |
    +-------------------------------+        |
    |WAIT_Fetch_next_instruction_LOW|--------|
    +-------------------------------+


In DECODE_INSTRUCTION: Read the instruction and update the outputs and put the instruction decoder output to 1
In WAIT_FOR_NEW_INSTRUCITON: Keep the outputs as they were 
"""




class RomHandler(py4hw.Logic):
    def __init__(self, parent, name,
                 # --- Memory Interface ---
                 mem,  # Type: MemoryInterface
                 
                 # --- Outputs ---
                 instructionOut, Address_Out,Instruction_fetched,Executed_Jump,
                 Pc_valL, # This is to load pc in memory for the POP and PUSH instruction
                 Pc_valH,
                 
                 # --- Indirect Jumps (IJMP, ICALL) via Z register ---
                 Load_Z, address_ZL, address_ZH,
                 
                 # --- Branches & Jumps ---
                 Load_K, K, 
                 Load_Jump, relative_Absolute, 
                 
                 # --- ROM Writing (SPM instruction) ---
                 Load_Byte, WriteVal,

                 PCL_LOAD_VAL,# This is connected to the MemoryInterfaceHandler to load the pc valeu form the ret instructions
                 PCH_LOAD_VAL,# 

                 # --- CommandInputs --- 
                 Fetch_next_instruction,
                 JumpWidth, # tells the component by how much it has to increment the pc to go to the next instructin 0 = pc +1 | 1 = pc +2 it is connected to the control Box
                 Load_PCL,# This is to control the loading of the pc register
                 Load_PCH,

                 reset_address=0):
        
        super().__init__(parent, name)

        # --- Internal Registers ---
        self.PC = reset_address          # 14-bit Program Counter
        self.FSM = 'FETCH_REQ'           # State machine initial state
        
        # Memory interface: we are the SOURCE (master/initiator)
        self.mem = self.addInterfaceSource('ins', mem)

        # --- Output Pins ---
        self.instructionOut = self.addOut('instructionOut', instructionOut)
        self.Address_Out = self.addOut('Address_Out', Address_Out)

        self.Instruction_fetched = self.addOut('Instruction_fetched',Instruction_fetched)
        self.Executed_Jump = self.addOut('Executed_Jump',Executed_Jump)
        
        # --- Input Pins (Control Signals from Decoder/Execute stage) ---
        self.Load_Z = self.addIn('Load_Z', Load_Z)
        self.address_ZL = self.addIn('address_ZL', address_ZL)
        self.address_ZH = self.addIn('address_ZH', address_ZH)
        
        self.Load_K = self.addIn('Load_K', Load_K)
        self.K = self.addIn('K', K)
        
        self.Load_Jump = self.addIn('Load_Jump', Load_Jump)
        self.relative_Absolute = self.addIn('relative_Absolute', relative_Absolute)
    
        self.Load_Byte = self.addIn('Load_Byte', Load_Byte)
        self.WriteVal = self.addIn('WriteVal', WriteVal)

        self.Fetch_next_instruction = self.addIn('Fetch_next_instruction',Fetch_next_instruction)

        self.Pc_valL =  self.addOut('Pc_valL',Pc_valL)
        self.PC_valH =  self.addOut('Pc_valH',Pc_valH)

        self.JumpWidth = self.addIn('JumpWidth',JumpWidth)
        self.Load_PCL  = self.addIn('Load_PCL',Load_PCL)
        self.Load_PCH = self.addIn('Load_PCH',Load_PCH)

        self.PCL_LOAD_VAL = self.addIn('PCL_LOAD_VAL',PCL_LOAD_VAL)
        self.PCH_LOAD_VAL = self.addIn('PCH_LOAD_VAL',PCH_LOAD_VAL) 

    def clock(self):

        # ---------------------------------------------------------
        # STATE: STOP - Halt Execution until Fetch_next_instruction
        # ---------------------------------------------------------
        if self.FSM == 'STOP':
            # Keep memory control signals cleanly deasserted
            self.mem.instype.prepare(0)
            self.mem.read.prepare(0)
            self.mem.write.prepare(0)
            
            # Transition to fetch if ControlBox Fetch_next_instruction execution
            if self.Fetch_next_instruction.get() == 1:
                self.FSM = 'FETCH_REQ'


        # ---------------------------------------------------------
        # STATE: FETCH_REQ - Initiate memory transaction
        # ---------------------------------------------------------
        if self.FSM == 'FETCH_REQ':
            
            
            self.mem.instype.prepare(1)     
            
            # Check for Store Program Memory (SPM) write request first
            if self.Load_Byte.get() == 1:
                # --- SPM WRITE TRANSACTION ---
                self.mem.write.prepare(1)           # Enable write
                self.mem.read.prepare(0)            # Disable read  
                self.mem.address.prepare(self.PC)   # Target address
                self.mem.write_data.prepare(self.WriteVal.get())  # Data to write
                self.FSM = 'WRITE_WAIT'
            
            else:
                # --- NORMAL INSTRUCTION FETCH ---
                self.mem.write.prepare(0)           # Disable write
                self.mem.read.prepare(1)            # Enable read
                self.mem.address.prepare(self.PC)   # Address to fetch
                
                # Drive current PC to output (for debugging/external monitoring)
                self.Address_Out.prepare(self.PC)
                
                self.FSM = 'FETCH_WAIT'

        # ---------------------------------------------------------
        # STATE: FETCH_WAIT - Complete read transaction
        # ---------------------------------------------------------
        elif self.FSM == 'FETCH_WAIT':
            
            # Check if memory has responded (resp=1 means operation complete)
            if self.mem.resp.get() == 1:
                
                # Deassert bus control signals (release the interface)
                self.mem.read.prepare(0)
                self.mem.instype.prepare(0)
                
                # Latch the fetched instruction from memory
                fetched_instruction = self.mem.read_data.get()
                self.instructionOut.prepare(fetched_instruction)
                
                # -----------------------------------------------------------------
                # PC UPDATE LOGIC - Evaluate all control signals for next address
                # -----------------------------------------------------------------
                load_z   = self.Load_Z.get()       # IJMP/ICALL via Z register
                load_k   = self.Load_K.get()       # Conditional branch taken
                load_jump = self.Load_Jump.get()   # RJMP/RCALL/JMP/CALL
                rel_abs  = self.relative_Absolute.get()  # 0=relative, 1=absolute
                k_val    = self.K.get()            # Jump offset or target address
                
                # Base: sequential next PC
                next_pc = self.PC + 1
                
                # --- PC Multiplexer (priority ordered) ---
                if load_z == 1:
                    # ===== INDIRECT JUMP/CALL (IJMP/ICALL) =====
                    # Load PC from Z register (ZH:ZL)
                    z_val = (self.address_ZH.get() << 8) | self.address_ZL.get()
                    self.PC = z_val & 0x3FFF        # Mask to 14-bit address space

                elif load_jump == 1:
                    if rel_abs == 1:
                        # ===== ABSOLUTE JUMP/CALL (JMP/CALL) =====
                        # K holds full target address
                        self.PC = k_val & 0x3FFF
                    else:
                        # ===== RELATIVE JUMP/RCALL (RJMP/RCALL) =====
                        # K is 12-bit signed offset (-2048..+2047)
                        
                        if k_val & 0x800:           # Bit 11 = sign bit
                            offset = k_val | 0xFFFFF000  # Sign-extend to 32-bit
                        else:
                            offset = k_val
                        # FIX #2: Parentheses ensure correct precedence
                        self.PC = (next_pc + offset) & 0x3FFF

                elif load_k == 1:
                    # ===== CONDITIONAL BRANCH TAKEN (BRxx, SBxx) =====
                    # K is 7-bit signed offset (-64..+63)
                    if k_val & 0x40:             # Bit 6 = sign bit  
                        offset = k_val | 0xFFFFFF80   # Sign-extend to 32-bit
                    else:
                        offset = k_val
                    self.PC = (next_pc + offset) & 0x3FFF

                else:
                    # ===== SEQUENTIAL EXECUTION =====
                    self.PC = next_pc & 0x3FFF    # FIX #4: Always mask to 14 bits
                
                # Return to request state for next instruction
                self.FSM = 'FETCH_REQ'

        # ---------------------------------------------------------
        # STATE: WRITE_WAIT - Complete SPM write transaction  
        # ---------------------------------------------------------
        elif self.FSM == 'WRITE_WAIT':
            self.mem.write.prepare(0)
            self.mem.instype.prepare(0)
            
            if self.mem.resp.get() == 1:
                self.PC = (self.PC + 1) & 0x3FFF
                # [CHANGED] Go to the trap state
                self.FSM = 'WAIT_Fetch_next_instruction_LOW'

        # ---------------------------------------------------------
        # STATE: WAIT_Fetch_next_instruction_LOW - The Single-Step Trap
        # ---------------------------------------------------------
        elif self.FSM == 'WAIT_Fetch_next_instruction_LOW':
            # Completely freeze execution until the user/ControlBox pulls Fetch_next_instruction to 0
            if self.Fetch_next_instruction.get() == 0:
                self.FSM = 'STOP'

        # ---------------------------------------------------------
        # DEFAULT: Safety fallback (should never reach here)
        # ---------------------------------------------------------
        else:
            print(f"[RomHandler WARNING] Unknown state '{self.FSM}', resetting to FETCH_REQ")
            self.FSM = 'FETCH_REQ'