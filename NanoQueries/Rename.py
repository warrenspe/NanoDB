# Standard imports
import os

# Project imports
from _BaseQuery import BaseQuery
import NanoIO.File
import NanoConfig

class Rename(BaseQuery):
    target = None
    oldName = None
    newName = None

    grammar = """
                  <target: %(table|database)%>
                  <oldName: _>
                  "to"
                  <newName: _>
              """

    def executeQuery(self, conn):
        if self.target == "database":
            # Ensure that the database we're renaming exists, and that its new name doesn't
            NanoFileIO.assertDatabaseExists(self.oldName)
            if NanoFileIO.checkDatabaseExists(self.newName):
                raise Exception("Database %s already exists" % self.newName)

            # Rename the database
            os.rename(NanoIO.File.dbPath(self.oldName), NanoIO.File.dbPath(self.newName))

            # If we had currently selected the old database, unselect it
            if conn.currentDatabase() == self.oldName:
                conn.selectDB(None)

            # Close any old tableIO connections we had open
            conn.close(dbNames=[self.oldName])

        elif self.target == "table":
            # Parse a dbName and tableName out of the new schema
            dbName, tableName = conn._parseName(newName)

            # Get the table
            table = conn._getTable(oldName)

            # Rename the table
            NanoIO.File._renameTable(table, dbName, tableName)

            # Close the old TableIO object in the connection
            conn.close([dbName], [oldTableNam])
