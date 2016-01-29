# Standard imports
import os

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

        # Back up the TableIO object
        #NanoIO.File._renameTable(tableIO, "_NanoDB_Backup

        # Create a new TableIO object

        # Overwrite our connections tableio object for this table


        # Add columns as desired to our new table io object

        # Remove columns as desired from this table io object

        # Modify columns as desired to this table io object

        # Add indices as desired to this table io object

        # Remove indices as desired from this table io object

        # Serialize our new table io object

        # Copy data from our old table to our new table

        # Delete our old table IO object

        tmpTableName = "_tmp_alter_table_" + tableIO.tableName
        NanoIO.File.createTable(tableIO.dbname, tmpTableName)
        newTableIO = NanoIO.Table.TableIO(tableIO.dbName, tmpTableName)

        # Update config
        newTableIO.config

        # Update table definition

        # Remove indices
