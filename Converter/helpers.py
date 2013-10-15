import struct


def bytes_to_int(bytes):
    return struct.unpack('>i', bytes)[0]


def bytes_to_short(bytes):
    return struct.unpack('>h', bytes)[0]


def bytes_to_unsigned_short(bytes):
    return struct.unpack('>H', bytes)[0]


def bytes_to_string(bytes):
    return struct.unpack('>' + str(len(bytes)) + 's', bytes)[0]


def byte_to_unsigned_tiny_int(byte):
    return struct.unpack('>h', '\x00' + byte)[0]


def byte_to_signed_tiny_int(byte):
    num = byte_to_unsigned_tiny_int(byte)
    if num > 127:
        return 0 - num
    return num
