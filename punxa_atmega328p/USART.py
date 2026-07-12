import py4hw
from punxa_atmega328p.Memory import *

UCSRA_REG = 0x00   # Control and Status register A
UCSRB_REG = 0x01   # Control and Status register B
UCSRC_REG = 0x02   # Control and Status register C
UBRRL_REG = 0x04   # Baud Rate Register Low
UBRRH_REG = 0x05   # Baud Rate Register High
UDR_REG =    0x06   # Transmit Buffer Register

UCSRA_RXC = 1 << 7    # Receive Complete
UCSRA_TXC = 1 << 6    # Transmit Complete
UCSRA_UDRE = 1 << 5   # Data register empty
UCSRA_FE = 1 << 4     # Frame Error
UCSRA_DOR = 1 << 3    # Data OverRun
UCSRA_PE = 1 << 2     # Parity Error
UCSRA_2X = 1 << 1     # Double Transmission Speed
UCSRA_MPCM = 1        # Multi-processor Communication Mode

class USART(py4hw.Logic):
    def __init__(self,parent,name:str,memory:MemoryInterface,RXD,TXD,USART_CLK,RXC_INT,TXC_INT,UDRE_INT):
        super().__init__(parent, name)

        self.interface = self.addInterfaceSink('port',memory)

        #Physical Pins
        self.RXD = self.addIn('RXD',RXD)
        self.TXD = self.addOut('TXD',TXD)
        self.USART_CLK = self.addOut('USART_CLK',USART_CLK)

        #Interrupts
        self.RXC_INT = self.addOut('RXC_INIT',RXC_INT)
        self.TXC_INT = self.addOut('TXC_INT', TXC_INT)
        self.UDRE_INT = self.addOut('UDRE_INT', UDRE_INT)

        self.TXD_val = 1
        self.RXC_INT_val = 0
        self.TXC_INT_val = 0
        self.USART_CLK_val = 0
        self.UDRE_INT_val = 0

        self.UCSR0A = 0x20 # Bit5: UDRE0 is 1 by default (Buffer Empty)
        self.UCSR0A_addr_LS = 0xC0

        self.UCSR0B = 0
        self.UCSR0B_addr_LS = 0xC1

        self.UCSR0C = 0x06 # Default: Async, No parity, 1 stop bit, 8 data bits
        self.UCSR0C_addr_LS = 0xC2

        self.UBRR0L = 0
        self.UBRR0L_addr_LS = 0xC4

        self.UBRR0H = 0
        self.UBRR0H_addr_LS = 0xC5

