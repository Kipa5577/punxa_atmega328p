import py4hw
from .Memory import *

# =============================================================================
# ADC -- real conversion state machine (replaces the ADCBehavioral stub that
# only ever did bus-register bookkeeping: ADSC was parsed but never acted
# on, ADCH/ADCL were plain read/write ints with no relationship to a
# conversion, and there was no ADIF/interrupt behavior or timing at all).
#
# Scope, matching this project's existing "explicitly out of scope" pattern
# used for TWI (master-only)/USART0 (no sync mode) etc:
#
#   IMPLEMENTED, per the ATmega328P datasheet's "Analog-to-Digital
#   Converter" chapter:
#     - ADMUX (REFS1:0, ADLAR, MUX3:0), ADCSRA (ADEN, ADSC, ADATE, ADIF,
#       ADIE, ADPS2:0), ADCSRB (ACME, ADTS2:0), ADCH/ADCL, DIDR0 -- full
#       bit-level register semantics, including the parts the old stub
#       got wrong or skipped entirely:
#         * ADIF sets on conversion completion UNCONDITIONALLY (real
#           datasheet behavior -- ADIE only gates whether an interrupt is
#           requested, not whether the flag itself latches, so ADIF can
#           be polled with interrupts disabled). ADIF is cleared by
#           writing a logical one to it (real hardware quirk), not by a
#           plain register overwrite.
#         * ADSC is set by software to start a single conversion and is
#           cleared by hardware the instant that conversion completes
#           (while a conversion is in progress ADSC reads as 1); it is
#           also cleared immediately if ADEN is cleared mid-conversion
#           (real datasheet: turning the ADC off terminates any ongoing
#           conversion).
#         * MUX/REFS selection is latched at the moment a conversion
#           starts, not read live throughout -- changing ADMUX while a
#           conversion is in progress has no effect on that conversion,
#           exactly as the datasheet specifies.
#         * Reading ADCL locks the ADCH/ADCL pair against being updated
#           by a completing conversion until ADCH is subsequently read
#           (the datasheet's "always read ADCL before ADCH" atomicity
#           mechanism) -- implemented as a real lock, not just documented.
#     - Conversion timing modeled in real ADC-clock cycles, derived from
#       the system clock via the ADPS2:0 prescaler (division factors
#       2/2/4/8/16/32/64/128 for ADPS2:0 = 0..7, matching the datasheet
#       table where 000 and 001 both mean /2): 25 ADC-clock cycles for
#       the first conversion after ADEN is set (datasheet: extended for
#       analog circuitry initialization), 13 for every conversion after
#       that, whether manually started (ADSC written directly), free-
#       running (ADATE=1, ADTS2:0=000), or triggered by one of the other
#       six ADTS2:0 sources (rising edge on the selected trigger wire).
#     - All eight single-ended input channels (ADC0-ADC7, MUX3:0 =
#       0000-0111) and the GND channel (MUX3:0 = 1111, always converts
#       to 0).
#
#   EXPLICITLY OUT OF SCOPE (documented here rather than silently
#   skipped, same convention as TWI.py's own scope note):
#     - Real analog modeling. This is a digital HDL simulator with no
#       analog front end -- exactly like PeerUART/PeerTimer feed already-
#       formed digital bit streams/edges rather than simulating an RC
#       line or a crystal, the ADC0-ADC7 input wires here carry an
#       already-quantized 10-bit code (0-1023) representing "what the
#       real ADC's sample-and-hold + successive-approximation ladder
#       would have produced for the voltage on that pin, referenced to
#       whatever REFS currently selects" -- a test peer supplies that
#       digitized value directly. REFS1:0 and ACME are therefore stored
#       faithfully (readable/writable exactly as real ADMUX/ADCSRB bits)
#       but have no functional effect on the conversion result, since
#       there is no real analog reference ladder to switch.
#     - The internal 1.1V bandgap reference channel (MUX3:0 = 1110) and
#       the differential input channels (MUX3:0 = 1000-1101, TQFP/MLF-
#       package only anyway). Both read back as a fixed 0 result rather
#       than a fabricated "plausible" value, so a test exercising them
#       fails loudly instead of silently passing on a made-up number.
#     - DIDR0's actual effect (disabling the digital input buffer on the
#       corresponding PORTC pin) -- stored faithfully as a register but
#       not cross-wired into GPIO.py's PORTC digital-input path, since
#       that would mean touching GPIO for an ADC change and this project
#       is still in the "each peripheral standalone" phase (no
#       ATmega328P_Top.py integration yet).
#     - The datasheet's fractional (1.5 / 2.5 ADC-clock) sample-and-hold
#       offset for the very start of a conversion -- this simulator
#       counts whole system-clock cycles throughout (see Timers.py's own
#       prescaler for the same whole-cycle convention), so both the
#       trigger-edge-to-sample-start delay and the "extra 0.5 cycle" the
#       datasheet lists for auto-triggered vs. free-running/manual
#       conversions are folded into the same 13-cycle whole-conversion
#       count. Worth revisiting only if a future test needs cycle-exact
#       ADC timing.
# =============================================================================
class ADC(py4hw.Logic):

    # ADPS2:0 -> ADC clock division factor (datasheet Table 23-5;
    # ADPS2:0 = 000 and 001 are both "/2").
    _PRESCALER_TABLE = {0: 2, 1: 2, 2: 4, 3: 8, 4: 16, 5: 32, 6: 64, 7: 128}

    FIRST_CONVERSION_CYCLES = 25
    NORMAL_CONVERSION_CYCLES = 13

    def __init__(self, parent, name, port: MemoryInterface,
                 ADC0, ADC1, ADC2, ADC3, ADC4, ADC5, ADC6, ADC7,
                 ADC_IRQ=None,
                 ACO_trig=None, INT0_trig=None,
                 T0_COMPA_trig=None, T0_OVF_trig=None,
                 T1_COMPB_trig=None, T1_OVF_trig=None, T1_CAPT_trig=None):
        super().__init__(parent, name)

        self.port0 = self.addInterfaceSink('port', port)

        # --- Channel inputs (see class docstring: pre-quantized 10-bit
        # codes, 0-1023, not real analog voltages) ---
        self.ADC0 = self.addIn('ADC0', ADC0)
        self.ADC1 = self.addIn('ADC1', ADC1)
        self.ADC2 = self.addIn('ADC2', ADC2)
        self.ADC3 = self.addIn('ADC3', ADC3)
        self.ADC4 = self.addIn('ADC4', ADC4)
        self.ADC5 = self.addIn('ADC5', ADC5)
        self.ADC6 = self.addIn('ADC6', ADC6)
        self.ADC7 = self.addIn('ADC7', ADC7)
        self._channel_wires = {
            0: self.ADC0, 1: self.ADC1, 2: self.ADC2, 3: self.ADC3,
            4: self.ADC4, 5: self.ADC5, 6: self.ADC6, 7: self.ADC7,
        }

        # --- Interrupt output (ADIF & ADIE -- see SimpleInterruptUnit,
        # which expects each source wire to already reflect "fire now",
        # not just the raw flag) -- optional, defaults to an internal
        # unconnected wire so ADC can be built/tested standalone before
        # any interrupt-controller integration exists.
        def _out1(w, nm):
            if w is None:
                w = py4hw.Wire(self, nm, 1)
            return self.addOut(nm, w)

        def _in1(w, nm):
            if w is None:
                w = py4hw.Wire(self, nm, 1)
                w.put(0)
            return self.addIn(nm, w)

        self.ADC_IRQ = _out1(ADC_IRQ, 'ADC_IRQ')

        # --- Auto-trigger source inputs (ADTS2:0 selects one of these;
        # a rising edge on the selected wire starts a conversion when
        # ADATE=1). Optional, same default-dummy-wire pattern as above --
        # real cross-peripheral wiring (Timer0/Timer1/Analog Comparator/
        # INT0) is top-level-integration work, out of scope here.
        self.ACO_trig = _in1(ACO_trig, 'ACO_trig')
        self.INT0_trig = _in1(INT0_trig, 'INT0_trig')
        self.T0_COMPA_trig = _in1(T0_COMPA_trig, 'T0_COMPA_trig')
        self.T0_OVF_trig = _in1(T0_OVF_trig, 'T0_OVF_trig')
        self.T1_COMPB_trig = _in1(T1_COMPB_trig, 'T1_COMPB_trig')
        self.T1_OVF_trig = _in1(T1_OVF_trig, 'T1_OVF_trig')
        self.T1_CAPT_trig = _in1(T1_CAPT_trig, 'T1_CAPT_trig')
        self._trigger_wires = {
            1: self.ACO_trig, 2: self.INT0_trig, 3: self.T0_COMPA_trig,
            4: self.T0_OVF_trig, 5: self.T1_COMPB_trig, 6: self.T1_OVF_trig,
            7: self.T1_CAPT_trig,
        }
        self._prev_trigger_level = {k: 0 for k in self._trigger_wires}

        # --- Registers ---
        self.ADMUX = 0
        self.ADMUX_addr_LS = 0x7C

        self.ADCSRA = 0
        self.ADCSRA_addr_LS = 0x7A

        self.ADCH = 0
        self.ADCH_addr_LS = 0x79
        self.ADCL = 0
        self.ADCL_addr_LS = 0x78

        self.ADCSRB = 0
        self.ADCSRB_addr_LS = 0x7B

        self.DIDR0 = 0
        self.DIDR0_addr_LS = 0x7E

        self.ADDR = 0

        # --- Parsed control fields (refreshed every clock() from the
        # raw register ints above) ---
        self.MUX = 0
        self.REFS = 0
        self.ADLAR = 0
        self.ADPS = 0
        self.ADIE = 0
        self.ADIF = 0
        self.ADATE = 0
        self.ADSC = 0
        self.ADEN = 0
        self.ADTS = 0
        self.ACME = 0

        # --- Conversion state machine ---
        self.state = 'IDLE'                # 'IDLE' | 'CONVERTING'
        self.conv_cycles_remaining = 0      # in ADC-clock cycles
        self.adc_prescaler_counter = 0
        self.first_conversion_pending = True   # True until ADEN's first
                                                # conversion has completed
        self.prev_ADEN = 0
        self.prev_ADSC_written = 0          # edge-detect a software ADSC write
        self.latched_mux = 0                # channel latched at conversion start
        self.latched_adlar = 0
        self.result = 0                     # 10-bit conversion result

        # ADCL-read lock (datasheet: reading ADCL blocks ADCH/ADCL from
        # being updated by a completing conversion until ADCH is read)
        self.adcl_read_lock = False

        self._adif_out = 0

    # -------------------------------------------------------------------
    def Memory_access(self):
        self.ADDR = self.port0.address.get()

        if (self.ADDR == self.ADMUX_addr_LS) and self.port0.instype.get() == 1:
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.ADMUX & 0b11101111)  # bit4 reserved, reads 0
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.ADMUX = self.port0.write_data.get() & 0b11101111
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)

        elif (self.ADDR == self.ADCSRA_addr_LS) and self.port0.instype.get() == 1:
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.ADCSRA)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                incoming = self.port0.write_data.get()
                # ADIF (bit4): write-one-to-clear, like a real flag bit --
                # NOT a plain overwrite. Every other bit (ADEN/ADSC/ADATE/
                # ADIE/ADPS2:0) is a normal read/write bit, taken directly
                # from the incoming byte.
                new_adif = self.ADCSRA & 0b00010000
                if incoming & 0b00010000:
                    new_adif = 0
                self.ADCSRA = (incoming & 0b11101111) | new_adif
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)

        elif (self.ADDR == self.ADCH_addr_LS) and self.port0.instype.get() == 1:
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.ADCH)
                self.port0.resp.prepare(1)
                # Reading ADCH releases the lock ADCL's read set (real
                # datasheet atomicity mechanism -- see class docstring).
                self.adcl_read_lock = False
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                # Real hardware: ADCH/ADCL have no documented write
                # function (they're conversion-result outputs). Ack the
                # bus transaction so a stray write doesn't hang the CPU,
                # but don't let it perturb the conversion result.
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)

        elif (self.ADDR == self.ADCL_addr_LS) and self.port0.instype.get() == 1:
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.ADCL)
                self.port0.resp.prepare(1)
                self.adcl_read_lock = True
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)

        elif (self.ADDR == self.ADCSRB_addr_LS) and self.port0.instype.get() == 1:
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.ADCSRB & 0b01000111)  # bit7, bits5:3 reserved
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.ADCSRB = self.port0.write_data.get() & 0b01000111
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)

        elif (self.ADDR == self.DIDR0_addr_LS) and self.port0.instype.get() == 1:
            if (self.port0.read.get() == 1) and (self.port0.write.get() == 0):
                self.port0.read_data.prepare(self.DIDR0 & 0b00111111)
                self.port0.resp.prepare(1)
            elif (self.port0.read.get() == 0) and (self.port0.write.get() == 1):
                self.DIDR0 = self.port0.write_data.get() & 0b00111111
                self.port0.resp.prepare(1)
            else:
                self.port0.resp.prepare(0)
        else:
            self.port0.resp.prepare(0)

    # -------------------------------------------------------------------
    def Parse_control_registers(self):
        self.MUX = self.ADMUX & 0b1111
        self.ADLAR = (self.ADMUX >> 5) & 0b1
        self.REFS = (self.ADMUX >> 6) & 0b11

        self.ADPS = (self.ADCSRA & 0b111)
        self.ADIE = (self.ADCSRA >> 3) & 0b1
        self.ADIF = (self.ADCSRA >> 4) & 0b1
        self.ADATE = (self.ADCSRA >> 5) & 0b1
        self.ADSC = (self.ADCSRA >> 6) & 0b1
        self.ADEN = (self.ADCSRA >> 7) & 0b1

        self.ADTS = self.ADCSRB & 0b111
        self.ACME = (self.ADCSRB >> 6) & 0b1

    # -------------------------------------------------------------------
    def _sample_channel(self, mux):
        """Real datasheet channel semantics for the part of MUX3:0 this
        model implements -- see class docstring for the deliberate scope
        cut on the bandgap/differential channels."""
        if 0 <= mux <= 7:
            raw = self._channel_wires[mux].get()
            return raw & 0x3FF
        if mux == 0b1111:  # GND
            return 0
        # 0b1110 (1.1V bandgap) and 0b1000-0b1101 (differential, TQFP-
        # only) -- explicitly out of scope, see class docstring.
        return 0

    def _start_conversion(self):
        self.state = 'CONVERTING'
        self.latched_mux = self.MUX
        self.latched_adlar = self.ADLAR
        if self.first_conversion_pending:
            self.conv_cycles_remaining = self.FIRST_CONVERSION_CYCLES
        else:
            self.conv_cycles_remaining = self.NORMAL_CONVERSION_CYCLES
        # ADSC reads back as 1 for the duration of the conversion --
        # ensure it's set even when hardware (auto-trigger), not
        # software, initiated this conversion.
        self.ADCSRA |= 0b01000000

    def _complete_conversion(self):
        self.result = self._sample_channel(self.latched_mux)
        self.first_conversion_pending = False

        if not self.adcl_read_lock:
            if self.latched_adlar:
                self.ADCH = (self.result >> 2) & 0xFF
                self.ADCL = (self.result << 6) & 0xC0
            else:
                self.ADCH = (self.result >> 8) & 0x03
                self.ADCL = self.result & 0xFF
        # else: real hardware behavior -- conversion result is held
        # internally and ADCH/ADCL simply aren't updated this cycle,
        # deliberately dropping this sample rather than corrupting a
        # 16-bit read in progress. (Matches the datasheet exactly: the
        # *next* completed conversion after ADCH is finally read will be
        # the one that lands in the registers.)

        # ADIF sets unconditionally on completion -- see class docstring
        # for why this deliberately does NOT follow Timers.py's
        # documented (and known-deviating) "flag only sets if the
        # enable bit is set" convention.
        self.ADCSRA |= 0b00010000

        if self.ADATE and self.ADTS == 0:
            # Free running: immediately ready to reconvert, ADSC stays 1.
            self.state = 'IDLE'
        else:
            # Single conversion or triggered mode: ADSC clears, wait for
            # the next software write / trigger edge.
            self.ADCSRA &= 0b10111111
            self.state = 'IDLE'

    def _check_start_conditions(self):
        # Software-initiated: ADSC written 1 (edge, not level -- so this
        # doesn't re-fire every cycle ADSC happens to read 1, e.g. while
        # a conversion it started is still running).
        adsc_now = (self.ADCSRA >> 6) & 0b1
        software_edge = (adsc_now == 1) and (self.prev_ADSC_written == 0)
        self.prev_ADSC_written = adsc_now

        if self.state == 'CONVERTING':
            return

        if not self.ADEN:
            return

        if self.ADATE:
            if self.ADTS == 0:
                # Free running mode: once started (ADSC written once),
                # _complete_conversion() already leaves ADSC=1 and
                # state='IDLE' so the very next cycle here restarts it
                # with no further edge needed.
                if adsc_now:
                    self._start_conversion()
                return
            else:
                # Auto-trigger on one of the six hardware sources.
                trig_wire = self._trigger_wires[self.ADTS]
                level = trig_wire.get() & 1
                prev = self._prev_trigger_level[self.ADTS]
                self._prev_trigger_level[self.ADTS] = level
                if (prev == 0) and (level == 1):
                    self._start_conversion()
                return

        # ADATE=0: plain single-conversion mode, purely software-started.
        if software_edge:
            self._start_conversion()

    def _advance_conversion(self):
        if self.state != 'CONVERTING':
            return

        # ADC clock derived from the system clock via ADPS2:0 (see
        # _PRESCALER_TABLE) -- same whole-system-clock-cycle counting
        # convention Timers.py's own prescaler uses.
        divider = self._PRESCALER_TABLE[self.ADPS]
        self.adc_prescaler_counter += 1
        if self.adc_prescaler_counter >= divider:
            self.adc_prescaler_counter = 0
            self.conv_cycles_remaining -= 1
            if self.conv_cycles_remaining <= 0:
                self._complete_conversion()

    # -------------------------------------------------------------------
    def update_outputs(self):
        self._adif_out = ((self.ADCSRA >> 4) & 0b1) & self.ADIE
        self.ADC_IRQ.prepare(self._adif_out)

    def clock(self):
        self.Memory_access()
        self.Parse_control_registers()

        # Turning the ADC off aborts any in-progress conversion and
        # resets the "next conversion is the extended 25-cycle one"
        # state, exactly as a real power-down/re-enable would (datasheet:
        # "If a conversion is in progress when it is switched off, the
        # conversion is terminated").
        if self.prev_ADEN == 1 and self.ADEN == 0:
            self.state = 'IDLE'
            self.conv_cycles_remaining = 0
            self.adc_prescaler_counter = 0
            self.ADCSRA &= 0b10111111  # ADSC cleared
        if self.prev_ADEN == 0 and self.ADEN == 1:
            self.first_conversion_pending = True
        self.prev_ADEN = self.ADEN

        self._check_start_conditions()
        self._advance_conversion()
        # Refresh parsed fields once more -- _start_conversion()/
        # _complete_conversion() above may have changed ADCSRA
        # (ADSC/ADIF) after the first Parse_control_registers() call.
        self.Parse_control_registers()
        self.update_outputs()


# Backward-compatible alias: nothing in this project referenced
# ADCBehavioral by name (grepped before this rewrite), but kept as a
# zero-cost alias in case any external/future code does.
ADCBehavioral = ADC
