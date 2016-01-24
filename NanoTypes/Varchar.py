# Project imports
import _BasePointerType as BasePointerType
import Uint

ADDRESS_TYPE = Uint.Uint(8)

class Varchar(BasePointerType.PointerType):

    def _toString(self, val):
        return val


    def _fromString(self, val):
        return val
