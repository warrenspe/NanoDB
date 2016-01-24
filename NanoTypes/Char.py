# Project imports
import _BaseType as BaseType

class Char(BaseType.Type):
    maxLength = 256

    def _init(self):
        self.size = self.quantifier
        if self.quantifier < 0 or self.quantifier > self.maxLength:
            raise Exception("%d out of range for char: 0-%d" % (self.quantifier, self.maxLength))
        self.nullVal = '\x00' * self.quantifier


    def _toString(self, val):
        return val.rjust(self.quantifier, '\x00')


    def _fromString(self, s):
        # Return the string without leading null bytes; or if the string
        # is entirely null bytes, None
        return s.lstrip('\x00') or None


    def isValid(self, val):
        return isinstance(val, basestring) and (len(val) <= self.maxLength or self.isNull(val))
