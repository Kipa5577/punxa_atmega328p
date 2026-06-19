import py4hw
import punxa_atmega328p as punxa

from punxa_atmega328p.assembly import assemble_program
from punxa_atmega328p.multi_cycle.RomHandler import RomHandler


# ----------------------------------------------------------
# Hardware
# ----------------------------------------------------------

hw = py4hw.HWSystem()


# ----------------------------------------------------------
# Small Test Program
# ----------------------------------------------------------

program = """
LDI R16, 1
LDI R17, 2
RJMP 0
"""

rom_words, symbols = assemble_program(program)

print("Assembled program:")

for i, word in enumerate(rom_words):
    print(f"{i:04X}: {word:04X}")
# ----------------------------------------------------------
# Instruction Memory
# ----------------------------------------------------------

ins_p = punxa.MemoryInterface(
    hw,
    "ins_mem",
    16,
    14
)

ins_mem = punxa.Ram_Memory(
    hw,
    "instruction_memory",
    16,
    14,
    ins_p
)



for addr, word in enumerate(rom_words):
    ins_mem.writeWord(addr, word)


# ----------------------------------------------------------
# ROM Handler control wires
# ----------------------------------------------------------

instructionOut = py4hw.Wire(hw, "instructionOut", 16)
addressOut     = py4hw.Wire(hw, "addressOut", 14)

Load_Z   = py4hw.Wire(hw, "Load_Z", 1)
addressZL = py4hw.Wire(hw, "addressZL", 8)
addressZH = py4hw.Wire(hw, "addressZH", 8)

Load_K   = py4hw.Wire(hw, "Load_K", 1)
K        = py4hw.Wire(hw, "K", 16)

Load_Jump = py4hw.Wire(hw, "Load_Jump", 1)
relative_Absolute = py4hw.Wire(hw, "relative_Absolute", 1)

Load_Byte = py4hw.Wire(hw, "Load_Byte", 1)
WriteVal  = py4hw.Wire(hw, "WriteVal", 16)


# ----------------------------------------------------------
# Defaults
# ----------------------------------------------------------

Load_Z.put(0)
addressZL.put(0)
addressZH.put(0)

Load_K.put(0)
K.put(0)

Load_Jump.put(0)
relative_Absolute.put(0)

Load_Byte.put(0)
WriteVal.put(0)


rom = RomHandler(
    hw,
    "rom",

    mem=ins_p,

    instructionOut=instructionOut,
    Address_Out=addressOut,

    Load_Z=Load_Z,
    address_ZL=addressZL,
    address_ZH=addressZH,

    Load_K=Load_K,
    K=K,

    Load_Jump=Load_Jump,
    relative_Absolute=relative_Absolute,

    Load_Byte=Load_Byte,
    WriteVal=WriteVal,

    reset_address=0
)


# ----------------------------------------------------------
# Waveforms
# ----------------------------------------------------------

watch = []

watch.extend(py4hw.debug.getInterfaceWires(ins_p))

watch.append(instructionOut)
watch.append(addressOut)

wvf = py4hw.Waveform(
    hw,
    "wvf",
    watch
)


# ----------------------------------------------------------
# Simulation
# ----------------------------------------------------------

sim = hw.getSimulator()

print("\nFetching instructions...\n")

for cycle in range(20):

    sim.clk(1)

    print(
        f"cycle={cycle:02d} "
        f"PC={rom.PC:04X} "
        f"FSM={rom.FSM} "
        f"INS=0x{instructionOut.get():04X}"
    )


# ----------------------------------------------------------
# Direct ROM verification
# ----------------------------------------------------------

print("\nExpected ROM contents")

for addr, expected in enumerate(rom_words):  

    actual = ins_mem.readWord(addr)

    print(
        f"addr={addr:04X} "
        f"expected=0x{expected:04X} "
        f"actual=0x{actual:04X}"
    )

    assert actual == expected, \
        f"ROM mismatch at {addr}"


print("\nROM load verified.")
print("RomHandler fetch test completed.")

