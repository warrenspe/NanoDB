# Project imports
from _BaseQuery import BaseQuery
import NanoConfig.Table

class Insert(BaseQuery):
    name = None
    vals = None

    grammar = """
                  "into"
                  <name: _>
                  "values"
                  {<vals: _all_>}
              """

    def executeQuery(self, conn):
        dbName, tableName = conn._parseName(self.name)

        tableIO = conn._getTable(self.name)

        # Ensure an expected number of values
        if len(self.vals) != len(tableIO.config.columns):
            raise Exception("Number of values given, %d != number columns, %d" % \
                            (len(self.vals), len(tableIO.config.columns)))

        tableIO.insertRow(*self.vals)
