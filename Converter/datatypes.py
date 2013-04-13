from decimal import *
from lxml import etree as ET


class Color (object):
    red = 1
    green = 1
    blue = 1

    @staticmethod
    def from_rgb(r, g, b):
        """
        Quick function to convert from PICT's int based
        RGB values to Pavara's decimal based
        """
        color = Color()
        color.red = Decimal(r) / Decimal(65535)
        color.green = Decimal(g) / Decimal(65535)
        color.blue = Decimal(b) / Decimal(65535)

        return color

    def __str__(self):
        return (str(self.red) + "," +
                str(self.green) + "," +
                str(self.blue))


class Point3D(object):
    x = 0
    y = 0
    z = 0

    def __str__(self):
        return (str(self.x) + "," +
                str(self.y) + "," +
                str(self.z))


class Block (object):
    size = Point3D()
    center = Point3D()
    color = Color()

    def to_xml(self, tree):
        el = ET.SubElement(tree, "block")
        el.set('size', str(self.size))
        el.set('center', str(self.center))
        el.set('color', str(self.color))


class Ramp (object):
    base = Point3D()
    top = Point3D()
    width = 0
    thickness = 0


class Goodie (object):
    location = Point3D()
    grenade = 0
    missiles = 0
    respawn = 0
    model = Point3D()
    spin = Point3D()


class Incarnator (object):
    location = Point3D()
    heading = 0