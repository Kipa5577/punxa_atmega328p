# -*- coding: utf-8 -*-
"""
ATmega328P_Top_NoADC.py
========================

A no-ADC variant of the ATmega328P chip, for FPGA boards with no analog
front-end to back an ADC model with (the motivating case: the target FPGA
this project actually gets deployed to has no on-board ADC hardware and no
analog input pins wired to anything meaningful -- synthesizing an ADC
model against nothing is at best dead logic and at worst a build that
references pins the board can't actually provide).

This is deliberately a thin wrapper, not a second copy of
ATmega328P_Chip's ~450-line body: ATmega328P_Top.py's `ATmega328P_Chip`
already accepts an `include_adc` constructor flag that skips building the
`ADC` peripheral, its ADC0-7 pins, and its 0x78-0x7E bus window entirely
(see that flag's own docstring for exactly what "skips" means). Keeping
one real implementation behind both entry points means a future change to
GPIO/Timer/SPI/USART/TWI wiring -- anything other than the ADC itself --
never has to be kept in sync by hand across two files.

Every other peripheral (GPIO, SPI, USART0, TWI0, Timer0/1/2) and every pin
mux is identical to the full chip -- this is "ATmega328P minus the ADC",
not a reduced-functionality chip in any other respect. Every base Arduino
sketch that doesn't call analogRead() (Blink, digital I/O, PWM via
analogWrite() on the OC pins, SPI, I2C/Wire, Serial) runs on this variant
exactly as it does on the full chip.
"""
from ATmega328P_Top import ATmega328P_Chip


class ATmega328P_Chip_NoADC(ATmega328P_Chip):
    """
    `ATmega328P_Chip(..., include_adc=False)` under a distinct, explicit
    name so a call site (or a person skimming imports) doesn't have to
    know the flag exists to reach for the ADC-less build. The ADC0-7
    constructor parameters aren't accepted at all here (unlike the base
    class, which merely ignores them) -- a caller building specifically
    for a no-ADC target has no legitimate analog codes to pass in the
    first place.
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
                 # Flashing / ISP Programming Interface Wires
                 PROG_MOSI=None, PROG_SCK=None, PROG_MISO=None):

        super().__init__(
            parent, name,
            RESET_N=RESET_N, VCC=VCC, GND=GND, AVCC=AVCC, AREF=AREF,
            XTAL1=XTAL1, XTAL2=XTAL2,
            PB0=PB0, PB1=PB1, PB2=PB2, PB3=PB3, PB4=PB4, PB5=PB5, PB6=PB6, PB7=PB7,
            PC0=PC0, PC1=PC1, PC2=PC2, PC3=PC3, PC4=PC4, PC5=PC5, PC6=PC6,
            PD0=PD0, PD1=PD1, PD2=PD2, PD3=PD3, PD4=PD4, PD5=PD5, PD6=PD6, PD7=PD7,
            PROG_MOSI=PROG_MOSI, PROG_SCK=PROG_SCK, PROG_MISO=PROG_MISO,
            include_adc=False,
        )
