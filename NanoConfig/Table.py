# Project imports
import NanoConfig.Index
import NanoConfig.Column
import NanoTypes
from NanoBlocks._VariableMemoryBlock import VariableMemoryBlock

class Config(VariableMemoryBlock):
    # Class Attributes
    name = None
    columns = None
    indices = None
    rowSize = None

    # VariableMemoryBlock definitions
    fields = [
        'name',
        'rowSize',
        'columns',
        'indices',
    ]
    dataTypes = {
        'name': VariableMemoryBlock.SerializableString,
        'rowSize': NanoTypes.Uint(4),
        'columns': VariableMemoryBlock.SerializableClass(NanoConfig.Column.Config),
        'indices': VariableMemoryBlock.SerializableClass(NanoConfig.Index.Config),
    }
    iterableFields = [
        'columns',
        'indices',
    ]
