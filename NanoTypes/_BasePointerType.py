# Standard imports
import os

# Project imports
import Uint

ADDRESS_TYPE = Uint.Uint(8)
# TODO modify this class so that if we continually update a row, changing nothing, it doesn't repeatedly serialize to the db
# TODO or just add dirty bits to classes that use it, though not as pretty
class PointerType:
    """
    Type which handles serializing data into a file store; expecting pointers to these values to be serialized in the
    database that the type belongs to.
    """

    indexable = False # Flag indicating whether or not this type can be indexed on
    fd = None         # A pointer to the filestore for this type

    # Data Model attributes
    def __init__(self, fd):
        self.fd = fd
        self._init()


    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.fd.name)


    # Private attributes
    def _toFile(self, serialized):
        """
        Writes the serialized string given to self.fd.  Returns the address we wrote to.
        """

        self.fd.seek(0, os.SEEK_END)
        address = self.fd.tell()
        self.fd.write(serialized)

        return address


    def _fromFile(self, address, length):
        """
        Returns the string stored at `address` of length `length` from self.fd
        """

        self.fd.seek(address)
        return self.fd.read(length)


    # Overridable attributes
    def _init(self):
        pass


    def _toString(self, val):
        """
        Function which should accept a value and return the serialized version of it.
        """

        raise NotImplementedError


    def _fromString(self, val):
        """
        Function which should accept the value to unserialize and return the unserialized version.
        """

        raise NotImplementedError


    # Public attributes
    def toString(self, val):
        """
        Accepts a value which should be serialized to the fileStore.
        """

        serialized = self._toString(val)

        address = self._toFile(serialized)

        # Return a pointer to the data we just wrote
        return ADDRESS_TYPE.toString(address) + ADDRESS_TYPE.toString(len(serialized))


    def fromString(self, val):
        address = ADDRESS_TYPE.fromString(val[:ADDRESS_TYPE.size])
        length = ADDRESS_TYPE.fromString(val[ADDRESS_TYPE.size:])

        return self._fromString(self._fromFile(address, length))
