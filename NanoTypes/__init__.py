# Standard imports
import os, importlib, re, inspect

# Project imports
import _BaseType
import _BasePointerType

# Globals
TYPE_NAME_RE = re.compile("(\D+)(\d+)?")
TYPES = dict()
POINTER_TYPES = dict()

for queryType in os.listdir("NanoTypes"):
    if queryType[0] != "_" and queryType[-3:] == ".py":
        module = importlib.import_module("NanoTypes.%s" % queryType[:-3])
        for itemName in dir(module):
            itemVal = getattr(module, itemName)
            if inspect.isclass(itemVal):
                if issubclass(itemVal, _BaseType.Type):
                    TYPES[itemName] = itemVal
                elif issubclass(itemVal, _BasePointerType.PointerType):
                    POINTER_TYPES[itemName] = itemVal
                else:
                    continue
                globals()[itemName] = itemVal

def getType(typeString, fd=None):
    match = TYPE_NAME_RE.match(typeString)
    if match is not None:
        typeName, quantifier = match.groups()
        typeName = typeName.title()
        
        if typeName in TYPES:
            return globals()[typeName](quantifier)
        elif typeName in POINTER_TYPES:
            if fd is None:
                raise Exception("Cannot initialize pointer type %s without a file descriptor." % typeString)
            return globals()[typeName](fd)

    raise TypeError("%s is not a valid type" % typeString)
