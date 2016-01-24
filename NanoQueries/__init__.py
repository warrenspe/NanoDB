# Standard imports
import os, importlib

for queryType in os.listdir("NanoQueries"):
    if queryType[0] != "_" and queryType[-3:] == ".py":
        module = importlib.import_module("NanoQueries.%s" % queryType[:-3])
        globals()[queryType[:-3]] = getattr(module, queryType[:-3])
