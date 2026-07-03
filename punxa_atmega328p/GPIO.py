import py4hw
from punxa_atmega328p.Memory import * 
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import Simulator
import py4hw.debug

## *_IO = IN and OUT instruction address
## *_LS =  LD LDS ST STS instruction address

#        An implementation idea but did not find a way to make it work
        #IO
#        self.RW = py4hw.Wire(self,'RW',1) # 0 read 1 write
#        self.OUTTB = py4hw.Wire(self,'OUTTB',8)
#        self.OUTTC = py4hw.Wire(self,'OUTTC',8)
#        self.OUTTD = py4hw.Wire(self,'OUTTD',8) 
#        self.INN =  py4hw.Wire(self,'INN',8)
#        self.ADDR =  py4hw.Wire(self,'addr',16)
#        self.READYB = py4hw.Wire(self,'READYB',1)
#        self.READYC = py4hw.Wire(self,'READYC',1)
#        self.READYD = py4hw.Wire(self,'READYD',1)
#        self.PORTB =  PortX(self,'PORTB',0x05,0x25,0x04,0x24,0x03,0x23,self.RW,self.ADDR,self.INN,self.OUTTB,self.READYB)
#        self.PORTC =  PortX(self,'PORTC',0x08,0x28,0x07,0x27,0x06,0x26,self.RW,self.ADDR,self.INN,self.OUTTC,self.READYC)
#        self.PORTD =  PortX(self,'PORTD',0x0B,0x2B,0x0A,0x2A,0x09,0x29,self.RW,self.ADDR,self.INN,self.OUTTD,self.READYD)
#        self.PORT = []
#        self.PORT.append(self.PORTB)
#        self.PORT.append(self.PORTC)
#        self.PORT.append(self.PORTD)

