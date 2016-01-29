"""
Contains miscellaneous functions for creating / getting / removing database, table, and index files.
"""

# Standard imports
import os, glob, shutil # TODO reimplement w/o shutils - random hanging

# Project imports
import NanoConfig

# Static globals
__TABLE_EXT = "tbl"    # Table Extension
__CONFIG_EXT = "tcf"   # Table Config Extension
__INDEX_EXT = "idx"    # Index Extension
__DELMGR_EXT = "del"   # Deleted Block Manager Extension
__PTR_FSTR_EXT = "pfs" # Pointer Type Filestore Extension


###
# Helper functions
###
dbPath = lambda dbName: os.path.join(NanoConfig.root_dir, dbName)
_path = lambda dbName, fileName, ext: os.path.join(dbPath(dbName), "%s.%s" % (fileName, ext))
indexFileName = lambda tableName, colName: "_idx_%s_%s" % (tableName, colName)
indexPath = lambda dbName, tableName, colName: _path(dbName, indexFileName(tableName, colName), __INDEX_EXT)
tablePath = lambda dbName, tableName: _path(dbName, tableName, __TABLE_EXT)
configPath = lambda dbName, tableName: _path(dbName, tableName, __CONFIG_EXT)
delMgrPath = lambda dbName, tableName: _path(dbName, tableName, __DELMGR_EXT)
ptrFstrName = lambda tableName, colName: "%s_%s" % (tableName, colName)
ptrFstrPath = lambda dbName, tableName, colName: _path(dbName, ptrFstrName(tableName, colName), __PTR_FSTR_EXT)

def checkDatabaseExists(dbName):
    if dbName is None or not os.path.isdir(dbPath(dbName)):
        return False
    return True

def checkTableExists(dbName, name):
    if os.path.isfile(tablePath(dbName, name)):
        return True
    return False

def checkIndexExists(dbName, tableName, colName):
    if os.path.isfile(indexPath(dbName, tableName, colName)):
        return True
    return False

def checkConfigExists(dbName, name):
    if os.path.isfile(configPath(dbName, name)):
        return True
    return False

def checkPtrFstrExists(dbName, tableName, colName):
    if os.path.isfile(ptrFstrPath(dbName, tableName, colName)):
        return True
    return False

def assertDatabaseExists(dbName):
    if not checkDatabaseExists(dbName):
        raise IOError("Database %s does not exist at %s" % (dbName, NanoConfig.root_dir))


def openReadWriteFile(path):
    """ Opens a file for read and writing.  Creates it if it does not exist, but does not truncate it if it does. """

    if os.path.isfile(path):
        return open(path, 'r+')
    return open(path, 'w+')

###
# API Functions
###

# Renames
def _renameIndex(index, dbName, tableName): #TODO test
    """ Renames an index to a new database / table name. """

    # Flush & close the index
    index.close()

    # Rename the index data file
    os.rename(indexPath(dbName, index.tableName, index.indexConfig.column.name),
              indexPath(dbName, tableName, index.indexConfig.column.name))

    # Rename the deleted manager file for our data file
    os.rename(delMgrPath(dbName, indexFileName(index.tableName, index.indexConfig.column.name)),
              delMgrPath(dbName, indexFileName(tableName, index.indexConfig.column.name)))
    

def _renameTable(table, dbName, tableName): # TODO test
    """ Renames a table to a new database / table name. """

    # Flush and close the table
    table.close()

    # Rename the table data file
    os.rename(tablePath(dbName, table.tableName), tablePath(dbName, tableName))

    # Rename the table config file
    os.rename(configPath(dbName, table.tableName), configPath(dbName, tableName))

    # Rename the table's deleted manager file
    os.rename(delMgrPath(dbName, table.tableName), delMgrPath(dbName, tableName))

    # Rename each index associated with this table
    for index in table.indices:
        _renameIndex(index, dbName, tableName)


