# source cpu_env/bin/activate
import py4hw
from Implementation.Lib.ALU_test import *                                      


sys = py4hw.HWSystem()

on = py4hw.Wire(sys,'on',1)
A = py4hw.Wire(sys,'A',8)
B = py4hw.Wire(sys, 'B',8)
OUT = py4hw.Wire(sys, 'OUT',8)
opp =  py4hw.Wire(sys,'opp',6)
Z = py4hw.Wire(sys,'Z',1) # Zero 

C = py4hw.Wire(sys,'C',1) # carry out

N = py4hw.Wire(sys,'N',1) # Negatif 



ALU = ALUBehavioral(sys,'A1',on,A,B,OUT,opp,Z,C,N);


py4hw.Sequence(sys,'opp',[0b000011,0b000110,0b001000,0b001010,0b001001],opp)
py4hw.Sequence(sys,'A',[0b11111111,0b00000001,0b00001010,0b00000000,0b00001101],A)
py4hw.Sequence(sys,'B',[0b00000001,0b00000010,0b00000000,0b00001010,0b00011001],B)
py4hw.Sequence(sys,'on',[1,1,0,0,0],on)

print('circuit created')

wvf = py4hw.Waveform(sys, 'wvf', [on,A,B,OUT,opp,Z,C,N])
sys.getSimulator().clk(100)
wvf.gui()
