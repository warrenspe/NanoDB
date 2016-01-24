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

        cursor = conn.getCursor(dbName, tableName)

        # Ensure an expected number of values
        if len(self.vals) != len(cursor.config.cols):
            raise Exception("Number of values given, %d != number columns, %d" % \
                            (len(self.vals), len(cursor.config.cols)))

        # Type assertions
        #for typ in cursor.config.cols:
        #    try:
        #        if typ == "int":
        #            int( # TODO
                
