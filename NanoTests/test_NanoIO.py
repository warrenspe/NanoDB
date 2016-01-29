# Standard imports
import time, sys, random

# Project imports
import NanoTests
import NanoTypes

import NanoBlocks.Index

import NanoIO.File
import NanoIO.Index

import NanoConfig
import NanoConfig.Table
import NanoConfig.Column
import NanoConfig.Index


class TestIndex(NanoTests.NanoTestCase):
    tableName = "IOTestIndex"
    indexColName = "IOTestIndexedColumn"
    indexConfig = None
    dataType = NanoTypes.getType('int4')

    def setUp(self):
        col = NanoConfig.Column.Config()
        col.name = self.indexColName
        col.typeString = "int4"
        self.indexConfig = NanoConfig.Index.Config()
        self.indexConfig.column = col
        self.indexConfig.unique = False

        NanoIO.File.deleteIndex(self.dbName, self.tableName, self.indexColName)
        NanoIO.File.createIndex(self.dbName, self.tableName, self.indexColName)
        self.IndexIO = NanoIO.Index.IndexIO(self.dbName, self.tableName, self.indexConfig)

    def tearDown(self):
        NanoIO.File.deleteIndex(self.dbName, self.tableName, self.indexColName)

    def _assertIndexBlockEqual(self, indexBlock, indexBlock2):
        self.assertEqual(indexBlock2.isLeaf, indexBlock.isLeaf)
        self.assertEqual(indexBlock2.address, indexBlock.address)
        self.assertEqual(indexBlock2.dataType.quantifier, indexBlock.dataType.quantifier)
        self.assertSequenceEqual(indexBlock2.keys, indexBlock.keys)
        self.assertSequenceEqual(indexBlock2.addresses, indexBlock.addresses)

    def testGetAndWriteBlockAtIndex(self):
        # Test getting a block from an index with no keys
        self._assertIndexBlockEqual(self.IndexIO._getBlockAtAddress(0), NanoBlocks.Index.LeafBlock(0, self.IndexIO.colType))

        # Test getting a fresh block
        indexBlock = NanoBlocks.Index.LeafBlock(0, NanoTypes.Int(4))
        self.IndexIO.indexFD.write(indexBlock.toString())

        self.assertFalse(0 in self.IndexIO.cacheMgr)
        self._assertIndexBlockEqual(indexBlock, self.IndexIO._getBlockAtAddress(0))

        # Test getting a block that should exist in the Block Cache Manager
        indexBlock.keys = [1]
        indexBlock.addresses = [2]
        self.IndexIO._writeBlockToFile(indexBlock)
        self.assertTrue(0 in self.IndexIO.cacheMgr)
        self._assertIndexBlockEqual(indexBlock, self.IndexIO._getBlockAtAddress(0))

    def testMarkDeletedBlock(self):
        indexBlock = NanoBlocks.Index.LeafBlock(5, NanoTypes.Int(4))
        indexBlock.keys = [1]
        indexBlock.addresses = [2]
        self.IndexIO._writeBlockToFile(indexBlock)
        self.IndexIO._markBlockDeleted(indexBlock)
        self.assertEqual(self.IndexIO.delMgr.popRef(), 5)
        self.assertIsNone(self.IndexIO.delMgr.popRef())

    def testGetIdxForNewBlock(self):
        self.assertEqual(self.IndexIO._getAddressForNewBlock(), NanoConfig.index_block_size)
        idxBlock = self.IndexIO._getBlockAtAddress(0)
        idxBlock.address = NanoConfig.index_block_size
        self.IndexIO._writeBlockToFile(idxBlock)
        self.assertEqual(self.IndexIO._getAddressForNewBlock(), NanoConfig.index_block_size * 2)
        self.IndexIO._markBlockDeleted(idxBlock)
        self.assertEqual(self.IndexIO._getAddressForNewBlock(), NanoConfig.index_block_size)

    def testAddLookupDelete(self):
        # Test adding to an empty index
        self.assertRaises(NanoBlocks.Index.KeyNotFound, self.IndexIO.lookup, 1)
        self.IndexIO.add(1, 2)
        self.assertEqual(self.IndexIO.lookup(1), 2)

        # Test adding to an index with a single partially full leaf block
        for i in range(5, 50, 2):
            self.IndexIO.add(i, i + 1)

        self.assertRaises(NanoBlocks.Index.KeyNotFound, self.IndexIO.lookup, 8)
        self.IndexIO.add(8, 9)
        self.assertEqual(self.IndexIO.lookup(8), 9)

        # Test adding values to the beginning of a partially full leaf block
        self.assertRaises(NanoBlocks.Index.KeyNotFound, self.IndexIO.lookup, 0)
        self.IndexIO.add(0, 0)
        self.assertEqual(self.IndexIO.lookup(0), 0)

        # Test adding to an index with a single full leaf block
        self.tearDown(); self.setUp()
        rootBlock = self.IndexIO._getBlockAtAddress(0)
        rootBlock.keys = []
        rootBlock.addresses = []
        for i in range(rootBlock.maxKeys):
            rootBlock.add(i, i + 1)
        self.IndexIO._writeBlockToFile(rootBlock)

        for i in range(rootBlock.maxKeys):
            self.assertEqual(self.IndexIO.lookup(i), i + 1)
        self.IndexIO.add(20, 20)
        self.IndexIO.add(500, 500)

        for i in range(1, 170):
            self.IndexIO.add(-i, i)

        # Test adding to an index with a root interior block pointing to leaf blocks # TODO

        # Test adding to an index with a full root interior block, pointing to leaf blocks # TODO

        # Test adding to an index with a root interior block pointing to interior blocks # TODO


    def testRandomAddDeleteLookup(self):
        seed = 124
        numPairs = 4000
        keyRange = (0, 10000000)
        random.seed(seed)

        keys = set([random.randint(*keyRange) for i in range(numPairs)])
        pairs = [(k, random.randint(*keyRange)) for k in keys]

        for k, a in pairs:
            self.IndexIO.add(k, a)

        for k, a in reversed(pairs):
            self.assertEqual(self.IndexIO.lookup(k), a)
            self.IndexIO.delete(k)
            self.assertRaises(NanoBlocks.Index.KeyNotFound, self.IndexIO.lookup, k)

        root = self.IndexIO._getBlockAtAddress(0)
        self.assertEqual(len(root.keys), 0)

    def testDelete(self): # TODO
        pass

    def testLookup(self): # TODO
        pass

    def testLookupCondition(self): # TODO
        pass

    def testIterate(self): # TODO
        pass


