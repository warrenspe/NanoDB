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
            NanoFileIO.assertDatabaseExists(self.oldName)
            if NanoFileIO.checkDatabaseExists(self.newName):
                raise Exception("Database %s already exists" % self.newName)
            os.rename(os.path.join(NanoConfig.root_dir, self.oldName),
                      os.path.join(NanoConfig.root_dir, self.newName))
            if conn.currentDatabase() == self.oldName:
                conn.selectDB(self.newName)
        elif self.target == "table":
            conn.getCursor(conn.dbName, self.oldName).close()
            del conn.cursors[conn.dbName][self.oldName]

            os.rename(os.path.join(NanoConfig.root_dir, self.oldName),
                      os.path.join(NanoConfig.root_dir, self.newName))

            # TODO rename indices
