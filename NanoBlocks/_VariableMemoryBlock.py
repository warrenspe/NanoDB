# Project imports
import NanoTypes

class VariableMemoryBlock:
    """
    Class which provides toString and fromString functionality to subclasses which should be serializable while not
    conforming to strict sizing requirements.

    Stores fields as follows:
        4 bytes: number of bytes required to serialize this field
        X bytes: Serialized version of this field
    """

    # Private Variables

    # DataType which is used to serialize the `numBytes` field preceeding each item in self.fields
    _sizeDataType = NanoTypes.Uint(4)

    # Subclassable Variables

    # List of fields on self that should be serialized in the file
    fields = None
    # Dictionary mapping fieldName to the dataType to convert to from the raw string representation
    dataTypes = None
    # List of fields which are stored as iterables
    iterableFields = None

    ###
    # Variable Memory DataType classes
    #
    # Classes which can be used as dataTypes when constructing new VariableMemoryBlock subclasses
    ###

    class SerializableString:
        """ DataType which can be used to serialize variables as variable lengthed strings. """

        @staticmethod
        def toString(s):
            return str(s) if s else ""

        @staticmethod
        def fromString(s):
            return s


    class SerializableClass:
        """
        DataType which can be used to wrap classes that define toString & fromString methods as types.

        Classes must be instantiable requiring no arguments.
        """

        classType = None

        def __init__(self, classType):
            self.classType = classType

        def toString(self, classInstance):
            return classInstance.toString() if classInstance else ""

        def fromString(self, s):
            classInstance = self.classType()
            if s:
                classInstance.fromString(s)
            return classInstance


    # Private methods
    def __serializeAttribute(self, fieldName, value):
        serializedVal = self.dataTypes[fieldName].toString(value)
        return self._sizeDataType.toString(len(serializedVal)) + serializedVal


    def __getFromBlock(self, fromDataType, idx, numBytes, s):
        """
        Pulls an object out of s.

        Inputs: fromDataType - The dataType to use to fromString the substring of s.
                idx          - The index to begin the substring of s.
                numBytes     - The number of bytes to extract from s.
                s            - The block to extract the substring from.

        Returns: (The Object fromString'd from the block, The index after reading from s)
        """

        if len(s) < idx + numBytes:
            raise Exception("Given string len(%s) is not long enough to unserialize %s" % (len(s), self))

        return fromDataType.fromString(s[idx: idx + numBytes]), idx + numBytes


    # Public methods
    def toString(self):
        """
        Returns a string representation of this object suitable for writing to a file.
        """

        # List of serialized fields
        toSerialize = []

        for fieldName in self.fields:
            attrVal = getattr(self, fieldName)

            # If this field has been marked as iterable
            if self.iterableFields and fieldName in self.iterableFields:
                # Ensure this variable is actually iterable
                if not hasattr(attrVal, '__iter__'):
                    toSerialize.append(self._sizeDataType.toString(0))

                else:
                    toSerialize.append("".join(
                        # Serialize the length of the iterable
                        [self._sizeDataType.toString(len(attrVal))] +
                        # Serialize each item of the iterable
                        [self.__serializeAttribute(fieldName, val) for val in attrVal]
                    ))

            # Otherwise serialize the attribute as a single value
            else:
                toSerialize.append(self.__serializeAttribute(fieldName, attrVal))

        return "".join(toSerialize)


    def fromString(self, s):
        """
        Initializes this object from the data found in s.

        Inputs: s - A string containing the data to initialize this instance with.

        Raises an error if s contains insufficient memory to initialize all fields in self.fields, or
        if it contains extra bytes not required to initialize all fields in self.fields.
        """

        # Current index into s
        idx = 0

        for fieldName in self.fields:
            # Get the number of bytes to initialize this field with
            fieldLength, idx = self.__getFromBlock(self._sizeDataType, idx, self._sizeDataType.size, s)

            # If this field has been marked as iterable
            if self.iterableFields and fieldName in self.iterableFields:
                setattr(self, fieldName, [])
                for i in range(fieldLength):
                    itemLength, idx = self.__getFromBlock(self._sizeDataType, idx, self._sizeDataType.size, s)
                    fieldVal, idx = self.__getFromBlock(self.dataTypes[fieldName], idx, itemLength, s)
                    getattr(self, fieldName).append(fieldVal)

            # Otherwise unserialize this single value
            else:
                fieldVal, idx = self.__getFromBlock(self.dataTypes[fieldName], idx, fieldLength, s)
                setattr(self, fieldName, fieldVal)

        if len(s) > idx:
            raise Exception("Given string len(%s) too long to unserialize %s" % (len(s), self))

        return self

