import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.Memory import *

from punxa_atmega328p.csr import *
from deprecated import deprecated


FETCH_HANDLER_STATES = [
    "FETCH_INSTRUCTION","WAIT_FETCH_INSTRUCTION","STOP","STATE_RESET"
]


class fetch_handler(py4hw.Logic):
    def __init__(self, parent, name:str, ins_mem:MemoryInterface,fetched_instruction_out,reset):
        super().__init__(parent, name)

        self.ins_mem = self.addInterfaceSource('ins',ins_mem)

        