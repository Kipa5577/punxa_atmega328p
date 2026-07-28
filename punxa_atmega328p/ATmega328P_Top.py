# -*- coding: utf-8 -*-
"""
ATmega328P Top-Level Integrated Chip Module with py4hw Mux Pin Mapping

Exposes the official 32-pin pinout interface matching the ATmega328P.
Uses py4hw.Mux instances to dynamically route pin signals between 
GPIO alternate port functions and active hardware peripherals (USART0, SPI, Timer0).
"""

import py4hw
import punxa_atmega328p as punxa
from punxa_atmega328p.Memory import MemoryInterface, Ram_Memory, StackPointer
from punxa_atmega328p.Interrupt_Unit import InterruptUnit
from punxa_atmega328p.GPIO import GPIO
from punxa_atmega328p.USART import USART0
from punxa_atmega328p.SPI import SPI
from punxa_atmega328p.Timers import TimerCounter0


class ATmega328P_Chip(py4hw.HWComponent):
    """
    Top-Level ATmega328P Chip Component with Multiplexed Pin Mapping.
    """

    def __init__(self, parent, name,
                 # Power & System Control
                 RESET_N, VCC, GND, AVCC, AREF, XTAL1, XTAL2,
                 # PORT B Pins
                 PB0, PB1, PB2, PB3, PB4, PB5, PB6, PB7,
                 # PORT C Pins
                 PC0, PC1, PC2, PC3, PC4, PC5, PC6,
                 # PORT D Pins
                 PD0, PD1, PD2, PD3, PD4, PD5, PD6, PD7,
                 # ADC Only Pins
                 ADC6, ADC7,
                 # Flashing / ISP Programming Interface Wires
                 PROG_MOSI, PROG_SCK, PROG_MISO):

        super().__init__(parent, name)

        dw = 8   # Data bus width
        aw = 16  # Address bus width

        # =========================================================================
        # 1. INTERNAL BUS INTERFACES & MEMORY MAP
        # =========================================================================
        data_p = MemoryInterface(self, 'data_mem', dw, aw)
        ins_p  = MemoryInterface(self, 'ins_mem', 16, 14)

        reg_p      = MemoryInterface(self, 'reg_p', dw, 7)         # 0x0000 - 0x001F
        gpio_p     = MemoryInterface(self, 'gpio_p', dw, 5)        # 0x0020 - 0x003F
        timer_p    = MemoryInterface(self, 'timer_p', dw, 8)       # 0x0000 - 0x00FF
        spi_p      = MemoryInterface(self, 'spi_p', dw, 2)         # 0x002C - 0x002E
        sp_p       = MemoryInterface(self, 'sp_p', dw, 2)          # 0x005D - 0x005E
        usart_p    = MemoryInterface(self, 'usart_p', dw, 3)       # 0x00C0 - 0x00C7
        int_unit_p = MemoryInterface(self, 'int_unit_p', dw, 1)    # 0x00FE - 0x00FF
        mem_p      = MemoryInterface(self, 'mem_p', dw, 11)        # 0x0100 - 0x08FF

        punxa.MultiplexedBus(self, 'bus', data_p, [
            (timer_p,    0x0000, 0x100),
            (reg_p,      0x0000, 0x020),
            (gpio_p,     0x0020, 0x020),
            (sp_p,       0x005D, 0x002),
            (int_unit_p, 0x00FE, 0x002),
            (spi_p,      0x002C, 0x003),
            (usart_p,    0x00C0, 0x008),
            (mem_p,      0x0100, 0x800)
        ])

        # =========================================================================
        # 2. INTERNAL INTERRUPT & CONTROL WIRES
        # =========================================================================
        self.interrupt_wire = py4hw.Wire(self, 'Interrupt_Line', 1); self.interrupt_wire.put(0)
        self.gie_wire       = py4hw.Wire(self, 'GIE_Line', 1);       self.gie_wire.put(0)

        # USART Internal Signals
        usart_rxc_int = py4hw.Wire(self, 'usart_rxc_int', 1); usart_rxc_int.put(0)
        usart_txc_int = py4hw.Wire(self, 'usart_txc_int', 1); usart_txc_int.put(0)
        usart_udre_int = py4hw.Wire(self, 'usart_udre_int', 1); usart_udre_int.put(0)
        usart_clk_internal = py4hw.Wire(self, 'usart_clk_internal', 1); usart_clk_internal.put(0)
        usart_txd_internal = py4hw.Wire(self, 'usart_txd_internal', 1); usart_txd_internal.put(1)
        usart_tx_enable    = py4hw.Wire(self, 'usart_tx_enable', 1); usart_tx_enable.put(0)

        # SPI Internal Signals
        spi_stc_int      = py4hw.Wire(self, 'spi_stc_int', 1); spi_stc_int.put(0)
        spi_mosi_internal = py4hw.Wire(self, 'spi_mosi_internal', 1); spi_mosi_internal.put(0)
        spi_sck_internal  = py4hw.Wire(self, 'spi_sck_internal', 1); spi_sck_internal.put(0)
        spi_enable        = py4hw.Wire(self, 'spi_enable', 1); spi_enable.put(0)

        # Timer0 Internal Signals
        ocf0a_int = py4hw.Wire(self, 'timer0_ocf0a_int', 1); ocf0a_int.put(0)
        ocf0b_int = py4hw.Wire(self, 'timer0_ocf0b_int', 1); ocf0b_int.put(0)
        tov0_int  = py4hw.Wire(self, 'timer0_tov0_int', 1);  tov0_int.put(0)
        oc0a_internal = py4hw.Wire(self, 'oc0a_internal', 1); oc0a_internal.put(0)
        oc0b_internal = py4hw.Wire(self, 'oc0b_internal', 1); oc0b_internal.put(0)
        timer0_com0a_enable = py4hw.Wire(self, 'timer0_com0a_enable', 1); timer0_com0a_enable.put(0)
        timer0_com0b_enable = py4hw.Wire(self, 'timer0_com0b_enable', 1); timer0_com0b_enable.put(0)

        # GPIO Alternate Function Wires (from VirtualGPIO)
        gpio_pd1_out = py4hw.Wire(self, 'gpio_pd1_out', 1); gpio_pd1_out.put(0)
        gpio_pd6_out = py4hw.Wire(self, 'gpio_pd6_out', 1); gpio_pd6_out.put(0)
        gpio_pd7_out = py4hw.Wire(self, 'gpio_pd7_out', 1); gpio_pd7_out.put(0)
        gpio_pb3_out = py4hw.Wire(self, 'gpio_pb3_out', 1); gpio_pb3_out.put(0)
        gpio_pb5_out = py4hw.Wire(self, 'gpio_pb5_out', 1); gpio_pb5_out.put(0)

        # Dummy wire fallbacks
        self.dummy_wire_low  = py4hw.Wire(self, 'dummy_low', 1);  self.dummy_wire_low.put(0)
        self.dummy_wire_high = py4hw.Wire(self, 'dummy_high', 1); self.dummy_wire_high.put(1)

        # Active-low RESET inversion
        internal_reset = py4hw.Wire(self, 'internal_reset', 1)
        
        py4hw.LogicNot(self, 'reset_inv', RESET_N, internal_reset)
        

        pmosi = PROG_MOSI 
        psck  = PROG_SCK 
        pmiso = PROG_MISO 

        # =========================================================================
        # 3. CPU CORE & MEMORY
        # =========================================================================
        self.cpu = punxa.multicycleProcessor(
            parent=self,
            name='cpu_core',
            Interrupt=self.interrupt_wire,
            Interrupt_Enable=self.gie_wire,
            ins_mem=ins_p,
            memory=data_p,
            reset=internal_reset,
            PROG_MOSI=pmosi,
            PROG_SCK=psck,
            PROG_MISO=pmiso,
            reset_address=0,
            Bus_Passthrough_Ranges=[
                (0x20, 0x36),
                (0x38, 0x3F),
                (0x40, 0x6F),
                (0xC0, 0xC7),
                (0xFE, 0xFF)
            ]
        )

        self.reg_mem = Ram_Memory(self, 'reg_mem', dw, 7, reg_p)
        self.sram    = Ram_Memory(self, 'sram_mem', dw, 11, mem_p)
        self.flash   = Ram_Memory(self, 'flash_mem', 16, 14, ins_p)
        self.sp      = StackPointer(self, 'stack_pointer', sp_p)

        # =========================================================================
        # 4. PERIPHERALS
        # =========================================================================
        self.gpio = GPIO(self, 'gpio', gpio_p)

        self.int_unit = InterruptUnit(
            self, 'interrupt_unit',
            memory=int_unit_p,
            Interrupt=self.interrupt_wire,
            Global_Interrupt_Enable=self.gie_wire,
            TIMER0_COMPA=ocf0a_int,
            TIMER0_COMPB=ocf0b_int,
            TIMER0_OVF=tov0_int,
            SPI_STC=spi_stc_int,
            USART_RX=usart_rxc_int,
            USART_UDRE=usart_udre_int,
            USART_TX=usart_txc_int
        )

        # --- USART0 ---
        rxd_wire = PD0
        xck_wire = PD4

        self.usart = USART0(
            self, 'usart0', usart_p,
            RXD=rxd_wire, TXD=usart_txd_internal, USART_CLK=xck_wire,
            RXC_INT=usart_rxc_int, TXC_INT=usart_txc_int, UDRE_INT=usart_udre_int
        )

        # --- SPI ---
        ss_wire   = PB2 
        miso_wire = PB4

        self.spi = SPI(
            self, 'spi', spi_p,
            SS=ss_wire, MISO=miso_wire, MOSI=spi_mosi_internal,
            CLK=spi_sck_internal, STC=spi_stc_int
        )

        spi_window_start = 0x2C
        self.spi.SPCR_addr_LS -= spi_window_start
        self.spi.SPSR_addr_LS -= spi_window_start
        self.spi.SPDR_addr_LS -= spi_window_start
        self.spi.SPCR_addr_IO = self.spi.SPCR_addr_LS
        self.spi.SPSR_addr_IO = self.spi.SPSR_addr_LS
        self.spi.SPDR_addr_IO = self.spi.SPDR_addr_LS

        # --- TimerCounter0 ---
        t0_pin = PD4 

        self.timer0 = TimerCounter0(
            self, 'timer0', timer_p,
            OC0A=oc0a_internal, OC0B=oc0b_internal, T0=t0_pin,
            OCF0A=ocf0a_int, OCF0B=ocf0b_int, TOV0=tov0_int
        )

        # =========================================================================
        # 5. PIN MAPPING MULTIPLEXERS (py4hw.Mux)
        # =========================================================================
        
        # --- PD1 (TXD vs GPIO PORTD Bit 1) ---
        # Select = 0: GPIO output, Select = 1: USART TXD
        
        py4hw.Mux(self, 'mux_pd1_txd', 
                      sel=usart_tx_enable, 
                      inputs=[gpio_pd1_out, usart_txd_internal], 
                      out=PD1)

        # --- PD6 (Timer0 OC0A vs GPIO PORTD Bit 6) ---
        # Select = 0: GPIO output, Select = 1: Timer0 OC0A
        py4hw.Mux(self, 'mux_pd6_oc0a', 
                      sel=timer0_com0a_enable, 
                      inputs=[gpio_pd6_out, oc0a_internal], 
                      out=PD6)

        # --- PD7 (Timer0 OC0B vs GPIO PORTD Bit 7) ---
        # Select = 0: GPIO output, Select = 1: Timer0 OC0B
        py4hw.Mux(self, 'mux_pd7_oc0b', 
                      sel=timer0_com0b_enable, 
                      inputs=[gpio_pd7_out, oc0b_internal], 
                      out=PD7)

        # --- PB3 (SPI MOSI vs GPIO PORTB Bit 3) ---
        # Select = 0: GPIO output, Select = 1: SPI MOSI
        py4hw.Mux(self, 'mux_pb3_mosi', 
                      sel=spi_enable, 
                      inputs=[gpio_pb3_out, spi_mosi_internal], 
                      out=PB3)

        # --- PB5 (SPI SCK vs GPIO PORTB Bit 5) ---
        # Select = 0: GPIO output, Select = 1: SPI SCK
        py4hw.Mux(self, 'mux_pb5_sck', 
                      sel=spi_enable, 
                      inputs=[gpio_pb5_out, spi_sck_internal], 
                      out=PB5)