"""
File containing tools used by NanoIndices & NanoQueries for the handling and usage of conditions in queries.
"""

# Globals
BINARY_OPERATORS = ("+", "-", "/", "*", "%")
LOGICAL_OPERATORS = ("!=", "<=", ">=", "==", "<", ">", "in")
UNARY_NEGATIONS = ("not",)
BINARY_CONJUNCTIONS = ("and", "or")


###
# Exceptions
###
class ConditionParsingException(Exception):
    msg = None
    tokens = None
    idx = None

    def __init__(self, msg, tokens=None, idx=0):
        self.msg = msg
        self.tokens = tokens
        self.idx = max(0, idx - 1)

    def __str__(self):
        if self.tokens:
            return "%s near %s" % (self.msg, " ".join(self.tokens[self.idx: self.idx + 5]))
        else:
            return self.msg

###
# Utility Classes
###
class EvalStatement:
    """
    Class which provides eval functionality for classes inheriting it.
    """

    _compiled = None

    def __str__(self):
        try:
            return self.toString()
        except NotImplementedError:
            return repr(self)

    def toString(self):
        """
        Returns a string representation of this class, suitable for passing to eval.
        """

        raise NotImplementedError

    def compile(self):
        """
        Compiles self into a code object, and both sets on self and returns this code object.
        """

        if not self._compiled:
            self._compiled = compile(self.toString(), "NanoDB", "eval")

        return self._compiled

    def eval(self, localVars=None):
        """
        Returns the result of running eval on self.

        Inputs: localVars - A dictionary of mappings to pass to eval.
        """

        return eval(self.compile(), None, localVars)

class BaseStatement(EvalStatement):
    """
    Super class of statements.
    """

    def _getFilters(self, filterNames):
        """
        Returns a list of filters which must be used for passes over an index.

        Inputs: filterNames - A set of tokens which can be filtered upon.
        """

        raise NotImplementedError

class Filter:
    """
    Class which represents a filter, to be applied to an index to reduce the number of tuples examined.

    Requires that a name of a column in the database appear on one side of one of a certain set of operators,
    and that a constant appears on the other side.
    """

    filterName = None

    # Filters
    greaterThan = None
    lessThan = None
    inItems = None

    # Filter flags
    greaterThanEqual = None
    lessThanEqual = None

    _oprDict = {'>': "greaterThan",
                '<': "lessThan",
                '>=': "greaterThan",
                '<=': "lessThan",
                '==': "inItems",
                'in': 'inItems',
    }
    _equalFlag = {
        '>=': ('greaterThanEqual', True),
        '<=': ('lessThanEqual', True),
        '>': ('greaterThanEqual', False),
        '<': ('lessThanEqual', False),
    }

    def __init__(self, filterName, opr, value):
        self.filterName = filterName

        attrName = self._oprDict[opr]

        # Edge cases, opr is `==` or `in`
        if opr == '==' and not hasattr(value, '__iter__'):
            setattr(self, attrName, [value])
        elif opr == 'in':
            setattr(self, attrName, list(value))
        else:
            setattr(self, attrName, ([value] if opr == '==' else value))

        if opr in self._equalFlag:
            setattr(self, *(self._equalFlag[opr]))

    def inverse(self):
        """
        Inverses all the filters on this instance.  Used when a NegateStatement nots a filter.
        """

        self.greaterThan, self.lessThan = self.lessThan, self.greaterThan
        self.greaterThanEqual, self.lessThanEqual = self.lessThanEqual, self.greaterThanEqual

        # We can't filter on =='s if we've inversed # TODO record !='s so we can flip them
        self.inItems = None

        return self


    def update(self, otherFilter):
        """
        Merges another filter into this filter.
        """

        # Ensure the filterNames are the same
        if otherFilter.filterName != self.filterName:
            raise Exception("Cannot merge filter: %s into self: %s" % (otherFilter.filterName, self.filterName))

        if otherFilter.greaterThan is not None and (self.greaterThan is None or otherFilter.greaterThan > self.greaterThan):
            self.greaterThan = otherFilter.greaterThan
            self.greaterThanEqual = otherFilter.greaterThanEqual
        if otherFilter.lessThan is not None and (self.lessThan is None or otherFilter.lessThan < self.lessThan):
            self.lessThan = otherFilter.lessThan
            self.lessThanEqual = otherFilter.lessThanEqual
        if otherFilter.inItems is not None:
            if self.inItems is None:
                self.inItems = otherFilter.inItems
            else:
                for item in otherFilter.inItems:
                    if item not in self.inItems:
                        self.inItems.append(item)

        return self