#       self.UDR0 = 0
        self.UDR0_addr_LS = 0xC6

        #Internal Data Buffers
        self.RXB_buffer = 0
        self.readBuffer = 0
        self.TXB_buffer = 0
        self.TXDB_full = False

        #Control & Status Bits
        #UCSR0A
        self.RXC0 = 0 
        self.TXC0 = 0
        self.UDRE0 = 1  
        self.FE0 = 0
        self.DOR0 = 0
        self.UPE0 = 0
        self.U2X0 = 0
        self.MPCM0 = 0

        #UCSR0B
        self.RXCIE0 = 0
        self.TXCIE0 = 0
        self.UDRIE0 = 0
        self.RXEN0 = 0
        self.TXEN0 = 0
        self.UCSZ02 = 0
        self.RXB80 = 0
        self.TXB80 = 0

        #UCSR0C
        self.UMSEL01 = 0
        self.UMSEL00 = 0
        self.UPM01 = 0
        self.UPM00 = 0
        self.USBS0 = 0
        self.UCSZ01 = 1
        self.UCSZ00 = 1
        self.UCPOL0 =0

        self.ticks_per_bit = 0

        self.opp_mode = 'Asynchronous'
        self.nbBits = 8
        self.nbStopBits = 1
        self.ParityMode = 'Disabled' #Disabled even odd

        # Transmit/Receive State Machines
        self.baud_counter = 0
        self.tx_state = 'IDLE' # 'IDLE' START' 'DATA' 'PARITY' 'STOP'  
        self.tx_shift_reg = 0
        self.tx_bits_left = 0
        self.tx_stop_cnt = 0
        self.tx_parity = 0
        self.tx_tick_cnt = 0
        
        self.rx_state = 'IDLE' # 'IDLE' START' 'DATA' 'PARITY' 'STOP'  
        self.rx_shift_reg = 0
        self.rx_bits_rcvd = 0
        self.rx_stop_cnt = 0
        self.rx_tick_cnt = 0
        self.rx_parity = 0 
        self.rx_fe = 0
        self.rx_upe = 0
        
        self.rx_shift_reg_full = False

        self.baud_Tick = False
        self.tickCounter = 0

    def Memory_access(self):
        ADDR = self.interface.address.get()
        read_opp = (self.interface.read.get() == 1) and (self.interface.write.get() == 0)
        write_opp = (self.interface.read.get() == 0) and (self.interface.write.get() == 1)
        valid_ins = (self.interface.instype.get() == 1)

        if valid_ins:
            if ADDR == self.UCSR0A_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UCSR0A)
                    self.interface.resp.prepare(1)
                elif write_opp:
                    data =  self.interface.write_data.get()
                    if data & (1<<6):
                        self.UCSR0A &= ~(1<<6) # clear TXC0
                    self.UCSR0A = (self.UCSR0A & 0b11111100) | (data & 0b00000011)

                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)

            elif ADDR == self.UCSR0B_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UCSR0B)
                    self.interface.resp.prepare(1)
                elif write_opp:

                    data = self.interface.write_data.get()
                    self.UCSR0B = (data & ~(1 << 1)) | (self.UCSR0B & (1 << 1))

                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UCSR0C_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UCSR0C)
                    self.interface.resp.prepare(1)
                elif write_opp:
                    self.UCSR0C = self.interface.write_data.get()
                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UBRR0L_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UBRR0L)
                    self.interface.resp.prepare(1)
                elif write_opp:
                    self.UBRR0L = self.interface.write_data.get()
                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UBRR0H_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UBRR0H)
                    self.interface.resp.prepare(1)
                elif write_opp:
                    self.UBRR0H = self.interface.write_data.get() & 0x0F
                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UDR0_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.RXB_buffer)

                    self.RXB_buffer = self.readBuffer # advance the fifo
                    self.readBuffer = 0

                    #reading UDR0 clears the RXC0 flag in hardware
                    if self.RXB_buffer != 0:
                        self.RXC0 = 1
                    else:
                        self.RXC0 = 0

                    self.update_UCSR0A()

                    self.interface.resp.prepare(1)
                elif write_opp:
                    data = self.interface.write_data.get() & 0xFF

                    if not self.TXDB_full:
                        self.TXB_buffer = data
                        self.TXDB_full = True
                        # Clear UDRE0 — buffer is now occupied
                        self.UDRE0 = 0
                        self.TXC0 = 0
                        self.update_UCSR0A()

                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            else:
                self.interface.resp.prepare(0)

    def Parse_control_registers(self):
        #Control & Status Bits
        #UCSR0A
        self.RXC0 = (self.UCSR0A>>7)&1
        self.TXC0 = (self.UCSR0A>>6)&1
        self.UDRE0 = (self.UCSR0A>>5)&1  
        self.FE0 = (self.UCSR0A>>4)&1
        self.DDR0 = (self.UCSR0A>>3)&1
        self.UPE0 = (self.UCSR0A>>2)&1
        self.U2X0 = (self.UCSR0A>>1)&1
        self.MPCM0 = (self.UCSR0A>>0)&1

        #UCSR0B
        self.RXCIE0 = (self.UCSR0B>>7)&1
        self.TXCIE0 = (self.UCSR0B>>6)&1
        self.UDRIE0 = (self.UCSR0B>>5)&1
        self.RXEN0 = (self.UCSR0B>>4)&1
        self.TXEN0 = (self.UCSR0B>>3)&1
        self.UCSZ02 = (self.UCSR0B>>2)&1
        self.RXB80 = (self.UCSR0B>>1)&1
        self.TXB80 = (self.UCSR0B>>0)&1

        #UCSR0C
        self.UMSEL01 = (self.UCSR0C>>7)&1
        self.UMSEL00 = (self.UCSR0C>>6)&1
        self.UPM01 = (self.UCSR0C>>5)&1
        self.UPM00 = (self.UCSR0C>>4)&1
        self.USBS0 = (self.UCSR0C>>3)&1
        self.UCSZ01 = (self.UCSR0C>>2)&1
        self.UCSZ00 = (self.UCSR0C>>1)&1
        self.UCPOL0 = (self.UCSR0C>>0)&1

        # Composed fields
        self.UBRR0 = ((self.UBRR0H&0xF)<<8) | self.UBRR0L
        self.UCSZ = (self.UCSZ02 << 2) | (self.UCSZ01<<1) | (self.UCSZ00<<0) 
        self.UMSEL = (self.UMSEL01<<1) | self.UMSEL00
        self.UPM = (self.UPM01<<1) | self.UPM00

    def update_UCSR0A(self):
        self.UCSR0A = (
            (self.RXC0 << 7 ) |
            (self.TXC0 << 6 ) |
            (self.UDRE0 << 5) |
            (self.FE0 << 4  ) |
            (self.DOR0 << 3 ) |
            (self.UPE0 << 2 ) |
            (self.U2X0 << 1 ) |
            (self.MPCM0 << 0)
        )

    def setSettings(self): 
        #NB of bits
        match self.UCSZ:
            case 0: self.nbBits = 5
            case 1: self.nbBits = 6
            case 2: self.nbBits = 7
            case 3: self.nbBits = 8
            case 7: self.nbBits = 9
            case _: self.nbBits = 8   # reserved → treat as 8

        self.nbStopBits = 2 if self.USBS0 else 1

        #UMSEL0 Bits Settings
        match self.UMSEL:
            case 0: self.opp_mode = 'Asynchronous'
            case 1: self.opp_mode = 'Synchronous'
            case 2: self.opp_mode = 'Master SPI'
            case _: self.opp_mode = '(Reserved)'

        match self.UPM:
            case 0: self.ParityMode = 'Disabled'
            case 2: self.ParityMode = 'even'
            case 3: self.ParityMode = 'odd'
            case _: self.ParityMode = 'Disabled'

    def Clock_Generator(self):
        self.baud_Tick = False
        
        if self.tickCounter >= self.UBRR0:
            self.baud_Tick = True
            self.tickCounter = 0 
        else:
            self.tickCounter += 1

        self.tickCounter += 1
        self.tickCounter &= 0xFFFF

        if self.baud_Tick:
            if self.USART_CLK_val == 0:
                self.USART_CLK_val = 1
            else:
                self.USART_CLK_val = 0

    def TX_logic(self):
    
        if self.baud_Tick == True:
            if self.TXEN0 == 1: # Enable Transmit

                if self.opp_mode == 'Asynchronous':
                    self.ticks_per_bit = 8 if self.U2X0 else 16
                else:
                    self.ticks_per_bit = 2

                if self.TXD != 0 :
                    match self.tx_state:
                        case 'IDLE':
                            self.TXD_val = 1
                            if self.TXDB_full:
                                self.tx_shift_reg = self.TXB_buffer
                                self.TXDB_full = False
                                self.TXB_buffer = 0 
                                self.UDRE0 = 1
                                self.update_UCSR0A()
                                if self.nbBits == 9:
                                    self.tx_shift_reg |= (self.TXB80 << 8)
                                self.tx_bits_left = self.nbBits
                                mask = (1 << self.nbBits) - 1
                                self.tx_parity = bin(self.tx_shift_reg & mask).count('1') & 1
                                self.tx_stop_cnt = self.nbStopBits
                                self.tx_tick_cnt = 0
                                self.tx_state = 'START'
                        
                        case 'START':
                            self.TXD_val = 0
                            self.tx_tick_cnt += 1
                            if self.tx_tick_cnt >= self.ticks_per_bit:
                                self .tx_tick_cnt = 0
                                self.tx_state = 'DATA'
                                
                        case 'DATA':
                            self.tx_tick_cnt += 1
                            if self.tx_tick_cnt >= self.ticks_per_bit:
                                self.tx_tick_cnt = 0
                                self.TXD_val = self.tx_shift_reg & 1                         
                                self.tx_shift_reg >>= 1
                                self.tx_bits_left -= 1 

                                if self.tx_bits_left <= 0:
                                    if self.ParityMode != 'Disabled':
                                        self.tx_state = 'PARITY'
                                    else:
                                        self.tx_state = 'STOP'

                        case 'PARITY':
                            self.tx_tick_cnt += 1
                            if self.tx_tick_cnt >= self.ticks_per_bit:
                                self.tx_tick_cnt = 0
                                if self.ParityMode == 'even':
                                    self.TXD_val = self.tx_parity
                                else:
                                    self.TXD_val = self.tx_parity ^ 1
                                self.tx_state = 'STOP'
                        
                        case 'STOP':
                            self.TXD_val = 1
                            self.tx_stop_cnt -= 1 
                            if self.tx_tick_cnt >= self.ticks_per_bit:
                                self.tx_tick_cnt = 0
                                self.tx_stop_cnt -= 1
                                if self.tx_stop_cnt == 0:
                                    self.TXC0 = 1
                                    self.update_UCSR0A()
                                    self.tx_state = 'IDLE'

                else:
                    self.TXD_val = 1
                    self.tx_state = 'IDLE' 

    def RX_logic(self):
            
        if self.baud_Tick == True:
            
            if self.RXEN0 == 1: # Enable Recive
                #Ticks per bit (oversampleing)

                if self.opp_mode == 'Asynchronous':
                    self.ticks_per_bit = 8 if self.U2X0 else 16
                else:
                    self.ticks_per_bit = 2

                sample_tick = self.ticks_per_bit >> 1 # midpoint

                rxd = self.RXD.get() & 1 

                match self.rx_state:
                    case 'IDLE':
                        # Wait for falling edge (START bit = logic 0)
                        if rxd == 0:
                            self.rx_tick_cnt = 0 
                            self.rx_shift_reg = 0
                            self.rx_bits_rcvd = 0 
                            self.rx_parity = 0
                            self.rx_fe = 0
                            self.rx_upe = 0
                            self.rx_state = 'START'

                    case 'START':
                        self.rx_tick_cnt += 1

                        if self.rx_tick_cnt == sample_tick:

                            if rxd == 1:
                                self.rx_state = 'IDLE'
                            else:
                                self.rx_state = 'DATA'
                                self.rx_tick_cnt = 0
                        
                    case 'DATA':
                        self.rx_tick_cnt += 1
                        if self.rx_tick_cnt == self.ticks_per_bit:
                            self.rx_tick_cnt = 0
                            bit = rxd # retriving the bit
                            self.rx_shift_reg |= (bit << self.rx_bits_rcvd)
                            self.rx_parity ^= bit # calculating the parity 
                            self.rx_bits_rcvd += 1

                            if self.rx_bits_rcvd == self.nbBits:
                                if self.ParityMode != 'Disabled':
                                    self.rx_state = 'PARITY'
                                else:
                                    self.rx_stop_cnt = self.nbStopBits
                                    self.rx_state = 'STOP'

                    case 'PARITY':
                        self.rx_tick_cnt += 1
                        if self.rx_tick_cnt == self.ticks_per_bit:
                            self.rx_tick_cnt = 0
                            parity_bit =  rxd 
                            expected_even = self.rx_parity
                            expected_odd = self.rx_parity ^ 1
                            
                            if (self.ParityMode == 'even') and (parity_bit != expected_even):
                                self.rx_upe = 1
                            elif (self.ParityMode == 'odd') and (parity_bit != expected_odd):
                                self.rx_upe = 1 
                            self.rx_stop_cnt = self.nbStopBits
                            self.rx_state = 'STOP'

                    case 'STOP':
                        self.rx_tick_cnt += 1 
                        if self.rx_tick_cnt == self.ticks_per_bit:
                            self.rx_tick_cnt = 0
                            stop_bit = rxd
                            self.rx_stop_cnt -= 1

                            if stop_bit != 1:
                                self.rx_fe = 1

                            if self.rx_stop_cnt == 0:

                                self.DOR0 = 1 if self.RXC0 else 0
                                
                                if self.readBuffer == 0 :
                                    self.readBuffer = self.rx_shift_reg & 0xFF
                                    self.rx_shift_reg_full = False
                                else:
                                    self.DOR0 = 1 # Data OverRun
                                    self.update_UCSR0A()

                                if self.nbBits == 9:
                                    bit8 = (self.rx_shift_reg >> 8) & 1
                                    self.UCSR0B = (self.UCSR0B & ~(1<<1)) | (bit8 << 1)

                                self.FE0 =self.rx_fe
                                self.UPE0 = self.rx_upe 
                                self.RXC0 = 1 
                                self.update_UCSR0A()
                                self.rx_state = 'IDLE'

            else:
                self.rx_state = 'IDLE'

    def update_interrupts(self):
        self.RXC_INT_val = 1 if (self.RXCIE0 and self.RXC0) else 0 
        self.TXC_INT_val = 1 if (self.TXCIE0 and self.TXC0) else 0
        self.UDRE_INT_val = 1 if (self.UDRIE0 and self.UDRE0) else 0

    def update_Outputs(self):
        self.TXD.prepare(self.TXD_val)
        self.RXC_INT.prepare(self.RXC_INT_val)
        self.TXC_INT.prepare(self.TXC_INT_val)
        self.UDRE_INT.prepare(self.UDRE_INT_val)
        self.USART_CLK.prepare(self.USART_CLK_val)

    def clock(self):

        self.Memory_access() # Handle any bus transactions  
        self.Parse_control_registers() # Decode control bits 
        self.setSettings() # Figure out the Settings
        self.Clock_Generator() # determine if it is a baud tick or not

        #update state machines
        self.TX_logic()
        self.RX_logic()

        #update interrupts lines
        self.update_interrupts()

        #Drive all output wires
        self.update_Outputs()

