# Project imports
from _BaseQuery import BaseQuery
import NanoIO.File
import NanoConfig.Table

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
            NanoIO.File.makeDatabase(self.name)

        elif self.target == "table":
            dbName, tableName = conn._parseName(self.name)
            configFD = NanoFileIO.makeTable(dbName, tableName)
            tableConfig = NanoConfig.Table.Config()
            tableConfig.initializeValues(self.name, zip(*[iter(self.cols)]*2), zip(*[iter(self.indices)]*2))
            tableConfig.write(configFD)
