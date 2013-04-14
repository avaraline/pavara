from decimal import *
from datatypes import *
from lxml import etree as ET
import shlex


def heading_from_arc(startAngle, angle):
        heading = (startAngle + (angle / 2)) + 180

        while(heading >= 360):
            heading -= 360

        return heading


class Converter:
    SCALE = 25

    def __init__(self):
        self.name = None
        self.tagline = None
        self.author = None
        self.description = None

        self.goodies = []
        self.incarnators = []
        self.teleporters = []
        self.blocks = []
        self.ramps = []

        self.wall_height = 3
        self.wa = 0
        self.base_height = 0

        self.fg_color = Color()
        self.cur_block = None
        self.cur_arc = None
        self.cur_object = False
        self.last_rect = None
        self.last_arc = None
        self.next_objects = []

        self.origin_x = 0
        self.origin_y = 0

        self.block_origin_changed = False
        self.arc_origin_changed = False

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

        getcontext().prec = 10
        real_src_x = Decimal(Decimal(rect.src.x + self.origin_x) / Decimal(Converter.SCALE)).quantize(Decimal('.1'))
        real_src_y = Decimal(Decimal(rect.src.y + self.origin_y) / Decimal(Converter.SCALE)).quantize(Decimal('.1'))
        real_dst_x = Decimal(Decimal(rect.dst.x + self.origin_x) / Decimal(Converter.SCALE)).quantize(Decimal('.1'))
        real_dst_y = Decimal(Decimal(rect.dst.y + self.origin_y) / Decimal(Converter.SCALE)).quantize(Decimal('.1'))
        size.x = (real_dst_x - real_src_x)
        size.z = (real_dst_y - real_src_y)
        size.y = self.wall_height
        center.x = Decimal(real_src_x + real_dst_x) / Decimal(2)
        center.z = Decimal(real_src_y + real_dst_y) / Decimal(2)
        center.y = (Decimal(self.wall_height) / Decimal(2)) + self.wa + self.base_height

        # Reset wa because it's a per wall variable
        self.wa = 0

        return size, center

    def convert(self, ops):
        getcontext().prec = 3
        lastText = False
        for op in ops:
            classname = op.__class__.__name__

            if (classname == "LongText" or
                    classname == "DHText" or
                    classname == "DVText" or
                    classname == "DHDVText"):
                thisText = True
            else:
                thisText = False
                if lastText:
                    self.parse_text(self.cur_text)

            if classname == "ClipRegion":
                self.cur_region = op.region
            elif classname == "Origin":
                self.origin_x -= op.dv
                self.origin_y -= op.dh
                self.block_origin_changed = True
                self.arc_origin_changed = True
            elif classname == "RGBForegroundColor":
                self.fg_color = Color.from_rgb(op.red, op.green, op.blue)
            elif classname == "FrameRectangle":
                if self.block_origin_changed:
                    self.block_origin_changed = False
                block = self.create_block(op.rect)
                self.cur_block = block
                self.blocks.append(block)
            elif classname == "PaintRectangle":
                if self.block_origin_changed:
                    self.block_origin_changed = False
                block = self.create_block(op.rect)
                self.cur_block = block
                self.cur_block.color = self.fg_color

            # A note for Frame/Paint Same Rectangle:
            # If the origin point changes and then one
            # of these is called, it means use the same
            # rectangle dimensions from the new origin point
            elif classname == "FrameSameRectangle":
                if self.block_origin_changed:
                    self.block_origin_changed = False
                    self.cur_block = self.create_block(self.last_rect)
                self.blocks.append(self.cur_block)
            elif classname == "PaintSameRectangle":
                if self.block_origin_changed:
                    self.block_origin_changed = False
                    self.cur_block = self.create_block(self.last_rect)
                self.cur_block.color = self.fg_color

            elif classname == "FrameArc":
                if self.arc_origin_changed:
                    self.arc_origin_changed = False
                self.cur_arc = self.create_arc(op.rect, op.startAngle, op.arcAngle)
                self.cur_arc.stroke = self.fg_color
            elif classname == "PaintArc":
                if self.arc_origin_changed:
                    self.arc_origin_changed = False
                self.cur_arc = self.create_arc(op.rect, op.startAngle, op.arcAngle)
                self.cur_arc.fill = self.fg_color

            # The same Arc functions can result in different
            # arcs if the angles are different
            elif classname == "FrameSameArc":
                if self.arc_origin_changed:
                    self.arc_origin_changed = False
                    self.cur_arc = self.create_arc(self.last_arc, op.startAngle, op.arcAngle)
                else:
                    heading = heading_from_arc(op.startAngle, op.arcAngle)
                    if self.cur_arc.heading is not heading:
                        self.cur_arc = self.create_arc(self.last_arc, op.startAngle, op.arcAngle)

                self.cur_arc.stroke = self.fg_color

            elif classname == "PaintSameArc":
                if self.arc_origin_changed:
                    self.arc_origin_changed = False
                    self.cur_arc = self.create_arc(self.last_arc, op.startAngle, op.arcAngle)
                else:
                    heading = heading_from_arc(op.startAngle, op.arcAngle)
                    if self.cur_arc.heading is not heading:
                        self.cur_arc = self.create_arc(self.last_arc, op.startAngle, op.arcAngle)

                self.cur_arc.fill = self.fg_color

            elif thisText:
                if lastText:
                    self.cur_text += " " + op.text
                else:
                    self.cur_text = op.text

            if thisText:
                lastText = True
            else:
                lastText = False

        mapEl = ET.Element('map')

        for inc in self.incarnators:
            inc.to_xml(mapEl)

        staticEl = ET.SubElement(mapEl, 'static')
        for static in self.blocks:
            static.to_xml(staticEl)

        for static in self.ramps:
            static.to_xml(staticEl)

        for good in self.goodies:
            good.to_xml(mapEl)

        ET.dump(mapEl)

    def create_block(self, rect):
        self.last_rect = rect
        block = Block()
        size, center = self.get_wall_points_from_rect(rect)
        block.size = size
        block.center = center
        return block

    def create_arc(self, rect, startAngle, arcAngle):
        arc = Arc()
        center = Point3D()
        self.last_arc = rect

        getcontext().prec = 10
        real_src_x = Decimal(Decimal(rect.src.x + self.origin_x) / Decimal(Converter.SCALE)).quantize(Decimal('.1'))
        real_src_y = Decimal(Decimal(rect.src.y + self.origin_y) / Decimal(Converter.SCALE)).quantize(Decimal('.1'))
        real_dst_x = Decimal(Decimal(rect.dst.x + self.origin_x) / Decimal(Converter.SCALE)).quantize(Decimal('.1'))
        real_dst_y = Decimal(Decimal(rect.dst.y + self.origin_y) / Decimal(Converter.SCALE)).quantize(Decimal('.1'))

        center.x = Decimal(real_src_x + real_dst_x) / Decimal(2)
        center.z = Decimal(real_src_y + real_dst_y) / Decimal(2)
        center.y = self.base_height
        arc.center = center
        arc.heading = heading_from_arc(startAngle, arcAngle)

        return arc

    def parse_text(self, text):
        in_unique = False
        in_object = False
        in_adjust = False
        cur_object = {}
        variable = None

        for word in shlex.split(text):
            if word == "unique":
                in_unique = True
            elif word == "object":
                in_object = True
            elif word == "adjust":
                in_adjust = True
            elif word == "end":
                if in_unique:
                    in_unique = False
                elif in_object:
                    in_object = False
                    self.parse_object(cur_object)
                    cur_object = {}
                elif in_adjust:
                    in_adjust = False
            elif in_object:
                if len(cur_object) == 0:
                    cur_object['type'] = word
                elif variable is None:
                    variable = word
                elif word is not "=":
                    cur_object[variable] = word
                    variable = None
            elif in_unique:
                # Do nothing
                pass
            elif in_adjust:
                self.parse_adjust(word)
            elif variable is None:
                variable = word
            elif word is not "=":
                self.parse_global_variable(variable, word)
                variable = None

    def parse_global_variable(self, key, value):
        if key == 'wa':
            self.wa = Decimal(value)
        elif key == 'wallHeight':
            self.wall_height = Decimal(value)
        elif key == 'baseHeight':
            self.base_height = Decimal(value)
        elif key == 'designer':
            self.author = value
        elif key == 'information':
            self.tagline = value

    def parse_adjust(self, word):
        pass    # need to handle ground/sky colours

    def parse_object(self, object):

        type = object['type']
        if type == "Incarnator":
            inc = Incarnator()
            inc.location = self.cur_arc.center
            if 'y' in object:
                inc.location.y += Decimal(object['y'])
            inc.heading = self.cur_arc.heading
            self.incarnators.append(inc)
        elif type == "Goody":
            good = Goody()
            good.location = self.cur_arc.center

            if 'y' in object:
                good.location.y += Decimal(object['y'])

            if 'grenades' in object:
                good.grenades = object['grenades']

            if 'missiles' in object:
                good.missiles = object['missiles']

            if 'shape' in object:
                good.model = self.translate_model(object['shape'])

            if 'speed' in object:
                good.spin.x = object['speed']

            self.goodies.append(good)
        elif type == "Ramp":
            ramp = Ramp()
            block = self.blocks.pop()
            arc = self.cur_arc
            deltaY = Decimal(object['deltaY'])
            ramp.color = block.color

            if 'y' in object:
                y = Decimal(object['y'])
            else:
                y = Decimal(0)

            if arc.heading > 315 or arc.heading <= 45:
                ramp.width = block.size.z

                ramp.base.x = block.center.x - (block.size.x / Decimal(2))
                ramp.base.y = y + self.base_height
                ramp.base.z = block.center.z

                ramp.top.x = block.center.x + (block.size.x / Decimal(2))
                ramp.top.y = y + self.base_height + deltaY
                ramp.top.z = block.center.z

            elif arc.heading > 45 and arc.heading <= 135:
                ramp.width = block.size.x

                ramp.base.x = block.center.x
                ramp.base.y = y + self.base_height
                ramp.base.z = block.center.z + (block.size.z / Decimal(2))

                ramp.top.x = block.center.x
                ramp.top.y = y + self.base_height + deltaY
                ramp.top.z = block.center.z - (block.size.z / Decimal(2))

            elif arc.heading > 135 and arc.heading <= 225:
                ramp.width = block.size.z

                ramp.base.x = block.center.x + (block.size.x / Decimal(2))
                ramp.base.y = y + self.base_height
                ramp.base.z = block.center.z

                ramp.top.x = block.center.x - (block.size.x / Decimal(2))
                ramp.top.y = y + self.base_height + deltaY
                ramp.top.z = block.center.z

            else:
                ramp.width = block.size.x

                ramp.base.x = block.center.x
                ramp.base.y = y + self.base_height
                ramp.base.z = block.center.z - (block.size.z / Decimal(2))

                ramp.top.x = block.center.x
                ramp.top.y = y + self.base_height + deltaY
                ramp.top.z = block.center.z + (block.size.z / Decimal(2))

            if 'thickness' in object:
                ramp.thickness = object['thickness']
            else:
                ramp.thickness = block.rounding

            self.ramps.append(ramp)

    def translate_model(self, shape):
        models = {
            'bspMissile': 'Missile',
            'bspGrenade': 'Grenade'
        }

        if shape in models:
            return models[shape]

        return 'StandardPill'
