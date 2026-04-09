# THE MC IS : ATMEGA328P

## Functional caracteristics

AVR Core : AVRe+ 
Missing instructions: ELPM, EIJMP, EICALL

32 8Bit registers
32Kbytes of self-programmable flash
1Kbytes of EEPROM
2Kbytes internal SRAM 

Program Counter : 15bits 

### Block Diagram of the AVR Architecture:

![Block Diagram of the AVR Architecture](./Images/Block%20Diagram%20of%20the%20AVR%20Architecture.png)





### Peripherals

- GPIO
- Timer/Counters
- UART
- Basic ADC
- SPI
- I2C
- Interrupt handling
- ROM loader for .hex files


### Memory

#### Program Memory 

![Program Memory](./Images/Program%20Memory%20Map.png)

#### Data Memory 

![Data Memory](./Images/Data%20Memory%20Map.png)


### Implementation 


## Instruction Set
Status Register (SREG) 

### ALU

|Instruction|Operands|Description|Operation|Binary|Flags|Clock Cycles|Operands|
|-----------|--------|-----------|---------|------|-----|------|--------|
|ADD|Rd,Rr|Add two registers| Rd <- Rd + Rr|0000 11rd dddd rrrr|Z,C,N,VH|1|0 <= d <= 31 , 0 <= r <= 31|
|ADC|Rd,Rr|Add with carry two registers| Rd <- Rd + Rr + C|0001 11rd dddd rrrr|Z,C,N,VH|1|0 <= d <= 31 , 0 <= r <= 3|
|ADIW|Rdl,K|Add immediate to word|Rdl <- Rdl + K|1001 0110 KKdd KKKK|Z,C,N,V,S|2|d=[24,26,28,30], 0 <= K <=63|
|SUB|Rd,Rr|Substract two registers|Rd <- Rd - Rr|0001 10rd dddd rrrr|Z,C,N,V,H|1|0 <= d <= 31 , 0 <= r <= 3|
|SUBI|Rd,K|Subtract constant from register | Rd <- Rd - K|0101 KKKK dddd KKKK|Z,C,N,V,H|1|16 <= d < 31 , 0 <= K <= 255|
|SBC|Rd,Rr|Subtract with carry two registers|Rd <- Rd – Rr – C|0000 10rd dddd rrrr|Z,C,N,V,H|1|0 <= d <= 31 , 0 <= r <= 3|
|SBCI|Rd,Rr|Subtract with carry two registers| Rd <- Rd – Rr – C|0100 KKKK dddd KKKK|Z,C,N,V,H|1|16 <= d <=31,0 <= K <= 255|
|SBIW|Rdl,K| Subtract immediate from word|Rdh: Rdl <- Rdh: Rdl – K|1001 0111 KKdd KKKK|Z,C,N,V,S|2|d=[24,26,28,30],0 <= K <=63|
|AND|Rd,Rr|Logical AND registers|Rd <- Rd x Rr|0010 00rd dddd rrrr|Z,N,V|1|0 <= d <= 31 , 0 <= r <= 31|
|ANDI|Rd,K|Logical AND register and constant| Rd <- Rd x K|0111 KKKK dddd KKKK|Z,N,V|1|16 <= d < 31 , 0 <= K <= 255|
|OR|Rd, Rr|Logical OR registers | Rd <- Rd v Rr|0010 10rd dddd rrrr|Z,N,V|1|0 <= d <= 31 , 0 <= r <= 31|
|ORI|Rd, K|Logical OR register and constant| Rd <- Rd v K|0110 KKKK dddd KKKK|Z,N,V|1|16 <= d < 31 , 0 <= K <= 255|
|EOR|Rd, Rr|Exclusive OR registers|Rd <- Rd XOR Rr|0010 01rd dddd rrrr|Z,N,V|1|0 <= d <= 31 , 0 <= r <= 31|
|COM|Rd|One’s complement|Rd <- 0xFF - Rd|1001 010d dddd 0000|Z,C,N,V|1|0 <= d <= 31|
|NEG|Rd|Two’s complement|Rd <- 0x00 - Rd|1001 010d dddd 0001|Z,C,N,V,H|1|0 <= d <= 31|
|SBR|Rd, K|Set bit(s) in register|Rd <- Rd v K|0110 KKKK dddd KKKK|Z,N,V|1|16 <= d < 31 , 0 <= K <= 255|
|CBR|Rd, K|Clear bit(s) in register|Rd <- Rd x (0xFF - K)|0111 XXXX dddd XXXX|Z,N,V|1| 16 <= d < 31 , 0 <= K <= 255 , X = (0xFF - K)|
|INC|Rd|Increment|Rd <- Rd + 1|1001 010d dddd 0011|Z,N,V|1|0 <= d <= 31|
|DEC|Rd|Decrement|Rd <- Rd - 1|1001 010d dddd 1010|Z,N,V|1|0 <= d <= 31|
|TST|Rd|Test for zero or minus|Rd <- Rd x Rd|0010 00dd dddd dddd|Z,N,V|1|0 <= d <= 31|
|CLR|Rd|Clear register|Rd <- Rd XOR Rd|1001 0100 1sss 1000|Z,N,V|1|0 <= s <= 7|
|SER|Rd|Set register|Rd <- 0xFF|1110 1111 dddd 1111|None|1|16 <= d < 31|
|MUL|Rd, Rr|Multiply unsigned|R1:R0 <- Rd x Rr|1001 11rd dddd rrrr|Z,C|2|0 <= d <= 31 , 0 <= r <= 31|
|MULS|Rd, Rr|Multiply signed|R1:R0 <- Rd x Rr|0000 0010 dddd rrrr|Z,C|2|0 <= d <= 31 , 0 <= r <= 31|
|MULSU|Rd, Rr|Multiply signed with unsigned|R1:R0 <- Rd x Rr|0000 0011 0ddd 0rrr|Z,C|2|0 <= d <= 31 , 0 <= r <= 31|
|FMUL|Rd, Rr|Fractional multiply unsigned|R1:R0 <- (Rd x Rr) << 1|0000 0011 0ddd 1rrr|Z,C|2|0 <= d <= 31 , 0 <= r <= 31|
|FMULS|Rd, Rr|Fractional multiply signed|R1:R0 <-(Rd x Rr) << 1|0000 0011 1ddd 0rrr|Z,C|2|0 <= d <= 31 , 0 <= r <= 31|
|FMULSU|Rd, Rr|Fractional multiply signed with unsigned|R1:R0 <-(Rd x Rr) << 1|0000 0011 1ddd 1rrr|Z,C|2|0 <= d <= 31 , 0 <= r <= 31|


