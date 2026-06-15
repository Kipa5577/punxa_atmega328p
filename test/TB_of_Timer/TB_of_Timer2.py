# -*- coding: utf-8 -*-
"""
MemoryInterfaceHandler - py4hw Behavioural Sequential implementation
inspired by the punxa_atmega328p coding style.

MemoryInterface convention (matching punxa):
    sourceToSink:  address (aw), write (1), data_in (dw)   CPU → Memory
    sinkToSource:  data_out (dw)                            Memory → CPU

addInterfaceSource → this component DRIVES the interface  (CPU side)
addInterfaceSink   → this component RECEIVES the interface (Memory side)
"""

import py4hw


# ---------------------------------------------------------------------------
# MemoryInterface definition  (mirrors punxa_atmega328p.MemoryInterface)
# ---------------------------------------------------------------------------
class MemoryInterface(py4hw.Interface):
    """
    Standard bus interface between a master (CPU) and a slave (Memory).

        sourceToSink  (master → slave):
            address   : aw bits
            write     :  1 bit   (1 = write, 0 = read)
            data_in   : dw bits  (data from master to slave)

        sinkToSource  (slave → master):
            data_out  : dw bits  (data from slave to master)
    """
    def __init__(self, parent: py4hw.Logic, name: str, dw: int, aw: int):
        super().__init__(parent, name)
        self.address  = self.addSourceToSink('address', aw)
        self.write    = self.addSourceToSink('write',    1)
        self.data_in  = self.addSourceToSink('data_in', dw)
        self.data_out = self.addSinkToSource('data_out', dw)


