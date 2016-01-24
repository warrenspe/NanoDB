#!/usr/bin/python

# Project imports
import NanoTests
import NanoQueries
import NanoQueries._QueryGrammar as QueryGrammar
import NanoTools.NanoCondition as NanoCondition

from NanoQueries._BaseQuery import BaseQuery

class TestTokenizeQuery(NanoTests.NanoTestCase):
    def testTokenize(self):
        # Test regular, expected tokens
        query = "Select name anothername\tyetAThirdName\nAndAnother(Something(else)) and, another"

        self.assertSequenceEqual(
            QueryGrammar.tokenizeQuery(query),
            ("Select", "name", "anothername", "yetAThirdName", "AndAnother", "(", "Something", "(", "else", ")", ")",
             "and", ",", "another")
        )

        # Test condition tokens
        query = "a > < <= >= + - / % * != = ><<=>=+-/%*"

        self.assertSequenceEqual(
            QueryGrammar.tokenizeQuery(query),
            ("a", ">", "<", "<=", ">=", "+", "-", "/", "%", "*", "!=", "=", ">", "<", "<=", ">=", "+", "-", "/", "%", "*")
        )

class TestQueryGrammar(NanoTests.NanoTestCase):
    def setUp(self):
        class Test(BaseQuery):
            grammar = None
        self.Test = Test

    def tearDown(self):
        del self.Test

    def testStringLiteral(self):
        # Test matching a literal defined with apostrophes
        self.Test.grammar = "'test'"
        self.Test("test test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test 'test'")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, 'test "test"')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test test 2")

        # Test matching a literal defined with quotation  marks
        self.Test.queryParser = None
        self.Test.grammar = '"test"'
        self.Test('test test')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test 'test'")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, 'test "test"')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")

        # Test literals defined with alternating apostrophes and quotation marks
        self.Test.queryParser = None
        self.Test.grammar = """ 'test" """
        self.assertRaises(QueryGrammar.UnmatchedException, self.Test, "test")

        self.Test.queryParser = None
        self.Test.grammar = """ "test' """
        self.assertRaises(QueryGrammar.UnmatchedException, self.Test, "test")

    def testObjectRegex(self):
        self.Test.grammar = "_"
        self.Test('test test')
        self.Test('test 2')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test 'test'")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, 'test "test"')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test test 2")

    def testStringRegex(self):
        self.Test.grammar = '_str_'
        self.Test('test "test"')
        self.Test("test '2'")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, 'test test')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, 'test test 2')

    def testAllRegex(self):
        self.Test.grammar = '_all_'
        self.Test('test "test"')
        self.Test("test '2'")
        self.Test("test test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test test 2")

    def testRegex(self):
        self.Test.grammar = "%abc|123%"
        self.Test("test 123")
        self.Test("test abc")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test ab3")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, 'test "123"')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test '123'")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test test 2")

    def testNotRegex(self):
        self.Test.grammar = "_!"
        self.assertRaises(QueryGrammar.UnmatchedException, self.Test, "test")

        self.Test.queryParser = None
        self.Test.grammar = "_!abc"
        self.assertRaises(QueryGrammar.UnmatchedException, self.Test, "test")

        self.Test.queryParser = None
        self.Test.grammar = "_!_"
        self.Test("test test")

        self.Test.queryParser = None
        self.Test.grammar = "_!abc_"
        self.Test("test 123")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test abc")
        

    def testNamedTokens(self):
        # Test a named token accepting a literal string
        self.Test.grammar = "<name: 'literal'>"
        self.assertEqual(self.Test("test literal").name, "literal")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test ab3")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, 'test "123"')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test '123'")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test test 2")

        # Test a named token accepting any non-string token
        self.Test.queryParser = None
        self.Test.grammar = "<name: _>"
        self.assertEqual(self.Test("test token").name, "token")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test test 2")

        # Test a named token accepting a regex
        self.Test.queryParser = None
        self.Test.grammar = "<name: %ReGex%>"
        self.assertEqual(self.Test("test regex").name, "regex")
        self.assertEqual(self.Test("test REGEX").name, "REGEX")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test reg")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test test 2")

        # Test a named token which is missing a token
        self.Test.queryParser = None
        self.Test.grammar = "<name: >"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")

        # Test a named token missing a closing bracket
        self.Test.queryParser = None
        self.Test.grammar = "<name: 'literal'"
        self.assertRaises(QueryGrammar.UnmatchedException, self.Test, "test")

        # Test a named token missing a name
        self.Test.queryParser = None
        self.Test.grammar = "<: 'literal'>"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")

        # Test a named token missing a semicolon
        self.Test.queryParser = None
        self.Test.grammar = "<test 'literal'>"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")

        # Test having multiple named tokens
        self.Test.queryParser = None
        self.Test.grammar = "<name: %ReGex%> <name2: _>"
        self.assertEqual(self.Test('test regex name').name, "regex")
        self.assertEqual(self.Test('test regex name').name2, "name")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test reg 2")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test regex 2 3")

        # Test rogue ending named match brackets
        self.Test.queryParser = None
        self.Test.grammar = '"where" *condition: order*>'
        self.assertRaises(QueryGrammar.UnmatchedException, self.Test, "test")

    def testConditions(self):
        # Test a well-formed condition block with stops
        self.Test.grammar = "'where' *where: limit, order, group*"
        cond = self.Test("test where a < b").where.mainStatement
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '<', 'b'))

        self.Test.queryParser = None
        self.Test.grammar = "'where' *where: limit, order, group* ['group'] ['order'] ['limit']"
        cond = self.Test("test where a < b").where.mainStatement
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '<', 'b'))
        cond = self.Test("test where a < b limit").where.mainStatement
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '<', 'b'))
        cond = self.Test("test where a < b and 1 == 2 limit").where.mainStatement
        leftCond = cond.statements[0]
        rightCond = cond.statements[1]
        self.assertIsInstance(cond, NanoCondition.AndStatement)
        self.assertSequenceEqual((leftCond.left[0], leftCond.opr, leftCond.right[0]), ('a', '<', 'b'))
        self.assertSequenceEqual((rightCond.left[0], rightCond.opr, rightCond.right[0]), ('1', '==', '2'))

        # Test a condition block without stops
        self.Test.queryParser = None
        self.Test.grammar = "*name:*"
        cond = self.Test("test a == 1").name.mainStatement
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '1'))

        # Test a malformed condition block without a name
        self.Test.queryParser = None
        self.Test.grammar = "*a, b, c*"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")
        self.Test.queryParser = None
        self.Test.grammar = "*:a, b, c*"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")
        self.Test.queryParser = None
        self.Test.grammar = "**"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")
        self.Test.queryParser = None
        self.Test.grammar = "*:*"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")


    def testAttributeDicts(self):
        # Test an attribute dict with multiple named components
        self.Test.grammar = "(dname: <name: 'literal'> 'unnamedtoken' <name2: _> <name3: %regex%>)"
        t = self.Test("test literal unnamedtoken token regEx")
        self.assertDictContainsSubset(t.dname, {'name': 'literal', 'name2': 'token', 'name3': 'regEx'})
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal unnamedtoken")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal unnamedtoken t")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal unnamedtoken t rege")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal unnamedtoken t regex 2")

        # Test an attribute dict with a ZeroOrOne block nested within it
        self.Test.queryParser = None
        self.Test.grammar = "(dname: <name: 'literal'> [<name2: 'token'>], <name3: '3'>)"
        t = self.Test("test literal token 3")
        self.assertDictContainsSubset(t.dname, {'name': 'literal', 'name2': 'token', 'name3': '3'})
        t = self.Test("test literal 3")
        self.assertDictContainsSubset(t.dname, {'name': 'literal', 'name3': '3'})
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal unnamedtoken t")

        # Test an attribute dict with no named components in it
        self.Test.queryParser = None
        self.Test.grammar = "(dname: 'literal1' 'literal2')"
        t = self.Test("test literal1 literal2")
        self.assertDictContainsSubset(t.dname, {})
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal1")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal1 literal2 literal3")

        # Test an attribute dict with no components
        self.Test.queryParser = None
        self.Test.grammar = "(dname: )"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")

        # Test an attribute dict with no name
        self.Test.queryParser = None
        self.Test.grammar = "(: 'literal')"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")

        # Test an attribute dict with no semicolon
        self.Test.queryParser = None
        self.Test.grammar = "(: 'literal')"
        self.assertRaises(QueryGrammar.NameException, self.Test, "test")

        # Test an attribute dict with no closing bracket
        self.Test.queryParser = None
        self.Test.grammar = "(dname: <name: 'literal'>"
        self.assertRaises(QueryGrammar.UnmatchedException, self.Test, "test")

    def testZeroOrOne(self):
        # Test a simple ZeroOrOne query
        self.Test.grammar = "'literal' [<cond1: 'if'>] 'literal2' ['if' <cond2: 'exists'>] 'literal3']"
        self.assertDictContainsSubset(self.Test("test literal if literal2 if exists literal3").__dict__,
                                      {'cond1': 'if', 'cond2': 'exists'})
        self.assertDictContainsSubset(self.Test("test literal literal2 if exists literal3").__dict__,
                                      {'cond2': 'exists'}) 
        self.assertDictContainsSubset(self.Test("test literal literal2 literal3").__dict__, {})
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test literal if literal2 exists")

        # Test a query which is solely a ZeroOrOne block
        self.Test.queryParser = None
        self.Test.grammar = "['test']"
        self.Test("test test")
        self.Test("test")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test a")

        # Test nested [] blocks
        self.Test.queryParser = None
        self.Test.grammar = "['test' ['if' 'exists'] <end: _>]"
        self.assertEqual(self.Test("test test if exists test").end, 'test')
        self.assertEqual(self.Test("test test token").end, 'token')
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test if exists")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test a")

        # Test [()]
        self.Test.queryParser = None
        self.Test.grammar = "[(dname: 'test' <name: _> <name2: 'a'>) 'q']"
        self.assertDictContainsSubset(self.Test("test test token a q").__dict__,
                                      {'dname': {'name': 'token', 'name2': 'a'}})
        self.assertDictContainsSubset(self.Test("test").__dict__, {})
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test q")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test tok a")

        # Test ending condition
        self.Test.queryParser = None
        self.Test.grammar = "<a: 'a'> <b: 'b'> <c: _> ['test']"
        self.assertDictContainsSubset(self.Test("test a b c test").__dict__, {'a': 'a', 'b': 'b', 'c': 'c'})
        self.assertDictContainsSubset(self.Test("test a b c").__dict__, {'a': 'a', 'b': 'b', 'c': 'c'})

        # Test beginning condition
        self.Test.queryParser = None
        self.Test.grammar = "['test'] <a: 'a'> <b: 'b'> <c: _>"
        self.assertDictContainsSubset(self.Test("test test a b c").__dict__, {'a': 'a', 'b': 'b', 'c': 'c'})
        self.assertDictContainsSubset(self.Test("test a b c").__dict__, {'a': 'a', 'b': 'b', 'c': 'c'})

        # Test mismatching two nested () and [] blocks
        self.Test.queryParser = None
        self.Test.grammar = "['test' ('test2' 'test3'] 'test4']"
        self.assertRaises(QueryGrammar.UnmatchedException, self.Test, "test")

    def testZeroOrMany(self):
        # Test a few simple ZeroOrMany queries
        self.Test.grammar = "{<name: _>}"
        self.assertSequenceEqual(self.Test("test a b c").name, ["a", "b", "c"])

        self.Test.queryParser = None
        self.Test.grammar = "{<name: _str_> _}"
        self.assertSequenceEqual(self.Test("""test a 'b' c "d" 'e' f""").name, ["'b'", '"d"', "'e'"])

        # Test a ZeroOrMany query containing ()'s
        self.Test.queryParser = None
        self.Test.grammar = "{(dname: <n1: '1'> <n2: '2'> '3' <n4: '4'>) '5'}"
        t = self.Test("test 1 2 3 4 5")
        self.assertDictContainsSubset(t.dname[0], {'n1': '1', 'n2': '2', 'n4': '4'})
        t = self.assertRaises(QueryGrammar.ParsingError, self.Test, "test 1 2 5 3 4")

        self.Test.queryParser = None
        self.Test.grammar = "{(dname: <n1: '1'> <n2: '2'>) (dname2: '3' <n4: '4'>) '5'}"
        t = self.Test("test 1 2 5 3 4 5 1 2 5")
        self.assertDictContainsSubset(t.dname[0], {'n1': '1', 'n2': '2'})
        self.assertDictContainsSubset(t.dname[1], {'n1': '1', 'n2': '2'})
        self.assertDictContainsSubset(t.dname2[0], {'n4': '4'})
        t = self.assertRaises(QueryGrammar.ParsingError, self.Test, "test 1 5 2 3 5 4")

        # Test a ZeroOrMany query containing []'s
        self.Test.queryParser = None
        self.Test.grammar = "{['5' <a: '6'>] ['6']}"
        t = self.Test("test 5 6 6 5 6")
        self.assertSequenceEqual(t.a, ['6', '6'])
        t = self.assertRaises(QueryGrammar.ParsingError, self.Test, "test 5")

        # Test a ZeroOrmany query containing []'s and ()'s
        self.Test.queryParser = None
        self.Test.grammar = "{['5', '7' <opt: '6'>] (nonopt: '5', <name: '7'>)}"
        t = self.Test("test 5 7 5 7 6")
        self.assertSequenceEqual(t.opt, ['6'])
        self.assertSequenceEqual(t.nonopt, [{'name': '7'}])

        # Test a mismatched ZeroOrMany query
        self.Test.queryParser = None
        self.Test.grammar = "{'5' ['4'}]"
        self.assertRaises(QueryGrammar.MisMatchedBracketException, self.Test, "test")

        # Test a query beginning with a ZeroOrMany
        self.Test.queryParser = None
        self.Test.grammar = "{'5' '6'} '1' '2' '3'"
        self.Test("test 5 6 5 1 2 3")
        self.Test("test 1 2 3")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test 5 1 6")

        # Test a query ending with a ZeroOrMany
        self.Test.queryParser = None
        self.Test.grammar = "'1' '2' '3' {'5' '6'}"
        self.Test("test 1 2 3 5 6 5")
        self.Test("test 1 2 3")
        self.assertRaises(QueryGrammar.ParsingError, self.Test, "test 5 6")

        # Test a complex grammar
        self.Test.queryParser = None
        self.Test.grammar = """
                            "tok"
                            _
                            _str_
                            _all_
                            %ReGeX%
                            <name: _>
                            <name2: _str_>
                            <name3: _all_>
                            <name4: %ReGeX%>
                            <name5: "tok5">
                            (dict1: "tok" <dname1: %ReGeX%> <dname2: "tok">)
                            ["tokenz" %regexz% _ <name6: "name6">]
                            {
                             "tok"
                             <listname1: "a">
                             (listname2: <a: _> <b: "b">)
                             (listname3: "1" "2" "3" <c: _>)
                             ["w" <d: _>]
                            }
                            <name7: _>
                            ["1"]
                            <name8: _all_>
                            """

        # Ensure well-formed queries don't raise errors & parse correctly
        q = """test tok tok 'tok' "tok" regeX someName 'someName2' someName3 regex tok5 tok regex tok tokenz regexz
               sometoken name6 tok a a2 b 1 2 3 c w d name7 1 name8"""
        t = self.Test(q)
        self.assertDictContainsSubset(t.__dict__, {
            'name': 'someName',
            'name2': "'someName2'",
            'name3': 'someName3',
            'name4': 'regex',
            'name5': 'tok5',
            'dict1': {'dname1': 'regex', 'dname2': 'tok'},
            'name6': 'name6',
            'listname1': ['a'],
            'listname2': [{'a': 'a2', 'b': 'b'}],
            'listname3': [{'c': 'c'}],
            'd': ['d'],
            'name7': 'name7',
            'name8': 'name8'
        })

        q = """test tok tok 'tok' tok regex name 'name2' name3 regex tok5 tok regex tok w someD a name7 'name8'"""
        t = self.Test(q)
        self.assertDictContainsSubset(t.__dict__, {
            'name': 'name',
            'name2': "'name2'",
            'name3': 'name3',
            'name4': 'regex',
            'name5': 'tok5',
            'dict1': {'dname1': 'regex', 'dname2': 'tok'},
            'listname1': ['a'],
            'd': ['someD'],
            'name7': 'name7',
            'name8': "'name8'"
        })


