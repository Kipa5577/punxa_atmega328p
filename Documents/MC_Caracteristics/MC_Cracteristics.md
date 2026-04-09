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
|ADD|Rd,Rr|Add two registers| Rd <- Rd + Rr|0000 11rd dddd rrrr|Z,C,N,V,H|1|0 <= d <= 31 , 0 <= r <= 31|
|ADC|Rd,Rr|Add with carry two registers| Rd <- Rd + Rr + C|0001 11rd dddd rrrr|Z,C,N,V,H|1|0 <= d <= 31 , 0 <= r <= 3|
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
|CPI|Rd, K|Compare register with immediate|if (Rr (b) = 0) PC<- PC +2 or 3| 0011 KKKK dddd KKKK|Z,N,V,C,H|
|SBRC|Rr, b|Skip if bit in register cleared|if (Rr(b)=1)  PC<- PC +2 or 3|1111 110r rrrr 0bbb|NONE|1/2/3|
|SBRS|Rr, b|Skip if bit in register is set|if (Rr(b)=1)  PC<- PC +2 or 3|1111 111r rrrr 0bbb|NONE|1/2/3|
|SBIC|P, b|Skip if bit in I/O register cleared|if (Rr(b)=1)  PC<- PC +2 or 3|1001 1001 AAAA Abbb|NONE|1/2/3|0 <= A <= 31 , 0 <= b <=7|
|SBIS|P, b|Skip if bit in I/O register is set|if (Rr(b)=1)  PC<- PC +2 or 3|1001 1011 AAAA Abbb|NONE|1/2/3|0 <= A <= 31 , 0 <= b <=7|
|BRBS|s, k|Branch if status flag set|if (Rr(b)=1)  PC<- PC +2 or 3|1111 00kk kkkk ksss|NONE|1/2|0<=s<=7,-64<= k <= 63|
|BRBC|s, k|Branch if status flag cleared|if (Rr(b)=1)  PC<- PC +2 or 3|1111 01kk kkkk ksss|NONE|1/2|0<=s<=7,-64<= k <= 63|
|BREQ|K|Branch if equal|if (Z = 1) then PC <- PC + K + 1|1111 00KK KKKK K001|NONE|1/2|0<=s<=7,-64<= k <= 63|
|BRNE|K|Branch if not equal|if (Z = 0) then PC <- PC + K + 1|1111 01KK KKKK K001|NONE|1/2|-64<= k <= 63|
|BRCS|K|Branch if carry set|if (C = 1) then PC <- PC + K + 1|1111 00KK KKKK K000|NONE|1/2|-64<= k <= 63|
|BRCC|K|Branch if carry cleared|if (C = 0) then PC <- PC + K + 1|1111 01KK KKKK K001|NONE|1/2|-64<= k <= 63|
|BRSH|K|Branch if same or higher|if (C = 0) then  PC <- PC + K + 1|1111 01KK KKKK K000|NONE|1/2|-64<= k <= 63|
|BRLO|K|Branch if lower|if (C = 1) then PC <- PC + K + 1|1111 00KK KKKK K000|NONE|1/2|-64<= k <= 63|
|BRMI|K|Branch if minus|if (N = 1) then PC <- PC + K + 1|1111 00KK KKKK K010|NONE|1/2|-64<= k <= 63|
|BRPL|K|Branch if plus|if (N = 0) then PC <- PC + K + 1|1111 01KK KKKK K010|NONE|1/2|-64<= k <= 63|
|BRGE|K|Branch if greater or equal, signed|if (N XOR V= 0) then PC <- PC + K + 1|1111 01KK KKKK K100|NONE|1/2|-64<= k <= 63|
|BRLT|K|Branch if less than zero, signed|if (N XOR V= 1) then PC <- PC + K + 1|1111 00KK KKKK K100|NONE|1/2|-64<= k <= 63|
|BRHS|K|Branch if half carry flag set|if (H = 1) then PC <- PC + K + 1|1111 00KK KKKK K101|NONE|1/2|-64<= k <= 63|
|BRHC|K|Branch if half carry flag cleared|if (H = 0) then PC <- PC + K + 1|1111 01KK KKKK K101|NONE|1/2|-64<= k <= 63|
|BRTS|K|Branch if T flag set|if (T = 1) then PC <- PC + K + 1|1111 00KK KKKK K110|NONE|1/2|-64<= k <= 63|
|BRTC|K|Branch if T flag cleared|if (T = 0) then PC <- PC + K + 1|1111 01KK KKKK K110|NONE|1/2|-64<= k <= 63|
|BRVS|K|Branch if overflow flag is set|if (V = 1) then PC <- PC + K + 1|1111 00KK KKKK K011|NONE|1/2|-64<= k <= 63|
|BRVC|K|Branch if overflow flag is cleared|if (V = 0) then PC <- PC + K + 1|1111 01KK KKKK K011|NONE|1/2|-64<= k <= 63|
|BRIE|K|Branch if interrupt enabled|if (I = 1) then PC <- PC + K + 1|1111 00KK KKKK K111|NONE|1/2|-64<= k <= 63|
|BRID|K|Branch if interrupt disabled|if (I = 0) then PC <- PC + K + 1|1111 01KK KKK K111|NONE|1/2|-64<= k <= 63|


