import py4hw
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import Simulator
import py4hw.debug

class MultiplexedBus(Logic):
    def __init__(self,parent:Logic,name:str,master,slaves):
        super().__init__(parent,name)

        self.master = self.addInterfaceSink('master',master)

        self.slaves = []
        self.start = []
        self.stop = []

        for idx, slave in enumerate(slaves):
            port = slave[0]
            start = slave[1]
            size = (1 << port.address.getWidth())

            if(len(slave)>2):
                addressSize = size
                size = slave[2]

                if (size > addressSize):
                    print("WARNING: provided size bigger that address size")

            stop = start + size - 1
        
            self.slaves.append(port)
            self.start.append(start)
            self.stop.append(stop)

            self.addInterfaceSource('slave_{}'.format(idx),port)

    def propagate(self):
        addr = self.master.address.get()
        read = self.master.read.get()
        write =  self.master.write.get()
        #be = self.master.be.get()
        write_data = self.master.write_data.get()
        # FIX: instype was never forwarded to any slave at all -- every
        # slave's instype wire sat at its own default (0) forever,
        # regardless of what the master actually drove. Harmless for
        # peripherals that ignore instype (VirtualGPIO, SimpleTimer,
        # VirtualUSART -- the mocks the ISA suite wires up), but fatal for
        # any peripheral that gates its register decode on
        # instype.get() == 1 (the real GPIO/TimerCounter0/1/2/ADC classes,
        # all of which distinguish `_addr_IO` (instype=0) from `_addr_LS`
        # (instype=1) register addresses): resp never asserts, and the
        # CPU hangs forever waiting for a response that will never come.
        # Found while building tb_timer_tests.py's real-CPU Timer0/1/2
        # integration harness -- `sts TCCR0B, r16` hung indefinitely with
        # TimerCounter0's own instype input stuck at 0 every cycle, even
        # after MemoryInterfaceHandler.py was fixed to actually drive its
        # own instype *output* (a separate, equally-necessary fix -- that
        # one only fixed the master side of this bus; this is the slave
        # side).
        instype = self.master.instype.get()

        handled = False 

        
        for idx, slave in enumerate(self.slaves):
            start = self.start[idx]
            stop = self.stop[idx]

            if(addr >= start and addr <= stop):
                slave_addr = addr - start 
                slave.address.put(slave_addr)
                slave.read.put(read)
                slave.write.put(write)
                slave.write_data.put(write_data)
                slave.instype.put(instype)
                #slave.be.put(be)

                self.master.read_data.put(slave.read_data.get())
                self.master.resp.put(slave.resp.get())
                handled = True

            else:
                slave.address.put(0)
                slave.read.put(0)
                slave.write.put(0)
                slave.write_data.put(0)
                slave.instype.put(instype)
                #slave.be.put(0)
                    