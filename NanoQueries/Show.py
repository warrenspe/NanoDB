# Project imports
from _BaseQuery import BaseQuery

class Show(BaseQuery):
    inDB = None
    like = None

    grammar = """
                  "tables"
                  ["in" <inDB: _>]
                  ["like" <like: _str_>]
              """
