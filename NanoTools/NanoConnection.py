"""
File containing a connection class which can be instantiated and used to access and act upon NanoDBs.
"""

# Standard imports
import collections

# Project imports
import NanoIO.Table
import NanoQueries
import NanoQueries._QueryGrammar

###
# Helper Functions / classes
###
class SelectDBExitRecord:
    """ Class which allows the use of `with` with a Connections selectDB method. """
    connection = None
    dbName = None
    
    def __init__(self, connection, dbName):
        self.connection = connection
        self.dbName = dbName
    def __enter__(self):
        pass
    def __exit__(self, typ, val, tb):
        self.connection.dbName = self.dbName

def parseQuery(query):
    queryType = (query[:query.find(' ')] if query.find(' ') != -1 else query).title()

    if hasattr(NanoQueries, queryType):
        return getattr(NanoQueries, queryType)(query)


###
# API Classes
###


class Result:
    rowcount = None
    rows = None

    def __init__(self, rows, rowcount=None):
        self.rows = rows
        self.rowcount = rowcount
        if self.rowcount is None:
            self.rowcount = len(rows)


class NanoConnection:
    # Public Attributes
    dbName = None  # Name of the currently selected database, if one is selected. Else None

    # Private Attributes
    _schemas = None # Dictionary mapping database names to dictionaries, mapping table names to TableIOs

    # Data Model methods
    def __init__(self, dbName=None):
        if dbName is not None:
            self.selectDB(dbName)
        self._schemas = collections.defaultdict(dict)

    def __enter__(self):
        return self


    def __exit__(self, a, b, c):
        self.close()


    def __del__(self):
        try:
            self.close()
        except AttributeError:
            pass


    # Private methods
    def _getTable(self, name):
        dbName, tableName = self._parseName(name)
        if tableName not in self._schemas[dbName]:
            self._schemas[dbName][tableName] = NanoIO.Table.TableIO(dbName, tableName)

        return self._schemas[dbName][tableName]
        

    def _parseName(self, name):
        if name.count(".") == 1:
            return name.split('.')
        if self.dbName is None:
            raise Exception("Database not selected.")
        return self.dbName, name


    # Public methods
    def execute(self, query):
        queryObj = parseQuery(query)
        return queryObj.executeQuery(self) # TODO handle wrapping in Result instance
        

    def close(self, dbNames=None):
        for dbName, dbDict in self._schemas.items():
            if dbNames is None or dbName in dbNames:
                for tableName, tableIO in dbDict.items():
                    tableIO.close()
                    self._schemas[dbName].pop(tableName)
                self._schemas.pop(dbName)

    def begin(self):
        pass # TODO transaction support

    def commit(self):
        pass # TODO transaction support

    def rollback(self):
        pass # TODO transaction support

    def selectDB(self, dbName):
        """
        Switches the current database to dbName, if it exists.  Supports usage with pythons 'with' statement:

        with conn.selectDB('dbA'):
            # Do things with dbA
        # original db is restored
        """
        
        if dbName is not None:
            NanoIO.File.assertDatabaseExists(dbName)

        record = SelectDBExitRecord(self, self.dbName)
        self.dbName = dbName
        return record

    use = selectDB
