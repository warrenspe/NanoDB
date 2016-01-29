# Standard imports
import re

# Project imports
from NanoQueries._QueryGrammar import QueryParser, tokenizeQuery

class BaseQuery:
    queryParser = None

    def __init__(self, query):
        queryTokens = tokenizeQuery(query)

        if len(queryTokens) == 0:
            raise Exception("No query given")

        elif queryTokens[0].lower() != self.__class__.__name__.lower():
            raise Exception("%s called for a %s query" % (self.__class__.__name__, queryTokens[0]))

        if self.queryParser is None:
            self.__class__.queryParser = QueryParser(self.__class__)

        self.queryParser.populate(self, queryTokens[1:])

    def executeQuery(self, conn):
        """
        Function which executes this instance of the query.

        Inputs: conn - The NanoConnection calling us.

        Outputs: A dictionary to be wrapped as a NanoResult.
        """

        raise NotImplementedError

    # TODO transaction support
    def begin(self):
        pass
    def rollback(self):
        pass
