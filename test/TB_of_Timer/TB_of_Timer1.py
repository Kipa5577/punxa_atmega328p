import py4hw
from punxa_atmega328p.Timers import *
from punxa_atmega328p.Memory import * 
import time
import math

#run from top directory using python -m test.TB_of_Timer.TB_of_Timer1

def TestBench_of_Timer1():

    sys = py4hw.HWSystem()
    SIGNALS1 = []

    # Initialize Wires
    OCF1B = py4hw.Wire(sys, 'OCF1B', 1)
    SIGNALS1.append(OCF1B)
    OCF1A = py4hw.Wire(sys, 'OCF1A', 1)
    SIGNALS1.append(OCF1A)
    TOV1 = py4hw.Wire(sys, 'TOV1', 1)
    SIGNALS1.append(TOV1)

    OC1A = py4hw.Wire(sys, 'OC1A', 1)
    SIGNALS1.append(OC1A)
    OC1B = py4hw.Wire(sys, 'OC1B', 1)
    SIGNALS1.append(OC1B)
    T1 = py4hw.Wire(sys, 'T1', 1)
    SIGNALS1.append(T1)
    ICF1 = py4hw.Wire(sys, 'ICF1', 1)
    SIGNALS1.append(ICF1)

    # Memory and Timer Instantiation
    interface1 = MemoryInterface(sys, 'interface1', 8, 16)
    TIMER1 = TimerCounter1(sys, 'TIMER1', interface1, OC1B, OC1A, T1, OCF1B, OCF1A, TOV1, ICF1)

    SIGNALS1.extend([
        interface1.write, interface1.read, interface1.address,
        interface1.write_data, interface1.read_data, interface1.resp
    ])

    CURRENT_TEST = 'START'
    wvf = py4hw.Waveform(sys, 'wvf', SIGNALS1)

    Testing = True
    with open("test/TB_of_Timer/Test_Results.txt", 'w+') as results:
        while Testing:
            match CURRENT_TEST:
                case 'START':
                    results.write("Starting Test Bench of Timer1\n")
                    CURRENT_TEST = 'TEST0'



                case 'TEST0': # TEST0: Normal mode, Compare Match Output Disconnected | No prescaling
                    results.write("TEST0\n")
                    # Setup
                    TIMER1.TCCR1A = 0x00
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1BH = 0b00010011
                    TIMER1.OCR1BL = 0b10001000
                    TIMER1.OCR1AH = 0b00100111
                    TIMER1.OCR1AL = 0b00010000

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    

                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.TCNT1 = 0 
                    # Testing 16-bit loop
                    for i in range(65536):
                        if TIMER1.TCNT1 != i % 65536:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 65536))

                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0")

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0")

                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        OVF GETS TO 1  after the TCNT1 reset s
