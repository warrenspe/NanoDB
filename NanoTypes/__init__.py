# Standard imports
import os, importlib, re, inspect

# Project imports
from Int import Int
from Char import Char
from Float import Float
from Uint import Uint
from Varchar import Varchar

# Globals
TYPE_NAME_RE = re.compile("(\D+)(\d+)?")
TYPES = {
    'int': Int,
    'char': Char,
    'float': Float,
    'uint': Uint,
    'varchar': Varchar,
}
for name, typeClass in TYPES.items():
    globals()[name.lower()] = typeClass


def getType(typeString):
    match = TYPE_NAME_RE.match(typeString)
    if match is not None:
        typeName, quantifier = match.groups()
        typeName = typeName.lower()
        
        if typeName in TYPES:
            return globals()[typeName](quantifier)

    raise TypeError("%s is not a valid type" % typeString)
