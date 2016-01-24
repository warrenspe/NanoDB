# Standard imports
import traceback

# Project imports
import NanoTools
import NanoBlocks
import NanoIO.File
import NanoTools.NanoCondition as NanoCondition
import NanoConfig
import NanoTests
import NanoTypes
import NanoQueries

class TestNanoCondition(NanoTests.NanoTestCase):

    def assertStatement(self, statement, left, opr=None, right=None):
        self.assertIsInstance(statement, NanoCondition.Statement)
        if statement.left is None:
            self.assertIsNone(left)
        else:
            self.assertSequenceEqual(statement.left, (left if hasattr(left, '__iter__') else [left]))
        if statement.right is None:
            self.assertIsNone(right)
        else:
            self.assertSequenceEqual(statement.right, (right if hasattr(right, '__iter__') else [right]))
        self.assertEqual(statement.opr, opr)

    def testParsing(self):
        # Ensure malformed conditions raise exceptions
        malformedQueries = (
            "(",
            ")",
            "(a",
            "a)",
            "((",
            "))",
            ">a",
            "a<",
            "a > (",
            "a < (a",
            "a < )",
            "a > a)",
            "((a > )",
            "a > or",
            "a or",
            "or a",
            "> or a",
            "> or",
            "a and b or c",
            "a +",
            "+",
            "(a +",
            "a or b < c and c",
            "a and a and b or c",
            "",
        )
        # (Not using assertRaises here because we want access to the query that blew up)
        for q in malformedQueries:
            try:
                NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q))
            except NanoCondition.ConditionParsingException:
                continue
            except Exception:
                raise Exception("%s\n^ raised while processing '%s'" % (traceback.format_exc(), q))
            raise AssertionError("Parsing error not raised: %s" % q)

        # Test well-formed conditions
        q = "a"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, 'a')

        q = "1"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, '1')

        q = "'a'"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, "'a'")

        q = "a or b"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.OrStatement)
        self.assertStatement(cond.statements[0], 'a')
        self.assertStatement(cond.statements[1], 'b')

        q = "1 or 2"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.OrStatement)
        self.assertStatement(cond.statements[0], '1')
        self.assertStatement(cond.statements[1], '2')

        q = "a and b"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.AndStatement)
        self.assertStatement(cond.statements[0], 'a')
        self.assertStatement(cond.statements[1], 'b')

        q = "1 and not 2"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.AndStatement)
        self.assertIsInstance(cond.statements[1], NanoCondition.NegateStatement)
        self.assertStatement(cond.statements[0], '1')
        self.assertStatement(cond.statements[1].statement, '2')

        q = "(a)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['a'])

        q = "(a + 2)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['a', '+', '2'])

        q = "not 2 + 2"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.NegateStatement)
        self.assertStatement(cond.statement, ['2', '+', '2'])

        q = "((2))"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['2'])

        q = "((2) + '2')"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['(', '2', ')', '+', "'2'"])

        q = "2 + (2)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['2', '+', '(', '2', ')'])

        q = "2 + (2+2)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['2', '+', '(', '2', '+', '2', ')'])

        q = "( 2 + 2 ) + 2"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['(', '2', '+', '2', ')', '+', '2'])

        q = "2 and 0 and (5 or 6)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.AndStatement)
        self.assertStatement(cond.statements[0], '2')
        self.assertStatement(cond.statements[1], '0')
        self.assertIsInstance(cond.statements[2], NanoCondition.OrStatement)
        self.assertStatement(cond.statements[2].statements[0], '5')
        self.assertStatement(cond.statements[2].statements[1], '6')

        q = "a and b and c and not (3 or 4) and d"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.AndStatement)
        self.assertStatement(cond.statements[0], 'a')
        self.assertStatement(cond.statements[1], 'b')
        self.assertStatement(cond.statements[2], 'c')
        self.assertIsInstance(cond.statements[3], NanoCondition.NegateStatement)
        self.assertIsInstance(cond.statements[3].statement, NanoCondition.OrStatement)
        self.assertStatement(cond.statements[3].statement.statements[0], '3')
        self.assertStatement(cond.statements[3].statement.statements[1], '4')
        self.assertStatement(cond.statements[4], 'd')

        q = "a < 5"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, 'a', '<', '5')

        q = "(a < 5)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, 'a', '<', '5')

        q = "a + 2 <= b + 5"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['a', '+', '2'], '<=', ['b', '+', '5'])

        q = "(a + 2) != (a + a)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertStatement(cond, ['(', 'a', '+', '2', ')'], '!=', ['(', 'a', '+', 'a', ')'])

        q = "a < 5 and b > 2"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.AndStatement)
        self.assertStatement(cond.statements[0], 'a', '<', '5')
        self.assertStatement(cond.statements[1], 'b', '>', '2')

        q = "a == a or (b == 1)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.OrStatement)
        self.assertStatement(cond.statements[0], 'a', '==', 'a')
        self.assertStatement(cond.statements[1], 'b', '==', '1')

        q = "(a) or a < 5"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.OrStatement)
        self.assertStatement(cond.statements[0], 'a')
        self.assertStatement(cond.statements[1], 'a', '<', '5')

        q = "(a < 5) or (b < 6 and c >= 7) or (1 + 2 < 4 + 5)"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.OrStatement)
        self.assertStatement(cond.statements[0], 'a', '<', '5')
        self.assertIsInstance(cond.statements[1], NanoCondition.AndStatement)
        self.assertStatement(cond.statements[1].statements[0], 'b', '<', '6')
        self.assertStatement(cond.statements[1].statements[1], 'c', '>=', '7')
        self.assertStatement(cond.statements[2], ['1', '+', '2'], '<', ['4', '+', '5'])

        q = "not ((not a and not b) or 1) or not not c"
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.OrStatement)
        self.assertIsInstance(cond.statements[0], NanoCondition.NegateStatement)
        self.assertIsInstance(cond.statements[0].statement, NanoCondition.OrStatement)
        self.assertIsInstance(cond.statements[0].statement.statements[0], NanoCondition.AndStatement)
        self.assertIsInstance(cond.statements[0].statement.statements[0].statements[0], NanoCondition.NegateStatement)
        self.assertIsInstance(cond.statements[0].statement.statements[0].statements[1], NanoCondition.NegateStatement)
        self.assertStatement(cond.statements[0].statement.statements[0].statements[0].statement, 'a')
        self.assertStatement(cond.statements[0].statement.statements[0].statements[1].statement, 'b')
        self.assertStatement(cond.statements[0].statement.statements[1], '1')
        self.assertStatement(cond.statements[1], 'c')

        q = """((a and "and") or not "or">=6 + b or a< 2 or not (7+4-(9/ 1) and ((5*6) == 4)))"""
        cond = NanoCondition.NanoCondition(NanoQueries._QueryGrammar.tokenizeQuery(q)).mainStatement
        self.assertIsInstance(cond, NanoCondition.OrStatement)
        self.assertIsInstance(cond.statements[0], NanoCondition.AndStatement)
        self.assertStatement(cond.statements[0].statements[0], 'a')
        self.assertStatement(cond.statements[0].statements[1], '"and"')
        self.assertIsInstance(cond.statements[1], NanoCondition.NegateStatement)
        self.assertStatement(cond.statements[1].statement, '"or"', '>=', ['6', "+", "b"])
        self.assertStatement(cond.statements[2], 'a', '<', '2')
        self.assertIsInstance(cond.statements[3], NanoCondition.NegateStatement)
        self.assertIsInstance(cond.statements[3].statement, NanoCondition.AndStatement)
        self.assertStatement(cond.statements[3].statement.statements[0], ['7', '+', '4', '-', '(', '9', '/', '1', ')'])
        self.assertStatement(cond.statements[3].statement.statements[1], ['(', '5', '*', '6', ')'], '==', '4')


