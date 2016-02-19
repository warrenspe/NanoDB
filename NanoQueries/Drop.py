# Project imports
from _BaseQuery import BaseQuery
import NanoIO.File

class Drop(BaseQuery):
    target = None
    ifExists = None
    name = None

    grammar = """
                  <target: %(table|database)%>
                  ["if" <ifExists: "exists">]
                  <name: _>
              """

    def executeQuery(self, conn):
        if self.target == "database":
            if self.ifExists and not NanoIO.File.checkDatabaseExists(self.name):
                return
            NanoIO.File.deleteDatabase(self.name)
            conn.close([self.target])


        elif self.target == "table":
            dbName, tableName = conn._parseName(self.name)

            if self.ifExists and not NanoIO.File.checkTableExists(tableName):
                return

            tableIO = conn._getTable(self.name)

            # Delete all associated indices for this table
            for colName, index in tableIO.indices.items():
                index.close()
                NanoIO.File.deleteIndex(dbName, tableName, colName)

            # Delete the table itself
            tableIO.close()
            NanoIO.File.deleteTable(dbName, tableName)
            conn._schemas[dbName].pop(tableName)
