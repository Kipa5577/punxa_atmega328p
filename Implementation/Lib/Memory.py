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
        self.read_data = self.addSinkToSource("readdata",data_width)
        self.address = self.addSourceToSink("address",address_width)
        self.write = self.addSourceToSink("write",1)
        self.write_data = self.addSourceToSink("writedata",data_width)
        if((data_width % 8) != 0):
            raise Exception('data_width must be multiple of byte,{} not supported').format(data_width)
        self.be = self.addSourceToSink('be', data_width // 8) #nb of bytes
        self.resp = self.addSinkToSource('resp',1)# 0 = OK , 1 = ERROR


class Memory(Logic):
    def __init__(self, parent:Logic, name:str, data_width:int, address_width:int, port:MemoryInterface):
        super().__init__(parent, name)

        self.port0 = self.addInterfaceSink('port',port)

        self.verbose = False
        self.values = bytearray((1 << address_width) * (data_width // 8))


    def wrtieByte(self,address:int, value:int):
        if(address>=0 and address < len(self.values)):
            return self.values[address]
            
    def readByte(self,address):
        if(address >= 0 and address < len(self.values)):
            return self.values[address]

    def clock(self):
        data_width = self.port0.read_data.getWidth()

        address = self.port0.address.get()
        be = self.port0.be.get()
        self.port0.resp.prepare(0)

        if(self.port0.read.get()):
            value = 0

            for i in range(data_width // 8):
                value = value | (self.readByte(address+i)<< (i*8))

            self.port0.read_data.prepare(value)
            print('reading address', address,'=',hex(value))
        elif(self.port0.write.get()):
            value = self.port0.write_data.get()

            print('writing address',address,'=',hex(value))

            for i in range(data_width // 8):
                if((be & 0x1)!=0):
                    self.wrtieByte(address + 1 ,value & 0xFF) 
                be = be >> 1
                value = value >> 8          


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


