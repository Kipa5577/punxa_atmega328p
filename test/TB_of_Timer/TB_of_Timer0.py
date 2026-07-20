import py4hw
from punxa_atmega328p.Timers import *
from punxa_atmega328p.Memory import * 
import time
import math


#run from top directory using python -m test.TB_of_Timer.TB_of_Timer0

def TestBench_of_Timer0():

    sys0 = py4hw.HWSystem()

    SIGNALS0 = []

    OCF0B = py4hw.Wire( sys0,'OCF0B',1)
    SIGNALS0.append(OCF0B)
    OCF0A = py4hw.Wire( sys0,'OCF0A',1)
    SIGNALS0.append(OCF0A)
    TOV0 = py4hw.Wire( sys0,'TOV0',1)
    SIGNALS0.append(TOV0)

    OC0A = py4hw.Wire(sys0,'OC0A',1)
    SIGNALS0.append(OC0A)
    OC0B = py4hw.Wire(sys0,'OC0B',1)
    SIGNALS0.append(OC0B)
    T0 = py4hw.Wire(sys0,'T0',1)
    SIGNALS0.append(T0)

    interface0 = MemoryInterface(sys0,'interface0',8,16)

    TIMER0 = TimerCounter0(sys0,'TIMER0',interface0,OC0B,OC0A,T0,OCF0B,OCF0A,TOV0)



    SIGNALS0.append(interface0.write)
    SIGNALS0.append(interface0.read)
    SIGNALS0.append(interface0.address)
    SIGNALS0.append(interface0.write_data)
    SIGNALS0.append(interface0.read_data)
    SIGNALS0.append(interface0.resp)

    CURRENT_TEST = 'START'

    wvf = py4hw.Waveform(sys0,'wvf',SIGNALS0)

    #sch = py4hw.Schematic(sys)
    #sch.draw()
    #sys.getSimulator().clk(len(TIMER0_WRITE_DATA_TEST))

    Testing = True
    with open("test/TB_of_Timer/Test_Results.txt",'w+') as results:
        while Testing:

            
            match CURRENT_TEST:

                case 'START':
                    print("Starting Test Bench of Timer0")

                    CURRENT_TEST = 'TEST0'
                case 'TEST0':# TEST0 :Normal mode Compare Match Output B disconnected and A disconnected (writing using Ls to load data) | No prescaling (X1)
                    results.write("TEST0\n")
                    #Setup
                    ## Loading the config values in memory
                    TIMER0.TCCR0A = 0x00
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    last_OC0A = 0
                    last_OC0B = 0

                    ## Testing
                    for i in range(255):
                        # counter test 

                        if TIMER0.TCNT0 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i%256))

                        #Output A
                        if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}".format(1,0))

                        #Output B 
                        if OC0B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0B = {} expected {}".format(1,0))

                        #Interrupt A
                        if (TIMER0.TCNT0) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER0.TCNT0) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| iteration = {}".format(0,1,i))

                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys0.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST1'
                case 'TEST1':# TEST1 :Normal mode Compare Match Output B Toggle and A Toggle (writing using Ls to load data) | No prescaling (X2)
                    results.write("TEST1\n")
                    #Setup
                    ## Loading the config values in memory
                    TIMER0.TCCR0A = 0x50
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    last_OC0A = 0
                    last_OC0B = 0

                    ## Testing
                    for i in range(255):
                        # counter test 

                        if TIMER0.TCNT0 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i%256))

                        #Output A 
                        if TIMER0.TCNT0 >= TIMER0.OCR0A:
                            if OC0A.get() == last_OC0A:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| Iteration = {}".format(last_OC0A,(1-last_OC0A),i))
                        else:
                            last_OC0A = OC0A.get()

        
                        #Output B 
                        if TIMER0.TCNT0 >= TIMER0.OCR0B:
                            if OC0B.get() == last_OC0B:# error val
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}| Iteration = {}".format(last_OC0B,(1-last_OC0B),i))
                        else:
                            last_OC0B = OC0B.get()


                        #Interrupt A
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))

                        sys0.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    ## Storing data
                    CURRENT_TEST = 'TEST2'
                case 'TEST2':# TEST2 :Normal mode Compare Match Output B Clear and A Clear (writing using Ls to load data) | No prescaling (X3)
                    results.write("TEST2\n")
                    #Setup
                    TIMER0.TCCR0A = 0xA0
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 1
                    TIMER0.OC0B_val = 1
                

                ## Testing
                    for i in range(255):
                        # counter test 

                        if TIMER0.TCNT0 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i%256))

                        #Output A 
                        if TIMER0.TCNT0 >= TIMER0.OCR0A:
                            if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| Iteration = {}".format(0,1,i))
                        else:
                            if OC0A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| Iteration = {}".format(1,0,i))
        
                        #Output B 
                        if TIMER0.TCNT0 >= TIMER0.OCR0B:
                            if OC0B.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}| Iteration = {}".format(0,1,i))
                        else:
                            if OC0B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}| Iteration = {}".format(1,0,i))

                        #Interrupt A
                        if (TIMER0.TCNT0) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER0.TCNT0) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))


                        sys0.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST3'
                case 'TEST3':# TEST3 :Normal mode Compare Match Output B Set and A Set (writing using Ls to load data) | No prescaling (X4)
                    results.write("TEST3\n")
                    #Setup
                    TIMER0.TCCR0A = 0xF0
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 0
                    TIMER0.OC0B_val = 0

                ## Testing
                    for i in range(255):
                        # counter test 

                        if TIMER0.TCNT0 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i%256))

                        #Output A 
                        if TIMER0.TCNT0 >= TIMER0.OCR0A:
                            if OC0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| Iteration = {}".format(0,1,i))
                        else:
                            if OC0A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| Iteration = {}".format(1,0,i))
        
                        #Output B 
                        if TIMER0.TCNT0 >= TIMER0.OCR0B:
                            if OC0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}| Iteration = {}".format(0,1,i))
                        else:
                            if OC0B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}| Iteration = {}".format(1,0,i))

                        #Interrupt A
                        if (TIMER0.TCNT0) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}".format(0,1))
                        #else:
                        #    if OCF0A.get() == 1:
                        #        TEST = False
                        #        ERROR_LIST.append("OCF0B = {} expected {}".format(1,0))

                        #Interrupt B 
                        if (TIMER0.TCNT0) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}".format(0,1))
                        #else:
                        #    if OCF0A.get() == 1:
                        #        TEST = False
                        #        ERROR_LIST.append("OCF0A = {} expected {}".format(1,0))
                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys0.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST4'
                case 'TEST4': # TEST4 :Fast PWM Mode mode Compare Match Output B disconnected and A disconnected (writing using Ls to load data) | No prescaling (X5)
                    results.write("TEST4\n")
                    #Setup
                    TIMER0.TCCR0A = 0x03
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 0
                    TIMER0.OC0B_val = 0

                    sys0.getSimulator().clk(1)

                ## Testing
                    for i in range(1,255):
                        # counter test 
                        if TIMER0.TCNT0 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}| iteration = {}".format(TIMER0.TCNT0,i%256))


                        #Output A
                        if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| iteration = {}".format(1,0,i))


                        #Output B 
                        if OC0B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0B = {} expected {}| iteration = {}".format(1,0,i))


                        #Interrupt A
                        if (TIMER0.TCNT0) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER0.TCNT0) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| iteration = {}".format(0,1,i))

                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys0.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST5'
                case 'TEST5':# TEST5 :Fast PWM Mode mode Compare Match Output B disconnected and A (Normal port operation, OC0A disconnected) (writing using Ls to load data) | No prescaling (X6.1)
                    results.write("TEST5\n")
                    #Setup
                    TIMER0.TCCR0A = 0x53
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 0
                    TIMER0.OC0B_val = 0

                    last_OC0A = 0
                    last_OC0B = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER0.TCNT0 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i%256))

                        #Output A
                        if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}".format(1,0))

                        #Output B 
                        if OC0B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0B = {} expected {}".format(1,0))


                        #Interrupt A
                        if (TIMER0.TCNT0) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if TIMER0.TCNT0 == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))

                        sys0.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST6'
                case 'TEST6':# TEST6 :Fast PWM Mode mode Compare Match Output B disconnected and A (Toggle OC0A on compare match.) (writing using Ls to load data) | No prescaling (X6.2)
                    results.write("TEST6\n")
                    #Setup
                    TIMER0.TCCR0A = 0x53
                    TIMER0.TCCR0B = 0x09

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                ## Testing
                    for i in range(255):
                        # counter test
                        # NOTE: TCCR0A low bits = 11 and TCCR0B.WGM02 = 1 (0x09) select
                        # WGM=7 (Fast PWM, TOP=OCR0A), NOT TOP=0xFF. TCNT0 free-runs
                        # 0..OCR0A-1 and wraps every OCR0A counts (this DUT resets
                        # TCNT0 to BOTTOM the instant it would equal TOP, so the
                        # value TOP=OCR0A itself is never observed - see TimerCounter0
                        # .Other_modes_Increment), so the expected value must be
                        # taken modulo OCR0A, not modulo 255.
                        expected_tcnt0 = i % (TIMER0.OCR0A + 1)
                        if TIMER0.TCNT0 != expected_tcnt0:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,expected_tcnt0))

                        #Output A 
                        if TIMER0.TCNT0 >= TIMER0.OCR0A:
                            if OC0A.get() == last_OC0A:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| Iteration = {}".format(last_OC0A,(1-last_OC0A),i))
                        else:
                            last_OC0A = OC0A.get()


                        if OC0B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0B = {} expected {}| Iteration = {}".format(1,0,i))


                        #Interrupt A
                        if (TIMER0.TCNT0) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if TIMER0.TCNT0 == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))

                        sys0.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST7'
                case 'TEST7':# TEST7 :Fast PWM Mode mode Compare Match Output B (Clear OC0B on compare match, set OC0B at BOTTOM,(non-inverting mode)) and A (Clear OC0A on compare match, set OC0A at BOTTOM,(non-inverting mode).) (writing using Ls to load data) | No prescaling (X7)
                    results.write("TEST7\n")
                    #Setup
                    TIMER0.TCCR0A = 0xA3
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0B_val = 1
                    TIMER0.OC0A_val = 1

                    sys0.getSimulator().clk(1)

                    TIMER0.TCNT0 = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER0.TCNT0 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i%256))

                        #Output A 
                        if TIMER0.TCNT0 >= TIMER0.OCR0A:
                            if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| Iteration = {}".format(1,0,i))
                        else:
                            if OC0A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}| Iteration = {}".format(0,1,i))
        
                        #Output B 
                        if TIMER0.TCNT0 >= TIMER0.OCR0B:
                            if OC0B.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}| Iteration = {}".format(1,0,i))
                        else:
                            if OC0B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}| Iteration = {}".format(0,1,i))

                        #Interrupt A
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| Iteration = {}".format(0,1,i))

                        #Interrupt B 
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| Iteration = {}".format(0,1,i))
                                
                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))

                        sys0.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST8'
                case 'TEST8':# TEST8 :Fast PWM Mode mode Compare Match Output B (Set OC0B on compare match, clear OC0B at BOTTOM,(inverting mode)) and A (Set OC0A on compare match, clear OC0A at BOTTOM,(inverting mode).) (writing using Ls to load data) | No prescaling (X8)
                    results.write("TEST8\n")
                    #Setup
                    TIMER0.TCCR0A = 0xF3
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0B_val = 0
                    TIMER0.OC0A_val = 0

                    sys0.getSimulator().clk(1)
                    TIMER0.TCNT0 = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER0.TCNT0 != i:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i))

                        #Output A 
                        if TIMER0.TCNT0 >= TIMER0.OCR0A:
                            if OC0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            if OC0A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(1,0,i))
        
                        #Output B 
                        if TIMER0.TCNT0 >= TIMER0.OCR0B:
                            if OC0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            if OC0B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(1,0,i))

                        #Interrupt A
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt B 
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}|Iteration {}".format(0,1,i))
                                
                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}|Iteration {}".format(0,1,i))

                        sys0.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST9'
                case 'TEST9':# TEST9 :Phase Correct PWM mode Compare Match Output B disconnected and A disconnected (writing using Ls) | No prescaling (X9)
                    results.write("TEST9\n")
                    #Setup
                    TIMER0.TCCR0A = 0x01
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0B_val = 0
                    TIMER0.OC0A_val = 0

                    sys0.getSimulator().clk(1)
                    TIMER0.TCNT0 = 0

                ## Testing
                    for i in range(255*2):
                        # counter test 

                        if i <= 255 :
                            if TIMER0.TCNT0 != i:
                                TEST = False
                                ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i))
                        else: 
                            if TIMER0.TCNT0 != (255 - (i - 255)):
                                TEST = False
                                ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,255-(i-255))) 


                        #Output A 
                        if ((TIMER0.TCNT0 >= TIMER0.OCR0A) and i<= 255) or ((TIMER0.TCNT0 <= TIMER0.OCR0A) and  i >= 255 ):
                            if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(0,1,i))
        

                        #Output B 
                        if ((TIMER0.TCNT0 >= TIMER0.OCR0B) and (i<= 255)) or ((TIMER0.TCNT0 <= TIMER0.OCR0A) and (i >= 255)):
                            if OC0B.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(0,1,i))


                        #Interrupt A
