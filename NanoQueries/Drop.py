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
            if self.ifExists and not NanoFileIO.checkDatabaseExists(self.name):
                return
            NanoFileIO.deleteDatabase(self.name)
            if self.name in conn.cursors:
                for cursor in conn.cursors[self.name].values():
                    cursor.close()
                conn.cursors.pop(self.name)


        elif self.target == "table":
            if self.ifExists and not NanoFileIO.checkTableExists(self.name):
                return
            dbName, tableName = conn._parseName(self.name)
            NanoFileIO.deleteTable(dbName, tableName)
            if conn._hasCursor(dbName, tableName):
                cursor = conn.getCursor(dbname, tableName)
                cursor.close()
                conn.cursors[dbName].pop(tableName)
                conn.cursorList.pop(cursor)
