import py4hw
from punxa_atmega328p.Memory import *


class InterruptUnit(py4hw.Logic):
    def __init__(self,parent,name:str,memory:MemoryInterface,Interrupt,Global_Interrupt_Enable,INT0,INT1,PCINT0,PCINT1,PCINT2,WDT,TIMER2_COMPA,TIMER2_COMPB,TIMER2_OVF,TIMER1_CAPT,TIMER1_COMPA,TIMER1_COMPB,TIMER1_OVF,TIMER0_COMPA,TIMER0_COMPB,TIMER0_OVF,SPI_STC,USART_RX,USART_UDRE,USART_TX,ADC,EE_READY,ANALOG_COMP,TWI,SPM_READY):
        super().__init__(parent,name)

        self.interface = self.addInterfaceSink('port',memory)

        self.JUMPto = 0

        self.I = self.addIn('I',Global_Interrupt_Enable)
        self.Interrupt = self.addOut('Interrupt',Interrupt)
        #interrutpts
        self.INT0 = self.addIn('INT0',INT0)
        self.INT1 = self.addIn('INT1',INT1)
        self.PCINT0 = self.addIn('PCINT0',PCINT0)
        self.PCINT1 = self.addIn('PCINT1',PCINT1)
        self.PCINT2 = self.addIn('PCINT2',PCINT2)
        self.WDT = self.addIn('WDT',WDT)
        self.TIMER2_COMPA = self.addIn('TIMER2_COMPA',TIMER2_COMPA)
        self.TIMER2_COMPB = self.addIn('TIMER2_COMPB',TIMER2_COMPB)
        self.TIMER2_OVF = self.addIn('TIMER2_OVF',TIMER2_OVF)
        self.TIMER1_CAPT = self.addIn('TIMER1_CAPT',TIMER1_CAPT)
        self.TIMER1_COMPA = self.addIn('TIMER1_COMPA',TIMER1_COMPA)
        self.TIMER1_COMPB = self.addIn('TIMER1_COMPB',TIMER1_COMPB)
        self.TIMER1_OVF = self.addIn('TIMER1_OVF',TIMER1_OVF)
        self.TIMER0_COMPA = self.addIn('TIMER0_COMPA',TIMER0_COMPA)
        self.TIMER0_COMPB = self.addIn('TIMER0_COMPB',TIMER0_COMPB)
        self.TIMER0_OVF = self.addIn('TIMER0_OVF',TIMER0_OVF)
        self.SPI_STC = self.addIn('SPI_STC',SPI_STC)
        self.USART_RX = self.addIn('USART_RX',USART_RX)
        self.USART_UDRE = self.addIn('USART_UDRE',USART_UDRE)
        self.USART_TX = self.addIn('USART_TX',USART_TX)
        self.ADC = self.addIn('ADC',ADC)
        self.EE_READY = self.addIn('EE_READY',EE_READY)
        self.ANALOG_COMP = self.addIn('ANALOG_COMP',ANALOG_COMP)
        self.TWI = self.addIn('TWI',TWI)
        self.SPM_READY = self.addIn('SPM_READY',SPM_READY)

    def clock(self):
        if self.I.get() == 1:

            if self.INT0.get() == 1:
                ## save the current pc position to the stack 

                ## go to the interrupt vector
                self.JUMPto = 0x002 

                self.Interrupt.preapare(1)

            elif self.INT1.get() == 1: 

                self.JUMPto = 0x004

                self.Interrupt.preapare(1)

            elif self.PCINT0.get() == 1: 

                self.JUMPto = 0x006

                self.Interrupt.preapare(1)

            elif self.PCINT1.get() == 1:

                self.JUMPto = 0x008

                self.Interrupt.preapare(1)

            elif self.PCINT2.get() == 1:

                self.JUMPto = 0x00A

                self.Interrupt.preapare(1)

            elif self.WDT.get() == 1:

                self.JUMPto = 0x00C

                self.Interrupt.preapare(1)

            elif self.TIMER2_COMPA.get() == 1:

                self.JUMPto = 0x00E

                self.Interrupt.preapare(1)

            elif self.TIMER2_COMPB.get() == 1:

                self.JUMPto = 0x010

                self.Interrupt.preapare(1)

            elif self.TIMER2_OVF.get() == 1: 

                self.JUMPto = 0x012

                self.Interrupt.preapare(1)

            elif self.TIMER1_CAPT.get() == 1:

                self.JUMPto = 0x014

                self.Interrupt.preapare(1)

            elif self.TIMER1_COMPA.get() == 1: 

                self.JUMPto = 0x016

                self.Interrupt.preapare(1)

            elif self.TIMER1_COMPB.get() == 1: 

                self.JUMPto = 0x018

                self.Interrupt.preapare(1)

            elif self.TIMER1_OVF.get() == 1: 

                self.JUMPto = 0x01A

                self.Interrupt.preapare(1)

            elif self.TIMER0_COMPA.get() == 1: 

                self.JUMPto = 0x01C

                self.Interrupt.preapare(1)

            elif self.TIMER0_COMPB.get() == 1:

                self.JUMPto = 0x01E

                self.Interrupt.preapare(1)

            elif self.TIMER0_OVF.get() == 1:

                self.JUMPto = 0x020

                self.Interrupt.preapare(1)

            elif self.SPI_STC.get() == 1:

                self.JUMPto = 0x022

                self.Interrupt.preapare(1)

            elif self.USART_RX.get() == 1:
            
                self.JUMPto = 0x24

                self.Interrupt.preapare(1)

            elif self.USART_UDRE.get() == 1:

                self.JUMPto = 0x026

                self.Interrupt.preapare(1)

            elif self.USART_TX.get() == 1:

                self.JUMPto = 0x028

                self.Interrupt.preapare(1)

            elif self.ADC.get() == 1:

                self.JUMPto = 0x2A

                self.Interrupt.preapare(1)

            elif self.EE_READY.get() == 1:

                self.JUMPto = 0x2C

                self.Interrupt.preapare(1)

            elif self.ANALOG_COMP.get() == 1:

                self.JUMPto = 0x2E

                self.Interrupt.preapare(1)

            elif self.TWI.get() == 1:

                self.JUMPto = 0x030

                self.Interrupt.preapare(1)

            elif self.SPM_READY.get() == 1: 

                self.JUMPto = 0x032
                
                self.Interrupt.preapare(1)



