import py4hw
from .CallRetFSM import * 
from .OppFSM import * 
from .LDSTFSM import * 
from .PopPushFSM import * 
from .MovFSM import * 
from .LPM import * 
from .FSM_SELECTOR import * 
from .FSM_OutputMerger import * 
# =============================================================================
# INSTRUCTION_FSM_BOX  —  top-level structural wrapper
# =============================================================================
class INSTRUCTION_FSM_BOX(py4hw.Logic):
    """
    Top-level structural wrapper that ties together:

        * FSM_SELECTOR   — decodes `Instruction` while `run` is high and
                           asserts exactly one of RUN_OPPFSM / RUN_MOVFSM /
                           RUN_POPPUSHFSM / RUN_LDSTFSM / RUN_CALLRETFSM.
        * OPP_FSM        — arithmetic / logic / skip / SREG / MOV ops.
        * MOV_FSM        — register-to-register moves (MOVW).
        * PopPush_FSM    — PUSH / POP.
        * LDST_FSM       — loads / stores / IN / OUT / SBI / CBI.
        * CallRet_FSM    — RJMP/IJMP/JMP/RCALL/ICALL/CALL/RET/RETI.
        * LPM_FSM        — LPM / LPMZ / LPMZ+ program-memory loads.

    The selector's RUN_* outputs gate the `run` input of the matching FSM.
    All FSM outputs are bitwise-OR-merged: FSMs in their STOP state drive
    0 on every output, so the OR passes only the active FSM's signals
    through to the box's external outputs.
    """

    def __init__(self, parent, name,
                 # ── Inputs (shared by every sub-FSM) ────────────────
                 IFB_RUN,
                 IFB_Instruction,
                 IFB_Resp,
                 IFB_Branch,
                 IFB_Executed_Jump,
                 IFB_Address_fetched, 
                 # ── Combined (OR-merged) Outputs ────────────────────
                 IFB_DONE,
                 IFB_LoadSelectMux,
                 IFB_LoadingMux,
                 IFB_Input_Select,
                 IFB_WE_MEMORY,
                 IFB_Read_Write,
                 IFB_Mem_Instruction,
                 IFB_IncDec,
                 IFB_InputSelect,
                 IFB_WE_Buffer,
                 IFB_Load_Z,
                 IFB_Load_K,
                 IFB_Load_Jump,
                 IFB_relative_Absolute,
                 IFB_Load_Byte,
                 IFB_Fetch_Address,
                 IFB_WB_Addr,
                 IFB_LOAD_PCL,
                 IFB_LOAD_PCH,
                 IFB_K_Select,
                 IFB_LPM_req,
                 IFB_SPM_req,
                 IFB_SPM_Done,
                 IFB_Reset=None,
                 ):
        super().__init__(parent, name)

        # ── External Inputs ──────────────────────────────────────────
        self.reset                  = self.addIn('reset', IFB_Reset) if IFB_Reset is not None else None
        self.run                    = self.addIn('run',                    IFB_RUN)
        self.Instruction            = self.addIn('Instruction',            IFB_Instruction)
        self.Resp                   = self.addIn('Resp',                   IFB_Resp)
        self.Branch                 = self.addIn('Branch',                 IFB_Branch)
        self.Executed_Jump          = self.addIn('Executed_Jump',          IFB_Executed_Jump)
        self.Address_fetched        = self.addIn('Address_fetched',        IFB_Address_fetched) 
        self.SPM_Done               = self.addIn('SPM_Done',               IFB_SPM_Done)

        # ── External Outputs (22, matching the constructor) ─────────
        self.done                   = self.addOut('done',                   IFB_DONE)
        self.LoadSelectMux          = self.addOut('LoadSelectMux',          IFB_LoadSelectMux)
        self.LoadingMux             = self.addOut('LoadingMux',             IFB_LoadingMux)
        self.Input_Select           = self.addOut('Input_Select',           IFB_Input_Select)
        self.WE                     = self.addOut('WE',                     IFB_WE_MEMORY)
        self.Read_Write             = self.addOut('Read_Write',             IFB_Read_Write)
        self.Mem_Instruction        = self.addOut('Mem_Instruction',        IFB_Mem_Instruction)
        self.IncDec                 = self.addOut('IncDec',                 IFB_IncDec)
        self.InputSelect            = self.addOut('InputSelect',            IFB_InputSelect)
        self.WE_Buffer              = self.addOut('WE_Buffer',              IFB_WE_Buffer)
        self.Load_Z                 = self.addOut('Load_Z',                 IFB_Load_Z)
        self.Load_K                 = self.addOut('Load_K',                 IFB_Load_K)
        self.Load_Jump              = self.addOut('Load_Jump',              IFB_Load_Jump)
        self.relative_Absolute      = self.addOut('relative_Absolute',      IFB_relative_Absolute)
        self.Load_Byte              = self.addOut('Load_Byte',              IFB_Load_Byte)
        self.Fetch_Address          = self.addOut('Fetch_Address',          IFB_Fetch_Address)
        self.WB_Addr                = self.addOut('WB_Addr',                IFB_WB_Addr)
        self.LOAD_PCL               = self.addOut('LOAD_PCL',               IFB_LOAD_PCL)
        self.LOAD_PCH               = self.addOut('LOAD_PCH',               IFB_LOAD_PCH)
        self.K_Select               = self.addOut('IFB_K_Select',           IFB_K_Select)
        self.LPM_req                = self.addOut('LPM_req',                IFB_LPM_req)
        self.SPM_req                = self.addOut('SPM_req',                IFB_SPM_req)

        # ==============================================================
        # INTERNAL WIRES
        # ==============================================================
        # FSM_SELECTOR -> RUN_* lines (one-hot)
        self.w_RUN_OPPFSM     = py4hw.Wire(self, 'w_RUN_OPPFSM',     1)
        self.w_RUN_MOVFSM     = py4hw.Wire(self, 'w_RUN_MOVFSM',     1)
        self.w_RUN_POPPUSHFSM = py4hw.Wire(self, 'w_RUN_POPPUSHFSM', 1)
        self.w_RUN_LDSTFSM    = py4hw.Wire(self, 'w_RUN_LDSTFSM',    1)
        self.w_RUN_CALLRETFSM = py4hw.Wire(self, 'w_RUN_CALLRETFSM', 1)
        self.w_RUN_LPMFSM     = py4hw.Wire(self, 'w_RUN_LPMFSM',     1)

        # Merged outputs that have NO external port (still needed by the merger)
        self.WE_MEMORY  = py4hw.Wire(self, 'WE_MEMORY',  1)

        # ── OPP FSM Wires ──
        self.w_opp_done                   = py4hw.Wire(self, 'w_opp_done',                   1)
        self.w_opp_NotExecute             = py4hw.Wire(self, 'w_opp_NotExecute',             1)
        self.w_opp_LoadSelectMux          = py4hw.Wire(self, 'w_opp_LoadSelectMux',          1)
        # FIX: widened 4->5 bits. LOAD_R1_BUFFER=16 (SPM's high-byte
        # operand load, see LPM.py's SPM path) needs 5 bits to represent;
        # a 4-bit wire silently truncated it to 0, so SPM_LOAD_R1 never
        # actually loaded MemoryInterfaceHandler's R1Buffer even though
        # every other LoadingMux code (max 15, LOAD_R0_BUFFER) fit fine.
        # All six per-FSM LoadingMux wires below share this fix for
        # consistency with the already-5-bit merged W_LoadingMux wire in
        # MulticycleProcessor.py.
        self.w_opp_LoadingMux             = py4hw.Wire(self, 'w_opp_LoadingMux',             5)
        self.w_opp_Input_Select           = py4hw.Wire(self, 'w_opp_Input_Select',           5)
        self.w_opp_WE                     = py4hw.Wire(self, 'w_opp_WE',                     1)
        self.w_opp_Read_Write             = py4hw.Wire(self, 'w_opp_Read_Write',             2)
        self.w_opp_Mem_Instruction        = py4hw.Wire(self, 'w_opp_Mem_Instruction',        5)
        self.w_opp_IncDec                 = py4hw.Wire(self, 'w_opp_IncDec',                 3)
        self.w_opp_write_Opperand_Buffer  = py4hw.Wire(self, 'w_opp_write_Opperand_Buffer',  3)
        self.w_opp_InputSelect            = py4hw.Wire(self, 'w_opp_InputSelect',            1)
        self.w_opp_Load_Z                 = py4hw.Wire(self, 'w_opp_Load_Z',                 1)
        self.w_opp_Load_K                 = py4hw.Wire(self, 'w_opp_Load_K',                 1)
        self.w_opp_Load_Jump              = py4hw.Wire(self, 'w_opp_Load_Jump',              1)
        self.w_opp_relative_Absolute      = py4hw.Wire(self, 'w_opp_relative_Absolute',      1)
        self.w_opp_Load_Byte              = py4hw.Wire(self, 'w_opp_Load_Byte',              1)
        self.w_opp_Fetch_next_instruction = py4hw.Wire(self, 'w_opp_Fetch_next_instruction', 1)
        self.w_opp_Fetch_Address          = py4hw.Wire(self, 'w_opp_Fetch_Address',          1)
        self.w_opp_WB_Addr                = py4hw.Wire(self, 'w_opp_WB_Addr',                8)
        self.w_opp_LOAD_PCL               = py4hw.Wire(self, 'w_opp_LOAD_PCL',               1)
        self.w_opp_LOAD_PCH               = py4hw.Wire(self, 'w_opp_LOAD_PCH',               1)
        self.w_opp_K_Select                = py4hw.Wire(self, 'w_opp_K_Select',                2)


        # ── MOV FSM Wires ──
        self.w_mov_done                   = py4hw.Wire(self, 'w_mov_done',                   1)
        self.w_mov_NotExecute             = py4hw.Wire(self, 'w_mov_NotExecute',             1)
        self.w_mov_LoadSelectMux          = py4hw.Wire(self, 'w_mov_LoadSelectMux',          1)
        self.w_mov_LoadingMux             = py4hw.Wire(self, 'w_mov_LoadingMux',             5)
        self.w_mov_Input_Select           = py4hw.Wire(self, 'w_mov_Input_Select',           5)
        self.w_mov_WE                     = py4hw.Wire(self, 'w_mov_WE',                     1)
        self.w_mov_Read_Write             = py4hw.Wire(self, 'w_mov_Read_Write',             2)
        self.w_mov_Mem_Instruction        = py4hw.Wire(self, 'w_mov_Mem_Instruction',        5)
        self.w_mov_IncDec                 = py4hw.Wire(self, 'w_mov_IncDec',                 3)
        self.w_mov_write_Opperand_Buffer  = py4hw.Wire(self, 'w_mov_write_Opperand_Buffer',  3)
        self.w_mov_InputSelect            = py4hw.Wire(self, 'w_mov_InputSelect',            1)
        self.w_mov_Load_Z                 = py4hw.Wire(self, 'w_mov_Load_Z',                 1)
        self.w_mov_Load_K                 = py4hw.Wire(self, 'w_mov_Load_K',                 1)
        self.w_mov_Load_Jump              = py4hw.Wire(self, 'w_mov_Load_Jump',              1)
        self.w_mov_relative_Absolute      = py4hw.Wire(self, 'w_mov_relative_Absolute',      1)
        self.w_mov_Load_Byte              = py4hw.Wire(self, 'w_mov_Load_Byte',              1)
        self.w_mov_Fetch_next_instruction = py4hw.Wire(self, 'w_mov_Fetch_next_instruction', 1)
        self.w_mov_Fetch_Address          = py4hw.Wire(self, 'w_mov_Fetch_Address',          1)
        self.w_mov_WB_Addr                = py4hw.Wire(self, 'w_mov_WB_Addr',                8)
        self.w_mov_LOAD_PCL               = py4hw.Wire(self, 'w_mov_LOAD_PCL',               1)
        self.w_mov_LOAD_PCH               = py4hw.Wire(self, 'w_mov_LOAD_PCH',               1)


        # ── POPPUSH FSM Wires ──
        self.w_poppush_done                   = py4hw.Wire(self, 'w_poppush_done',                   1)
        self.w_poppush_NotExecute             = py4hw.Wire(self, 'w_poppush_NotExecute',             1)
        self.w_poppush_LoadSelectMux          = py4hw.Wire(self, 'w_poppush_LoadSelectMux',          1)
        self.w_poppush_LoadingMux             = py4hw.Wire(self, 'w_poppush_LoadingMux',             5)
        self.w_poppush_Input_Select           = py4hw.Wire(self, 'w_poppush_Input_Select',           5)
        self.w_poppush_WE                     = py4hw.Wire(self, 'w_poppush_WE',                     1)
        self.w_poppush_Read_Write             = py4hw.Wire(self, 'w_poppush_Read_Write',             2)
        self.w_poppush_Mem_Instruction        = py4hw.Wire(self, 'w_poppush_Mem_Instruction',        5)
        self.w_poppush_IncDec                 = py4hw.Wire(self, 'w_poppush_IncDec',                 3)
        self.w_poppush_write_Opperand_Buffer  = py4hw.Wire(self, 'w_poppush_write_Opperand_Buffer',  3)
        self.w_poppush_InputSelect            = py4hw.Wire(self, 'w_poppush_InputSelect',            1)
        self.w_poppush_Load_Z                 = py4hw.Wire(self, 'w_poppush_Load_Z',                 1)
        self.w_poppush_Load_K                 = py4hw.Wire(self, 'w_poppush_Load_K',                 1)
        self.w_poppush_Load_Jump              = py4hw.Wire(self, 'w_poppush_Load_Jump',              1)
        self.w_poppush_relative_Absolute      = py4hw.Wire(self, 'w_poppush_relative_Absolute',      1)
        self.w_poppush_Load_Byte              = py4hw.Wire(self, 'w_poppush_Load_Byte',              1)
        self.w_poppush_Fetch_next_instruction = py4hw.Wire(self, 'w_poppush_Fetch_next_instruction', 1)
        self.w_poppush_Fetch_Address          = py4hw.Wire(self, 'w_poppush_Fetch_Address',          1)
        self.w_poppush_WB_Addr                = py4hw.Wire(self, 'w_poppush_WB_Addr',                8)
        self.w_poppush_LOAD_PCL               = py4hw.Wire(self, 'w_poppush_LOAD_PCL',               1)
        self.w_poppush_LOAD_PCH               = py4hw.Wire(self, 'w_poppush_LOAD_PCH',               1)


        # ── LDST FSM Wires ──
        self.w_ldst_done                   = py4hw.Wire(self, 'w_ldst_done',                   1)
        self.w_ldst_NotExecute             = py4hw.Wire(self, 'w_ldst_NotExecute',             1)
        self.w_ldst_LoadSelectMux          = py4hw.Wire(self, 'w_ldst_LoadSelectMux',          1)
        self.w_ldst_LoadingMux             = py4hw.Wire(self, 'w_ldst_LoadingMux',             5)
        self.w_ldst_Input_Select           = py4hw.Wire(self, 'w_ldst_Input_Select',           5)
        self.w_ldst_WE                     = py4hw.Wire(self, 'w_ldst_WE',                     1)
        self.w_ldst_Read_Write             = py4hw.Wire(self, 'w_ldst_Read_Write',             2)
        self.w_ldst_Mem_Instruction        = py4hw.Wire(self, 'w_ldst_Mem_Instruction',        5)
        self.w_ldst_IncDec                 = py4hw.Wire(self, 'w_ldst_IncDec',                 3)
        self.w_ldst_write_Opperand_Buffer  = py4hw.Wire(self, 'w_ldst_write_Opperand_Buffer',  3)
        self.w_ldst_InputSelect            = py4hw.Wire(self, 'w_ldst_InputSelect',            1)
        self.w_ldst_Load_Z                 = py4hw.Wire(self, 'w_ldst_Load_Z',                 1)
        self.w_ldst_Load_K                 = py4hw.Wire(self, 'w_ldst_Load_K',                 1)
        self.w_ldst_Load_Jump              = py4hw.Wire(self, 'w_ldst_Load_Jump',              1)
        self.w_ldst_relative_Absolute      = py4hw.Wire(self, 'w_ldst_relative_Absolute',      1)
        self.w_ldst_Load_Byte              = py4hw.Wire(self, 'w_ldst_Load_Byte',              1)
        self.w_ldst_Fetch_next_instruction = py4hw.Wire(self, 'w_ldst_Fetch_next_instruction', 1)
        self.w_ldst_Fetch_Address          = py4hw.Wire(self, 'w_ldst_Fetch_Address',          1)
        self.w_ldst_WB_Addr                = py4hw.Wire(self, 'w_ldst_WB_Addr',                8)
        self.w_ldst_LOAD_PCL               = py4hw.Wire(self, 'w_ldst_LOAD_PCL',               1)
        self.w_ldst_LOAD_PCH               = py4hw.Wire(self, 'w_ldst_LOAD_PCH',               1)


        # ── CALLRET FSM Wires ──
        self.w_callret_done                   = py4hw.Wire(self, 'w_callret_done',                   1)
        self.w_callret_NotExecute             = py4hw.Wire(self, 'w_callret_NotExecute',             1)
        self.w_callret_LoadSelectMux          = py4hw.Wire(self, 'w_callret_LoadSelectMux',          1)
        self.w_callret_LoadingMux             = py4hw.Wire(self, 'w_callret_LoadingMux',             5)
        self.w_callret_Input_Select           = py4hw.Wire(self, 'w_callret_Input_Select',           5)
        self.w_callret_WE                     = py4hw.Wire(self, 'w_callret_WE',                     1)
        self.w_callret_Read_Write             = py4hw.Wire(self, 'w_callret_Read_Write',             2)
        self.w_callret_Mem_Instruction        = py4hw.Wire(self, 'w_callret_Mem_Instruction',        5)
        self.w_callret_IncDec                 = py4hw.Wire(self, 'w_callret_IncDec',                 3)
        self.w_callret_write_Opperand_Buffer  = py4hw.Wire(self, 'w_callret_write_Opperand_Buffer',  3)
        self.w_callret_InputSelect            = py4hw.Wire(self, 'w_callret_InputSelect',            1)
        self.w_callret_Load_Z                 = py4hw.Wire(self, 'w_callret_Load_Z',                 1)
        self.w_callret_Load_K                 = py4hw.Wire(self, 'w_callret_Load_K',                 1)
        self.w_callret_Load_Jump              = py4hw.Wire(self, 'w_callret_Load_Jump',              1)
        self.w_callret_relative_Absolute      = py4hw.Wire(self, 'w_callret_relative_Absolute',      1)
        self.w_callret_Load_Byte              = py4hw.Wire(self, 'w_callret_Load_Byte',              1)
        self.w_callret_Fetch_next_instruction = py4hw.Wire(self, 'w_callret_Fetch_next_instruction', 1)
        self.w_callret_Fetch_Address          = py4hw.Wire(self, 'w_callret_Fetch_Address',          1)
        self.w_callret_WB_Addr                = py4hw.Wire(self, 'w_callret_WB_Addr',                8)
        self.w_callret_LOAD_PCL               = py4hw.Wire(self, 'w_callret_LOAD_PCL',               1)
        self.w_callret_LOAD_PCH               = py4hw.Wire(self, 'w_callret_LOAD_PCH',               1)
        self.w_callret_K_Select               = py4hw.Wire(self, 'w_callret_K_Select',               2)

        # ── LPM FSM Wires ──
        self.w_lpm_done                   = py4hw.Wire(self, 'w_lpm_done',                   1)
        self.w_lpm_NotExecute             = py4hw.Wire(self, 'w_lpm_NotExecute',             1)
        self.w_lpm_LoadSelectMux          = py4hw.Wire(self, 'w_lpm_LoadSelectMux',          1)
        self.w_lpm_LoadingMux             = py4hw.Wire(self, 'w_lpm_LoadingMux',             5)
        self.w_lpm_Input_Select           = py4hw.Wire(self, 'w_lpm_Input_Select',           5)
        self.w_lpm_WE                     = py4hw.Wire(self, 'w_lpm_WE',                     1)
        self.w_lpm_Read_Write             = py4hw.Wire(self, 'w_lpm_Read_Write',             2)
        self.w_lpm_Mem_Instruction        = py4hw.Wire(self, 'w_lpm_Mem_Instruction',        5)
        self.w_lpm_IncDec                 = py4hw.Wire(self, 'w_lpm_IncDec',                 3)
        self.w_lpm_write_Opperand_Buffer  = py4hw.Wire(self, 'w_lpm_write_Opperand_Buffer',  3)
        self.w_lpm_InputSelect            = py4hw.Wire(self, 'w_lpm_InputSelect',            1)
        self.w_lpm_Write_Enable           = py4hw.Wire(self, 'w_lpm_Write_Enable',           1)
        self.w_lpm_Load_Z                 = py4hw.Wire(self, 'w_lpm_Load_Z',                 1)
        self.w_lpm_Load_K                 = py4hw.Wire(self, 'w_lpm_Load_K',                 1)
        self.w_lpm_Load_Jump              = py4hw.Wire(self, 'w_lpm_Load_Jump',              1)
        self.w_lpm_relative_Absolute      = py4hw.Wire(self, 'w_lpm_relative_Absolute',      1)
        self.w_lpm_Load_Byte              = py4hw.Wire(self, 'w_lpm_Load_Byte',              1)
        self.w_lpm_Fetch_next_instruction = py4hw.Wire(self, 'w_lpm_Fetch_next_instruction', 1)
        self.w_lpm_Fetch_Address          = py4hw.Wire(self, 'w_lpm_Fetch_Address',          1)
        self.w_lpm_WB_Addr                = py4hw.Wire(self, 'w_lpm_WB_Addr',                8)
        self.w_lpm_LOAD_PCL               = py4hw.Wire(self, 'w_lpm_LOAD_PCL',               1)
        self.w_lpm_LOAD_PCH               = py4hw.Wire(self, 'w_lpm_LOAD_PCH',               1)
        self.w_lpm_LPM_req                = py4hw.Wire(self, 'w_lpm_LPM_req',                1)
        self.w_lpm_SPM_req                = py4hw.Wire(self, 'w_lpm_SPM_req',                1)



        # ==============================================================
        # FSM_SELECTOR  —  decodes Instruction while run==1 and raises
        # exactly one of the RUN_* lines.
        # ==============================================================
        self.selector = FSM_SELECTOR(
            self, 'FSM_SELECTOR',
            self.run,
            self.Instruction,
            self.w_RUN_OPPFSM,
            self.w_RUN_MOVFSM,
            self.w_RUN_POPPUSHFSM,
            self.w_RUN_LDSTFSM,
            self.w_RUN_CALLRETFSM,
            self.w_RUN_LPMFSM,
        )

        # ==============================================================
        # OPP_FSM  — arithmetic / logic / skip / SREG ops
        # ==============================================================
        self.opp_fsm = OPP_FSM(
            self, 'OPP_FSM',
            reset                      = self.reset,
            run                       = self.w_RUN_OPPFSM,
            done                      = self.w_opp_done,
            Instruction               = self.Instruction,
            Resp                      = self.Resp,
            Branch                    = self.Branch,
            Executed_Jump             = self.Executed_Jump,
            LoadSelectMux             = self.w_opp_LoadSelectMux,
            LoadingMux                = self.w_opp_LoadingMux,
            InputSelectMemory         = self.w_opp_Input_Select,
            WEMEMORY                  = self.w_opp_WE,
            Read_Write                = self.w_opp_Read_Write,
            Mem_Instruction           = self.w_opp_Mem_Instruction,
            IncDec                    = self.w_opp_IncDec,
            WEBUFFER                  = self.w_opp_write_Opperand_Buffer,
            InputSelectBuffer         = self.w_opp_InputSelect,
            Load_Z                    = self.w_opp_Load_Z,
            Load_K                    = self.w_opp_Load_K,
            Load_Jump                 = self.w_opp_Load_Jump,
            relative_Absolute         = self.w_opp_relative_Absolute,
            Load_Byte                 = self.w_opp_Load_Byte,
            Fetch_next_instruction    = self.w_opp_Fetch_next_instruction,
            Fetch_Address             = self.w_opp_Fetch_Address,
            WB_Addr                   = self.w_opp_WB_Addr,
            LOAD_PCL                  = self.w_opp_LOAD_PCL,
            LOAD_PCH                  = self.w_opp_LOAD_PCH,
            K_Select                  = self.w_opp_K_Select,
        )

        # ==============================================================
        # MOV_FSM  — register-to-register moves
        # ==============================================================
        self.mov_fsm = MOV_FSM(
            self, 'MOV_FSM',
            reset                      = self.reset,
            run                       = self.w_RUN_MOVFSM,
            done                      = self.w_mov_done,
            Instruction               = self.Instruction,
            Resp                      = self.Resp,
            Branch                    = self.Branch,
            Executed_Jump             = self.Executed_Jump,
            LoadSelectMux             = self.w_mov_LoadSelectMux,
            LoadingMux                = self.w_mov_LoadingMux,
            InputSelectMemory         = self.w_mov_Input_Select,
            WEMEMORY                  = self.w_mov_WE,
            Read_Write                = self.w_mov_Read_Write,
            Mem_Instruction           = self.w_mov_Mem_Instruction,
            IncDec                    = self.w_mov_IncDec,
            WEBUFFER                  = self.w_mov_write_Opperand_Buffer,
            InputSelectBuffer         = self.w_mov_InputSelect,
            Load_Z                    = self.w_mov_Load_Z,
            Load_K                    = self.w_mov_Load_K,
            Load_Jump                 = self.w_mov_Load_Jump,
            relative_Absolute         = self.w_mov_relative_Absolute,
            Load_Byte                 = self.w_mov_Load_Byte,
            Fetch_next_instruction    = self.w_mov_Fetch_next_instruction,
            Fetch_Address             = self.w_mov_Fetch_Address,
            WB_Addr                   = self.w_mov_WB_Addr,
            LOAD_PCL                  = self.w_mov_LOAD_PCL,
            LOAD_PCH                  = self.w_mov_LOAD_PCH,
        )

        # ==============================================================
        # PopPush_FSM  — PUSH / POP
        # ==============================================================
        self.poppush_fsm = PopPush_FSM(
            self, 'PopPush_FSM',
            reset                      = self.reset,
            run                       = self.w_RUN_POPPUSHFSM,
            done                      = self.w_poppush_done,
            Instruction               = self.Instruction,
            Resp                      = self.Resp,
            Branch                    = self.Branch,
            Executed_Jump             = self.Executed_Jump,
            LoadSelectMux             = self.w_poppush_LoadSelectMux,
            LoadingMux                = self.w_poppush_LoadingMux,
            InputSelectMemory         = self.w_poppush_Input_Select,
            WEMEMORY                  = self.w_poppush_WE,
            Read_Write                = self.w_poppush_Read_Write,
            Mem_Instruction           = self.w_poppush_Mem_Instruction,
            IncDec                    = self.w_poppush_IncDec,
            WEBUFFER                  = self.w_poppush_write_Opperand_Buffer,
            InputSelectBuffer         = self.w_poppush_InputSelect,
            Load_Z                    = self.w_poppush_Load_Z,
            Load_K                    = self.w_poppush_Load_K,
            Load_Jump                 = self.w_poppush_Load_Jump,
            relative_Absolute         = self.w_poppush_relative_Absolute,
            Load_Byte                 = self.w_poppush_Load_Byte,
            Fetch_next_instruction    = self.w_poppush_Fetch_next_instruction,
            Fetch_Address             = self.w_poppush_Fetch_Address,
            WB_Addr                   = self.w_poppush_WB_Addr,
            LOAD_PCL                  = self.w_poppush_LOAD_PCL,
            LOAD_PCH                  = self.w_poppush_LOAD_PCH,
        )

        # ==============================================================
        # LDST_FSM  — loads / stores / IN / OUT / SBI / CBI
        # ==============================================================
        self.ldst_fsm = LDST_FSM(
            self, 'LDST_FSM',
            reset                      = self.reset,
            run                       = self.w_RUN_LDSTFSM,
            done                      = self.w_ldst_done,
            Instruction               = self.Instruction,
            Resp                      = self.Resp,
            Branch                    = self.Branch,
            Executed_Jump             = self.Executed_Jump,
            Address_fetched           = self.Address_fetched, 
            LoadSelectMux             = self.w_ldst_LoadSelectMux,
            LoadingMux                = self.w_ldst_LoadingMux,
            InputSelectMemory         = self.w_ldst_Input_Select,
            WEMEMORY                  = self.w_ldst_WE,
            Read_Write                = self.w_ldst_Read_Write,
            Mem_Instruction           = self.w_ldst_Mem_Instruction,
            IncDec                    = self.w_ldst_IncDec,
            WEBUFFER                  = self.w_ldst_write_Opperand_Buffer,
            InputSelectBuffer         = self.w_ldst_InputSelect,
            Load_Z                    = self.w_ldst_Load_Z,
            Load_K                    = self.w_ldst_Load_K,
            Load_Jump                 = self.w_ldst_Load_Jump,
            relative_Absolute         = self.w_ldst_relative_Absolute,
            Load_Byte                 = self.w_ldst_Load_Byte,
            Fetch_next_instruction    = self.w_ldst_Fetch_next_instruction,
            Fetch_Address             = self.w_ldst_Fetch_Address,
            WB_Addr                   = self.w_ldst_WB_Addr,
            LOAD_PCL                  = self.w_ldst_LOAD_PCL,
            LOAD_PCH                  = self.w_ldst_LOAD_PCH,
        )

        # ==============================================================
        # CALLRET_FSM  —  jumps / calls / returns
        # ==============================================================
        self.callret_fsm = CallRet_FSM(
            self, 'CALLRET_FSM',
            reset                      = self.reset,
            run                       = self.w_RUN_CALLRETFSM,
            done                      = self.w_callret_done,
            Instruction               = self.Instruction,
            Resp                      = self.Resp,
            Branch                    = self.Branch,
            Executed_Jump             = self.Executed_Jump,
            Address_fetched           = self.Address_fetched, 
            LoadSelectMux             = self.w_callret_LoadSelectMux,
            LoadingMux                = self.w_callret_LoadingMux,
            InputSelectMemory         = self.w_callret_Input_Select,
            WEMEMORY                  = self.w_callret_WE,
            Read_Write                = self.w_callret_Read_Write,
            Mem_Instruction           = self.w_callret_Mem_Instruction,
            IncDec                    = self.w_callret_IncDec,
            WEBUFFER                  = self.w_callret_write_Opperand_Buffer,
            InputSelectBuffer         = self.w_callret_InputSelect,
            Load_Z                    = self.w_callret_Load_Z,
            Load_K                    = self.w_callret_Load_K,
            Load_Jump                 = self.w_callret_Load_Jump,
            relative_Absolute         = self.w_callret_relative_Absolute,
            Load_Byte                 = self.w_callret_Load_Byte,
            Fetch_next_instruction    = self.w_callret_Fetch_next_instruction,
            Fetch_Address             = self.w_callret_Fetch_Address,
            WB_Addr                   = self.w_callret_WB_Addr,
            LOAD_PCL                  = self.w_callret_LOAD_PCL,
            LOAD_PCH                  = self.w_callret_LOAD_PCH,
            K_Select                  = self.w_callret_K_Select,
        )

        # ==============================================================
        # LPM_FSM  —  LPM / LPMZ / LPMZ+ program-memory loads
        # ==============================================================
        self.lpm_fsm = LPM_FSM(
            self, 'LPM_FSM',
            reset                      = self.reset,
            run                       = self.w_RUN_LPMFSM,
            done                      = self.w_lpm_done,
            Instruction               = self.Instruction,
            Resp                      = self.Resp,
            Branch                    = self.Branch,
            Executed_Jump             = self.Executed_Jump,
            Address_fetched           = self.Address_fetched,
            NotExecute                = self.w_lpm_NotExecute,
            LoadSelectMux             = self.w_lpm_LoadSelectMux,
            LoadingMux                = self.w_lpm_LoadingMux,
            Input_Select              = self.w_lpm_Input_Select,
            WE                        = self.w_lpm_WE,
            Read_Write                = self.w_lpm_Read_Write,
            Mem_Instruction           = self.w_lpm_Mem_Instruction,
            IncDec                    = self.w_lpm_IncDec,
            write_Opperand_Buffer     = self.w_lpm_write_Opperand_Buffer,
            InputSelect               = self.w_lpm_InputSelect,
            Write_Enable              = self.w_lpm_Write_Enable,
            Load_Z                    = self.w_lpm_Load_Z,
            Load_K                    = self.w_lpm_Load_K,
            Load_Jump                 = self.w_lpm_Load_Jump,
            relative_Absolute         = self.w_lpm_relative_Absolute,
            Load_Byte                 = self.w_lpm_Load_Byte,
            Fetch_next_instruction    = self.w_lpm_Fetch_next_instruction,
            Fetch_Address             = self.w_lpm_Fetch_Address,
            LOAD_PCL                  = self.w_lpm_LOAD_PCL,
            LOAD_PCH                  = self.w_lpm_LOAD_PCH,
            WB_Addr                   = self.w_lpm_WB_Addr,
            LPM_req                   = self.w_lpm_LPM_req,
            SPM_req                   = self.w_lpm_SPM_req,
            SPM_Done                  = self.SPM_Done,
        )

        # ==============================================================
        # OUTPUT MERGER  —  OR-merges all FSM outputs
        # ==============================================================
        opp_outputs = {
            'done':                   self.w_opp_done,
            'LoadSelectMux':          self.w_opp_LoadSelectMux,
            'LoadingMux':             self.w_opp_LoadingMux,
            'Input_Select':           self.w_opp_Input_Select,
            'WE':                     self.w_opp_WE,
            'Read_Write':             self.w_opp_Read_Write,
            'Mem_Instruction':        self.w_opp_Mem_Instruction,
            'IncDec':                 self.w_opp_IncDec,
            'WE_Buffer':              self.w_opp_write_Opperand_Buffer,
            'InputSelect':            self.w_opp_InputSelect,
            'Load_Z':                 self.w_opp_Load_Z,
            'Load_K':                 self.w_opp_Load_K,
            'Load_Jump':              self.w_opp_Load_Jump,
            'relative_Absolute':      self.w_opp_relative_Absolute,
            'Load_Byte':              self.w_opp_Load_Byte,
            'Fetch_next_instruction': self.w_opp_Fetch_next_instruction,
            'Fetch_Address':          self.w_opp_Fetch_Address,
            'WB_Addr':                self.w_opp_WB_Addr,
            'LOAD_PCL':               self.w_opp_LOAD_PCL,
            'LOAD_PCH':               self.w_opp_LOAD_PCH,
            'K_Select':               self.w_opp_K_Select,
        }

        mov_outputs = {
            'done':                   self.w_mov_done,
            'LoadSelectMux':          self.w_mov_LoadSelectMux,
            'LoadingMux':             self.w_mov_LoadingMux,
            'Input_Select':           self.w_mov_Input_Select,
            'WE':                     self.w_mov_WE,
            'Read_Write':             self.w_mov_Read_Write,
            'Mem_Instruction':        self.w_mov_Mem_Instruction,
            'IncDec':                 self.w_mov_IncDec,
            'WE_Buffer':              self.w_mov_write_Opperand_Buffer,
            'InputSelect':            self.w_mov_InputSelect,
            'Load_Z':                 self.w_mov_Load_Z,
            'Load_K':                 self.w_mov_Load_K,
            'Load_Jump':              self.w_mov_Load_Jump,
            'relative_Absolute':      self.w_mov_relative_Absolute,
            'Load_Byte':              self.w_mov_Load_Byte,
            'Fetch_next_instruction': self.w_mov_Fetch_next_instruction,
            'Fetch_Address':          self.w_mov_Fetch_Address,
            'WB_Addr':                self.w_mov_WB_Addr,
            'LOAD_PCL':               self.w_mov_LOAD_PCL,
            'LOAD_PCH':               self.w_mov_LOAD_PCH,
        }

        poppush_outputs = {
            'done':                   self.w_poppush_done,
            'LoadSelectMux':          self.w_poppush_LoadSelectMux,
            'LoadingMux':             self.w_poppush_LoadingMux,
            'Input_Select':           self.w_poppush_Input_Select,
            'WE':                     self.w_poppush_WE,
            'Read_Write':             self.w_poppush_Read_Write,
            'Mem_Instruction':        self.w_poppush_Mem_Instruction,
            'IncDec':                 self.w_poppush_IncDec,
            'WE_Buffer':              self.w_poppush_write_Opperand_Buffer,
            'InputSelect':            self.w_poppush_InputSelect,
            'Load_Z':                 self.w_poppush_Load_Z,
            'Load_K':                 self.w_poppush_Load_K,
            'Load_Jump':              self.w_poppush_Load_Jump,
            'relative_Absolute':      self.w_poppush_relative_Absolute,
            'Load_Byte':              self.w_poppush_Load_Byte,
            'Fetch_next_instruction': self.w_poppush_Fetch_next_instruction,
            'Fetch_Address':          self.w_poppush_Fetch_Address,
            'WB_Addr':                self.w_poppush_WB_Addr,
            'LOAD_PCL':               self.w_poppush_LOAD_PCL,
            'LOAD_PCH':               self.w_poppush_LOAD_PCH,
        }

        ldst_outputs = {
            'done':                   self.w_ldst_done,
            'LoadSelectMux':          self.w_ldst_LoadSelectMux,
            'LoadingMux':             self.w_ldst_LoadingMux,
            'Input_Select':           self.w_ldst_Input_Select,
            'WE':                     self.w_ldst_WE,
            'Read_Write':             self.w_ldst_Read_Write,
            'Mem_Instruction':        self.w_ldst_Mem_Instruction,
            'IncDec':                 self.w_ldst_IncDec,
            'WE_Buffer':              self.w_ldst_write_Opperand_Buffer,
            'InputSelect':            self.w_ldst_InputSelect,
            'Load_Z':                 self.w_ldst_Load_Z,
            'Load_K':                 self.w_ldst_Load_K,
            'Load_Jump':              self.w_ldst_Load_Jump,
            'relative_Absolute':      self.w_ldst_relative_Absolute,
            'Load_Byte':              self.w_ldst_Load_Byte,
            'Fetch_next_instruction': self.w_ldst_Fetch_next_instruction,
            'Fetch_Address':          self.w_ldst_Fetch_Address,
            'WB_Addr':                self.w_ldst_WB_Addr,
            'LOAD_PCL':               self.w_ldst_LOAD_PCL,
            'LOAD_PCH':               self.w_ldst_LOAD_PCH,
        }

        callret_outputs = {
            'done':                   self.w_callret_done,
            'LoadSelectMux':          self.w_callret_LoadSelectMux,
            'LoadingMux':             self.w_callret_LoadingMux,
            'Input_Select':           self.w_callret_Input_Select,
            'WE':                     self.w_callret_WE,
            'Read_Write':             self.w_callret_Read_Write,
            'Mem_Instruction':        self.w_callret_Mem_Instruction,
            'IncDec':                 self.w_callret_IncDec,
            'WE_Buffer':              self.w_callret_write_Opperand_Buffer,
            'InputSelect':            self.w_callret_InputSelect,
            'Load_Z':                 self.w_callret_Load_Z,
            'Load_K':                 self.w_callret_Load_K,
            'Load_Jump':              self.w_callret_Load_Jump,
            'relative_Absolute':      self.w_callret_relative_Absolute,
            'Load_Byte':              self.w_callret_Load_Byte,
            'Fetch_next_instruction': self.w_callret_Fetch_next_instruction,
            'Fetch_Address':          self.w_callret_Fetch_Address,
            'WB_Addr':                self.w_callret_WB_Addr,
            'LOAD_PCL':               self.w_callret_LOAD_PCL,
            'LOAD_PCH':               self.w_callret_LOAD_PCH,
            'K_Select':               self.w_callret_K_Select,
        }

        lpm_outputs = {
            'done':                   self.w_lpm_done,
            'LoadSelectMux':          self.w_lpm_LoadSelectMux,
            'LoadingMux':             self.w_lpm_LoadingMux,
            'Input_Select':           self.w_lpm_Input_Select,
            'WE':                     self.w_lpm_WE,
            'Read_Write':             self.w_lpm_Read_Write,
            'Mem_Instruction':        self.w_lpm_Mem_Instruction,
            'IncDec':                 self.w_lpm_IncDec,
            'WE_Buffer':              self.w_lpm_write_Opperand_Buffer,
            'InputSelect':            self.w_lpm_InputSelect,
            'Load_Z':                 self.w_lpm_Load_Z,
            'Load_K':                 self.w_lpm_Load_K,
            'Load_Jump':              self.w_lpm_Load_Jump,
            'relative_Absolute':      self.w_lpm_relative_Absolute,
            'Load_Byte':              self.w_lpm_Load_Byte,
            'Fetch_next_instruction': self.w_lpm_Fetch_next_instruction,
            'Fetch_Address':          self.w_lpm_Fetch_Address,
            'WB_Addr':                self.w_lpm_WB_Addr,
            'LOAD_PCL':               self.w_lpm_LOAD_PCL,
            'LOAD_PCH':               self.w_lpm_LOAD_PCH,
            'LPM_req':                self.w_lpm_LPM_req,
            'SPM_req':                self.w_lpm_SPM_req,
        }


        merged_outputs = {
            'done':                   self.done,
            'LoadSelectMux':          self.LoadSelectMux,
            'LoadingMux':             self.LoadingMux,
            'Input_Select':           self.Input_Select,
            'WE':                     self.WE,
            'Read_Write':             self.Read_Write,
            'Mem_Instruction':        self.Mem_Instruction,
            'IncDec':                 self.IncDec,
            'WE_Buffer':              self.WE_Buffer,
            'InputSelect':            self.InputSelect,
            'Load_Z':                 self.Load_Z,
            'Load_K':                 self.Load_K,
            'Load_Jump':              self.Load_Jump,
            'relative_Absolute':      self.relative_Absolute,
            'Load_Byte':              self.Load_Byte,
            'Fetch_Address':          self.Fetch_Address,
            'WB_Addr':                self.WB_Addr,
            'LOAD_PCL':               self.LOAD_PCL,
            'LOAD_PCH':               self.LOAD_PCH,
            'K_Select':               self.K_Select,
            'LPM_req':                self.LPM_req,
            'SPM_req':                self.SPM_req,
            
        }

        self.merger = FSM_OutputMerger(
            self, 'FSM_OutputMerger',
            opp_outputs,
            mov_outputs,
            poppush_outputs,
            ldst_outputs,
            callret_outputs,
            lpm_outputs,
            merged_outputs,
        )