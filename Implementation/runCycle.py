import py4hw



class SingleCycleATmega328P(py4hw.Logic):

    def __init__(sel,parent, name:str , memory:MemoryInterface):
        super().__init__(parent,name)

        self.mem =self.addInterfaceSource('memory',memory)
        self.pc = 0x0
        self.reg = [0]*32
