# Project imports
import Int

class Float(Int.Int):
    structMapping = {
        4: 'f',
        8: 'd',
    }
    nullVal = float('inf')

    def _toString(self, val):
        return self.structObj.pack(float(val))


    def isValid(self, val):
        try:
            float(val)
            return True
        except (ValueError, AttributeError):
            return False
