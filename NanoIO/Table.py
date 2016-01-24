"""
File containing a class which allows manipulation & access to database tables.
"""

# Standard imports
import os

# Project imports
import NanoTools
import NanoTypes
import NanoIO.File
import NanoIO.Index
import NanoConfig.Table
from NanoBlocks._MemoryMappedBlock import MemoryMappedBlock

class TableIO:
    """ Class which can be instantiated for a given table that can be later called to access / manipulate said table. """

    dbName = None          # Name of the database this table resides in
    tableName = None       # Name of the table we're manipulating
    config = None          # A NanoConfig.Table.Config instance for this table
    configFD = None        # A file descriptor open to the file for this table's configuration
    tableFD = None         # A file descriptor open to the file for this table
    indices = None         # A dictionary mapping column names on this table to NanoIO.Index.IndexIO instances
    delMgr = None          # A NanoTools.DeletedBlockManager instance to manage deleted rows of this table
    memoryMappedRow = None # A class subclassing MemoryMappedBlock that can be used to convert values to/from strings

    # Data Model methods
    def __init__(self, dbName, tableName):
        self.dbName = dbName
        self.tableName = tableName
        self.tableFD = NanoIO.File.getTable(dbName, tableName)
        self.configFD = NanoIO.File.getConfig(dbName, tableName)
        self.delMgr = NanoTools.DeletedBlockManager(dbName, tableName)
        self._getTableConfig()
        self._initializeIndices()
        self.constructMemoryMappedRow()

    def __del__(self):
        try:
            self.close()
        except AttributeError:
            pass

    # Private methods
    def _getTableConfig(self):
        """ Sets the associated table configuration for this table file on this instance. """

        self.configFD.seek(0)
        self.config = NanoConfig.Table.Config().fromString(self.configFD.read())


    def _setTableConfig(self):
        """ Updates the configuration file for this table based on self.config. """

        self.configFD.seek(0)
        self.configFD.truncate()
        self.configFD.write(self.config.toString())


    def _initializeIndices(self):
        """ Initializes self.indices to be a dictionary mapping index column names to IndexIO instances. """

        self.indices = dict()
        for indexConfig in self.config.indices:
            self.indices[indexConfig.column.name] = NanoIO.Index.IndexIO(self.dbName, self.tableName, indexConfig)


    def constructMemoryMappedRow(self):
        """
        Creates a class, subclassing MemoryMappedBlock, that can be used to serialize rows to our data file,
        and convert serialized rows back into classes in memory.
        """

        class MemoryMappedRow(MemoryMappedBlock):
            """
            Class which can be used to get/store rows for this table.  Adds an additional byte flag to the beginning
            of each and every row to indicate whether or not that row is still valid. (When a row is deleted it will
            be set to False).
            """

            blockSize = self.config.rowSize
            fields = ['_valid'] + [col.name for col in self.config.columns]
            dataTypes = [NanoTypes.Uint(1)] + [NanoTypes.getType(col.typeString) for col in self.config.columns]

        self.memoryMappedRow = MemoryMappedRow


    def _writeRowAt(self, pos, row):
        """
        Writes a row to a given position in the data file.

        Inputs: pos - The position to write the row to.  If None, the row will be written to either a position returned
                      from self.delMgr, or if that returns None as well, the end of the file.
                row - An instance of self.memoryMappedRow to write to the file.
        """

        if pos is None:
            idx = self.delMgr.popRef()
            if idx is None:
                self.tableFD.seek(0, os.SEEK_END)
            else:
                self.tableFD.seek(idx)
        else:
            self._seekPos(pos)

        self.tableFD.write(row.toString())

    def _validateFields(self, *args, **kwargs):
        """
        Ensures that we weren't given more positional arguments than our row can handle,
        and that all keyword arguments appear in our row.
        """

        if len(args) > len(self.config.columns):
            raise Exception("Too many values given for table %s. Values: %s" % (self.config.name, args))

        for kwarg in kwargs:
            if kwarg not in self.memorymappedRow.fields:
                raise Exception("Unknown value given for table %; value: %s" % (self.config.name, kwarg))


    def _valsToRow(self, *args, **kwargs):
        """ Uses given positional and keyword arguments to populate an instance of self.memoryMappedRow. """
        
        self._validateFields(*args, **kwargs)

        row = self.MemoryMappedRow()
        row._valid = True
        toSet = dict(zip(self.memoryMappedRow.fields, args))
        toSet.update(kwargs)
        for key, val in toSet.items():
            setattr(row, key, val)

        return row


    def _posToIdx(self, pos):
        """ Converts a position (0, 1, 2, 3, ...) to an index (which is a multiple of self.rowSize). """

        return self.config.rowSize * pos


    def _seekPos(self, pos):
        """ Seeks self.tableFD to the given position index. """

        self.tableFD.seek(self._posToIdx(pos))


    # Public methods
    def close(self):
        """ Closes all active file descriptors associated with this object. """

        self.delMgr.close()
        self.configFD.close()
        self.tableFD.close()


    def truncate(self):
        """ Truncates our data file for this table. """

        self.tableFD.seek(0)
        self.tableFD.truncate()


    def getRow(self, pos):
        """ Gets the row from this table at the given position (0, 1, 2, 3, ...). """

        self._seekPos(pos)
        row = self.memoryMappedRow.fromString(self.tableFD.read(self.config.rowSize)) # TODO test if file is empty, get pos 1
        if not row._valid:
            raise Exception("No data at position %d" % pos)
        return row


    def insertRow(self, *args, **kwargs):
        """ Inserts a row into our table file using the given values to construct the row. """

        row = self._valsToRow(*args, **kwargs)
        self._writeRowAt(None, row)


    def updateRow(self, pos, **kwargs):
        """ Updates the row in the file at the given position, updating the values from the given keyword arguments. """

        self._validateFields(**kwargs)
        row = self.getRow(pos)
        for kwarg in kwargs:
            setattr(row, kwarg, kwargs[kwarg])

        self._writeRowAt(pos, row)


    def deleteRow(self, pos):
        """ Deletes the row in the file at the given position. """

        row = self.getRow(pos)
        row._valid = False
        self._writeRowAt(pos, row)
        self.delMgr.addRef(self._posToIdx(pos))
