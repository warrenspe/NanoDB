# Project imports
import NanoTypes
import NanoIO.File
import NanoTests
from NanoBlocks._MemoryMappedBlock import MemoryMappedBlock

class MemoryMappedTester(MemoryMappedBlock):
    blockSize = 10
    fields = [
        'name',
        'typ',
        'typ2',
    ]
    dataTypes = {
        'name': NanoTypes.Char(4),
        'typ': NanoTypes.Uint(2),
        'typ2': NanoTypes.Uint(4),
    }

class TestNanoTypes(NanoTests.NanoTestCase):

    def testGetType(self):
        self.assertEqual(str(NanoTypes.getType("int1")), "Int1")
        self.assertEqual(str(NanoTypes.getType("int2")), "Int2")
        self.assertEqual(str(NanoTypes.getType("int4")), "Int4")
        self.assertEqual(str(NanoTypes.getType("int8")), "Int8")
        self.assertEqual(str(NanoTypes.getType("uint4")), "Uint4")
        self.assertEqual(str(NanoTypes.getType("char10")), "Char10")
        self.assertEqual(str(NanoTypes.getType("float4")), "Float4")
        self.assertEqual(str(NanoTypes.getType("float8")), "Float8")

    def testInt(self):
        for iVal in (1, 2, 4, 8):
            i = NanoTypes.getType("int%d" % iVal)

            self.assertEqual(i.isValid('test'), False)
            self.assertEqual(i.isValid(i), False)
            self.assertEqual(i.isValid(i.maxVal + 1), False)
            self.assertEqual(i.isValid(i.minVal - 2), False)
            self.assertEqual(i.isValid(i.minVal), True)
            self.assertEqual(i.isValid(i.maxVal), True)
            self.assertEqual(i.toString(1), "\x01" + ("\x00" * (iVal - 1)))
            self.assertEqual(i.toString(16), "\x10" + ("\x00" * (iVal - 1)))
            self.assertEqual(i.fromString("\x10" + ("\x00" * (iVal - 1))), 16)
            self.assertEqual(i.isValid(i.nullVal), True)
            self.assertEqual(i.toString(None), i.toString(i.nullVal))
            self.assertEqual(i.fromString(i.toString(None)), None)
            self.assertEqual(i.fromString(i.toString(i.nullVal)), None)
            self.assertRaises(ValueError, i.toString, i.maxVal + 1)

    def testUint(self):
        for iVal in (1, 2, 4, 8):
            i = NanoTypes.getType("uint%d" % iVal)

            self.assertEqual(i.isValid('test'), False)
            self.assertEqual(i.isValid(i), False)
            self.assertEqual(i.isValid(i.maxVal + 2), False)
            self.assertEqual(i.isValid(-1), False)
            self.assertEqual(i.isValid(0), True)
            self.assertEqual(i.isValid(i.maxVal), True)
            self.assertEqual(i.toString(1), "\x01" + ("\x00" * (iVal - 1)))
            self.assertEqual(i.toString(16), "\x10" + ("\x00" * (iVal - 1)))
            self.assertEqual(i.fromString("\x10" + ("\x00" * (iVal - 1))), 16)
            self.assertEqual(i.isValid(i.nullVal), True)
            self.assertEqual(i.toString(None), i.toString(i.nullVal))
            self.assertEqual(i.fromString(i.toString(None)), None)
            self.assertEqual(i.fromString(i.toString(i.nullVal)), None)
            self.assertRaises(ValueError, i.toString, i.maxVal + 2)


    def testFloat(self):
        for iVal in (4, 8):
            f = NanoTypes.getType("float%d" % iVal)

            self.assertEqual(f.isValid('test'), False)
            self.assertEqual(f.isValid(f), False)
            self.assertEqual(f.isValid(f.nullVal), True)
            self.assertEqual(f.isValid(0), True)
            self.assertEqual(f.isValid(0.0), True)
            self.assertEqual(f.isValid(100000.0), True)
            self.assertEqual(f.isValid(23495812980375.123547861235), True)
            self.assertEqual(f.isValid(-129357.12351235), True)
            self.assertEqual(f.toString(f.nullVal), f.toString(None))
            self.assertEqual(f.fromString(f.toString(None)), None)
            self.assertRaises(ValueError, f.toString, 'testing')


    def testChar(self):
        for iVal in range(1, 257):
            c = NanoTypes.getType("char%d" % iVal)

            self.assertEqual(c.isValid(4), False)
            self.assertEqual(c.isValid(c), False)
            self.assertEqual(c.isValid(c.nullVal), True)
            self.assertEqual(c.isValid("a" * iVal), True)
            self.assertEqual(c.isValid("_" * iVal), True)
            self.assertEqual(c.toString(None), c.toString(c.nullVal))
            self.assertEqual(c.fromString(c.nullVal), None)
            self.assertEqual(c.fromString(c.toString(None)), None)
            self.assertRaises(ValueError, c.toString, 54)

    def testVarchar(self):
        fd = NanoIO.File.createPtrFstr(self.dbName, 'NanoTypes', 'Varchar')

        v = NanoTypes.getType('varchar', fd)

        idx = v.toString('test')
        self.assertEqual(v.fromString(idx), 'test')
        self.assertEqual(v.fromString(idx), 'test')
        self.assertEqual(v.fromString(idx), 'test')

        idx2 = v.toString('test2')
        self.assertEqual(v.fromString(idx), 'test')
        self.assertEqual(v.fromString(idx2), 'test2')