###
# Statement classes
###
class Statement(BaseStatement):
    """
    Class representing a singular statement, ie should not contain any conjunctions.
    Examples: a < (5 + 4)
              6 == 4
              "test"
    """

    left = None       # Left side of the statement
    opr = None        # Operator of the statement
    right = None      # Right side of the statement

    def __init__(self, left, opr=None, right=None):
        self.left = left
        self.opr = opr
        self.right = right

        # To ensure the syntactical validity of the statements we were initialized with, compile ourself
        try:
            self.compile()
        except SyntaxError:
            invalidSyntax = " ".join([str(tok) for tok in left])
            if self.opr:
                invalidSyntax += " %s " % self.opr
            if self.right:
                invalidSyntax += " ".join([str(tok) for tok in right])
            raise ConditionParsingException("Invalid Syntax: %s" % invalidSyntax)

    def toString(self):
        if self.opr:
            return "((%s) %s (%s))" % (" ".join([str(tok) for tok in self.left]),
                                       self.opr,
                                       " ".join([str(tok) for tok in self.right]))
        else:
            return " ".join([str(tok) for tok in self.left])

    def _getFilters(self, filterNames):
        # Ensure our operator is filterable
        if self.opr not in ('>', '<', '<=', '>=', '==', 'in'):
            return []

        # Determine if either our right or left is a filterable name
        if len(self.left) == 1 and self.left[0] in filterNames:
            filterName = self.left[0]
            filterValue = " ".join([str(tok) for tok in self.right])
        elif len(self.right) == 1 and self.right[0] in filterNames:
            filterName = self.right[0]
            filterValue = " ".join([str(tok) for tok in self.left])
        else:
            return []

        # Ensure that the other side is a constant; ie it does not require any name mappings to evaluate
        try:
            filterValue = eval(filterValue)
        except NameError:
            return []

        # If everything checked out, return a filter
        return [Filter(filterName, self.opr, filterValue)]


class NegateStatement(BaseStatement):
    """
    Class which contains a statement which will be not'd.
    """

    statement = None

    def __init__(self, statement):
        self.statement = statement

    def toString(self):
        return "not (%s)" % self.statement.toString()

    def _getFilters(self, filterName):
        return [filt.inverse() for filt in self.statement._getFilters()]


class OrStatement(BaseStatement):
    """
    Class containing a list of or'd statements/BaseStatements for a condition.
    """

    statements = None # List of or'd statements in this statements

    def __init__(self, *statements):
        self.statements = statements

    def toString(self):
        return " or ".join([statement.toString() for statement in self.statements])

    def _getFilters(self, filterNames):
        filters = dict()
        for statement in self.statements:
            for filt in statement._getFilters(filterNames):
                if filt.filterName in filters:
                    filters[filt.filterName].update(filt)
                else:
                    filters[filt.filterName] = filt
        return filters.values()

class AndStatement(BaseStatement):
    """
    Class containing a list of and'd statements/BaseStatements for a condition.
    """

    statements = None # List of or'd statements in this statements

    def __init__(self, *statements):
        self.statements = statements

    def toString(self):
        return " and ".join([statement.toString() for statement in self.statements])

    def _getFilters(self, filterNames):
        filters = dict()
        for statement in self.statements:
            for filt in statement._getFilters(filterNames):
                if filt.filterName in filters:
                    filters[filt.filterName].update(filt)
                else:
                    filters[filt.filterName] = filt
        return filters.values()

