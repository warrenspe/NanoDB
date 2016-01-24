"""
File containing utilities to parse a grammer, constructing a QueryParser to utilize it.
"""

# Standard imports
import re, collections

# Project imports
import NanoTools.NanoCondition

###
# Grammar Parsing Exceptions
###

class NameException(Exception):
    idx = None
    block = None

    def __init__(self, idx, block):
        self.idx = idx
        self.block = block

    def __str__(self):
        return "Invalid named token\nIndex: %s\n%s" % (self.idx, self.block[self.idx: self.idx + 20])

class UnmatchedException(Exception):
    unmatchedChar = None
    idx = None
    block = None

    def __init__(self, unmatchedChar, idx, block):
        self.unmatchedChar = unmatchedChar
        self.idx = idx
        self.block = block

    def __str__(self):
        return "Unmatched %s\nIndex: %s\n%s" % (self.unmatchedChar, self.idx, self.block)

class MisMatchedBracketException(Exception):
    bracketType = None
    idx = None
    block = None

    def __init__(self, bracketType, idx, block):
        self.bracketType = bracketType
        self.idx = idx
        self.block = block

    def __str__(self):
        return "Mismatched %s\nIndex: %s\n%s" % (self.bracketType, self.idx, self.block[self.idx: self.idx + 20])

###
# Query Parsing Errors
###

class ParsingError(Exception):
    msg = None

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Parser error; %s " % self.msg

