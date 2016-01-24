# Project imports
import NanoTypes
import NanoTests
import NanoBlocks.Index

class TestIndexBlock(NanoTests.NanoTestCase):

    def assertBlocksEqual(self, block1, block2):
        self.assertEqual(block1.address, block2.address)
        self.assertEqual(block1.isLeaf, block2.isLeaf)
        self.assertEqual(block1.parent, block2.parent)
        self.assertIsInstance(block1.dataType, block2.dataType.__class__)
        self.assertEqual(block1.dataType.quantifier, block2.dataType.quantifier)
        self.assertSequenceEqual(block1.keys, block2.keys)
        self.assertSequenceEqual(block1.addresses, block2.addresses)

    def testLookup(self):
        # Leaf block
        block = NanoBlocks.Index.LeafBlock(0, NanoTypes.Int(1))
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 1)

        block.keys = [1]
        block.addresses = [1]
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 0)
        self.assertEqual(block.lookup(1), 1)
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 2)

        block.keys = [1, 3]
        block.addresses = ['a', 'b']
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 0)
        self.assertEqual(block.lookup(1), 'a')
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 2)
        self.assertEqual(block.lookup(3), 'b')
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 4)

        # Interior block
        block = NanoBlocks.Index.InteriorBlock(0, NanoTypes.Int(1))
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 1)

        block.keys = [1]
        block.addresses = [1]
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 0)
        self.assertEqual(block.lookup(1), 1)
        self.assertEqual(block.lookup(2), 1)

        block.keys = [1, 3]
        block.addresses = ['a', 'b']
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.lookup, 0)
        self.assertEqual(block.lookup(1), 'a')
        self.assertEqual(block.lookup(2), 'a')
        self.assertEqual(block.lookup(3), 'b')
        self.assertEqual(block.lookup(4), 'b')


    def testStringIO(self):
        for blockClass in (NanoBlocks.Index.LeafBlock, NanoBlocks.Index.InteriorBlock):
            for keyType in ("int1", "int2", "int4", "int8", "uint2", "uint8",
                            "float4", "float8"):

                block = blockClass(101, NanoTypes.getType(keyType))
                block2 = blockClass(101, NanoTypes.getType(keyType))
                block.keys = []
                block.addresses = []

                block2.fromString(block.toString())
                self.assertBlocksEqual(block, block2)

                block.keys = [1]
                block.addresses = [4]
                block2.fromString(block.toString())
                self.assertBlocksEqual(block, block2)

                block.keys = range(1, 40, 2)
                block.addresses = [i * 2 for i in range(1, 40, 2)]
                block2.fromString(block.toString())
                self.assertBlocksEqual(block, block2)

                block.keys = [1] * block.maxKeys
                block.addresses = range(block.maxKeys)
                block2.fromString(block.toString())
                self.assertBlocksEqual(block, block2)

                self.assertRaises(Exception, NanoBlocks.Index._IndexBlock.fromString, block.toString() + '\x00')

                block.keys = [block.dataType.nullVal] * (block.maxKeys + 1)
                block.addresses = [NanoBlocks.Index.ADDRESS_TYPE.nullVal] * (block.maxKeys + 1)

                self.assertRaises(Exception, block.toString)

        for blockClass in (NanoBlocks.Index.LeafBlock, NanoBlocks.Index.InteriorBlock):
            for keyQuantifier in range(1, 40):
                
                block = blockClass(101, NanoTypes.getType("char%d" % keyQuantifier))
                block2 = blockClass(101, NanoTypes.getType("char%d" % keyQuantifier))
                block.idx = 101
                block.parent = 154
                block.keys = []
                block.addresses = []

                block2.fromString(block.toString())
                self.assertBlocksEqual(block, block2)

                block.keys = ['1']
                block.addresses = [4]
                block2.fromString(block.toString())
                self.assertBlocksEqual(block, block2)
                block.keys = ["1" * keyQuantifier] * block.maxKeys
                block.addresses = range(block.maxKeys)
                block2.fromString(block.toString())
                self.assertBlocksEqual(block, block2)

                self.keys = [str(k) for k in range(block.maxKeys + 1)]
                self.assertRaises(Exception, NanoBlocks.Index._IndexBlock.fromString, block.toString())


    def testAdd(self):
        # Add to an empty leaf block
        block = NanoBlocks.Index.LeafBlock(101, NanoTypes.getType("int1"))
        block.keys = []
        block.addresses = []
        block.add(5, 7)
        self.assertSequenceEqual(block.keys, [5])
        self.assertSequenceEqual(block.addresses, [7])

        # Add to a half full leaf block
        block.add(6, 8)
        block.add(4, 5)
        block.add(5, 10)
        self.assertSequenceEqual(block.keys, [4, 5, 5, 6])
        self.assertSequenceEqual(block.addresses, [5, 10, 7, 8])

        # Add to 1 off from full leaf block
        block.keys = [2] + ([3] * (block.maxKeys - 2))
        block.addresses = [5] * (block.maxKeys - 1)
        block.add(1, 1)
        self.assertSequenceEqual(block.keys, [1, 2] + ([3] * (block.maxKeys - 2)))
        self.assertSequenceEqual(block.addresses, [1] + ([5] * (block.maxKeys - 1)))

        block.keys = [2] + ([3] * (block.maxKeys - 2))
        block.addresses = [5] * (block.maxKeys - 1)
        block.add(2, 2)
        self.assertSequenceEqual(block.keys, [2, 2] + ([3] * (block.maxKeys - 2)))
        self.assertSequenceEqual(block.addresses, [2] + ([5] * (block.maxKeys - 1)))

        block.keys = [2] + ([3] * (block.maxKeys - 2))
        block.addresses = [5] * (block.maxKeys - 1)
        block.add(3, 3)
        self.assertSequenceEqual(block.keys, [2, 3] + ([3] * (block.maxKeys - 2)))
        self.assertSequenceEqual(block.addresses, [5, 3] + ([5] * (block.maxKeys - 2)))

        # Add to a full leaf block
        block.keys = [3] * block.maxKeys
        block.addresses = [4] * block.maxKeys
        self.assertRaises(BufferError, block.add, 2, 3)
        self.assertRaises(BufferError, block.add, 3, 3)
        self.assertRaises(BufferError, block.add, 4, 3)

        # Add to an empty interior block
        block = NanoBlocks.Index.InteriorBlock(101, NanoTypes.getType("int1"))
        block.keys = []
        block.addresses = []
        block.add(5, 7)
        block.add(6, 8)
        self.assertSequenceEqual(block.keys, [5, 6])
        self.assertSequenceEqual(block.addresses, [7, 8])

        # Add to a interior block with 1 key and 1 address
        block = NanoBlocks.Index.InteriorBlock(101, NanoTypes.getType("int1"))
        block.keys = [4]
        block.addresses = [5]
        block.add(5, 4)
        self.assertSequenceEqual(block.keys, [4, 5])
        self.assertSequenceEqual(block.addresses, [5, 4])

        block = NanoBlocks.Index.InteriorBlock(101, NanoTypes.getType("int1"))
        block.keys = [4]
        block.addresses = [5]
        block.add(3, 4)
        self.assertSequenceEqual(block.keys, [3, 4])
        self.assertSequenceEqual(block.addresses, [4, 5])


        # Add to a half full interior block
        block.add(6, 8)
        block.add(4, 5)
        block.add(5, 10)
        self.assertSequenceEqual(block.keys, [3, 4, 4, 5, 6])
        self.assertSequenceEqual(block.addresses, [4, 5, 5, 10, 8])

        # Add to 1 off from full interior block
        block.keys = [2] + ([3] * (block.maxKeys - 2))
        block.addresses = [5] * (block.maxKeys - 1)
        block.add(1, 1)
        self.assertSequenceEqual(block.keys, [1, 2] + ([3] * (block.maxKeys - 2)))
        self.assertSequenceEqual(block.addresses, [1] + ([5] * (block.maxKeys - 1)))

        block.keys = [2] + ([3] * (block.maxKeys - 2))
        block.addresses = [5] * (block.maxKeys - 1)
        block.add(2, 2)
        self.assertSequenceEqual(block.keys, [2, 2] + ([3] * (block.maxKeys - 2)))
        self.assertSequenceEqual(block.addresses, [2] + ([5] * (block.maxKeys - 1)))

        block.keys = [2] + ([3] * (block.maxKeys - 2))
        block.addresses = [5] * (block.maxKeys - 1)
        block.add(3, 3)
        self.assertSequenceEqual(block.keys, [2, 3] + ([3] * (block.maxKeys - 2)))
        self.assertSequenceEqual(block.addresses, [5, 3] + ([5] * (block.maxKeys - 2)))

        # Add to a full interior block
        self.assertRaises(BufferError, block.add, 1, 3)
        self.assertRaises(BufferError, block.add, 2, 3)
        self.assertRaises(BufferError, block.add, 3, 3)
        self.assertRaises(BufferError, block.add, 4, 3)


    def testDelete(self):
        # Delete from an empty block
        block = NanoBlocks.Index.LeafBlock(101, NanoTypes.getType("int1"))
        block.keys = []
        block.addresses = []
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.delete, 1)

        # Delete a non-present key from the block
        block.keys = [5]
        block.addresses = [6]
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.delete, 1)

        # Delete from a leaf with 1 key
        block.delete(5)
        self.assertSequenceEqual(block.keys, [])
        self.assertSequenceEqual(block.addresses, [])

        # Delete from the beginning of a half-full leaf
        block.keys = [3, 4, 5, 6, 7]
        block.addresses = [8, 9, 10, 11, 12]
        block.delete(3)
        self.assertSequenceEqual(block.keys, [4, 5, 6, 7])
        self.assertSequenceEqual(block.addresses, [9, 10, 11, 12])

        # Delete from the end of a half-full leaf
        block.delete(7)
        self.assertSequenceEqual(block.keys, [4, 5, 6])
        self.assertSequenceEqual(block.addresses, [9, 10, 11])

        # Delete from the middle of a half-full leaf
        block.delete(5)
        self.assertSequenceEqual(block.keys, [4, 6])
        self.assertSequenceEqual(block.addresses, [9, 11])

        # Delete from a interior with 1 key and 1 address
        block = NanoBlocks.Index.InteriorBlock(101, NanoTypes.getType("int1"))
        block.keys = [5]
        block.addresses = [6]
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.delete, 4)
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.delete, 6)
        block.delete(5)
        self.assertSequenceEqual(block.keys, [])
        self.assertSequenceEqual(block.addresses, [])

        # Delete from the beginning of a half-full interior block
        block.keys = [3, 4, 5, 6, 7]
        block.addresses = [8, 9, 10, 11, 12]
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.delete, 2)
        self.assertRaises(NanoBlocks.Index.KeyNotFound, block.delete, 8)
        block.delete(3)
        self.assertSequenceEqual(block.keys, [4, 5, 6, 7])
        self.assertSequenceEqual(block.addresses, [9, 10, 11, 12])

        # Delete from the end of a half-full interior block
        block.delete(7)
        self.assertSequenceEqual(block.keys, [4, 5, 6])
        self.assertSequenceEqual(block.addresses, [9, 10, 11])

        # Delete from the middle of a half-full interior block
        block.delete(5)
        self.assertSequenceEqual(block.keys, [4, 6])
        self.assertSequenceEqual(block.addresses, [9, 11])
