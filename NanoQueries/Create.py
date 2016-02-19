# Project imports
from _BaseQuery import BaseQuery
import NanoIO.File
import NanoConfig.Table
import NanoConfig.Index
import NanoConfig.Column
import NanoTypes

class Create(BaseQuery):
    target = None
    name = None
    cols = None
    indices = None

    grammar = """
                  [<target: "database"> <name: _>]
                  [
                   <target: "table">
                   <name: _>
                   {
                    (cols: <name: _!index_> <type: _>)
                    ["index" <indices: _>]
                   }
                  ]
              """

    def executeQuery(self, conn):
        if self.target == "database":
            NanoIO.File.createDatabase(self.name)

        elif self.target == "table":
            dbName, tableName = conn._parseName(self.name)

            # Assert that the database exists, but the table does not
            NanoIO.File.assertDatabaseExists(dbName)
            if NanoIO.File.checkTableExists(dbName, tableName):
                raise IOError("Cannot create table, table file %s.%s already exists" % (dbName, tableName))
            if NanoIO.File.checkConfigExists(dbName, tableName):
                raise IOError("Cannot create table, config file for table %s.%s already exists" % (dbName, tableName))

            tableConfig = NanoConfig.Table.Config()
            tableConfig.name = tableName

            # Add columns to this table
            colDict = dict()
            tableConfig.columns = []
            rowSize = 1
            for column in self.cols:
                # Sanity check; disallow duplicated column names
                if column['name'] in colDict:
                    raise Exception("Duplicated column name: %s" % column['name'])

                columnConfig = NanoConfig.Column.Config()
                columnConfig.name = column['name']
                columnConfig.typeString = column['type']
                # Validate this type string
                typ = NanoTypes.getType(columnConfig.typeString)
                colDict[column['name']] = columnConfig
                tableConfig.columns.append(columnConfig)
                rowSize += typ.size

            tableConfig.rowSize = rowSize

            # Add indices to this table
            idxSet = set()
            tableConfig.indices = []
            if self.indices:
                for index in self.indices:
                    # Sanity check; disallow duplicated indices
                    if index in idxSet:
                        raise Exception("Duplicated index name: %s" % index)
                    # Ensure this indexed column exists in our table
                    if index not in colDict:
                        raise Exception("Cannot create index on missing column: %s" % index)
                    # Ensure that the index file for this index doesn't somehow already exist
                    if NanoIO.File.checkIndexExists(dbName, tableName, index):
                        raise Exception("Cannot create table %s.%s; index file already exists at %s" % \
                                        (dbName, tableName, NanoIO.File.indexPath(dbName, tableName, index)))

                    idxSet.add(index)

                    indexConfig = NanoConfig.Index.Config()
                    indexConfig.column = colDict[index]
                    tableConfig.indices.append(indexConfig)

                # Create each index for this table
                for index in self.indices:
                    NanoIO.File.createIndex(dbName, tableName, index)

            # Create this table
            configFD = NanoIO.File.createTable(dbName, tableName)
            configFD.write(tableConfig.toString())
            configFD.close()
