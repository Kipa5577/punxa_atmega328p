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
- Fetch_next_instruction (1-bit): One-shot fetch trigger. Setting this to 1
  causes the RomHandler to fetch exactly one instruction word from ROM.
  After that fetch completes, the RomHandler will NOT fetch again until
  this signal has been pulled back to 0 and then raised to 1 a second
  time (edge-triggered handshake, not a free-running enable).
- Load_Z (1-bit): High to trigger an indirect jump (IJMP/ICALL).
- address_ZL / address_ZH (8-bit): The lower/upper bytes of the Z register.
- Load_Jump (1-bit): High to trigger an unconditional jump or call.
- relative_Absolute (1-bit): 0 = Relative Jump (adds K to PC+1), 1 = Absolute Jump (PC = K).
- Load_K (1-bit): High to trigger a conditional branch (BRxx/SBxx).
- K_select (2-bit): Selects which K bus supplies the offset/address this cycle
    (0 = K7 for branches, 1 = K12 for RJMP/RCALL, 2 = K7_22 for absolute JMP/CALL).
- K7 / K12 / K7_22: Offset or absolute address sources. Treated as a 7-bit signed
  offset for branches, a 12-bit signed offset for relative jumps, or an absolute
  address for JMP/CALL.
- Load_Byte (1-bit): High to initiate a Memory Write transaction (SPM instruction).
- WriteVal (Variable width): The data to be written into the Instruction Memory during SPM.

Outputs:
- instructionOut (16-bit/32-bit): The latched instruction fetched from memory.
- Address_Out (14-bit): The current value of the Program Counter (PC).

FSM States:
- STOP: Halts until Fetch_next_instruction == 1.
- FETCH_REQ: Asserts memory read (or write if Load_Byte == 1) and address.
- FETCH_WAIT: Waits for memory `resp` == 1. Latches instruction and calculates the next PC.
- WRITE_WAIT: Waits for memory `resp` == 1 during an SPM operation.
- WAIT_Fetch_next_instruction_LOW: Single-step trap; freezes execution until
  Fetch_next_instruction is pulled back to 0.
=============================================================================
"""

"""
    STATE MACHINE

    +------+
    | STOP |<----------------------------------------------+
    +------+                                                |
        |                                                   |
    Fetch_next_instruction == 1                              |
        |                                                    |
        v                                                    |
    +-----------+   Load_Byte==1    +------------+           |
    | FETCH_REQ |------------------>| WRITE_WAIT |           |
    +-----------+                   +------------+           |
        |  Load_Byte==0                   |                  |
        v                            mem.resp == 1            |
    +------------+                        |                  |
    | FETCH_WAIT |                        |                  |
    +------------+                        |                  |
        |                                 |                  |
    mem.resp == 1                         |                  |
        |                                 v                  |
        +------------------------> +--------------------------+
                                    | WAIT_Fetch_next_instr_LOW |
                                    +--------------------------+
                                                |
                                Fetch_next_instruction == 0
                                                |
                                                +-------------> STOP

    Every single fetch (and every SPM write) is gated one-for-one by
    Fetch_next_instruction. After a word is fetched, the FSM does NOT
    loop back to FETCH_REQ on its own. It parks in
    WAIT_Fetch_next_instruction_LOW until the caller drops the signal
    to 0 (acknowledged here) and goes back to STOP, where it then waits
    for the signal to rise to 1 again before fetching the next word.
    This makes Fetch_next_instruction a true "fetch one word, then wait
    for me to pulse you again" handshake rather than a free-running enable.