class SimpleInterruptUnit(py4hw.Logic):
    def __init__(self, parent, name: str, memory: py4hw.Interface, Interrupt, Global_Interrupt_Enable, **kwargs):
        super().__init__(parent, name)

        self.interface = self.addInterfaceSink('port', memory)
        self.JUMPto = 0
        
        self.I = self.addIn('I', Global_Interrupt_Enable)
        self.Interrupt = self.addOut('Interrupt', Interrupt)

        self.vector_table = {
            'INT0':          0x002, 'INT1':          0x004, 'PCINT0':        0x006,
            'PCINT1':        0x008, 'PCINT2':        0x00A, 'WDT':           0x00C,
            'TIMER2_COMPA':  0x00E, 'TIMER2_COMPB':  0x010, 'TIMER2_OVF':    0x012,
            'TIMER1_CAPT':   0x014, 'TIMER1_COMPA':  0x016, 'TIMER1_COMPB':  0x018,
            'TIMER1_OVF':    0x01A, 'TIMER0_COMPA':  0x01C, 'TIMER0_COMPB':  0x01E,
            'TIMER0_OVF':    0x020, 'SPI_STC':       0x022, 'USART_RX':      0x024,
            'USART_UDRE':    0x026, 'USART_TX':      0x028, 'ADC':           0x02A,
            'EE_READY':      0x02C, 'ANALOG_COMP':   0x02E, 'TWI':           0x030,
            'SPM_READY':     0x032
        }

        self.active_interrupts = {}
        for name, vector_address in self.vector_table.items():
            wire = kwargs.get(name, None)
            if wire is not None:
                self.active_interrupts[name] = {'port': self.addIn(name, wire), 'vector': vector_address}

    def clock(self):
        # 1. Handle Incoming Interrupt Signals
        interrupt_triggered = False
        
        if self.I.get() == 1:
            for name, config in self.active_interrupts.items():
                if config['port'].get() == 1:
                    self.JUMPto = config['vector']
                    self.Interrupt.prepare(1)  
                    interrupt_triggered = True
                    break

        if not interrupt_triggered:
            self.Interrupt.prepare(0)

        # 2. Handle Memory Bus
        bus_active = (self.interface.read.get() == 1) or (self.interface.write.get() == 1)
        if bus_active:
            self.interface.resp.prepare(1) # Prevent CPU hanging
        else:
            self.interface.resp.prepare(0)

        if self.interface.read.get() == 1:
            relative_addr = self.interface.address.get()
            if relative_addr == 0x00:
                self.interface.read_data.prepare(self.JUMPto & 0xFF)
            elif relative_addr == 0x01:
                self.interface.read_data.prepare((self.JUMPto >> 8) & 0xFF)
            else:
                self.interface.read_data.prepare(0)
        else:
            self.interface.read_data.prepare(0)