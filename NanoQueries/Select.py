# Project imports
from _BaseQuery import BaseQuery

class Select(BaseQuery):
    distinct = None
    name = None
    attrs = None
    innerJoins = None
    leftJoins = None
    where = None
    orderBy = None
    orderByDir = None
    limit = None


    grammar = """
                  [<distinct: "distinct">]
                  {<attrs: _!from_>}
                  "from"
                  <name: _>
                  {
                   (innerJoins: "inner" "join" <name: _> "on" *condition: inner, left, where, order, limit*)
                   (leftJoins: "left" "join" <name: _> "on" *condition: inner, left, where, order, limit*)
                  }
                  ["where" *where: order, limit*]
                  ["order" "by" <orderBy: _> <orderByDir: %(asc|desc)%>]
                  ["limit" <limit: %\d+%>]
              """
