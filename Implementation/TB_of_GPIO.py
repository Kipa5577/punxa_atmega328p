import py4hw
from Lib.Memory import *
from Lib.GPIO import *


sys = py4hw.HWSystem()


Interface = MemoryInterface(sys,'port0',8,16)

Module = GPIO(sys,'GPIO',Interface)
#read
#read_data
#address
#write
#write_data
#be
#resp

py4hw.Sequence(sys,'read',[0,0,0,0,0,0,0,0,17],Interface.read)
py4hw.Sequence(sys,'read_data',[0,0,0,0,0,0,0,0,1],Interface.read_data)
py4hw.Sequence(sys,'address',[0,0,0,0,0,0,0,0,17],Interface.address)
py4hw.Sequence(sys,'write',[0,0,0,0,0,0,0,0,1],Interface.write)
py4hw.Sequence(sys,'write_data',[0,0,0,0,0,0,0,0,17],Interface.write_data)
py4hw.Sequence(sys,'be',[0,0,0,0,0,0,0,0,1],Interface.be)
py4hw.Sequence(sys,'be',[0,0,0,0,0,0,0,0,1],Interface.resp)


sch = py4hw.Schematic(sys)
sch.draw()