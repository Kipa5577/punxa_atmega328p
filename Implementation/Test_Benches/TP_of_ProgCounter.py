# source cpu_env/bin/activate
import py4hw
from Lib.ProgramCounter import *                                      


sys = py4hw.HWSystem()

Load_data = py4hw.Wire(sys,'Load_data',16)
Load_Enable = py4hw.Wire(sys,'Load_Enable',1)
OUT = py4hw.Wire(sys,'OUT',16)

PC = ProgCounter(sys,'PC1',Load_data,Load_Enable,OUT)

py4hw.Sequence(sys,'Load_data',[0,0,0,0,0,0,0,0,17],Load_data)
py4hw.Sequence(sys,'Load_Enable',[0,0,0,0,0,0,0,0,1],Load_Enable)

print('circuit created')

wvf = py4hw.Waveform(sys, 'wvf', [Load_data,Load_Enable,OUT])
sys.getSimulator().clk(5)
wvf.gui()