# Query parsing functionality
class QueryParser:
    """
    Class which parses a grammer string to create a series of rules which can be used to parse queries.

    Below we will detail the grammar we accept to parse queries and how different tokens will modify the behavior of the
    constructed QueryParser.

    Accepted Grammar:

        ###
        # Tokens
        ###

        "Literal Token" - Must match an input token exactly as written (though case insensitive).
        'Literal Token' - Must match an input token exactly as written (though case insensitive).

        %Regular Expr%  - Matches a token if the regular expression matches it (case insensitive)

        _               - Matches any token as long as it is not a literal string.

        _str_           - Matches any token, as long as it is a literal string (begins/ends with " or ')

        _all_           - Matches any token, including literal strings.

        _!..._          - Matches any token EXCEPT the one passed (case insensitive).  Example: _!from_

        ###
        # Naming, Grouping, & Conditions
        ###

        *name: stops*   - Matches a condition.  Sets the parsed condition on the constructed
                          class using the given name, similar to a Named Match (See below).  The stops parameter should
                          be a list of comma seperated keywords which signify tokens that should not be included in the
                          condition (or in other words, that the condition concludes prior to them).
                          Note that the stop parameters are not required if a condition is to extend to the end of a query.
                          Examples: *where: group, having, limit*
                                    *where: group*
                                    *where:*

        <name: token>   - Named Match. Usage: <attribute-name: token-to-match>.
                          If we do not exist within an attributeDict boundary the matched token will be set on the
                          constructed class using: setattr(class, name, matched-token)
                          If we do exist within an attributeDict boundary, the matched token will appear in the
                          dictionary as key: val being attrName: `matched-token`.  See Attribute Boundaries below.
                          Examples: <colName: _> <innerJoin: "inner">

        (name: ...)     - AttributeDict boundary.  Any named matches made within the brackets will be recorded in a
                          dictionary instead of being set directly on the constructed class. This dictionary will then
                          be set on the class using: setattr(class, name, constructed-dict).
                          When used inside {   } brackets, groups tokens together such that all tokens inside must
                          match, else no match is made.  Note that (...) blocks cannot be nested.

        ###
        # Iterating & Conditionals
        ###

        [...]           - Specifies Zero or one matches of any tokens it wraps.

        {...}           - Specifies Zero or more matches of any tokens / groups it wraps.
                          Note: This quantifier modifies the behaviour of wrapped named matches / named attribute dicts,
                                in that instead of being set on the constructed class directly, they will instead be
                                appended to a list which will be set on the class.
                          Note: Nesting {} blocks is untested / unsupported at the moment.

    Notes:
        * The first token of any query is automatically stripped to determine the type of class to construct.
        * If the final token of a query is a semicolon it is ignored.

    """

    grammarRules = None

    def __init__(self, queryClass):
        """
        Inputs: queryClassInstance - An instance of a QueryType to create a QueryParser for.
        """

        self.grammarRules = _tokenizeGrammar(queryClass.grammar)[0]
        

    def _applyRule(self, rule, idx, queryTokens):
        """
        Attempts to apply this grammarToken to the list of queryTokens, starting at index idx.

        Inputs: rule        - The grammar rule to check if applicable to the current queryTokens.
                idx         - The current index into the list of queryTokens.
                queryTokens - The list of queryTokens we're currently parsing.

        If the rule applies, returns a tuple containing:
            (dictionary mapping named-token-name: parsed-value, idx after applying the rule)
        """

        # If the given index is greater than the length of our queryTokens, we weren't passed enough tokens,
        if idx >= len(queryTokens):
            # Unless we are processing a ZeroOr .. rule
            if isinstance(rule, dict) and rule['type'].startswith('ZeroOr'):
                return dict(), idx
            raise ParsingError("Expecting further tokens in query.")

        # If the given grammar rule is a regular expression, we accept a single token.  Check if it applies
        if isinstance(rule, re._pattern_type):
            if rule.match(queryTokens[idx]):
                return dict(), idx + 1
            # If we are trying to match a literal and we failed, raise a parsing exception
            raise ParsingError("Unexpected token: %s" % queryTokens[idx])

        # If we weren't given a regular expression, we expect that we were given a dictionary
        elif isinstance(rule, dict):
            if rule['type'] == 'NamedToken':
                if rule['tokens'].match(queryTokens[idx]):
                    return {rule['name']: queryTokens[idx]}, idx + 1
                # If we fail to match a named literal, raise a parsing exception
                raise ParsingError("Unexpected token: %s" % queryTokens[idx])

            # Otherwise, if we were given an AttributeDict, handle each token it wraps seperately
            elif rule['type'] == 'AttributeDict':
                retDict = dict()
                for token in rule['tokens']:
                    updateDict, idx = self._applyRule(token, idx, queryTokens)
                    # Update our current dictionary of values and continue
                    retDict.update(updateDict)

                return {rule['name']: retDict}, idx

            # Otherwise, if we were given a condition, construct it from the given query & conditionStops
            elif rule['type'] == 'Condition':
                conditionTokens = []
                while idx < len(queryTokens):
                    # If the current token we're looking at is identified as a token which shouldn't be included
                    # in the condition, break out of our loop & parse what we've gathered thus far
                    if queryTokens[idx] in rule['conditionStops']:
                        break

                    conditionTokens.append(queryTokens[idx])
                    idx += 1

                return {rule['name']: NanoTools.NanoCondition.NanoCondition(conditionTokens)}, idx

            # Otherwise, if we were given a Zero or One expression
            elif rule['type'] == 'ZeroOrOne':
                retDict = dict()
                oldIdx = idx
                for token in rule['tokens']:
                    # Because we can match this rule zero times, catch any parser errors
                    try:
                        updateDict, idx = self._applyRule(token, idx, queryTokens)
                    except ParsingError:
                        return dict(), oldIdx

                    # Otherwise, update our current dictionary of values and continue
                    retDict.update(updateDict)

                return retDict, idx

            # Otherwise if we were given a Zero or Many expression
            elif rule['type'] == 'ZeroOrMany':
                retDict = collections.defaultdict(list)
                # Run until we find a token we can't process
                while True:
                    # Record what our idx was before trying all our rules
                    oldIdx = idx

                    # Find a rule in our tokens list that applies
                    for token in rule['tokens']:
                        # Try to apply this token, if we fail ignore it and try the next
                        try:
                            updateDict, idx = self._applyRule(token, idx, queryTokens)

                        except ParsingError:
                            continue

                        # Because we're processing a Zero or Many expression, join the results into a list
                        for key, val in updateDict.items():
                            retDict[key].append(val)

                    # If our idx hasn't changed after running all the rules, none of them applied
                    if oldIdx == idx:
                        return dict(retDict), idx

            # If we weren't given a dictionary with an understood type key, something has gone wrong.
            raise Exception("Unable to parse malformed rule: %s" % rule)

        # If we weren't given a regular expression or a dictionary, something has gone wrong.
        raise Exception("Error applying unknown rule: %s" % rule)


    def populate(self, queryClassInstance, queryTokens):
        """
        Parses a list of query tokens based on the rules found in self.grammarRules.

        Inputs: queryInstance - An instance of a Query to populate from the given queryTokens.
                queryTokens   - A tokenized form of the query we're running.
        """

        idx = 0

        # Attempt to apply each of our rules to the given list of query tokens
        for rule in self.grammarRules:
            toSet, idx = self._applyRule(rule, idx, queryTokens)

            for key, val in toSet.items():
                setattr(queryClassInstance, key, val)

        # After we're done processing all the rules we have; ensure we are at the end of our input
        if idx < len(queryTokens):
            raise ParsingError("Query is longer than we have rules to process; last token at %s: %s" % (idx, queryTokens[idx]))

        return queryClassInstance


###
# Utility functions
##

# Tokenizing regex
TOKENIZE_RE = re.compile("""("[^"]*"|'[^']*'|[\w.]+|%s|\S)""" % ("|".join(NanoTools.NanoCondition.LOGICAL_OPERATORS)))

