# Integer state encoding (was string-based; converted for
# stock py4hw Verilog-transpiler compatibility -- see report):
#   0 = 'STOP'
#   1 = 'INCREMENT_STORED_PC'
#   2 = 'READ_L_BYTE_OF_PC'
#   3 = 'LOAD_L_BYTE_OF_PC_TO_STACK'
#   4 = 'READ_H_BYTE_OF_PC'
#   5 = 'LOAD_H_BYTE_OF_PC_TO_STACK'
#   6 = 'FETCH_K_OFFSET'
#   7 = 'WAIT_K_OFFSET'
#   8 = 'JUMP_R'
#   9 = 'FETCH_ADDRESS_Z_L'
#   10 = 'WAIT_FETCH_ADDRESS_Z_L'
#   11 = 'LOAD_ADDRESS_Z_L'
#   12 = 'FETCH_ADDRESS_Z_H'
#   13 = 'WAIT_FETCH_ADDRESS_Z_H'
#   14 = 'LOAD_ADDRESS_Z_H'
#   15 = 'JUMP_I'
#   16 = 'FETCH_ADDRESS_BYTE'
#   17 = 'WAIT_ADDRESS_RECONSTRUCTION'
#   18 = 'JUMP'
#   19 = 'FETCH_L_BYTE_OF_PC'
#   20 = 'WAIT_FETCH_L_BYTE_OF_PC'
#   21 = 'LATCH_L_BYTE_OF_PC'
#   22 = 'STORE_L_BYTE_OF_PC'
#   23 = 'FETCH_H_BYTE_OF_PC'
#   24 = 'WAIT_FETCH_H_BYTE_OF_PC'
#   25 = 'LATCH_H_BYTE_OF_PC'
#   26 = 'STORE_H_BYTE_OF_PC'

import py4hw

STATES = [
    "STOP",

    # Prepare return address
    "INCREMENT_STORED_PC",

    # Push PC
    # NOTE: SP lives permanently inside MemoryInterfaceHandler (self.SPL/self.SPH).
    # Any access to SRAM 0x5D/0x5E is intercepted there and redirected to those
    # same registers, and MEM_SP addressing reads/writes them directly. There is
    # no separate copy in SRAM to fetch into a buffer or write back afterwards
    # (the old FETCH_STACK_POINTER_*/SAVE_DECREMENTED_SP_* dance is gone) -
    # SP is just used directly, the way a real CPU's SP register works.
    "READ_L_BYTE_OF_PC",
    "LOAD_L_BYTE_OF_PC_TO_STACK",

    "READ_H_BYTE_OF_PC",
    "LOAD_H_BYTE_OF_PC_TO_STACK",

    # RCALL
    "FETCH_K_OFFSET",
    "WAIT_K_OFFSET",
    "JUMP_R",

    # ICALL
    "FETCH_ADDRESS_Z_L",
    "WAIT_FETCH_ADDRESS_Z_L",
    "LOAD_ADDRESS_Z_L",

    "FETCH_ADDRESS_Z_H",
    "WAIT_FETCH_ADDRESS_Z_H",
    "LOAD_ADDRESS_Z_H",

    "JUMP_I",

    # CALL
    "FETCH_ADDRESS_BYTE",
    "WAIT_ADDRESS_RECONSTRUCTION",
    "JUMP",

    # RET
    "FETCH_L_BYTE_OF_PC",
    "WAIT_FETCH_L_BYTE_OF_PC",
    "LATCH_L_BYTE_OF_PC",
    "STORE_L_BYTE_OF_PC",

    "FETCH_H_BYTE_OF_PC",
    "WAIT_FETCH_H_BYTE_OF_PC",
    "LATCH_H_BYTE_OF_PC",
    "STORE_H_BYTE_OF_PC",
]

OPCODE_RJMP  = 29
OPCODE_IJMP  = 30
OPCODE_JMP   = 31

