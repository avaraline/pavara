from Converter import resource
from Converter.converter import Converter
import Converter.pict.reader as pReader

import argparse
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', metavar='file')

    args = parser.parse_args()

    f = open(args.file + '/..namedfork/rsrc', 'rb')
    data = f.read()
    if(len(data) == 0):
        print "No resource fork!"
        sys.exit(1)

    reader = resource.Reader()
    resources = reader.parse(data)

    for pict in resources['PICT'].values():
        ops = pReader.parse(pict['data'])
        conv = Converter()
        conv.convert(ops)
