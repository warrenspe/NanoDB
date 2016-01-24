# Standard imports
import copy

# Project imports
from _BaseQuery import BaseQuery
import NanoIO.Table
import NanoIO.File

class Alter(BaseQuery):
    name = None
    addColumns = None
    removeColumns = None
    modifyColumns = None
    addIndex = None
    removeIndex = None

    grammar = """
                  "table"
                  <name: _>
                  {
                   (addColumns: "add" "column" <name: _> <type: _>)
                   (removeColumns: "remove" "column" <name: _>)
                   (modifyColumns: "modify" "column" <name: _> <newName: _> <newType: _>)
                   ["add" "index" <addIndex: _>]
                   ["remove" "index" <removeIndex: _>]
                  }
              """

    def executeQuery(self, conn):
        # Get tableIO object
        tableIO = conn._getTable(self.name)

        # Create a new tableIO object
        #if NanoFile.checkTable

        tmpTableName = "_tmp_alter_table_" + tableIO.tableName
        NanoIO.File.createTable(tableIO.dbname, tmpTableName)
        newTableIO = NanoIO.Table.TableIO(tableIO.dbName, tmpTableName)

        # Update config
        newTableIO.config

        # Update table definition

        # Remove indices
