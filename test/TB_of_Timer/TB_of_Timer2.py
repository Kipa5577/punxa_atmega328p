import py4hw
from punxa_atmega328p.Timers import *
from punxa_atmega328p.Memory import * 
import time
import math


#run from top directory using python -m test.TB_of_Timer.TB_of_Timer2

def TestBench_of_Timer2():

    sys2 = py4hw.HWSystem()

    SIGNALS2 = []

    OCF2B = py4hw.Wire( sys2,'OCF2B',1)
    SIGNALS2.append(OCF2B)
    OCF2A = py4hw.Wire( sys2,'OCF2A',1)
    SIGNALS2.append(OCF2A)
    TOV2 = py4hw.Wire( sys2,'TOV2',1)
    SIGNALS2.append(TOV2)

    OC2A = py4hw.Wire(sys2,'OC2A',1)
    SIGNALS2.append(OC2A)
    OC2B = py4hw.Wire(sys2,'OC2B',1)
    SIGNALS2.append(OC2B)
    T2 = py4hw.Wire(sys2,'T2',1)
    SIGNALS2.append(T2)

    interface2 = MemoryInterface(sys2,'interface2',8,16)

    TIMER2 = TimerCounter2(sys2,'TIMER2',interface2,OC2B,OC2A,T2,OCF2B,OCF2A,TOV2)



    SIGNALS2.append(interface2.write)
    SIGNALS2.append(interface2.read)
    SIGNALS2.append(interface2.address)
    SIGNALS2.append(interface2.write_data)
    SIGNALS2.append(interface2.read_data)
    SIGNALS2.append(interface2.resp)

    CURRENT_TEST = 'START'

    wvf = py4hw.Waveform(sys2,'wvf',SIGNALS2)

    #sch = py4hw.Schematic(sys)
    #sch.draw()
    #sys.getSimulator().clk(len(TIMER2_WRITE_DATA_TEST))

    Testing = True
    with open("test/TB_of_Timer/Test_Results_Timer2.txt",'w+') as results:
        while Testing:

            
            match CURRENT_TEST:

                case 'START':
                    print("Starting Test Bench of Timer2")

                    CURRENT_TEST = 'TEST0'
                case 'TEST0':# TEST0 :Normal mode Compare Match Output B disconnected and A disconnected (writing using Ls to load data) | No prescaling (X1)
                    results.write("TEST0\n")
                    #Setup
                    ## Loading the config values in memory
                    TIMER2.TCCR2A = 0x00
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    last_OC2A = 0
                    last_OC2B = 0

                    ## Testing
                    for i in range(255):
                        # counter test 

                        if TIMER2.TCNT2 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i%256))

                        #Output A
                        if OC2A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}".format(1,0))

                        #Output B 
                        if OC2B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2B = {} expected {}".format(1,0))

                        #Interrupt A
                        if (TIMER2.TCNT2) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}| iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER2.TCNT2) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}| iteration = {}".format(0,1,i))

                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys2.getSimulator().clk(1)


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
                    TIMER2.TCCR2A = 0x50
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    last_OC2A = 0
                    last_OC2B = 0

                    ## Testing
                    for i in range(255):
                        # counter test 

                        if TIMER2.TCNT2 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i%256))

                        #Output A 
                        if TIMER2.TCNT2 >= TIMER2.OCR2A:
                            if OC2A.get() == last_OC2A:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| Iteration = {}".format(last_OC2A,(1-last_OC2A),i))
                        else:
                            last_OC2A = OC2A.get()

        
                        #Output B 
                        if TIMER2.TCNT2 >= TIMER2.OCR2B:
                            if OC2B.get() == last_OC2B:# error val
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}| Iteration = {}".format(last_OC2B,(1-last_OC2B),i))
                        else:
                            last_OC2B = OC2B.get()


                        #Interrupt A
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))

                        sys2.getSimulator().clk(1)

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
                    TIMER2.TCCR2A = 0xA0
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 1
                    TIMER2.OC2B_val = 1
                

                ## Testing
                    for i in range(255):
                        # counter test 

                        if TIMER2.TCNT2 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i%256))

                        #Output A 
                        if TIMER2.TCNT2 >= TIMER2.OCR2A:
                            if OC2A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| Iteration = {}".format(0,1,i))
                        else:
                            if OC2A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| Iteration = {}".format(1,0,i))
        
                        #Output B 
                        if TIMER2.TCNT2 >= TIMER2.OCR2B:
                            if OC2B.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}| Iteration = {}".format(0,1,i))
                        else:
                            if OC2B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}| Iteration = {}".format(1,0,i))

                        #Interrupt A
                        if (TIMER2.TCNT2) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER2.TCNT2) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))


                        sys2.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST3'
                case 'TEST3':# TEST3 :Normal mode Compare Match Output B Set and A Set (writing using Ls to load data) | No prescaling (X4)
                    results.write("TEST3\n")
                    #Setup
                    TIMER2.TCCR2A = 0xF0
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 0
                    TIMER2.OC2B_val = 0

                ## Testing
                    for i in range(255):
                        # counter test 

                        if TIMER2.TCNT2 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i%256))

                        #Output A 
                        if TIMER2.TCNT2 >= TIMER2.OCR2A:
                            if OC2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| Iteration = {}".format(0,1,i))
                        else:
                            if OC2A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| Iteration = {}".format(1,0,i))
        
                        #Output B 
                        if TIMER2.TCNT2 >= TIMER2.OCR2B:
                            if OC2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}| Iteration = {}".format(0,1,i))
                        else:
                            if OC2B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}| Iteration = {}".format(1,0,i))

                        #Interrupt A
                        if (TIMER2.TCNT2) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}".format(0,1))
                        #else:
                        #    if OCF2A.get() == 1:
                        #        TEST = False
                        #        ERROR_LIST.append("OCF2B = {} expected {}".format(1,0))

                        #Interrupt B 
                        if (TIMER2.TCNT2) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}".format(0,1))
                        #else:
                        #    if OCF2A.get() == 1:
                        #        TEST = False
                        #        ERROR_LIST.append("OCF2A = {} expected {}".format(1,0))
                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys2.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST4'
                case 'TEST4': # TEST4 :Fast PWM Mode mode Compare Match Output B disconnected and A disconnected (writing using Ls to load data) | No prescaling (X5)
                    results.write("TEST4\n")
                    #Setup
                    TIMER2.TCCR2A = 0x03
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 0
                    TIMER2.OC2B_val = 0

                    sys2.getSimulator().clk(1)

                ## Testing
                    for i in range(1,255):
                        # counter test 
                        if TIMER2.TCNT2 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}| iteration = {}".format(TIMER2.TCNT2,i%256))


                        #Output A
                        if OC2A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| iteration = {}".format(1,0,i))


                        #Output B 
                        if OC2B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2B = {} expected {}| iteration = {}".format(1,0,i))


                        #Interrupt A
                        if (TIMER2.TCNT2) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}| iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER2.TCNT2) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}| iteration = {}".format(0,1,i))

                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys2.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST5'
                case 'TEST5':# TEST5 :Fast PWM Mode mode Compare Match Output B disconnected and A (Normal port operation, OC2A disconnected) (writing using Ls to load data) | No prescaling (X6.1)
                    results.write("TEST5\n")
                    #Setup
                    TIMER2.TCCR2A = 0x53
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 0
                    TIMER2.OC2B_val = 0

                    last_OC2A = 0
                    last_OC2B = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER2.TCNT2 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i%256))

                        #Output A
                        if OC2A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}".format(1,0))

                        #Output B 
                        if OC2B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2B = {} expected {}".format(1,0))


                        #Interrupt A
                        if (TIMER2.TCNT2) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if TIMER2.TCNT2 == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))

                        sys2.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST6'
                case 'TEST6':# TEST6 :Fast PWM Mode mode Compare Match Output B disconnected and A (Toggle OC2A on compare match.) (writing using Ls to load data) | No prescaling (X6.2)
                    results.write("TEST6\n")
                    #Setup
                    TIMER2.TCCR2A = 0x53
                    TIMER2.TCCR2B = 0x09

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                ## Testing
                    for i in range(255):
                        # counter test
                        # NOTE: TCCR2A low bits = 11 and TCCR2B.WGM02 = 1 (0x09) select
                        # WGM=7 (Fast PWM, TOP=OCR2A), NOT TOP=0xFF. TCNT2 free-runs
                        # 0..OCR2A-1 and wraps every OCR2A counts (this DUT resets
                        # TCNT2 to BOTTOM the instant it would equal TOP, so the
                        # value TOP=OCR2A itself is never observed - see TimerCounter2
                        # .Other_modes_Increment), so the expected value must be
                        # taken modulo OCR2A, not modulo 255.
                        expected_tcnt0 = i % (TIMER2.OCR2A + 1)
                        if TIMER2.TCNT2 != expected_tcnt0:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,expected_tcnt0))

                        #Output A 
                        if TIMER2.TCNT2 >= TIMER2.OCR2A:
                            if OC2A.get() == last_OC2A:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| Iteration = {}".format(last_OC2A,(1-last_OC2A),i))
                        else:
                            last_OC2A = OC2A.get()


                        if OC2B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2B = {} expected {}| Iteration = {}".format(1,0,i))


                        #Interrupt A
                        if (TIMER2.TCNT2) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if TIMER2.TCNT2 == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}| Iteration = {}".format(0,1,i))


                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))

                        sys2.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST7'
                case 'TEST7':# TEST7 :Fast PWM Mode mode Compare Match Output B (Clear OC2B on compare match, set OC2B at BOTTOM,(non-inverting mode)) and A (Clear OC2A on compare match, set OC2A at BOTTOM,(non-inverting mode).) (writing using Ls to load data) | No prescaling (X7)
                    results.write("TEST7\n")
                    #Setup
                    TIMER2.TCCR2A = 0xA3
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2B_val = 1
                    TIMER2.OC2A_val = 1

                    sys2.getSimulator().clk(1)

                    TIMER2.TCNT2 = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER2.TCNT2 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i%256))

                        #Output A 
                        if TIMER2.TCNT2 >= TIMER2.OCR2A:
                            if OC2A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| Iteration = {}".format(1,0,i))
                        else:
                            if OC2A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}| Iteration = {}".format(0,1,i))
        
                        #Output B 
                        if TIMER2.TCNT2 >= TIMER2.OCR2B:
                            if OC2B.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}| Iteration = {}".format(1,0,i))
                        else:
                            if OC2B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}| Iteration = {}".format(0,1,i))

                        #Interrupt A
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}| Iteration = {}".format(0,1,i))

                        #Interrupt B 
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}| Iteration = {}".format(0,1,i))
                                
                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}| Iteration = {}".format(0,1,i))

                        sys2.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST8'
                case 'TEST8':# TEST8 :Fast PWM Mode mode Compare Match Output B (Set OC2B on compare match, clear OC2B at BOTTOM,(inverting mode)) and A (Set OC2A on compare match, clear OC2A at BOTTOM,(inverting mode).) (writing using Ls to load data) | No prescaling (X8)
                    results.write("TEST8\n")
                    #Setup
                    TIMER2.TCCR2A = 0xF3
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2B_val = 0
                    TIMER2.OC2A_val = 0

                    sys2.getSimulator().clk(1)
                    TIMER2.TCNT2 = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER2.TCNT2 != i:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i))

                        #Output A 
                        if TIMER2.TCNT2 >= TIMER2.OCR2A:
                            if OC2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            if OC2A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(1,0,i))
        
                        #Output B 
                        if TIMER2.TCNT2 >= TIMER2.OCR2B:
                            if OC2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            if OC2B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(1,0,i))

                        #Interrupt A
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt B 
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}|Iteration {}".format(0,1,i))
                                
                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}|Iteration {}".format(0,1,i))

                        sys2.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST9'
                case 'TEST9':# TEST9 :Phase Correct PWM mode Compare Match Output B disconnected and A disconnected (writing using Ls) | No prescaling (X9)
                    results.write("TEST9\n")
                    #Setup
                    TIMER2.TCCR2A = 0x01
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2B_val = 0
                    TIMER2.OC2A_val = 0

                    sys2.getSimulator().clk(1)
                    TIMER2.TCNT2 = 0

                ## Testing
                    for i in range(255*2):
                        # counter test 

                        if i <= 255 :
                            if TIMER2.TCNT2 != i:
                                TEST = False
                                ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i))
                        else: 
                            if TIMER2.TCNT2 != (255 - (i - 255)):
                                TEST = False
                                ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,255-(i-255))) 


                        #Output A 
                        if ((TIMER2.TCNT2 >= TIMER2.OCR2A) and i<= 255) or ((TIMER2.TCNT2 <= TIMER2.OCR2A) and  i >= 255 ):
                            if OC2A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))
        

                        #Output B 
                        if ((TIMER2.TCNT2 >= TIMER2.OCR2B) and (i<= 255)) or ((TIMER2.TCNT2 <= TIMER2.OCR2A) and (i >= 255)):
                            if OC2B.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(0,1,i))


                        #Interrupt A
