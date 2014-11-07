from pavara.base_objects import *
from pavara.utils.geom import GeomBuilder, to_cartesian
from panda3d.core import Shader, NodePath, LRotationf, LRotation, TransformState, Point2, Point3, Vec2, Vec3
from pavara.assets import load_model
from panda3d.bullet import BulletBoxShape, BulletGhostNode, BulletSphereShape, BulletPlaneShape, BulletRigidBodyNode, BulletConvexHullShape
from direct.actor.Actor import Actor
import math

class Block (PhysicalObject):
    """
    A block.
    """

    def __init__(self, size, color, mass, center, hpr, name=None):
        super(Block, self).__init__(name)
        self.size = size
        self.color = color
        self.mass = mass
        self.center = center
        self.hpr = hpr

    def create_node(self):
        return NodePath(GeomBuilder('block').add_block(self.color, (0, 0, 0), self.size).get_geom_node())

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        node.add_shape(BulletBoxShape(Vec3(self.size[0] / 2.0, self.size[1] / 2.0, self.size[2] / 2.0)))
        return node

    def add_solid(self, node):
        node.add_shape(BulletBoxShape(Vec3(self.size[0] / 2.0, self.size[1] / 2.0, self.size[2] / 2.0)), TransformState.make_pos_hpr(Point3(*self.center), self.hpr))

    def add_to(self, geom_builder):
        rot = LRotationf()
        rot.set_hpr(self.hpr)
        geom_builder.add_block(self.color, self.center, self.size, rot)

    def attached(self):
        self.move(self.center)
        self.rotate(*self.hpr)

class Ramp (PhysicalObject):
    """
    A ramp.
    """

    def __init__(self, base, top, width, thickness, color, mass, hpr, name=None):
        super(Ramp, self).__init__(name)
        self.base = Point3(*base)
        self.top = Point3(*top)
        self.width = width
        self.thickness = thickness
        self.color = color
        self.mass = mass
        self.hpr = hpr
        self.midpoint = Point3((self.base + self.top) / 2.0)

    def create_node(self):
        rel_base = Point3(self.base - (self.midpoint - Point3(0, 0, 0)))
        rel_top = Point3(self.top - (self.midpoint - Point3(0, 0, 0)))
        self.geom = GeomBuilder().add_ramp(self.color, rel_base, rel_top, self.width, self.thickness).get_geom_node()
        return NodePath(self.geom)

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        mesh = BulletConvexHullShape()
        mesh.add_geom(self.geom.get_geom(0))
        node.add_shape(mesh)
        return node

    def add_solid(self, node):
        mesh = BulletConvexHullShape()
        mesh.add_geom(GeomBuilder().add_ramp(self.color, self.base, self.top, self.width, self.thickness, LRotationf(*self.hpr)).get_geom())
        node.add_shape(mesh)
        return node

    def add_to(self, geom_builder):
        geom_builder.add_ramp(self.color, self.base, self.top, self.width, self.thickness, LRotationf(*self.hpr))

    def attached(self):
        self.move(self.midpoint)
        self.rotate(*self.hpr)

class Wedge (PhysicalObject):
    """
    Ramps with some SERIOUS 'tude.
    """

    def __init__(self, base, top, width, color, mass, hpr, name=None):
        super(Wedge, self).__init__(name)
        self.base = Point3(*base)
        self.top = Point3(*top)
        self.width = width
        self.color = color
        self.mass = mass
        self.hpr = hpr
        self.midpoint = Point3((self.base + self.top) / 2.0)

    def create_node(self):
        rel_base = Point3(self.base - (self.midpoint - Point3(0, 0, 0)))
        rel_top = Point3(self.top - (self.midpoint - Point3(0, 0, 0)))
        self.geom = GeomBuilder().add_wedge(self.color, rel_base, rel_top, self.width).get_geom_node()
        return NodePath(self.geom)

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        mesh = BulletConvexHullShape()
        mesh.add_geom(self.geom.get_geom(0))
        node.add_shape(mesh)
        return node

    def add_solid(self, node):
        mesh = BulletConvexHullShape()
        mesh.add_geom(GeomBuilder().add_wedge(self.color, self.base, self.top, self.width, LRotationf(*self.hpr)).get_geom())
        node.add_shape(mesh)
        return node

    def add_to(self, geom_builder):
        geom_builder.add_wedge(self.color, self.base, self.top, self.width, LRotationf(*self.hpr))

    def attached(self):
        self.move(self.midpoint)
        self.rotate(*self.hpr)

