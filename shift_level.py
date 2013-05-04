import argparse
import re

class Shifter (object):
    def __init__(self, x_offset=0.0, z_offset=0.0):
        self.x_offset = x_offset
        self.z_offset = z_offset

    def shift(self, match):
        x = match.group(1)
        z = match.group(2)
        out = match.group(0)
        out = out.replace(x, str(float(x) - self.x_offset))
        out = out.replace(z, str(float(z) - self.z_offset))
        return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=open)
    parser.add_argument('x_offset', type=float, metavar='x-offset')
    parser.add_argument('z_offset', type=float, metavar='z-offset')

    args = parser.parse_args()
    level_out = args.file.read()
    shifter = Shifter(args.x_offset, args.z_offset)

    # Perform x/z shifts.
    level_out = re.sub(r'location="([0-9\.\-]+),[0-9\.\-]+,([0-9\.\-]+)"', shifter.shift, level_out)
    level_out = re.sub(r'center="([0-9\.\-]+),[0-9\.\-]+,([0-9\.\-]+)"', shifter.shift, level_out)
    level_out = re.sub(r'base="([0-9\.\-]+),[0-9\.\-]+,([0-9\.\-]+)"', shifter.shift, level_out)
    level_out = re.sub(r'top="([0-9\.\-]+),[0-9\.\-]+,([0-9\.\-]+)"', shifter.shift, level_out)

    # Clean up unnecesssary decimal places.
    level_out = re.sub(r'\.0,', ',', level_out)
    level_out = re.sub(r'\.0"', '"', level_out)

    print level_out
