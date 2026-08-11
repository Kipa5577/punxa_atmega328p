# -*- coding: utf-8 -*-
"""
ATmega328P Top-Level Integrated Chip Module
============================================

Wires the CPU core (`multicycleProcessor`) together with every real
peripheral model in this project -- GPIO, SPI, USART0, TWI0, ADC, and
Timer0/1/2 -- behind the official 32-pin DIP pinout, with
`py4hw.Mux`-based multiplexers implementing the real chip's
alternate-function pin sharing (e.g. PB3 is GPIO *or* Timer2's OC2A
*or* SPI's MOSI, exactly one at a time, exactly like real hardware).

This replaces a previous version of this file that did not actually
run: it subclassed a nonexistent `py4hw.HWComponent` (every other
component in this project subclasses `py4hw.Logic`), called a
nonexistent `py4hw.LogicNot` (the real name is `py4hw.Not`), and called
`py4hw.Mux(..., inputs=[...], out=...)` with keyword arguments that
don't exist on `py4hw.Mux` (its real signature is positional:
`Mux(parent, name, sel, ins, r)`) -- so every one of those calls raised
before a single instruction could run. It also only wired up GPIO (as
the incomplete `VirtualGPIO` stub, missing PORTD entirely), USART0,
SPI, and Timer0, with mux-enable wires created but never actually
driven by anything (always 0, so the muxes could never have selected
the peripheral side even if construction had succeeded).

Bus design
----------
Real ATmega328P register addresses are absolute values baked directly
into each peripheral class (GPIO, TimerCounter0/1/2, TWI0, ADC -- see
each file's docstring addendum on the single-address refactor that
replaced the old dual IO/LS-address + `instype` scheme). Several of
these peripherals' registers are scattered across the *entire* 0x00-
0xFF low+extended I/O space rather than one contiguous block, so they
each need a full zero-based window to see their own real addresses
unmodified. `py4hw`'s `MultiplexedBus` can't give more than one slave a
full overlapping window at once without later slaves clobbering
earlier ones for *every* address (see `Bus.py`: it's last-match-wins,
not break-on-first-match) -- `TB_of_Timer/timer_bus_router.py` solved
this for Timer0/1/2 alone with a small address-dispatch router; this
file generalizes that same idea into `PeripheralBusRouter`, covering
GPIO + Timer0/1/2 + TWI0 in one router occupying a single slot on the
real bus, dispatching each transaction to whichever one of those
sub-peripherals actually owns the address (introspected automatically
from each instance's own `*_addr` attributes -- no hardcoded address
tables to keep in sync by hand).

SPI (0x2C-0x2E) and USART0 (0xC0-0xC7, already natively
window-relative) don't need the router: SPI's three registers are
rebased to a small 0x2C-relative window the same way `TB_of_SPI/
tb_spi.py` does it, and both are given their own narrow
`MultiplexedBus` slot listed *after* the wide router slot, so they win
their own addresses via the same last-match-wins mechanism (the router
never claims 0x2C-0x2E or 0xC0-0xC7 in the first place, so there's no
real conflict -- just bus plumbing).

ADC (0x78-0x7E) *is* handled by the router (like GPIO/Timer/TWI, it
uses real absolute addresses and needs a full window), since its
address range doesn't overlap GPIO/Timer/TWI's own addresses.

Pin boundary convention
------------------------
This is a digital-only functional simulator, not an electrical one --
`py4hw.Wire` has exactly one producer, so there is no true tri-state
"floating bus" the way real silicon has. Every named top-level pin
(`PB0`, `PC4`, `PD1`, ...) is therefore, by convention:

  * For pins with an alternate *output* function (TXD, MOSI, SCK,
    OC0A/OC0B/OC1A/OC1B/OC2A/OC2B): the single producer is a
    `py4hw.Mux` selecting between GPIO's own per-bit output and the
    active peripheral's output, driven by that peripheral's own
    enable-status pin (`TXEN_STATUS`, `MASTER_ACTIVE`, `OCxy_ENABLE` --
    see USART.py/SPI.py/Timers.py's docstring addenda). Pure-GPIO pins
    with no alternate function (PB0, PB6, PB7, PC6, PD2, PD7) are
    driven directly and unconditionally by GPIO's own per-bit output --
    this model does not attempt full bidirectional/pull-up simulation
    for those specific pins at the *chip* boundary (GPIO.py's own
    `PORTx_ext_in`/`PORTx_ext_oe` inputs, which do support that, are
    tied off to "nothing external driving" here; see `TB_of_GPIO/
    tb_gpio_tests.py` + `peer_gpio.py` for the fully bidirectional
    pattern if a future caller needs to drive these pins from outside).
  * For pins with an alternate *input* function (RXD, SS, MISO, T0, T1,
    T2, XCK): the same named wire is read directly as an input by both
    GPIO (for PINx reads) and the relevant peripheral(s) -- whoever is
    driving that wire from outside this chip (a test peer, e.g.) is
    "the outside world", same convention the original file already
    used for RXD/SS/MISO.
  * PC0-PC5 are the ordinary 1-bit digital GPIO pins. ADC0-ADC5 are
    *separate* top-level ports carrying pre-quantized 10-bit analog
    codes (matching how ADC.py's own ADC6/ADC7 already work, and how
    ADC.py's docstring describes channel inputs generally) -- this
    simulator has no analog voltage representation, so the digital
    PCx pin and its analog ADCx counterpart are deliberately modeled
    as two different signals rather than one, real hardware pin-sharing
    notwithstanding.
  * TWI's SDA/SCL (PC4/PC5) are the one genuinely open-drain case: the
    physical pin is the AND of GPIO's own output bit and TWI0's
    drive-intent output (see `TWI.py`'s `OpenDrainAnd`), and that same
    combined line feeds back into both GPIO's ext_in and TWI0's sense
    inputs -- no enable-mux needed here, since TWI0's intent output
    idles at 1 ("release") whenever TWEN=0, which is exactly a no-op
    against the AND combiner.
"""

