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


# Handled by OPP_FSM: ALU ops (Rd<-op(Rd,Rr/K)), compares, skips, single-register
# ops, SREG bit set/clear, MOV, 16-bit ADIW/SBIW, and conditional branches. 
# See OPP_FSM's own opcode sets for the exact per-instruction routing inside that FSM.
OPP_FSM_INS = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
    23, 24, 25, 26, 27, 28, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
    51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 67, 68, 69, 70,
    71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88,
    89, 90, 91, 92, 93, 95
}
 
# Handled by MOV_FSM: register-to-register / register-pair moves.
# NOTE: 93 (MOV) appears in OPP_FSM_INS as well as here in the original
# source. The if/elif order below checks OPP_FSM_INS first, so MOV (93)
# is routed to OPP_FSM, not MOV_FSM, as written. MOVW (94) is the only
# opcode that actually reaches this branch.
MOV_FSM_INS = {
    93,
    94
}
 
POPPUSH_FSM_INS = {
    126,
    127,
}
 
# Handled by LDST_FSM: all indirect/direct SRAM loads & stores (X/Y/Z
# pointer addressing, displacement addressing, direct LDS/STS) and the
# I/O space accesses IN/OUT and SBI/CBI (single-bit I/O set/clear, which
# reuses the same A-6bit/Rd-style memory-interface access as IN/OUT).
LDST_FSM_INS = {
    96, 97, 98,            # LDX, LDX+, LD-X
    99, 100, 101, 102,     # LDY, LDY+, LD-Y, LDDY
    103, 104, 105, 106,    # LDZ, LDZ+, LD-Z, LDDZ
    107,                   # LDS
    108, 109, 110,         # STX, STX+, ST-X
    111, 112, 113, 114,    # STY, STY+, ST-Y, STDY
    115, 116, 117, 118,    # STZ, STZ+, ST-Z, STDZ
    119,                   # STS
    124, 125,              # IN, OUT
    65, 66,                # SBI, CBI
}
 
# Handled by CALLRET_FSM: unconditional jumps/calls and subroutine return.
CALLRET_FSM_INS = {
    29, 30, 31,            # RJMP, IJMP, JMP
    32, 33, 34,            # RCALL, ICALL, CALL
    35, 36,                # RET, RETI
}

# --------------------------------------------------------------------------
# NOT YET ROUTED to any sub-FSM by this selector — flagged rather than
# guessed, since assigning them silently could route an instruction to an
# FSM that doesn't actually decode it:
#
#   120-123       LPM/LPMZ/LPMZ+/SPM — explicitly commented OUT of
#                                  LDST_FSM's _LOAD_MEM/_STORE_MEM sets,
#                                  so routing them to LDST_FSM_INS would
#                                  silently fall through to STOP with no
#                                  work done.
#   128-131       NOP/SLEEP/WDR/BREAK — take no operand and need no
#                                  sub-FSM at all; the main controller
#                                  likely advances directly without
#                                  asserting any RUN_* line.
# --------------------------------------------------------------------------
 
 
class FSM_SELECTOR(py4hw.Logic):
    def __init__(self, parent, name, run, instruction,
                 RUN_OPPFSM, RUN_MOVFSM, RUN_POPPUSHFSM, RUN_LDSTFSM, RUN_CALLRETFSM):
        super().__init__(parent, name)
 
        self.run = self.addIn('RUN', run)
        self.instruction = self.addIn('INSTRUCTION', instruction)
 
        self.RUN_OPPFSM = self.addOut('RUN_OPPFSM', RUN_OPPFSM)
        self.RUN_MOVFSM = self.addOut('RUN_MOVFSM', RUN_MOVFSM)
        self.RUN_POPPUSHFSM = self.addOut('RUN_POPPUSHFSM', RUN_POPPUSHFSM)
        self.RUN_LDSTFSM = self.addOut('RUN_LDSTFSM', RUN_LDSTFSM)
        self.RUN_CALLRETFSM = self.addOut('RUN_CALLRETFSM', RUN_CALLRETFSM)
 
    def propagate(self):
        run = self.run.get()
        ins = self.instruction.get()
 
        OPPFSM = 0
        MOVFSM = 0
        POPPUSHFSM = 0
        LDSTFSM = 0
        CALLRETFSM = 0
 
        # Only decode and dispatch while the main controller is actually
        # requesting a sub-FSM to run; otherwise keep every RUN_* line low.
        if run:
            if ins in OPP_FSM_INS:
                print("OPP_FSM Selected")
                OPPFSM = 1
            elif ins in MOV_FSM_INS:       # mov instructions
                print("MOV_FSM Selected")
                MOVFSM = 1
            elif ins in POPPUSH_FSM_INS:
                print("POPPUSH_FSM Selected")
                POPPUSHFSM = 1
            elif ins in LDST_FSM_INS:
                print("LDST_FSM Selected")
                LDSTFSM = 1
            elif ins in CALLRET_FSM_INS:
                print("CALLRET_FSM Selected")
                CALLRETFSM = 1

 
        self.RUN_CALLRETFSM.put(CALLRETFSM)
        self.RUN_LDSTFSM.put(LDSTFSM)
        self.RUN_MOVFSM.put(MOVFSM)
        self.RUN_OPPFSM.put(OPPFSM)
        self.RUN_POPPUSHFSM.put(POPPUSHFSM)