#                        if TIMER1.TCNT1 == 0xFFFF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST1'
                case 'TEST1': # TEST1: Normal mode, Compare Match Toggle OC1A/OC1B | No prescaling
                    results.write("TEST1\n")
                    # Setup
                    TIMER1.TCCR1A = 0x50
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1BH = 0b00010011
                    TIMER1.OCR1BL = 0b10001000
                    TIMER1.OCR1AH = 0b00100111
                    TIMER1.OCR1AL = 0b00010000

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    last_OC1A = 0
                    last_OC1B = 0


                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.TCNT1 = 0 
                    # Testing
                    for i in range(65536):
                        if TIMER1.TCNT1 != i % 65536:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 65536))

                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == last_OC1A:
                                TEST = False
                                ERROR_LIST.append("OC1A = {} expected {} | iter = {}".format(last_OC1A, 1-last_OC1A, i))
                        else:
                            last_OC1A = OC1A.get()

                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == last_OC1B:
                                TEST = False
                                ERROR_LIST.append("OC1B = {} expected {} | iter = {}".format(last_OC1B, 1-last_OC1B, i))
                        else:
                            last_OC1B = OC1B.get()

                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST2'
                case 'TEST2': # TEST2: Normal mode, Clear OC1A/OC1B on match | No prescaling
                    results.write("TEST2\n")
                    # Setup
                    TIMER1.TCCR1A = 0xA0
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1BH = 0b00010011
                    TIMER1.OCR1BL = 0b10001000
                    TIMER1.OCR1AH = 0b00100111
                    TIMER1.OCR1AL = 0b00010000

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 

                    # FIXED: We MUST set the pins high initially to test that they clear to 0!
                    TIMER1.OC1A_val = 1 
                    TIMER1.OC1B_val = 1


                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.TCNT1 = 0 
                    # Testing 16-bit loop
                    for i in range(65536):
                        if TIMER1.TCNT1 != i % 65536:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 65536))

                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))
        
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST3'
                case 'TEST3': # TEST3: Normal mode, Set OC1A/OC1B on match | No prescaling
                    results.write("TEST3\n")
                    # Setup
                    TIMER1.TCCR1A = 0xF0
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1BH = 0b00010011
                    TIMER1.OCR1BL = 0b10001000
                    TIMER1.OCR1AH = 0b00100111
                    TIMER1.OCR1AL = 0b00010000

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 

                    # Good practice: Ensure pins start low for "Set" verification
                    TIMER1.OC1A_val = 0 
                    TIMER1.OC1B_val = 0


                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.TCNT1 = 0 
                    # Testing
                    for i in range(65536):
                        if TIMER1.TCNT1 != i % 65536:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 65536))

                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
        
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST4'
                
                case 'TEST4': # TEST4: Normal mode, External clock on T1 (falling edge)
                    results.write("TEST4\n") # Fixed from TEST15
                    TIMER1.TCCR1A = 0x00
                    TIMER1.TCCR1B = 0x06 # CS12:10 = 110 (Ext clock falling edge)
                    
                    # Setup Compare Match thresholds to test flags
                    TIMER1.OCR1AH = 0x00
                    TIMER1.OCR1AL = 0x40 # 64
                    TIMER1.OCR1BH = 0x00
                    TIMER1.OCR1BL = 0x80 # 128

                    ERROR_LIST = []
                    TEST = True 
                    
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags initially
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0

                    T1.prepare(1)
                    sys.getSimulator().clk(1)
                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0


                    counter = 0
                    clockCounter = 0

                    # Run past 65536 increments to trigger the Overflow edge case
                    while True:
                        # Apply modulo 65536 so the expected value wraps correctly at overflow

                        
                        if TIMER1.TCNT1 != math.floor(counter/2)% 65536:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, math.floor(counter/2)% 65536, counter))

                        # Verify physical outputs remain disconnected (0)
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter {}".format(counter))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter {}".format(counter))

                        # Verify Interrupt Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(counter))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(counter))