###
# Condition class
###
class NanoCondition:
    """
    Class which represents a condition expressed in a query.  Provides functionality used by NanoIndices to filter
    candidate tuples out of an index.
    """

    mainStatement = None # An instance of AndStatement, OrStatement or BaseStatement for this condition.
    _statementDict = {'and': AndStatement, 'or': OrStatement, 'not': NegateStatement}

    def __init__(self, tokens):
        """
        Initialize an instance of a NanoCondition from the tokens given.

        tokens - A list of tokens as passed in the query.
        """

        self.mainStatement = self.parse(tokens)


    def _findMatchedBracket(self, tokens):
        """
        Accepts a list of tokens where the first is expected to be the first token after the "(" token.
        Returns the index of the associated ")" token, or raises a ConditionParsingException if one does not exist.
        """

        openCount = 1
        for idx, token in enumerate(tokens):
            if token == "(":
                openCount += 1
            elif token == ")":
                openCount -= 1
                if openCount == 0:
                    return idx

        raise ConditionParsingException("Unmatched (", tokens, 0)

    def _findNext(self, tokens, startIdx, toFind):
        """
        Searches for the next occurrance of a token in toFind in tokens that exists in the same scope.  Ie if a match
        occurs within a ( ... ) block it won't be matched.

        Inputs: tokens   - A list of tokens to search for one in toFind in.
                startIdx - The index in tokens to begin searching from.
                toFind   - An iterable of tokens that we are looking for.

        Returns the index of the associated found token, or -1 if one is not found.
        """

        i = startIdx
        while i < len(tokens):
            token = tokens[i]
            i += 1

            # If we encounter an opening brace jump until it closes before we resume searching
            if token == "(":
                i += self._findMatchedBracket(tokens[i:]) + 1

            elif token in toFind:
                return i - 1

        return -1


    def _stripSurroundingBrackets(self, tokens):
        """
        Strips ( ) brackets surrounding the tokens given, if and only if they open and close each other.
        """

        while tokens and tokens[0] == "(" and tokens[-1] == ")":
            if self._findMatchedBracket(tokens[1:]) == len(tokens) - 2:
                tokens = tokens[1:-1]
            else:
                break

        return tokens


    def _constructStatement(self, queryTokens):
        """
        Constructs an instance of Statement from the queryTokens at the given index.

        Inputs: queryTokens - A list of tokens in the query to use to construct an instance of Statement

        Outputs: An instance of Statement if successful, else raises a ConditionParsingException.
        """

        queryTokens = self._stripSurroundingBrackets(queryTokens)

        # Find the location of any logical operators within our tokens
        logicalOperatorIdx = self._findNext(queryTokens, 0, LOGICAL_OPERATORS)

        # If there aren't any, our statement is just a single expression
        if logicalOperatorIdx == -1:
            return Statement(queryTokens)

        # Otherwise we have a binary statement
        else:
            # Ensure we have tokens on either side of the operator
            if logicalOperatorIdx == 0 or logicalOperatorIdx == len(queryTokens) - 1:
                raise ConditionParsingException("Logical operator missing an operand", queryTokens, logicalOperatorIdx)
            left = queryTokens[:logicalOperatorIdx]
            opr = queryTokens[logicalOperatorIdx]
            right = queryTokens[logicalOperatorIdx + 1:]
            return Statement(left, opr, right)


    def parse(self, queryTokens):
        """
        Constructs an instance of one of the Statements to represent the query tokens given

        Inputs: queryTokens - The query tokens to parse into statements.

        Outputs: A Statement, NegateStatement, OrStatement, or AndStatement representing the query given.
        """

        currentTokens = []
        statementTokens = []
        statementClass = None
        negationFlag = False

        # Run through the tokens and break them up their respective statements
        idx = 0
        while idx < len(queryTokens):
            token = queryTokens[idx]

            # If we encounter an opening bracket, ignore all the contents; we're only concerned with our current scope
            if token == "(":
                newIdx = self._findNext(queryTokens, idx + 1, ")")
                if newIdx == -1:
                    raise ConditionParsingException("Unmatched (", queryTokens, idx)

                currentTokens.extend(queryTokens[idx: newIdx + 1])
                idx = newIdx

            elif token.lower() in BINARY_CONJUNCTIONS:
                # If our statementClass is not the same as this token, raise an exception, as it's ambiguous
                # whether or not we should be an `and` statement with `or` substatements, or an `or` statement with
                # `and` substatements.
                if statementClass is not None and self._statementDict[token.lower()] != statementClass:
                    raise ConditionParsingException("Ambigious usage of and's and or's.", queryTokens, idx)
                statementClass = self._statementDict[token.lower()]

                # Group up all the tokens we've seen thus far as tokens for a single statement.
                if not len(currentTokens):
                    raise ConditionParsingException("Conjunction missing operand", queryTokens, idx)

                statementTokens.append({'negate': negationFlag, 'tokens': currentTokens})
                currentTokens = []
                negationFlag = False

            elif token.lower() in UNARY_NEGATIONS:
                # If we encounter a negation ensure there is something following it
                if len(queryTokens) == idx:
                    raise ConditionParsingException("Condition cannot end with a unary negation.", queryTokens, idx)

                negationFlag = not negationFlag

            else:
                currentTokens.append(token)

            idx += 1

        # Once we've parsed through all our tokens, we should have some remaining in currentTokens.
        # If we don't raise an exception
        if not len(currentTokens):
            if statementClass is not None:
                raise ConditionParsingException("Conjunction missing right-hand operand", queryTokens, idx)
            else:
                raise ConditionParsingException("No condition given", queryTokens, 0)

        # Add these remaining tokens to statementTokens
        statementTokens.append({'negate': negationFlag, 'tokens': currentTokens})

        # Create statements for each group of tokens we have
        statements = []
        for tokenDict in statementTokens:
            # If there is a conjunction or negation in this set of tokens recursively call self.parse
            if set([t.lower() for t in tokenDict['tokens']]).intersection(set(BINARY_CONJUNCTIONS + UNARY_NEGATIONS)):
                # Remove any wrapping brackets from the tokens to parse to prevent infinitely looping on brackets
                toAppend = self.parse(self._stripSurroundingBrackets(tokenDict['tokens']))

            # Otherwise, wrap it up as a single statement
            else:
                toAppend = self._constructStatement(tokenDict['tokens'])

            statements.append(NegateStatement(toAppend) if tokenDict['negate'] else toAppend)

        # If we hit a conjunction, create an And/OrStatement, passing all the different statements we parsed
        if statementClass is not None:
            return statementClass(*statements)

        # If we never hit a conjunction we should only have a single statement in our list of statements. Return it.
        return statements[0]


    def lookupStrategy(self): # TODO
        """
        Returns a list of dictionaries, where each indicates a pass over the index that must be made, filters that
        should be used to restrict the number of tuples that needed to be considered for each pass, and the condition
        that each tuple considered in the pass must satisfy.  
        """

        filters = self.mainStatement._getFilters()
