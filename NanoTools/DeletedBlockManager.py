# Standard imports
import os

# Project imports
import NanoTypes
import NanoIO.File

POINTER_TYPE = NanoTypes.Uint(8)

class DeletedBlockManager:
    fd = None
    name = None
    db = None

    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.fd = NanoIO.File.openReadWriteFile(NanoIO.File.delMgrPath(db, name))


    def __del__(self):
        try:
            self.close()
        except AttributeError:
            pass


    def truncate(self):
        self.fd.seek(0)
        self.fd.truncate()


    def close(self):
        self.fd.close()


    def addRef(self, val):
        self.fd.write(POINTER_TYPE.toString(val))


    def popRef(self):
        self.fd.seek(0, os.SEEK_END)
        if self.fd.tell() == 0:
            return None
        self.fd.seek(-POINTER_TYPE.size, os.SEEK_END)
        ret = self.fd.read()
        self.fd.seek(-POINTER_TYPE.size, os.SEEK_END)
        self.fd.truncate()
        return POINTER_TYPE.fromString(ret)
