import py4hw
import os
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
    while 1 :
        start_Code = f.read(1)
        if not start_Code:
            break
        start_Code = str(start_Code,'utf-8')
        print(start_Code)
        nbbytes = str(f.read(2),'utf-8')
        #print(nbbytes)
        starting_address =  str(f.read(4),'utf-8')
        #print(starting_address)
        record_type = str(f.read(2),'utf-8')
        #print(record_type)
        if record_type == "00": # To write only "Data Record"
            ##print("True")
            memory_position = int(starting_address,16)//2
            for i in range(int(nbbytes,16)//2): 
                byte = str(f.read(4),'utf-8')
                print("{index} {val}".format(index = i ,val = byte))    
                CPU.flash[memory_position] = int(byte,16)  #little or big 
                memory_position+=1

            checksum = str(f.read(2),'utf-8')
            print(checksum)
            end_of_line_caracters = str(f.read(2),'utf-8')
            print(end_of_line_caracters)
    f.close()

main_loop = True
while main_loop == True:
    print("Hello \n n : next instruction \n r: ram memory dump \n f: flash memory dump \n e: exit ")
    
    print("Register State")
    #print register state 
    print("Current instruction:{instruction}".format(instruction =  ins_to_str(CPU.flash[CPU.pc])))
    for i in range(32):
        print("R{index} : {value}".format(index = i, value = CPU.reg[i]),end=" ")
    print("Pc:{value}".format(value = CPU.pc))
    print("Ps:{value}".format(value = CPU.stack_pointer))

    user_command = input()
    if user_command ==  'f':
        if os.path.exists("FlashMemoryDump.txt"):
            os.remove("FlashMemoryDump.txt")

        ## CPU Flash memory dump  
        dump = open("FlashMemoryDump.txt", "a")
        #dump with instrucions decoded. #CALL and JUMP are 32bits 
        for i in range(0,len(CPU.flash)):
            ins = CPU.flash[i] 
            if CPU.pc == i: 
                dump.write(">{0:>016b} : {instr} \n".format(ins,instr = ins_to_str(ins)))
            else:
                dump.write("{0:>016b} : {instr} \n".format(ins,instr = ins_to_str(ins)))

        dump.close()

    elif user_command == 'r':
        if os.path.exists("RamMemoryDump.txt"):
            os.remove("RamMemoryDump.txt")

        ## CPU Flash memory dump  
        dump = open("RamMemoryDump.txt", "a")
        #dump with instrucions decoded. #CALL and JUMP are 32bits 
        for i in range(0,len(CPU.flash)):
            ins = CPU.flash[i] 
            dump.write("{0:>016b} : {instr} \n".format(ins,instr = ins_to_str(ins)))

        dump.close()
        
    elif user_command == 'n':        
        sys.getSimulator().clk(1)
        print("Current instruction:{instruction}".format(instruction =  ins_to_str(CPU.flash[CPU.pc])))
        for i in range(32):
            print("R{index}:{value}".format(index = i, value = CPU.reg[i]),end=" ")
        print("Pc:{value}".format(value = CPU.pc))
        print("Ps:{value}".format(value = CPU.stack_pointer))
        print("---------------------------------------------------------------")
    
    elif user_command == 'e':#to exit
        main_loop = False


#print register state 


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


