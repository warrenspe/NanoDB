# Project imports
from _BaseQuery import BaseQuery

class Describe(BaseQuery):
    name = None

    grammar = """
                  "table" <name: _>
              """