#                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
#                            if OCF2A.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF2A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(1,0,i))


                        #Interrupt B 
#                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
#                            if OCF2B.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OCF2B = {} expected {}".format(0,1))
#                        else:
#                            if OCF2B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF2B = {} expected {}".format(1,0))
                                

                        #Interrupt OVF
#                        if (TIMER2.TCNT2) == 0xFF:
#                            if TOV2.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))


                        sys2.getSimulator().clk(1)

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST10'
                case 'TEST10':# TEST10 :Phase Correct PWM mode Compare Match Output B disconnected and A (Normal port operation, OC2A disconnected.) (writing using Ls) | No prescaling (X10.1)
                    results.write("TEST10\n")
                    #Setup
                    TIMER2.TCCR2A = 0xA3
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128


                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts


                    TIMER2.OC2B_val = 0
                    TIMER2.OC2A_val = 0
                    sys2.getSimulator().clk(1)

                    TIMER2.TCNT2 = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER2.TCNT2 != i%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i%256))


                        #Output A 
                        if OC2A.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))
        

                        #Output B 
                        if OC2B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(0,1,i))


                        #Interrupt A
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF2A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(1,0,i))


                        #Interrupt B 
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF2B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF2B = {} expected {}|Iteration {}".format(1,0,i))
                                

                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}|Iteration {}".format(0,1,i))


                        sys2.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST11'
                case 'TEST11':# TEST11 :Phase Correct PWM mode Compare Match Output B disconnected and A (Toggle OC2A on compare match.) (writing using Ls) | No prescaling (X10.2)
                    results.write("TEST11\n")
                    #Setup
                    TIMER2.TCCR2A = 0xA3
                    TIMER2.TCCR2B = 0x09

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 0
                    TIMER2.OC2B_val = 0

                    sys2.getSimulator().clk(1)

                    last_OCR2A = OC2A.get()
                    TIMER2.TCNT2 = 0

                ## Testing
                    for i in range(255):
                        # counter test 
                        if TIMER2.TCNT2 != i%(TIMER2.OCR2A + 1):
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i%(TIMER2.OCR2A + 1)))

                        #Output A 
                        if ((TIMER2.TCNT2 == TIMER2.OCR2A) and i <= 255) or ((TIMER2.TCNT2 == TIMER2.OCR2A) and i>=255):
                            if OC2A.get() == last_OCR2A:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            last_OCR2A


                        #Interrupt A
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF2A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration".format(1,0,i))

                        #Interrupt B 
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}|Iteration".format(0,1,i))
#                        else:
#                            if OCF2B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF2B = {} expected {}|Iteration".format(1,0,i))
                                
                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}|Iteration".format(0,1,i))


                        sys2.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST12'
                case 'TEST12':# TEST12 :Phase Correct PWM mode Compare Match Output B (Clear OC2B on compare match when up-counting. Set OC2B on compare match when down-counting.) and A (Clear OC2A on compare match when up-counting. Set OC2A on compare match when down-counting.) (writing using Ls) | No prescaling (X11)
                    results.write("TEST12\n")
                    #Setup
                    TIMER2.TCCR2A = 0xA1
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 1
                    TIMER2.OC2B_val = 1

                    sys2.getSimulator().clk(1)

                    last_OCR2A = OC2A.get()
                    TIMER2.TCNT2 = 0

                    counter = 0
                ## Testing
                    for i in range(511):
                        # counter test 
                        if i < 255:
                            if TIMER2.TCNT2 != i:
                                TEST = False
                                ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i))
                        elif i>=255:
                            if TIMER2.TCNT2 != 255-counter:
                                TEST = False
                                ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,255-counter))
                            counter += 1

                        #Output A 
                        if  64<=i<=445:   #((TIMER2.TCNT2 >= TIMER2.OCR2A) and (i < 255)) or ((TIMER2.TCNT2 <= TIMER2.OCR2A) and (i>=255)):
                            if OC2A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(1,0,i))
                        else:
                            if OC2A.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))
        
                        #Output B 
                        if  128<=i<=381:# (TIMER2.TCNT2 >= TIMER2.OCR2B) and i <= 255) or ((TIMER2.TCNT2 <= TIMER2.OCR2B) and i>=255):
                            if OC2B.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(1,0,i))
                        else:
                            if OC2B.get() == 0:
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt A
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF2A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF2A = {} expected {}".format(1,0))

                        #Interrupt B 
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF2B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OCF2B = {} expected {}".format(1,0))
                                
                        #Interrupt OVF