class BlockRamp (PhysicalObject):
    """
    Old-style ramps like in the original game. Basically just a block that is
    rotated, and specified differently in XML. Should maybe be a Block subclass?
    """

    def __init__(self, base, top, width, thickness, color, mass, hpr, name=None):
        super(BlockRamp, self).__init__(name)
        self.base = Point3(*base)
        self.top = Point3(*top)
        self.width = width
        self.thickness = thickness
        self.__adjust_ends__()
        self.color = color
        self.length = (self.top - self.base).length()
        self.mass = mass
        self.hpr = hpr
        v1 = self.top - self.base
        if self.base.get_x() != self.top.get_x():
            p3 = Point3(self.top.get_x()+100, self.top.get_y(), self.top.get_z())
        else:
            p3 = Point3(self.top.get_x(), self.top.get_y(), self.top.get_z() + 100)
        v2 = self.top - p3
        self.up = v1.cross(v2)
        self.up.normalize()
        self.midpoint = Point3((self.base + self.top) / 2.0)

    def __quadratic__(self, a, b, c):
        sqrt = math.sqrt(b**2.0 - 4.0 * a * c)
        denom = 2.0 * a
        return (-b - sqrt)/denom, (-b + sqrt)/denom

    def __adjust_ends__(self):
        SEARCH_ITERATIONS = 20
        v = self.top - self.base
        l = v.get_xz().length()
        h = abs(v.get_y())
        midx = l / 2.0
        midy = h / 2.0
        maxr = v.length() / 2.0
        minr = max(midx, midy)
        for i in range(0, SEARCH_ITERATIONS):
            r = (maxr - minr)/2.0 + minr
            # r = ((midl - x)**2 + (midh - y)**2)**0.5 substitute 0 for x and solve, then do the same for y. these two values represent the corners of a ramp and the distance between them is thickness.
            miny, maxy = self.__quadratic__(1, -2 * midy, midx**2 + midy**2 - r ** 2)
            minx, maxx = self.__quadratic__(1, -2 * midx, midx**2 + midy**2 - r ** 2)
            d = (minx**2 + miny**2)**0.5
            if d == self.thickness: # yaaaaay
                break
            elif d > self.thickness: # r is too small
                minr = r
            else: # r is too large
                maxr = r
        # x and y should be pretty close to where we want the corners of the ramp to be. the midpoint between them is where we want the base to be.
        leftcorner = Point2(0, miny)
        bottomcorner = Point2(minx, 0)
        newbase = (leftcorner - bottomcorner)/2 + bottomcorner
        midramp = Point2(midx, midy)
        newtop = (midramp - newbase)*2 + newbase
        topxz = v.get_xz()/l*newtop.get_x()
        if int(h) == 0:
            topy = newtop.get_y()
        else:
            topy = v.get_y()/h*newtop.get_y()
        self.top = self.base + (topxz[0], topy, topxz[1])
        bottomxz = v.get_xz()/l*newbase.get_x()
        if int(h) == 0:
            bottomy = newbase.get_y()
        else:
            bottomy = v.get_y()/h*newbase.get_y()
        self.base = self.base + (bottomxz[0], bottomy, bottomxz[1])


    def create_node(self):
        return NodePath(GeomBuilder('ramp').add_block(self.color, (0, 0, 0), (self.thickness, self.width, self.length)).get_geom_node())

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        node.add_shape(BulletBoxShape(Vec3(self.thickness / 2.0, self.width / 2.0, self.length / 2.0)))
        return node

    def add_solid(self, node):
        node.add_shape(BulletBoxShape(Vec3(self.thickness / 2.0, self.width / 2.0, self.length / 2.0)), TransformState.make_pos_hpr(Point3(*self.midpoint), self.hpr))

    def add_to(self, geom_builder):
        # honestly i don't understand this at all
        diff = self.top - self.base
        if diff.get_z() == 0:
            vec2 = diff.get_xy()
            vec2 = Vec2(abs(diff.get_x()), diff.get_y())
            vec1 = Vec2(1, 0)
        else:
            vec1 = diff.get_yz()
            vec1 = Vec2(diff.get_y(), abs(diff.get_z()))
            vec2 = Vec2(0, -1)
        rot = LRotation(diff.get_xz().signedAngleDeg(Vec2(0, -1)), (vec1.signedAngleDeg(vec2) ), 90)
        rot = rot * LRotation(*self.hpr)
        self.hpr = rot.get_hpr()
        geom_builder.add_block(self.color, self.midpoint, (self.thickness, self.width, self.length), rot)

    def attached(self):
        # Do the block rotation after we've been attached (i.e. have a NodePath), so we can use node.look_at.
        self.move(self.midpoint)
        self.node.look_at(self.top, self.up)
        self.rotate_by(*self.hpr)