#                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
#                            if OCF0A.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF0A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration {}".format(1,0,i))


                        #Interrupt B 
#                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
#                            if OCF0B.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OCF0B = {} expected {}".format(0,1))
#                        else:
#                            if OCF0B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF0B = {} expected {}".format(1,0))
                                

                        #Interrupt OVF
#                        if (TIMER0.TCNT0) == 0xFF:
#                            if TOV0.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))


                        sys0.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST10'
                case 'TEST10':# TEST10 :Phase Correct PWM mode Compare Match Output B disconnected and A (Normal port operation, OC0A disconnected.) (writing using Ls) | No prescaling (X10.1)
                    results.write("TEST10\n")
                    #Setup
                    TIMER0.TCCR0A = 0xA3
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128


                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts


                    TIMER0.OC0B_val = 0
                    TIMER0.OC0A_val = 0
                    sys0.getSimulator().clk(1)

                    TIMER0.TCNT0 = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER0.TCNT0 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i%256))


                        #Output A 
                        if OC0A.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(0,1,i))
        

                        #Output B 
                        if OC0B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(0,1,i))


                        #Interrupt A
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF0A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration {}".format(1,0,i))


                        #Interrupt B 
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF0B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF0B = {} expected {}|Iteration {}".format(1,0,i))
                                

                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}|Iteration {}".format(0,1,i))


                        sys0.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST11'
                case 'TEST11':# TEST11 :Phase Correct PWM mode Compare Match Output B disconnected and A (Toggle OC0A on compare match.) (writing using Ls) | No prescaling (X10.2)
                    results.write("TEST11\n")
                    #Setup
                    TIMER0.TCCR0A = 0xA3
                    TIMER0.TCCR0B = 0x09

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 0
                    TIMER0.OC0B_val = 0

                    sys0.getSimulator().clk(1)

                    last_OCR0A = OC0A.get()
                    TIMER0.TCNT0 = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER0.TCNT0 != i%(TIMER0.OCR0A + 1):
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i%(TIMER0.OCR0A + 1)))

                        #Output A 
                        if ((TIMER0.TCNT0 == TIMER0.OCR0A) and i <= 255) or ((TIMER0.TCNT0 == TIMER0.OCR0A) and i>=255):
                            if OC0A.get() == last_OCR0A:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            last_OCR0A


                        #Interrupt A
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF0A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration".format(1,0,i))

                        #Interrupt B 
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}|Iteration".format(0,1,i))
#                        else:
#                            if OCF0B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF0B = {} expected {}|Iteration".format(1,0,i))
                                
                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}|Iteration".format(0,1,i))


                        sys0.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST12'
                case 'TEST12':# TEST12 :Phase Correct PWM mode Compare Match Output B (Clear OC0B on compare match when up-counting. Set OC0B on compare match when down-counting.) and A (Clear OC0A on compare match when up-counting. Set OC0A on compare match when down-counting.) (writing using Ls) | No prescaling (X11)
                    results.write("TEST12\n")
                    #Setup
                    TIMER0.TCCR0A = 0xA1
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 1
                    TIMER0.OC0B_val = 1

                    sys0.getSimulator().clk(1)

                    last_OCR0A = OC0A.get()
                    TIMER0.TCNT0 = 0

                    counter = 0
                ## Testing
                    for i in range(511):
                        # counter test 
                        if i < 255:
                            if TIMER0.TCNT0 != i:
                                TEST = False
                                ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i))
                        elif i>=255:
                            if TIMER0.TCNT0 != 255-counter:
                                TEST = False
                                ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,255-counter))
                            counter += 1

                        #Output A 
                        if  64<=i<=445:   #((TIMER0.TCNT0 >= TIMER0.OCR0A) and (i < 255)) or ((TIMER0.TCNT0 <= TIMER0.OCR0A) and (i>=255)):
                            if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(1,0,i))
                        else:
                            if OC0A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(0,1,i))
        
                        #Output B 
                        if  128<=i<=381:# (TIMER0.TCNT0 >= TIMER0.OCR0B) and i <= 255) or ((TIMER0.TCNT0 <= TIMER0.OCR0B) and i>=255):
                            if OC0B.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(1,0,i))
                        else:
                            if OC0B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt A
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF0A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF0A = {} expected {}".format(1,0))

                        #Interrupt B 
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF0B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF0B = {} expected {}".format(1,0))
                                
                        #Interrupt OVF
