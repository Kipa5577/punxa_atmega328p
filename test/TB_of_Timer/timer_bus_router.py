# -*- coding: utf-8 -*-
"""
TimerBusRouter -- test-harness-only infrastructure (not part of the
punxa_atmega328p CPU package) that lets TimerCounter0, TimerCounter1, and
TimerCounter2 all sit on the real CPU's data bus at once.

Why this exists instead of three punxa.MultiplexedBus slave entries:
each TimerCounter's register addresses are absolute/real ATmega328P
addresses (TCCR0A=0x44, TCCR1A=0x80, TCCR2A=0xB0, ...), baked directly
into each class rather than being relative to wherever it's mapped --
same reason the old single-timer tb_timers.py had to give TimerCounter0 a
window spanning the *entire* 0x00-0xFF low+extended-I/O space rather than
a tight one. That's fine for exactly one such peripheral (see that file's
docstring: it relies on being listed first, with reg_p/sp_p/int_unit_p's
narrower windows listed after it so they win for their own addresses --
Bus.py's MultiplexedBus.propagate() has no `break` on match, so the
*last* listed slave whose range contains an address wins).

With three timers, that trick stops working: TimerCounter0/1/2's real
addresses are scattered across the same 0x00-0xFF span but don't overlap
*each other*, so no single ordering of three equally-wide, mutually
overlapping windows can make each timer win for its own addresses while
losing for the other two's. (Timer0 needs to win at 0x44-0x48/0x35/0x6E,
Timer1 at 0x80-0x8B/0x36/0x6F, Timer2 at 0xB0-0xB4/0x37/0x70 --
listing all three with identical 0x00-0xFF windows means whichever is
*last* in the list wins for literally every address, clobbering the
other two everywhere.)

This router sidesteps the problem entirely: it owns exactly one slot on
the real MultiplexedBus (a single wide window, still listed before
reg_p/sp_p/int_unit_p for the same reason the old harness needed that
ordering), and internally dispatches by *exact* address membership to
whichever of the three real TimerCounter sub-ports actually owns that
address -- mirroring each TimerCounter's own internal decode instead of
fighting it through range-based bus arbitration.
"""
import py4hw


class TimerBusRouter(py4hw.Logic):
    # Every real ATmega328P address each TimerCounter class recognizes
    # (see Timers.py's *_addr_LS constants). Kept here rather than
    # imported so this file has no dependency on internal attribute
    # names -- just the real hardware addresses, which are public and
    # stable across any future refactor of Timers.py.
    TIMER0_ADDRS = {0x35, 0x44, 0x45, 0x46, 0x47, 0x48, 0x6E}
    TIMER1_ADDRS = {0x36, 0x6F, 0x80, 0x81, 0x82, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B}
    TIMER2_ADDRS = {0x37, 0x70, 0xB0, 0xB1, 0xB2, 0xB3, 0xB4}

    def __init__(self, parent, name, master, timer0_port, timer1_port, timer2_port):
        super().__init__(parent, name)
        self.master = self.addInterfaceSink('master', master)
        self.t0 = self.addInterfaceSource('timer0', timer0_port)
        self.t1 = self.addInterfaceSource('timer1', timer1_port)
        self.t2 = self.addInterfaceSource('timer2', timer2_port)

    def propagate(self):
        addr = self.master.address.get()
        read = self.master.read.get()
        write = self.master.write.get()
        write_data = self.master.write_data.get()
        instype = self.master.instype.get()

        if addr in self.TIMER0_ADDRS:
            target = self.t0
        elif addr in self.TIMER1_ADDRS:
            target = self.t1
        elif addr in self.TIMER2_ADDRS:
            target = self.t2
        else:
            target = None

        for sub in (self.t0, self.t1, self.t2):
            if sub is target:
                sub.address.put(addr)
                sub.read.put(read)
                sub.write.put(write)
                sub.write_data.put(write_data)
                sub.instype.put(instype)
            else:
                sub.address.put(0)
                sub.read.put(0)
                sub.write.put(0)
                sub.write_data.put(0)
                sub.instype.put(instype)

        if target is not None:
            self.master.read_data.put(target.read_data.get())
            self.master.resp.put(target.resp.get())
        else:
            self.master.read_data.put(0)
            self.master.resp.put(0)
