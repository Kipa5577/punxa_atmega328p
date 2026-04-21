# source cpu_env/bin/activate

import datetime
import py4hw
from Lib.Instruction_Decoder import *      
'''

sys = py4hw.HWSystem()


ADRESS = py4hw.Wire(sys,'ADRESS',16)
DATA_IN = py4hw.Wire(sys,'DATA_IN',16)
DATA_OUT = py4hw.Wire(sys,'DATA_OUT',16)
Write_Enable = py4hw.Wire(sys,'Write_Enable',1);


PC = ProgramMemory(sys,'Mem1',ADRESS,DATA_IN,DATA_OUT, Write_Enable);

py4hw.Sequence(sys,'ADRESS',[0xFFFF,0xFFFF,0xFAFF,0xFAFF],ADRESS)
py4hw.Sequence(sys,'DATA_IN',[0xBBBB,0xBBBB,0xAAAA,0xAAAA],DATA_IN)
py4hw.Sequence(sys,'Write_Enable',[1,1,0,0],Write_Enable)

print('circuit created')



wvf = py4hw.Waveform(sys, 'wvf', [ADRESS,DATA_IN,DATA_OUT, Write_Enable])
sys.getSimulator().clk(100)
wvf.gui()
'''

list = []
f = open("output.txt", "a")
x = datetime.datetime.now()
f.write("Test conducted on {time} \n".format(time = x))
for ins in range(2**16):
    with open("output.txt", "a") as f:
        f.write("Ins {0:>016b} is {instruction}\n".format(ins,instruction = ins_to_str(ins)))
    if ins_to_str(ins) not in list:
        list.append(ins_to_str(ins))
print(list)
print(len(list))