#                        if (TIMER2.TCNT2) == 0xFF:
#                            if TOV2.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys2.getSimulator().clk(1)


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)


                    CURRENT_TEST = 'TEST13'
                case 'TEST13':# TEST13 :Phase Correct PWM mode Compare Match Output B (Set OC2B on compare match when up-counting. Clear OC2B on compare match when down-counting, inverting mode) and A (Set OC2A on compare match when up-counting. Clear OC2A on compare match when down-counting, inverting mode) (writing using Ls) | No prescaling (X12)
                    results.write("TEST13\n")
                    #Setup
                    TIMER2.TCCR2A = 0xF1
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 0
                    TIMER2.OC2B_val = 0

                    sys2.getSimulator().clk(1)

                    last_OCR2A = OC2A.get()
                    TIMER2.TCNT2 = 0

                    counter = 0
                ## Testing
                    for i in range(511):
                        # counter test 
                        if i < 255:
                            if TIMER2.TCNT2 != i:
                                TEST = False
                                ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,i))
                        elif i>=255:
                            if TIMER2.TCNT2 != 255-counter:
                                TEST = False
                                ERROR_LIST.append("TCNT2 = {} expected {}".format(TIMER2.TCNT2,255-counter))
                            counter += 1

                        #Output A (inverting: high inside the [OCR2A, 510-OCR2A] window)
                        if  64<=i<=445:
                            if OC2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            if OC2A.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(1,0,i))
        
                        #Output B (inverting)
                        if  128<=i<=381:
                            if OC2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(0,1,i))
                        else:
                            if OC2B.get() == 1:
                                TEST = False
                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(1,0,i))

                        #Interrupt A
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt B 
                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}|Iteration {}".format(0,1,i))

                        sys2.getSimulator().clk(1)


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
                    TIMER2.TCCR2A = 0x02
                    TIMER2.TCCR2B = 0x01

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    last_OC2A = 0
                    last_OC2B = 0

                    TIMER2.OC2A_val = 0
                    TIMER2.OC2B_val = 0

                    sys2.getSimulator().clk(1)

                    TIMER2.TCNT2 = 0

                    counter = 0
                    ## Testing
                    for i in range(128):
                        # counter test 

                        if (TIMER2.TCNT2) <= TIMER2.OCR2A:
                                if TIMER2.TCNT2 != i%(TIMER2.OCR2A + 1):
                                    TEST = False
                                    ERROR_LIST.append("TCNT2 = {} expected {}|Iteration {}".format(TIMER2.TCNT2,i%(TIMER2.OCR2A + 1),i))
                        


                        #Output A
                        if OC2A.get() == 1:# error val
                                TEST = False
                                ERROR_LIST.append("OC2A = {} expected {}".format(1,0))


                        #Output B 
                        if OC2B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2B = {} expected {}".format(1,0))


                        #Interrupt A
                        if (TIMER2.TCNT2) == TIMER2.OCR2A:
                            counter = 0
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}| iteration = {}".format(0,1,i))


                        #Interrupt B 
                        if (TIMER2.TCNT2) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}| iteration = {}".format(0,1,i))

                        #Interrupt OVF
                        if (TIMER2.TCNT2) == 0xFF:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}".format(0,1))

                        sys2.getSimulator().clk(1)
                        counter+=1

                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST15'
                case 'TEST15':# TEST15 :Normal mode Compare Match Output B disconnected and A disconnected (writing using Ls) | /32 prescaler (X14)
                    results.write("TEST15\n")
                    #Setup
                    TIMER2.TCCR2A = 0x00
                    TIMER2.TCCR2B = 0x03  # CS22:20 = 011 -> clk/32 (Timer2-specific tap)

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 0
                    TIMER2.OC2B_val = 0

                    sys2.getSimulator().clk(1)

                    TIMER2.TCNT2 = 0
                    counter = 0
                    clockCounter = 1
                ## Testing
                    for i in range(8192):

                        # counter test 
                        if TIMER2.TCNT2 != counter%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}|Iteration {}".format(TIMER2.TCNT2,counter%256,i))

                        #Output A 
                        if OC2A.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))

                        #Output B 
                        if OC2B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt A
                        if (TIMER2.TCNT2) == TIMER2.OCR2A:
                            if OCF2A.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2A = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt B 
                        if (TIMER2.TCNT2) == TIMER2.OCR2B:
                            if OCF2B.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OCF2B = {} expected {}|Iteration {}".format(0,1,i))

                        #Interrupt OVF (fires the cycle AFTER TCNT2 reads 0xFF, i.e. when it reads 0 again)
                        if (TIMER2.TCNT2) == 0 and counter > 0:
                            if TOV2.get() == 0:# error val
                                TEST = False
                                ERROR_LIST.append("OVF = {} expected {}|Iteration {}".format(0,1,i))

                        sys2.getSimulator().clk(1)
                        clockCounter += 1
                        if clockCounter >= 32:
                            clockCounter = 0
                            counter += 1 


                    ## Storing data
                    ITEM = []
                    ITEM.append(TEST)
                    ITEM.append(ERROR_LIST)
                    results.write('%s\n' %ITEM)

                    CURRENT_TEST = 'TEST16'
                case 'TEST16':# TEST16 :Normal mode Compare Match Output B disconected and A disconected (writing using Ls) | /8 prescaler (X15)
                    results.write("TEST16\n")
                    #Setup
                    TIMER2.TCCR2A = 0x00
                    TIMER2.TCCR2B = 0x02

                    TIMER2.OCR2A = 64
                    TIMER2.OCR2B = 128

                    TIMER2.TCNT2 = 0

                    ERROR_LIST = []
                    TEST = True 

                    TIMER2.TIMSK2 = 0b111
                    TIMER2.TIFR2 = 0 # clear interrupts

                    TIMER2.OC2A_val = 0
                    TIMER2.OC2B_val = 0

                    sys2.getSimulator().clk(1)

                    TIMER2.TCNT2 = 0
                    counter = 0
                    clockCounter = 1
                ## Testing
                    for i in range(4080):

                        # counter test 
                        if TIMER2.TCNT2 != counter%256:
                            TEST = False
                            ERROR_LIST.append("TCNT2 = {} expected {}|Iteration {}".format(TIMER2.TCNT2,counter%256,i))


                        #Output A 
                        if OC2A.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))

        

                        #Output B 
                        if OC2B.get() == 1:# error val
                            TEST = False
                            ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(0,1,i))


                        #Interrupt A
#                        if (TIMER2.TCNT2-1) == TIMER2.OCR2A:
#                            if OCF2A.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF2A.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OC2A = {} expected {}|Iteration {}".format(1,0,i))

                        #Interrupt B 
#                        if (TIMER2.TCNT2-1) == TIMER2.OCR2B:
#                            if OCF2B.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(0,1,i))
#                        else:
#                            if OCF2B.get() == 1:
#                                TEST = False
#                                ERROR_LIST.append("OC2B = {} expected {}|Iteration {}".format(1,0,i))
                                
                        #Interrupt OVF
#                        if (TIMER2.TCNT2) == 0xFF:
#                            if TOV2.get() == 0:# error val
#                                TEST = False
#                                ERROR_LIST.append("OVF = {} expected {}|Iteration {}".format(0,1,i))

                        sys2.getSimulator().clk(1)
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
    TestBench_of_Timer2()