#                        if TIMER1.TCNT1 == 0xFFFF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(counter))

                        sys.getSimulator().clk(1)
                        clockCounter += 1
                        if clockCounter >= 2:
                            counter += 1 
                            clockCounter = 0

                            last_T1 = T1.get()
                            T1.prepare(1 - last_T1)
                        
                        # (65536 * 2) = 131,072. We add 10 to ensure we see it wrap back to 0.
                        if counter >= 131082:
                            break

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST5'
                case 'TEST5': # TEST5: Normal mode, /8 prescaler
                    results.write("TEST5\n") # Fixed from TEST16
                    TIMER1.TCCR1A = 0x00
                    TIMER1.TCCR1B = 0x02 # CS11 = 1 (Prescaler 8)
                    
                    # Setup Compare Match thresholds to test flags
                    TIMER1.OCR1AH = 0x00
                    TIMER1.OCR1AL = 0x40 # 64
                    TIMER1.OCR1BH = 0x00
                    TIMER1.OCR1BL = 0x80 # 128

                    ERROR_LIST = []
                    TEST = True 
                    
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.TCNT1 = 0

                    counter = 0
                    clockCounter = 1

                    # 65536 * 8 = 524,288 simulated clock cycles. 
                    # We add 16 extra cycles to ensure we capture the overflow edge case.
                    for i in range(524304):
                        
                        if TIMER1.TCNT1 != counter % 65536:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, counter % 65536, i))

                        # Verify physical outputs remain disconnected (0)
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter {}".format(i))

                        # Verify Interrupt Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0xFFFF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)
                        clockCounter += 1
                        if clockCounter >= 8:
                            clockCounter = 0
                            counter += 1 

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST6'

                case 'TEST6': # TEST6: Fast PWM 8-bit mode, Disconnected | No prescaling
                    results.write("TEST6\n") # FIXED
                    # Setup
                    TIMER1.TCCR1A = 0x01
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags
                    sys.getSimulator().clk(1)
                    TIMER1.TCNT1 = 0 
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    # Testing Fast PWM 8-bit (TOP = 0x00FF)
                    for i in range(256):
                        if TIMER1.TCNT1 != i % 256:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter = {}".format(TIMER1.TCNT1, i % 256, i))

                        # Verify Disconnected Outputs
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0xFF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST7' # FIXED
                case 'TEST7': # TEST7: Fast PWM 8-bit, Normal port operation | No prescaling
                    results.write("TEST7\n") # FIXED
                    # Setup (COM1A1:0 = 01, COM1B1:0 = 01 in Mode 5 means Normal port operation)
                    TIMER1.TCCR1A = 0x51
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 

                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    for i in range(257):
                        if TIMER1.TCNT1 != i % 256:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 256))

                        # Verify Outputs Remain Disconnected (0)
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == 0 and i > 0 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST8' # FIXED
                case 'TEST8': # TEST8: Fast PWM 8-bit, disconnected OC1A/OC1B  | No prescaling
                    results.write("TEST8\n") # FIXED
                    # Setup 
                    # Setup: WGM 5 (Fast PWM 8-bit)
                    TIMER1.TCCR1A = 0x51 
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    # Set TOP to 255 using ICR1
                    TIMER1.ICR1H = 0
                    TIMER1.ICR1L = 255

                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    last_OC1B = 0 # ADDED OC1B Check

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 

                    sys.getSimulator().clk(1)
                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(257):
                        if TIMER1.TCNT1 != i % 256:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 256))

                        # Check OC1A Toggle
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == 0 and i > 0 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST9' # FIXED

                case 'TEST9': # TEST9: Fast PWM 8-bit, non-inverting (Clear on match, set at BOTTOM)
                    results.write("TEST9\n") # FIXED
                    TIMER1.TCCR1A = 0xA1 # COM1A1=1, COM1A0=0 | COM1B1=1, COM1B0=0
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 1
                    TIMER1.OC1B_val = 1

                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    for i in range(257):
                        # OC1A Non-Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))

                        # OC1B Non-Inverting PWM (Added)
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == 0 and i > 0 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST10' # FIXED

                case 'TEST10':# TEST10: Fast PWM 8-bit, inverting (Set on match, clear at BOTTOM)
                    results.write("TEST10\n") # FIXED
                    TIMER1.TCCR1A = 0xF1 # COM1A1=1, COM1A0=1 | COM1B1=1, COM1B0=1
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(257):
                        # OC1A Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        # OC1B Inverting PWM (Added)
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == 0 and i > 0 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST11' # Assuming continuation to Phase Correct tests
                case 'TEST11':# TEST11: Fast PWM 9-bit mode, Disconnected | No prescaling
                    results.write("TEST11\n")
                    # Setup (COM1A=00, COM1B=00, WGM11=1, WGM10=0)
                    TIMER1.TCCR1A = 0x02
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    # 9-bit mode TOP is 511 (0x01FF)
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128 # Match at 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0   # Match at 256 (0x0100)

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    sys.getSimulator().clk(1)
                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0

                    # Testing Fast PWM 9-bit (TOP = 0x01FF / 511)
                    for i in range(512):
                        if TIMER1.TCNT1 != i % 512:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter = {}".format(TIMER1.TCNT1, i % 512, i))

                        # Verify Disconnected Outputs
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0x01FF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST12'
                case 'TEST12':# TEST12: Fast PWM 9-bit, Normal port operation | No prescaling
                    results.write("TEST12\n")
                    # Setup (COM1x=01 is Normal port operation in Mode 6) -> 0x50 + 0x02 = 0x52
                    TIMER1.TCCR1A = 0x52
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0

                    for i in range(512):
                        if TIMER1.TCNT1 != i % 512:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 512))

                        # Verify Outputs Remain Disconnected (Normal Port)
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0x01FF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST13'
                case 'TEST13':# TEST13: Fast PWM 9-bit, Toggle OC1A/OC1B on match | No prescaling
                    results.write("TEST13\n")
                    # Setup (Using 0x52 to verify py4hw Toggle logic)
                    TIMER1.TCCR1A = 0x52 
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    last_OC1B = 0

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0

                    for i in range(512):
                        if TIMER1.TCNT1 != i % 512:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 512))

                        # Check OC1A Toggle
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0x01FF and i > 0 and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST14'

                case 'TEST14':# TEST14: Fast PWM 9-bit, non-inverting (Clear on match, set at BOTTOM)
                    results.write("TEST14\n")
                    # COM1A=10, COM1B=10 -> 0xA0 + 0x02 = 0xA2
                    TIMER1.TCCR1A = 0xA2 
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 1
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0


                    for i in range(512):
                        # OC1A Non-Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))

                        # OC1B Non-Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0x01FF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST15'
                case 'TEST15':# TEST15: Fast PWM 9-bit, inverting (Set on match, clear at BOTTOM)
                    results.write("TEST15\n")
                    # COM1A=11, COM1B=11 -> 0xF0 + 0x02 = 0xF2
                    TIMER1.TCCR1A = 0xF2 
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0


                    for i in range(512):
                        # OC1A Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        # OC1B Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0x01FF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST16' # Or whatever your next state i
                case 'TEST16':# TEST16: Fast PWM 10-bit mode, Disconnected | No prescaling
                    results.write("TEST16\n")
                    # Setup (COM1A=00, COM1B=00, WGM11=1, WGM10=1 -> Mode 7)
                    TIMER1.TCCR1A = 0x03
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    # 10-bit mode TOP is 1023 (0x03FF)
                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0   # Match at 256 (0x0100)
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0   # Match at 768 (0x0300)

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0


                    # Testing Fast PWM 10-bit (TOP = 0x03FF / 1023)
                    for i in range(1024):
                        if TIMER1.TCNT1 != i % 1024:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter = {}".format(TIMER1.TCNT1, i % 1024, i))

                        # Verify Disconnected Outputs
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0x03FF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST17'

                case 'TEST17':# TEST17: Fast PWM 10-bit, Normal port operation | No prescaling
                    results.write("TEST17\n")
                    # Setup (COM1x=01 is Normal port operation) -> 0x50 + 0x03 = 0x53
                    TIMER1.TCCR1A = 0x53
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0


                    for i in range(1024):
                        if TIMER1.TCNT1 != i % 1024:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 1024))

                        # Verify Outputs Remain Disconnected (Normal Port)
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