class USART_1(py4hw.Logic):
    def __init__(self,parent,name:str,memory:MemoryInterface,RXD,TXD,USART_CLK,RXC_INT,TXC_INT,UDRE_INT):
        super().__init__(parent, name)

        self.interface = self.addInterfaceSink('port',memory)

        #Physical Pins
        self.RXD = self.addIn('RXD',RXD)
        self.TXD = self.addOut('TXD',TXD)
        self.USART_CLK = self.addIn('USART_CLK',USART_CLK)

        #Interrupts
        self.RXC_INT = self.addOut('RXC_INIT',RXC_INT)
        self.TXC_INT = self.addOut('TXC_INT', TXC_INT)
        self.UDRE_INT = self.addIn('UDRE_INT', UDRE_INT)

        self.TXD_val = 1
        self.RXC_INT_val = 0
        self.TXC_INT_val = 0
        self.USART_CLK_val = 0
        self.UDRE_INT_val = 0

        self.UCSR0A = 0x20 # Bit5: UDRE0 is 1 by default (Buffer Empty)
        self.UCSR0A_addr_LS = 0xC0

        self.UCSR0B = 0
        self.UCSR0B_addr_LS = 0xC1

        self.UCSR0C = 0x06 # Default: Async, No parity, 1 stop bit, 8 data bits
        self.UCSR0C_addr_LS = 0xC2

        self.UBRR0L = 0
        self.UBRR0L_addr_LS = 0xC4

        self.UBRR0H = 0
        self.UBRR0H_addr_LS = 0xC5

