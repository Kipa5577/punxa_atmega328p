import py4hw
from Lib.Memory import *
from Lib.GPIO import *
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import Simulator
import py4hw.debug

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


#Interface.read_data = py4hw.Wire(sys,'read_data',1)
#Interface.resp = py4hw.Wire(sys,'resp',1)


py4hw.Sequence(sys,'read',[0,0,0,1,1,0,0,0,0],Interface.read)
#py4hw.Sequence(sys,'read_data',[0,0,0,0,0,0,0,0,1],Interface.read_data)
py4hw.Sequence(sys,'address',[0x2B],Interface.address)
py4hw.Sequence(sys,'write',[1,1,0,0,0,0,0,0,0],Interface.write)
py4hw.Sequence(sys,'write_data',[0xFF],Interface.write_data)
py4hw.Sequence(sys,'be',[1],Interface.be)
#py4hw.Sequence(sys,'resp',[0,0,0,0,0,0,0,0,1],Interface.resp)

wvf = py4hw.Waveform(sys, 'wvf', [Interface.read_data,Interface.resp,Interface.read,Interface.address,Interface.write,Interface.write_data,Interface.be])

sch = py4hw.Schematic(sys)
sch.draw()
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))

sys.getSimulator().clk(1)
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))
sys.getSimulator().clk(1)
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))

sys.getSimulator().clk(1)
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))

sys.getSimulator().clk(1)
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))

sys.getSimulator().clk(1)
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))

sys.getSimulator().clk(1)
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))

sys.getSimulator().clk(1)
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))

sys.getSimulator().clk(1)
print("Output Debug: {val1} {val2} {val3}".format(val1 = Module.addresGot,val2 = Module.writeab, val3 = Module.readab))


wvf.gui()