class TestBlockCacheManager(NanoTests.NanoTestCase):
    tableName = "testIndexTable"
    colName = "testIndexCol"
    old_max_num_dirty_blocks = NanoConfig.max_num_dirty_blocks
    old_index_block_size = NanoConfig.index_block_size

    def setUp(self):
        NanoConfig.num_index_dirty_blocks = 4
        NanoConfig.index_block_size = 29

        self.blocks = []
        self.blocks2 = []
        for i in range(4):
            self.blocks.append(NanoBlocks.Index.LeafBlock(101, NanoTypes.getType('char4')))
            self.blocks[-1].pointers = []
            self.blocks[-1].keys = ["blk%d" % i]
            self.blocks[-1].address = i * NanoConfig.index_block_size
            self.blocks2.append(NanoBlocks.Index.LeafBlock(101, NanoTypes.getType('char4')))
            self.blocks2[-1].pointers = []
            self.blocks2[-1].keys = ["blk%d" % i]
            self.blocks2[-1].address = i * NanoConfig.index_block_size


        self.fd = NanoIO.File.createIndex(self.dbName, self.tableName, self.colName)

        self.dirtyMgr = NanoTools.BlockCacheManager.BlockCacheManager(self.fd)

    def tearDown(self):
        self.fd.close()
        NanoIO.File.deleteIndex(self.dbName, self.tableName, self.colName)
        NanoConfig.max_num_dirty_blocks = self.old_max_num_dirty_blocks
        NanoConfig.index_block_size = self.old_index_block_size

    def testAdd(self):
        self.assertEqual(len(self.dirtyMgr), 0)
        for block in self.blocks:
            self.dirtyMgr.addBlock(block)

        self.assertItemsEqual(self.dirtyMgr.dirtyDict.keys(), [b.address for b in self.blocks])
        self.assertItemsEqual(self.dirtyMgr.dirtyDict.values(), self.blocks)
        self.assertItemsEqual(self.dirtyMgr.dirtyDict.keys(), [b.address for b in self.blocks])

        for block in self.blocks:
            self.assertIn(block.address, self.dirtyMgr)
            self.assertEqual(block, self.dirtyMgr.getBlock(block.address))
        self.assertEqual(len(self.dirtyMgr), len(self.blocks))

        # Test overwriting previously inserted blocks
        for block in self.blocks2:
            self.dirtyMgr.addBlock(block)

        self.assertEqual(len(self.dirtyMgr), len(self.blocks))
        self.assertItemsEqual(self.dirtyMgr.dirtyDict.values(), self.blocks2)
        self.assertNotIn(self.blocks[0], self.dirtyMgr.dirtyDict.values())

        # Test writing more than NUM_INDEX_DIRTY_BLOCKS
        self.dirtyMgr.addBlock(self.blocks[0])

        self.assertEqual(len(self.dirtyMgr), len(self.blocks))
        self.assertIn(self.blocks[0], self.dirtyMgr.dirtyDict.values())
        
        self.assertNotIn(self.blocks2[0].address, self.dirtyMgr.dirtyDict.values())

    def testGet(self):
        self.assertEqual(len(self.dirtyMgr), 0)
        for block in self.blocks:
            self.dirtyMgr.addBlock(block)

        self.assertItemsEqual(self.dirtyMgr.dirtyDict.values(), self.blocks)

        for block in self.blocks:
            self.assertEqual(self.dirtyMgr.getBlock(block.address), block)

        self.dirtyMgr.truncate()

        self.assertEqual(len(self.dirtyMgr), 0)

        for block in self.blocks2:
            self.dirtyMgr.addBlock(block)
            self.assertEqual(self.dirtyMgr.getBlock(block.address), block)

        for block in self.blocks:
           self.assertRaises(Exception, self.dirtyMgr.getBlock, block)


    def testFlush(self):
        self.assertEqual(len(self.dirtyMgr), 0)
        for block in self.blocks:
            self.dirtyMgr.addBlock(block)

        self.assertEqual(self.dirtyMgr.fd.tell(), 0)

        for block in self.blocks[:0:-1]:
            self.dirtyMgr.flushBlock(block.address)

        self.fd.seek(0)
        flushed = self.fd.read()
        self.assertIn("blk1", flushed)
        self.assertIn("blk2", flushed)
        self.assertIn("blk3", flushed)
        self.assertNotIn("blk0", flushed)

        self.dirtyMgr.flushBlock()
        self.fd.seek(0)
        self.assertIn("blk0", self.fd.read())


    def testTruncate(self):
        self.assertEqual(len(self.dirtyMgr), 0)
        for block in self.blocks:
            self.dirtyMgr.addBlock(block)

        self.dirtyMgr.truncate()

        self.assertEqual(len(self.dirtyMgr), 0)
        for block in self.blocks:
            self.assertNotIn(block.address, self.dirtyMgr)


