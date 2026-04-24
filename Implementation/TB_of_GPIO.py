import py4hw
from Lib.Memory import *
from Lib.GPIO import *


sys = py4hw.HWSystem()


#mem = MemoryInterface(sys,'port0',8,16)

#Com = GPIO(sys,'GPIO',mem)

sch = py4hw.Schematic(sys)
sch.draw()