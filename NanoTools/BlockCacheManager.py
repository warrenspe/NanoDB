# Standard imports
import collections

# Project imports
import NanoConfig
from NanoBlocks._CacheableBlock import CacheableBlock


class BlockCacheManager:
    """
    Class which provides caching functionality; operates entirely in memory.

    If using this manager, before any reads from the file one should first
    check the manager to see if a dirty version of the block exists.  Ie: the file
    may not have the most updated form of the block.

    Requires the block objects it handles to extend the CacheableBlock class.
    """

    dirtyDict = None # Maps addressess to blocks
    fd = None        # File descriptor used to flush blocks to the file

    def __init__(self, fd):
        self.fd = fd
        self.dirtyDict = collections.OrderedDict()

    def __contains__(self, val):
        """
        Data model function for handling `in`.  Keyed on addresses.

        Inputs: val - The address to test if is dirty.
        """

        return val in self.dirtyDict


    def __len__(self):
        """
        Data model function for handling len(). Returns the number of dirty blocks.
        """

        return len(self.dirtyDict)


    def keys(self):
        return self.dirtyDict.keys()
    def values(self):
        return self.dirtyDict.values()
    def items(self):
        return self.dirtyDict.items()


    def addBlock(self, block):
        """
        Writes a block to the manager indicating it is dirty.
        The given block must subclass the CacheableBlock class else a TypeError is raised.

        Inputs: block - The block to add to the manager.
        """

        if not isinstance(block, CacheableBlock):
            raise TypeError("%s does not subclass CacheableBlock" % block)

        if block.address in self:
            del self.dirtyDict[block.address]

        elif len(self) > NanoConfig.max_num_dirty_blocks:
            self.flushBlock()

        self.dirtyDict[block.address] = block


    def getBlock(self, address):
        if address not in self:
            raise Exception("Given address %d not in dirty block manager" % address)
        self.dirtyDict[address] = self.dirtyDict.pop(address)
        return self.dirtyDict[address]


    def flushBlock(self, address=None): # TODO be smart about combining blocks
        if address is None:
            address = self.dirtyDict.keys()[0]
        elif address not in self:
            raise Exception("Given address: %d not in dirty block manager" % address)

        self.dirtyDict.pop(address)._write(self.fd)


    def flushAll(self):
        for blockAddress in self.dirtyDict:
            self.flushBlock(blockAddress)


    def truncate(self):
        self.dirtyDict = collections.OrderedDict()