class TestDeletedBlockManager(NanoTests.NanoTestCase):
    tableName = "DelBlockTestTable"

    def setUp(self):
        self.delMgr = NanoTools.DeletedBlockManager.DeletedBlockManager(self.dbName, self.tableName)

    def tearDown(self):
        self.delMgr.close()

    def testAddPop(self):
        self.assertIsNone(self.delMgr.popRef())
        for i in range(150):
            self.delMgr.addRef(i)

        for i in range(150)[::-1]:
            self.assertEqual(self.delMgr.popRef(), i)

        self.assertIsNone(self.delMgr.popRef())


    def testTruncate(self):
        self.assertIsNone(self.delMgr.popRef())
        for i in range(150):
            self.delMgr.addRef(i)

        self.delMgr.truncate()

        self.assertIsNone(self.delMgr.popRef())

        self.delMgr.addRef(1)
        self.assertEqual(self.delMgr.popRef(), 1)


    def testPersistent(self):
        self.assertIsNone(self.delMgr.popRef())
        for i in range(150):
            self.delMgr.addRef(i)

        self.delMgr.close()

        self.delMgr = NanoTools.DeletedBlockManager.DeletedBlockManager(self.dbName, self.tableName)

        for i in range(150)[::-1]:
            self.assertEqual(self.delMgr.popRef(), i)

        self.assertIsNone(self.delMgr.popRef())