class TestNanoQueryParsing(NanoTests.NanoTestCase): # TODO test executing for each

    def testAlter(self):
        q = """Alter table Name
               add cOlUmn colName int4
               remove column otherName
               remove column othername2
               modify Column colName1 colName2 int8
               add index name
               add index name2
               remove Index col1
               remove Index col2"""
        a = NanoQueries.Alter(q)

        self.assertEqual(a.name, "Name")
        self.assertSequenceEqual(a.addColumns, ({'name': 'colName', 'type': 'int4'},))
        self.assertSequenceEqual(a.removeColumns, ({'name': 'otherName'}, {'name': 'othername2'}))
        self.assertSequenceEqual(a.modifyColumns, ({'name': 'colName1', 'newName': 'colName2', 'newType': 'int8'},))
        self.assertSequenceEqual(a.addIndex, ['name', 'name2'])
        self.assertSequenceEqual(a.removeIndex, ['col1', 'col2'])

        q = """Alter table Name
               add cOlUmn colName int4
               remove column otherName
               remove column othername2
               modify Column colName1 colName2 int8"""
        a = NanoQueries.Alter(q)

        self.assertEqual(a.name, "Name")
        self.assertSequenceEqual(a.addColumns, ({'name': 'colName', 'type': 'int4'},))
        self.assertSequenceEqual(a.removeColumns, ({'name': 'otherName'}, {'name': 'othername2'}))
        self.assertSequenceEqual(a.modifyColumns, ({'name': 'colName1', 'newName': 'colName2', 'newType': 'int8'},))
        self.assertIsNone(a.addIndex)
        self.assertIsNone(a.removeIndex)

        q = "alter table name"
        a = NanoQueries.Alter(q)
        self.assertEqual(a.name, 'name')
        self.assertIsNone(a.addColumns)
        self.assertIsNone(a.removeColumns)
        self.assertIsNone(a.modifyColumns)
        self.assertIsNone(a.addIndex)
        self.assertIsNone(a.removeIndex)

    def testCreate(self):
        q = """Create database testing"""
        a = NanoQueries.Create(q)

        self.assertEqual(a.target, 'database')
        self.assertEqual(a.name, 'testing')
        self.assertIsNone(a.cols)
        self.assertIsNone(a.indices)

