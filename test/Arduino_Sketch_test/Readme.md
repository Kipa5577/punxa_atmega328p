

## Pin Connetions

|Arduino Pin| AVR Pin | FPGA(DE GPIO 0 )|ESP32 Pin| ESP32 Pin Static Hardware Function & Boot Rules        |
|-----------|---------|-----------------|---------|--------------------------------------------------------|
|D0 (RX)    |PD0      |GPIO0_D0         |GPIO17   |UART2 TX[cite: 1]                                       |
|D1 (TX)    |PD1      |GPIO0_D1         |GPIO16   |UART2 RX[cite: 1]                                       |
|D2         |PD2      |GPIO0_D2         |GPIO18   |Bidirectional[cite: 1]                                  |
|D3(PWM)    |PD3      |GPIO0_D3         |GPIO19   |Bidirectional[cite: 1]                                  |
|D4         |PD4      |GPIO0_D4         |GPIO21   |Bidirectional[cite: 1]                                  |
|D5(PWM)    |PD5      |GPIO0_D6         |GPIO22   |Bidirectional[cite: 1]                                  |
|D6(PWM)    |PD6      |GPIO0_D8         |GPIO23   |Bidirectional[cite: 1]                                  |
|D7         |PD7      |GPIO0_D9         |GPIO25   |Bidirectional[cite: 1]                                  |
|D8         |PB0      |GPIO0_D10        |GPIO26   |Bidirectional[cite: 1]                                  |
|D9(PWM)    |PB1      |GPIO0_D11        |GPIO27   |Bidirectional[cite: 1]                                  |
|D10(SS)    |PB2      |GPIO0_D12        |GPIO32   |Bidirectional[cite: 1]                                  |
|D11(MOSI)  |PB3      |GPIO0_D13        |GPIO33   |Bidirectional/ISP MOSI[cite: 1]                         |
|D12(MISO)  |PB4      |GPIO0_D14        |GPIO4    |Bidirectional/ISP MISO[cite: 1]                         |
|D13(SCK)   |PB5      |GPIO0_D15        |GPIO5    |Bidirectional/ISP SCK (Must be HIGH at boot)[cite: 1]   |
|A0         |PC0      |GPIO0_D16        |GPIO12   |AVR_RESET (Must be LOW at boot)[cite: 1]                |
|A1         |PC1      |GPIO0_D17        |GPIO2    |Bidirectional (Must be LOW to flash ESP32)              |
|A2         |PC2      |GPIO0_D18        |GPIO14   |Bidirectional[cite: 1]                                  |
|A3         |PC3      |GPIO0_D19        |GPIO15   |Bidirectional (Must be HIGH at boot)[cite: 1]           |
|A4(SDA)    |PC4      |GPIO0_D20        |GPIO13   |I2C SDA                                                 |
|A5(SCL)    |PC5      |GPIO0_D21        |GPIO0    |I2C SCL (Must be HIGH at boot)                          |



Before every test the soft processor is flashed without a bootloader 

## The test sequance 
- Digital Output Verification 
- Digital Input & Serial
- Hardware PWM Verification 
- Timer & Frequency
- Software Bit-Banging
- Hardware SPI Verification
- Hardware I2C Verification
- Hardware Serial Verification
- Bootloader Verification Test 
