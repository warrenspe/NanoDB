# Standard imports
import os

# Project imports
import NanoTypes
import NanoConfig
import NanoTools
import NanoIO.File
from NanoBlocks.Index import LeafBlock, InteriorBlock, KeyNotFound

class IndexIO:
    """ Class whose instances are responsible for managing an index of a column in a given table. """

    dbName = None      # Name of the database containing the table whose column this index is for
    tableName = None   # Name of the table the column this index is for belongs to
    indexConfig = None # NanoConfig.Index.Config instance for this Index
    colType = None     # DataType of the column this index is for
    indexFD = None     # A file descriptor open to this index's file

    # Data Model methods
    def __init__(self, dbName, tableName, indexConfig):
        self.dbName = dbName
        self.tableName = tableName
        self.indexConfig = indexConfig
        self.indexFD = NanoIO.File.getIndex(self.dbName, self.tableName, self.indexConfig.column.name)

        self.cacheMgr = NanoTools.BlockCacheManager.BlockCacheManager(self.indexFD)
        self.delMgr = NanoTools.DeletedBlockManager.DeletedBlockManager(
            self.dbName, "_idx_%s_%s" % (self.tableName, self.indexConfig.column.name)
        )
        self.colType = NanoTypes.getType(self.indexConfig.column.typeString)

        # Check if our index is empty.  If it is, create an empty leafblock to start with
        self.indexFD.seek(0, os.SEEK_END)
        if self.indexFD.tell() == 0:
            self.indexFD.write(LeafBlock(0, self.colType).toString())
            self.indexFD.flush()


    def __str__(self):
        """ Prints a visual representation of this Index. """

        def strInner(_blockAddress, _indentation):
            toReturn = []
            block = self._getBlockAtAddress(_blockAddress)

            toReturn.append(" ".join((
                (" " * _indentation),
                str(block.address),
                "(<= %s)" % block.parent,
                "L" if block.isLeaf else "I",
                "(minKey:%s)" % ("-" if not block.keys else block.keys[0]),
                "(numKeys:%s)" % len(block.addresses),
            )))

            if isinstance(block, InteriorBlock):
                for addr in block.addresses:
                    toReturn.extend(strInner(addr, _indentation + 2))
            return toReturn

        rootBlock = self._getBlockAtAddress(0)
        toReturn = [
            "\n",
            "Index Details:",
            "Max number keys: %s" % rootBlock.maxKeys,
            "DataType: %s" % self.colType
        ]
        toReturn.extend(strInner(0, 0))
        toReturn.append('')
        return "\n".join(toReturn)


    # Private methods
    def _lookupBlock(self, key, startAddress=0, findLeaf=0):
        """
        Iterates down the Index tree to find a block containing the given key.

        Inputs: key          - The key to which we should find a block containing.
                startAddress - The address of the block to begin searching from.
                findLeaf     - Boolean which if true indicates we should find a LeafBlock or return None.
                               If false we will return a leaf block if we can actually find the key in the index,
                               otherwise we will return the lowest interior block that the key could exist in.

        Outputs:
            If findLeaf is True: The leaf block found if successful, else raises a KeyNotFound exception.
            Else: The lowest block found via recursion that the key could possibly reside in.
        """

        block = self._getBlockAtAddress(startAddress)

        while isinstance(block, InteriorBlock):
            try:
                nextAddress = block.lookup(key)

            except KeyNotFound as e:
                if findLeaf:
                    raise e
                return block

            block = self._getBlockAtAddress(nextAddress)

        # If we're here we've found a leaf block, we are done! Return it.
        return block


    def _getBlockAtAddress(self, address):
        """ Returns the index block at the given index. """

        if address in self.cacheMgr:
            return self.cacheMgr.getBlock(address)

        self.indexFD.seek(address)
        block = self.indexFD.read(NanoConfig.index_block_size)

        if not block:
            raise IndexError("Index does not contain an address: %s" % address)

        # Check the first byte of the block to determine whether or not it is a leaf or interior block
        return (LeafBlock if ord(block[0]) else InteriorBlock)(address, self.colType).fromString(block)


    def _writeBlockToFile(self, block):
        """ Marks that the block should be serialized to the index. """

        self.cacheMgr.addBlock(block)


    def _markBlockDeleted(self, block):
        """ Marks that the index at which this block existed is available for a new block to be written to. """

        # Do not allow deletion of the first index block
        if block.address == 0:
            return

        self.delMgr.addRef(block.address)


    def _getAddressForNewBlock(self):
        """ Returns an index which we can write a new block to.  Re-uses previously deleted indices if possible. """

        address = self.delMgr.popRef()
        if address is None:
            # Determine the index of the end of the file;
            # This will be the maximum of either os.SEEK_END, or max(self.dirtyMgr.keys) + NanoConfig.index_block_size
            self.indexFD.seek(0, os.SEEK_END)
            dirtyMax = (max(self.cacheMgr.keys()) + NanoConfig.index_block_size if len(self.cacheMgr.keys()) else -1)
            address = max(self.indexFD.tell(), dirtyMax)

        return address


    def _updateChildrensParent(self, block):
        """ Updates the parent attribute of all children blocks of this InteriorBlock to point to it. """

        if block.isLeaf:
            raise Exception("Cannot call _updateChildrensParent on a LeafBlock.")

        for childAddress in block.addresses:
            child = self._getBlockAtAddress(childAddress)
            child.parent = block.address
            self._writeBlockToFile(child)

    def _updateParentsKeys(self, block, oldKey, newKey):
        """
        In the event that we add a key to the left end of a block, its key (which indicates that everything in the block
        is >= than it) needs to be updated; and this is true for all the parents of this block as well, assuming that
        this block and its parents are the smallest blocks in all of their parents.

        Inputs: block  - The block whose key has been updated
                oldKey - The old key for this block.
                newKey - The new key for this block.
        """

        parent = self._getBlockAtAddress(block.parent)
        # Check if this key was the smallest key in this block.
        if parent.keys[0] == oldKey:
            parent.deleteAddress(block.address)
            parent.add(newKey, block.address)
            self._writeBlockToFile(parent)
            self._updateParentsKeys(parent, oldKey, newKey)

    def _splitBlock(self, block):
        """ Splits a block into two different blocks, each having half of the keys of the original. """

        # Edge case: if we're splitting the root block; simply copy it elsewhere into the tree and create a new root block
        if block.address == 0:
            block.address = self._getAddressForNewBlock()
            block.parent = 0
            newRoot = InteriorBlock(0, self.colType)
            newRoot.add(block.keys[0], block.address)
            self._writeBlockToFile(newRoot)
            self._writeBlockToFile(block)
            # If our root was an interior block, update its children to point to its new address
            if not block.isLeaf:
                self._updateChildrensParent(block)

        # Ensure our parent block has room for another key
        parentBlock = self._getBlockAtAddress(block.parent)
        # If it doesn't, we must split it as well
        if parentBlock.full():
            self._splitBlock(parentBlock)
            # Re-acquire these blocks from the file as its parent may have changed from the splitting of its parent
            block = self._getBlockAtAddress(block.address)
            parentBlock = self._getBlockAtAddress(block.parent)

        # Create a new block and add half our keys to it
        newBlock = (LeafBlock if block.isLeaf else InteriorBlock)(self._getAddressForNewBlock(), self.colType)
        newBlock.parent = parentBlock.address
        middleIndex = len(block.keys) / 2
        block.keys, newBlock.keys = block.keys[:middleIndex], block.keys[middleIndex:]
        block.addresses, newBlock.addresses = block.addresses[:middleIndex], block.addresses[middleIndex:]

        # If we've split an interior block we need to update the parent of each of the blocks we just copied over
        if not block.isLeaf:
            self._updateChildrensParent(newBlock)

        # Add the new block to our parent
        parentBlock.add(newBlock.keys[0], newBlock.address)

        # Serialize the parent, old, and new block to the index file
        self._writeBlockToFile(block)
        self._writeBlockToFile(newBlock)
        self._writeBlockToFile(parentBlock)


    def _iterate(self, minValue=None, maxValue=None, minEqual=False, maxEqual=False, blockAddress=0):
        """
        Recursive function 
        Iterates over the values in this Index, optionally starting at a min value and ending at a max value.

        Inputs: minValue - An optional value which serves as a minimum value for any values returned.
                maxValue - An optional value which serves as a maximum value for any values returned.
                minEqual - If minValue != None, specifies that we want to return a value that matches minValue exactly.
                maxEqual - If maxValue != None, specifies that we want to return a value that matches maxValue exactly.
                blockAddress - The address of the block to begin searching in.

        Returns: An iterator over the list of file positions pointed to by this index.
        """

        block = self._getBlockAtAddress(blockAddress)

        # If this block is empty, do nothing
        if not block.keys:
            return
        # Ensure that all of our keys are not less than the minValue nor greater than the maxValue
        if maxValue is not None and (block.keys[0] >= maxVal if maxEqual else block.keys[0] > maxVal):
            return
        if minValue is not None and (block.keys[-1] < minValue if minEqual else block.keys[-1] <= minValue):
            return 

        minCondition = lambda x: (x >= minValue if minEqual else x > minValue)
        maxCondition = lambda x: (x <= maxValue if maxEqual else x < maxValue)
        condition = lambda x: minCondition(x) and maxCondition(x)

        # Find all keys that apply and iterate over them seperately
        toIterate = [address for key, address in zip(block.keys, block.addresses) if condition(key)]

        for address in toIterate:
            # If this is an interior block, iterate over the block at this address
            if isinstance(block, InteriorBlock):
                for val in self._iterate(minValue, maxValue, minEqual, maxEqual, address):
                    yield val

            # Otherwise this is a leaf block, just yield the address
            else:
                yield address


    # Public methods
    def lookup(self, key): # TODO modify indexblock to lookup -> keynotfounderror
        """
        Looks up the position of a single value in the database table file

        Inputs: key - The key to look up in the index.

        Returns: The position in the database table file that the tuple with the given key appears in if found.
                 Raises a NanoBlocks.Index.KeyNotFound if it does not exist in the index.
        """

        block = self._lookupBlock(key, findLeaf=True)

        position = block.lookup(key)

        return position


    def lookupCondition(self, condition):
        """
        Returns a list of positions in the database table file which satisfy the given condition.

        Inputs: condition - An instance of NanoTools.NanoCondition containing the conditions to look up.

        Returns: A list of positions of tuples in the database table file satisfying the given condition.
        """

        positions = []

        if condition.inItems is not None:
            for item in condition.inItems:
                try:
                    positions.append(self.lookup(item))

                except KeyNotFound:
                    pass

        positions.extend(self._iterate(condition.minValue, condition.maxValue, condition.minEqual, conition.maxEqual, 0))

        return positions


    def add(self, key, pos):
        """
        Adds the given key to the index.

        Inputs: key - The value of the column in the tuple to be looked up upon.
                pos - The position of the tuple in the database table file.
        """

        block = self._lookupBlock(key)

        # If our search yielded an interior block, then this key is less than all other keys in this block.
        # In this case, we want to check our leftmost block to see if we can add this key to it.  This requires it
        # to be a leaf block and to not be full
        if isinstance(block, InteriorBlock):
            leftBlock = self._getBlockAtAddress(block.addresses[0])
            if isinstance(leftBlock, LeafBlock) and not leftBlock.full():
                prevKey = leftBlock.keys[0]
                leftBlock.add(key, pos)
                self._writeBlockToFile(leftBlock)
                self._updateParentsKeys(leftBlock, prevKey, key)
                return

        # Otherwise, we are either adding to a leaf block or adding a new block to an interior block
        # however if this block is full we cannot do either.  Split it if it is
        if block.full():
            self._splitBlock(block)
            # Now, we no longer know whether or not this block is the block which this key should be inserted into;
            # as it is just as likely that we should be inserting into the new block which was just created when we
            # split the existing block.  Because of this, find the correct block to insert into again from scratch.
            block = self._lookupBlock(key)

        # At this point there are two things we can do:
        #  If this is an interior block we need to add a new leaf block to it
        #  If this is a leaf block we need to add the value to it
        if isinstance(block, InteriorBlock):
            # Record what the previous first key in our interior block was; if we add the new leaf block to the front of
            # our interior block we will potentially need to update our interior blocks parents reference keys to it
            prevKey = block.keys[0]
            leaf = LeafBlock(self._getAddressForNewBlock(), self.colType)
            leaf.parent = block.address
            leaf.add(key, pos)
            block.add(key, leaf.address)
            self._writeBlockToFile(leaf)
            self._writeBlockToFile(block)
            if block.keys[0] != prevKey:
                self._updateParentsKeys(block, prevKey, block.keys[0])

        # Otherwise we found a leaf, add this value to it
        else:
            block.add(key, pos)
            self._writeBlockToFile(block)


    def delete(self, key):
        """
        Deletes the first entry in the index matching the given value.

        Inputs: key - The key to delete from the index.

        Outputs: None if successful; raises a KeyNotFound exception if the key cannot be found.
        """

        block = self._lookupBlock(key, findLeaf=True)

        block.delete(key)
        self._writeBlockToFile(block)

        # Iterate through this blocks lineage; deleting empty (non-root) blocks
        while len(block.keys) == 0 and block.address != 0:
            self._markBlockDeleted(block)
            parent = self._getBlockAtAddress(block.parent)
            parent.deleteAddress(block.address)
            self._writeBlockToFile(parent)
            block = parent

        # Edge case; if we iterated all the way up to the root block, check if it's empty.
        # if it is, convert it into an empty leaf block
        if block.address == 0 and len(block.keys) == 0 and isinstance(block, InteriorBlock):
            self._writeBlockToFile(LeafBlock(0, self.colType))


    def close(self):
        self.cacheMgr.flushAll()
        self.delMgr.close()
        self.indexFD.close()
