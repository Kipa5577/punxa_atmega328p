import py4hw

class FSM_OutputMerger(py4hw.Logic):
    """
    Behavioral leaf component that merges the matching output of every
    sub-FSM into a single external output. Because an inactive
    FSM is held in its STOP state and therefore drives 0 on every output,
    the bitwise OR forwards only the active FSM's value.
    
    Implemented with explicit declarations and propagation mirroring ALU_Merger.
    """
    def __init__(self, parent, name,
                 opp_outputs, mov_outputs, poppush_outputs,
                 ldst_outputs, callret_outputs,
                 merged_outputs):
        super().__init__(parent, name)

        # --- Inputs: OPP_FSM ---
        self.opp_done                   = self.addIn('opp_done',                   opp_outputs['done'])
        self.opp_LoadSelectMux          = self.addIn('opp_LoadSelectMux',          opp_outputs['LoadSelectMux'])
        self.opp_LoadingMux             = self.addIn('opp_LoadingMux',             opp_outputs['LoadingMux'])
        self.opp_Input_Select           = self.addIn('opp_Input_Select',           opp_outputs['Input_Select'])
        self.opp_WE                     = self.addIn('opp_WE',                     opp_outputs['WE'])
        self.opp_Read_Write             = self.addIn('opp_Read_Write',             opp_outputs['Read_Write'])
        self.opp_Mem_Instruction        = self.addIn('opp_Mem_Instruction',        opp_outputs['Mem_Instruction'])
        self.opp_IncDec                 = self.addIn('opp_IncDec',                 opp_outputs['IncDec'])
        self.opp_write_Opperand_Buffer  = self.addIn('WE_Buffer',                  opp_outputs['WE_Buffer'])
        self.opp_InputSelect            = self.addIn('opp_InputSelect',            opp_outputs['InputSelect'])
        self.opp_Load_Z                 = self.addIn('opp_Load_Z',                 opp_outputs['Load_Z'])
        self.opp_Load_K                 = self.addIn('opp_Load_K',                 opp_outputs['Load_K'])
        self.opp_Load_Jump              = self.addIn('opp_Load_Jump',              opp_outputs['Load_Jump'])
        self.opp_relative_Absolute      = self.addIn('opp_relative_Absolute',      opp_outputs['relative_Absolute'])
        self.opp_Load_Byte              = self.addIn('opp_Load_Byte',              opp_outputs['Load_Byte'])
        self.opp_Fetch_Address          = self.addIn('opp_Fetch_Address',          opp_outputs['Fetch_Address'])
        self.opp_WB_Addr                = self.addIn('opp_WB_Addr',                opp_outputs['WB_Addr'])
        self.opp_JumpWidth              = self.addIn('opp_JumpWidth',              opp_outputs['JumpWidth'])
        self.opp_LOAD_PCL               = self.addIn('opp_LOAD_PCL',               opp_outputs['LOAD_PCL'])
        self.opp_LOAD_PCH               = self.addIn('opp_LOAD_PCH',               opp_outputs['LOAD_PCH'])

        # --- Inputs: MOV_FSM ---
        self.mov_done                   = self.addIn('mov_done',                   mov_outputs['done'])
        self.mov_LoadSelectMux          = self.addIn('mov_LoadSelectMux',          mov_outputs['LoadSelectMux'])
        self.mov_LoadingMux             = self.addIn('mov_LoadingMux',             mov_outputs['LoadingMux'])
        self.mov_Input_Select           = self.addIn('mov_Input_Select',           mov_outputs['Input_Select'])
        self.mov_WE                     = self.addIn('mov_WE',                     mov_outputs['WE'])
        self.mov_Read_Write             = self.addIn('mov_Read_Write',             mov_outputs['Read_Write'])
        self.mov_Mem_Instruction        = self.addIn('mov_Mem_Instruction',        mov_outputs['Mem_Instruction'])
        self.mov_IncDec                 = self.addIn('mov_IncDec',                 mov_outputs['IncDec'])
        self.mov_write_Opperand_Buffer  = self.addIn('mov_write_Opperand_Buffer',  mov_outputs['WE_Buffer'])
        self.mov_InputSelect            = self.addIn('mov_InputSelect',            mov_outputs['InputSelect'])
        self.mov_Load_Z                 = self.addIn('mov_Load_Z',                 mov_outputs['Load_Z'])
        self.mov_Load_K                 = self.addIn('mov_Load_K',                 mov_outputs['Load_K'])
        self.mov_Load_Jump              = self.addIn('mov_Load_Jump',              mov_outputs['Load_Jump'])
        self.mov_relative_Absolute      = self.addIn('mov_relative_Absolute',      mov_outputs['relative_Absolute'])
        self.mov_Load_Byte              = self.addIn('mov_Load_Byte',              mov_outputs['Load_Byte'])
        self.mov_Fetch_Address          = self.addIn('mov_Fetch_Address',          mov_outputs['Fetch_Address'])
        self.mov_WB_Addr                = self.addIn('mov_WB_Addr',                mov_outputs['WB_Addr'])
        self.mov_JumpWidth              = self.addIn('mov_JumpWidth',              mov_outputs['JumpWidth'])
        self.mov_LOAD_PCL               = self.addIn('mov_LOAD_PCL',               mov_outputs['LOAD_PCL'])
        self.mov_LOAD_PCH               = self.addIn('mov_LOAD_PCH',               mov_outputs['LOAD_PCH'])

        # --- Inputs: POPPUSH_FSM ---
        self.poppush_done                   = self.addIn('poppush_done',                   poppush_outputs['done'])
        self.poppush_LoadSelectMux          = self.addIn('poppush_LoadSelectMux',          poppush_outputs['LoadSelectMux'])
        self.poppush_LoadingMux             = self.addIn('poppush_LoadingMux',             poppush_outputs['LoadingMux'])
        self.poppush_Input_Select           = self.addIn('poppush_Input_Select',           poppush_outputs['Input_Select'])
        self.poppush_WE                     = self.addIn('poppush_WE',                     poppush_outputs['WE'])
        self.poppush_Read_Write             = self.addIn('poppush_Read_Write',             poppush_outputs['Read_Write'])
        self.poppush_Mem_Instruction        = self.addIn('poppush_Mem_Instruction',        poppush_outputs['Mem_Instruction'])
        self.poppush_IncDec                 = self.addIn('poppush_IncDec',                 poppush_outputs['IncDec'])
        self.poppush_write_Opperand_Buffer  = self.addIn('poppush_write_Opperand_Buffer',  poppush_outputs['WE_Buffer'])
        self.poppush_InputSelect            = self.addIn('poppush_InputSelect',            poppush_outputs['InputSelect'])
        self.poppush_Load_Z                 = self.addIn('poppush_Load_Z',                 poppush_outputs['Load_Z'])
        self.poppush_Load_K                 = self.addIn('poppush_Load_K',                 poppush_outputs['Load_K'])
        self.poppush_Load_Jump              = self.addIn('poppush_Load_Jump',              poppush_outputs['Load_Jump'])
        self.poppush_relative_Absolute      = self.addIn('poppush_relative_Absolute',      poppush_outputs['relative_Absolute'])
        self.poppush_Load_Byte              = self.addIn('poppush_Load_Byte',              poppush_outputs['Load_Byte'])
        self.poppush_Fetch_Address          = self.addIn('poppush_Fetch_Address',          poppush_outputs['Fetch_Address'])
        self.poppush_WB_Addr                = self.addIn('poppush_WB_Addr',                poppush_outputs['WB_Addr'])
        self.poppush_JumpWidth              = self.addIn('poppush_JumpWidth',              poppush_outputs['JumpWidth'])
        self.poppush_LOAD_PCL               = self.addIn('poppush_LOAD_PCL',               poppush_outputs['LOAD_PCL'])
        self.poppush_LOAD_PCH               = self.addIn('poppush_LOAD_PCH',               poppush_outputs['LOAD_PCH'])

        # --- Inputs: LDST_FSM ---
        self.ldst_done                   = self.addIn('ldst_done',                   ldst_outputs['done'])
        self.ldst_LoadSelectMux          = self.addIn('ldst_LoadSelectMux',          ldst_outputs['LoadSelectMux'])
        self.ldst_LoadingMux             = self.addIn('ldst_LoadingMux',             ldst_outputs['LoadingMux'])
        self.ldst_Input_Select           = self.addIn('ldst_Input_Select',           ldst_outputs['Input_Select'])
        self.ldst_WE                     = self.addIn('ldst_WE',                     ldst_outputs['WE'])
        self.ldst_Read_Write             = self.addIn('ldst_Read_Write',             ldst_outputs['Read_Write'])
        self.ldst_Mem_Instruction        = self.addIn('ldst_Mem_Instruction',        ldst_outputs['Mem_Instruction'])
        self.ldst_IncDec                 = self.addIn('ldst_IncDec',                 ldst_outputs['IncDec'])
        self.ldst_write_Opperand_Buffer  = self.addIn('ldst_write_Opperand_Buffer',  ldst_outputs['WE_Buffer'])
        self.ldst_InputSelect            = self.addIn('ldst_InputSelect',            ldst_outputs['InputSelect'])
        self.ldst_Load_Z                 = self.addIn('ldst_Load_Z',                 ldst_outputs['Load_Z'])
        self.ldst_Load_K                 = self.addIn('ldst_Load_K',                 ldst_outputs['Load_K'])
        self.ldst_Load_Jump              = self.addIn('ldst_Load_Jump',              ldst_outputs['Load_Jump'])
        self.ldst_relative_Absolute      = self.addIn('ldst_relative_Absolute',      ldst_outputs['relative_Absolute'])
        self.ldst_Load_Byte              = self.addIn('ldst_Load_Byte',              ldst_outputs['Load_Byte'])
        self.ldst_Fetch_Address          = self.addIn('ldst_Fetch_Address',          ldst_outputs['Fetch_Address'])
        self.ldst_WB_Addr                = self.addIn('ldst_WB_Addr',                ldst_outputs['WB_Addr'])
        self.ldst_JumpWidth              = self.addIn('ldst_JumpWidth',              ldst_outputs['JumpWidth'])
        self.ldst_LOAD_PCL               = self.addIn('ldst_LOAD_PCL',               ldst_outputs['LOAD_PCL'])
        self.ldst_LOAD_PCH               = self.addIn('ldst_LOAD_PCH',               ldst_outputs['LOAD_PCH'])

        # --- Inputs: CALLRET_FSM ---
        self.callret_done                   = self.addIn('callret_done',                   callret_outputs['done'])
        self.callret_LoadSelectMux          = self.addIn('callret_LoadSelectMux',          callret_outputs['LoadSelectMux'])
        self.callret_LoadingMux             = self.addIn('callret_LoadingMux',             callret_outputs['LoadingMux'])
        self.callret_Input_Select           = self.addIn('callret_Input_Select',           callret_outputs['Input_Select'])
        self.callret_WE                     = self.addIn('callret_WE',                     callret_outputs['WE'])
        self.callret_Read_Write             = self.addIn('callret_Read_Write',             callret_outputs['Read_Write'])
        self.callret_Mem_Instruction        = self.addIn('callret_Mem_Instruction',        callret_outputs['Mem_Instruction'])
        self.callret_IncDec                 = self.addIn('callret_IncDec',                 callret_outputs['IncDec'])
        self.callret_write_Opperand_Buffer  = self.addIn('callret_write_Opperand_Buffer',  callret_outputs['WE_Buffer'])
        self.callret_InputSelect            = self.addIn('callret_InputSelect',            callret_outputs['InputSelect'])
        self.callret_Load_Z                 = self.addIn('callret_Load_Z',                 callret_outputs['Load_Z'])
        self.callret_Load_K                 = self.addIn('callret_Load_K',                 callret_outputs['Load_K'])
        self.callret_Load_Jump              = self.addIn('callret_Load_Jump',              callret_outputs['Load_Jump'])
        self.callret_relative_Absolute      = self.addIn('callret_relative_Absolute',      callret_outputs['relative_Absolute'])
        self.callret_Load_Byte              = self.addIn('callret_Load_Byte',              callret_outputs['Load_Byte'])
        self.callret_Fetch_Address          = self.addIn('callret_Fetch_Address',          callret_outputs['Fetch_Address'])
        self.callret_WB_Addr                = self.addIn('callret_WB_Addr',                callret_outputs['WB_Addr'])
        self.callret_JumpWidth              = self.addIn('callret_JumpWidth',              callret_outputs['JumpWidth'])
        self.callret_LOAD_PCL               = self.addIn('callret_LOAD_PCL',               callret_outputs['LOAD_PCL'])
        self.callret_LOAD_PCH               = self.addIn('callret_LOAD_PCH',               callret_outputs['LOAD_PCH'])

        # --- Outputs ---
        self.out_done                   = self.addOut('out_done',                   merged_outputs['done'])
        self.out_LoadSelectMux          = self.addOut('out_LoadSelectMux',          merged_outputs['LoadSelectMux'])
        self.out_LoadingMux             = self.addOut('out_LoadingMux',             merged_outputs['LoadingMux'])
        self.out_Input_Select           = self.addOut('out_Input_Select',           merged_outputs['Input_Select'])
        self.out_WE                     = self.addOut('out_WE',                     merged_outputs['WE'])
        self.out_Read_Write             = self.addOut('out_Read_Write',             merged_outputs['Read_Write'])
        self.out_Mem_Instruction        = self.addOut('out_Mem_Instruction',        merged_outputs['Mem_Instruction'])
        self.out_IncDec                 = self.addOut('out_IncDec',                 merged_outputs['IncDec'])
        self.out_write_Opperand_Buffer  = self.addOut('out_write_Opperand_Buffer',  merged_outputs['WE_Buffer'])
        self.out_InputSelect            = self.addOut('out_InputSelect',            merged_outputs['InputSelect'])
        self.out_Load_Z                 = self.addOut('out_Load_Z',                 merged_outputs['Load_Z'])
        self.out_Load_K                 = self.addOut('out_Load_K',                 merged_outputs['Load_K'])
        self.out_Load_Jump              = self.addOut('out_Load_Jump',              merged_outputs['Load_Jump'])
        self.out_relative_Absolute      = self.addOut('out_relative_Absolute',      merged_outputs['relative_Absolute'])
        self.out_Load_Byte              = self.addOut('out_Load_Byte',              merged_outputs['Load_Byte'])
        self.out_Fetch_Address          = self.addOut('out_Fetch_Address',          merged_outputs['Fetch_Address'])
        self.out_WB_Addr                = self.addOut('out_WB_Addr',                merged_outputs['WB_Addr'])
        self.out_JumpWidth              = self.addOut('out_JumpWidth',              merged_outputs['JumpWidth'])
        self.out_LOAD_PCL               = self.addOut('out_LOAD_PCL',               merged_outputs['LOAD_PCL'])
        self.out_LOAD_PCH               = self.addOut('out_LOAD_PCH',               merged_outputs['LOAD_PCH'])

    def propagate(self):
        # --- Bitwise OR assignments mirroring ALU_Merger ---
        self.out_done.put(self.opp_done.get() | self.mov_done.get() | self.poppush_done.get() | self.ldst_done.get() | self.callret_done.get())
        
        self.out_LoadSelectMux.put(self.opp_LoadSelectMux.get() | self.mov_LoadSelectMux.get() | self.poppush_LoadSelectMux.get() | self.ldst_LoadSelectMux.get() | self.callret_LoadSelectMux.get())
        
        self.out_LoadingMux.put(self.opp_LoadingMux.get() | self.mov_LoadingMux.get() | self.poppush_LoadingMux.get() | self.ldst_LoadingMux.get() | self.callret_LoadingMux.get())
        
        self.out_Input_Select.put(self.opp_Input_Select.get() | self.mov_Input_Select.get() | self.poppush_Input_Select.get() | self.ldst_Input_Select.get() | self.callret_Input_Select.get())
        
        self.out_WE.put(self.opp_WE.get() | self.mov_WE.get() | self.poppush_WE.get() | self.ldst_WE.get() | self.callret_WE.get())
        
        self.out_Read_Write.put(self.opp_Read_Write.get() | self.mov_Read_Write.get() | self.poppush_Read_Write.get() | self.ldst_Read_Write.get() | self.callret_Read_Write.get())
        
        self.out_Mem_Instruction.put(self.opp_Mem_Instruction.get() | self.mov_Mem_Instruction.get() | self.poppush_Mem_Instruction.get() | self.ldst_Mem_Instruction.get() | self.callret_Mem_Instruction.get())
        
        self.out_IncDec.put(self.opp_IncDec.get() | self.mov_IncDec.get() | self.poppush_IncDec.get() | self.ldst_IncDec.get() | self.callret_IncDec.get())
        
        self.out_write_Opperand_Buffer.put(self.opp_write_Opperand_Buffer.get() | self.mov_write_Opperand_Buffer.get() | self.poppush_write_Opperand_Buffer.get() | self.ldst_write_Opperand_Buffer.get() | self.callret_write_Opperand_Buffer.get())
        
        self.out_InputSelect.put(self.opp_InputSelect.get() | self.mov_InputSelect.get() | self.poppush_InputSelect.get() | self.ldst_InputSelect.get() | self.callret_InputSelect.get())
        
        self.out_Load_Z.put(self.opp_Load_Z.get() | self.mov_Load_Z.get() | self.poppush_Load_Z.get() | self.ldst_Load_Z.get() | self.callret_Load_Z.get())
        
        self.out_Load_K.put(self.opp_Load_K.get() | self.mov_Load_K.get() | self.poppush_Load_K.get() | self.ldst_Load_K.get() | self.callret_Load_K.get())
        
        self.out_Load_Jump.put(self.opp_Load_Jump.get() | self.mov_Load_Jump.get() | self.poppush_Load_Jump.get() | self.ldst_Load_Jump.get() | self.callret_Load_Jump.get())
        
        self.out_relative_Absolute.put(self.opp_relative_Absolute.get() | self.mov_relative_Absolute.get() | self.poppush_relative_Absolute.get() | self.ldst_relative_Absolute.get() | self.callret_relative_Absolute.get())
        
        self.out_Load_Byte.put(self.opp_Load_Byte.get() | self.mov_Load_Byte.get() | self.poppush_Load_Byte.get() | self.ldst_Load_Byte.get() | self.callret_Load_Byte.get())
        
        self.out_Fetch_Address.put(self.opp_Fetch_Address.get() | self.mov_Fetch_Address.get() | self.poppush_Fetch_Address.get() | self.ldst_Fetch_Address.get() | self.callret_Fetch_Address.get())
        
        self.out_WB_Addr.put(self.opp_WB_Addr.get() | self.mov_WB_Addr.get() | self.poppush_WB_Addr.get() | self.ldst_WB_Addr.get() | self.callret_WB_Addr.get())
        
        self.out_JumpWidth.put(self.opp_JumpWidth.get() | self.mov_JumpWidth.get() | self.poppush_JumpWidth.get() | self.ldst_JumpWidth.get() | self.callret_JumpWidth.get())
        
        self.out_LOAD_PCL.put(self.opp_LOAD_PCL.get() | self.mov_LOAD_PCL.get() | self.poppush_LOAD_PCL.get() | self.ldst_LOAD_PCL.get() | self.callret_LOAD_PCL.get())
        
        self.out_LOAD_PCH.put(self.opp_LOAD_PCH.get() | self.mov_LOAD_PCH.get() | self.poppush_LOAD_PCH.get() | self.ldst_LOAD_PCH.get() | self.callret_LOAD_PCH.get())