# Creates
def createDatabase(dbName):
    if checkDatabaseExists(dbName):
        raise Exception("Database already exists")
    else:
        # Create the database
        os.makedirs(dbPath(dbName))

def createTable(dbName, name):
    assertDatabaseExists(dbName)

    # Ensure no table with this name already exists
    if checkTableExists(dbName, name):
        raise Exception("Table %s.%s already exists" % (dbName, name))

    if checkConfigExists(dbName, name):
        raise Exception("(Rogue?) configuration file %s.%s already exists" % (dbName, name))

    # Create a table and config file
    open(tablePath(dbName, name), "w+").close()
    open(configPath(dbName, name), "w+").close()

    return open(configPath(dbName, name), "w+")

def createIndex(dbName, tableName, colName):
    assertDatabaseExists(dbName)

    if checkIndexExists(dbName, tableName, colName):
        raise Exception("Index %s.%s_%s already exists" % (dbName, tableName, colName))

    # Create an index file
    open(indexPath(dbName, tableName, colName), "w+").close()

    return open(indexPath(dbName, tableName, colName), "w+")

def createPtrFstr(dbName, tableName, colName):
    if checkPtrFstrExists(dbName, tableName, colName):
        raise Exception("Pointer-Type filestore %s.%s_%s already exists." % (dbName, tableName, colName))

    open(ptrFstrPath(dbName, tableName, colName), 'w+').close()

    return open(ptrFstrPath(dbName, tableName, colName), 'w+')

# Deletes
def deleteDatabase(name):
    assertDatabaseExists(name)
    shutil.rmtree(dbPath(name), ignore_errors=True)

def deleteIndex(dbName, tableName, colName):
    assertDatabaseExists(dbName)

    if checkIndexExists(dbName, tableName, colName):
        os.remove(indexPath(dbName, tableName, colName))

def deleteTable(dbName, name):
    assertDatabaseExists(dbName)

    # Remove the table file
    if checkTableExists(dbName, name):
        os.remove(tablePath(dbName, name))

    # Remove indices and the config file
    if checkConfigExists(dbName, name):
        # Remove indices first so we don't lose reference to them

        # TODO remove indices before we remove the config file

        os.remove(configPath(dbName, name))

def deletePtrFstr(dbName, tableName, colName):
    if checkPtrFstrExists(dbName, tableName, colName):
        os.remove(ptrFstrPath(dbName, tableName, colName))

# Gets
def getTablesInDatabase(dbName):
    assertDatabaseExists(dbName)

    tableNames = [table[:-(len(__TABLE_EXT) + 1)]
                  for table in os.listdir(dbPath(dbName))
                  if table[-len(__TABLE_EXT):] == __TABLE_EXT]

    return [tableName for tableName in tableNames
            if checkTableExists(dbName, tableName) and
               checkConfigExists(dbName, tableName)]

def getTable(dbName, tableName):
    assertDatabaseExists(dbName)

    if not checkTableExists(dbName, tableName):
        raise Exception("Table %s.%s does not exist!" % (dbName, tableName))

    return openReadWriteFile(tablePath(dbName, tableName))

def getIndex(dbName, tableName, colName):
    assertDatabaseExists(dbName)

    if not checkIndexExists(dbName, tableName, colName):
        raise Exception("Index %s.%s_%s does not exist!" % (dbName, tableName, colName))

    return openReadWriteFile(indexPath(dbName, tableName, colName))

def getConfig(dbName, tableName):
    assertDatabaseExists(dbName)

    if not checkConfigExists(dbName, tableName):
        raise Exception("TableConfig %s.%s does not exist!" % (dbName, tableName))

    return openReadWriteFile(configPath(dbName, tableName))

def getPtrFstr(dbName, tableName, colName):
    assertDatabaseExists(dbName)

    if not checkPtrFstrExists(dbName, tableName, colName):
        raise Exception("Pointer-Type filestore %s.%s_%s does not exists!" % (dbName, tableName, colName))

    return openReadWriteFile(ptrFstrPath(dbName, tableName, colName))