# Function to tokenize a query
def tokenizeQuery(query):
    queryTokens = TOKENIZE_RE.findall(query)
    if len(queryTokens) and queryTokens[-1] == ";":
        queryTokens = queryTokens[:-1]
    return queryTokens

def _findNext(char, startIndex, block):
    """
    Finds the next occurrance of char in block appearing after index, startIndex.

    Ignores matches that appear within "", '' or %% blocks

    Raises an exception if unable to find another occurrance.

    Returns the index at which the match was found otherwise.
    """

    i = startIndex

    while i < len(block):
        token = block[i]
        if token == char:
            return i

        elif token in ("'", '"', '%'):
            nextI = block.find(token, i + 1)
            if nextI == -1:
                raise UnmatchedException(token, i, block)
            i = nextI

        i += 1

    raise UnmatchedException(char, max(0, startIndex - 1), block)


def _tokenizeGrammar(grammar, idx=0):
    """
    Tokenizes a given grammar into elements that are easier to parse through.
    """

    rules = []
    # Iterate over each element of the grammar
    while idx < len(grammar):
        token = grammar[idx]

        # If the token is a closing bracket; return.
        if token in ("}", ")", "]"):
            return rules, idx

        # If we've hit a closing bracket for a named match, something's gone wrong, raise an exception
        if token == '>':
            raise UnmatchedException(token, idx, grammar)

        # Handle literal tokens
        if token in ('"', "'"):
            endIdx = _findNext(token, idx + 1, grammar)
            rules.append(re.compile("^%s$" % grammar[idx + 1: endIdx], re.I))

        # Handle regular expressions
        elif token == "%":
            endIdx = _findNext("%", idx + 1, grammar)
            rules.append(re.compile("^%s$" % grammar[idx + 1: endIdx], re.I))

        # Handle catch-all tokens
        elif token == '_':
            # Edge cases, check if this is the beginning of an _all_
            if grammar[idx:idx + 5] == '_all_':
                endIdx = idx + 5
                rules.append(re.compile("""^((".+"|'.+')|([^"']\S*[^'"]|[^"']))$"""))
            # Else if it's the beginning of a _str_
            elif grammar[idx:idx + 5] == '_str_':
                endIdx = idx + 5
                rules.append(re.compile("""^(".+"|'.+')$"""))
            # Else if it's a _!..._
            elif len(grammar) > idx + 1 and grammar[idx + 1] == '!':
                endIdx = grammar.find('_', idx + 1)
                if endIdx == -1:
                    raise UnmatchedException(token, idx, grammar)
                rules.append(re.compile("^(?!%s$).*$""" % grammar[idx + 2: endIdx]))

            # Otherwise it's just a _
            else:
                endIdx = idx
                rules.append(re.compile("""^([^"']\S*[^'"]|[^"'])$"""))

        # Handle conditions
        elif token == "*":
            endIdx = _findNext("*", idx + 1, grammar)
            block = grammar[idx + 1: endIdx]

            if block.find(":") == -1:
                raise NameException(idx, block)

            name, stops = block.split(":", 1)

            # Ensure we have a name, tokens are optional for conditions
            if not name.strip():
                raise NameException(idx, block)

            rules.append({
                'type': 'Condition',
                'name': name.strip(),
                'conditionStops': [stop.strip() for stop in stops.split(',')]
            })

        # Handle named tokens and AttributeDictionaries
        elif token in ("<", "("):
            endIdx = _findNext({"<": ">", "(": ")"}[token], idx + 1, grammar)
            block = grammar[idx + 1: endIdx]

            if block.find(":") == -1:
                raise NameException(idx, block)

            name, tokens = block.split(":", 1)

            # Ensure we have a token and a name
            if not tokens.strip() or not name.strip():
                raise NameException(idx, block)

            tokens = _tokenizeGrammar(tokens.strip())[0]
            # If this is a named token we only accept a single token, not a list; only use the first item
            if token == '<':
                tokens = tokens[0]

            rules.append({
                'type': {'<': 'NamedToken', '(': 'AttributeDict'}[token],
                'name': name.strip(),
                'tokens': tokens
            })

        # Handle Zero or One and Zero or Many blocks
        elif token in ("[", "{"):
            tokens, endIdx = _tokenizeGrammar(grammar, idx + 1)

            # Ensure we returned on the same type of bracket we left on; otherwise raise an exception
            if {"[": "]", "{": "}"}[token] != grammar[endIdx]:
                raise MisMatchedBracketException(token, idx, grammar)

            rules.append({
                'type': {"{": "ZeroOrMany", "[": "ZeroOrOne"}[token],
                'tokens': tokens
            })

        # If this token didn't match anything move on to the next
        else:
            endIdx = idx

        idx = endIdx + 1

    return rules, idx