#                        if (TIMER0.TCNT0) == 0xFF:
#                            if TOV0.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys0.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST13'
                case 'TEST13':# TEST13 :Phase Correct PWM mode Compare Match Output B (Set OC0B on compare match when up-counting. Clear OC0B on compare match when down-counting, inverting mode) and A (Set OC0A on compare match when up-counting. Clear OC0A on compare match when down-counting, inverting mode) (writing using Ls) | No prescaling (X12)
                    results.write("TEST13\n")
                    #Setup
                    TIMER0.TCCR0A = 0xF1
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 0
                    TIMER0.OC0B_val = 0

                    sys0.getSimulator().clk(1)

                    last_OCR0A = OC0A.get()
                    TIMER0.TCNT0 = 0

                    counter = 0
                ## Testing
                    for i in range(511):
                        # counter test 
                        if i < 255:
                            if TIMER0.TCNT0 != i:
                                TEST = False
                                ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,i))
                        elif i>=255:
                            if TIMER0.TCNT0 != 255-counter:
                                TEST = False
                                ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,255-counter))
                            counter += 1

                        #Output A (inverting: high inside the [OCR0A, 510-OCR0A] window)
                        if  64<=i<=445:
                            if OC0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            if OC0A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(1,0,i))
        
                        #Output B (inverting)
                        if  128<=i<=381:
                            if OC0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            if OC0B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(1,0,i))

                        #Interrupt A
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt B 
                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}|Iteration {}".format(0,1,i))

                        sys0.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST14'
                case 'TEST14':# TEST14 :CTC Output B disconnected and A disconnected (writing using Ls to load data) | No prescaling (X13)
                    results.write("TEST14\n")
                    #Setup
                    ## Loading the config values in memory
                    TIMER0.TCCR0A = 0x02
                    TIMER0.TCCR0B = 0x01

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    last_OC0A = 0
                    last_OC0B = 0

                    TIMER0.OC0A_val = 0
                    TIMER0.OC0B_val = 0

                    sys0.getSimulator().clk(1)

                    TIMER0.TCNT0 = 0

                    counter = 0
                    ## Testing
                    for i in range(128):
                        # counter test 

                        if (TIMER0.TCNT0) <= TIMER0.OCR0A:
                                if TIMER0.TCNT0 != i%(TIMER0.OCR0A + 1):
                                    TEST = False
                                    ERROR_LIST.append("TCNT0 = {} expected {}|Iteration {}".format(TIMER0.TCNT0,i%(TIMER0.OCR0A + 1),i))
                        


                        #Output A
                        if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}".format(1,0))


                        #Output B 
                        if OC0B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0B = {} expected {}".format(1,0))


                        #Interrupt A
                        if (TIMER0.TCNT0) == TIMER0.OCR0A:
                            counter = 0
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER0.TCNT0) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| iteration = {}".format(0,1,i))

                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys0.getSimulator().clk(1)
                        counter+=1

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST15'
                case 'TEST15':# TEST15 :Normal mode Compare Match Output B disconected and A disconected (writing using Ls) | External clock source on T0 pin. Clock on falling edge. (X14)
                    results.write("TEST15\n")
                    #Setup
                    TIMER0.TCCR0A = 0x00
                    TIMER0.TCCR0B = 0x07

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 0
                    TIMER0.OC0B_val = 0


                    last_T0 = 0
                    T0.prepare(0)

                    sys0.getSimulator().clk(1)

                    TIMER0.TCNT0 = 0

                    counter = 0
                    clockCounter = 0
                ## Testing
                    while 1:

                        # counter test 
                        if TIMER0.TCNT0 != math.floor(counter/2): # 2 transitions
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}".format(TIMER0.TCNT0,math.floor(counter/2)))


                        #Output A
                        if OC0A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC0A = {} expected {}".format(1,0))


                        #Output B 
                        if OC0B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0B = {} expected {}".format(1,0))


                        #Interrupt A
                        if (TIMER0.TCNT0) == TIMER0.OCR0A:
                            if OCF0A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0A = {} expected {}| iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER0.TCNT0) == TIMER0.OCR0B:
                            if OCF0B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF0B = {} expected {}| iteration = {}".format(0,1,i))

                        #Interrupt OVF
                        if (TIMER0.TCNT0) == 0xFF:
                            if TOV0.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys0.getSimulator().clk(1)
                        clockCounter+=1
                        if clockCounter >= 2:
                            counter += 1 
                        last_T0 = T0.get()
                        T0.prepare(1-last_T0)
                        if counter >= 255:
                            break
                        


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST16'
                case 'TEST16':# TEST16 :Normal mode Compare Match Output B disconected and A disconected (writing using Ls) | /8 prescaler (X15)
                    results.write("TEST16\n")
                    #Setup
                    TIMER0.TCCR0A = 0x00
                    TIMER0.TCCR0B = 0x02

                    TIMER0.OCR0A = 64
                    TIMER0.OCR0B = 128

                    TIMER0.TCNT0 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER0.TIMSK0 = 0b111
                    TIMER0.TIFR0 = 0 # clear interrupts

                    TIMER0.OC0A_val = 0
                    TIMER0.OC0B_val = 0

                    sys0.getSimulator().clk(1)

                    TIMER0.TCNT0 = 0
                    counter = 0
                    clockCounter = 1
                ## Testing
                    for i in range(4080):

                        # counter test 
                        if TIMER0.TCNT0 != counter%256:
                            TEST = False
                            ERROR_LIST.append("TCNT0 = {} expected {}|Iteration {}".format(TIMER0.TCNT0,counter%256,i))


                        #Output A 
                        if OC0A.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(0,1,i))

        

                        #Output B 
                        if OC0B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(0,1,i))


                        #Interrupt A
#                        if (TIMER0.TCNT0-1) == TIMER0.OCR0A:
#                            if OCF0A.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF0A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OC0A = {} expected {}|Iteration {}".format(1,0,i))

                        #Interrupt B 
#                        if (TIMER0.TCNT0-1) == TIMER0.OCR0B:
#                            if OCF0B.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF0B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OC0B = {} expected {}|Iteration {}".format(1,0,i))
                                
                        #Interrupt OVF
#                        if (TIMER0.TCNT0) == 0xFF:
#                            if TOV0.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OVF = {} expected {}|Iteration {}".format(0,1,i))

                        sys0.getSimulator().clk(1)
                        clockCounter += 1
                        if clockCounter >= 8:
                            clockCounter = 0
                            counter += 1 


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'FINAL'
                case 'FINAL':
                    results.write("TEST SUMMARY:")
                    
                    
                    results.close()

                    break
                    wvf.gui()
                    Testing = False
                    CURRENT_TEST = 'FINAL'

if __name__ == "__main__":
    TestBench_of_Timer0()