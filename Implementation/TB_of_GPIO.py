import py4hw
from Lib.Memory import *
from Lib.GPIO import *
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import Simulator
import py4hw.debug

#TEST SEQUANCE LISTS
READ_TEST =         [0   ,0   ,0   ,1   ,1    ]
WRITE_TEST =        [1   ,1   ,0   ,0   ,0    ]
WRITE_DATA_TEST =   [0xF0,0xF0,0xF0,0   ,0   ,0xA0,0xA0,0xA0,0   ,0   ,0xB0,0xB0,0xB0  ,0   ,0   ]
READ_DATA_CORRECT = [0   ,0   ,0   ,0xF0,0xF0,0xF0,0xF0,0xF0,0xA0,0xA0,0xA0,0xA0,0xA0  ,0xB0,0xB0]
ADDRESS_TEST_IO = [
                0x2B,0x2B,0x2B,0x2B,0x2B, #GPIOR2
                0x2A,0x2A,0x2A,0x2A,0x2A, #GPIOR1
                0x1E,0x1E,0x1E,0x1E,0x1E, #GPIOR0

                0x05,0x05,0x05,0x05,0x05, #PORTB
                0x04,0x04,0x04,0x04,0x04, #DDRB
                0x03,0x03,0x03,0x03,0x03, #PINB

                0x08,0x08,0x08,0x08,0x08, #PORTC
                0x07,0x07,0x07,0x07,0x07, #DDRC
                0x06,0x06,0x06,0x06,0x06, #PINC

                0x0B,0x0B,0x0B,0x0B,0x0B, #PORTD
                0x0A,0x0A,0x0A,0x0A,0x0A, #DDRD
                0x09,0x09,0x09,0x09,0x09, #PIND

                ]
ADDRESS_TEST_LS = [
                0x4B,0x4B,0x4B,0x4B,0x4B, #GPIOR2
                0x4A,0x4A,0x4A,0x4A,0x4A, #GPIOR1
                0x3E,0x3E,0x3E,0x3E,0x3E, #GPIOR0

                0x25,0x25,0x25,0x25,0x25, #PORTB
                0x24,0x24,0x24,0x24,0x24, #DDRB
                0x23,0x23,0x23,0x23,0x23, #PINB

                0x28,0x28,0x28,0x28,0x28, #PORTC
                0x27,0x27,0x27,0x27,0x27, #DDRC
                0x26,0x26,0x26,0x26,0x26, #PINC

                0x2B,0x2B,0x2B,0x2B,0x2B, #PORTD
                0x2A,0x2A,0x2A,0x2A,0x2A, #DDRD
                0x29,0x29,0x29,0x29,0x29, #PIND
                ]
BE_TEST = [1]
ADDRESS_TEST_FULL = []
ADDRESS_TEST_FULL.append(ADDRESS_TEST_IO)
ADDRESS_TEST_FULL.append(ADDRESS_TEST_LS)
INSTYPE_TEST = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


# Valeurs Correctes


sys = py4hw.HWSystem()


Interface = MemoryInterface(sys,'port0',8,16)
instype = py4hw.Wire(sys,'INSTYPE',1)

Module = GPIO(sys,'GPIO',Interface,instype)
#read
#read_data
#address
#write
#write_data
#be
#resp


#Interface.read_data = py4hw.Wire(sys,'read_data',1)
#Interface.resp = py4hw.Wire(sys,'resp',1)

py4hw.Sequence(sys,'INSTYPE',INSTYPE_TEST,instype)
py4hw.Sequence(sys,'read',READ_TEST,Interface.read)
#py4hw.Sequence(sys,'read_data',[0,0,0,0,0,0,0,0,1],Interface.read_data)
py4hw.Sequence(sys,'address',ADDRESS_TEST_LS,Interface.address)
py4hw.Sequence(sys,'write',WRITE_TEST,Interface.write)
py4hw.Sequence(sys,'write_data',WRITE_DATA_TEST,Interface.write_data)
py4hw.Sequence(sys,'be',BE_TEST,Interface.be)
#py4hw.Sequence(sys,'resp',[0,0,0,0,0,0,0,0,1],Interface.resp)

wvf = py4hw.Waveform(sys, 'wvf', [Interface.read_data,Interface.resp,Interface.read,Interface.address,Interface.write,Interface.write_data,Interface.be,instype])

#sch = py4hw.Schematic(sys)
#sch.draw()

print("Output Debug: GPIOR2:{val1} GPIOR1:{val2} GPIOR0:{val3}".format(val1 = Module.GPIOR2,val2 = Module.GPIOR1, val3 = Module.GPIOR0))
print("Output Debug: PORTB: {val1} PORTC: {val2} PORTD: {val3}".format(val1 = Module.PORTB,val2 = Module.PORTC, val3 = Module.PORTD))
print("Output Debug: DDRB:  {val1} DDRC:  {val2} DDRD:  {val3}".format(val1 = Module.DDRB,val2 = Module.DDRC, val3 = Module.DDRD))
print("Output Debug: PINB:  {val1} PINC:  {val2} PIND:  {val3}".format(val1 = Module.PINB,val2 = Module.PINC, val3 = Module.PIND))

#cycle = True
#while cycle:
#    a = input()
#    sys.getSimulator().clk(1)
#    print(Module.ADDR)
#    print(Module.PORTB_addr_IO)
#    if a == 'e':
#        cycle = FALSE

sys.getSimulator().clk(1000)
print("Output Debug: GPIOR2:{val1} GPIOR1:{val2} GPIOR0:{val3}".format(val1 = Module.GPIOR2,val2 = Module.GPIOR1, val3 = Module.GPIOR0))
print("Output Debug: PORTB: {val1} PORTC: {val2} PORTD: {val3}".format(val1 = Module.PORTB,val2 = Module.PORTC, val3 = Module.PORTD))
print("Output Debug: DDRB:  {val1} DDRC:  {val2} DDRD:  {val3}".format(val1 = Module.DDRB,val2 = Module.DDRC, val3 = Module.DDRD))
print("Output Debug: PINB:  {val1} PINC:  {val2} PIND:  {val3}".format(val1 = Module.PINB,val2 = Module.PINC, val3 = Module.PIND))

wvf.gui()