#       self.UDR0 = 0
        self.UDR0_addr_LS = 0xC6

        #Internal Data Buffers
        self.RXB_buffer = 0
        self.readBuffer = 0
        self.TXB_buffer = 0
        self.TXDB_full = False

        #Control & Status Bits
        #UCSR0A
        self.RXC0 = 0 
        self.TXC0 = 0
        self.UDRE0 = 1  
        self.FE0 = 0
        self.DOR0 = 0
        self.UPE0 = 0
        self.U2X0 = 0
        self.MPCM0 = 0

        #UCSR0B
        self.RXCIE0 = 0
        self.TXCIE0 = 0
        self.UDRIE0 = 0
        self.RXEN0 = 0
        self.TXEN0 = 0
        self.UCSZ02 = 0
        self.RXB80 = 0
        self.TXB80 = 0

        #UCSR0C
        self.UMSEL01 = 0
        self.UMSEL00 = 0
        self.UPM01 = 0
        self.UPM00 = 0
        self.USBS0 = 0
        self.UCSZ01 = 1
        self.UCSZ00 = 1
        self.UCPOL0 =0


        self.opp_mode = 'Asynchronous'
        self.nbBits = 8
        self.nbStopBits = 1
        self.ParityMode = 'Disabled' #Disabled even odd


        self.rx_fifo = []
        self.rx_dor_flag = 0

        self.TXB_buffer = 0
        self.TXDB_full = False

        # Transmit/Receive State Machines
        self.baud_counter = 0
        self.tx_state = 'IDLE' # 'IDLE' START' 'DATA' 'PARITY' 'STOP'  
        self.tx_shift_reg = 0
        self.tx_bits_left = 0
        self.tx_stop_cnt = 0
        self.tx_parity = 0
        self.tx_tick_cnt = 0
        
        self.rx_state = 'IDLE' # 'IDLE' START' 'DATA' 'PARITY' 'STOP'  
        self.rx_shift_reg = 0
        self.rx_bits_rcvd = 0
        self.rx_stop_cnt = 0
        self.rx_tick_cnt = 0
        self.rx_parity = 0 
        self.rx_fe = 0
        self.rx_upe = 0
        
        self.rx_shift_reg_full = False

        self.baud_Tick = False
        self.tickCounter = 0

        # RX FIFO Level 0 (Front of the queue - what the CPU reads)
        self.rx_fifo_data_0 = 0
        self.rx_fifo_fe_0 = 0
        self.rx_fifo_upe_0 = 0

        # RX FIFO Level 1 (Back of the queue)
        self.rx_fifo_data_1 = 0
        self.rx_fifo_fe_1 = 0
        self.rx_fifo_upe_1 = 0

        #Hardware Counters/Flags
        self.rx_fifo_items = 0
        self.readValue = 0

    def Update_fifo(self):
        self.rx_fifo_data_0 = self.rx_fifo_data_1
        self.rx_fifo_fe_0 = self.rx_fifo_fe_1
        self.rx_fifo_upe_0 = self.rx_fifo_upe_1

        #self.rx_fifo_data_1 
        #self.rx_fifo_fe_1 =
        #self.rx_fifo_upe_1 =

    def Memory_access(self):
        ADDR = self.interface.address.get()
        read_opp = (self.interface.read.get() == 1) and (self.interface.write.get() == 0)
        write_opp = (self.interface.read.get() == 0) and (self.interface.write.get() == 1)
        valid_ins = self.interface.instype.get() == 1 

        if valid_ins:
            if ADDR == self.UCSR0A_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UCSR0A)
                    self.interface.resp.prepare(1)
                elif write_opp:
                    data =  self.interface.write_data.get()
                    if data & (1<<6):
                        self.UCSR0A &= ~(1<<6) # clear TXC0
                    self.UCSR0A = (self.UCSR0A & 0b11111100) | (data & 0b00000011)

                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UCSR0B_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UCSR0B)
                    self.interface.resp.prepare(1)
                elif write_opp:

                    data = self.interface.write_data.get()
                    self.UCSR0B = (data & ~(1 << 1)) | (self.UCSR0B & (1 << 1))

                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UCSR0C_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UCSR0C)
                    self.interface.resp.prepare(1)
                elif write_opp:
                    self.UCSR0C = self.interface.write_data.get()
                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UBRR0L_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UBRR0L)
                    self.interface.resp.prepare(1)
                elif write_opp:
                    self.UBRR0L = self.interface.write_data.get()
                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UBRR0H_addr_LS:
                if read_opp:
                    self.interface.read_data.prepare(self.UBRR0H)
                    self.interface.resp.prepare(1)
                elif write_opp:
                    self.UBRR0H = self.interface.write_data.get() & 0x0F
                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            elif ADDR == self.UDR0_addr_LS:
                if read_opp:
                    if len(self.rx_fifo) > 0:

                        packet = self.rx_fifo.pop(0)
                        self.interface.read_data.prepare(self.rx_fifo[0])

                        self.FE0 = 0


                    self.interface.resp.prepare(1)
                elif write_opp:
                    data = self.interface.write_data.get() & 0xFF

                    if not self.TXDB_full:
                        self.TXB_buffer = data
                        self.TXDB_full = True
                        # Clear UDRE0 — buffer is now occupied
                        self.UDRE0 = 0
                        self.TXC0 = 0
                        self.update_UCSR0A()

                    self.interface.resp.prepare(1)
                else:
                    self.interface.resp.prepare(0)
            else:
                self.interface.resp.prepare(0)

    def Parse_control_registers(self):
        #Control & Status Bits
        #UCSR0A
        self.RXC0 = (self.UCSR0A>>7)&1
        self.TXC0 = (self.UCSR0A>>6)&1
        self.UDRE0 = (self.UCSR0A>>5)&1  
        self.FE0 = (self.UCSR0A>>4)&1
        self.DDR0 = (self.UCSR0A>>3)&1
        self.UPE0 = (self.UCSR0A>>2)&1
        self.U2X0 = (self.UCSR0A>>1)&1
        self.MPCM0 = (self.UCSR0A>>0)&1

        #UCSR0B
        self.RXCIE0 = (self.UCSR0B>>7)&1
        self.TXCIE0 = (self.UCSR0B>>6)&1
        self.UDRIE0 = (self.UCSR0B>>5)&1
        self.RXEN0 = (self.UCSR0B>>4)&1
        self.TXEN0 = (self.UCSR0B>>3)&1
        self.UCSZ02 = (self.UCSR0B>>2)&1
        self.RXB80 = (self.UCSR0B>>1)&1
        self.TXB80 = (self.UCSR0B>>0)&1

        #UCSR0C
        self.UMSEL01 = (self.UCSR0C>>7)&1
        self.UMSEL00 = (self.UCSR0C>>6)&1
        self.UPM01 = (self.UCSR0C>>5)&1
        self.UPM00 = (self.UCSR0C>>4)&1
        self.USBS0 = (self.UCSR0C>>3)&1
        self.UCSZ01 = (self.UCSR0C>>2)&1
        self.UCSZ00 = (self.UCSR0C>>1)&1
        self.UCPOL0 = (self.UCSR0C>>0)&1

        # Composed fields
        self.UBRR0 = ((self.UBRR0H&0xF)<<8) | self.UBRR0L
        self.UCSZ = (self.UCSZ02 << 2) | (self.UCSZ01<<1) | (self.UCSZ00<<0) 
        self.UMSEL = (self.UMSEL01<<1) | self.UMSEL00
        self.UPM = (self.UPM01<<1) | self.UPM00

    def update_UCSR0A(self):
        self.UCSR0A = (
            (self.RXC0 << 7 ) |
            (self.TXC0 << 6 ) |
            (self.UDRE0 << 5) |
            (self.FE0 << 4  ) |
            (self.DDR0 << 3 ) |
            (self.UPE0 << 2 ) |
            (self.U2X0 << 1 ) |
            (self.MPCM0 << 0)
        )

    def setSettings(self): 
        #NB of bits
        match self.UCSZ:
            case 0: self.nbBits = 5
            case 1: self.nbBits = 6
            case 2: self.nbBits = 7
            case 3: self.nbBits = 8
            case 7: self.nbBits = 9
            case _: self.nbBits = 8   # reserved → treat as 8


        self.nbStopBits = 2 if self.USBS0 else 1

        #UMSEL0 Bits Settings
        match self.UMSEL:
            case 0: self.opp_mode = 'Asynchronous'
            case 1: self.opp_mode = 'Synchronous'
            case 2: self.opp_mode = 'Master SPI'
            case _: self.opp_mode = '(Reserved)'

        match self.UPM:
            case 0: self.ParityMode = 'Disabled'
            case 2: self.ParityMode = 'even'
            case 3: self.ParityMode = 'odd'
            case _: self.ParityMode = 'Disabled'

    def Clock_Generator(self):
        self.baud_Tick = False
        
        if self.tickCounter >= self.UBRR0:
            self.baud_Tick = True
            self.tickCounter = 0 
        else:
            self.tickCounter += 1

        if self.baud_Tick:
            self.USART_CLK_val = 1 ^ self.USART_CLK_val

    def TX_logic(self):
        if self.baud_Tick == True:
            if self.TXEN0 == 1: # Enable Transmit

                if self.opp_mode == 'Asynchronous':
                    self.ticks_per_bit = 8 if self.U2X0 else 16
                else:
                    self.ticks_per_bit = 2

                if self.TXD != 0 :
                    match self.tx_state:
                        case 'IDLE':
                            self.TXD_val = 1
                            if self.TXDB_full:

                                self.tx_shift_reg = self.TXB_buffer
                                self.TXDB_full = False
                                self.TXB = 0 
                                self.UDRE0 = 1
                                self.update_UCSR0A()

                                if self.nbBits == 9:
                                    self.tx_shift_reg |= (self.TXB80 << 8)
                                self.tx_bits_left = self.nbBits

                                mask = (1 << self.nbBits) - 1
                                
                                self.tx_parity = bin(self.tx_shift_reg & mask).count('1') & 1
                                self.tx_stop_cnt = self.nbStopBits
                                self.tx_tick_cnt = 0
                                self.tx_state = 'START'
                        
                        case 'START':

                            self.TXD_val = 0
                            self.tx_tick_cnt += 1
                            if self.tx_tick_cnt >= self.ticks_per_bit:
                                self.tx_tick_cnt = 0
                                self.tx_state = 'DATA'
                                

                        case 'DATA':
                            
                            self.tx_tick_cnt += 1
                            if self.tx_tick_cnt >= self.ticks_per_bit:
                                self.tx_tick_cnt = 0
                                self.TXD_val = self.tx_shift_reg & 1                         
                                self.tx_shift_reg >>= 1
                                self.tx_bits_left -= 1 
                                if self.tx_bits_left == 0:
                                    if self.ParityMode != 'Disabled':
                                        self.tx_state = 'PARITY'
                                    else:
                                        self.tx_state = 'STOP'

                        case 'PARITY':
                            self.tx_tick_cnt += 1
                            if self.tx_tick_cnt >= self.ticks_per_bit:
                                self.tx_tick_cnt = 0
                                if self.ParityMode == 'even':
                                    self.TXD_val = self.tx_parity
                                else:
                                    self.TXD_val = self.tx_parity ^ 1
                                self.tx_state = 'STOP'
                        

                        case 'STOP':

                            self.TXD_val = 1
                            self.tx_stop_cnt -= 1 
                            if self.tx_tick_cnt >= self.ticks_per_bit:
                                self.tx_tick_cnt = 0
                                self.tx_stop_cnt -= 1
                                if self.tx_stop_cnt == 0:
                                    self.TXC0 = 1
                                    self.update_UCSR0A()
                                    self.tx_state = 'IDLE'

            
                else:
                    self.TXD_val = 1
                    self.tx_state = 'IDLE' 

    def RX_logic(self):
            
        if self.baud_Tick == True:
            
            if self.RXEN0 == 1: # Enable Recive
                #Ticks per bit (oversampleing)

                if self.opp_mode == 'Asynchronous':
                    self.ticks_per_bit = 8 if self.U2X0 else 16
                else:
                    self.ticks_per_bit = 2

                sample_tick = self.ticks_per_bit >>1 # midpoint

                rxd = self.RXD.get() & 1 

                match self.rx_state:
                    case 'IDLE':
                        # Wait for falling edge (START bit = logic 0)
                        if rxd == 0:
                            self.rx_tick_cnt = 0 
                            self.rx_shift_reg = 0
                            self.rx_bits_rcvd = 0 
                            self.rx_parity = 0
                            self.rx_fe = 0
                            self.rx_upe = 0
                            self.rx_state = 'START'

                    case 'START':
                        self.rx_tick_cnt += 1

                        if self.rx_tick_cnt == sample_tick:

                            if rxd == 1:
                                self.rx_state = 'IDLE'
                            else:
                                self.rx_state = 'DATA'
                                self.rx_tick_cnt = 0
                        
                    case 'DATA':
                        self.rx_tick_cnt += 1
                        if self.rx_tick_cnt == self.ticks_per_bit:
                            self.rx_tick_cnt = 0
                            bit = rxd # retriving the bit
                            self.rx_shift_reg |= (bit << self.rx_bits_rcvd)
                            self.rx_parity ^= bit # calculating the parity 
                            self.rx_bits_rcvd += 1
                            if self.rx_bits_rcvd == self.nbBits:
                                if self.ParityMode != 'Disabled':
                                    self.rx_state = 'PARITY'
                                else:
                                    self.rx_stop_cnt = self.nbStopBits
                                    self.rx_state = 'STOP'

                    case 'PARITY':
                        self.rx_tick_cnt += 1
                        if self.rx_tick_cnt == self.ticks_per_bit:
                            self.rx_tick_cnt = 0
                            parity_bit =  rxd 
                            expected_even = self.rx_parity
                            expected_odd = self.rx_parity ^ 1
                            if (self.ParityMode == 'even') and (parity_bit != expected_even):
                                self.rx_upe = 1
                            elif (self.ParityMode == 'odd') and (parity_bit != expected_odd):
                                self.rx_upe = 1 
                            self.rx_stop_cnt = self.nbStopBits
                            self.rx_state = 'STOP'

                    case 'STOP':
                        self.rx_tick_cnt += 1 
                        if self.rx_tick_cnt == self.ticks_per_bit:
                            self.rx_tick_cnt = 0
                            stop_bit = rxd
                            self.rx_stop_cnt -= 1

                            if stop_bit != 1:
                                self.rx_fe = 1

                            if self.rx_stop_cnt == 0:

                                self.DOR0 = 1 if self.RXC0 else 0
                                
                                if self.readBuffer == 0 :
                                    self.readBuffer = self.rx_shift_reg & 0xFF
                                    self.rx_shift_reg_full = False
                                else:
                                    self.DOR0 = 1 # Data OverRun
                                    self.update_UCSR0A()

                                if self.nbBits == 9:
                                    bit8 = (self.rx_shift_reg >> 8) & 1
                                    self.UCSR0B = (self.UCSR0B & ~(1<<1)) | (bit8 << 1)

                                self.FE0 = self.rx_fe
                                self.UPE0 = self.rx_upe 
                                self.RXC0 = 1 
                                self.update_UCSR0A()
                                self.rx_state = 'IDLE'

            
            else:
                self.rx_state = 'IDLE'

    def update_interrupts(self):
        self.RXC_INT_val = 1 if (self.RXCIE0 and self.RXC0) else 0 
        self.TXC_INT_val = 1 if (self.TXCIE0 and self.TXC0) else 0
        self.UDRE_INT_val = 1 if (self.UDRIE0 and self.UDRE0) else 0

    def update_Outputs(self):
        self.TXD.prepare(self.TXD_val)
        self.RXC_INT.prepare(self.RXC_INT_val)
        self.TXC_INT.prepare(self.TXC_INT_val)
        self.UDRE_INT.prepare(self.UDRE_INT_val)
        #self.USART_CLK.prepare(self.USART_CLK_val)

    def clock(self):

        self.Memory_access() # Handle any bus transactions  
        self.Parse_control_registers() # Decode control bits 
        self.setSettings() # Figure out the Settings
        self.Clock_Generator() # determine if it is a baud tick or not

        #update state machines
        self.TX_logic()
        self.RX_logic()

        #update interrupts lines
        self.update_interrupts()

        #Drive all output wires
        self.update_Outputs()
        
        
