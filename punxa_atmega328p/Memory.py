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
        self.instype = self.addSourceToSink("instype",1)

        if((data_width % 8) != 0):
            raise Exception('data_width must be multiple of byte,{} not supported').format(data_width)
        
        #self.be = self.addSourceToSink('be', data_width // 8) #nb of bytes does not make sense because the registers of the mcu are 8 bit8 
        self.resp = self.addSinkToSource('resp',1)# 0 = normal state, 1 = Operation Performed


class Ram_Memory(Logic):
    def __init__(self, parent:Logic, name:str, dw:int, aw:int, port:MemoryInterface):
        super().__init__(parent, name)

        
        self.port = self.addInterfaceSink('port', port)
        
        self.data = [0]*(1<<aw)

    def clock(self):
        add = self.port.address.get()

        # ensure that no simultaneous read and write operations are done
        assert not((self.port.read.get() == 1) and (self.port.write.get() == 1))
        
        if (self.port.write.get() == 1):
            self.data[add] = self.port.write_data.get()
            #assert isinstance (add.int)
            self.port.resp.prepare(1)
        elif (self.port.read.get() == 1):
            self.port.read_data.prepare(self.data[add])
            self.port.resp.prepare(1)
        else:
            self.port.resp.prepare(0)
            
    def writeWord(self, address, value):
        self.data[address] = value 
        
    def readWord(self, address):
        return self.data[address] 

    def on_button_click(self):
        pass
    
    def tkinter_gui(self, parent):
        from tkinter import ttk
        import tkinter as tk
        
        #print('parent',  type(parent))
        frame = ttk.Frame(parent, padding="10")
        #frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        #parent.add(frame)

        # Create Treeview with five columns
        columns = ("address", "3", "2", "1", "0")
        tree = ttk.Treeview(frame, columns=columns, show="headings")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        # Add headings to the columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=100)  # Adjust width as needed

        # Insert sample data into the treeview
        for i in range(len(self.data)):
            v = self.data[i]
            
            #print('value', i, '=', v)
            
            b0 = v & 0xFF
            v = v >> 8
            b1 = v & 0xFF
            v = v >> 8
            b2 = v & 0xFF
            v = v >> 8
            b3 = v & 0xFF
            
            tree.insert("", "end", values=("{:08X}".format(i), '{:02X}'.format(b3), '{:02X}'.format(b2), '{:02X}'.format(b1), '{:02X}'.format(b0)))

        # Create label, entry box, and button
        label = ttk.Label(frame, text="Selected Item:")
        edit_box = ttk.Entry(frame)
        button = ttk.Button(frame, text="Update", command=self.on_button_click)

        # Grid layout for Treeview
        tree.grid(column=0, row=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        vsb.grid(column=3, row=0,  sticky="ns")

        # Grid layout for label, entry box, and button
        label.grid(column=0, row=1, padx=10, pady=5, sticky="w")
        edit_box.grid(column=1, row=1, padx=10, pady=5, sticky="ew")
        button.grid(column=2, row=1, padx=10, pady=5, sticky="e")

        # Configure row and column weights for expanding
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        return frame
    

class EEPROM_Memory(Logic):
    def __init__(self, parent:Logic, name:str, data_width:int, address_width:int, port:MemoryInterface,EERI):
        super().__init__(parent,name)
        
        self.port0 = self.addInterfaceSink('port',port)
        self.startAddress = 0x000
        self.stopAddress = 0x3FF
        self.values = [0]*(self.stopAddress-self.startAddress)

        self.EERI = py4hw.addOut('EERI',EERI)


        self.EEARH = 0
        self.EEARH_addr_IO = 0x22
        self.EEARH_addr_LS = 0x42


        self.EEARL = 0
        self.EEARL_addr_IO = 0x21 
        self.EEARL_addr_LS = 0x41


        self.EEDR = 0
        self.EEDR_addr_IO = 0x20
        self.EEDR_addr_LS = 0x40


        self.EECR = 0
        self.EECR_addr_IO = 0x1F
        self.EECR_addr_LS = 0x3F

        self.ADDR = 0



    def clock(self):

        self.ADDR = self.port0.address.get()
        if ((self.ADDR == self.EEARH_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.EEARH_addr_LS) and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.EEARH)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.EEARH = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.EEARL_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.EEARL_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.EEARL)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.EEARL = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        elif ((self.ADDR == self.EEDR_addr_IO) and self.port0.instype.get() == 0) or ((self.ADDR == self.EECR_addr_LS)and self.port0.instype.get() == 1):
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):  #read
                self.port0.read_data.prepare(self.EEDR)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1): #write
                self.EEDR = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)

        address = ((self.EEARH<<8)&0b1)|(self.EEARL)

        #EEPROM Control Register

        EEPM = ((self.EECR>>4) & 3)
        EERIE =  ((self.EECR>>3) & 1)
        EEMPE = ((self.EECR>>2) & 1 )
        EEPE = ((self.EECR>>1) & 1)
        EERE = (self.EECR & 1)

        if (address >= self.startAddress) and (address <= self.stopAddress):

            
            
            print("opperation")
            #print((self.port0.read.get() == 1) and (self.port0.write.get() == 0))
            #print((self.port0.read.get() == 1) and (self.port0.write.get() == 1))

            if EEPM == 1:
                self.port0.read_data.prepare(self.values[address])
                self.port0.resp.prepare(1)
                #print('reading address ', address, '=', self.values[address])


            elif EEPM == 2:
                self.values[address] = self.port0.write_data.get()
                self.port0.resp.prepare(1)
                #print('writing address ', address, '=', self.values[address])
                
            elif EEPM == 0:
                self.port0.read_data.preapre(self.values[address])
                self.values[address] = self.port0.write_data.get()
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        else:
            self.port0.resp.prepare(0)
            





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