In FETCH_WAIT: latch the fetched instruction, update outputs, and compute
the next PC (sequential / branch / jump / indirect), then park in the
single-step trap state until the next Fetch_next_instruction pulse.
"""




class RomHandler(py4hw.Logic):
    def __init__(self, parent, name,
                 # --- Memory Interface ---
                 RH_mem,  # Type: MemoryInterface
                 
                 # --- Outputs ---
                 RH_instructionOut, # 16-bit Gives the raw instruction code to the instruction decoder 
                 RH_Address_Out, # 16-bit Gives the address word to the MemoryController
                 RH_Value_Out, # 16-bit Gives the value stored in rom to the memory controller
                 RH_Pc_valL, # 8-bit Outputs the low 8 bits of the program counter value
                 RH_Pc_valH, # 8-bit Outputs the high 8 bits of the program counter value


                # -- StateOutputs -- 
                 RH_Instruction_fetched, # 1-bit Signal to indicate to the Control Box that the instruction has been outputed 
                 RH_Executed_Jump,# 1-bit Signal to indicate to the Control Box component that the jump instruction has been correctly executed

                 
                 # --- Indirect Jumps (IJMP, ICALL) via Z register ---
                 RH_Load_Z, # 1-bit it tels the RomHandler to fetch the value in the rom at address Z  
                 RH_address_ZL, # 8-bit Inputs the low 8 bits of the Zaddress value
                 RH_address_ZH, # 8-bit Input the high 8 bits of the Zaddress value 
                 
                 # --- Branches & Jumps ---
                 RH_Load_K, # 1-bit Tels the RomHandler to use a K value to Jump 
                 RH_K_select, # 2-bit Tels the RomHandler wich K to use 
                 RH_K7, # branch instructions 
                 RH_K12,# RCALL/RJMP 
                 #K16,# LDS/STS SECOND WORD THIS IS TO MEMORY
                 #K22,# JMP/CALL 22-bit absolute
                 RH_K7_22, # JMP/CALL 7 bits comming from the instruction decoder
                 RH_Load_Jump, # 1-bit Tels the RomHandler to jump 
                 RH_relative_Absolute, # 1-bit Tels the RomHandler if the jump is relative or absolute 
                 
                 # --- ROM Writing (SPM instruction) ---
                 RH_Load_Byte, # 1-bit this value tells the RomHandler that it should write the WriteVal to the rom 
                 RH_WriteVal, # 8-bit this signal tells the Romhandler the value that it shoud write

                 RH_PCL_LOAD_VAL,# 8-bit this 
                 RH_PCH_LOAD_VAL,# 

                 # --- CommandInputs --- 
                 RH_Fetch_next_instruction,
                 RH_JumpWidth, # tells the component by how much it has to increment the pc to go to the next instructin 0 = pc +1 | 1 = pc +2 it is connected to the control Box
                 RH_Load_PCL,# This is to control the loading of the pc register
                 RH_Load_PCH,

                 RH_fetch_address, # control imput that tell the component to fetch the next word form the rom memory 
                 RH_Address_fetched,# control values that signals the control box that the address was fetched

                 RH_reset_address=0):
        
        super().__init__(parent, name)

        # --- Internal Registers ---
        self.PC = RH_reset_address          # 14-bit Program Counter
        self.FSM = 'STOP'           # State machine initial state
        
        # Memory interface: we are the SOURCE (master/initiator)
        self.mem = self.addInterfaceSource('ins', RH_mem)

        # --- Output Pins ---
        self.instructionOut = self.addOut('instructionOut', RH_instructionOut)
        self.Address_Out = self.addOut('Address_Out', RH_Address_Out)

        self.Value_Out = self.addOut('Value_Out',RH_Value_Out)

        self.Instruction_fetched = self.addOut('Instruction_fetched',RH_Instruction_fetched)
        self.Executed_Jump = self.addOut('Executed_Jump',RH_Executed_Jump)
        
        # --- Input Pins (Control Signals from Decoder/Execute stage) ---
        self.Load_Z = self.addIn('Load_Z', RH_Load_Z)
        self.address_ZL = self.addIn('address_ZL', RH_address_ZL)
        self.address_ZH = self.addIn('address_ZH', RH_address_ZH)
        
        self.Load_K = self.addIn('Load_K', RH_Load_K)
        self.K_select = self.addIn('K_select',RH_K_select)
        self.K7 = self.addIn('K7',RH_K7)
        self.K12 = self.addIn('K12',RH_K12)
        self.K7_22 = self.addIn('K7_22',RH_K7_22)
        
        self.Load_Jump = self.addIn('Load_Jump', RH_Load_Jump)
        self.relative_Absolute = self.addIn('relative_Absolute', RH_relative_Absolute)
    
        self.Load_Byte = self.addIn('Load_Byte', RH_Load_Byte)
        self.WriteVal = self.addIn('WriteVal', RH_WriteVal)

        self.Fetch_next_instruction = self.addIn('Fetch_next_instruction',RH_Fetch_next_instruction)

        self.Pc_valL =  self.addOut('Pc_valL',RH_Pc_valL)
        self.PC_valH =  self.addOut('Pc_valH',RH_Pc_valH)

        self.JumpWidth = self.addIn('JumpWidth',RH_JumpWidth)
        self.Load_PCL  = self.addIn('Load_PCL',RH_Load_PCL)
        self.Load_PCH = self.addIn('Load_PCH',RH_Load_PCH)

        self.PCL_LOAD_VAL = self.addIn('PCL_LOAD_VAL',RH_PCL_LOAD_VAL)
        self.PCH_LOAD_VAL = self.addIn('PCH_LOAD_VAL',RH_PCH_LOAD_VAL) 

        self.fetch_address = self.addIn('fetch_address',RH_fetch_address)
        self.Address_fetched = self.addOut('Address_fetched',RH_Address_fetched)

    def _select_K(self):
        """
        Multiplex between the three K sources based on K_select.
        0 = K7   (7-bit signed offset, conditional branches)
        1 = K12  (12-bit signed offset, RJMP/RCALL)
        2 = K7_22 (absolute target, JMP/CALL)
        Falls back to K7 for any unmapped select value.
        """
        sel = self.K_select.get()
        if sel == 0:
            return self.K7.get()
        elif sel == 1:
            return self.K12.get()
        elif sel == 2:
            return self.K7_22.get()
        else:
            return self.K7.get()

    def clock(self):

        # ---------------------------------------------------------
        # STATE: STOP - Halt Execution until Fetch_next_instruction
        # ---------------------------------------------------------
        if self.FSM == 'STOP':
            # Keep memory control signals cleanly deasserted
            self.mem.instype.prepare(0)
            self.mem.read.prepare(0)
            self.mem.write.prepare(0)
            # Keep handshake outputs deasserted while halted
            self.Instruction_fetched.prepare(0)
            self.Executed_Jump.prepare(0)

            # Transition to fetch if ControlBox Fetch_next_instruction execution
            if self.Fetch_next_instruction.get() == 1:
                self.FSM = 'FETCH_REQ'

        # ---------------------------------------------------------
        # STATE: FETCH_REQ - Initiate memory transaction
        # ---------------------------------------------------------
        elif self.FSM == 'FETCH_REQ':

            self.Instruction_fetched.prepare(0)
            self.Executed_Jump.prepare(0)
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

                # Also expose the raw fetched word on Value_Out for the
                # MemoryController (previously left undriven).
                self.Value_Out.prepare(fetched_instruction)

                # Signal to ControlBox / decoder that a new instruction is ready
                self.Instruction_fetched.prepare(1)
                
                # -----------------------------------------------------------------
                # PC UPDATE LOGIC - Evaluate all control signals for next address
                # -----------------------------------------------------------------
                load_z    = self.Load_Z.get()       # IJMP/ICALL via Z register
                load_k    = self.Load_K.get()        # Conditional branch taken
                load_jump = self.Load_Jump.get()     # RJMP/RCALL/JMP/CALL
                rel_abs   = self.relative_Absolute.get()  # 0=relative, 1=absolute
                k_val     = self._select_K()         # FIX: was self.K.get() -- no such pin existed

                # Base: sequential next PC
                next_pc = self.PC + 1

                # Track whether any jump was taken this cycle
                jumped = False

                # --- PC Multiplexer (priority ordered) ---
                if load_z == 1:
                    # ===== INDIRECT JUMP/CALL (IJMP/ICALL) =====
                    # Load PC from Z register (ZH:ZL)
                    z_val = (self.address_ZH.get() << 8) | self.address_ZL.get()
                    self.PC = z_val & 0x3FFF        # Mask to 14-bit address space
                    jumped = True

                elif load_jump == 1:
                    if rel_abs == 1:
                        # ===== ABSOLUTE JUMP/CALL (JMP/CALL) =====
                        # K holds full target address
                        self.PC = k_val & 0x3FFF
                    else:
                        # ===== RELATIVE JUMP/RCALL (RJMP/RCALL) =====
                        # K is 12-bit signed offset (-2048..+2047)
                        if k_val & 0x800:           # Bit 11 = sign bit
                            offset = k_val - 0x1000  # Sign-extend via arithmetic, not a wide mask
                        else:
                            offset = k_val
                        self.PC = (next_pc + offset) & 0x3FFF
                    jumped = True

                elif load_k == 1:
                    # ===== CONDITIONAL BRANCH TAKEN (BRxx, SBxx) =====
                    # K is 7-bit signed offset (-64..+63)
                    if k_val & 0x40:             # Bit 6 = sign bit
                        offset = k_val - 0x80     # Sign-extend via arithmetic
                    else:
                        offset = k_val
                    self.PC = (next_pc + offset) & 0x3FFF
                    jumped = True

                else:
                    # ===== SEQUENTIAL EXECUTION =====
                    self.PC = next_pc & 0x3FFF    # Always mask to 14 bits

                # Signal ControlBox that the jump target is committed
                self.Executed_Jump.prepare(1 if jumped else 0)

                # FIX: Do NOT loop straight back to FETCH_REQ. The handler
                # must wait for Fetch_next_instruction to be pulsed again
                # before fetching the next word. Go through the same
                # single-step trap used by the SPM write path.
                self.FSM = 'WAIT_Fetch_next_instruction_LOW'

        # ---------------------------------------------------------
        # STATE: WRITE_WAIT - Complete SPM write transaction  
        # ---------------------------------------------------------
        elif self.FSM == 'WRITE_WAIT':
            self.mem.write.prepare(0)
            self.mem.instype.prepare(0)
            
            if self.mem.resp.get() == 1:
                self.PC = (self.PC + 1) & 0x3FFF
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