import datatypes
import struct


def bytes_to_short(bytes):
    return struct.unpack('>h', bytes)[0]


class Operation (object):
    length = 0

    def get_length(self):
        """
        Returns the length (in bytes) of the static data of this
        operation
        """
        return self.length

    def parse(self, bytes):
        pass


class VariableLengthOperation (Operation):
    vari_length = 0

    def parse_variable(self, bytes):
        pass

    def get_variable_length(self):
        return self.vari_length


class NOP (Operation):
    pass


class ClipRegion (VariableLengthOperation):
    length = 2

    def parse(self, bytes):
        self.vari_length = bytes_to_short(bytes) - 2

    def parse_variable(self, bytes):
        self.rect = datatypes.Rect(bytes)


class BackgroundPattern (Operation):
    length = 8


class FrameRectangle (Operation):
    length = 8

    def parse(self, bytes):
        self.rect = datatypes.Rect(bytes)


class ShortComment (Operation):
    length = 2

    def parse(self, bytes):
        self.kind = bytes_to_short(bytes)


class Factory (object):
    opcodes = {
        0x0000: NOP,
        0x0001: ClipRegion,
        0x0002: BackgroundPattern,
        #"0003": TextFont,
        #"0004": TextFace,
        0x0030: FrameRectangle,
        0x00a0: ShortComment
    }

    @staticmethod
    def get_op(opcode):
        if opcode not in Factory.opcodes:
            return None

        return Factory.opcodes[opcode]()