class StackPointer(py4hw.Logic):
    """
    A dedicated memory-mapped component to store the Stack Pointer (SP).
    In the ATmega328P, SPL is at I/O address 0x3D (SRAM address 0x5D)
    and SPH is at I/O address 0x3E (SRAM address 0x5E).
    """
    def __init__(self, parent: py4hw.Logic, name: str, port: MemoryInterface):
        super().__init__(parent, name)
        
        self.port = self.addInterfaceSink('port', port)
        
        # Internal registers for SPL and SPH
        self.SPL = 0
        self.SPH = 0

    def clock(self):
        address = self.port.address.get()

        # Ensure no simultaneous read and write operations
        assert not((self.port.read.get() == 1) and (self.port.write.get() == 1))
        
        # Base addresses for SP in the ATmega328P SRAM map
        SPL_ADDR = 0x5D
        SPH_ADDR = 0x5E

        if self.port.write.get() == 1:
            write_data = self.port.write_data.get()
            if address == SPL_ADDR:
                self.SPL = write_data & 0xFF
                print(f"[{self.name}] WRITE SPL: {self.SPL:02X}")
            elif address == SPH_ADDR:
                self.SPH = write_data & 0xFF
                print(f"[{self.name}] WRITE SPH: {self.SPH:02X}")
                
            self.port.resp.prepare(1)

        elif self.port.read.get() == 1:
            if address == SPL_ADDR:
                self.port.read_data.prepare(self.SPL)
                print(f"[{self.name}] READ SPL: {self.SPL:02X}")
            elif address == SPH_ADDR:
                self.port.read_data.prepare(self.SPH)
                print(f"[{self.name}] READ SPH: {self.SPH:02X}")
            else:
                self.port.read_data.prepare(0) # Default if out of bounds
                
            self.port.resp.prepare(1)

        else:
            self.port.resp.prepare(0)
            
    # Helpers to view the full 16-bit SP value
    def get_sp(self):
        return (self.SPH << 8) | self.SPL