# TODO update testing of execute
#        self.assertFalse(NanoFileIO.checkDatabaseExists("testing"))
#        self.conn.execute(q)
#        self.assertTrue(NanoFileIO.checkDatabaseExists("testing"))
#        NanoFileIO.deleteDatabase('testing')
#
        q = """Create table testTable
               colName1 int4
               index colName1
               colName2 char15
               index  colName2"""
        a = NanoQueries.Create(q)

        self.assertEqual(a.target, "table")
        self.assertEqual(a.name, "testTable")
        self.assertSequenceEqual(a.cols, ({'name': 'colName1', 'type': 'int4'},
                                          {'name':'colName2', 'type': 'char15'}))
        self.assertSequenceEqual(a.indices, ['colName1', 'colName2'])

# TODO update testing of execute
#        self.assertFalse(NanoFileIO.checkTableExists(self.dbName, "testTable"))
#        self.conn.execute(q)
#        config = self.conn.getCursor("testTable").config
#        self.assertTrue(NanoFileIO.checkTableExists(self.dbName, "testTable"))
#        self.assertTrue(NanoFileIO.checkConfigExists(self.dbName, "testTable"))
#        self.assertEqual(config.name, "testTable")
#        self.assertSequenceEqual(config.cols.keys(), ["colName1", "colName2"])
#        self.assertIsInstance(config.cols.values()[0], NanoTypes.Int)
#        self.assertIsInstance(config.cols.values()[1], NanoTypes.Char)
#        self.assertItemsEqual(config.indices.items(), [("colName1", "idx1"), ("colName2", "idx2")])

    def testDrop(self): # TODO test execute
        q = """Drop table testing"""
        a = NanoQueries.Drop(q)

        self.assertEqual(a.target, 'table')
        self.assertIsNone(a.ifExists)
        self.assertEqual(a.name, 'testing')

