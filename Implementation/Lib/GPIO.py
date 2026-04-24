import py4hw
from Lib.Memory import * 
import py4hw
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import Simulator
import py4hw.debug

## *_IO = IN and OUT instruction address
## *_LS =  LD LDS ST STS instruction address
class GPIO(py4hw.Logic):
    def __init__(self,parent,name:str,memory:MemoryInterface):
        super().__init__(parent,name)

        self.interface = self.addInterfaceSink('port',memory)
        self.GPIOR2 = 0
        self.GPIOR2_addr_IO = 0x2B
        self.GPIOR2_addr_LS = 0x4B
        self.GPIOR1 = 0
        self.GPIOR1_addr_IO = 0x2A
        self.GPIOR1_addr_LS = 0x4A
        self.GPIOR0 = 0
        self.GPIOR0_addr_IO = 0x1E
        self.GPIOR0_addr_LS = 0x3E
        self.opp = 'none'
        self.addresGot = 0
        self.writeab = 0
        self.readab = 0
#       self.oppOut = py4hw.Wire(self,'oppOut',2)
#       self.addr=  py4hw.Wire(self,'addr',16)
#       self.stateB = py4hw.Wire(self,'stateB',1)
#       self.stateC = py4hw.Wire(self,'stateC',1)
#       self.stateD = py4hw.Wire(self,'stateD',1)
#       self.dataIN = py4hw.Wire(self,'dataIN',8)

        #self.PORTB =  PortX(self,'PORTB',0x05,0x25,0x04,0x24,0x03,0x23,self.oppOut,self.addr,self.dataIN,self.stateB)
        #self.PORTC =  PortX(self,'PORTC',0x08,0x28,0x07,0x27,0x06,0x26,self.oppOut,self.addr,self.dataIN,self.stateC)
        #self.PORTD =  PortX(self,'PORTD',0x0B,0x2B,0x0A,0x2A,0x09,0x29,self.oppOut,self.addr,self.dataIN,self.stateD)

#        def propagate(self):
#            if self.interface.address.get() == self.GPIOR2_addr_IO:
#                if self.interface.read.get() == 1:
#                   self.interface.read_data.put(self.GPIOR2)
#                elif self.interface.write.get() ==1:
#                    self.GPIOR2 = self.interface.write_data.get()
                

        def clock(self):
            self.addresGot = self.interface.address.get()
            self.writeab =  self.interface.write.get()
            self.readab =  self.interface.read.get()
            if self.interface.address.get() == self.GPIOR2_addr_IO:
                if self.interface.read.get() == 1:
                    self.interface.read_data.prepare(self.GPIOR2)
                elif self.interface.write.get() ==1:
                    self.GPIOR2 = self.interface.write_data.get()

#        def clock(self):
#            if self.interface.read.get() == 1:
#                 self.opp = 'read'
#            elif self.interface.write.get() == 1:
#                 self.opp = 'write'
#            else:
#                self.opp = 'none'
#                self.oppOut.oppOut(0)

#                addr =  self.interface.address.get()
#                match self.interface.address.get():
#                    case self.GPIOR2_addr_IO | self.GPIOR2_addr_LS:
#                        match self.opp:
#                            case 'read':
#                                self.interface.read_data.prepare(self.GPIOR2)
#                            case 'write':
#                                self.PORTX = self.interface.write_data.get()
#
#                    case self.GPIOR1_addr_IO | self.GPIOR1_addr_LS:
#                        match self.opp:
#                            case 'read':
#                                self.interface.read_data.prepare(self.GPIOR1)
#                            case 'write':
#                                self.PORTX = self.dataIN.get()
#                    case self.GPIOR0_addr_IO | self.GPIOR0_addr_LS:
#                        match self.opp:
#                            case 'read':
#                                self.interface.read_data.prepare(self.GPIOR0)
#                            case 'write':
#                                self.PORTX = self.interface.write_data.get()
#                    case _:
#                        print("ohlolo")
#                        match self.opp:
#                            case 'read':
#                                self.oppOut.prepare(2)
#                            case 'write':
#                                self.oppOut.prepare(1)
#                               self.dataIN.prepare(self.interface.write_data.get())
                     


class PortX(py4hw.Logic):
    def __init__(self,parent,name:str,PORT_IO_addr,PORT_LS_addr,DDRX_IO_addr,DDRX_LS_addr,PINX_IO_addr,PINX_LS_addr,opp,addr,dataIN,state):
        super().__init__(parent,name)

        #Port data register
        self.PORTX = 0
        self.PORTX_addr_IO = PORT_IO_addr
        self.PORTX_addr_LS = PORT_LS_addr

        #Port data direction register
        self.DDRX = 0
        self.DDRX_addr_IO = DDRX_IO_addr
        self.DDRX_addr_LS = DDRX_LS_addr

        #Port input pins address
        self.PINX = 0
        self.PINX_addr_IO = PINX_IO_addr
        self.PINX_addr_LS = PINX_LS_addr

        #IO
        self.opp = self.addIn('opp',opp)
        self.addr = self.addIn('addr',addr)
        self.dataIN = self.addIn('dataIn',dataIN)
        self.state = self.addOut('state',state)
        #read 2
        #write 1
        #none 0

        def clock(self):
                
                match self.addr.get():
                    case self.PORTX_addr_IO | self.PORTX_addr_LS: 
                        match self.opp.get():
                            case 2:
                                self.state.prepare(1)
                            case 1:
                                self.PORTX = self.dataIN.get()
                                self.state.prepare(1)

                    case self.DDRX_addr_IO | self.DDRX_addr_LS :
                        match self.opp.get():
                            case 2:
                                self.state.prepare(1)
                            case 1:
                                self.DDRX = self.dataIN.get()
                                self.state.prepare(1)

                    case self.PINX_addr_IO | self.PINX_addr_LS :
                        match self.opp.get():
                            case 2:
                                self.state.prepare(1)
                            case 1:
                                self.PINX = self.dataIN.get()
                                self.state.prepare(1)
                    case _:
                        self.state.prepare(0)
            
        