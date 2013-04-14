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
    SCALE = Decimal(18)
    SNAP = Decimal('.01')

    def __init__(self):
        self.name = None           # Stores the map name
        self.tagline = None        # Map tagline
        self.author = None         # Map author
        self.description = None    # Map description

        self.goodies = []          # List of all goodies
        self.incarnators = []      # List of all incarnators
        self.teleporters = []      # List of all teleporters
        self.blocks = []           # List of all static blocks
        self.ramps = []            # List of all static ramps

        self.wall_height = 3       # Current wall height (default 3)
        self.wa = 0                # Current wa, resets after every wall
        self.base_height = 0       # Current base height

        self.fg_color = Color()    # Last foreground colour
        self.cur_block = None      # Last created block
        self.cur_arc = None        # Last arc
        self.last_rect = None      # Last Rect used on a block
        self.last_arc = None       # Last Rect used for an arc

        self.origin_x = 0          # Current origin x
        self.origin_y = 0          # Current origin y

        self.pen_x = 1             # Current pen x
        self.pen_y = 1             # Current pen y

        # When the origin is changed some PICT calls
        # mean different things, thus why we store
        # data on different 'types' of origin change
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

        real_src_x = (rect.src.x + self.origin_x)
        real_src_y = (rect.src.y + self.origin_y)
        real_dst_x = (rect.dst.x + self.origin_x)
        real_dst_y = (rect.dst.y + self.origin_y)
        size.x = Decimal(real_dst_x - real_src_x) - self.pen_x
        size.z = Decimal(real_dst_y - real_src_y) - self.pen_y
        size.y = Decimal(self.wall_height)
        center.x = Decimal(real_src_x + real_dst_x) / Decimal(2)
        center.z = Decimal(real_src_y + real_dst_y) / Decimal(2)
        center.y = (Decimal(self.wall_height) / Decimal(2)) + self.wa + self.base_height
        size.x = self.scale_and_snap(size.x)
        size.z = self.scale_and_snap(size.z)

        center.x = self.scale_and_snap(center.x)
        center.z = self.scale_and_snap(center.z)
        # Reset wa because it's a per wall variable
        self.wa = 0

        return size, center

    def convert(self, ops):
        getcontext().prec = 10
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
            elif classname == "PenSize":
                self.pen_x = op.size.x
                self.pen_y = op.size.y
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

                self.last_rect = op.rect
                self.block_color = self.fg_color

            # A note for Frame/Paint Same Rectangle:
            # If the origin point changes and then one
            # of these is called, it means use the same
            # rectangle dimensions from the new origin point
            elif classname == "FrameSameRectangle":
                self.cur_block = self.create_block(self.last_rect)
                if self.block_origin_changed:
                    self.block_origin_changed = False
                else:
                    self.cur_block.color = self.block_color
                self.blocks.append(self.cur_block)
            elif classname == "PaintSameRectangle":
                if self.block_origin_changed:
                    self.block_origin_changed = False

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

        real_src_x = rect.src.x + self.origin_x
        real_src_y = rect.src.y + self.origin_y
        real_dst_x = rect.dst.x + self.origin_x
        real_dst_y = rect.dst.y + self.origin_y

        center.x = Decimal(real_src_x + real_dst_x) / Decimal(2)
        center.z = Decimal(real_src_y + real_dst_y) / Decimal(2)
        center.y = self.base_height

        center.x = self.scale_and_snap(center.x)
        center.z = self.scale_and_snap(center.z)

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

            if 'thickness' in object:
                ramp.thickness = object['thickness']
            else:
                ramp.thickness = block.rounding

            if deltaY == 0:
                block.size.y = ramp.thickness
                block.center.y = y + self.base_height
                self.blocks.append(block)
                return

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

            self.ramps.append(ramp)

    def scale_and_snap(self, dec):
        return (dec / Converter.SCALE).quantize(Converter.SNAP)

    def translate_model(self, shape):
        models = {
            'bspMissile': 'Missile',
            'bspGrenade': 'Grenade'
        }

        if shape in models:
            return models[shape]

        return 'StandardPill'