import math
import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.Memory import MemoryInterface, Ram_Memory, StackPointer
from punxa_atmega328p.Interrupt_Unit import SimpleInterruptUnit
from punxa_atmega328p.GPIO import GPIO
from punxa_atmega328p.USART import USART0
from punxa_atmega328p.SPI import SPI
from punxa_atmega328p.TWI import TWI0, OpenDrainAnd
from punxa_atmega328p.ADC import ADC
from punxa_atmega328p.Timers import TimerCounter0, TimerCounter1, TimerCounter2


def _collect_register_addresses(instance):
    """Introspects a peripheral instance for every `*_addr` attribute
    (the single-address scheme every real peripheral in this project
    now uses -- see GPIO.py's docstring addendum) and returns the set
    of real ATmega328P addresses it owns. Used by `PeripheralBusRouter`
    so its dispatch table is always in sync with whatever addresses a
    peripheral class actually implements, instead of a hand-maintained
    address table (the approach `timer_bus_router.py` had to use before
    this refactor existed) that can silently drift out of date."""
    addrs = set()
    for attr_name, value in vars(instance).items():
        if attr_name.endswith('_addr') and isinstance(value, int):
            addrs.add(value)
    return addrs


class PeripheralBusRouter(py4hw.Logic):
    """
    Generalizes `TB_of_Timer/timer_bus_router.py`'s address-dispatch
    trick from "just Timer0/1/2" to any number of absolute-addressed
    peripherals sharing one bus slot. See this file's module docstring
    ("Bus design") for the full rationale.

    `targets` is a list of `(label, instance, port)` tuples: `instance`
    is the already-constructed peripheral object (introspected once,
    here, for its owned addresses), `port` is the `MemoryInterface`
    that same instance was built against (this router becomes that
    interface's driving source, same as `MultiplexedBus` would be).
    """

    def __init__(self, parent, name, master, targets):
        super().__init__(parent, name)
        self.master = self.addInterfaceSink('master', master)

        self.targets = []
        for label, instance, port in targets:
            addrs = _collect_register_addresses(instance)
            self.targets.append({
                'label': label,
                'port': self.addInterfaceSource(label, port),
                'addrs': addrs,
            })

    def propagate(self):
        addr = self.master.address.get()
        read = self.master.read.get()
        write = self.master.write.get()
        write_data = self.master.write_data.get()
        instype = self.master.instype.get()

        target = None
        for t in self.targets:
            if addr in t['addrs']:
                target = t
                break

        for t in self.targets:
            p = t['port']
            if t is target:
                p.address.put(addr)
                p.read.put(read)
                p.write.put(write)
                p.write_data.put(write_data)
                p.instype.put(instype)
            else:
                p.address.put(0)
                p.read.put(0)
                p.write.put(0)
                p.write_data.put(0)
                p.instype.put(instype)

        if target is not None:
            self.master.read_data.put(target['port'].read_data.get())
            self.master.resp.put(target['port'].resp.get())
        else:
            self.master.read_data.put(0)
            self.master.resp.put(0)


