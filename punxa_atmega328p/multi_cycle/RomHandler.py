import py4hw
# import Memory  # Assuming MemoryInterface is available in your workspace

class RomHandler(py4hw.Logic):
    def __init__(self, parent, name,
                 # --- Memory Interface (Bundled) ---
                 mem,  # Type: MemoryInterface
                 
                 # --- Outputs ---
                 instructionOut, Address_Out,
                 
                 # --- Indirect Jumps (IJMP, ICALL) ---
                 Load_Z, address_ZL, address_ZH,
                 
                 # --- Branches (BRxx) & Jumps (RJMP, JMP, CALL) ---
                 Load_K, K, 
                 Load_Jump, relative_Absolute, 
                 
                 # --- ROM Writing (SPM) ---
                 Load_Byte, WriteVal,
                 
                 # Initialization
                 reset_address=0):
        
        super().__init__(parent, name)

        # --- Internal Registers ---
        self.PC = reset_address
        self.FSM = 'FETCH_REQ'  # Initial state
        
        # Store the memory interface directly as an Interface Source
        self.mem = self.addInterfaceSource('ins', mem)

        # --- Output Pins ---
        self.instructionOut = self.addOut('instructionOut', instructionOut)
        self.Address_Out = self.addOut('Address_Out', Address_Out)
        
        # --- Input Pins (Execution Controls) ---
        self.Load_Z = self.addIn('Load_Z', Load_Z)
        self.address_ZL = self.addIn('address_ZL', address_ZL)
        self.address_ZH = self.addIn('address_ZH', address_ZH)
        
        self.Load_K = self.addIn('Load_K', Load_K)
        self.K = self.addIn('K', K)
        
        self.Load_Jump = self.addIn('Load_Jump', Load_Jump)
        self.relative_Absolute = self.addIn('relative_Absolute', relative_Absolute)
        
        self.Load_Byte = self.addIn('Load_Byte', Load_Byte)
        self.WriteVal = self.addIn('WriteVal', WriteVal)


    def Clock(self):
        # 1. Output the current PC so the rest of the CPU knows where we are
        self.Address_Out.put(self.PC)

        # ---------------------------------------------------------
        # FETCH & EXECUTE STATE MACHINE
        # ---------------------------------------------------------
        match self.FSM:

            case 'FETCH_REQ':
                
                self.mem.instype.put(0) 
                
                # Prioritize Writing to ROM if requested (SPM instruction)
                if self.Load_Byte.get() == 1:
                    self.mem.write.put(1)                # Enable Write
                    self.mem.read.put(0)                 # Disable Read
                    self.mem.address.put(self.PC)           
                    self.mem.write_data.put(self.WriteVal.get())
                    self.FSM = 'WRITE_WAIT'
                
                else:
                    # Normal Execution: Request the next instruction
                    self.mem.write.put(0)                # Disable Write
                    self.mem.read.put(1)                 # Enable Read
                    self.mem.address.put(self.PC)
                    self.FSM = 'FETCH_WAIT'

            case 'FETCH_WAIT':
                # Depress the read request signal so we don't trigger memory twice
                self.mem.read.put(0)
                self.mem.instype.put(0)
                
                # Wait for memory latency (resp = 1 means operation performed)
                if self.mem.resp.get() == 1:
                    
                    # Latch and output the fetched instruction
                    fetched_instruction = self.mem.read_data.get()
                    self.instructionOut.put(fetched_instruction)
                    
                    # Evaluate Control Signals 
                    load_z = self.Load_Z.get()
                    load_k = self.Load_K.get()           
                    load_jump = self.Load_Jump.get()     
                    rel_abs = self.relative_Absolute.get() 
                    k_val = self.K.get()

                    # Standard PC increment
                    next_pc = self.PC + 1

                    # --- PC MULTIPLEXER ---
                    if load_z == 1:
                        # Indirect Jump/Call
                        z_val = (self.address_ZH.get() << 8) | self.address_ZL.get()
                        self.PC = z_val

                    elif load_jump == 1:
                        if rel_abs == 1:
                            # Absolute Jump/Call
                            self.PC = k_val
                        else:
                            # Relative Jump/Call
                            self.PC = next_pc + k_val &0xFFF

                    elif load_k == 1:
                        # Taken Conditional Branch
                        self.PC = next_pc + k_val

                    else:
                        # Normal Sequential Execution
                        self.PC = next_pc

                    self.FSM = 'FETCH_REQ'

            case 'WRITE_WAIT':
                # Depress the write request signal
                self.mem.write.put(0)
                self.mem.instype.put(0)
                
                if self.mem.resp.get() == 1:
                    self.FSM = 'FETCH_REQ'
                    
            case _:
                self.FSM = 'FETCH_REQ'