#INSTYPE 0 for IO | 1 for LS
class GPIO(py4hw.Logic):
    def __init__(self,parent,name:str,memory:MemoryInterface):
        super().__init__(parent,name)

        self.interface = self.addInterfaceSink('port',memory)
        #GENERAL GPIOR ADDRESSES 
        self.GPIOR2 = 0
        self.GPIOR2_addr_IO = 0x2B
        self.GPIOR2_addr_LS = 0x4B
        self.GPIOR1 = 0
        self.GPIOR1_addr_IO = 0x2A
        self.GPIOR1_addr_LS = 0x4A
        self.GPIOR0 = 0
        self.GPIOR0_addr_IO = 0x1E
        self.GPIOR0_addr_LS = 0x3E
        #PORTB 
        #Port data register
        self.PORTB = 0
        self.PORTB_addr_IO = 0x5
        self.PORTB_addr_LS = 0x25
        #Port data direction register
        self.DDRB = 0
        self.DDRB_addr_IO = 0x4
        self.DDRB_addr_LS = 0x24
        #Port input pins address
        self.PINB = 0
        self.PINB_addr_IO = 0x3
        self.PINB_addr_LS = 0x23
        #PORTC
        #Port data register
        self.PORTC = 0
        self.PORTC_addr_IO = 0x8
        self.PORTC_addr_LS = 0x28
        #Port data direction register
        self.DDRC = 0
        self.DDRC_addr_IO = 0x7
        self.DDRC_addr_LS = 0x27
        #Port input pins address
        self.PINC = 0
        self.PINC_addr_IO = 0x6
        self.PINC_addr_LS = 0x26 
        #PORTD
        #Port data register
        self.PORTD = 0
        self.PORTD_addr_IO = 0xB
        self.PORTD_addr_LS = 0x2B
        #Port data direction register
        self.DDRD = 0
        self.DDRD_addr_IO = 0xA
        self.DDRD_addr_LS = 0x2A
        #Port input pins address
        self.PIND = 0
        self.PIND_addr_IO = 0x9
        self.PIND_addr_LS = 0x29
        self.ADDR = 0
        #Interrupts

    def clock(self):
        self.ADDR = self.interface.address.get()
        if ((self.ADDR == self.GPIOR2_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.GPIOR2_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.GPIOR2)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.GPIOR2 = self.interface.write_data.get()
                self.interface.resp.prepare(0)
            else:
                self.interface.resp.prepare(1)
        elif ((self.ADDR == self.GPIOR1_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.GPIOR1_addr_LS)and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.GPIOR1)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.GPIOR1 = self.interface.write_data.get()
                self.interface.resp.prepare(0)
            else:
                self.interface.resp.prepare(1)
        elif ((self.ADDR == self.GPIOR0_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.GPIOR0_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):
                self.interface.read_data.prepare(self.GPIOR0)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1):
                self.GPIOR0 = self.interface.write_data.get()
            else:
                self.interface.resp.prepare(1)   
        elif ((self.ADDR == self.PORTB_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PORTB_addr_LS) and self.interface.instype.get() == 1): #PORTB
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.PORTB)
                self.interface.resp.prepare(0)

            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PORTB = self.interface.write_data.get()
                self.interface.resp.prepare(0)
            else:
                self.interface.resp.prepare(1)
        elif ((self.ADDR == self.DDRB_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.DDRB_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.DDRB)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1):  #write
                self.DDRB = self.interface.write_data.get()
                self.interface.resp.prepare(0)
            else:
                self.interface.resp.prepare(1)
        elif ((self.ADDR == self.PINB_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PINB_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0): #read
                self.interface.read_data.prepare(self.PINB)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PINB = self.interface.write_data.get()
            else:
                self.interface.resp.prepare(1)  
        elif ((self.ADDR == self.PORTC_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PORTC_addr_LS) and self.interface.instype.get() == 1): #PORTC
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.PORTC)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PORTC = self.interface.write_data.get()
            else:
                self.interface.resp.prepare(1)
        elif ((self.ADDR == self.DDRC_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.DDRC_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.DDRC)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1):  #write
                self.DDRC = self.interface.write_data.get()
            else:
                self.interface.resp.prepare(1)
        elif ((self.ADDR == self.PINC_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PINC_addr_LS) and self.interface.instype.get() == 1):   #PORTD
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0): #read
                self.interface.read_data.prepare(self.PINC)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PINC = self.interface.write_data.get()
            else:
                self.interface.resp.prepare(1)        
        elif ((self.ADDR == self.PORTD_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PORTD_addr_LS) and self.interface.instype.get() == 1): 
            print("test1")
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.PORTD)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PORTD = self.interface.write_data.get()
            else:
                self.interface.resp.prepare(1)
        elif ((self.ADDR == self.DDRD_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.DDRD_addr_LS) and self.interface.instype.get() == 1):
            print("test2")
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.DDRD)
                self.interface.resp.prepare(0)
            elif ((self.interface.read.get() == 0) and self.interface.instype.get() == 0) and ((self.interface.write.get() == 1) and self.interface.instype.get() == 1):  #write
                self.DDRD = self.interface.write_data.get()
            else:
                self.interface.resp.prepare(1)
        elif ((self.ADDR == self.PIND_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PIND_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0): #read
                self.interface.read_data.prepare(self.PIND)
                self.interface.resp.prepare(0)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PIND = self.interface.write_data.get()
            else:
                self.interface.resp.prepare(1)
        else:
                self.interface.resp.prepare(1)                

#print("else")
#        else:
#            for port in self.PORT:
#                if (self.interface.address.get() == port.PORTX_addr_IO) or (self.interface.address.get() == port.PORTX_addr_LS):
#                    if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
#                        self.interface.read_data.prepare(port.PORTX)
#                    elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
#                        port.PORTX = self.interface.write_data.get()#
#
#                elif (self.interface.address.get() == port.DDRX_addr_IO) or (self.interface.address.get() == port.DDRX_addr_LS):
#                    if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
#                        self.interface.read_data.prepare(port.DDRX)
#                    elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
#                        port.DDRX = self.interface.write_data.get()
#
#                elif (self.interface.address.get() == port.PINX_addr_IO) or (self.interface.address.get() == port.PINX_addr_LS):
#                    if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):
#                        self.interface.read_data.prepare(port.PINX)
#                    elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1):
#                        port.PINX = self.interface.write_data.get()

                     

# This is my original Idea for port implementation but I dont know why it does not work 
class PortX(py4hw.Logic):
    def __init__(self,parent,name:str,PORT_IO_addr,PORT_LS_addr,DDRX_IO_addr,DDRX_LS_addr,PINX_IO_addr,PINX_LS_addr,RW,ADDR,INN,OUTT,READY):
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
        self.RW = self.addIn('RW',RW)
        self.ADDR = self.addIn('ADDR',ADDR)
        self.INN = self.addIn('INN',INN)
        self.OUTT = self.addOut('OUTT',OUTT)
        self.READY = self.addOut('READY',READY)

        #none 0

#def clock(self):
    def propagate(self):               
        if (self.ADDR.get() == self.PORTX_addr_IO) or (self.ADDR.get() == self.PORTX_addr_LS):
            if (self.RW.get() == 1) and (self.RW.get() == 0):  #read
                self.OUTT.put(self.PORTX)
                self.READY.put(1)
            elif (self.RW.get() == 0) and (self.RW.get() == 1): #write
                self.PORTX = self.INN.get()
                        
        elif (self.ADDR.get() == self.DDRX_addr_IO) or (self.ADDR.get() == self.DDRX_addr_LS):
                if (self.RW.get() == 1) and (self.RW.get() == 0):  #read
                    self.OUTT.put(self.DDRX)
                    self.READY.put(1)
                elif (self.RW.get() == 0) and (self.RW.get() == 1):  #write
                    self.DDRX = self.INN.get()

        elif (self.ADDR.get() == self.PINX_addr_IO) or (self.ADDR.get() == self.PINX_addr_LS):
                if (self.RW.get() == 1) and (self.RW.get() == 0): #read
                    self.OUTT.put(self.PINX)
                    self.READY.put(1)
                elif (self.RW.get() == 0) and (self.RW.get() == 1): #write
                    self.PINX = self.INN.get()
        else:
            self.READY.put(0)  
        



class VirtualGPIO(py4hw.Logic):
    def __init__(self, parent, name: str, memory: MemoryInterface):
        super().__init__(parent, name)
        self.interface = self.addInterfaceSink('port', memory)

        # PORTB group
        self.port_b = 0
        self.ddr_b = 0

        # PORTC group
        self.port_c = 0
        self.ddr_c = 0

        # General purpose I/O registers
        self.gpior0 = 0
        self.gpior1 = 0

        # address -> (name, kind, group)
        # kind: 'pin' / 'port' / 'ddr' / 'gpior'
        self.add_map = {
            0x03: ('PINB',  'pin',  'b'),
            0x04: ('DDRB',  'ddr',  'b'),
            0x05: ('PORTB', 'port', 'b'),
            0x06: ('PINC',  'pin',  'c'),
            0x07: ('DDRC',  'ddr',  'c'),
            0x08: ('PORTC', 'port', 'c'),
            0x1A: ('GPIOR1', 'gpior', 'gpior1'),
            0x1E: ('GPIOR0', 'gpior', 'gpior0'),
        }

    def _read_value(self, kind, group):
        if kind == 'ddr':
            return self.ddr_b if group == 'b' else self.ddr_c
        if kind in ('port', 'pin'):
            return self.port_b if group == 'b' else self.port_c
        if kind == 'gpior':
            return self.gpior0 if group == 'gpior0' else self.gpior1
        return 0

    def clock(self):
        add = self.interface.address.get()
        v = self.interface.write_data.get()

        entry = self.add_map.get(add)
        name = entry[0] if entry else f'0x{add:02X}'

        if self.interface.read.get():
            if entry is None:
                self.interface.resp.prepare(0)
                return
            _, kind, group = entry
            value = self._read_value(kind, group)
            self.interface.read_data.prepare(value)
            print(f'Reading GPIO {name} = {self.interface.read_data.next:02X}')
            self.interface.resp.prepare(1)

        elif self.interface.write.get():
            if entry is None:
                self.interface.resp.prepare(0)
                return
            _, kind, group = entry

            if kind == 'pin':
                # PIN registers are read-only on real hardware; ignore writes
                print(f'Ignoring write to read-only {name}={v:02X}')
                self.interface.resp.prepare(1)
                return

            print(f'Writing GPIO {name}={v:02X}')
            if kind == 'ddr':
                if group == 'b':
                    self.ddr_b = v
                else:
                    self.ddr_c = v
            elif kind == 'port':
                if group == 'b':
                    self.port_b = v
                else:
                    self.port_c = v
            elif kind == 'gpior':
                if group == 'gpior0':
                    self.gpior0 = v
                else:
                    self.gpior1 = v

            self.interface.resp.prepare(1)
        else:
            self.interface.resp.prepare(0)