# Project imports
import NanoTests
import NanoConfig.Table
import NanoConfig.Index
import NanoConfig.Column
# TODO test setting config options

class TestConfigs(NanoTests.NanoTestCase):
    def assertColumnsEqual(self, c1, c2):
        self.assertEqual(c1.name, c2.name)
        self.assertEqual(c1.typeString, c2.typeString)

    def assertIndicesEqual(self, i1, i2):
        self.assertColumnsEqual(i1.column, i2.column)
        self.assertEqual(i1.unique, i2.unique)

    def assertTablesEqual(self, t1, t2):
        self.assertEqual(t1.name, t2.name)
        self.assertEqual(t1.rowSize, t2.rowSize)
        self.assertEqual(len(t1.indices), len(t2.indices))
        self.assertEqual(len(t1.columns), len(t2.columns))

        for i in range(len(t1.indices)):
            self.assertIndicesEqual(t1.indices[i], t2.indices[i])

        for i in range(len(t1.columns)):
            self.assertColumnsEqual(t1.columns[i], t2.columns[i])

    def testColumn(self):
        column = NanoConfig.Column.Config()
        column2 = NanoConfig.Column.Config()

        column.name = 'test'
        column.typeString = 'int4'

        column2.fromString(column.toString())

        self.assertColumnsEqual(column, column2)

    def testIndex(self):
        index = NanoConfig.Index.Config()
        index2 = NanoConfig.Index.Config()
        index.column = NanoConfig.Column.Config()
        index.column.name = 'test'
        index.column.typeString = 'int4'

        index.unique = 1

        index2.fromString(index.toString())

        self.assertIndicesEqual(index, index2)

    def testTable(self):
        table = NanoConfig.Table.Config()
        table2 = NanoConfig.Table.Config()

        col1 = NanoConfig.Column.Config()
        col2 = NanoConfig.Column.Config()
        col1.name = 'col1'
        col1.typeString = 'int1'
        col2.name = 'column2'
        col2.typeString = 'char2'

        idx1 = NanoConfig.Index.Config()
        idx2 = NanoConfig.Index.Config()
        idx3 = NanoConfig.Index.Config()
        idx1.unique = 1
        idx1.column = col1
        idx2.unique = 0
        idx2.column = col2
        idx3.unique = 1
        idx3.column = col1

        table.name = 'testTable'
        table.columns = [col1, col2]
        table.indices = [idx1, idx2, idx3]
        table.rowSize = 45

        table2.fromString(table.toString())

        self.assertTablesEqual(table, table2)
