#!/usr/bin/python

# Standard imports
import unittest, argparse, sys, os, glob

sys.path.append('.')

# Project imports
import NanoIO.File

# Globals
TEST_DIR = "NanoTests"

class NanoTestCase(unittest.TestCase):
    dbName = "NanoDBUnitTests"

    @classmethod
    def tearDownClass(cls):
        # Clear the testing database
        for f in glob.glob(os.path.join(NanoIO.File.dbPath(cls.dbName), '*')):
            os.remove(f)


def run(verbosity=1):
    loader = unittest.TestLoader()
    suite = loader.discover(TEST_DIR)
    _runSuite(suite, verbosity)

def runSelective(testFiles, verbosity):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(["%s.test_%s" % (TEST_DIR, testFile) for testFile in testFiles])
    _runSuite(suite, verbosity)

def _runSuite(testSuite, verbosity):
    if not NanoIO.File.checkDatabaseExists(NanoTestCase.dbName):
        NanoIO.File.createDatabase(NanoTestCase.dbName)
    try:
        unittest.TextTestRunner(verbosity=verbosity).run(testSuite)
    finally:
        NanoIO.File.deleteDatabase(NanoTestCase.dbName)
    raw_input("\nPress enter to close.")

def main():
    parser = argparse.ArgumentParser(description="Execute NanoDB Unit Tests")
    parser.add_argument("testFiles", nargs="*")
    parser.add_argument("--verbosity", nargs="?", choices=['1', '2'], default=1)
    args = parser.parse_args()

    # NanoConfig loads configuration by default; we want this to occur after we consume our cmdline args.
    import NanoConfig

    if len(args.testFiles):
        runSelective(args.testFiles, int(args.verbosity))
    else:
        run(int(args.verbosity))

if __name__ == '__main__':
    main()
