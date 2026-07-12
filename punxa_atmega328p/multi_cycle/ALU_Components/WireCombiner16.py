import py4hw


class WireCombiner16(py4hw.Logic):
    """Combines a High 8-bit wire and a Low 8-bit wire into a 16-bit wire."""
    def __init__(self, parent, name, in_high, in_low, out_16):
        super().__init__(parent, name)
        self.in_high = self.addIn('in_high', in_high)
        self.in_low = self.addIn('in_low', in_low)
        self.out_16 = self.addOut('out_16', out_16)

    def propagate(self):
        val_high = self.in_high.get() & 0xFF
        val_low = self.in_low.get() & 0xFF
        # Shift the high byte left by 8 bits, and OR it with the low byte
        combined = (val_high << 8) | val_low
        self.out_16.put(combined)