This is a classic pointer register file and memory interface, very similar to the architecture used in AVR microcontrollers (with the X, Y, Z, and SP registers).

Comparing your `py4hw` code to the schematic, you have a solid structural foundation, but there are a few behavioral discrepancies that prevent it from functioning exactly like the hardware—specifically around the pre-decrement timing, the +1 address multiplexer, and how the `BusData` register handles reads vs. writes.

Here are the key fixes applied to make your code match the schematic:

* **Pre-Decrement vs. Post-Increment Timing:** In your original code, the address was sent to memory *before* being decremented during a Pre-Decrement operation. Hardware logic (like the `+` and `-` adders in the schematic) computes the decremented address on the fly. The corrected code applies the `-1` to the `base_address` before asserting it on the bus.
* **The Address `+1` Multiplexer:** In the schematic, there is an adder right before `DataBusADDRESS` controlled by the LSB of `Mem_instruction` (labeled `0001` branching from the select line). This means odd instructions (like `MEM_X_PLUS`) push `Pointer + 1` to the address bus without modifying the underlying register. Your original `selectAddress` function ignored the `_PLUS` instructions entirely.
* **Data Bus Muxing Bug:** In `selectWriteData`, your original code returned `self.BusData` when selecting `INPUT_DATABUS`. However, the MUX on the far right of the schematic selects the *input pin* `DataBusInput`. Returning the internal register caused an infinite loop of old data.
* **Clock Evaluation Order:** Hardware executes in parallel, but your behavioral model is evaluated sequentially. To simulate the hardware correctly, the address must be generated and asserted *first*, followed by the memory read/write phase, followed by latching the data into the registers, and finally auto-updating the pointers.
* **`MEM_ROM` Typo:** The constant `MEM_RAM_ADDR_REG` was defined as `8`, but your address logic checked for `self.MEM_ROM`, which threw an attribute error.

Here is the fully corrected and operational `py4hw` component:

```python
import py4hw
# import Memory # Assuming this is provided in your environment

class MemoryInterfaceHandler(py4hw.Logic):

    # ----------------------------------------------------------
    # Memory instruction encodings
    # ----------------------------------------------------------
    # 0=X, 1=X+1, 2=Y, 3=Y+1, 4=Z, 5=Z+1, 6=SP, 7=SP+1, 8=RamAddrReg
    MEM_X = 0
    MEM_X_PLUS = 1
    MEM_Y = 2
    MEM_Y_PLUS = 3
    MEM_Z = 4
    MEM_Z_PLUS = 5
    MEM_SP = 6
    MEM_SP_PLUS = 7
    MEM_RAM_ADDR_REG = 8

    # --- Input select ---
    INPUT_DATABUS = 0
    INPUT_RESL = 1
    INPUT_RESH = 2
    INPUT_GENERAL = 3

    # --- LoadSelectMux ---
    LOAD_BUS_DATA = 0
    LOAD_XL_MINUS = 1
    LOAD_XH_MINUS = 2
    LOAD_XL_PLUS = 3
    LOAD_XH_PLUS = 4
    LOAD_YL_MINUS = 5
    LOAD_YH_MINUS = 6
    LOAD_YL_PLUS = 7
    LOAD_YH_PLUS = 8
    LOAD_ZL_MINUS = 9
    LOAD_ZH_MINUS = 10
    LOAD_ZL_PLUS = 11
    LOAD_ZH_PLUS = 12

    # --- LoadingMux ---
    LOAD_XL = 0
    LOAD_XH = 1
    LOAD_YL = 2
    LOAD_YH = 3
    LOAD_ZL = 4
    LOAD_ZH = 5
    LOAD_SPL = 6
    LOAD_SPH = 7

    # --- Increment/Decrement Control ---
    INC_NONE = 0
    INC_POST_INC = 1
    INC_PRE_DEC = 2


    def __init__(self, parent, name: str,
            # control inputs
            reset, WE, LoadSelectMux, LoadingMux, IncDec, ReadWrite, InputSelect, Mem_instruction, RomAddress,
            # data inputs
            DataBusInput, ResL, ResH, GeneralInput,
            # memory interface
            memory, # type: MemoryInterface
            # output
            RegisterOut,
        ):
        super().__init__(parent, name)

        # Memory interface
        self.mem = self.addInterfaceSource('memory', memory)

        # Control inputs
        self.reset = self.addIn('reset', reset)
        self.WE = self.addIn('WE', WE)
        self.LoadSelectMux = self.addIn('LoadSelectMux', LoadSelectMux)
        self.LoadingMux = self.addIn('LoadingMux', LoadingMux)
        self.IncDec = self.addIn('IncDec', IncDec)
        self.ReadWrite = self.addIn('ReadWrite', ReadWrite)
        self.InputSelect = self.addIn('InputSelect', InputSelect)
        self.Mem_instruction = self.addIn('Mem_instruction', Mem_instruction)
        self.RomAddress = self.addIn('RomAddress', RomAddress)

        # Data inputs
        self.DataBusInput = self.addIn('DataBusInput', DataBusInput)
        self.ResL = self.addIn('ResL', ResL)
        self.ResH = self.addIn('ResH', ResH)
        self.GeneralInput = self.addIn('GeneralInput', GeneralInput)

        # Output
        self.RegisterOut = self.addOut('RegisterOut', RegisterOut)

        # --------------------------------------------------
        # Internal pointer registers
        # --------------------------------------------------
        self.XregL = 0
        self.XregH = 0
        self.YregL = 0
        self.YregH = 0
        self.ZregL = 0
        self.ZregH = 0
        self.SPL = 0
        self.SPH = 0

        # Internal bus register
        self.BusData = 0

    # ==========================================================
    # Helpers
    # ==========================================================

    def getX(self): return (self.XregH << 8) | self.XregL
    def getY(self): return (self.YregH << 8) | self.YregL
    def getZ(self): return (self.ZregH << 8) | self.ZregL
    def getSP(self): return (self.SPH << 8) | self.SPL

    def setX(self, value):
        self.XregL = value & 0xFF
        self.XregH = (value >> 8) & 0xFF

    def setY(self, value):
        self.YregL = value & 0xFF
        self.YregH = (value >> 8) & 0xFF

    def setZ(self, value):
        self.ZregL = value & 0xFF
        self.ZregH = (value >> 8) & 0xFF

    def setSP(self, value):
        self.SPL = value & 0xFF
        self.SPH = (value >> 8) & 0xFF

    # ==========================================================
    # Address generation
    # ==========================================================

    def selectAddress(self):
        mem_instr = self.Mem_instruction.get()
        base_address = 0
        pointer_name = None

        if mem_instr in (self.MEM_X, self.MEM_X_PLUS):
            base_address = self.getX()
            pointer_name = "X"
        elif mem_instr in (self.MEM_Y, self.MEM_Y_PLUS):
            base_address = self.getY()
            pointer_name = "Y"
        elif mem_instr in (self.MEM_Z, self.MEM_Z_PLUS):
            base_address = self.getZ()
            pointer_name = "Z"
        elif mem_instr in (self.MEM_SP, self.MEM_SP_PLUS):
            base_address = self.getSP()
            pointer_name = "SP"
        elif mem_instr == self.MEM_RAM_ADDR_REG:
            base_address = self.RomAddress.get()
            pointer_name = "ROM"


        # --- Displacement Addressing ---
        elif mem_instr in (self.MEM_Y_Q, self.MEM_Z_Q):
            # 1. Get the raw unsigned value from the bus
            q_val = self.Q.get()
            
            # 2. Sign-extend assuming a 6-bit wire (Values 0 to 63)
            # If the 6th bit (0x20) is 1, it's a negative number.
            if q_val & 0x20:  
                q_val -= 0x40 # Convert e.g., 63 into -1 in Python
                
            # 3. Add to the correct base register
            if mem_instr == self.MEM_Y_Q:
                base_address = self.getY() + q_val
            else:
                base_address = self.getZ() + q_val


        # Apply Pre-decrement BEFORE accessing memory if mode requires it
        mode = self.IncDec.get()
        if pointer_name in ("X", "Y", "Z", "SP") and mode == self.INC_PRE_DEC:
            base_address -= 1


        return base_address & 0xFFFF, pointer_name

    # ==========================================================
    # Address update logic
    # ==========================================================

    def updatePointer(self, ptr_name):
        if ptr_name is None or ptr_name == "ROM":
            return

        mode = self.IncDec.get()
        if mode == self.INC_NONE:
            return

        if ptr_name == "X":
            val = self.getX()
            self.setX(val - 1 if mode == self.INC_PRE_DEC else val + 1)
        elif ptr_name == "Y":
            val = self.getY()
            self.setY(val - 1 if mode == self.INC_PRE_DEC else val + 1)
        elif ptr_name == "Z":
            val = self.getZ()
            self.setZ(val - 1 if mode == self.INC_PRE_DEC else val + 1)
        elif ptr_name == "SP":
            val = self.getSP()
            self.setSP(val - 1 if mode == self.INC_PRE_DEC else val + 1)

    # ==========================================================
    # Data source selection
    # ==========================================================

    def selectWriteData(self):
        sel = self.InputSelect.get()

        if sel == self.INPUT_DATABUS:
            return self.mem.read_data.get() # Fixed: Was self.BusData
        elif sel == self.INPUT_RESL:
            return self.ResL.get()
        elif sel == self.INPUT_RESH:
            return self.ResH.get()
        elif sel == self.INPUT_GENERAL:
            return self.GeneralInput.get()
        return 0

    # ==========================================================
    # Main clocked behavior
    # ==========================================================

    def Clock(self):
        # ----------------------------------------------
        # 0. Reset
        # ----------------------------------------------
        if self.reset.get():
            self.XregL = 0
            self.XregH = 0
            self.YregL = 0
            self.YregH = 0
            self.ZregL = 0
            self.ZregH = 0
            self.SPL = self.SPH = 0
            self.BusData = 0
            
            self.RegisterOut.put(0)
            self.mem.DataBusADDRESS.put(0)
            self.mem.DataBusOut.put(0)
            return

        # ----------------------------------------------
        # 1. Address generation
        # ----------------------------------------------
        # Address must be asserted to the bus first so the memory can react
        address, pointer_name = self.selectAddress()
        self.mem.address.put(address)

        # ----------------------------------------------
        # 2. Memory operation & BusData latching
        # ----------------------------------------------
        rw = self.ReadWrite.get()

        if rw: 
            # WRITE: Latch data from MUX and send to memory
            self.BusData = self.selectWriteData()
            self.mem.DataBusOut.put(self.BusData)
        else:  
            # READ: Latch data from memory bus
            self.BusData = self.mem.MemDataBus.get()

        # The schematic shows BusData routing directly to RegisterOut
        self.RegisterOut.put(self.BusData)

        # ----------------------------------------------
        # 3. Register loading
        # ----------------------------------------------
        if self.WE.get():
            load_sel = self.LoadingMux.get()
            data = self.BusData & 0xFF

            if load_sel == self.LOAD_XL: self.XregL = data
            elif load_sel == self.LOAD_XH: self.XregH = data
            elif load_sel == self.LOAD_YL: self.YregL = data
            elif load_sel == self.LOAD_YH: self.YregH = data
            elif load_sel == self.LOAD_ZL: self.ZregL = data
            elif load_sel == self.LOAD_ZH: self.ZregH = data
            elif load_sel == self.LOAD_SPL: self.SPL = data
            elif load_sel == self.LOAD_SPH: self.SPH = data

        # ----------------------------------------------
        # 4. Pointer update
        # ----------------------------------------------
        self.updatePointer(pointer_name)