### Branch Instructions


|Instruction|Operands|Description|Operation|Binary|Flags|Clock Cycles|Operands|
|-----------|--------|-----------|---------|------|-----|------|--------|
|RJMP|K|Relative jump|PC <- PC + K + 1|1100 KKKK KKKK KKKK|NONE|2|k-2k<= K <= 2|
|IJMP||Indirect jump to (Z)|PC <- Z|1001 0100 0000 1001|NONE|2||
|JMP|K|Direct jump|PC <- K|1001 010K KKKK 110K KKKK KKKK KKKK KKKK|NONE|3|0 <= K<= 4M|
|RCALL|K|Relative subroutine call|PC <- PC + K +1|1101 KKKK KKKK KKKK|NONE|3||
|ICALL||Indirect call to (Z)|PC <- Z|1001 0101 0000 1001|NONE|3||
|CALL|K|Direct subroutine call| PC <- K|1001 010K KKKK 111K KKKK KKKK KKKK KKKK|NONE|4||
|RET||Subroutine return|PC <- STACK|1001 0101 0000 1000|NONE|4||
|RETI||Interrupt return|PC <- STACK|1001 0101 0001 1000|I|4||
|CPSE|Rd, Rr|Compare, skip if equal|if (Rd = Rr) PC<- PC +2 or 3|0001 00rd dddd rrrr|NONE|1/2/3|
|CP|Rd, Rr|Compare|Rd-Rr|0001 01rd dddd rrrr|Z,N,V,C,H|1|0 <= d <= 31 , 0 <= r <= 31|
|CPC|Rd, Rr|Compare with carry|Rd-Rr-C|0000 01rd dddd rrrr|Z, N,V,C,H|1|0 <= d <= 31 , 0 <= r <= 31|
|CPI|Rd, K|Compare register with immediate|if (Rr (b) = 0) PC<- PC +2 or 3| 0011 KKKK dddd KKKK|Z,N,V,C,H
|SBRC|Rr, b|Skip if bit in register cleared|if (Rr(b)=1)  PC<- PC +2 or 3| 
|SBRS|Rr, b|Skip if bit in register is set|if (Rr(b)=1)  PC<- PC +2 or 3|
|SBIC|P, b|Skip if bit in I/O register cleared|if (Rr(b)=1)  PC<- PC +2 or 3| 
|SBIS|P, b|Skip if bit in I/O register is set|if (Rr(b)=1)  PC<- PC +2 or 3| 
|BRBS|s, k|Branch if status flag set|if (Rr(b)=1)  PC<- PC +2 or 3| 
|BRBC|s, k|Branch if status flag cleared|if (Rr(b)=1)  PC<- PC +2 or 3| 
|BREQ|K|Branch if equal|if (Z = 1) then PC <- PC + K + 1|
|BRNE|K|Branch if not equal|if (Z = 0) then PC <- PC + K + 1|
|BRCS|K|Branch if carry set|if (C = 1) then PC <- PC + K + 1|
|BRCC|K|Branch if carry cleared|if (C = 0) then PC <- PC + K + 1|
|BRSH|K|Branch if same or higher|if (C = 0) then  PC <- PC + K + 1|
|BRLO|K|Branch if lower|if (C = 1) then PC <- PC + K + 1|
|BRMI|K|Branch if minus|if (N = 1) then PC <- PC + K + 1|
|BRPL|K|Branch if plus|if (N = 0) then PC <- PC + K + 1|
|BRGE|K|Branch if greater or equal, signed|if (N XOR V= 0) then PC <- PC + K + 1|
|BRLT|K|Branch if less than zero, signed|if (N XOR V= 1) then PC <- PC + K + 1|
|BRHS|K|Branch if half carry flag set|if (H = 1) then PC <- PC + K + 1|
|BRHC|K|Branch if half carry flag cleared|if (H = 0) then PC <- PC + K + 1|
|BRTS|K|Branch if T flag set|if (T = 1) then PC <- PC + K + 1|
|BRTC|K|Branch if T flag cleared|if (T = 0) then PC <- PC + K + 1|
|BRVS|K|Branch if overflow flag is set|if (V = 1) then PC <- PC + K + 1|
|BRVC|K|Branch if overflow flag is cleared|if (V = 0) then PC <- PC + K + 1|
|BRIE|K|Branch if interrupt enabled|if (I = 1) then PC <- PC + K + 1|
|BRID|K|Branch if interrupt disabled|if (I = 0) then PC <- PC + K + 1|


