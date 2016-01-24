# Project imports
import Int

class Uint(Int.Int):
    structMapping = {
        1: 'B',
        2: 'H',
        4: 'I',
        8: 'Q',
    }
    maxVal = None
    minVal = 0

    def _init(self):
        self.maxVal = 2**(self.size * 8) - 2
        self.nullVal = self.maxVal + 1
