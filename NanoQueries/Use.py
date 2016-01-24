# Project imports
from _BaseQuery import BaseQuery

class Use(BaseQuery):
    name = None

    grammar = """
                  <name: _>
              """

    def executeQuery(self, conn):
        conn.selectDB(self.name)