class VirtualUSART(py4hw.Logic):
    def __init__(self, parent, name, mem: MemoryInterface, debug: bool = False):
        super().__init__(parent, name)
        
        self.mem = self.addInterfaceSink('', mem)
        self.status_control_A = UCSRA_UDRE
        self.status_control_B = 0
        self.status_control_C = 0
        self.console = ''
        self.debug = debug
        
        # --- Track previous states for edge detection ---
        self.prev_write = False
        self.prev_read = False
        
    def clock(self):
        add = self.mem.address.get()
        v = self.mem.write_data.get()
        
        # Capture current memory states
        is_write = (self.mem.write.get() == 1)
        is_read = (self.mem.read.get() == 1)
        
        # Detect rising edges (first clock cycle of the operation)
        is_new_write = is_write and not self.prev_write
        is_new_read = is_read and not self.prev_read
        
        if is_write:
            if (add == UCSRA_REG):
                self.status_control_A = v
            elif (add == UCSRB_REG):
                self.status_control_B = v
            elif (add == UCSRC_REG):
                self.status_control_C = v
            elif (add == UBRRH_REG):
                self.baud_rate_h = v
            elif (add == UBRRL_REG):
                self.baud_rate_l = v     
            elif (add == UDR_REG):
                # --- EDGE DETECTION: Only append on the first cycle ---
                if is_new_write:
                    char = chr(v)
                    self.console += char
                    
                    # --- Output directly to the terminal ---
                    print(char, end='', flush=True) 
            else:
                if is_new_write:
                    print(f'\nWARNING Writing to the USART: {add:04X}={v:02X}')
                
            self.mem.resp.prepare(1)
            
        elif is_read:
            if (add == UCSRA_REG):
                self.mem.read_data.prepare(self.status_control_A)
            else:
                if is_new_read:
                    print(f'\nWARNING Reading to the USART: {add:04X}')
            self.mem.resp.prepare(1)
            
        else:
            self.mem.resp.prepare(0)

        # --- AI-Friendly State & I/O Trace ---
        if self.debug:
            trace_log = (
                f"\nUSART_TRACE | "
                f"status_control_A: {self.status_control_A} | "
                f"status_control_B: {self.status_control_B} | "
                f"status_control_C: {self.status_control_C} | "
                f"Console: {repr(self.console)}"
            )
            
            # --- EDGE DETECTION: Only print once per read/write cycle ---
            if is_new_write or is_new_read:
                print(trace_log)
                
        # Update history for the next clock tick
        self.prev_write = is_write
        self.prev_read = is_read