### Bit and Bit-Test Instructions 

|Instruction|Operands|Description|Operation|Binary|Flags|Clock Cycles|Operands|
|-----------|--------|-----------|---------|------|-----|------|--------|
|SBI|P, b|Set bit in I/O register|I/O (P,b)<-1|1001 1010  AAAA Abbb|NONE|2|0 <= A<= 31, 0<= b <= 7| 
|CBI|P, b|Clear bit in I/O register|I/O (P,b)<-0|1001 1000 AAAA Abbbb|NONE|2|0 <= A<= 31, 0<= b <= 7|
|LSL|Rd|Logical shift left|Rd(n+1)<-Rd(n),Rd(0)<-0|0000 11dd dddd dddd|Z,C,N,V|1|0 <= d <= 31|
|LSR|Rd|Logical shift right|Rd(n)<-Rd(n+1),Rd(7)<-0|1001 010d dddd 0110|Z,C,N,V|1|0 <= d <= 31|
|ROL|Rd|Rotate left through carry|Rd(0)<-C,Rd(n+1)<-Rd(n),C<-Rd(7)|0001 11dd dddd dddd|Z,C,N,V|1|0 <= d <= 31|
|ROR|Rd|Rotate right through carry|Rd(7)<-C,Rd(n)<-Rd(n+1),C<-Rd(0)|1001 010d dddd 0111|Z,C,N,V|1|0 <= d <= 31|
|ASR|Rd|Arithmetic shift right|Rd<-Rd(n+1),n=0..6|1001 010d dddd 0101|Z,C,N,V|1|0 <= d <= 31|
|SWAP|Rd|Swap nibbles|Rd(3..0)<-Rd(7..4),Rd(7..4)<-Rd(3..0)|1001 010d dddd 0010|NONE|1|0 <= d <= 31|
|BSET|S|Flag set|SREG(S)<-1|1001 0100 0sss 1000|SREG (s)|1|0 <= s <= 7|
|BCLR|S|Flag clear|SREG(S)<-0|1001 0100 1sss 1000|SREG (s)|1|0 <= s <= 7|
|BST|Rr,b|Bit store from register to T|T<- Rr(b)|1111 101d dddd 0bbb|T|1|0 <= d <= 31,0 <= s <= 7|
|BLD|Rd,b|Bit load from T to register|Rd(b)<- T |1111 101d dddd 0bbb|NONE|1|0 <= d <= 31,0 <= s <= 7|
|SEC||Set carry|C<-1|1001 0100 0000 1000|C|1|NONE|
|CLC||Clear carry|C<-0|1001 0100 1000 1000|C|1|NONE|
|SEN||Set negative flag|N<-1|1001 0100 0010 1000|N|1|NONE|
|CLN||Clear negative flag|N<-0|1001 0100 1010 1000|N|1|NONE|
|SEZ||Set zero flag|Z<-1|1001 0100 0001 1000|Z|1|NONE|
|CLZ||Clear zero flag|Z<-0|1001 0100 1001 1000|Z|1|NONE|
|SEI||Global interrupt enable|I<-1|1001 0100 0111 1000|I|1|NONE|
|CLI||Global interrupt disable|I<-0|1001 0100 1111 1000|I|1|NONE|
|SES||Set signed test flag|S<-1|1001 0100 0100 1000|S|1|NONE|
|CLS||Clear signed test flag|S<-0|1001 0100 1100 1000|S|1|NONE|
|SEV||Set twos complement overflow|V<-1|1001 0100 0011 1000|V|1|NONE|
|CLV||Clear twos complement overflow|V<-0|1001 0100 1011 1000|V|1|NONE|
|SET||Set T in SREG|T<-1|1001 0100 0110 1000|T|1|NONE|
|CLT||Clear T in SREG|T<-0|1001 0100 1110 1000|T|1|NONE|
|SEH||Set half carry flag in SREG|H<-1|1001 0100 0101 1000|H|1|NONE|
|CLH||Clear half carry flag in SREG|H<-0|1001 0100 1101 1000|H|1|NONE|

