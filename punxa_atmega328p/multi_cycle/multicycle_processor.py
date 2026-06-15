import py4hw
from Memory import *
import ALU
import punxa_atmega328p.multi_cycle.MemoryInterfaceHandler as MemoryInterfaceHandler
import Instruction_decoder
import PC_handler


states = [
    STATE_RESET,
    STATE_FETCH_INS,
    STATE_DECODE,
    STATE_FETCH_OP2_REQ,STATE_FETCH_OP2_WAIT,
    STATE_FETCH_OP1_REQ,STATE_FETCH_OP1_WAIT,
    STATE_COMPUTE_RESULT,STATE_STORE_RESULT,
    STATE_INTERRUPT,
    STATE_SKIP
]


class multicycleProcessor(py4hw.logic):
    def __init__(self,parent,name:str,
                 reset,
                 memory:MemoryInterfaceHandler,
                 resetAddress, registerBase):
        
        super().__init__(parent, name)

        self.mem = self.addInterfaceSource('memory', memory)

        self.addIn('reset',reset)
        self.Pc = resetAddress



