# Project imports
from _BaseQuery import BaseQuery

class Delete(BaseQuery):
    name = None
    condition = None
    orderBy = None
    orderByDir = None
    limit = None

    grammar = """
                  "from"
                  <name: _>
                  ["where" *condition: order, limit*]
                  ["order" "by" <orderBy: _> <orderByDir: %(asc|desc)%>]
                  ["limit" <limit: %\d+%>]
              """

    def executeQuery(self, conn):
        pass
