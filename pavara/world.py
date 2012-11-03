from pandac.PandaModules import *
from pavara.utils.geom import make_box, make_dome, to_cartesian, make_square
from pavara.assets import load_model

DEFAULT_AMBIENT_COLOR = (0.4, 0.4, 0.4, 1)
DEFAULT_GROUND_COLOR = (0.75, 0.5, 0.25, 1)
DEFAULT_SKY_COLOR = (0.7, 0.8, 1, 1)
DEFAULT_HORIZON_COLOR = (1, 0.8, 0, 1)
DEFAULT_HORIZON_SCALE = 0.05

class WorldObject (object):
    """
    """

    last_unique_id = 0

    def __init__(self, name=None):
        self.name = name
        if not self.name:
            WorldObject.last_unique_id += 1
            self.name = '%s:%d' % (self.__class__.__name__, WorldObject.last_unique_id)

    def attached(self, world):
        # TODO: subclass or mix-in to handle adding physics here?
        pass

    def detached(self, world):
        pass


class PhysicalObject (WorldObject):
    geom = None
    node = None
    solid = None

    def rotate(self, yaw, pitch, roll):
        self.node.set_hpr(self.node, yaw, pitch, roll)

    def move(self, center):
        self.node.set_pos(*center)

class Block (PhysicalObject):
    """
    """

    def __init__(self, size, color, name=None):
        super(Block, self).__init__(name)
        self.geom = make_box(color, (0,0,0), *size)

class Dome (PhysicalObject):
    """
    """

    def __init__(self, radius, color, name=None):
        super(Dome, self).__init__(name)
        self.geom = make_dome(color, radius, 8, 5)

class Ground (PhysicalObject):
    """
    """

    def __init__(self, radius, color, name=None):
        super(Ground, self).__init__(name)
        self.color = color
        #self.geom = make_box(color, (0, 0, 0), radius, 0.5, radius)
        self.solid = CollisionPlane(Plane(Vec3(0, 1, 0), Point3(0, 0, 0)))

    def attached(self, world):
        world.sky.set_ground(self.color)

class Ramp (PhysicalObject):
    """
    """

    def __init__(self, base, top, width, thickness, color, name=None):
        super(Ramp, self).__init__(name)
        self.base = Point3(*base)
        self.top = Point3(*top)
        self.thickness = thickness
        distance = self.top - self.base
        length = distance.length()
        self.geom = make_box(color, (0,0,0), thickness, width, length)

    def orientate(self):
        v1 = self.top - self.base
        if self.base.get_x() != self.top.get_x():
            p3 = Point3(self.top.get_x()+100, self.top.get_y(), self.top.get_z())
        else:
            p3 = Point3(self.top.get_x(), self.top.get_y(), self.top.get_z() + 100)
        v2 = self.top - p3
        up = v1.cross(v2)
        up.normalize()
        midpoint = Point3((self.base + self.top) / 2.0)
        self.node.set_pos(midpoint)
        self.node.look_at(self.top, up)

class Incarnator (WorldObject):
    """
    """

    def __init__(self, pos, angle):
        WorldObject.__init__(self, 'Incarnator')
        self.pos = pos
        self.angle = angle
        self.h = None

    def placeHector(self, render):
        self.h = Hector(render, self.pos[0], self.pos[1], self.pos[2], self.angle)

class Sky (WorldObject):

    def __init__(self, ground=DEFAULT_GROUND_COLOR, color=DEFAULT_SKY_COLOR, horizon=DEFAULT_HORIZON_COLOR, scale=DEFAULT_HORIZON_SCALE):
        super(Sky, self).__init__('sky')
        self.ground = ground
        self.color = color
        self.horizon = horizon
        self.scale = scale

    def attached(self, world):
        geom = GeomNode('sky')
        bounds = world.camera.node().get_lens().make_bounds()
        dl = bounds.getMin()
        ur = bounds.getMax()
        z = dl.getZ() * 0.99
        geom.add_geom(make_square((1, 1, 1, 1), dl.getX(), dl.getY(), 0, ur.getX(), ur.getY(), 0))
        self.node = world.render.attach_new_node(geom)
        self.node.set_shader(Shader.load('Shaders/Sky.sha'))
        self.node.set_shader_input('camera', world.camera)
        self.node.set_shader_input('sky', self.node)
        self.node.set_shader_input('groundColor', *self.ground)
        self.node.set_shader_input('skyColor', *self.color)
        self.node.set_shader_input('horizonColor', *self.horizon)
        self.node.set_shader_input('gradientHeight', self.scale, 0, 0, 0)
        self.node.reparent_to(world.camera)
        self.node.set_pos(world.camera, 0, 0, z)

    def set_ground(self, color):
        self.ground = color
        self.node.set_shader_input('groundColor', *self.ground)

    def set_color(self, color):
        self.color = color
        self.node.set_shader_input('skyColor', *self.color)

    def set_horizon(self, color):
        self.horizon = color
        self.node.set_shader_input('horizonColor', *self.horizon)

    def set_scale(self, height):
        self.scale = height
        self.node.set_shader_input('gradientHeight', self.scale, 0, 0, 0)

class World (object):
    """
    """

    def __init__(self, camera):
        self.objects = {}
        self.solids = []
        self.render = NodePath('world')
        self.camera = camera
#        self.pm = PhysicsManager()
        self.ambient = self._make_ambient()
        self.sky = self.attach(Sky())

    def _make_ambient(self):
        alight = AmbientLight('ambient')
        alight.set_color(VBase4(*DEFAULT_AMBIENT_COLOR))
        node = self.render.attach_new_node(alight)
        self.render.set_light(node)
        return node

    def attach(self, obj):
        assert isinstance(obj, WorldObject)
        assert obj.name not in self.objects
        if isinstance(obj, PhysicalObject):
            if obj.geom:
                obj.node = self.render.attach_new_node(obj.geom)
            if obj.solid:
                self.solids.append(obj.solid)
        self.objects[obj.name] = obj
        obj.attached(self)
        return obj

    def set_ambient(self, color):
        self.ambient.node().set_color(VBase4(*color))

    def add_celestial(self, azimuth, elevation, color, intensity, radius, visible):
        location = Vec3(to_cartesian(azimuth, elevation, 1000.0 * 255.0 / 256.0))
        dlight = DirectionalLight('celestial')
        dlight.set_color((color[0]*intensity, color[1]*intensity, color[2]*intensity, 1.0))
        node = self.render.attach_new_node(dlight)
        node.look_at(*(location * -1))
        self.render.set_light(node)
        if visible:
            sphere = load_model('misc/sphere')
            sphere.set_transparency(TransparencyAttrib.MAlpha)
            sphere.reparent_to(self.render)
            sphere.set_light_off()
            sphere.set_effect(CompassEffect.make(self.camera, CompassEffect.PPos))
            sphere.set_scale(45*radius)
            sphere.set_color(*color)
            sphere.set_pos(location)
