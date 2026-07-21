# Microcontroller and tools
MCU = atmega328p
CC = avr-gcc
OBJCOPY = avr-objcopy

# Compiler flags for assembly
ASFLAGS = -mmcu=$(MCU) -x assembler-with-cpp -Wall

# Directories
SRC_DIR = isa
OUT_DIR = isa_hex

# Find all .asm files in the isa directory
SRCS = $(wildcard $(SRC_DIR)/*.asm)

# Map the .asm files to .hex files in the isa_hex directory
HEXS = $(patsubst $(SRC_DIR)/%.asm, $(OUT_DIR)/%.hex, $(SRCS))

# Default target
all: $(HEXS)

# 2. Extract the .hex file from the .elf file
$(OUT_DIR)/%.hex: $(OUT_DIR)/%.elf
	$(OBJCOPY) -O ihex -R .eeprom $< $@

# 1. Compile the .asm file into an .elf file
$(OUT_DIR)/%.elf: $(SRC_DIR)/%.asm | $(OUT_DIR)
	$(CC) $(ASFLAGS) $< -o $@

# Create the output directory
$(OUT_DIR):
	mkdir -p $(OUT_DIR)

# Clean up compiled files
clean:
	rm -rf $(OUT_DIR)