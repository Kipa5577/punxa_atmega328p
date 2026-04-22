import py4hw
from Lib.SingleCycle.runCycle import *
from Lib.Memory import *
from Lib.Instruction_Decoder import *

#  +-----+    +-----+     +-----+
#  | CPU |--C-| bus |--B--| mem |
#  +-----+    |     |     +-----+
#             |     |     +------+
#             |     |--U--| uart |
#             |     |     +------+
#             |     |     +-----+
#             |     |--S--| SPI |
#             |     |     +-----+
#             |     |     +-----+
#             |     |--A--| ADC |
#             |     |     +-----+
#             |     |     +------+
#             |     |--G--| GPIO |
#             |     |     +------+
#             |     |      +-----------+
#             |     |--T0--| 8bitTimer0|
#             |     |      +-----------+
#             |     |      +------------+
#             |     |--T1--| 16bitTimer1|
#             |     |      +------------+
#             |     |      +-----------+
#             |     |--T2--| 8bitTimer2|
#             |     |      +-----------+
#             +-----+
#  | start               | stop                | device        |
#  | 0080 0000 0000 0000 | 0080 0000 FFFF FFFF | memory (2GB)  |
#  | 0000 00FF F0C2 C000 | 0000 00FF F0C2 CFFF | UART          |
#  | 0000 0000 0200 0000 | 0000 0000 0202 FFFF | CLINT         |
#  | 0000 0000 0C00 0000 | 0000 0000 0C0F FFFF | PLIC          |
#  | 0000 0000 0C00 0000 | 0000 0000 0C0F FFFF | GPIO          |




sys = py4hw.HWSystem()

mem = MemoryInterface(sys,'port0',8,16)

CPU = SingleCycleATmega328P(sys,'Arduino',mem)
RAM = Memory(sys,'mem',8,16,mem)



 

## loading hex file to memory
memory_position = 0
with open('./Code_Test/main.hex','rb') as f:
    while 1:
        byte = f.read(2)
        if not byte:
            break
        CPU.flash[memory_position] = int.from_bytes(byte,"big")  #little or big 
        memory_position+=1
    f.close()


## CPU memory dump raw 
dump = open("memoryDump.txt", "a")

#for i in range(len(CPU.flash)):
#    dump.write(str(CPU.flash[i]))
#    if i % 16 == 0:
#        dump.write("\n")


print(type(CPU.flash[0]))
print(bin(CPU.flash[0] ))#+ CPU.flash[1]))

#dump with instrucions decoded.
for i in range(0,len(CPU.flash)):
    ins = CPU.flash[i] 
    dump.write("{0:>016b} : {instr} \n".format(ins,instr = ins_to_str(ins)))

dump.close()
        





#UART
#SPI
#ADC
#GPIO
#I2C
# 8-bit Timer/Counter0 with PWM
# 8-bit Timer/Counter2 with PWM
# 16-bit Timer/Counter1 wiht PWM


#sch = py4hw.Schematic(sys)
#sch.draw()


