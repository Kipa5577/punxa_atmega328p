import py4hw

op_codes = {
    # Arithmetic and Logic
    'ADD': 1, 'ADC': 2, 'ADIW': 3, 'SUB': 4, 'SUBI': 5, 'SBC': 6, 'SBCI': 7, 'SBIW': 8,
    'AND': 9, 'ANDI': 10, 'OR': 11, 'ORI': 12, 'EOR': 13, 'COM': 14, 'NEG': 15,
    'SBR': 16, 'CBR': 17, 'INC': 18, 'DEC': 19, 'TST': 20, 'CLR': 21, 'SER': 22,
    
    # Multipliers
    'MUL': 23, 'MULS': 24, 'MULSU': 25, 'FMUL': 26, 'FMULS': 27, 'FMULSU': 28,
    
    # Branch Instructions
    'RJMP': 29, 'IJMP': 30, 'JMP': 31, 'RCALL': 32, 'ICALL': 33, 'CALL': 34,
    'RET': 35, 'RETI': 36, 'CPSE': 37, 'CP': 38, 'CPC': 39, 'CPI': 40,
    'SBRC': 41, 'SBRS': 42, 'SBIC': 43, 'SBIS': 44, 
    'BRBS': 45, 'BRBC': 46, 'BREQ': 47, 'BRNE': 48, 'BRCS': 49, 'BRCC': 50, 
    'BRSH': 51, 'BRLO': 52, 'BRMI': 53, 'BRPL': 54, 'BRGE': 55, 'BRLT': 56, 
    'BRHS': 57, 'BRHC': 58, 'BRTS': 59, 'BRTC': 60, 'BRVS': 61, 'BRVC': 62, 
    'BRIE': 63, 'BRID': 64,
    
    # Bit and Bit-Test Instructions
    'SBI': 65, 'CBI': 66, 'LSL': 67, 'LSR': 68, 'ROL': 69, 'ROR': 70, 'ASR': 71,
    'SWAP': 72, 'BSET': 73, 'BCLR': 74, 'BST': 75, 'BLD': 76,
    'SEC': 77, 'CLC': 78, 'SEN': 79, 'CLN': 80, 'SEZ': 81, 'CLZ': 82, 
    'SEI': 83, 'CLI': 84, 'SES': 85, 'CLS': 86, 'SEV': 87, 'CLV': 88, 
    'SET': 89, 'CLT': 90, 'SEH': 91, 'CLH': 92,
    
    # Data Transfer Instructions
    'MOV': 93, 'MOVW': 94, 'LDI': 95,
    
    # Memory Transfers 
    'LDX': 96,  'LDX+': 97,  'LD-X': 98, 
    'LDY': 99,  'LDY+': 100, 'LD-Y': 101, 'LDDY': 102,
    'LDZ': 103, 'LDZ+': 104, 'LD-Z': 105, 'LDDZ': 106, 
    'LDS': 107,
    
    'STX': 108, 'STX+': 109, 'ST-X': 110, 
    'STY': 111, 'STY+': 112, 'ST-Y': 113, 'STDY': 114,
    'STZ': 115, 'STZ+': 116, 'ST-Z': 117, 'STDZ': 118, 
    'STS': 119,
    
    'LPM': 120, 'LPMZ': 121, 'LPMZ+': 122, 'SPM': 123,
    
    # I/O and Stacks
    'IN': 124, 'OUT': 125, 'PUSH': 126, 'POP': 127,
    
    # MCU Control
    'NOP': 128, 'SLEEP': 129, 'WDR': 130, 'BREAK': 131
}
op_names = {v: k for k, v in op_codes.items()}

# Handled by OPP_FSM: ALU ops (Rd<-op(Rd,Rr/K)), compares, skips, single-register
# ops, SREG bit set/clear, MOV, 16-bit ADIW/SBIW, and conditional branches.
OPP_FSM_INS = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
    23, 24, 25, 26, 27, 28, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
    51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 
    71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88,
    89, 90, 91, 92, 93
}
 
# Handled by MOV_FSM: register-to-register / register-pair moves.
MOV_FSM_INS = {
    93,
    94
}
 
POPPUSH_FSM_INS = {
    126,
    127,
}
 
