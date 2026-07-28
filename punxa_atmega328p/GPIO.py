import py4hw
from punxa_atmega328p.Memory import * 
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import Simulator
import py4hw.debug

## *_IO = IN and OUT instruction address
## *_LS =  LD LDS ST STS instruction address

# NOTE on the commented-out PortX-based design directly below GPIO's class
# body (kept for history): that approach tried to drive per-port pin I/O
# through the standalone PortX component's own propagate()-based
# read/write decode wired to shared RW/ADDR/INN/OUTT busses -- it's not
# used. The real pin-level I/O added below (Round: GPIO pin-level pass)
# takes a simpler route: plain 8-bit val/oe/ext_in/ext_oe wires added
# directly on GPIO itself, computed once per clock() alongside the
# existing bus decode, no separate sub-component.

#INSTYPE 0 for IO | 1 for LS
class GPIO(py4hw.Logic):
    """
    Round (GPIO pin-level pass) -- two classes of bugs fixed relative to
    the version this replaced, plus real physical pin I/O added for the
    first time:

    1. **`resp` polarity was inverted on every read/write branch.** The
       project-wide convention (see Memory.py's own docstring: "resp: 0 =
       normal state, 1 = Operation Performed", and mirrored in the real
       Timers.py/TWI.py peripherals that already pass CPU integration)
       is resp=1 on a completed read or write, resp=0 otherwise. The
       version this replaced did the opposite on every register branch
       (resp=0 on success, resp=1 on the invalid/idle catch-all) --
       harmless only by accident, because GPIO was only ever driven
       through VirtualGPIO in every prior CPU-integration test
       (tb_usart.py's Round 8 swap to the real GPIO class happened to
       only exercise writes whose resp value was never actually
       checked). A real per-cycle busy-wait poll against this class as
       it stood would have hung or falsely completed immediately,
       depending on which branch it landed on.
    2. **Several write branches (GPIOR0, PINB, PORTC, DDRC, PINC, PORTD,
       PIND) never called `resp.prepare()` at all** on the write path --
       left the wire holding whatever the previous cycle prepared.
    3. **DDRD's write condition was unreachable dead code**: it required
       `instype.get() == 0 and instype.get() == 1` in the same boolean
       expression -- impossible, so `sts DDRD, r16` through the real CPU
       silently never updated DDRD (the write fell through to the
       invalid/idle branch instead). Confirmed nothing else in this
       project set DDRD any other way. This one bug alone would have
       made it impossible to ever configure PORTD as an output through
       the real CPU.
    4. **No physical pin I/O existed at all** -- PORTx/DDRx/PINx were
       plain Python ints toggled only by bus reads/writes; there was no
       wire an external peer could drive to emulate an input pin, and no
       wire reflecting what the chip actually drives out when a bit is
       configured as output. Added below: per port (B/C/D), a val/oe
       pair driven out (what this chip is putting on the pins) and an
       ext_in/ext_oe pair driven in (what the outside world is putting
       on the pins) -- the standard two-signal tri-state-emulation
       pattern for a non-electrical functional simulator, chosen over
       modeling analog floating voltages. See PIN_read semantics below.
    5. Two leftover debug `print("test1")`/`print("test2")` statements
       removed from the PORTD/DDRD branches.

    PIN register read semantics (per bit, computed once per clock()
    alongside the existing bus decode):

        DDR bit == 1 (output):  PIN bit = PORT bit
            (reading a pin configured as output reads back the driven
            level, matching real AVR behavior)
        DDR bit == 0 (input):
            ext_oe bit == 1 (peer actively driving this bit): PIN bit = ext_in bit
            ext_oe bit == 0 (floating): PIN bit = PORT bit
                (this is the internal pull-up: PORT=1 with DDR=0 pulls
                the floating pin to 1; PORT=0 with DDR=0 reads 0 with
                no pull-up -- exactly AVR's documented DDRx=0/PORTx=1
                pull-up-enable behavior, without needing to model an
                analog floating voltage)

    Output pins (`<P>_val`/`<P>_oe`, driven out every cycle):
        val = PORTx, oe = DDRx -- a peer wanting to know what's actually
        being driven checks oe first (1 = this chip is driving that bit,
        so val is meaningful) before trusting val.

    All four pin wires per port are optional constructor kwargs
    (default None -> an internally-created, unconnected dummy wire) so
    any existing or future bus-only instantiation of GPIO (e.g. a future
    top-level integration that doesn't need pin-level testing) keeps
    working unchanged.
    """
    def __init__(self, parent, name: str, memory: MemoryInterface,
                 PORTB_val=None, PORTB_oe=None, PORTB_ext_in=None, PORTB_ext_oe=None,
                 PORTC_val=None, PORTC_oe=None, PORTC_ext_in=None, PORTC_ext_oe=None,
                 PORTD_val=None, PORTD_oe=None, PORTD_ext_in=None, PORTD_ext_oe=None):
        super().__init__(parent, name)

        self.interface = self.addInterfaceSink('port', memory)

        def _out(w, nm):
            if w is None:
                w = py4hw.Wire(self, nm, 8)
            return self.addOut(nm, w)

        def _in(w, nm):
            if w is None:
                w = py4hw.Wire(self, nm, 8)
                w.put(0)
            return self.addIn(nm, w)

        # --- Physical pin ports (see class docstring for semantics) ---
        self.PORTB_val = _out(PORTB_val, 'PORTB_val')
        self.PORTB_oe = _out(PORTB_oe, 'PORTB_oe')
        self.PORTB_ext_in = _in(PORTB_ext_in, 'PORTB_ext_in')
        self.PORTB_ext_oe = _in(PORTB_ext_oe, 'PORTB_ext_oe')

        self.PORTC_val = _out(PORTC_val, 'PORTC_val')
        self.PORTC_oe = _out(PORTC_oe, 'PORTC_oe')
        self.PORTC_ext_in = _in(PORTC_ext_in, 'PORTC_ext_in')
        self.PORTC_ext_oe = _in(PORTC_ext_oe, 'PORTC_ext_oe')

        self.PORTD_val = _out(PORTD_val, 'PORTD_val')
        self.PORTD_oe = _out(PORTD_oe, 'PORTD_oe')
        self.PORTD_ext_in = _in(PORTD_ext_in, 'PORTD_ext_in')
        self.PORTD_ext_oe = _in(PORTD_ext_oe, 'PORTD_ext_oe')

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

    def _update_pins(self):
        """Physical pin computation -- runs every clock() regardless of
        whether this cycle's bus access targets GPIO at all, same as a
        real chip's pins are always live. See class docstring for the
        PIN-read / pull-up semantics this implements."""
        ext_in_b = self.PORTB_ext_in.get()
        ext_oe_b = self.PORTB_ext_oe.get()
        self.PINB = ((self.DDRB & self.PORTB) |
                     (~self.DDRB & ((ext_oe_b & ext_in_b) | (~ext_oe_b & self.PORTB)))) & 0xFF
        self.PORTB_val.prepare(self.PORTB)
        self.PORTB_oe.prepare(self.DDRB)

        ext_in_c = self.PORTC_ext_in.get()
        ext_oe_c = self.PORTC_ext_oe.get()
        self.PINC = ((self.DDRC & self.PORTC) |
                     (~self.DDRC & ((ext_oe_c & ext_in_c) | (~ext_oe_c & self.PORTC)))) & 0xFF
        self.PORTC_val.prepare(self.PORTC)
        self.PORTC_oe.prepare(self.DDRC)

        ext_in_d = self.PORTD_ext_in.get()
        ext_oe_d = self.PORTD_ext_oe.get()
        self.PIND = ((self.DDRD & self.PORTD) |
                     (~self.DDRD & ((ext_oe_d & ext_in_d) | (~ext_oe_d & self.PORTD)))) & 0xFF
        self.PORTD_val.prepare(self.PORTD)
        self.PORTD_oe.prepare(self.DDRD)

    def clock(self):
        self._update_pins()
        self.ADDR = self.interface.address.get()
        if ((self.ADDR == self.GPIOR2_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.GPIOR2_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.GPIOR2)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.GPIOR2 = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.GPIOR1_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.GPIOR1_addr_LS)and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.GPIOR1)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.GPIOR1 = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.GPIOR0_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.GPIOR0_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):
                self.interface.read_data.prepare(self.GPIOR0)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1):
                self.GPIOR0 = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.PORTB_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PORTB_addr_LS) and self.interface.instype.get() == 1): #PORTB
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.PORTB)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PORTB = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.DDRB_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.DDRB_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.DDRB)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1):  #write
                self.DDRB = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.PINB_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PINB_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0): #read
                self.interface.read_data.prepare(self.PINB)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                # Real AVR quirk: writing PINx toggles the corresponding
                # PORTx bits rather than storing into PINx (PINx is
                # read-only as far as its own storage goes). Not yet
                # implemented -- see HANDOFF.md open items. Left as a
                # plain (non-functional-effect) ack for now so a test
                # that writes PINx doesn't hang, matching this file's
                # prior behavior of accepting but not using the value.
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.PORTC_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PORTC_addr_LS) and self.interface.instype.get() == 1): #PORTC
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.PORTC)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PORTC = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.DDRC_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.DDRC_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.DDRC)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1):  #write
                self.DDRC = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.PINC_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PINC_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0): #read
                self.interface.read_data.prepare(self.PINC)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.PORTD_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PORTD_addr_LS) and self.interface.instype.get() == 1): 
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.PORTD)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.PORTD = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.DDRD_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.DDRD_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0):  #read
                self.interface.read_data.prepare(self.DDRD)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1):  #write
                self.DDRD = self.interface.write_data.get()
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        elif ((self.ADDR == self.PIND_addr_IO) and self.interface.instype.get() == 0) or ((self.ADDR == self.PIND_addr_LS) and self.interface.instype.get() == 1):
            if (self.interface.read.get() == 1) and (self.interface.write.get() == 0): #read
                self.interface.read_data.prepare(self.PIND)
                self.interface.resp.prepare(1)
            elif (self.interface.read.get() == 0) and (self.interface.write.get() == 1): #write
                self.interface.resp.prepare(1)
            else:
                self.interface.resp.prepare(0)
        else:
                self.interface.resp.prepare(0)


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
        # The MultiplexedBus already stripped the 0x20 offset!
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