class TestFile(NanoTests.NanoTestCase):

    dbName2 = "NanoDBUnitTests2"
    tableName = "IOTestFile"
    indexColName = "IOTestIndexedColumn"

    def testRenaming(self): # TODO finish
        col = NanoConfig.Column.Config()
        col.name = self.indexColName
        col.typeString = "int4"
        self.indexConfig = NanoConfig.Index.Config()
        self.indexConfig.column = col
        self.indexConfig.unique = False

        NanoIO.File.deleteIndex(self.dbName, self.tableName, self.indexColName)
        NanoIO.File.createIndex(self.dbName, self.tableName, self.indexColName)

        NanoIO.createTable(self.dbName, self.tableName).close()
        tableIO = NanoIO.Table.TableIO(self.dbName, self.tableName)
        indexIO = NanoIO.Index.IndexIO(self.dbName, self.tableName, self.indexConfig)

    def testDatabaseUtils(self): # TODO figure out why this hangs - shutil?
        NanoIO.File.createDatabase(self.dbName2)

        self.assertTrue(NanoIO.File.checkDatabaseExists(self.dbName2))
        self.assertIsNone(NanoIO.File.assertDatabaseExists(self.dbName2))

        NanoIO.File.deleteDatabase(self.dbName2)

        # Give the file system a bit of time to remove the iNode
        time.sleep(.01)

        self.assertFalse(NanoIO.File.checkDatabaseExists(self.dbName2))
        self.assertRaises(IOError, NanoIO.File.assertDatabaseExists, self.dbName2)

    def testTableUtils(self):
        self.assertTrue(NanoIO.File.checkDatabaseExists(self.dbName))

        configFD = NanoIO.File.createTable(self.dbName, self.tableName)
        self.assertFalse(configFD.closed)
        configFD.close()

        configFD = NanoIO.File.getConfig(self.dbName, self.tableName)
        self.assertFalse(configFD.closed)
        configFD.close()

        tableFD = NanoIO.File.getTable(self.dbName, self.tableName)
        self.assertFalse(tableFD.closed)
        tableFD.close()

        self.assertTrue(NanoIO.File.checkTableExists(self.dbName, self.tableName))
        self.assertTrue(NanoIO.File.checkConfigExists(self.dbName, self.tableName))

        NanoIO.File.deleteTable(self.dbName, self.tableName)

        self.assertFalse(NanoIO.File.checkTableExists(self.dbName, self.tableName))
        self.assertFalse(NanoIO.File.checkConfigExists(self.dbName, self.tableName))

    def testIndexUtils(self):
        self.assertTrue(NanoIO.File.checkDatabaseExists(self.dbName))

        NanoIO.File.createIndex(self.dbName, self.tableName, self.indexColName)

        self.assertTrue(NanoIO.File.checkIndexExists(self.dbName, self.tableName, self.indexColName))
        self.assertRaises(Exception, NanoIO.File.createIndex, self.dbName, self.tableName, self.indexColName)

        index = NanoIO.File.getIndex(self.dbName, self.tableName, self.indexColName)

        self.assertFalse(index.closed)

        index.close()

        NanoIO.File.deleteIndex(self.dbName, self.tableName, self.indexColName)

        self.assertFalse(NanoIO.File.checkIndexExists(self.dbName, self.tableName, self.indexColName))
        self.assertRaises(Exception, NanoIO.File.getIndex, self.dbName, self.tableName, self.indexColName)

    def testPtrFstrUtils(self):
        self.assertTrue(NanoIO.File.checkDatabaseExists(self.dbName))

        self.assertFalse(NanoIO.File.checkPtrFstrExists(self.dbName, 'testTable', 'testCol'))

        NanoIO.File.createPtrFstr(self.dbName, 'testTable', 'testCol')

        self.assertTrue(NanoIO.File.checkPtrFstrExists(self.dbName, 'testTable', 'testCol'))

        self.assertRaises(Exception, NanoIO.File.createPtrFstr, self.dbName, 'testTable', 'testCol')

        fd = NanoIO.File.getPtrFstr(self.dbName, 'testTable', 'testCol')

        self.assertFalse(fd.closed)

        fd.close()

        NanoIO.File.deletePtrFstr(self.dbName, 'testTable', 'testCol')

        self.assertFalse(NanoIO.File.checkPtrFstrExists(self.dbName, 'testTable', 'testCol'))
        self.assertRaises(Exception, NanoIO.File.getPtrFstr, self.dbName, 'testTable', 'testCol')

    def testGetTablesInDatabase(self):
        self.assertTrue(NanoIO.File.checkDatabaseExists(self.dbName))

        NanoIO.File.createTable(self.dbName, self.tableName)

        self.assertTrue(NanoIO.File.checkTableExists(self.dbName, self.tableName))
        self.assertSequenceEqual(NanoIO.File.getTablesInDatabase(self.dbName), [self.tableName])

        NanoIO.File.createTable(self.dbName, self.tableName + "1")

        self.assertTrue(NanoIO.File.checkTableExists(self.dbName, self.tableName + "1"))
        self.assertSequenceEqual(NanoIO.File.getTablesInDatabase(self.dbName), [self.tableName, self.tableName + "1"])

        NanoIO.File.deleteTable(self.dbName, self.tableName)

        self.assertSequenceEqual(NanoIO.File.getTablesInDatabase(self.dbName), [self.tableName + '1'])
