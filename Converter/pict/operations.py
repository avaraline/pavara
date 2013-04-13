import datatypes
from Converter.helpers import *


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


class Reserved(VariableLengthOperation):
    length = 2

    def parse(self, bytes):
        self.vari_length = bytes_to_short(bytes)


class NOP (Operation):
    pass


class ClipRegion (VariableLengthOperation):
    length = 2

    def parse(self, bytes):
        self.vari_length = bytes_to_short(bytes) - 2

    def parse_variable(self, bytes):
        self.rect = datatypes.Rect(bytes)


class TextFont (Operation):
    length = 2

    def parse(self, bytes):
        self.font = bytes_to_short(bytes)


class PenSize (Operation):
    length = 4

    def parse(self, bytes):
        self.size = datatypes.Point(bytes)


class PenMode (Operation):
    length = 2

    def parse(self, bytes):
        self.mode = bytes_to_short(bytes)


class TextSize (Operation):
    length = 2

    def parse(self, bytes):
        self.size = bytes_to_short(bytes)


class TextRatio (Operation):
    length = 8

    def parse(self, bytes):
        self.numerator = datatypes.Point(bytes[0:4])
        self.denominator = datatypes.Point(bytes[4:8])


class ShortLine (Operation):
    length = 6

    def parse(self, bytes):
        self.start = datatypes.Point(bytes)
        self.dh = byte_to_signed_tiny_int(bytes[2:3])
        self.dv = byte_to_signed_tiny_int(bytes[3:4])


class LongText (VariableLengthOperation):
    length = 5

    def parse(self, bytes):
        self.loc = datatypes.Point(bytes[0:4])
        self.vari_length = byte_to_unsigned_tiny_int(bytes[4:5])+1

    def parse_variable(self, bytes):
        self.text = bytes_to_string(bytes)


class FrameRectangle (Operation):
    length = 8

    def parse(self, bytes):
        self.rect = datatypes.Rect(bytes)


class ShortComment (Operation):
    length = 2

    def parse(self, bytes):
        self.kind = bytes_to_short(bytes)


class LongComment (VariableLengthOperation):
    length = 4

    def parse(self, bytes):
        self.kind = bytes_to_short(bytes[0:2])
        self.vari_length = bytes_to_short(bytes[2:4])

    def parse_variable(self, bytes):
        self.comment = bytes_to_string(bytes)


class Factory (object):
    opcodes = {
        0x0: NOP,
        0x1: ClipRegion,
        #0x2: BackgroundPattern,
        0x3: TextFont,
        #"0003": TextFont,
        #"0004": TextFace,
        0x7: PenSize,
        0x8: PenMode,
        0xd: TextSize,
        0x10: TextRatio,
        0x22: ShortLine,
        0x28: LongText,
        0x2c: Reserved,
        0x2e: Reserved,
        0x30: FrameRectangle,
        0xa0: ShortComment,
        0xa1: LongComment
    }

    @staticmethod
    def get_op(opcode):
        if opcode not in Factory.opcodes:
            return None

        return Factory.opcodes[opcode]()


