# Project imports
import NanoTypes
import NanoConfig.Column
from NanoBlocks._VariableMemoryBlock import VariableMemoryBlock

class Config(VariableMemoryBlock):
    # Class Attributes
    column = None
    unique = None # TODO implement - raise error if multiple added

    # VariableMemoryMappedBlock definitions
    fields = [
        'column',
        'unique',
    ]
    dataTypes = {
        'column': VariableMemoryBlock.SerializableClass(NanoConfig.Column.Config),
        'unique': NanoTypes.Uint(1),
    }

