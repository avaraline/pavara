from decimal import *
from lxml import etree as ET


class Color (object):

    def __init__(self):
        self.red = 1
        self.green = 1
        self.blue = 1

    @staticmethod
    def from_rgb(r, g, b):
        """
        Quick function to convert from PICT's int based
        RGB values to Pavara's decimal based
        """
        color = Color()
        color.red = (Decimal(r) / Decimal(65535)).quantize(Decimal('0.001'))
        color.green = (Decimal(g) / Decimal(65535)).quantize(Decimal('0.001'))
        color.blue = (Decimal(b) / Decimal(65535)).quantize(Decimal('0.001'))

        return color

    def __str__(self):
        return (str(self.red) + "," +
                str(self.green) + "," +
                str(self.blue))


class Point3D(object):

    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def __str__(self):
        return (str(self.x) + "," +
                str(self.y) + "," +
                str(self.z))


class Arc (object):

    def __init__(self):
        self.fill = Color()
        self.stroke = Color()
        self.heading = 0
        self.center = Point3D()


class Block (object):

    def __init__(self):
        self.size = Point3D()
        self.center = Point3D()
        self.color = Color()
        self.rounding = 0

    def to_xml(self, tree):
        el = ET.SubElement(tree, "block")
        el.set('size', str(self.size))
        el.set('center', str(self.center))
        el.set('color', str(self.color))


class Ramp (object):

    def __init__(self):
        self.base = Point3D()
        self.top = Point3D()
        self.width = 0
        self.thickness = 0
        self.color = Color()

    def to_xml(self, tree):
        if self.thickness > 0:
            el = ET.SubElement(tree, "blockramp")
            el.set('thickness', str(self.thickness))
        else:
            el = ET.SubElement(tree, 'ramp')
        el.set('base', str(self.base))
        el.set('top', str(self.top))
        el.set('width', str(self.width))
        el.set('color', str(self.color))


class Goody (object):

    def __init__(self):
        self.location = Point3D()
        self.grenades = 0
        self.missiles = 0
        self.respawn = 30
        self.model = None
        self.spin = Point3D()

    def to_xml(self, tree):
        el = ET.SubElement(tree, "goody")
        el.set('location', str(self.location))
        el.set('grenades', str(self.grenades))
        el.set('missiles', str(self.missiles))
        el.set('respawn', str(self.respawn))
        el.set('spin', str(self.spin))
        el.set('model', str(self.model))


class Incarnator (object):

    def __init__(self):
        self.location = Point3D()
        self.heading = 0

    def to_xml(self, tree):
        el = ET.SubElement(tree, "incarnator")
        el.set('location', str(self.location))
        el.set('heading', str(self.heading))

class SkyColor(object):

    def __init__(self):
        self.horizon = Color()
        self.color = Color()

    def to_xml(self, tree):
        el = ET.SubElement(tree, "sky")
        el.set("horizon", str(self.horizon))
        el.set("color", str(self.color))


class GroundColor (object):

    def __init__(self):
        self.color = Color()

    def to_xml(self, tree):
        el = ET.SubElement(tree, "ground")
        el.set("color", str(self.color))
