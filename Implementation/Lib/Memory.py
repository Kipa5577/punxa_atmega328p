import py4hw
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import Simulator
import py4hw.debug
import mmap

#2048 bytes of ram
#32256 of rom 

class MemoryInterface(Interface):

    def __init__(self, parent:Logic, name:str, data_width:int, address_width:int):
        super().__init__(parent,name)

        self.read = self.addSourceToSink("read",1)
        self.write = self.addSourceToSink("write",1) # These are to enable read an wirte 

        self.write_data = self.addSourceToSink("writedata",data_width) 
        self.read_data = self.addSinkToSource("readdata",data_width)

        self.address = self.addSourceToSink("address",address_width)

        if((data_width % 8) != 0):
            raise Exception('data_width must be multiple of byte,{} not supported').format(data_width)
        
        #self.be = self.addSourceToSink('be', data_width // 8) #nb of bytes does not make sense because the registers of the mcu are 8 bit8 
        self.resp = self.addSinkToSource('resp',1)# 0 = normal state, 1 = Operation Performed


class Memory(Logic):
    def __init__(self, parent:Logic, name:str, data_width:int, address_width:int, port:MemoryInterface):
        super().__init__(parent, name)

        self.port0 = self.addInterfaceSink('port',port)
        self.startAddress = 0x0100
        self.stopAddress = 0x08FF
        self.values = [0]*(self.stopAddress-self.startAddress)

    def clock(self):
        address = self.port0.address.get()
        print("Address:",address)

        if (address >= self.startAddress) and (address <= self.stopAddress):
            address = address -0x0100 -1
            #print("opperation")
            #print((self.port0.read.get() == 1) and (self.port0.write.get() == 0))
            #print((self.port0.read.get() == 1) and (self.port0.write.get() == 1))
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.values[address])
                self.port0.resp.prepare(1)
                print('reading address ', address, '=', self.values[address])

            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.values[address] = self.port0.write_data.get()
                self.port0.resp.prepare(1)
                print('writing address ', address, '=', self.values[address])
                
            else:
                self.port0.resp.prepare(0)
        else:
            self.port0.resp.prepare(0)



class PersistentMemory(Logic):
    def __init__(self, parent:Logic, name:str,filename,port:MemoryInterface):
        super().__init__(parent,name)
        
        self.port = self.addInterfaceSink('port',port)
        file =  open(filename,'r+b')
        self.mm = mmap.mmap(file.foleno(),0)

    def clock(self):
        data_width = self.port.read_data.getWidth()

        address = self.port.address.get()
        be = self.port.be.get()

        if(self.port.read.get()):
            value = 0
            for i in range(data_width // 8 ):
                value = value | (self.readByte(address+i)<<(i*8))
            print('reading address',hex(address),'=',hex(value))

        elif(self.prot.write.get()):
            value = self.port.write_data.get()
            print('witing addres',hex(address),'=',hex(value))

            for i in range(data_width // 8):
                if((be & 0x1) != 0):
                    self.writeByte(address +i, value & 0xFF)
            




class ProgramMemory(py4hw.Logic):
    def __init__(self,parent,name,ADRESS,DATA_IN,DATA_OUT, Write_Enable): #RW = 0 then R else W
        super().__init__(parent, name)

        self.ADRESS = self.addIn('ADRESS', ADRESS)
        self.memory = [0]*32256 #address_width data_width
        self.DATA_OUT = self.addOut('DATA_OUT', DATA_OUT)
        self.DATA_IN = self.addIn('DATA_IN',DATA_IN)
        self.Write_Enable = self.addIn('Write_Enable',Write_Enable)

    def clock(self):
        if self.Write_Enable.get() == 1:
            self.DATA_OUT.prepare(self.memory[self.ADRESS.get()])
        else: 
            self.memory[self.ADRESS.get()] = self.DATA_IN


