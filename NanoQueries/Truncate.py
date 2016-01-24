# Project imports
from _BaseQuery import BaseQuery

class Truncate(BaseQuery):
    name = None

    grammar = """
                  "table"
                  <name: _>
              """

    def executeQuery(self, conn):
        cursor = conn.getCursor(conn._parseName(self.name))
        cursor.truncate()
