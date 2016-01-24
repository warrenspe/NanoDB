# Project import
from _BaseQuery import BaseQuery

class Update(BaseQuery):
    name = None
    colSets = None
    where = None
    orderBy = None
    orderByDir = None
    limit = None

    grammar = """
                  <name: _>
                  "set"
                  {(colSets: <name: _> "=" <val: _all_>)}
                  ["where" *where: order, limit*]
                  ["order" "by" <orderBy: _> <orderByDir: %(asc|desc)%>]
                  ["limit" <limit: %\d+%>]
              """