class Dome (PhysicalObject):
    """
    A dome.
    """

    def __init__(self, radius, samples, planes, color, mass, center, hpr, name=None):
        super(Dome, self).__init__(name)
        self.radius = radius
        self.samples = samples
        self.planes = planes
        self.color = color
        self.mass = mass
        self.center = center
        self.hpr = hpr

    def create_node(self):
        self.geom = GeomBuilder().add_dome(self.color, (0, 0, 0), self.radius, self.samples, self.planes).get_geom_node()
        return NodePath(self.geom)

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        mesh = BulletConvexHullShape()
        mesh.add_geom(self.geom.get_geom(0))
        node.add_shape(mesh)
        return node

    def add_solid(self, node):
        mesh = BulletConvexHullShape()
        mesh.add_geom(GeomBuilder().add_dome(self.color, self.center, self.radius, self.samples, self.planes, LRotationf(*self.hpr)).get_geom())
        node.add_shape(mesh)
        return node

    def add_to(self, geom_builder):
        rot = LRotationf(*self.hpr)
        geom_builder.add_dome(self.color, self.center, self.radius, self.samples, self.planes, rot)

    def attached(self):
        self.move(self.center)
        self.rotate_by(*self.hpr)

class Goody (PhysicalObject):
    def __init__(self, pos, model, items, respawn, spin, name=None):
        super(Goody, self).__init__(name)
        self.pos = Vec3(*pos)
        self.grenades = items[0]
        self.missiles = items[1]
        self.boosters = items[2]
        self.model = model
        self.respawn = respawn
        self.spin = Vec3(*spin)
        self.geom = None
        self.active = True
        self.timeout = 0
        self.spin_bone = None

    def create_node(self):
        if self.model == "Grenade":
            m = Actor('grenade.egg')
            shell = m.find('**/shell')
            shell.setColor(1,.3,.3,1)
            inner_top = m.find('**/inner_top')
            inner_bottom = m.find('**/inner_bottom')
            inner_top.setColor(.4,.4,.4,1)
            inner_bottom.setColor(.4,.4,.4,1)
            self.spin_bone = m.controlJoint(None, 'modelRoot', 'grenade_bone')
            m.set_scale(GRENADE_SCALE)

        elif self.model == "Missile":
            m = load_model('missile.egg')
            body = m.find('**/bodywings')
            body.set_color(.3,.3,1,1)
            main_engines = m.find('**/mainengines')
            wing_engines = m.find('**/wingengines')
            main_engines.set_color(.1,.1,.1,1)
            wing_engines.set_color(.1,.1,.1,1)
            m.set_scale(MISSILE_SCALE)
        else:
            m = load_model('misc/rgbCube')
            m.set_scale(.5)
            m.set_hpr(45,45,45)
        return m

    def create_solid(self):
        node = BulletGhostNode(self.name)
        node_shape = BulletSphereShape(.5)
        node.add_shape(node_shape)
        node.set_kinematic(True)
        return node

    def attached(self):
        self.node.set_pos(self.pos)
        self.world.register_updater(self)
        self.world.register_collider(self)
        self.solid.setIntoCollideMask(GHOST_COLLIDE_BIT)

    def update(self, dt):
        if not self.active:
            self.timeout += dt
            if self.timeout > self.respawn:
                self.active = True
                self.node.show()
                self.timeout = 0
            return
        if self.spin_bone:
            self.spin_bone.set_hpr(self.spin_bone, self.spin[2]*dt, self.spin[1]*dt, self.spin[0]*dt)
        else:
            self.rotate_by(*[x * dt for x in self.spin])
        result = self.world.physics.contact_test(self.solid)
        for contact in result.getContacts():
            node_1 = contact.getNode0()
            node_2 = contact.getNode1()
            if "Walker" in node_2.get_name():
               # TODO: identify which player and credit them with the items.
               self.active = False
               self.node.hide()

