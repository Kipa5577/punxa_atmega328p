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


port_C = MemoryInterface(sys,'port_C',8,16)
port_B = MemoryInterface(sys,'port_B',8,16)
port_U = MemoryInterface(sys,'port_U',8,16)
port_S = MemoryInterface(sys,'port_S',8,16)
port_A = MemoryInterface(sys,'port_A',8,16)
port_G = MemoryInterface(sys,'port_G',8,16)
port_T0= MemoryInterface(sys,'prot_T0',8,16)
port_T1= MemoryInterface(sys,'prot_T1',8,16)
port_T2= MemoryInterface(sys,'prot_T2',8,16)





#sch = py4hw.Schematic(sys)
#sch.draw()
 

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
        print(nbbytes)
        starting_address =  str(f.read(4),'utf-8')
        print(starting_address)
        record_type = str(f.read(2),'utf-8')
        print(record_type)
        if record_type == "00": # To write only "Data Record"
            ##print("True")
            memory_position = int(starting_address,16)//2

            for i in range(int(nbbytes,16)//2): 
                byteLSB = str(f.read(2),'utf-8')  #there may be a problem between word adressis and byte adressis but I am willing to let it slide
                byteMSB = str(f.read(2),'utf-8')
                byte = byteMSB + byteLSB
                CPU.flash[memory_position] = int(byte,16)  #little or big 
                print("{flash} {mem_pos} {index} {val}".format(flash=hex(CPU.flash[memory_position]),mem_pos=memory_position,index = i ,val = byte))   
                memory_position+=1

            checksum = str(f.read(2),'utf-8')
            print(checksum)
            end_of_line_caracters = str(f.read(2),'utf-8')
            print(end_of_line_caracters)

        elif record_type == '01': #"End of Record."

            memory_position = int(starting_address,16)//2
            byte = str(f.read(4),'utf-8')
            print("{index} {val}".format(index = i ,val = byte)) 
            #CPU.flash[memory_position] = int(byte,16)  #little or big 
            checksum = str(f.read(2),'utf-8')
            print(checksum)
            end_of_line_caracters = str(f.read(2),'utf-8')
            print(end_of_line_caracters)
            
        elif record_type == '02':  #"Extended Segment Address Record"
            print("Record type 02 not implemented")

        elif record_type == '03':  #"Start Segment Address Record"
            print("Record type 03 not implemented")

        elif record_type == '04':  #"Extended Linear Address Record"
            byte = str(f.read(4),'utf-8')
            print("{val}".format( val = byte)) 
            memory_position = 0
            checksum = str(f.read(2),'utf-8')
            print(checksum)
            end_of_line_caracters = str(f.read(2),'utf-8')
            print(end_of_line_caracters)

        elif record_type == '05':  #"Extended Linear Address Record"
            print("Record type 05 not implemented")
            
    f.close()



print("Hello \n n : next instruction \n r: ram memory dump \n f: flash memory dump \n e: exit ")
    
print("Register State")
#print register state 
print("Current instruction:{instruction}".format(instruction =  ins_to_str(CPU.flash[CPU.pc])))
for i in range(32):
    print("R{index} : {value}".format(index = i, value = CPU.reg[i]),end=" ")
print("Pc:{value}".format(value = CPU.pc))
print("Ps:{value}".format(value = CPU.stack_pointer))
print("opp:{value1} ins:{value2} Rr:{value3} Rd:{value4} K:{value5}".format(value1 = CPU.opp,value2 = CPU.ins, value3 = CPU.Rr, value4 = CPU.Rd,value5 = CPU.K))
#print("I:{I} T:{T} H:{H} S:{S} V:{V} N:{N} Z:{Z} C{C}".format(I = CPU.I))
print("SREG:{0:>08b}".format(CPU.SREG))

main_loop = True
while main_loop == True:


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
        for i in range(0,len(RAM.values)):
            val = RAM.values[i]
            dump.write("{0:>016b} : {val1} \n".format(val,val1 = val))

        dump.close()
        
    elif user_command == 'n':        
        sys.getSimulator().clk(1)
        print("Current instruction:{instruction}".format(instruction =  ins_to_str(CPU.flash[CPU.pc])))
        for i in range(32):
            print("R{index}:{value}".format(index = i, value = CPU.reg[i]),end=" ")
        print("Pc:{value}".format(value = CPU.pc))
        print("Ps:{value}".format(value = CPU.stack_pointer))
        print("opp:{value1} ins:{value2} Rr:{value3} Rd:{value4} K:{value5}".format(value1 = CPU.opp,value2 = CPU.ins, value3 = CPU.Rr, value4 = CPU.Rd,value5 = CPU.K))
        print("SREG:{0:>08b}".format(CPU.SREG))
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


