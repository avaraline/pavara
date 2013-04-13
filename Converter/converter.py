from decimal import *
from datatypes import *
from lxml import etree as ET


def heading_from_arc(startAngle, angle):
    heading = ((startAngle + angle) / 2) + 180
    while(heading >= 360):
        heading -= 360

    return heading


class Converter:
    SCALE = 8

    def __init__(self):
        self.name = None
        self.tagline = None
        self.author = None
        self.description = None

        self.goodies = []
        self.incarnators = []
        self.teleporters = []
        self.static = []

        self.wall_height = 3
        self.wa = 0
        self.base_height = 0

        self.fg_color = Color()
        self.cur_block = None
        self.cur_arc = None
        self.last_rect = None

        self.origin_x = 0
        self.origin_y = 0

        self.origin_changed = False

    def get_wall_points_from_rect(self, rect):
        size = Point3D()
        center = Point3D()

        # Assuming here that source is always top left
        # and dest is always bottom right seems to be
        # true based on all PICTs checked
        #
        # Also assuming that the 'size' is the full
        # length/width/height, not halved
        #
        # Swapping the z and y around as well as we're now in
        # 3D space

        getcontext().prec = 4
        real_src_x = Decimal(rect.src.x + self.origin_x) / Decimal(Converter.SCALE)
        real_src_y = Decimal(rect.src.y + self.origin_y) / Decimal(Converter.SCALE)
        real_dst_x = Decimal(rect.dst.x + self.origin_x) / Decimal(Converter.SCALE)
        real_dst_y = Decimal(rect.dst.y + self.origin_y) / Decimal(Converter.SCALE)
        size.x = (real_dst_x - real_src_x)
        size.z = (real_dst_y - real_src_y)
        size.y = self.wall_height
        center.x = Decimal(real_src_x + real_dst_x) / Decimal(2)
        center.z = Decimal(real_src_y + real_dst_y) / Decimal(2)
        center.y = Decimal(self.wall_height + self.wa) / Decimal(2)

        # Reset wa because it's a per wall variable
        self.wa = 0

        return size, center

    def convert(self, ops):
        getcontext().prec = 3

        for op in ops:
            classname = op.__class__.__name__
            if classname == "ClipRegion":
                self.cur_region = op.region
            elif classname == "Origin":
                print "Origin changed"
                self.origin_x -= op.dv
                self.origin_y -= op.dh
                self.origin_changed = True
            elif classname == "RGBForegroundColor":
                self.fg_color = Color.from_rgb(op.red, op.green, op.blue)
            elif classname == "FrameRectangle":
                if self.origin_changed:
                    self.origin_changed = False
                block = self.create_block(op.rect)
                self.cur_block = block
                self.static.append(block)
            elif classname == "PaintRectangle":
                if self.origin_changed:
                    self.origin_changed = False
                block = self.create_block(op.rect)
                self.cur_block = block
                self.cur_block.color = self.fg_color
                print block
                print self.cur_block.color
            elif classname == "FrameSameRectangle":
                if self.origin_changed:
                    self.origin_changed = False
                    self.cur_block = self.create_block(self.last_rect)
                print "Framing last"
                print self.cur_block
                print self.cur_block.color
                self.static.append(self.cur_block)
            elif classname == "PaintSameRectangle":
                if self.origin_changed:
                    self.origin_changed = False
                    self.cur_block = self.create_block(self.last_rect)
                self.cur_block.color = self.fg_color

        print self.goodies
        print self.incarnators
        print self.teleporters

        staticEl = ET.Element('static')
        for static in self.static:
            static.to_xml(staticEl)

        ET.dump(staticEl)

    def create_block(self, rect):
        self.last_rect = rect
        block = Block()
        size, center = self.get_wall_points_from_rect(rect)
        block.size = size
        block.center = center
        return block
