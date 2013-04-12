from helpers import *


class Reader(object):

    def get_name(self, raw, offset):
        if offset == -1:
            return ""
        length = bytes_to_short('\x00' + raw[offset:offset + 1])
        return bytes_to_string(raw[offset + 1:offset + 1 + length])

    def get_data(self, raw, offset):
        length = bytes_to_int(raw[offset:offset + 4])
        return raw[offset + 4:offset + 4 + length]

    def parse(self, rawData):
        resources = {}

        header = rawData[0:16]

        dataOffset = bytes_to_int(header[0:0 + 4])
        mapOffset = bytes_to_int(header[4:8])
        dataLength = bytes_to_int(header[8:12])
        mapLength = bytes_to_int(header[12:16])

        data = rawData[dataOffset:dataOffset + dataLength]

        map = rawData[mapOffset:mapOffset + mapLength]

        nameOffset = bytes_to_short(map[26:28])
        numTypes = bytes_to_short(map[28:30])

        typeLength = 8 * (numTypes + 1)
        # the part of the header that tells us the offset lies
        rawTypes = map[30:30 + typeLength]
        rawList = map[30 + typeLength:nameOffset]
        rawNames = map[nameOffset:]

        types = {}
        for i in range(numTypes):
            name = bytes_to_string(rawTypes[8 * i:(8 * i) + 4])
            number = bytes_to_short(rawTypes[(8 * i) + 4:(8 * i) + 6]) + 1
            offset = bytes_to_short(rawTypes[(8 * i) + 6:(8 * i) + 8])

            types[name] = {'offset': offset, 'number': number}

        list = {}
        for k, v in types.iteritems():
            # Offset supplied is wrong
            realOffset = ((v['offset'] - typeLength) - 2)
            rawResources = rawList[realOffset:realOffset +
                                   ((v['number']) * 12)]
            list[k] = {}

            for i in range(v['number']):
                off = i * 12
                id = bytes_to_short(rawResources[off:off + 2])
                nameOffset = bytes_to_short(rawResources[off + 2:off + 4])
                # Data offset is 3 bytes long, need an extra one
                dataOffset = bytes_to_int("\x00" +
                                          rawResources[off + 5:off + 8])
                list[k][id] = {
                    'nameOffset': nameOffset,
                    'dataOffset': dataOffset
                }

        for type, definitions in list.iteritems():
            resources[type] = {}

            for id, offsets in definitions.iteritems():
                resource = {
                    'name': self.get_name(rawNames, offsets['nameOffset']),
                    'data': self.get_data(data, offsets['dataOffset'])
                }
                resources[type][id] = resource

        return resources
