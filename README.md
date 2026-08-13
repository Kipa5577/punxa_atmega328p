# punxa_atmega328p

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![HDL Engine](https://img.shields.io/badge/HDL-py4hw-blue)](https://github.com/py4hw/py4hw)

**Punxa-ATmega328P** is a Python-based full-system simulator for the ATmega328P microcontroller. Built

## Assembly

We implemented a custom assembler to support the development and testing of programs for the simulator. It supports:

- Instructions and pseudo-instructions
- Labels
- Simple macros (high, low)

## Testing & Validation

The project includes an ISA test suite to verify the correctness of the processor models.

### Singlecycle Processor Model
<pre>
Total: 111 Correct: 110 (99.1 %)
99.1 %   |█████████████████████████████████████████████|
</pre>

### Multicycle Processor Model
<pre>
Total: 111 | Correct: 111 (100.0 %)
100.0 %  |█████████████████████████████████████████████|
</pre>

#### Peripherals

##### GPIO:
<pre>
Total: 15 Correct: 15 (100.0 %)
100.0 %  |█████████████████████████████████████████████|
</pre>
##### ADC:
<pre>
Total: 11 Correct: 11 (100.0 %)
100.0 %  |█████████████████████████████████████████████|
</pre>
##### SPI:
<pre>
Total: 8 Correct: 8 (100.0 %)
100.0 %  |█████████████████████████████████████████████|
</pre>
##### Timers:
<pre>
Group: test_timer0 Total: 37 Correct: 37 (100.0 %)
test_timer0     100.0 %  |█████████████████████████████████████████████|
Group: test_timer1 Total: 54 Correct: 54 (100.0 %)
test_timer1     100.0 %  |█████████████████████████████████████████████|
Group: test_timer2 Total: 30 Correct: 30 (100.0 %)
test_timer2     100.0 %  |█████████████████████████████████████████████|
</pre>

##### TWI:
<pre>
Total: 2 Correct: 2 (100.0 %)
100.0 %  |█████████████████████████████████████████████|
</pre>

##### USART:
<pre>
Total: 17 Correct: 15 (88.2 %)
88.2 %   |████████████████████████████████████████░░░░░|
</pre>


### Verilog isa tests
These tests are conducted on the verilog code instantiated on a FPGA and they run all the ISA tests this time each isa test is programmed in to the memory of the cpu via the ISP interface.
There is also a bonus test to test if a bootloader works.

<pre>
Total:112  Correct:  (88.2 %)
88.2 %   |████████████████████████████████████████░░░░░|
</pre>
s







## 🔗 Repository



## ⚙️ Getting Started / Installation

