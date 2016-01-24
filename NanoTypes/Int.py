# Standard imports
import numbers

# Project imports
import _BaseType as BaseType

class Int(BaseType.Type):
    structMapping = {
        1: 'b',
        2: 'h',
        4: 'i',
        8: 'q',
    }
    maxVal = None
    minVal = None

    def _init(self):
        self.maxVal = 2**((self.size * 8) - 1) - 1
        self.minVal = -self.maxVal
        self.nullVal = self.minVal - 1


    def _toString(self, val):
        return self.structObj.pack(int(val))


    def _fromString(self, val):
        return self.structObj.unpack(val)[0]


    def isValid(self, val):
        if isinstance(val, (basestring, numbers.Number)):
            try:
                val = long(val)
            except (ValueError, AttributeError):
                return False
            
        return (val >= self.minVal and val <= self.maxVal) or self._isNull(val)
