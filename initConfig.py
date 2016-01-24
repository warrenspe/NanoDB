"""
File which attempts to determine the best configuration options for the users system
"""

# Standard imports
import os, ConfigParser, time, random

# Project imports
import NanoConfig
import NanoConfig.Index
import NanoConfig.Column
import NanoIO.File
import NanoIO.Index

CONFIG_NAME = 'Nano.cfg'
TEMP_DB_NAME = 'initConfigSandbox'
RAND_SEED = 123

cfgFD = NanoIO.File.openReadWriteFile(CONFIG_NAME)

# Create a config writer
confWriter = ConfigParser.RawConfigParser()
confWriter.read(CONFIG_NAME) # Attempt to read anything that may already exist in the configuration.

if not confWriter.has_section('config'):
    confWriter.add_section('config')
if not confWriter.has_option('config', 'root_dir'):
    confWriter.set('config', 'root_dir', os.path.abspath(os.path.join(os.path.dirname(__file__), 'dbs')))

NanoConfig.root_dir = confWriter.get('config', 'root_dir')

# Create a test `database`
try:
    NanoIO.File.deleteDatabase(TEMP_DB_NAME)
except IOError:
    pass
NanoIO.File.createDatabase(TEMP_DB_NAME)


# Calculate max_num_dirty_blocks & index_block_size
def testConfig(mnd, ibs):
    runTimes = []
    for i in range(5):
        colConfig = NanoConfig.Column.Config()
        colConfig.name = 'testCol'
        colConfig.typeString = 'int4'
        idxConfig = NanoConfig.Index.Config()
        idxConfig.column = colConfig
        NanoIO.File.deleteIndex(TEMP_DB_NAME, 'temp', 'testCol')
        NanoIO.File.createIndex(TEMP_DB_NAME, 'temp', 'testCol')
        index = NanoIO.Index.IndexIO(TEMP_DB_NAME, 'temp', idxConfig)
        random.seed(RAND_SEED)
        start = time.time()
        for i in range(1000):
            index.add(random.randint(-1000, 1000), random.randint(0, 1000))
        runTimes.append(time.time() - start)
    return sum(runTimes) / float(len(runTimes))

ibs = 256
mnd = 10
minAvg = 0
for tempMND in range(10, 55, 5):
    for tempIBS in range(256, 512, 64):
        NanoConfig.max_num_dirty_blocks = tempMND
        NanoConfig.index_block_size = tempIBS
        avg = testConfig(tempMND, tempIBS)
        if minAvg == 0 or avg < minAvg:
            ibs = tempIBS
            mnd = tempMND
            minAvg = avg


confWriter.set('config', 'max_num_dirty_blocks', mnd)
confWriter.set('config', 'index_block_size', ibs)

confWriter.write(cfgFD)

NanoIO.File.deleteDatabase(TEMP_DB_NAME)