### Bit and Bit-Test Instructions 

|Instruction|Operands|Description|Operation|Binary|Flags|Clock Cycles|Operands|
|-----------|--------|-----------|---------|------|-----|------|--------|
|SBI|P, b|Set bit in I/O register|
|CBI|P, b|Clear bit in I/O register|
|LSL|Rd|Logical shift left|
|LSR|Rd|Logical shift right|
|ROL|Rd|Rotate left through carry|
|ROR|Rd|Rotate right through carry|
|ASR|Rd|Arithmetic shift right|
|SWAP|Rd|Swap nibbles|
|BSET|S|Flag set|
|BCLR|S|Flag clear|
|BST|Rr,b|Bit store from register to T|
|BLD|Rd,b|Bit load from T to register|
|SEC|Set carry|
|CLC|Clear carry|
|SEN|Set negative flag|
|CLN|Clear negative flag|
|SEZ|Set zero flag|
|CLZ|Clear zero flag|
|SEI|Global interrupt enable|
|CLI|Global interrupt disable|
|SES|Set signed test flag|
|CLS|Clear signed test flag|
|SEV|Set twos complement overflow|
|CLV|Clear twos complement overflow|
|SET|Set T in SREG|
|CLT|Clear T in SREG|
|SEH|Set half carry flag in SREG|
|CLH|Clear half carry flag in SREG|

### Data Transfer Instructions

|Instruction|Operands|Description|Operation|Binary|Flags|Clock Cycles|Operands|
|-----------|--------|-----------|---------|------|-----|------|--------|
|MOV|Rd, Rr|Move between registers|
|MOVW|Rd, Rr|Copy register word|
|LDI|Rd, K|Load immediate|
|LD|Rd, X|Load indirect|
|LD|Rd, X+|Load indirect and post-inc|
|LD|Rd, – X|Load indirect and pre-dec|
|LD|Rd, Y|Load indirect|
|LD|Rd, Y+|Load indirect and post-inc|
|LD|Rd, – Y|Load indirect and pre-dec|
|LDD|Rd, Y+ q|Load indirect with displacement|
|LD|Rd, Z|Load indirect|
|LD|Rd, Z+|Load indirect and post-inc|
|LD|Rd, –Z|Load indirect and pre-dec|
|LDD|Rd, Z+ q|Load indirect with displacement|
|LDS|Rd, k|Load direct from SRAM|
|ST|X, Rr|Store indirect|
|ST|X+, Rr|Store indirect and post-inc|
|ST|– X, Rr|Store indirect and pre-dec|
|ST|Y, Rr|Store indirect|
|ST|Y+, Rr|Store indirect and post-inc|
|ST|– Y, Rr|Store indirect and pre-dec|
|STD|Y+ q, Rr|Store indirect with displacement|
|ST|Z, Rr|Store indirect|(Y)<-Rr|
|ST|Z +, Rr|Store indirect and post-inc|(Y)<-Rr,Y<-Y+1|
|ST|–Z, Rr|Store indirect and pre-dec| Y<-Y-1,(Y)<-Rr|
|STD|Z + q, Rr|Store indirect with displacement| (Y+q) <- Rr|
|STS|k, Rr|Store direct to SRAM|(K) <- Rr|
|LPM||Load program memory| R0 <- (Z)|
|LPM|Rd, Z|Load program memory| Rd <- (Z)|
|LPM|Rd, Z+|Load program memory and post-inc|Rd <- (Z), Z<-Z+1|
|SPM||Store program memory| (Z) <- R1:R0|
|IN|Rd, P|In port|Rd <- P|
|OUT|P, Rr|Out port|P <- Rr|
|PUSH|Rr|Push register on stack| STACK <- Rr|
|POP|Rd|Pop register from stack| Rd <- STACK|

### MCU Control Instructions

|Instruction|Operands|Description|Operation|Binary|Flags|Clock Cycles|Operands|
|-----------|--------|-----------|---------|------|-----|------|--------|
|NOP||No operation|
|SLEEP||Sleep|
|WDR||Watchdog reset|
|BREAK||Break|