import py4hw

class Instruction_decoder(py4hw.Logic):
    def __init__(self, parent, name: str,
                 # Inputs
                 Instruction, SKIP,
                 # Outputs
                 Address_XYZ, Read_Write, ALU_Instr, ExtraAddr, 
                 K, PC_Jump_val, Sval, ValueToLoad, Q, 
                 LoadingMux, WritingMux, ImputSelect, WE):
        super().__init__(parent, name)

        # --- Inputs ---
        self.Instruction = self.addIn('Instruction', Instruction)
        self.SKIP = self.addIn('SKIP', SKIP)

        # --- Outputs ---
        # Memory Interface Controls
        self.Address_XYZ = self.addOut('Address_XYZ', Address_XYZ) # Connects to Mem_instruction
        self.Read_Write = self.addOut('Read_Write', Read_Write)
        self.WE = self.addOut('WE', WE)
        self.LoadingMux = self.addOut('LoadingMux', LoadingMux)
        self.WritingMux = self.addOut('WritingMux', WritingMux)    # Connects to LoadSelectMux
        self.ImputSelect = self.addOut('ImputSelect', ImputSelect)

        # ALU & Execution Controls
        self.ALU_Instr = self.addOut('ALU_Instr', ALU_Instr)
        self.ExtraAddr = self.addOut('ExtraAddr', ExtraAddr)       # E.g., Rd/Rr direct addresses
        self.K = self.addOut('K', K)                               # Immediate value
        self.Q = self.addOut('Q', Q)                               # Displacement value
        self.PC_Jump_val = self.addOut('PC_Jump_val', PC_Jump_val) # For Branch/Jump
        self.Sval = self.addOut('Sval', Sval)                      # Bit/Status flag tests
        self.ValueToLoad = self.addOut('ValueToLoad', ValueToLoad) # Direct Data

        # --- Internal State Machine ---
        # 0 = Fetch Instruction (handled by PC, decoder idle/reset)
        # 1 = Fetch Rr from Memory
        # 2 = Fetch Rd from Memory / Execute ALU
        # 3 = Write Result back to Memory
        self.state = 0

    def Clock(self):
        # 1. Read Current Instruction
        inst = self.Instruction.get()
        skip = self.SKIP.get()

        if skip:
            # If the ALU SKIP flag is high, we bypass execution and reset state
            self.reset_control_lines()
            self.state = 0
            return

        # 2. Decode Instruction Fields (Standard AVR 16-bit mapping)
        # You will need to expand these masks based on your specific ISA implementation
        opcode = (inst >> 12) & 0xF
        
        # Extract Rd (Destination Register 0-31) - Usually bits 4-8
        Rd_addr = (inst >> 4) & 0x1F
        
        # Extract Rr (Source Register 0-31) - Usually bits 0-3 and bit 9
        Rr_addr = (inst & 0x0F) | ((inst >> 5) & 0x10)
        
        # Extract K (8-bit immediate) - Usually split across bits 8-11 and 0-3
        k_val = ((inst >> 4) & 0xF0) | (inst & 0x0F)
        
        # Extract q (6-bit displacement for Y+q, Z+q)
        q_val = ((inst >> 8) & 0x20) | ((inst >> 7) & 0x18) | (inst & 0x07)

        # Push immediate/displacement values to the bus
        self.K.put(k_val)
        self.Q.put(q_val)

        # =========================================================
        # EXECUTION STATE MACHINE
        # =========================================================
        
        # --- Example 1: ALU Operations (ADD, SUB, AND, etc.) ---
        # Let's assume Opcode 0x0 or 0x1 are register-to-register ALU ops
        if opcode in (0x0, 0x1):
            
            if self.state == 0:
                # Cycle 1: Fetch Rr from memory
                self.Address_XYZ.put(8)          # MEM_RAM_ADDR_REG (Direct Addressing mode)
                self.ExtraAddr.put(Rr_addr)      # Route Rr address to Memory's RomAddress
                self.Read_Write.put(0)           # READ mode
                self.WE.put(0)
                
                # Advance state
                self.state = 1

            elif self.state == 1:
                # Cycle 2: Rr is now on the memory bus. We assume it latches into ALU ImputRegB0.
                # Now, set up the fetch for Rd.
                self.Address_XYZ.put(8)          # MEM_RAM_ADDR_REG
                self.ExtraAddr.put(Rd_addr)      # Route Rd address to Memory
                self.Read_Write.put(0)           # READ mode
                self.WE.put(0)
                
                self.state = 2

            elif self.state == 2:
                # Cycle 3: Rd is now on the bus. ALU executes the math.
                # Prepare to write the result back to Rd memory address.
                self.ALU_Instr.put(inst & 0x03FF) # Send specific ALU operation code
                
                # Wait for ALU combinational logic to settle...
                self.state = 3

            elif self.state == 3:
                # Cycle 4: Write ALU result back to Memory
                self.Address_XYZ.put(8)          # MEM_RAM_ADDR_REG (Still pointing to Rd)
                self.ExtraAddr.put(Rd_addr)
                self.Read_Write.put(1)           # WRITE mode
                
                # Configure Memory Handler Multiplexers
                self.ImputSelect.put(0)          # INPUT_DATABUS (to take ALU output)
                self.WE.put(1)                   # Trigger Memory Write
                
                # Instruction complete, reset to fetch next instruction
                self.state = 0

        # --- Example 2: Load/Store with X/Y/Z Pointers ---
        # Assume Opcode 0x8 is LD/ST via pointer (e.g., LD Rd, X+)
        elif opcode == 0x8:
            if self.state == 0:
                # Execute Memory Pointer Operation
                # Instruction bits define if we use X, Y, or Z and if it's Post-Inc/Pre-Dec
                ptr_mode = (inst >> 2) & 0xF     # Extract MEM_X, MEM_X_PLUS, etc.
                self.Address_XYZ.put(ptr_mode)
                
                # Example: If bit 9 is 1, it's a STORE (Write to memory), if 0, LOAD (Read from memory)
                is_store = (inst >> 9) & 1
                self.Read_Write.put(is_store)
                self.WE.put(is_store)            # Write if STORE
                
                self.state = 1

            elif self.state == 1:
                # For a LOAD, data is now on the bus. Write it to register file (Rd).
                is_store = (inst >> 9) & 1
                if not is_store:
                    self.Address_XYZ.put(8)      # MEM_RAM_ADDR_REG
                    self.ExtraAddr.put(Rd_addr)  # Point to Rd
                    self.Read_Write.put(1)       # WRITE to register file in memory
                    self.ImputSelect.put(0)      # Take from Databus
                    self.WE.put(1)
                
                self.state = 0

        # --- Default / Unimplemented ---
        else:
            self.reset_control_lines()
            self.state = 0

    def reset_control_lines(self):
        """Helper to safely zero-out control lines when idle."""
        self.Address_XYZ.put(0)
        self.Read_Write.put(0)
        self.WE.put(0)
        self.ALU_Instr.put(0)
        self.LoadingMux.put(0)
        self.WritingMux.put(0)
        self.ImputSelect.put(0)