class Sky (WorldObject):
    """
    The sky is actually just a square re-parented onto the camera, with a shader to handle the coloring and gradient.
    """

    def __init__(self, ground=DEFAULT_GROUND_COLOR, color=DEFAULT_SKY_COLOR, horizon=DEFAULT_HORIZON_COLOR, scale=DEFAULT_HORIZON_SCALE):
        super(Sky, self).__init__('sky')
        self.ground = ground
        self.color = color
        self.horizon = horizon
        self.scale = scale

    def attached(self):
        if not self.world.camera:
            self.node = self.world.scene.attach_new_node('sky')
            return
        geom = GeomNode('sky')
        bounds = self.world.camera.node().get_lens().make_bounds()
        dl = bounds.getMin()
        ur = bounds.getMax()
        z = dl.getZ() * 0.99

        geom.add_geom(GeomBuilder('sky').add_rect((1, 1, 1, 1), dl.getX(), dl.getY(), 0, ur.getX(), ur.getY(), 0).get_geom())
        self.node = self.world.scene.attach_new_node(geom)
        self.node.set_shader(Shader.load('Shaders/Sky.sha'))
        self.node.set_shader_input('camera', self.world.camera)
        self.node.set_shader_input('sky', self.node)
        self.node.set_shader_input('groundColor', *self.ground)
        self.node.set_shader_input('skyColor', *self.color)
        self.node.set_shader_input('horizonColor', *self.horizon)
        self.node.set_shader_input('gradientHeight', self.scale, 0, 0, 0)
        self.node.reparent_to(self.world.camera)
        self.node.set_pos(self.world.camera, 0, 0, z)

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
    def detach(self):
        self.node.detach_node()

class Ground (PhysicalObject):
    """
    The ground. This is not a visible object, but does create a physical solid.
    """

    def __init__(self, radius, color, name=None):
        super(Ground, self).__init__(name)
        self.color = color

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        node.add_shape(BulletPlaneShape(Vec3(0, 1, 0), 1))
        return node

    def attached(self):
        self.move((0, -1.0, 0))
        # We need to tell the sky shader what color we are.
        self.world.sky.set_ground(self.color)

class Incarnator (PhysicalObject):
    def __init__(self, pos, heading, name=None):
        super(Incarnator, self).__init__(name)
        self.pos = Vec3(*pos)
        self.heading = Vec3(to_cartesian(math.radians(heading), 0, 1000.0 * 255.0 / 256.0)) * -1

    def attached(self):
        self.dummy_node = self.world.scene.attach_new_node("incarnator"+self.name)
        self.dummy_node.set_pos(self.world.scene, self.pos)
        if self.world.audio3d:
            self.sound = self.world.audio3d.loadSfx('Sounds/incarnation_mono.wav')
        else: self.sound = False

    def was_used(self):
        if self.sound:
            self.world.audio3d.attachSoundToObject(self.sound, self.dummy_node)
            self.sound.play()