OPCODE_RET   = (
                35, # RET
                # 36 (RETI) intentionally NOT here — InterruptFSM owns
                # RETI now (it also has to re-enable the I flag on return,
                # which this FSM has no mechanism to do). FSM_SELECTOR no
                # longer routes RETI's `run` to CallRetFSM at all.
                )
OPCODE_RCALL = 32 
OPCODE_ICALL = 33
OPCODE_CALL  = 34

# 2-byte (1-word) instructions
two_byte_instructions = [
    'ADD', 'ADC', 'ADIW', 'SUB', 'SUBI', 'SBC', 'SBCI', 'SBIW', 'AND', 'ANDI', 
    'OR', 'ORI', 'EOR', 'COM', 'NEG', 'SBR', 'CBR', 'INC', 'DEC', 'TST', 'CLR', 
    'SER', 'MUL', 'MULS', 'MULSU', 'FMUL', 'FMULS', 'FMULSU', 'RJMP', 'IJMP', 
    'RCALL', 'ICALL', 'RET', 'RETI', 'CPSE', 'CP', 'CPC', 'CPI', 'SBRC', 'SBRS', 
    'SBIC', 'SBIS', 'BRBS', 'BRBC', 'BREQ', 'BRNE', 'BRCS', 'BRCC', 'BRSH', 
    'BRLO', 'BRMI', 'BRPL', 'BRGE', 'BRLT', 'BRHS', 'BRHC', 'BRTS', 'BRTC', 
    'BRVS', 'BRVC', 'BRIE', 'BRID', 'SBI', 'CBI', 'LSL', 'LSR', 'ROL', 'ROR', 
    'ASR', 'SWAP', 'BSET', 'BCLR', 'BST', 'BLD', 'SEC', 'CLC', 'SEN', 'CLN', 
    'SEZ', 'CLZ', 'SEI', 'CLI', 'SES', 'CLS', 'SEV', 'CLV', 'SET', 'CLT', 'SEH', 
    'CLH', 'MOV', 'MOVW', 'LDI', 'LDX', 'LDX+', 'LD-X', 'LDY', 'LDY+', 'LD-Y', 
    'LDDY', 'LDZ', 'LDZ+', 'LD-Z', 'LDDZ', 'STX', 'STX+', 'ST-X', 'STY', 'STY+', 
    'ST-Y', 'STDY', 'STZ', 'STZ+', 'ST-Z', 'STDZ', 'LPM', 'LPMZ', 'LPMZ+', 
    'SPM', 'IN', 'OUT', 'PUSH', 'POP', 'NOP', 'SLEEP', 'WDR', 'BREAK'
]

# 4-byte (2-word) instructions
four_byte_instructions = ['JMP', 'CALL', 'LDS', 'STS']

