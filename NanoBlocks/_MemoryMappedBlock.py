# Project imports
import NanoTypes._BaseType as BaseType

class MemoryMappedBlock:
    """
    Class which provides toString and fromString functionality to subclasses representing
    fixed memory blocks in the database.
    """

    # Number of bytes we expect to be in a block
    blockSize = None
    # List of fieldNames in the order they should appear in the block
    fields = None
    # Dictionary mapping fieldName to the dataType to convert to from the raw string representation
    dataTypes = None
    # Set of fields which should be treated as an iterable of datatypes.
    iterableFields = None
    # Dictionary mapping list-fieldName to a UInt which will be used to stored the length of the list immediately
    # prior to serializing the list itself
    iterableFieldNumItemsDataType = None
    # Dictionary mapping iterableFields to the maximum size of the field in the block.
    iterableFieldSizes = None

    ###
    # Memory Mapped DataType classes
    #
    # Classes which can be used as dataTypes when constructing new MemoryMappedBlock subclasses
    ###

    class MemoryMappedClass(BaseType.Type):
        """
        Type which can serialize a MemoryMappedBlock subclass instance as though it were a type.

        Requires that the class may be instantiated with no arguments.
        """

        indexable = False
        classDef = None
        size = None

        def __init__(self, classDef):
            self.classDef = classDef
            self.size = self.classDef.blockSize

        def _toString(self, val):
            return val.toString()


        def _fromString(self, val):
            return self.classDef().fromString(val)


        def isValid(self, val):
            return isinstance(val, self.classDef)


    # Public methods
    def toString(self):
        """
        Returns a string representation of this object suitable for writing to a file.
        """

        fieldsToSerialize = []
        for fieldName in self.fields:
            if self.iterableFields and fieldName in self.iterableFields:
                toSerialize = "".join([
                    # Serialize the number of items in the list
                    self.iterableFieldNumItemsDataType[fieldName].toString(len(getattr(self, fieldName))),
                    # Serialize the list
                    "".join([self.dataTypes[fieldName].toString(val) for val in getattr(self, fieldName)])
                ])
                fieldSize = self.iterableFieldNumItemsDataType[fieldName].size + self.iterableFieldSizes[fieldName]

            else:
                toSerialize = self.dataTypes[fieldName].toString(getattr(self, fieldName))
                fieldSize = self.dataTypes[fieldName].size

            fieldsToSerialize.append(toSerialize.ljust(fieldSize, '\x00'))

        toReturn = "".join(fieldsToSerialize)

        if len(toReturn) > self.blockSize:
            raise Exception("Error toString'ing %s; length of block generated: %s; longer than expected: %s"
                             % (self, len(toReturn), self.blockSize))

        return toReturn.ljust(self.blockSize, '\x00')


    def fromString(self, block):
        """
        Initializes this object with data from the given block of data.
        """

        if len(block) != self.blockSize:
            raise Exception("Cannot fromString block of length: %s; expecting len(%s)" % (len(block), self.blockSize))

        fieldStart = 0
        for fieldName in self.fields:
            if self.iterableFields and fieldName in self.iterableFields:
                # Get the length of the list to create
                numItemsDataType = self.iterableFieldNumItemsDataType[fieldName]
                numItems = numItemsDataType.fromString(block[fieldStart: fieldStart + numItemsDataType.size])
                fieldStart += numItemsDataType.size

                # Get the list
                fieldSize = self.iterableFieldSizes[fieldName]
                fieldEnd = fieldStart + (self.dataTypes[fieldName].size * numItems)
                fieldValue = map(lambda x: self.dataTypes[fieldName].fromString(''.join(x)),
                                 zip(*[
                                     iter(block[fieldStart:fieldEnd])
                                 ] * self.dataTypes[fieldName].size)
                             )

            else:
                fieldSize = self.dataTypes[fieldName].size
                fieldValue = self.dataTypes[fieldName].fromString(block[fieldStart: fieldStart + fieldSize])

            # Increment fieldStart so we can grab the next block
            fieldStart += fieldSize
            # Set this value on self
            setattr(self, fieldName, fieldValue)

        return self

