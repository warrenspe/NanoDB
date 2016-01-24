# Standard imports
import struct

class UnknownTypeError(Exception):
    pass


class Type:
    """ Fixed memory base for a type which can be used to serialize variables for insertion into files. """

    indexable = True     # Flag indicating whether or not this type can be indexed on
    quantifier = None    # Quantifier modifying storage size of type
    nullVal = None       # Type-specific variable containing the NULL value of this type
    size = None          # Number of bytes this type requires to be serialized into a string
    structMapping = None # Optional parameter: If defined allows the use of the struct
                         # module to implement the to/fromString functions
                         # Should map quantifier values to struct codes
    structObj = None     # An object which is created if a structMapping is defined

    # Data Model attributes
    def __init__(self, quantifier):
        if quantifier:
            self.quantifier = int(quantifier)

        if self.structMapping:
            if self.quantifier not in self.structMapping:
                raise UnknownTypeError(str(self))
            self.structObj = struct.Struct(self.structMapping[self.quantifier])
            self.size = self.structObj.size

        self._init()


    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, (self.quantifier or ""))


    # Private attributes
    def _isNull(self, val):
        return val == self.nullVal or val is None


    # Overridable attributes
    def _init(self):
        pass


    def _toString(self, val):
        raise NotImplementedError


    def _fromString(self, val):
        raise NotImplementedError


    # API attributes
    def toString(self, val):
        # If we're packing None, use our null value
        if val is None:
            val = self.nullVal

        # If the value we were given is invalid, raise an exception
        if not self.isValid(val):
            raise ValueError("%s invalid value for %s" % (val, self))

        return self._toString(val)


    def fromString(self, val):
        # Ensure we have a string to work with
        if not isinstance(val, basestring):
            raise Exception("Cannot fromString: %s (%s)" % (val, type(val)))

        if len(val) != self.size:
            raise Exception("%s not of length %d for %s" % (val, self.size, self))

        toReturn = self._fromString(val)

        if toReturn == self.nullVal:
            return None

        return toReturn


    def isValid(self, val):
        raise NotImplementedError