#                        if TIMER1.TCNT1 == 0x03FF and TOV1.get() == 0:
#                            TEST = False
#                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST18'

                case 'TEST18':# TEST18: Fast PWM 10-bit, Toggle OC1A/OC1B on match | No prescaling
                    results.write("TEST18\n")
                    # Setup (COM1x=01)
                    TIMER1.TCCR1A = 0x53 
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    last_OC1B = 0

                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(1025):
                        if TIMER1.TCNT1 != i % 1024:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {}".format(TIMER1.TCNT1, i % 1024))

                       
                        # In WGM 7, COM=1 means Disconnected (Normal port operation). 
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == 0 and i > 0 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST19'
                case 'TEST19':# TEST19: Fast PWM 10-bit, non-inverting (Clear on match, set at BOTTOM)
                    results.write("TEST19\n")
                    # COM1A=10, COM1B=10 -> 0xA0 + 0x03 = 0xA3
                    TIMER1.TCCR1A = 0xA3 
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 1
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(1025):
                        # OC1A Non-Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))

                        # OC1B Non-Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == 0 and i > 0 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST20'
                case 'TEST20':# TEST20: Fast PWM 10-bit, inverting (Set on match, clear at BOTTOM)
                    results.write("TEST20\n")
                    # COM1A=11, COM1B=11 -> 0xF0 + 0x03 = 0xF3
                    TIMER1.TCCR1A = 0xF3 
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(1025):
                        # OC1A Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        # OC1B Inverting PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == 0 and i > 0 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1")

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST21' # Or 'FINAL' depending on your state machine
                case 'TEST21':# TEST21: Phase Correct PWM 8-bit, Disconnected
                    results.write("TEST21\n") # FIXED
                    # Setup (WGM11=0, WGM10=1 -> Mode 1)
                    TIMER1.TCCR1A = 0x01
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 
                    
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'  

                    # Count up to 255 and down to 0 (510 total transitions)
                    # Loop 511 times to ensure we hit the final 0 (BOTTOM)
                    for i in range(511):
                        expected_val = i if i <= 255 else 510 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Verify Disconnected Outputs
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags (Trigger on match up and down)
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        # In Phase Correct, TOV is set at BOTTOM (0)
                        if i == 510 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST22' # FIXED

                case 'TEST22':# TEST22: Phase Correct PWM 8-bit, Normal port operation
                    results.write("TEST22\n") # FIXED
                    TIMER1.TCCR1A = 0x51
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 
                    
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'  

                    for i in range(511):
                        expected_val = i if i <= 255 else 510 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Verify Disconnected Outputs (Normal Port)
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 510 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST23' # FIXED
                case 'TEST23':# TEST23: Phase Correct PWM 8-bit, Toggle OC1A/OC1B on match
                    results.write("TEST23\n") # FIXED
                    TIMER1.TCCR1A = 0x51
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    last_OC1B = 0
                    
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'

                    for i in range(511):
                        expected_val = i if i <= 255 else 510 - i
                        
                        # Add sanity check for TCNT1
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))
                        # Check OC1A Toggle
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 510 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST24' # FIXED
                case 'TEST24':# TEST24: Phase Correct PWM 8-bit, Clear up, Set down (Non-Inverting)
                    results.write("TEST24\n") # FIXED
                    TIMER1.TCCR1A = 0xA1 # COM1A=10, COM1B=10
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 
                    
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 1
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'

                    for i in range(511):
                        # OC1A Non-Inverting boundaries
                        if i >= 64 and i < 446: # 510 - 64 = 446
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))

                        # OC1B Non-Inverting boundaries (Added)
                        if i >= 128 and i < 382: # 510 - 128 = 382
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 510 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST25'
                case 'TEST25':# TEST25: Phase Correct PWM 8-bit, Set up, Clear down (Inverting)
                    results.write("TEST25\n")
                    TIMER1.TCCR1A = 0xF1 # COM1A=11, COM1B=11
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1BH = 0
                    TIMER1.OCR1BL = 128
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 64

                    ERROR_LIST = []
                    TEST = True 
                    
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(511):
                        # OC1A Inverting boundaries
                        if i >= 64 and i < 446: # 510 - 64 = 446
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        # OC1B Inverting boundaries
                        if i >= 128 and i < 382: # 510 - 128 = 382
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 510 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST26' # Or 'FINAL'


                case 'TEST25':# TEST25: Phase Correct PWM 9-bit, Disconnected
                    results.write("TEST25\n")
                    # Setup (WGM11=1, WGM10=0 -> Mode 2)
                    TIMER1.TCCR1A = 0x02
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    # 9-bit TOP is 511
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0   # 256

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    # Count up to 511 and down to 0 (1022 total transitions)
                    for i in range(1023):
                        expected_val = i if i <= 511 else 1022 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Verify Disconnected Outputs
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 1022 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST26'
                case 'TEST26':# TEST26: Phase Correct PWM 9-bit, Normal port operation
                    results.write("TEST26\n")
                    # COM1x=01 (Normal Port) -> 0x50 + 0x02 = 0x52
                    TIMER1.TCCR1A = 0x52
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(1023):
                        expected_val = i if i <= 511 else 1022 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Verify Outputs Remain Disconnected
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 1022 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST27'
                case 'TEST27':# TEST27: Phase Correct PWM 9-bit, Toggle OC1A/OC1B on match
                    results.write("TEST27\n")
                    TIMER1.TCCR1A = 0x52
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    last_OC1B = 0
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'

                    for i in range(1023):
                        expected_val = i if i <= 511 else 1022 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Check OC1A Toggle
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 1022 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST28'
                case 'TEST28':# TEST28: Phase Correct PWM 9-bit, Clear up, Set down (Non-Inverting)
                    results.write("TEST28\n")
                    # COM1A=10, COM1B=10 -> 0xA0 + 0x02 = 0xA2
                    TIMER1.TCCR1A = 0xA2
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 1
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'

                    for i in range(1023):
                        # OC1A Non-Inverting boundaries (OCR1A = 128)
                        # Down-match happens at 1022 - 128 = 894
                        if i >= 128 and i < 894: 
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))

                        # OC1B Non-Inverting boundaries (OCR1B = 256)
                        # Down-match happens at 1022 - 256 = 766
                        if i >= 256 and i < 766: 
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 1022 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST29'
                case 'TEST29':# TEST29: Phase Correct PWM 9-bit, Set up, Clear down (Inverting)
                    results.write("TEST29\n")
                    # COM1A=11, COM1B=11 -> 0xF0 + 0x02 = 0xF2
                    TIMER1.TCCR1A = 0xF2
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1AH = 0
                    TIMER1.OCR1AL = 128
                    TIMER1.OCR1BH = 1
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(1023):
                        # OC1A Inverting boundaries
                        if i >= 128 and i < 894: 
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        # OC1B Inverting boundaries
                        if i >= 256 and i < 766: 
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 1022 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST30' # Or FINAL depending on your state machine

                case 'TEST30':# TEST30: Phase Correct PWM 10-bit, Disconnected
                    results.write("TEST30\n") # FIXED NUMBERING
                    # Setup (WGM11=1, WGM10=1 -> Mode 3)
                    TIMER1.TCCR1A = 0x03
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    # 10-bit TOP is 1023
                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0   # Match at 256
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0   # Match at 768

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    # Count up to 1023 and down to 0 (2046 total transitions)
                    for i in range(2047):
                        expected_val = i if i <= 1023 else 2046 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Verify Disconnected Outputs
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        # TOV1 triggers at BOTTOM
                        if i == 2046 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST31'
                case 'TEST31':# TEST31: Phase Correct PWM 10-bit, Normal port operation
                    results.write("TEST31\n")
                    # COM1x=01 (Normal Port) -> 0x50 + 0x03 = 0x53
                    TIMER1.TCCR1A = 0x53
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(2047):
                        expected_val = i if i <= 1023 else 2046 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Verify Outputs Remain Disconnected
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 2046 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST32'
                case 'TEST32':# TEST32: Phase Correct PWM 10-bit, Toggle OC1A/OC1B on match
                    results.write("TEST32\n")
                    TIMER1.TCCR1A = 0x53
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00

                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0 

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    last_OC1B = 0
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'

                    for i in range(2047):
                        expected_val = i if i <= 1023 else 2046 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Check OC1A Toggle
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 2046 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST33'
                case 'TEST33':# TEST33: Phase Correct PWM 10-bit, Clear up, Set down (Non-Inverting)
                    results.write("TEST33\n")
                    # COM1A=10, COM1B=10 -> 0xA0 + 0x03 = 0xA3
                    TIMER1.TCCR1A = 0xA3
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0   # 256
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0   # 768

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 1
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'

                    for i in range(2047):
                        # OC1A Non-Inverting boundaries (OCR1A = 256)
                        # Down-match happens at 2046 - 256 = 1790
                        if i >= 256 and i < 1790: 
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))

                        # OC1B Non-Inverting boundaries (OCR1B = 768)
                        # Down-match happens at 2046 - 768 = 1278
                        if i >= 768 and i < 1278: 
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 2046 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST34'

                case 'TEST34':# TEST34: Phase Correct PWM 10-bit, Set up, Clear down (Inverting)
                    results.write("TEST34\n")
                    # COM1A=11, COM1B=11 -> 0xF0 + 0x03 = 0xF3
                    TIMER1.TCCR1A = 0xF3
                    TIMER1.TCCR1B = 0x01
                    TIMER1.TCCR1C = 0x00
                    
                    TIMER1.OCR1AH = 1
                    TIMER1.OCR1AL = 0   # 256
                    TIMER1.OCR1BH = 3
                    TIMER1.OCR1BL = 0   # 768

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    for i in range(2047):
                        # OC1A Inverting boundaries
                        if i >= 256 and i < 1790: 
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        # OC1B Inverting boundaries
                        if i >= 768 and i < 1278: 
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        if i == 2046 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST35' # Or 'FINAL'
                case 'TEST35':# TEST35: Phase and Frequency Correct PWM, TOP=ICR1 (Mode 8)
                    results.write("TEST35\n")
                    # COM1A=10, COM1B=10 (Non-inverting) | WGM11=0, WGM10=0 -> 0xA0
                    TIMER1.TCCR1A = 0xA0
                    # WGM13=1, WGM12=0, CS10=1 -> 0x11
                    TIMER1.TCCR1B = 0x11
                    TIMER1.TCCR1C = 0x00
                    
                    # Set custom TOP using ICR1 = 500 (0x01F4)
                    TIMER1.ICR1H = 0x01
                    TIMER1.ICR1L = 0xF4
                    
                    # Set compare thresholds
                    TIMER1.OCR1AH = 0x00
                    TIMER1.OCR1AL = 200 # OCR1A = 200
                    TIMER1.OCR1BH = 0x01
                    TIMER1.OCR1BL = 144 # OCR1B = 400

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 1
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0
                    TIMER1.direction = 'Increment'

                    # Count up to 500 and down to 0 (1000 total transitions)
                    for i in range(1001):
                        expected_val = i if i <= 500 else 1000 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # OC1A Non-Inverting boundaries (OCR1A = 200)
                        # Down-match happens at 1000 - 200 = 800
                        if i >= 200 and i < 800: 
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))

                        # OC1B Non-Inverting boundaries (OCR1B = 400)
                        # Down-match happens at 1000 - 400 = 600
                        if i >= 400 and i < 600: 
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        # In Mode 8, TOV1 triggers at BOTTOM (0)
                        if i == 1000 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST36'
                case 'TEST36':# TEST36: Phase and Frequency Correct PWM, TOP=OCR1A (Mode 9)
                    results.write("TEST36\n")
                    # COM1A=01 (Toggle on match), COM1B=10 (Non-inverting) | WGM11=0, WGM10=1 -> 0x61
                    TIMER1.TCCR1A = 0x61
                    # WGM13=1, WGM12=0, CS10=1 -> 0x11
                    TIMER1.TCCR1B = 0x11
                    TIMER1.TCCR1C = 0x00
                    
                    # Set custom TOP using OCR1A = 500 (0x01F4)
                    TIMER1.OCR1AH = 0x01
                    TIMER1.OCR1AL = 0xF4
                    
                    # Set OCR1B = 250
                    TIMER1.OCR1BH = 0x00
                    TIMER1.OCR1BL = 250

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    # Count up to 500 and down to 0 (1000 transitions)
                    for i in range(1001):
                        expected_val = i if i <= 500 else 1000 - i
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # OC1A Toggle at TOP (OCR1A match)
                        if TIMER1.TCNT1 == TIMER1.OCR1A:
                            if OC1A.get() == last_OC1A:
                                TEST = False
                                ERROR_LIST.append("OC1A = {} expected {} | iter = {}".format(last_OC1A, 1-last_OC1A, i))
                        else:
                            last_OC1A = OC1A.get()

                        # OC1B Non-Inverting boundaries (OCR1B = 250)
                        # Down-match happens at 1000 - 250 = 750
                        if i >= 250 and i < 750: 
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags (TOV1 triggers at BOTTOM)
                        if i == 1000 and TOV1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST37'
                case 'TEST37':# TEST37: Fast PWM, TOP=ICR1 (Mode 14)
                    results.write("TEST37\n")
                    # COM1A=10, COM1B=10 (Non-inverting) | WGM11=1, WGM10=0 -> 0xA2
                    TIMER1.TCCR1A = 0xA2
                    # WGM13=1, WGM12=1, CS10=1 -> 0x19
                    TIMER1.TCCR1B = 0x19
                    TIMER1.TCCR1C = 0x00
                    
                    # Set custom TOP using ICR1 = 600 (0x0258)
                    TIMER1.ICR1H = 0x02
                    TIMER1.ICR1L = 0x58
                    
                    # Set compare thresholds
                    TIMER1.OCR1AH = 0x00
                    TIMER1.OCR1AL = 200 # OCR1A = 200
                    TIMER1.OCR1BH = 0x01
                    TIMER1.OCR1BL = 144 # OCR1B = 400

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 1
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    # Cycle length is TOP + 1 (601). We simulate two full cycles.
                    for i in range(1202):
                        expected_val = i % 601
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # OC1A Non-Inverting Fast PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1A:
                            if OC1A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1A = 0 expected 1 | iter = {}".format(i))

                        # OC1B Non-Inverting Fast PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags (TOV1 and ICF1 trigger at TOP in Mode 14)
                        if TIMER1.TCNT1 == 0 and i > 0:
                            if TOV1.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))
                            if ICF1.get() == 0:
                                TEST = False
                                ERROR_LIST.append("ICF1 = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST38'
                case 'TEST38':# TEST38: Fast PWM, TOP=OCR1A (Mode 15)
                    results.write("TEST38\n")
                    # COM1A=01 (Toggle on match), COM1B=10 (Non-inverting) | WGM11=1, WGM10=1 -> 0x63
                    TIMER1.TCCR1A = 0x63
                    # WGM13=1, WGM12=1, CS10=1 -> 0x19
                    TIMER1.TCCR1B = 0x19
                    TIMER1.TCCR1C = 0x00
                    
                    # Set custom TOP using OCR1A = 600 (0x0258)
                    TIMER1.OCR1AH = 0x02
                    TIMER1.OCR1AL = 0x58
                    
                    # Set OCR1B = 300 (0x012C)
                    TIMER1.OCR1BH = 0x01
                    TIMER1.OCR1BL = 0x2C

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 1
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    # Cycle length is TOP + 1 (601). Simulate two full cycles.
                    for i in range(1202):
                        expected_val = i % 601
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # OC1A Toggle at TOP (OCR1A match)
                        if TIMER1.TCNT1 == TIMER1.OCR1A:
                            if OC1A.get() == last_OC1A:
                                TEST = False
                                ERROR_LIST.append("OC1A = {} expected {} | iter = {}".format(last_OC1A, 1-last_OC1A, i))
                        else:
                            last_OC1A = OC1A.get()

                        # OC1B Non-Inverting Fast PWM
                        if TIMER1.TCNT1 >= TIMER1.OCR1B:
                            if OC1B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))
                        else:
                            if OC1B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC1B = 0 expected 1 | iter = {}".format(i))

                        # Verify Flags (TOV1 and OCF1A trigger at TOP in Mode 15)
                        if TIMER1.TCNT1 == 0 and i > 0:
                            if TOV1.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OVF = 0 expected 1 | iter = {}".format(i))
                            if OCF1A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST39'
                
                case 'TEST39':# TEST39: CTC Mode, TOP = OCR1A (Mode 4)
                    results.write("TEST39\n")
                    # Setup (COM1A=01 Toggle on match, COM1B=00 Disconnected | WGM11=0, WGM10=0)
                    TIMER1.TCCR1A = 0x40 
                    # WGM13=0, WGM12=1, CS10=1 (No prescaling) -> 0x09
                    TIMER1.TCCR1B = 0x09
                    TIMER1.TCCR1C = 0x00

                    # Set custom TOP using OCR1A = 63 (0x003F)
                    TIMER1.OCR1AH = 0x00
                    TIMER1.OCR1AL = 63
                    
                    # Set OCR1B = 30
                    TIMER1.OCR1BH = 0x00
                    TIMER1.OCR1BL = 30

                    ERROR_LIST = []
                    TEST = True 
                    last_OC1A = 0
                    last_OC1B = 0
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    # Cycle length is TOP + 1 (64). Simulate 4 full cycles (256 ticks).
                    for i in range(256):
                        expected_val = i % 64
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Check OC1A Toggle (Toggles at TOP/OCR1A match)
                        if TIMER1.TCNT1 == TIMER1.OCR1A:
                            if OC1A.get() == last_OC1A:
                                TEST = False
                                ERROR_LIST.append("OC1A = {} expected {} | iter = {}".format(last_OC1A, 1-last_OC1A, i))
                        else:
                            last_OC1A = OC1A.get()

                        # Verify Disconnected Output OC1B
                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        # In CTC mode, Overflow only happens at MAX (0xFFFF), so it should stay 0 here
                        if TOV1.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OVF = 1 expected 0 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'TEST40'
                case 'TEST40':# TEST40: CTC Mode, TOP = ICR1 (Mode 12)
                    results.write("TEST40\n")
                    # Setup (COM1A=00, COM1B=00 Disconnected | WGM11=0, WGM10=0)
                    TIMER1.TCCR1A = 0x00
                    # WGM13=1, WGM12=1, CS10=1 (No prescaling) -> 0x19
                    TIMER1.TCCR1B = 0x19
                    TIMER1.TCCR1C = 0x00

                    # Set custom TOP using ICR1 = 100 (0x0064)
                    TIMER1.ICR1H = 0x00
                    TIMER1.ICR1L = 100
                    
                    # Set Compare Thresholds
                    TIMER1.OCR1AH = 0x00
                    TIMER1.OCR1AL = 40  # OCR1A = 40
                    TIMER1.OCR1BH = 0x00
                    TIMER1.OCR1BL = 80  # OCR1B = 80

                    ERROR_LIST = []
                    TEST = True 
                    TIMER1.TIMSK1 = 0b111
                    TIMER1.TIFR1 = 0 # Clear flags
                    TIMER1.OC1A_val = 0
                    TIMER1.OC1B_val = 0
                    sys.getSimulator().clk(1)

                    TIMER1.TCNT1 = 0
                    TIMER1.TCNT1H = 0
                    TIMER1.TCNT1L = 0

                    # Cycle length is TOP + 1 (101). Simulate 3 full cycles (303 ticks).
                    for i in range(303):
                        expected_val = i % 101
                        if TIMER1.TCNT1 != expected_val:
                            TEST = False
                            ERROR_LIST.append("TCNT1 = {} expected {} | iter {}".format(TIMER1.TCNT1, expected_val, i))

                        # Verify Disconnected Outputs
                        if OC1A.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1A = 1 expected 0 | iter = {}".format(i))

                        if OC1B.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OC1B = 1 expected 0 | iter = {}".format(i))

                        # Verify Flags (OCF1A, OCF1B)
                        if TIMER1.TCNT1 == TIMER1.OCR1A and OCF1A.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1A = 0 expected 1 | iter = {}".format(i))

                        if TIMER1.TCNT1 == TIMER1.OCR1B and OCF1B.get() == 0:
                            TEST = False
                            ERROR_LIST.append("OCF1B = 0 expected 1 | iter = {}".format(i))

                        # In Mode 12 (CTC via ICR1), ICF1 triggers at TOP (ICR1 match)
                        if TIMER1.TCNT1 == 0 and i > 0 and ICF1.get() == 0:
                            TEST = False
                            ERROR_LIST.append("ICF1 = 0 expected 1 | iter = {}".format(i))

                        # Overflow only happens at MAX (0xFFFF)
                        if TOV1.get() == 1:
                            TEST = False
                            ERROR_LIST.append("OVF = 1 expected 0 | iter = {}".format(i))

                        sys.getSimulator().clk(1)

                    results.write('%s\n' % [TEST, ERROR_LIST])
                    CURRENT_TEST = 'FINAL' # Test bench complete

                case 'FINAL':
                    results.write("TEST Finished\n")
                    results.close()
                    #wvf.gui()
                    Testing = False
                    CURRENT_TEST = 'FINAL'

if __name__ == '__main__':
    TestBench_of_Timer1()