# ---------------------------------------------------------------------------
# MemoryInterfaceHandler  –  Behavioural Sequential
# ---------------------------------------------------------------------------
class MemoryInterfaceHandler(py4hw.Logic):
    """
    Behavioural Sequential register file and memory interface handler.

    Acts as the MASTER on the memory interface:
      • Drives  address / write / data_in  (addInterfaceSource)
      • Reads   data_out                   (addInterfaceSource → inPort)

    Internal registers (plain Python ints, updated each clock()):
        _SPH, _SPL      Stack Pointer High / Low  (8-bit each)
        _XH,  _XL       X index register pair     (8-bit each)
        _YH,  _YL       Y index register pair     (8-bit each)
        _ZH,  _ZL       Z index register pair     (8-bit each)
        _RomAddrReg     ROM address latch          (16-bit)
        _MemDatabus     Memory data latch          (8-bit)

    Ports:
        reset           1-bit   synchronous reset (active high)
        WE              1-bit   master write-enable for register file
        LoadSelectMux   4-bit   destination register select (0-7)
        LoadingMux      3-bit   data source select (0-7)
        IncDec          1-bit   0=SP+1 (pop), 1=SP-1 (push)
        ReadWrite       2-bit   [0]=latch from bus  [1]=drive bus output
        InputSelect     2-bit   data-bus input source (0-3)
        Mem_instruction 4-bit   address-mux select (0-8)
        RomAddress      16-bit  address from ROM controller
        DataBusInput    8-bit   data arriving from external memory
        ResL            8-bit   ALU result low byte
        ResH            8-bit   ALU result high byte
        GeneralInput    8-bit   general purpose input
        RegisterOut     8-bit   MemDatabus read output

    LoadSelectMux encoding:  0=SPH 1=SPL 2=XH 3=XL 4=YH 5=YL 6=ZH 7=ZL

    LoadingMux encoding:
        0=ResL  1=ResH  2=GeneralInput  3=DataBusInput
        4=SP_next_low  5=SP_next_high  6=RomAddr_low  7=RomAddr_high

    Mem_instruction (address mux) encoding:
        0=X  1=X+1  2=Y  3=Y+1  4=Z  5=Z+1  6=SP  7=SP+1  8=RomAddrReg

    InputSelect encoding:
        0=DataBusInput  1=ResL  2=ResH  3=GeneralInput
    """

    def __init__(
        self,
        parent: py4hw.Logic,
        name: str,
        # control inputs
        reset,
        WE,
        LoadSelectMux,
        LoadingMux,
        IncDec,
        ReadWrite,
        InputSelect,
        Mem_instruction,
        RomAddress,
        # data inputs
        DataBusInput,
        ResL,
        ResH,
        GeneralInput,
        # memory interface  (this component is the master / source)
        memory: MemoryInterface,
        # output
        RegisterOut,
    ):
        super().__init__(parent, name)

        # ---- scalar ports ------------------------------------------------
        self._reset           = self.addIn('reset',           reset)
        self._WE              = self.addIn('WE',              WE)
        self._LoadSelectMux   = self.addIn('LoadSelectMux',   LoadSelectMux)
        self._LoadingMux      = self.addIn('LoadingMux',      LoadingMux)
        self._IncDec          = self.addIn('IncDec',          IncDec)
        self._ReadWrite       = self.addIn('ReadWrite',       ReadWrite)
        self._InputSelect     = self.addIn('InputSelect',     InputSelect)
        self._Mem_instruction = self.addIn('Mem_instruction', Mem_instruction)
        self._RomAddress      = self.addIn('RomAddress',      RomAddress)
        self._DataBusInput    = self.addIn('DataBusInput',    DataBusInput)
        self._ResL            = self.addIn('ResL',            ResL)
        self._ResH            = self.addIn('ResH',            ResH)
        self._GeneralInput    = self.addIn('GeneralInput',    GeneralInput)
        self._RegisterOut     = self.addOut('RegisterOut',    RegisterOut)

        # ---- memory interface (master side) ------------------------------
        # addInterfaceSource: sourceToSink wires become OutPorts (we drive them)
        #                     sinkToSource wires become InPorts  (we read them)
        self._mem = self.addInterfaceSource('memory', memory)

        # Convenient aliases to the interface wires
        self._mem_address  = memory.address   # out: address we put on the bus
        self._mem_write    = memory.write     # out: write-enable to memory
        self._mem_data_in  = memory.data_in   # out: data we write to memory
        self._mem_data_out = memory.data_out  # in:  data memory returns to us

        # ---- internal register file state --------------------------------
        self._SPH        = 0
        self._SPL        = 0
        self._XH         = 0
        self._XL         = 0
        self._YH         = 0
        self._YL         = 0
        self._ZH         = 0
        self._ZL         = 0
        self._RomAddrReg = 0
        self._MemDatabus = 0

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------
    def _sp(self):
        return ((self._SPH & 0xFF) << 8) | (self._SPL & 0xFF)

    def _x(self):
        return ((self._XH & 0xFF) << 8) | (self._XL & 0xFF)

    def _y(self):
        return ((self._YH & 0xFF) << 8) | (self._YL & 0xFF)

    def _z(self):
        return ((self._ZH & 0xFF) << 8) | (self._ZL & 0xFF)

    def _sp_next(self):
        """SP ± 1:  IncDec=0 → SP+1 (pop),  IncDec=1 → SP-1 (push)."""
        if self._IncDec.get():
            return (self._sp() - 1) & 0xFFFF
        return (self._sp() + 1) & 0xFFFF

    def _loading_mux(self):
        """Return the 8-bit value selected by LoadingMux."""
        sel     = self._LoadingMux.get() & 0x7
        sp_next = self._sp_next()
        rom     = self._RomAddress.get() & 0xFFFF
        sources = [
            self._ResL.get()         & 0xFF,   # 0 – ResL
            self._ResH.get()         & 0xFF,   # 1 – ResH
            self._GeneralInput.get() & 0xFF,   # 2 – GeneralInput
            self._DataBusInput.get() & 0xFF,   # 3 – DataBusInput
            sp_next         & 0xFF,            # 4 – SP_next low
            (sp_next >> 8)  & 0xFF,            # 5 – SP_next high
            rom             & 0xFF,            # 6 – RomAddr low
            (rom >> 8)      & 0xFF,            # 7 – RomAddr high
        ]
        return sources[sel]

    def _addr_mux(self):
        """Return the 16-bit address selected by Mem_instruction."""
        sel = self._Mem_instruction.get() & 0xF
        x, y, z, sp = self._x(), self._y(), self._z(), self._sp()
        options = [
            x,                   # 0 – X
            (x  + 1) & 0xFFFF,  # 1 – X+1
            y,                   # 2 – Y
            (y  + 1) & 0xFFFF,  # 3 – Y+1
            z,                   # 4 – Z
            (z  + 1) & 0xFFFF,  # 5 – Z+1
            sp,                  # 6 – SP
            (sp + 1) & 0xFFFF,  # 7 – SP+1
            self._RomAddrReg,    # 8 – RomAddrReg
        ]
        return options[sel] if sel <= 8 else 0

    def _input_mux(self):
        """Return the 8-bit value selected by InputSelect for MemDatabus."""
        sel = self._InputSelect.get() & 0x3
        sources = [
            self._mem_data_out.get() & 0xFF,  # 0 – data_out from memory bus
            self._ResL.get()         & 0xFF,  # 1 – ResL
            self._ResH.get()         & 0xFF,  # 2 – ResH
            self._GeneralInput.get() & 0xFF,  # 3 – GeneralInput
        ]
        return sources[sel]

    def _drive_memory_interface(self):
        """Drive the three master→slave wires of the memory interface."""
        rw = self._ReadWrite.get()
        self._mem_address.put(self._addr_mux())
        self._mem_write.put(1 if (rw & 0b10) else 0)
        self._mem_data_in.put(self._MemDatabus if (rw & 0b10) else 0)

    # -----------------------------------------------------------------------
    # Sequential – rising clock edge
    # -----------------------------------------------------------------------
    def clock(self):
        # synchronous reset
        if self._reset.get():
            self._SPH = self._SPL = 0
            self._XH  = self._XL  = 0
            self._YH  = self._YL  = 0
            self._ZH  = self._ZL  = 0
            self._RomAddrReg = 0
            self._MemDatabus = 0
            self._RegisterOut.prepare(0)
            self._mem_address.prepare(0)
            self._mem_write.prepare(0)
            self._mem_data_in.prepare(0)
            return

        # register file write  (DMX + WE)
        if self._WE.get():
            data = self._loading_mux()
            dest = self._LoadSelectMux.get() & 0xF
            if   dest == 0: self._SPH = data
            elif dest == 1: self._SPL = data
            elif dest == 2: self._XH  = data
            elif dest == 3: self._XL  = data
            elif dest == 4: self._YH  = data
            elif dest == 5: self._YL  = data
            elif dest == 6: self._ZH  = data
            elif dest == 7: self._ZL  = data

        # RomAddress latch  (enabled by Mem_instruction[3])
        if self._Mem_instruction.get() & 0x8:
            self._RomAddrReg = self._RomAddress.get() & 0xFFFF

        # MemDatabus latch  (enabled by ReadWrite[0] = read_data)
        if self._ReadWrite.get() & 0b01:
            self._MemDatabus = self._input_mux()

        # prepare sequential outputs
        self._RegisterOut.prepare(self._MemDatabus)
        self._mem_address.prepare(self._addr_mux())
        rw = self._ReadWrite.get()
        self._mem_write.prepare(1 if (rw & 0b10) else 0)
        self._mem_data_in.prepare(self._MemDatabus if (rw & 0b10) else 0)

    # -----------------------------------------------------------------------
    # Combinational – drives outputs between clock edges
    # -----------------------------------------------------------------------
    def propagate(self):
        self._RegisterOut.put(self._MemDatabus)
        self._drive_memory_interface()


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    hw = py4hw.HWSystem()

    # wires
    rst     = hw.wire('reset',           1)
    WE      = hw.wire('WE',              1)
    LSM     = hw.wire('LoadSelectMux',   4)
    LMux    = hw.wire('LoadingMux',      3)
    IncDec  = hw.wire('IncDec',          1)
    RW      = hw.wire('ReadWrite',       2)
    ISel    = hw.wire('InputSelect',     2)
    MInstr  = hw.wire('Mem_instruction', 4)
    RomAddr = hw.wire('RomAddress',     16)
    DBIn    = hw.wire('DataBusInput',    8)
    ResL    = hw.wire('ResL',            8)
    ResH    = hw.wire('ResH',            8)
    GenIn   = hw.wire('GeneralInput',    8)
    RegOut  = hw.wire('RegisterOut',     8)

    # memory interface
    mem_p = MemoryInterface(hw, 'mem', dw=8, aw=16)

    dut = MemoryInterfaceHandler(
        hw, 'MIH',
        reset=rst,
        WE=WE, LoadSelectMux=LSM, LoadingMux=LMux, IncDec=IncDec,
        ReadWrite=RW, InputSelect=ISel, Mem_instruction=MInstr,
        RomAddress=RomAddr,
        DataBusInput=DBIn, ResL=ResL, ResH=ResH, GeneralInput=GenIn,
        memory=mem_p,
        RegisterOut=RegOut,
    )

    def tick(n=1):
        hw.getSimulator().clk(n)

    # reset
    rst.put(1); tick(2); rst.put(0)

    # load XH=0xBE  (LoadingMux=0→ResL, LoadSelectMux=2→XH)
    ResL.put(0xBE); LMux.put(0); LSM.put(2); WE.put(1); tick()
    # load XL=0xEF  (LoadSelectMux=3→XL)
    ResL.put(0xEF); LSM.put(3); tick()
    WE.put(0)

    # address mux sel=0 → X
    MInstr.put(0); hw.getSimulator().propagateAll()
    print(f"mem.address via X   (expect 0xBEEF): 0x{mem_p.address.get():04X}")
    assert mem_p.address.get() == 0xBEEF

    # simulate memory returning 0xAB; latch it (InputSelect=0→data_out, ReadWrite[0]=1)
    mem_p.data_out.put(0xAB); ISel.put(0); RW.put(0b01); tick()
    hw.getSimulator().propagateAll()
    print(f"RegisterOut          (expect 0xAB):   0x{RegOut.get():02X}")
    assert RegOut.get() == 0xAB

    # write cycle (ReadWrite[1]=1) – check mem.write and mem.data_in
    RW.put(0b10); hw.getSimulator().propagateAll()
    print(f"mem.write            (expect 1):       {mem_p.write.get()}")
    print(f"mem.data_in          (expect 0xAB):   0x{mem_p.data_in.get():02X}")
    assert mem_p.write.get() == 1
    assert mem_p.data_in.get() == 0xAB

    print("\nAll checks passed.")