# Handled by LDST_FSM: all indirect/direct SRAM loads & stores.
LDST_FSM_INS = {
    95,                    # LDI
    96, 97, 98,            # LDX, LDX+, LD-X
    99, 100, 101, 102,     # LDY, LDY+, LD-Y, LDDY
    103, 104, 105, 106,    # LDZ, LDZ+, LD-Z, LDDZ
    107,                   # LDS
    108, 109, 110,         # STX, STX+, ST-X
    111, 112, 113, 114,    # STY, STY+, ST-Y, STDY
    115, 116, 117, 118,    # STZ, STZ+, ST-Z, STDZ
    119,                   # STS
    124, 125,              # IN, OUT
}
 
# Handled by CALLRET_FSM: unconditional jumps/calls and subroutine return.
# NOTE: RETI (36) is intentionally excluded — InterruptFSM owns it now,
# since returning from an interrupt also has to re-enable the I flag,
# which CallRetFSM has no mechanism to do. InterruptFSM is wired as a
# sibling of this box (see ControlBox), not dispatched through here.
CALLRET_FSM_INS = {
    29, 30, 31,            # RJMP, IJMP, JMP
    32, 33, 34,            # RCALL, ICALL, CALL
    35,                    # RET
}

# Handled by LPM_FSM: Program Memory load AND store instructions (LPM_FSM
# implements both -- see LPM.py, which now drives the SPM_req/R0_BUFFER/
# R1_BUFFER path for opcode 123 as well as its original LPM/LPMZ/LPMZ+
# handling).
LPM_FSM_INS = {
    120, 121, 122,         # LPM, LPMZ, LPMZ+
    123,                   # SPM
}

# NOTE: 128-131 (NOP/SLEEP/WDR/BREAK) remain unrouted -- these are handled
# directly by MainFSM (see MainFSM.EXECUTION), not dispatched to any
# sub-FSM here.
 
