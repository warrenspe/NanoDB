# Standard imports
import bisect

# Project imports
import NanoTypes.Int
import NanoConfig
from NanoBlocks._MemoryMappedBlock import MemoryMappedBlock
from NanoBlocks._CacheableBlock import CacheableBlock

# Globals

FLAG_TYPE = NanoTypes.Uint(1)
LIST_LEN_TYPE = NanoTypes.Uint(2)
ADDRESS_TYPE = NanoTypes.Uint(8)

# Exceptions
class KeyNotFound(Exception):
    pass


class _IndexBlock(MemoryMappedBlock, CacheableBlock):
    """
    Class which represents a block of an index in a file.

    Structure of the block is:
    isLeaf (1 byte):        A flag indicating whether the block is a leaf (addresses point to the db table)
                            or an internal node (addresses point to further index blocks).
    NumKeys (2 bytes):      An unsigned integer representation of the number of keys in the block
    NumAddresses (2 bytes): An unsigned integer representation of the number of addresses in the block
    Keys (X bytes):         Values which lookup values can be compared to, to determine where a given value
                            would be located in the database table.
    Addresses (X bytes):    Addresses which are pointed to by keys.
    """

    address = None      # File index which this block begins at
    parent = 0          # Index of parent block
    isLeaf = None       # Subclassed flag; indicates whether this block is a leaf or interior block
    dataType = None     # Type of data which can be looked by the index (DATA_BLOCK / INDEX_BLOCK)
    keys = None         # List of keys which allow mappings to addresses
    addresses = None    # List of addresses mapped to by our keys
    maxKeys = None      # Maximum number of keys this block can hold

    # MemoryMappedBlock definitions
    fields = [
        'isLeaf',
        'parent',
        'keys',
        'addresses',
    ]
    dataTypes = None # Set in __init__
    iterableFields = {'keys', 'addresses'}
    iterableFieldNumItemsDataType = {
        'keys': LIST_LEN_TYPE,
        'addresses': LIST_LEN_TYPE,
    }
    iterableFieldSizes = None # Set in __init__

    def __init__(self, address, dataType):
        self.address = address
        self.dataType = dataType
        self.keys = []
        self.addresses = []

        # MemoryMappedBlock calculations
        self.blockSize = NanoConfig.index_block_size
        self.maxKeys = int((self.blockSize - (FLAG_TYPE.size + ADDRESS_TYPE.size + (2 * LIST_LEN_TYPE.size)))
                           / (self.dataType.size + ADDRESS_TYPE.size))
        self.dataTypes = {
            'isLeaf': FLAG_TYPE,
            'parent': ADDRESS_TYPE,
            'keys': dataType,
            'addresses': ADDRESS_TYPE,
        }
        self.iterableFieldSizes = {
            'keys': self.maxKeys * self.dataType.size,
            'addresses': self.maxKeys * ADDRESS_TYPE.size,
        }


    def full(self):
        return len(self.keys) >= self.maxKeys


    def add(self, key, address):
        """
        Adds a key & address to this Block.

        Inputs: key     - The key which will be used for lookups.
                address - The address which will be returned upon successful lookup.
        """

        if self.full():
            raise BufferError("IndexBlock is full")

        # Calculate the index to insert the entry into
        idx = bisect.bisect_left(self.keys, key)
        self.keys.insert(idx, key)
        self.addresses.insert(idx, address)


    def delete(self, key=None):
        """
        Deletes a key & associated address from this Block, given a key.

        Inputs: key - The key to delete.

        Raises an KeyNotFound exception if key is not found in the block.
        """

        if not self.keys:
            raise KeyNotFound("IndexBlock is empty, cannot delete %s" % key)

        idx = bisect.bisect(self.keys, key)

        if idx == 0 or self.keys[idx - 1] != key:
            raise KeyNotFound(str(key))

        self.keys.pop(idx - 1)
        self.addresses.pop(idx - 1)


    def deleteAddress(self, address):
        """
        Deletes a key & associated address from this Block, given an address.

        Inputs: address - The address to delete.

        Raises an KeyNotFound exception if address is not found in the block.
        """

        if not self.keys:
            raise KeyNotFound("IndexBlock is empty, cannot delete %s" % key)



        if address not in self.addresses:
            raise KeyNotFound("IndexBlock Address: %s" % address)

        idx = self.addresses.index(address)

        self.keys.pop(idx)
        self.addresses.pop(idx)


    def lookup(self, val):
        raise NotImplementedError


class LeafBlock(_IndexBlock):
    """
    IndexBlock which contains a mapping of key to address, where the address points to a tuple in the database table.
    """

    isLeaf = 1

    def lookup(self, key):
        """
        Looks up and returns an address associated with the given key value.

        Returns: The found address if we found a perfect match for the given value; else raises a KeyNotFound error.
        """

        # Since we're a LeafBlock, the value given must be a perfect match to the value we looked up
        idx = bisect.bisect(self.keys, key)

        # Since we're bisecting right, if idx is 0 the value we searched for was less than everything in self.keys
        # Additionally, since we're a leaf block the key we matched must equal the key we were passed
        if idx == 0 or key != self.keys[idx - 1]:
            raise KeyNotFound(str(key))

        return self.addresses[idx - 1]


class InteriorBlock(_IndexBlock):
    """
    IndexBlock which contains a mapping of key to address, where the address points to another IndexBlock.

    Main difference of InteriorBlocks from LeafBlocks being that InteriorBlocks 
    """

    isLeaf = 0

    def lookup(self, key):
        """
        Looks up and returns an address associated with the given key value.

        Returns: The address, if we can find one in the block - else raises a KeyNotFound error.
        """

        # Get the index of the address to return
        idx = bisect.bisect(self.keys, key)

        # If the idx is 0 the key we're searching for is less than our smallest key.  Since our keys point to blocks
        # whose values are all greater than or equal to it we do not contain that key. Raise a KeyNotFound
        if idx == 0:
            raise KeyNotFound(str(key))

        # Return the address on the correct side of the matched key
        return self.addresses[idx - 1]
