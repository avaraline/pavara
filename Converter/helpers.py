import struct


def bytes_to_int(bytes):
    return struct.unpack('>i', bytes)[0]


def bytes_to_short(bytes):
    return struct.unpack('>h', bytes)[0]


def bytes_to_string(bytes):
    return struct.unpack('>' + str(len(bytes)) + 's', bytes)[0]
