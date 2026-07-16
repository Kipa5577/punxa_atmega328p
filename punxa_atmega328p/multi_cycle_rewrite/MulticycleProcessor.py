import py4hw

from .ControlBox import *
from .Datapath import *

class multicycleProcessor(py4hw.Logic):
    """
    Top-level CPU: exactly two peer components.

        Datapath   -- all storage (registers) and the units that compute
                      what goes into it (RomHandler, Instruction_decoder,
                      ALU_STRUC, MemoryInterfaceHandler).
        ControlBox -- MainFSM + INSTRUCTION_FSM_BOX + InterruptFSM, driving
                      Datapath purely through the D_* control/status
                      boundary below.

    External signature is unchanged from the pre-rewrite version, so
    existing testbenches (tb_ISA_tests_Multicycle.py etc.) should not need
    any changes.
    """

    def __init__(self, parent, name, Interrupt, Interrupt_Enable, ins_mem, memory, reset, reset_address=0,
                 Bus_Passthrough_Ranges=None):
        super().__init__(parent, name)

        self.reset = self.addIn('reset', reset)
        self.Interrupt = self.addIn('interrupt', Interrupt)
        self.Interrupt_Enable = self.addOut('Interrupt_Enable', Interrupt_Enable)
        self.ins_mem = self.addInterfaceSource('ins_mem', ins_mem)
        self.memory = self.addInterfaceSource('memory', memory)

        # -------------------------
        # Datapath <-> ControlBox boundary wires
        # -------------------------
        # Datapath -> ControlBox (status/handshakes)
        W_Resp = self.wire('W_Resp', 1)
        W_Branch = self.wire('W_Branch', 1)
        W_Skip = self.wire('W_Skip', 1)
        W_Instruction = self.wire('W_Instruction', 16)
        W_Instruction_fetched = self.wire('W_Instruction_fetched', 1)
        W_Instruction_decoded = self.wire('W_Instruction_decoded', 1)
        W_Executed_Jump = self.wire('W_Executed_Jump', 1)
        W_Address_fetched = self.wire('W_Address_fetched', 1)
        W_SPM_Done = self.wire('W_SPM_Done', 1)

        # ControlBox -> Datapath (control signals)
        W_LoadSelectMux = self.wire('W_LoadSelectMux', 3)
        W_LoadingMux = self.wire('W_LoadingMux', 5)
        W_Input_Select = self.wire('W_Input_Select', 5)
        W_WE_MEMORY = self.wire('W_WE_MEMORY', 6)
        W_Read_Write = self.wire('W_Read_Write', 2)
        W_mem_instr = self.wire('W_mem_instr', 5)
        W_IncDec = self.wire('W_IncDec', 3)
        W_InputSelect = self.wire('W_InputSelect', 1)
        W_WE_Buffer = self.wire('W_WE_Buffer', 4)
        W_Load_Z = self.wire('W_Load_Z', 1)
        W_Load_K = self.wire('W_Load_K', 1)
        W_K_Select = self.wire('W_K_Select', 2)
        W_Load_Jump = self.wire('W_Load_Jump', 1)
        W_relative_Absolute = self.wire('W_relative_Absolute', 1)
        W_Load_Byte = self.wire('W_Load_Byte', 1)
        W_Fetch_next_instruction = self.wire('W_Fetch_next_instruction', 1)
        W_Fetch_Address = self.wire('W_Fetch_Address', 1)
        W_WB_Addr = self.wire('W_WB_Addr', 8)
        W_JumpWidth = self.wire('W_JumpWidth', 1)
        W_LOAD_PCL = self.wire('W_LOAD_PCL', 1)
        W_LOAD_PCH = self.wire('W_LOAD_PCH', 1)
        W_LPM_req = self.wire('W_LPM_req', 2)
        W_SPM_req = self.wire('W_SPM_req', 2)

        # Interrupt-support signals crossing the same boundary (previously
        # dangling/unconnected at this top level -- see rewrite spec §10.1
        # bug note. CB_Interrupt_Entrance is informational/debug-only on
        # the Datapath side; I_Force_WE/Value feed the SREG_I override mux.)
        W_Interrupt_Entrance = self.wire('W_Interrupt_Entrance', 1)
        W_I_Force_WE = self.wire('W_I_Force_WE', 1)
        W_I_Force_Value = self.wire('W_I_Force_Value', 1)
        # FIX (SREG write race): single-cycle pulse, ControlBox -> Datapath,
        # marking the exact cycle the current instruction's leaf FSM
        # retires -- see ControlBox.py's CB_ALU_Commit docstring.
        W_ALU_Commit = self.wire('W_ALU_Commit', 1)

        # -------------------------
        # Sub-components
        # -------------------------
        Datapath(
            self, 'Datapath',
            reset=self.reset,
            ins_mem=ins_mem,
            memory=memory,
            reset_address=reset_address,
            Interrupt_Enable=self.Interrupt_Enable,
            Bus_Passthrough_Ranges=Bus_Passthrough_Ranges,

            D_Resp=W_Resp,
            D_Branch=W_Branch,
            D_Skip=W_Skip,
            D_Instruction=W_Instruction,
            D_Instruction_fetched=W_Instruction_fetched,
            D_Instruction_decoded=W_Instruction_decoded,
            D_Executed_Jump=W_Executed_Jump,
            D_Address_fetched=W_Address_fetched,
            D_SPM_Done=W_SPM_Done,

            D_LoadSelectMux=W_LoadSelectMux,
            D_LoadingMux=W_LoadingMux,
            D_Input_Select=W_Input_Select,
            D_WE_MEMORY=W_WE_MEMORY,
            D_Read_Write=W_Read_Write,
            D_mem_instr=W_mem_instr,
            D_IncDec=W_IncDec,
            D_InputSelect=W_InputSelect,
            D_WE_Buffer=W_WE_Buffer,
            D_Load_Z=W_Load_Z,
            D_Load_K=W_Load_K,
            D_K_Select=W_K_Select,
            D_Load_Jump=W_Load_Jump,
            D_relative_Absolute=W_relative_Absolute,
            D_Load_Byte=W_Load_Byte,
            D_Fetch_next_instruction=W_Fetch_next_instruction,
            D_Fetch_Address=W_Fetch_Address,
            D_WB_Addr=W_WB_Addr,
            D_JumpWidth=W_JumpWidth,
            D_LOAD_PCL=W_LOAD_PCL,
            D_LOAD_PCH=W_LOAD_PCH,
            D_LPM_req=W_LPM_req,
            D_SPM_req=W_SPM_req,
            D_I_Force_WE=W_I_Force_WE,
            D_I_Force_Value=W_I_Force_Value,
            D_ALU_Commit=W_ALU_Commit,
        )

        control_Box(
            self, 'ControlBox',
            CB_Instruction=W_Instruction,
            CB_Resp=W_Resp,
            CB_Branch=W_Branch,
            CB_Skip=W_Skip,
            CB_Interrupt=self.Interrupt,
            CB_Instruction_fetched=W_Instruction_fetched,
            CB_Instruction_decoded=W_Instruction_decoded,
            CB_Executed_Jump=W_Executed_Jump,
            CB_Address_fetched=W_Address_fetched,
            CB_LoadSelectMux=W_LoadSelectMux,
            CB_LoadingMux=W_LoadingMux,
            CB_Input_Select=W_Input_Select,
            CB_WE_MEMORY=W_WE_MEMORY,
            CB_Read_Write=W_Read_Write,
            CB_mem_instr=W_mem_instr,
            CB_IncDec=W_IncDec,
            CB_InputSelect=W_InputSelect,
            CB_WE_Buffer=W_WE_Buffer,
            CB_Load_Z=W_Load_Z,
            CB_Load_K=W_Load_K,
            CB_K_Select=W_K_Select,
            CB_Load_Jump=W_Load_Jump,
            CB_relative_Absolute=W_relative_Absolute,
            CB_Load_Byte=W_Load_Byte,
            CB_Fetch_next_instruction=W_Fetch_next_instruction,
            CB_Fetch_Address=W_Fetch_Address,
            CB_WB_Addr=W_WB_Addr,
            CB_JumpWidth=W_JumpWidth,
            CB_LOAD_PCL=W_LOAD_PCL,
            CB_LOAD_PCH=W_LOAD_PCH,
            CB_LPM_req=W_LPM_req,
            CB_SPM_req=W_SPM_req,
            # --- bug fix: these 4 were previously omitted from this call
            # entirely even though control_Box() requires them (see
            # rewrite spec §10.1) ---
            CB_SPM_Done=W_SPM_Done,
            CB_Interrupt_Entrance=W_Interrupt_Entrance,
            CB_I_Force_WE=W_I_Force_WE,
            CB_I_Force_Value=W_I_Force_Value,
            CB_ALU_Commit=W_ALU_Commit,
            # --- new: CPU-wide reset rollout ---
            CB_Reset=self.reset,
        )