### Data Transfer Instructions

|Instruction|Operands|Description|Operation|Binary|Flags|Clock Cycles|Operands|
|-----------|--------|-----------|---------|------|-----|------|--------|
|MOV|Rd, Rr|Move between registers|Rd<-Rr|0010 11rd dddd rrrr|NONE|1|0 <= d <= 31 , 0 <= r <= 31|
|MOVW|Rd, Rr|Copy register word|Rd+1:Rd<-Rr+1:Rr|0000 0001 dddd rrrr|NONE|1|0 <= d <= 31 , 0 <= r <= 31|
|LDI|Rd, K|Load immediate|Rd <- K|1110 KKKK dddd KKKK|NONE|1|16 <= d <= 31, 0 <= K <= 255|
|LD|Rd, X|Load indirect|Rd <- (X)|1001 000d dddd 1100|NONE|2|0 <= d <= 31|
|LD|Rd, X+|Load indirect and post-inc|Rd <- (X),X<-X+1|1001 000d dddd 1101|NONE|2|0 <= d <= 31|
|LD|Rd, – X|Load indirect and pre-dec|X<-X-1,Rd <- (X)|1001 000d dddd 1110|NONE|2|0 <= d <= 31|
|LD|Rd, Y|Load indirect|Rd <- (Y)|1000 000d dddd 1000|NONE|2|0 <= d <= 31|
|LD|Rd, Y+|Load indirect and post-inc|Rd <- (Y),Y<-Y+1|1001 000d dddd 1001|NONE|2|0 <= d <= 31|
|LD|Rd, – Y|Load indirect and pre-dec|Y<-Y-1,Rd <- (Y)|1001 000d dddd 1010|NONE|2|0 <= d <= 31|
|LDD|Rd, Y+ q|Load indirect with displacement|Rd <- (Y +q)|10q0 qq0d dddd 1qqq|NONE|2|0 <= d <= 31|
|LD|Rd, Z|Load indirect|Rd <- (Z)|1000 000d dddd 0000|NONE|2|0 <= d <= 31|
|LD|Rd, Z+|Load indirect and post-inc|Rd <- (Z),Z<-Z+1|1001 000d dddd 0001|NONE|2|0 <= d <= 31|
|LD|Rd, –Z|Load indirect and pre-dec|Z<-Z-1,Rd <- (Z)|1001 000d dddd 0010|NONE|2|0 <= d <= 31|
|LDD|Rd, Z+ q|Load indirect with displacement|Rd <- (Z +q)|10q0 qq0d dddd 0qqq|NONE|2|0 <= d <= 31|
|LDS|Rd, k|Load direct from SRAM|Rd <- DS(k)|1001 000d dddd 0000 kkkk kkkk kkkk kkkk|NONE|2|0 <= d <= 31,0 <= k <= 65535|
|ST|X, Rr|Store indirect|(X)<- Rd|1001 001r rrrr 1100|NONE|2|0 <= r <= 31|
|ST|X+, Rr|Store indirect and post-inc|(X)<- Rr, X<-X+1|1001 001r rrrr 1101|NONE|2|0 <= r <= 31|
|ST|– X, Rr|Store indirect and pre-dec|X <- X-1,(X)<- Rr|1001 001r rrrr 1110|NONE|2|0 <= r <= 31|
|ST|Y, Rr|Store indirect|(Y)<- Rd|1000 001r rrrr 1000|NONE|2|0 <= r <= 31|
|ST|Y+, Rr|Store indirect and post-inc|(Y)<- Rr, Y<-Y+1|1001 001r rrrr 1001|NONE|2|0 <= r <= 31|
|ST|– Y, Rr|Store indirect and pre-dec|Y <- Y-1,(Y)<- Rr|1001 001r rrrr 1010|NONE|2|0 <= r <= 31|
|STD|Y+ q, Rr|Store indirect with displacement|(Y+q)<- Rr|10q0 qq1r rrrr 1qqq|NONE|2|0 <= r <= 31|
|ST|Z, Rr|Store indirect|(Y)<-Rr|(Z)<-Rr|1000 001r rrrr 0000|NONE|2|0 <= r <= 31|
|ST|Z +, Rr|Store indirect and post-inc|(Z)<-Rr,Z<-Z+1|1001 001r rrrr 0001|NONE|2|0 <= r <= 31|
|ST|–Z, Rr|Store indirect and pre-dec| Z<-Z-1,(Z)<-Rr|1001 001r rrrr 0010|NONE|2|0 <= r <= 31|
|STD|Z + q, Rr|Store indirect with displacement| (Z+q) <- Rr|10q0 qq1r rrrr 0qqq|NONE|2|0 <= r <= 31|
|STS|k, Rr|Store direct to SRAM|(K) <- Rr|1001 001d dddd 0000 kkkk kkkk kkkk kkkk|NONE|2|0 <= d <= 31,0 <= k <= 65535|
|LPM||Load program memory| R0 <- (Z)|1001 0101 1100 1000|NONE|3|R0 implied|
|LPM|Rd, Z|Load program memory| Rd <- (Z)|1001 000d dddd 0100|NONE|3|0 <= d <= 31|
|LPM|Rd, Z+|Load program memory and post-inc|Rd <- (Z), Z<-Z+1|1001 000d dddd 0101|NONE|3|0 <= d <= 31|
|SPM||Store program memory| (Z) <- R1:R0|1001 0101 1110 1000|NONE|1||
|IN|Rd, A|In port|Rd <- P|1011 OAAd dddd AAAA|NONE|1|0 <= d <= 31, 0 <= A <= 63| 
|OUT|A, Rr|Out port|P <- Rr|1011 1AAr rrrr AAAA|NONE|1|0 <= d <= 31,0 <= A <= 63|
|PUSH|Rr|Push register on stack| STACK <- Rr|1001 001d dddd 1111|NONE|2|0 <= d <= 31|
|POP|Rd|Pop register from stack| Rd <- STACK|1001 000d dddd 1111|NONE|2|0 <= d <= 31|

### MCU Control Instructions

|Instruction|Operands|Description|Operation|Binary|Flags|Clock Cycles|Operands|
|-----------|--------|-----------|---------|------|-----|------|--------|
|NOP||No operation||0000 0000 0000 0000|NONE|1|NONE|
|SLEEP||Sleep||1001 0101 1000 1000|NONE|1|NONE|
|WDR||Watchdog reset||1001 0101 1010 1000|NONE|1|NONE|
|BREAK||Break||1001 0101 1001 1000|NONE|N/A|NONE|