# TODO update testing of execute
#        self.assertFalse(NanoFileIO.checkTableExists(self.dbName, "testing"))
#        self.assertFalse(NanoFileIO.checkConfigExists(self.dbName, "testing"))
#        NanoFileIO.makeTable(self.dbName, "testing")
#        self.assertTrue(NanoFileIO.checkTableExists(self.dbName, "testing"))
#        self.assertTrue(NanoFileIO.checkConfigExists(self.dbName, "testing"))
#
#        self.conn.execute(q)
#        self.assertFalse(NanoFileIO.checkTableExists(self.dbName, "testing"))
#        self.assertFalse(NanoFileIO.checkConfigExists(self.dbName, "testing"))

        q = """Drop database if exists db"""
        a = NanoQueries.Drop(q)

        self.assertEqual(a.target, 'database')
        self.assertEqual(a.ifExists, 'exists')
        self.assertEqual(a.name, 'db')

# TODO udpate testing of execute
#        self.assertFalse(NanoFileIO.checkDatabaseExists("db"))
#        NanoFileIO.makeDatabase("db")
#        NanoFileIO.makeTable("db", "testTable")
#        self.conn.execute(q)
#        self.assertFalse(NanoFileIO.checkDatabaseExists("db"))


    def testRename(self): # TODO test execute
        q = """Rename table db to db2"""
        a = NanoQueries.Rename(q)

        self.assertEqual(a.target, 'table')
        self.assertEqual(a.oldName, 'db')
        self.assertEqual(a.newName, 'db2')

        q = """Rename database db to db2"""
        a = NanoQueries.Rename(q)

        self.assertEqual(a.target, 'database')
        self.assertEqual(a.oldName, 'db')
        self.assertEqual(a.newName, 'db2')

    def testTruncate(self): # TODO test execute
        q = """truncate table test"""
        a = NanoQueries.Truncate(q)

        self.assertEqual(a.name, 'test')

    def testDelete(self): # TODO test execute
        q = """delete from test"""
        a = NanoQueries.Delete(q)

        self.assertEqual(a.name, 'test')
        self.assertIsNone(a.condition)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """delete from test order by test2 asc"""
        a = NanoQueries.Delete(q)

        self.assertEqual(a.name, 'test')
        self.assertIsNone(a.condition)
        self.assertEqual(a.orderBy, 'test2')
        self.assertEqual(a.orderByDir, 'asc')
        self.assertIsNone(a.limit)

        q = """delete from test limit 5"""
        a = NanoQueries.Delete(q)

        self.assertEqual(a.name, 'test')
        self.assertIsNone(a.condition)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertEqual(a.limit, '5')

        q = """Delete from test where a == 5"""
        a = NanoQueries.Delete(q)

        self.assertEqual(a.name, 'test')
        cond = a.condition.mainStatement
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '5'))
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """Delete from test where a >= 7 order by testing desc"""
        a = NanoQueries.Delete(q)

        self.assertEqual(a.name, 'test')
        cond = a.condition.mainStatement
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '>=', '7'))
        self.assertEqual(a.orderBy, 'testing')
        self.assertEqual(a.orderByDir, 'desc')
        self.assertIsNone(a.limit)

        q = """Delete from test where a >= 7 limit 5"""
        a = NanoQueries.Delete(q)

        self.assertEqual(a.name, 'test')
        cond = a.condition.mainStatement
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '>=', '7'))
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertEqual(a.limit, '5')

        q = """Delete from test order by testing asc limit 5"""
        a = NanoQueries.Delete(q)

        self.assertEqual(a.name, 'test')
        self.assertIsNone(a.condition)
        self.assertEqual(a.orderBy, 'testing')
        self.assertEqual(a.orderByDir, 'asc')
        self.assertEqual(a.limit, '5')

    def testInsert(self): # TODO test execute
        q = """Insert into testing values 1 2 "val" 4 5"""
        a = NanoQueries.Insert(q)

        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.vals, ('1', '2', '"val"', '4', '5'))


    def testSelect(self): # TODO test execute
        q = """Select distinct val from testing"""
        a = NanoQueries.Select(q)

        self.assertEqual(a.distinct, "distinct")
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val'])
        self.assertIsNone(a.innerJoins)
        self.assertIsNone(a.leftJoins)
        self.assertIsNone(a.where)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """Select val1 val2 from testing where a == 6"""
        a = NanoQueries.Select(q)
        cond = a.where.mainStatement

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertIsNone(a.leftJoins)
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '6'))
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """Select distinct "val" val2 from testing order by testCol asc"""
        a = NanoQueries.Select(q)

        self.assertEqual(a.distinct, "distinct")
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['"val"', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertIsNone(a.leftJoins)
        self.assertIsNone(a.where)
        self.assertEqual(a.orderBy, "testCol")
        self.assertEqual(a.orderByDir, "asc")
        self.assertIsNone(a.limit)

        q = """Select val "valYOU" val6 from testing limit 17"""
        a = NanoQueries.Select(q)

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val', '"valYOU"', 'val6'])
        self.assertIsNone(a.innerJoins)
        self.assertIsNone(a.leftJoins)
        self.assertIsNone(a.where)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertEqual(a.limit, "17")

        q = """Select val1 val2 from testing where a == 5 order by testCol desc"""
        a = NanoQueries.Select(q)
        cond = a.where.mainStatement

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertIsNone(a.leftJoins)
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '5'))
        self.assertEqual(a.orderBy, 'testCol')
        self.assertEqual(a.orderByDir, 'desc')
        self.assertIsNone(a.limit)

        q = """Select val1 val2 from testing where a == 5 limit 6"""
        a = NanoQueries.Select(q)
        cond = a.where.mainStatement

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertIsNone(a.leftJoins)
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '5'))
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertEqual(a.limit, '6')

        q = """Select val1 val2 from testing order by testttt desc limit 4"""
        a = NanoQueries.Select(q)

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertIsNone(a.leftJoins)
        self.assertIsNone(a.where)
        self.assertEqual(a.orderBy, 'testttt')
        self.assertEqual(a.orderByDir, 'desc')
        self.assertEqual(a.limit, '4')

        q = """Select val1 val2 from testing inner join someTab on someTab.test == val1"""
        a = NanoQueries.Select(q)

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertEqual(len(a.innerJoins), 1)
        self.assertEqual(a.innerJoins[0]['name'], 'someTab')
        joinCond = a.innerJoins[0]['condition'].mainStatement
        self.assertSequenceEqual((joinCond.left[0], joinCond.opr, joinCond.right[0]), ('someTab.test', '==', 'val1'))
        self.assertIsNone(a.leftJoins)
        self.assertIsNone(a.where)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """Select val1 val2 from testing left join someTab on someTab.test == val1"""
        a = NanoQueries.Select(q)

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertEqual(len(a.leftJoins), 1)
        self.assertEqual(a.leftJoins[0]['name'], 'someTab')
        joinCond = a.leftJoins[0]['condition'].mainStatement
        self.assertSequenceEqual((joinCond.left[0], joinCond.opr, joinCond.right[0]), ('someTab.test', '==', 'val1'))
        self.assertIsNone(a.where)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """Select val1 val2
               from testing
               left join someTab on someTab.test == val1
               inner join someTable2 on someTable2.test==val7
               inner join someTable3 on 'foo'=='bar'"""
        a = NanoQueries.Select(q)

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertEqual(len(a.innerJoins), 2)
        self.assertEqual(len(a.leftJoins), 1)
        leftJoin = a.leftJoins[0]['condition'].mainStatement
        innerJoin1 = a.innerJoins[0]['condition'].mainStatement
        innerJoin2 = a.innerJoins[1]['condition'].mainStatement
        self.assertEqual(a.leftJoins[0]['name'], 'someTab')
        self.assertEqual(a.innerJoins[0]['name'], 'someTable2')
        self.assertEqual(a.innerJoins[1]['name'], 'someTable3')
        self.assertSequenceEqual((leftJoin.left[0], leftJoin.opr, leftJoin.right[0]), ('someTab.test', '==', 'val1'))
        self.assertSequenceEqual((innerJoin1.left[0], innerJoin1.opr, innerJoin1.right[0]), ('someTable2.test', '==', 'val7'))
        self.assertSequenceEqual((innerJoin2.left[0], innerJoin2.opr, innerJoin2.right[0]), ("'foo'", '==', "'bar'"))
        self.assertIsNone(a.where)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """Select val1 val2 from testing inner join someTab on "tab"==tab where a == 6"""
        a = NanoQueries.Select(q)
        cond = a.where.mainStatement

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        innerJoin = a.innerJoins[0]['condition'].mainStatement
        self.assertEqual(len(a.innerJoins), 1)
        self.assertEqual(a.innerJoins[0]['name'], "someTab")
        self.assertSequenceEqual((innerJoin.left[0], innerJoin.opr, innerJoin.right[0]), ('"tab"', '==', 'tab'))
        self.assertIsNone(a.leftJoins)
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '6'))
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """Select distinct "val" val2 from testing left join someTab on "tab"==tab order by testCol asc"""
        a = NanoQueries.Select(q)

        self.assertEqual(a.distinct, "distinct")
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['"val"', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertEqual(len(a.leftJoins), 1)
        self.assertEqual(a.leftJoins[0]['name'], "someTab")
        leftJoin = a.leftJoins[0]['condition'].mainStatement
        self.assertSequenceEqual((leftJoin.left[0], leftJoin.opr, leftJoin.right[0]), ('"tab"', '==', 'tab'))
        self.assertIsNone(a.where)
        self.assertEqual(a.orderBy, "testCol")
        self.assertEqual(a.orderByDir, "asc")
        self.assertIsNone(a.limit)

        q = """Select val "valYOU" val6 from testing left join someTab on "tab"==tab limit 17"""
        a = NanoQueries.Select(q)

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val', '"valYOU"', 'val6'])
        self.assertIsNone(a.innerJoins)
        self.assertEqual(len(a.leftJoins), 1)
        self.assertEqual(a.leftJoins[0]['name'], "someTab")
        leftJoin = a.leftJoins[0]['condition'].mainStatement
        self.assertSequenceEqual((leftJoin.left[0], leftJoin.opr, leftJoin.right[0]), ('"tab"', '==', 'tab'))
        self.assertIsNone(a.where)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertEqual(a.limit, "17")

        q = """Select val1 val2 from testing left join someTab on "tab"==tab where a == 5 order by testCol desc"""
        a = NanoQueries.Select(q)
        cond = a.where.mainStatement

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertEqual(len(a.leftJoins), 1)
        self.assertEqual(a.leftJoins[0]['name'], "someTab")
        leftJoin = a.leftJoins[0]['condition'].mainStatement
        self.assertSequenceEqual((leftJoin.left[0], leftJoin.opr, leftJoin.right[0]), ('"tab"', '==', 'tab'))
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '5'))
        self.assertEqual(a.orderBy, 'testCol')
        self.assertEqual(a.orderByDir, 'desc')
        self.assertIsNone(a.limit)

        q = """Select val1 val2 from testing left join someTab on "tab"==tab where a== 5 limit 6"""
        a = NanoQueries.Select(q)
        cond = a.where.mainStatement

        self.assertIsNone(a.distinct)
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertEqual(len(a.leftJoins), 1)
        self.assertEqual(a.leftJoins[0]['name'], "someTab")
        leftJoin = a.leftJoins[0]['condition'].mainStatement
        self.assertSequenceEqual((leftJoin.left[0], leftJoin.opr, leftJoin.right[0]), ('"tab"', '==', 'tab'))
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '5'))
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertEqual(a.limit, '6')

        q = """Select val1 val2 from testing left join someTab on "tab"==tab order by testttt desc limit 4"""
        a = NanoQueries.Select(q)

        self.assertIsNone(a.distinct) # TODO convert these to isNones everywhere
        self.assertEqual(a.name, "testing")
        self.assertSequenceEqual(a.attrs, ['val1', 'val2'])
        self.assertIsNone(a.innerJoins)
        self.assertEqual(len(a.leftJoins), 1)
        self.assertEqual(a.leftJoins[0]['name'], "someTab")
        leftJoin = a.leftJoins[0]['condition'].mainStatement
        self.assertSequenceEqual((leftJoin.left[0], leftJoin.opr, leftJoin.right[0]), ('"tab"', '==', 'tab'))
        self.assertIsNone(a.where)
        self.assertEqual(a.orderBy, 'testttt')
        self.assertEqual(a.orderByDir, 'desc')
        self.assertEqual(a.limit, '4')

    def testUpdate(self): # TODO test execute
        q = """update test set a = 4"""
        a = NanoQueries.Update(q)

        self.assertEqual(a.name, 'test')
        self.assertSequenceEqual(a.colSets, ({'name': 'a', 'val': '4'},))
        self.assertIsNone(a.where)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """update test set a = 4 b = 7 order by test2 asc"""
        a = NanoQueries.Update(q)

        self.assertEqual(a.name, 'test')
        self.assertSequenceEqual(a.colSets, ({'name': 'a', 'val': '4'}, {'name': 'b', 'val': '7'}))
        self.assertIsNone(a.where)
        self.assertEqual(a.orderBy, 'test2')
        self.assertEqual(a.orderByDir, 'asc')
        self.assertIsNone(a.limit)

        q = """update test set a = "1g8" limit 5"""
        a = NanoQueries.Update(q)

        self.assertEqual(a.name, 'test')
        self.assertSequenceEqual(a.colSets, ({'name': 'a', 'val': '"1g8"'},))
        self.assertIsNone(a.where)
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertEqual(a.limit, '5')

        q = """update test set a = 4 where a == 5"""
        a = NanoQueries.Update(q)
        cond = a.where.mainStatement

        self.assertEqual(a.name, 'test')
        self.assertSequenceEqual(a.colSets, ({'name': 'a', 'val': '4'},))
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '==', '5'))
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertIsNone(a.limit)

        q = """Update test set a = 4 where a >= 7 order by testing desc"""
        a = NanoQueries.Update(q)
        cond = a.where.mainStatement

        self.assertEqual(a.name, 'test')
        self.assertSequenceEqual(a.colSets, ({'name': 'a', 'val': '4'},))
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '>=', '7'))
        self.assertEqual(a.orderBy, 'testing')
        self.assertEqual(a.orderByDir, 'desc')
        self.assertIsNone(a.limit)

        q = """update test set a=4 where a >= 7 limit 5"""
        a = NanoQueries.Update(q)
        cond = a.where.mainStatement

        self.assertEqual(a.name, 'test')
        self.assertSequenceEqual(a.colSets, ({'name': 'a', 'val': '4'},))
        self.assertSequenceEqual((cond.left[0], cond.opr, cond.right[0]), ('a', '>=', '7'))
        self.assertIsNone(a.orderBy)
        self.assertIsNone(a.orderByDir)
        self.assertEqual(a.limit, '5')

        q = """Update test set a= 4 order by testing asc limit 5"""
        a = NanoQueries.Update(q)

        self.assertEqual(a.name, 'test')
        self.assertSequenceEqual(a.colSets, ({'name': 'a', 'val': '4'},))
        self.assertIsNone(a.where)
        self.assertEqual(a.orderBy, 'testing')
        self.assertEqual(a.orderByDir, 'asc')
        self.assertEqual(a.limit, '5')

    def testUse(self): # TODO test execute
        q = """Use test"""
        a = NanoQueries.Use(q)

        self.assertEqual(a.name, 'test')

    def testDescribe(self): # TODO test execute
        q = """Describe table testTable"""
        a = NanoQueries.Describe(q)

        self.assertEqual(a.name, "testTable")

    def testShow(self): # TODO test execute
        q = "SHOW tables"
        a = NanoQueries.Show(q)

        self.assertIsNone(a.like)
        self.assertIsNone(a.inDB)

        q = "Show tables in testDatabase"
        a = NanoQueries.Show(q)

        self.assertIsNone(a.like)
        self.assertEqual(a.inDB, "testDatabase")

        q = 'Show Tables like "testing"'
        a = NanoQueries.Show(q)

        self.assertEqual(a.like, '"testing"')
        self.assertIsNone(a.inDB)

        q = 'show tables IN testDatabase like "test"'
        a = NanoQueries.Show(q)

        self.assertEqual(a.like, '"test"')
        self.assertEqual(a.inDB, "testDatabase")

        q = 'show tables like "test" in testDatabase'
        self.assertRaises(Exception, NanoQueries.Show, q)

        q = 'show tables like "test" like "test"'
        self.assertRaises(Exception, NanoQueries.Show, q)

        q = 'show tables in testDB in testDB'
        self.assertRaises(Exception, NanoQueries.Show, q)