class FSM_SELECTOR(py4hw.Logic):
    def __init__(self, parent, name, run, instruction,
                 RUN_OPPFSM, RUN_MOVFSM, RUN_POPPUSHFSM, RUN_LDSTFSM, RUN_CALLRETFSM, RUN_LPMFSM):
        super().__init__(parent, name)
 
        self.run = self.addIn('run', run)
        self.instruction = self.addIn('instruction', instruction)
 
        self.RUN_OPPFSM = self.addOut('RUN_OPPFSM', RUN_OPPFSM)
        self.RUN_MOVFSM = self.addOut('RUN_MOVFSM', RUN_MOVFSM)
        self.RUN_POPPUSHFSM = self.addOut('RUN_POPPUSHFSM', RUN_POPPUSHFSM)
        self.RUN_LDSTFSM = self.addOut('RUN_LDSTFSM', RUN_LDSTFSM)
        self.RUN_CALLRETFSM = self.addOut('RUN_CALLRETFSM', RUN_CALLRETFSM)
        # Fixed: Added output name and wire parameter
        self.RUN_LPMFSM = self.addOut('RUN_LPMFSM', RUN_LPMFSM) 
 
        self.debug = 1

        # Rising-edge tracking for `run`, used only to gate the debug
        # prints below (not the RUN_* dispatch outputs). `run` is a
        # single-cycle pulse from MainFSM, but py4hw's settle model calls
        # propagate() twice per clock step, so an ungated `if run: print`
        # fires twice per real dispatch even though the underlying sub-FSM
        # only ever starts once (same class of issue as the
        # InterruptFSM.Entrance level-vs-edge bug — see handoff). Purely
        # cosmetic: RUN_* outputs still get put() every settle pass as
        # required for correct combinational behavior.
        self._prev_run = 0

    def propagate(self):
        run_active = self.run.get()
        ins = self.instruction.get()

        rising = (run_active == 1 and self._prev_run == 0)
        self._prev_run = run_active
 
        OPPFSM = 0
        MOVFSM = 0
        POPPUSHFSM = 0
        LDSTFSM = 0
        CALLRETFSM = 0
        LPMFSM = 0
 
        # Only decode and dispatch while the main controller is actually
        # requesting a sub-FSM to run_active; otherwise keep every RUN_* line low.
        if run_active:
            # NOTE: this used to also compute `ins_name = op_names.get(ins,
            # ...)` purely to make the debug prints below show a mnemonic
            # instead of a bare opcode. Removed for stock-transpiler
            # compatibility: a plain-dict `.get()` call here collides with
            # the transpiler's blanket interception of any `.get(...)` call
            # as a *wire* read (see report) -- and unlike a `print(...)`
            # call itself, this assignment is never stripped, so it would
            # reach the AST rewrite passes and break. The prints are
            # debug-only and get removed entirely during Verilog export
            # either way; they now just show the numeric opcode instead of
            # its mnemonic.
            if (((ins == 1) or ((ins == 2) or ((ins == 3) or ((ins == 4) or ((ins == 5) or ((ins == 6) or ((ins == 7) or ((ins == 8) or ((ins == 9) or ((ins == 10) or ((ins == 11) or ((ins == 12) or ((ins == 13) or ((ins == 14) or ((ins == 15) or ((ins == 16) or ((ins == 17) or ((ins == 18) or ((ins == 19) or ((ins == 20) or ((ins == 21) or ((ins == 22) or ((ins == 23) or ((ins == 24) or ((ins == 25) or ((ins == 26) or ((ins == 27) or ((ins == 28) or ((ins == 37) or ((ins == 38) or ((ins == 39) or ((ins == 40) or ((ins == 41) or ((ins == 42) or ((ins == 43) or ((ins == 44) or ((ins == 45) or ((ins == 46) or ((ins == 47) or ((ins == 48) or ((ins == 49) or ((ins == 50) or ((ins == 51) or ((ins == 52) or ((ins == 53) or ((ins == 54) or ((ins == 55) or ((ins == 56) or ((ins == 57) or ((ins == 58) or ((ins == 59) or ((ins == 60) or ((ins == 61) or ((ins == 62) or ((ins == 63) or ((ins == 64) or ((ins == 65) or ((ins == 66) or ((ins == 67) or ((ins == 68) or ((ins == 69) or ((ins == 70) or ((ins == 71) or ((ins == 72) or ((ins == 73) or ((ins == 74) or ((ins == 75) or ((ins == 76) or ((ins == 77) or ((ins == 78) or ((ins == 79) or ((ins == 80) or ((ins == 81) or ((ins == 82) or ((ins == 83) or ((ins == 84) or ((ins == 85) or ((ins == 86) or ((ins == 87) or ((ins == 88) or ((ins == 89) or ((ins == 90) or ((ins == 91) or ((ins == 92) or (ins == 93)))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))):
                if self.debug == 1 and rising:
                    print(f"OPP_FSM Selected | Instruction: {ins}")
                OPPFSM = 1
            elif ((ins == 93) or (ins == 94)):
                if self.debug == 1 and rising:
                    print(f"MOV_FSM Selected | Instruction: {ins}")
                MOVFSM = 1
            elif ((ins == 126) or (ins == 127)):
                if self.debug == 1 and rising:
                    print(f"POPPUSH_FSM Selected | Instruction: {ins}")
                POPPUSHFSM = 1
            elif (((ins == 95) or ((ins == 96) or ((ins == 97) or ((ins == 98) or ((ins == 99) or ((ins == 100) or ((ins == 101) or ((ins == 102) or ((ins == 103) or ((ins == 104) or ((ins == 105) or ((ins == 106) or ((ins == 107) or ((ins == 108) or ((ins == 109) or ((ins == 110) or ((ins == 111) or ((ins == 112) or ((ins == 113) or ((ins == 114) or ((ins == 115) or ((ins == 116) or ((ins == 117) or ((ins == 118) or ((ins == 119) or ((ins == 124) or (ins == 125)))))))))))))))))))))))))))):
                if self.debug == 1 and rising:
                    print(f"LDST_FSM Selected | Instruction: {ins}")
                LDSTFSM = 1
            elif (((ins == 32) or ((ins == 33) or ((ins == 34) or ((ins == 35) or ((ins == 29) or ((ins == 30) or (ins == 31)))))))):
                if self.debug == 1 and rising:
                    print(f"CALLRET_FSM Selected | Instruction: {ins}")
                CALLRETFSM = 1
            elif (((ins == 120) or ((ins == 121) or ((ins == 122) or (ins == 123))))):
                if self.debug == 1 and rising:
                    print(f"LPM_FSM Selected | Instruction: {ins}")
                LPMFSM = 1

 
        self.RUN_CALLRETFSM.put(CALLRETFSM)
        self.RUN_LDSTFSM.put(LDSTFSM)
        self.RUN_MOVFSM.put(MOVFSM)
        self.RUN_OPPFSM.put(OPPFSM)
        self.RUN_POPPUSHFSM.put(POPPUSHFSM)
        self.RUN_LPMFSM.put(LPMFSM)