class CallRet_FSM(py4hw.Logic):
    def __init__(self, parent, name,
                 # ── Logic inputs ─────────────────────────────────────────
                 run, # 1-Bit The main FSM pulls this to high to trigger this FSM
                 done, # 1-Bit The main FSM receives this to high to indicate that this FSM has finished
                 # ── Inputs ──────────────────────────────────────────────
                 Instruction,        # 8-bit opcode from instruction decoder
                 Resp,               # 1-bit: memory operation Finished
                 Address_fetched,    # 1-bit: romHandler Fetched address
                 Branch,             # 1-bit: ALU branch condition met
                 Executed_Jump,      # This tell the control box that the romHandler has successfully executed the jump instruction

                 # ── Memory Interface Outputs ─────────────────────────────
                 LoadSelectMux,      # address mux for memory reads
                 LoadingMux,         # selects which pointer reg is loaded
                 InputSelectMemory,  # data source mux for memory writes
                 WEMEMORY,           # write enable for pointer registers
                 Read_Write,         # 0=idle, 1=write , 2=read
                 Mem_Instruction,    # pointer selection for Mem_instruction in MemoryInterface
                 IncDec,             # This increments or Decrements address
                 Fetch_next_instruction,

                 # ── ALU Buffer Outputs ───────────────────────────────────
                 InputSelectBuffer,  # 1 = Load Data in to Rr0 , 0 = Load K in to Rr0
                 WEBUFFER,           # 1 = Rd0, 2 = Rd1, 3 = Rr0, 4 = Rr1, 5 = IOBuffer

                 # ── ROM Handler Outputs ──────────────────────────────────
                 Load_Z,             # load Z pointer from program memory
                 Load_K,             # load immediate K to rom loader for relative or absolute jump
                 Load_Jump,          # trigger PC jump
                 relative_Absolute,  # 0=relative, 1=absolute jump
                 Load_Byte,          # 0 = fetches form rom  1 = writes to rom
                 Fetch_Address,      # In the case of STS instruction to fetch the instruction address
                 LOAD_PCL,
                 LOAD_PCH,
                 K_Select,

                 # ── Write-back address ───────────────────────────────────
                 WB_Addr,            # 5-bit explicit write-back address 
                                  reset=None,
             ):
        super().__init__(parent, name)
        self.reset = self.addIn('reset', reset)  # always driven by a real wire in this project (see report)

        # ── Logic inputs ─────────────────────────────────────────────────
        self.run                   = self.addIn('run', run)
        self.done                  = self.addOut('done', done)
        
        # ── Register inputs ──────────────────────────────────────────────
        self.Instruction           = self.addIn('Instruction', Instruction)
        self.Resp                  = self.addIn('Resp', Resp)
        self.Branch                = self.addIn('Branch', Branch)
        self.Executed_Jump         = self.addIn('Executed_Jump', Executed_Jump)
        self.Address_fetched       = self.addIn('Address_fetched', Address_fetched)

        # ── Register outputs ─────────────────────────────────────────────
        self.LoadSelectMux         = self.addOut('LoadSelectMux', LoadSelectMux)
        self.LoadingMux            = self.addOut('LoadingMux', LoadingMux)
        self.InputSelectMemory     = self.addOut('InputSelectMemory', InputSelectMemory)
        self.WEMEMORY              = self.addOut('WEMEMORY', WEMEMORY)
        self.Read_Write            = self.addOut('Read_Write', Read_Write)
        self.Mem_Instruction       = self.addOut('Mem_Instruction', Mem_Instruction)
        self.IncDec                = self.addOut('IncDec', IncDec)

        self.InputSelectBuffer     = self.addOut('InputSelectBuffer', InputSelectBuffer)
        self.WEBUFFER              = self.addOut('WEBUFFER', WEBUFFER)

        self.Load_Z                = self.addOut('Load_Z', Load_Z)
        self.Load_K                = self.addOut('Load_K', Load_K)
        self.Load_Jump             = self.addOut('Load_Jump', Load_Jump)
        self.relative_Absolute     = self.addOut('relative_Absolute', relative_Absolute)
        self.Load_Byte             = self.addOut('Load_Byte', Load_Byte)

        self.WB_Addr               = self.addOut('WB_Addr', WB_Addr)
        self.Fetch_Address         = self.addOut('Fetch_Address', Fetch_Address)

        self.LOAD_PCL              = self.addOut('LOAD_PCL', LOAD_PCL)
        self.LOAD_PCH              = self.addOut('LOAD_PCH', LOAD_PCH)

        self.K_SELECT              = self.addOut('K_SELECT',K_Select)

        # ── FSM state ────────────────────────────────────────────────────
        self.current_state = 0
        self._latched_inst = 0
        self._wb_addr_val = 0
        self._pointer_update_pending = 0  # was False; int form required for the stock transpiler's __init__ parser (see report)
        self.debug = 0
        
    def clock(self):
        if self.reset.get():  # reset is always driven by a real wire in this project (see report)
            self.current_state = 0
            self.done.prepare(0)
            self.LoadSelectMux.prepare(0)
            self.LoadingMux.prepare(0)
            self.InputSelectMemory.prepare(0)
            self.WEMEMORY.prepare(0)
            self.Read_Write.prepare(0)
            self.Mem_Instruction.prepare(0)
            self.IncDec.prepare(0)
            self.InputSelectBuffer.prepare(0)
            self.WEBUFFER.prepare(0)
            self.Load_Z.prepare(0)
            self.Load_K.prepare(0)
            self.Load_Jump.prepare(0)
            self.relative_Absolute.prepare(0)
            self.Load_Byte.prepare(0)
            self.WB_Addr.prepare(0)
            self.Fetch_Address.prepare(0)
            self.LOAD_PCL.prepare(0)
            self.LOAD_PCH.prepare(0)
            self.K_SELECT.prepare(0)
        else:

            # Read inputs
            inst              = self.Instruction.get()
            resp              = self.Resp.get()
            branch            = self.Branch.get()
            executed_jump     = self.Executed_Jump.get()
            run_active               = self.run.get()
            address_fetched   = self.Address_fetched.get()

            # Default internal wire states
            InputSelect_Buffer = 0       
            WE_Buffer = 0
            LoadSelectMux = 0 
            LoadingMux = 0
        

            RH_K_select = 0
            RH_Load_K = 0

            Read_Write = 0
        
            Mem_Instruction = 0
            IncDec = 0
            InputSelect_Memory = 0
            WE_Memory = 0
            WB_Addr = 0

            Load_Z = 0
            Load_K = 0
            Load_Jump = 0
            relative_Absolute = 0
            Load_Byte = 0
            Fetch_Address = 0
        
            # New defaults for PC loading
            Load_PCL = 0
            Load_PCH = 0

            done = 0

            JumpWidth = 1
            K_select = 0

            state = self.current_state
            i     = self._latched_inst
            next_state = state

            # ================================================================
            # STATE MACHINE
            # ================================================================

            if state == 0:
                if run_active == 1:
                    self._latched_inst = inst

                    # Route RJMP/IJMP/JMP directly to their jump states.
                    # RCALL/ICALL/CALL/RET/RETI all touch the stack pointer, but SP
                    # now lives permanently inside MemoryInterfaceHandler (self.SPL/
                    # self.SPH) — any access to 0x5D/0x5E is intercepted there and
                    # redirected straight to those registers, so there's no external
                    # SRAM copy to sync from first. We go straight to the push
                    # (CALL family) or pop (RET family) using Mem_Instruction = 7
                    # (MEM_SP), which reads/writes the resident SP directly — the
                    # same "SP is just always there" model a real CPU's SP uses.
                    if self._latched_inst == 29:
                        next_state = 6
                    elif self._latched_inst == 30:
                        next_state = 9
                    elif self._latched_inst == 31:
                        next_state = 16
                    elif ((self._latched_inst == 35)):
                        next_state = 19
                    else: # RCALL, ICALL, CALL
                        next_state = 4

            # ------------------------------------------------
            # CALL / RCALL / ICALL
            # ------------------------------------------------

            elif state == 4:
                # Issue cycle: assert the write for PCH -> [SP] here so the
                # request has one full cycle to be seen before we ever sample
                # resp. IncDec only fires on this issue cycle.
                Read_Write = 1
                Mem_Instruction = 7
                InputSelect_Memory = 15     # INPUT_PCH
                IncDec = 3                  # post-decrement SP after this write
                next_state = 5

            elif state == 5:
                # Wait cycle: re-assert the same transaction but hold IncDec at
                # 0 so SP isn't decremented again on every retry while resp
                # settles (mirrors WAIT_FETCH_L_BYTE_OF_PC below).
                Read_Write = 1
                Mem_Instruction = 7
                InputSelect_Memory = 15
                IncDec = 0
                if resp == 1:
                    next_state = 2

            elif state == 2:
                # Issue cycle: assert the write for PCL -> [SP] here.
                Read_Write = 1
                Mem_Instruction = 7
                InputSelect_Memory = 14     # INPUT_PCL
                IncDec = 3                  # post-decrement SP after this write
                next_state = 3

            elif state == 3:
                # Wait cycle: hold IncDec at 0 while polling resp.
                Read_Write = 1
                Mem_Instruction = 7
                InputSelect_Memory = 14
                IncDec = 0
                if resp == 1:
                    # PC has been pushed and SP already lives updated in
                    # MemoryInterfaceHandler's resident SPL/SPH — no separate
                    # SRAM write-back needed. Dispatch straight to the jump.
                    if i == 32:
                        next_state = 6
                    elif i == 33:
                        next_state = 9
                    else: # CALL
                        next_state = 16

            # ------------------------------------------------
            # RCALL / RJMP
            # ------------------------------------------------
            elif state == 6:
                Load_K = 1                  # Tell ROM loader to expect offset
                next_state = 7

            elif state == 7:
                next_state = 8

            elif state == 8:
                Load_Jump = 1
                K_select = 1                 # FIX: Use K12 for 12-bit offsets (RJMP/RCALL)
                relative_Absolute = 0       # 0 = Relative jump (PC + K)
                if executed_jump == 1:
                    next_state = 0
                    done = 1

            # ------------------------------------------------
            # ICALL / IJMP
            # ------------------------------------------------
            elif state == 9:
                WB_Addr = 30                  # R30 = ZL
                Mem_Instruction = 14          # MEM_WB_ADDR
                Read_Write = 2                # Read
                InputSelect_Memory = 1
                next_state = 10

            elif state == 10:
                WB_Addr = 30
                Mem_Instruction = 14
                Read_Write = 2
                InputSelect_Memory = 1

                if resp == 1:
                    next_state = 11

            elif state == 11:
                WB_Addr = 30                  # R30 = ZL
                Mem_Instruction = 14          # MEM_WB_ADDR
                Read_Write = 2                # Read
                InputSelect_Memory = 1
                WE_Memory = 1
                LoadingMux = 5                # LOAD_ZL
                next_state = 12

            elif state == 12:
                WB_Addr = 31                  # R31 = ZH
                Mem_Instruction = 14
                Read_Write = 2
                InputSelect_Memory = 1
                next_state = 13

            elif state == 13:
                WB_Addr = 31
                Mem_Instruction = 14
                Read_Write = 2
                InputSelect_Memory = 1

                if resp == 1:
                    next_state = 14

            elif state == 14:
                WB_Addr = 31
                Mem_Instruction = 14
                Read_Write = 2
                WE_Memory = 1
                LoadingMux = 6                # LOAD_ZH
                next_state = 15

            elif state == 15:
                # FIX: RomHandler's STOP-state jump logic has two independent
                # paths: Load_Z (PC <- {ZH,ZL} from MemoryInterfaceHandler's
                # address_ZL/address_ZH outputs) and Load_Jump+relative_Absolute
                # (PC <- K-mux value | latched_addr_word, driven by K_select).
                # ICALL/IJMP just spent 6 states loading the Z register into
                # MIH's internal ZregL/ZregH — but asserting Load_Jump here
                # takes the WRONG path: K_select defaults to 0 (K7), so this
                # jumped using a stale/unrelated K7 offset combined with
                # whatever latched_addr_word was left over from the last
                # JMP/CALL/LDS/STS, landing PC on garbage instead of Z.
                Load_Z = 1
                if executed_jump == 1:
                    done = 1
                    next_state = 0

            # ------------------------------------------------
            # CALL / JMP
            # ------------------------------------------------
            elif state == 16:
                Fetch_Address = 1           # Get absolute 32-bit address word
                next_state = 17
 
            elif state == 17:
                if address_fetched == 1:
                    # Fetch_Address must be driven to 0 in this state!
                    Fetch_Address = 0 
                    next_state = 18
 
            elif state == 18:
                Load_Jump = 1
                relative_Absolute = 1       # Absolute Jump
                K_select = 2                 # K7_22 source (CALL/JMP absolute 22-bit address)
                if executed_jump == 1:
                    next_state = 0
                    done = 1


            # ------------------------------------------------
            # RET (Pop PC from Stack)
            # ------------------------------------------------
            elif state == 19:
                Read_Write = 2              # Read Memory
                Mem_Instruction = 7         # MEM_SP: use buffered SP as address
                IncDec = 4                  # 4 = Pre-increment SP (standard AVR POP)
                next_state = 20
 
            elif state == 20:
                Read_Write = 2
                Mem_Instruction = 7
                IncDec = 0                  
                if resp == 1:
                    # Drop to idle before latching — don't keep asking MIH to
                    # read again while we're about to sample its output bus.
                    next_state = 21

            elif state == 21:
                # One idle cycle with no memory transaction in flight, so
                # BusData / PCL_LOAD_VAL is guaranteed stable before we pulse
                # Load_PCL on the next cycle.
                next_state = 22
 
            elif state == 22:
                Load_PCL = 1                # Assert PCL load pin (memory idle)
                next_state = 23
 
            elif state == 23:
                Read_Write = 2              
                Mem_Instruction = 7
                IncDec = 4                  # Pre-increment SP again
                next_state = 24
 
            elif state == 24:
                Read_Write = 2
                Mem_Instruction = 7
                IncDec = 0                  
                if resp == 1:
                    next_state = 25

            elif state == 25:
                # Same settle cycle as the L byte, before pulsing Load_PCH.
                next_state = 26
 
            elif state == 26:
                # RET is a direct PC load (PCL then PCH), not a jump — RomHandler
                # never asserts Executed_Jump for Load_PCL/Load_PCH-only loads,
                # so we must NOT wait on it here (that caused an infinite loop).
                # Pulse Load_PCH and finish immediately.
                Load_PCH = 1                # Assert PCH load pin (memory idle)
                next_state = 0
                done = 1

            # ================================================================
            # Drive outputs
            # ================================================================

            self.LoadSelectMux.prepare(LoadSelectMux)
            self.LoadingMux.prepare(LoadingMux)
            self.InputSelectMemory.prepare(InputSelect_Memory)
            self.WEMEMORY.prepare(WE_Memory)
            self.Read_Write.prepare(Read_Write)
            self.Mem_Instruction.prepare(Mem_Instruction)
            self.IncDec.prepare(IncDec)

            self.InputSelectBuffer.prepare(InputSelect_Buffer)
            self.WEBUFFER.prepare(WE_Buffer)

            self.Load_Z.prepare(Load_Z)
            self.Load_K.prepare(Load_K)
            self.Load_Jump.prepare(Load_Jump)
            self.relative_Absolute.prepare(relative_Absolute)
            self.Load_Byte.prepare(Load_Byte)
        
            #self.Fetch_next_instruction.prepare(0) 
            self.Fetch_Address.prepare(Fetch_Address)

            self.LOAD_PCL.prepare(Load_PCL)
            self.LOAD_PCH.prepare(Load_PCH)

            self.WB_Addr.prepare(WB_Addr)
            self.done.prepare(done)

            self.K_SELECT.put(K_select)

            if self.debug and (self.current_state != 0):
                print(
                    f"CALLRET_TRACE | "
                    f"{self.current_state} -> {next_state} | "
                    f"Inst:{i} "
                    f"MemInstr:{Mem_Instruction} "
                    f"RW:{Read_Write} "
                    f"Resp:{resp} "
                    f"Done:{done}"
                )

            self.current_state = next_state