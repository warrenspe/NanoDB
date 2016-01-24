# Project imports
from NanoBlocks._VariableMemoryBlock import VariableMemoryBlock

class Config(VariableMemoryBlock):
    # Class Attributes
    name = None
    typeString = None

    # VariableMemoryBlock definitions
    fields = [
        'name',
        'typeString'
    ]
    dataTypes = {
        'name': VariableMemoryBlock.SerializableString,
        'typeString': VariableMemoryBlock.SerializableString,
    }

