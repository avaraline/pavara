import operations
import struct


def bytes_to_short(bytes):
    return struct.unpack('>h', bytes)[0]


def bytes_to_int(bytes):
    return struct.unpack('>i', bytes)[0]


def parse(pict):
    # The first 40 bytes are header information
    if bytes_to_int(pict[10:14]) != 0x001102ff:
        print "ERROR: Not a version 2 PICT"
        return

    data = pict[40:]

    ops = []
    while len(data) > 0:
        opcode = bytes_to_short(data[:2])
        op = operations.Factory.get_op(opcode)
        if op is None:
            print 'ERROR: Unknown opcode ' + str(hex(opcode))
            return ops
        data = data[2:]

        length = op.get_length()

        op.parse(data[:length])
        data = data[length:]

        if isinstance(op, operations.VariableLengthOperation):
            vari_length = op.get_variable_length()
            op.parse_variable(data[:vari_length])
            data = data[vari_length:]

        ops.append(op)
 
    return ops
