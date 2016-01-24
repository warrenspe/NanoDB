class CacheableBlock:
    """
    Class which provides an interface for a BlockCacheManager to work with when
    caching objects.
    """

    address = None # The address this block resides in in the file.

    # Private methods
    def _write(self, fd):
        """
        Writes this block to memory.

        Inputs: fd - A file descriptor of the file to write to.
        """

        fd.seek(self.address)
        fd.write(self.toString())


    # Subclassable methods
    def toString(self):
        """
        Function which must be overridden by classes extending this class.

        Should return a string representation of the block to write to the file.
        """

        raise NotImplementedError