class ATmega328P_Chip(py4hw.Logic):
    """
    Top-Level ATmega328P Chip Component with Multiplexed Pin Mapping.

    Every pin argument is optional (defaults to an internally-created,
    unconnected dummy wire) so partial/test-only instantiation still
    works -- same optional-pin convention every peripheral in this
    project already uses for its own physical pins.

    Pass `include_adc=False` to build this chip with no ADC peripheral
    at all (see that constructor parameter's own docstring) -- used by
    ATmega328P_Top_NoADC.py for FPGA targets with no analog front-end.
    """

    def __init__(self, parent, name,
                 # Power & System Control
                 RESET_N=None, VCC=None, GND=None, AVCC=None, AREF=None,
                 XTAL1=None, XTAL2=None,
                 # PORT B Pins
                 PB0=None, PB1=None, PB2=None, PB3=None, PB4=None, PB5=None, PB6=None, PB7=None,
                 # PORT C Pins
                 PC0=None, PC1=None, PC2=None, PC3=None, PC4=None, PC5=None, PC6=None,
                 # PORT D Pins
                 PD0=None, PD1=None, PD2=None, PD3=None, PD4=None, PD5=None, PD6=None, PD7=None,
                 # Analog channel inputs (pre-quantized 10-bit codes -- see
                 # module docstring's "Pin boundary convention" on why
                 # these are separate from PC0-PC5/dedicated ADC6-7 pins)
                 ADC0=None, ADC1=None, ADC2=None, ADC3=None, ADC4=None, ADC5=None,
                 ADC6=None, ADC7=None,
                 # Flashing / ISP Programming Interface Wires
                 PROG_MOSI=None, PROG_SCK=None, PROG_MISO=None,
                 # Set False to build the chip with no ADC peripheral at
                 # all -- for targets (e.g. certain FPGA boards) with no
                 # analog front-end to back an ADC model with. See
                 # ATmega328P_Top_NoADC.py, which is just a thin wrapper
                 # around this same flag. When False, ADC0-7 are accepted
                 # for call-site compatibility but never touched -- no
                 # ADC instance is built, its 0x78-0x7E register window
                 # is simply unclaimed on the bus (reads as 0/writes are
                 # no-ops, same as any other unmapped address), and
                 # ADC_IRQ never fires.
                 include_adc=True):

        super().__init__(parent, name)
        self.include_adc = include_adc

        dw = 8   # Data bus width
        aw = 16  # Address bus width

        def pin(w, nm, default=0):
            """Every unconnected top-level pin defaults to a fresh,
            internally-created Wire pre-seeded with `default` -- avoids
            a `Wire.get()` on a never-`.put()` wire crashing on the
            first cycle, same pattern GPIO.py's own optional pins use."""
            if w is None:
                w = py4hw.Wire(self, nm, 1)
                w.put(default)
            return w

        def pin10(w, nm, default=0):
            if w is None:
                w = py4hw.Wire(self, nm, 10)
                w.put(default)
            return w

        # Idle-high by real-hardware convention (open pins the outside
        # world would normally pull up): RESET_N, RXD, SS, MISO.
        RESET_N = pin(RESET_N, 'RESET_N', default=1)
        PD0 = pin(PD0, 'PD0', default=1)   # RXD
        PB2 = pin(PB2, 'PB2', default=1)   # SS
        PB4 = pin(PB4, 'PB4', default=1)   # MISO

        PB0 = pin(PB0, 'PB0'); PB1 = pin(PB1, 'PB1'); PB3 = pin(PB3, 'PB3')
        PB5 = pin(PB5, 'PB5'); PB6 = pin(PB6, 'PB6'); PB7 = pin(PB7, 'PB7')
        PC0 = pin(PC0, 'PC0'); PC1 = pin(PC1, 'PC1'); PC2 = pin(PC2, 'PC2')
        PC3 = pin(PC3, 'PC3'); PC4 = pin(PC4, 'PC4'); PC5 = pin(PC5, 'PC5')
        PC6 = pin(PC6, 'PC6')
        PD1 = pin(PD1, 'PD1'); PD2 = pin(PD2, 'PD2'); PD3 = pin(PD3, 'PD3')
        PD4 = pin(PD4, 'PD4'); PD5 = pin(PD5, 'PD5'); PD6 = pin(PD6, 'PD6')
        PD7 = pin(PD7, 'PD7')

        if include_adc:
            ADC0 = pin10(ADC0, 'ADC0'); ADC1 = pin10(ADC1, 'ADC1')
            ADC2 = pin10(ADC2, 'ADC2'); ADC3 = pin10(ADC3, 'ADC3')
            ADC4 = pin10(ADC4, 'ADC4'); ADC5 = pin10(ADC5, 'ADC5')
            ADC6 = pin10(ADC6, 'ADC6'); ADC7 = pin10(ADC7, 'ADC7')

        PROG_MOSI = pin(PROG_MOSI, 'PROG_MOSI')
        PROG_SCK = pin(PROG_SCK, 'PROG_SCK')
        if PROG_MISO is None:
            PROG_MISO = py4hw.Wire(self, 'PROG_MISO', 1)

        # =====================================================================
        # 1. INTERNAL BUS INTERFACES & MEMORY MAP
        # =====================================================================
        data_p = MemoryInterface(self, 'data_mem', dw, aw)
        ins_p = MemoryInterface(self, 'ins_mem', 16, 14)

        reg_p = MemoryInterface(self, 'reg_p', dw, 7)          # 0x00-0x1F (CPU register file)
        periph_router_p = MemoryInterface(self, 'periph_router_p', dw, 8)  # 0x00-0xFF (GPIO/Timer0-2/TWI0/ADC)
        gpio_p = MemoryInterface(self, 'gpio_p', dw, 8)
        timer0_p = MemoryInterface(self, 'timer0_p', dw, 8)
        timer1_p = MemoryInterface(self, 'timer1_p', dw, 8)
        timer2_p = MemoryInterface(self, 'timer2_p', dw, 8)
        twi_p = MemoryInterface(self, 'twi_p', dw, 8)
        adc_p = MemoryInterface(self, 'adc_p', dw, 8) if include_adc else None
        spi_p = MemoryInterface(self, 'spi_p', dw, 2)          # 0x2C-0x2E, window-relative
        usart_p = MemoryInterface(self, 'usart_p', dw, 3)      # 0xC0-0xC7, natively relative
        sp_p = MemoryInterface(self, 'sp_p', dw, 2)            # 0x5D-0x5E
        int_unit_p = MemoryInterface(self, 'int_unit_p', dw, 1)  # 0xFE-0xFF
        mem_p = MemoryInterface(self, 'mem_p', dw, 11)         # 0x100-0x8FF (SRAM)

        # =====================================================================
        # 2. INTERNAL INTERRUPT & CONTROL WIRES
        # =====================================================================
        self.interrupt_wire = self.wire('Interrupt_Line', 1); self.interrupt_wire.put(0)
        self.gie_wire = self.wire('GIE_Line', 1); self.gie_wire.put(0)

        # USART0 internal signals
        usart_rxc_int = self.wire('usart_rxc_int', 1); usart_rxc_int.put(0)
        usart_txc_int = self.wire('usart_txc_int', 1); usart_txc_int.put(0)
        usart_udre_int = self.wire('usart_udre_int', 1); usart_udre_int.put(0)
        usart_txd_internal = self.wire('usart_txd_internal', 1); usart_txd_internal.put(1)
        usart_clk_internal = self.wire('usart_clk_internal', 1); usart_clk_internal.put(0)
        usart_txen_status = self.wire('usart_txen_status', 1); usart_txen_status.put(0)

        # SPI internal signals
        spi_stc_int = self.wire('spi_stc_int', 1); spi_stc_int.put(0)
        spi_mosi_internal = self.wire('spi_mosi_internal', 1); spi_mosi_internal.put(0)
        spi_sck_internal = self.wire('spi_sck_internal', 1); spi_sck_internal.put(0)
        spi_master_active = self.wire('spi_master_active', 1); spi_master_active.put(0)

        # Timer0/1/2 internal signals
        ocf0a_int = self.wire('ocf0a_int', 1); ocf0a_int.put(0)
        ocf0b_int = self.wire('ocf0b_int', 1); ocf0b_int.put(0)
        tov0_int = self.wire('tov0_int', 1); tov0_int.put(0)
        oc0a_internal = self.wire('oc0a_internal', 1); oc0a_internal.put(0)
        oc0b_internal = self.wire('oc0b_internal', 1); oc0b_internal.put(0)
        oc0a_enable = self.wire('oc0a_enable', 1); oc0a_enable.put(0)
        oc0b_enable = self.wire('oc0b_enable', 1); oc0b_enable.put(0)

        ocf1a_int = self.wire('ocf1a_int', 1); ocf1a_int.put(0)
        ocf1b_int = self.wire('ocf1b_int', 1); ocf1b_int.put(0)
        tov1_int = self.wire('tov1_int', 1); tov1_int.put(0)
        icf1_int = self.wire('icf1_int', 1); icf1_int.put(0)
        oc1a_internal = self.wire('oc1a_internal', 1); oc1a_internal.put(0)
        oc1b_internal = self.wire('oc1b_internal', 1); oc1b_internal.put(0)
        oc1a_enable = self.wire('oc1a_enable', 1); oc1a_enable.put(0)
        oc1b_enable = self.wire('oc1b_enable', 1); oc1b_enable.put(0)

        ocf2a_int = self.wire('ocf2a_int', 1); ocf2a_int.put(0)
        ocf2b_int = self.wire('ocf2b_int', 1); ocf2b_int.put(0)
        tov2_int = self.wire('tov2_int', 1); tov2_int.put(0)
        oc2a_internal = self.wire('oc2a_internal', 1); oc2a_internal.put(0)
        oc2b_internal = self.wire('oc2b_internal', 1); oc2b_internal.put(0)
        oc2a_enable = self.wire('oc2a_enable', 1); oc2a_enable.put(0)
        oc2b_enable = self.wire('oc2b_enable', 1); oc2b_enable.put(0)

        # TWI0 internal signals (open-drain intent lines -- see
        # module docstring)
        twi_int = self.wire('twi_int', 1); twi_int.put(0)
        twi_sda_intent = self.wire('twi_sda_intent', 1); twi_sda_intent.put(1)
        twi_scl_intent = self.wire('twi_scl_intent', 1); twi_scl_intent.put(1)
        twi_sda_sense = self.wire('twi_sda_sense', 1); twi_sda_sense.put(1)
        twi_scl_sense = self.wire('twi_scl_sense', 1); twi_scl_sense.put(1)

        # ADC internal signals
        adc_irq = self.wire('adc_irq', 1); adc_irq.put(0)

        # GPIO physical pin buses (val/oe out, ext_in/ext_oe in), one
        # trio per port -- see GPIO.py's own docstring for the exact
        # PIN-read / pull-up semantics these implement.
        b_val = self.wire('gpio_b_val', 8); b_oe = self.wire('gpio_b_oe', 8)
        c_val = self.wire('gpio_c_val', 8); c_oe = self.wire('gpio_c_oe', 8)
        d_val = self.wire('gpio_d_val', 8); d_oe = self.wire('gpio_d_oe', 8)
        # No external driver at the chip boundary for pure-GPIO bits in
        # this pass (see module docstring) -- tie ext_in/ext_oe low so
        # GPIO's own pull-up/floating-pin logic still behaves sanely
        # (DDR=0/PORT=1 still reads back 1, DDR=0/PORT=0 still reads 0).
        b_ext_in = self.wire('gpio_b_ext_in', 8); b_ext_in.put(0)
        b_ext_oe = self.wire('gpio_b_ext_oe', 8); b_ext_oe.put(0)
        c_ext_in = self.wire('gpio_c_ext_in', 8); c_ext_in.put(0)
        c_ext_oe = self.wire('gpio_c_ext_oe', 8); c_ext_oe.put(0)
        d_ext_in = self.wire('gpio_d_ext_in', 8); d_ext_in.put(0)
        d_ext_oe = self.wire('gpio_d_ext_oe', 8); d_ext_oe.put(0)

        self.dummy_wire_low = self.wire('dummy_low', 1); self.dummy_wire_low.put(0)
        self.dummy_wire_high = self.wire('dummy_high', 1); self.dummy_wire_high.put(1)

        # Active-low RESET inversion
        internal_reset = self.wire('internal_reset', 1)
        py4hw.Not(self, 'reset_inv', RESET_N, internal_reset)

        # =====================================================================
        # 3. INTERNAL BUS TOPOLOGY
        # =====================================================================
        # periph_router_p listed first: it's a full [0,0x100) window, but
        # (per module docstring) only ever answers for addresses that
        # actually belong to GPIO/Timer0/1/2/TWI0/ADC. Every narrower
        # window listed after it wins its own addresses via
        # MultiplexedBus's last-match-wins semantics (see Bus.py).
        punxa.MultiplexedBus(self, 'bus', data_p, [
            (periph_router_p, 0x0000, 0x100),
            (reg_p, 0x0000, 0x020),
            (spi_p, 0x002C, 0x003),
            (usart_p, 0x00C0, 0x008),
            (sp_p, 0x005D, 0x002),
            (int_unit_p, 0x00FE, 0x002),
            (mem_p, 0x0100, 0x800),
        ])

        # =====================================================================
        # 4. CPU CORE & MEMORY
        # =====================================================================
        self.cpu = punxa.multicycleProcessor(
            parent=self,
            name='cpu_core',
            Interrupt=self.interrupt_wire,
            Interrupt_Enable=self.gie_wire,
            ins_mem=ins_p,
            memory=data_p,
            reset=internal_reset,
            PROG_MOSI=PROG_MOSI,
            PROG_SCK=PROG_SCK,
            PROG_MISO=PROG_MISO,
            reset_address=0,
            # Interface-compatibility only -- MemoryInterfaceHandler's
            # real gate is an inline check covering this exact set of
            # ranges (see that file's `is_passthrough` comment); kept
            # here so a future fix that makes it honor this constructor
            # argument doesn't silently change behavior underneath us.
            Bus_Passthrough_Ranges=[
                (0x20, 0x36), (0x37, 0x37), (0x38, 0x3F), (0x40, 0x6F),
                (0x70, 0x70), (0x78, 0x7E), (0x80, 0x8B), (0xB0, 0xB4),
                (0xB8, 0xBC), (0xC0, 0xC7), (0xFE, 0xFF),
            ],
        )

        self.reg_mem = Ram_Memory(self, 'reg_mem', dw, 7, reg_p)
        self.sram = Ram_Memory(self, 'sram_mem', dw, 11, mem_p)
        self.flash = Ram_Memory(self, 'flash_mem', 16, 14, ins_p)
        self.sp = StackPointer(self, 'stack_pointer', sp_p)

        # =====================================================================
        # 5. PERIPHERALS
        # =====================================================================
        self.gpio = GPIO(
            self, 'gpio', gpio_p,
            PORTB_val=b_val, PORTB_oe=b_oe, PORTB_ext_in=b_ext_in, PORTB_ext_oe=b_ext_oe,
            PORTC_val=c_val, PORTC_oe=c_oe, PORTC_ext_in=c_ext_in, PORTC_ext_oe=c_ext_oe,
            PORTD_val=d_val, PORTD_oe=d_oe, PORTD_ext_in=d_ext_in, PORTD_ext_oe=d_ext_oe,
        )

        self.timer0 = TimerCounter0(
            self, 'timer0', timer0_p,
            OC0A=oc0a_internal, OC0B=oc0b_internal, T0=PD4,
            OCF0A=ocf0a_int, OCF0B=ocf0b_int, TOV0=tov0_int,
            OC0A_ENABLE=oc0a_enable, OC0B_ENABLE=oc0b_enable,
        )

        self.timer1 = TimerCounter1(
            self, 'timer1', timer1_p,
            OC1A=oc1a_internal, OC1B=oc1b_internal, T1=PD5,
            OCF1A=ocf1a_int, OCF1B=ocf1b_int, TOV1=tov1_int, ICF1=icf1_int,
            OC1A_ENABLE=oc1a_enable, OC1B_ENABLE=oc1b_enable,
        )

        self.timer2 = TimerCounter2(
            self, 'timer2', timer2_p,
            OC2A=oc2a_internal, OC2B=oc2b_internal, T2=self.dummy_wire_low,
            OCF2A=ocf2a_int, OCF2B=ocf2b_int, TOV2=tov2_int,
            OC2A_ENABLE=oc2a_enable, OC2B_ENABLE=oc2b_enable,
        )

        self.twi = TWI0(
            self, 'twi0', twi_p,
            SCL_drive=twi_scl_intent, SCL_sense=twi_scl_sense,
            SDA_drive=twi_sda_intent, SDA_sense=twi_sda_sense,
            TWI_INT=twi_int,
        )

        if include_adc:
            self.adc = ADC(
                self, 'adc', adc_p,
                ADC0=ADC0, ADC1=ADC1, ADC2=ADC2, ADC3=ADC3,
                ADC4=ADC4, ADC5=ADC5, ADC6=ADC6, ADC7=ADC7,
                ADC_IRQ=adc_irq,
                T0_COMPA_trig=ocf0a_int, T0_OVF_trig=tov0_int,
                T1_COMPB_trig=ocf1b_int, T1_OVF_trig=tov1_int, T1_CAPT_trig=icf1_int,
            )
        else:
            # No ADC hardware on this target (see class docstring / the
            # `include_adc` constructor parameter) -- adc_irq simply
            # stays tied to its 0 default forever (never driven by
            # anything), and 0x78-0x7E is left unclaimed on the bus.
            self.adc = None

        self.usart = USART0(
            self, 'usart0', usart_p,
            RXD=PD0, TXD=usart_txd_internal, USART_CLK=usart_clk_internal,
            RXC_INT=usart_rxc_int, TXC_INT=usart_txc_int, UDRE_INT=usart_udre_int,
            TXEN_STATUS=usart_txen_status,
        )

        self.spi = SPI(
            self, 'spi', spi_p,
            SS=PB2, MISO=PB4, MOSI=spi_mosi_internal, CLK=spi_sck_internal,
            STC=spi_stc_int, MASTER_ACTIVE=spi_master_active,
        )
        # Rebase SPI's absolute addresses to this instance's 0x2C-relative
        # bus window -- same technique TB_of_SPI/tb_spi.py uses (see that
        # file's comment for the full rationale).
        _spi_window_start = 0x2C
        self.spi.SPCR_addr -= _spi_window_start
        self.spi.SPSR_addr -= _spi_window_start
        self.spi.SPDR_addr -= _spi_window_start

        periph_targets = [
            ('gpio', self.gpio, gpio_p),
            ('timer0', self.timer0, timer0_p),
            ('timer1', self.timer1, timer1_p),
            ('timer2', self.timer2, timer2_p),
            ('twi0', self.twi, twi_p),
        ]
        if include_adc:
            periph_targets.append(('adc', self.adc, adc_p))

        self.periph_router = PeripheralBusRouter(
            self, 'periph_router', periph_router_p,
            targets=periph_targets,
        )

        # SimpleInterruptUnit dispatches purely by kwarg name (see
        # Interrupt_Unit.py) -- every source this chip actually
        # generates is wired in; sources with no implemented peripheral
        # (INT0/INT1/PCINT*/WDT/EE_READY/ANALOG_COMP/SPM_READY) are
        # simply omitted rather than tied to a dummy wire, matching how
        # every existing per-peripheral testbench in this project uses
        # this same class.
        self.int_unit = SimpleInterruptUnit(
            self, 'interrupt_unit',
            memory=int_unit_p,
            Interrupt=self.interrupt_wire,
            Global_Interrupt_Enable=self.gie_wire,
            TIMER0_COMPA=ocf0a_int, TIMER0_COMPB=ocf0b_int, TIMER0_OVF=tov0_int,
            TIMER1_CAPT=icf1_int, TIMER1_COMPA=ocf1a_int, TIMER1_COMPB=ocf1b_int, TIMER1_OVF=tov1_int,
            TIMER2_COMPA=ocf2a_int, TIMER2_COMPB=ocf2b_int, TIMER2_OVF=tov2_int,
            SPI_STC=spi_stc_int,
            USART_RX=usart_rxc_int, USART_UDRE=usart_udre_int, USART_TX=usart_txc_int,
            ADC=adc_irq,
            TWI=twi_int,
        )

        # =====================================================================
        # 6. PIN-MAPPING MULTIPLEXERS (py4hw.Mux)
        # =====================================================================
        # Per-bit taps off GPIO's own val/oe port buses -- one BitsLSBF
        # split per port, reused by every mux below that needs "GPIO's
        # own idea of what this bit should output".
        b_val_bits = self.wires('b_val_bit', 8, 1)
        d_val_bits = self.wires('d_val_bit', 8, 1)
        py4hw.BitsLSBF(self, 'split_b_val', b_val, b_val_bits)
        py4hw.BitsLSBF(self, 'split_d_val', d_val, d_val_bits)

        def mux2(label, sel, gpio_bit, alt, out_wire):
            """2-input py4hw.Mux, GPIO on select=0, alternate function
            on select=1 -- the shared pattern every single-alternate-
            function pin below uses."""
            py4hw.Mux(self, label, sel, [gpio_bit, alt], out_wire)

        # --- PB0, PB6, PB7, PC6, PD2, PD7: no alternate function
        # modeled here (ICP1/CLKO, XTAL1/XTAL2, RESET, INT0, AIN1
        # respectively) -- GPIO drives these pins directly.
        py4hw.Bit(self, 'bit_pb0', b_val, 0, PB0)
        py4hw.Bit(self, 'bit_pb6', b_val, 6, PB6)
        py4hw.Bit(self, 'bit_pb7', b_val, 7, PB7)
        py4hw.Bit(self, 'bit_pc6', c_val, 6, PC6)
        py4hw.Bit(self, 'bit_pd2', d_val, 2, PD2)
        py4hw.Bit(self, 'bit_pd7', d_val, 7, PD7)

        # --- PC0-PC3: plain digital GPIO (their analog ADC0-ADC3
        # counterparts are separate top-level ports -- see module
        # docstring).
        py4hw.Bit(self, 'bit_pc0', c_val, 0, PC0)
        py4hw.Bit(self, 'bit_pc1', c_val, 1, PC1)
        py4hw.Bit(self, 'bit_pc2', c_val, 2, PC2)
        py4hw.Bit(self, 'bit_pc3', c_val, 3, PC3)

        # --- PB1 (OC1A vs GPIO) ---
        mux2('mux_pb1_oc1a', oc1a_enable, b_val_bits[1], oc1a_internal, PB1)

        # --- PB2 (OC1B vs GPIO). SS itself is read directly off the
        # physical pin above (SPI.SS=PB2), independent of this mux. ---
        mux2('mux_pb2_oc1b', oc1b_enable, b_val_bits[2], oc1b_internal, PB2)

        # --- PB3 (GPIO / Timer2 OC2A / SPI MOSI) -- three-way,
        # implemented as two nested 2-input muxes with SPI given
        # priority over Timer2 over GPIO, matching the real-hardware
        # expectation that a firmware wouldn't enable two alternate
        # functions on the same pin at once. ---
        pb3_gpio_or_oc2a = self.wire('pb3_gpio_or_oc2a', 1)
        mux2('mux_pb3_oc2a', oc2a_enable, b_val_bits[3], oc2a_internal, pb3_gpio_or_oc2a)
        mux2('mux_pb3_mosi', spi_master_active, pb3_gpio_or_oc2a, spi_mosi_internal, PB3)

        # --- PB4 (MISO). SPI never drives MISO in this model (master-
        # mode only, see SPI.py) -- GPIO drives the pin directly, and
        # SPI.MISO=PB4 reads it as an input regardless. ---
        py4hw.Bit(self, 'bit_pb4', b_val, 4, PB4)

        # --- PB5 (SPI SCK vs GPIO) ---
        mux2('mux_pb5_sck', spi_master_active, b_val_bits[5], spi_sck_internal, PB5)

        # --- PC4 (TWI SDA vs GPIO), PC5 (TWI SCL vs GPIO): real
        # open-drain combine, no enable-mux needed (see module
        # docstring) -- OpenDrainAnd(gpio_release, twi_intent) -> pin,
        # and that combined line feeds back into TWI0's sense inputs.
        # GPIO's own contribution to an open-drain line is NOT simply
        # its push-pull PORTC bit: GPIO only actually pulls the line
        # low when it's BOTH configured as an output (DDR=1) AND
        # writing 0 -- when DDR=0 (the real-hardware-correct
        # configuration for using TWI at all), GPIO must contribute
        # "released" (1) regardless of PORTC's bit value, or an
        # unrelated PORTC4/5=0 default would falsely hold the bus low
        # forever. gpio_release = NOT(oe) OR val, built straight off
        # GPIO's own val/oe port buses.
        pc4_val_bit = self.wire('pc4_val_bit', 1); pc4_oe_bit = self.wire('pc4_oe_bit', 1)
        pc5_val_bit = self.wire('pc5_val_bit', 1); pc5_oe_bit = self.wire('pc5_oe_bit', 1)
        py4hw.Bit(self, 'bit_pc4_val', c_val, 4, pc4_val_bit)
        py4hw.Bit(self, 'bit_pc4_oe', c_oe, 4, pc4_oe_bit)
        py4hw.Bit(self, 'bit_pc5_val', c_val, 5, pc5_val_bit)
        py4hw.Bit(self, 'bit_pc5_oe', c_oe, 5, pc5_oe_bit)
        pc4_not_oe = self.wire('pc4_not_oe', 1); pc5_not_oe = self.wire('pc5_not_oe', 1)
        py4hw.Not(self, 'not_pc4_oe', pc4_oe_bit, pc4_not_oe)
        py4hw.Not(self, 'not_pc5_oe', pc5_oe_bit, pc5_not_oe)
        pc4_release = self.wire('pc4_release', 1); pc5_release = self.wire('pc5_release', 1)
        py4hw.Or2(self, 'or_pc4_release', pc4_not_oe, pc4_val_bit, pc4_release)
        py4hw.Or2(self, 'or_pc5_release', pc5_not_oe, pc5_val_bit, pc5_release)
        OpenDrainAnd(self, 'od_sda', [pc4_release, twi_sda_intent], PC4)
        OpenDrainAnd(self, 'od_scl', [pc5_release, twi_scl_intent], PC5)
        # Feed the combined lines back so TWI0 senses the real bus
        # level (its own drive included) -- this is what the I2C
        # protocol actually depends on for correctness (clock
        # stretching, arbitration-adjacent checks, etc.), and is fully
        # wired here.
        py4hw.Buf(self, 'sda_sense_buf', PC4, twi_sda_sense)
        py4hw.Buf(self, 'scl_sense_buf', PC5, twi_scl_sense)
        # Scope note: GPIO's own PINC read of bits 4/5 still reflects
        # PORTC's own written value rather than the true combined
        # open-drain bus level (that would need per-bit splicing into
        # GPIO's PORTC_ext_in/PORTC_ext_oe 8-bit buses, which carry all
        # 8 PORTC bits as one signal -- out of scope for this pass,
        # since TWI0's own sense inputs above already carry the signal
        # that actually matters for I2C correctness). A future pass
        # wanting fully accurate PINC reads on PC4/PC5 while TWI0 is
        # active would build c_ext_in/c_ext_oe from 8 individual 1-bit
        # wires via py4hw.ConcatenateLSBF, tying bits 4/5 to the sensed
        # open-drain lines and the rest to 0, instead of the single
        # tied-low 8-bit wire used here.

        # --- PD1 (USART TXD vs GPIO) ---
        mux2('mux_pd1_txd', usart_txen_status, d_val_bits[1], usart_txd_internal, PD1)

        # --- PD3 (Timer2 OC2B vs GPIO) ---
        mux2('mux_pd3_oc2b', oc2b_enable, d_val_bits[3], oc2b_internal, PD3)

        # --- PD4: no output alternate function to mux (XCK0 is only
        # ever driven by this chip in synchronous-master mode, which
        # this USART0 model wires via optional XCK_in/XCK_DDR_OUT kwargs
        # not used in this integration pass -- see USART.py) -- GPIO
        # drives the pin, and Timer0.T0/USART XCK both read it as an
        # input regardless (same physical pin, real hardware convention).
        py4hw.Bit(self, 'bit_pd4', d_val, 4, PD4)

        # --- PD5 (Timer0 OC0B vs GPIO). Timer1's T1 external-clock
        # input also reads this same physical pin passively. ---
        mux2('mux_pd5_oc0b', oc0b_enable, d_val_bits[5], oc0b_internal, PD5)

        # --- PD6 (Timer0 OC0A vs GPIO) ---
        mux2('mux_pd6_oc0a', oc0a_enable, d_val_bits[6], oc0a_internal, PD6)
