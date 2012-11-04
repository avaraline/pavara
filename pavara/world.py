from pandac.PandaModules import *
from panda3d.ode import *
from pavara.utils.geom import make_box, make_dome, to_cartesian, make_square
from pavara.assets import load_model

DEFAULT_AMBIENT_COLOR = (0.4, 0.4, 0.4, 1)
DEFAULT_GROUND_COLOR =  (0.75, 0.5, 0.25, 1)
DEFAULT_SKY_COLOR =     (0.7, 0.8, 1, 1)
DEFAULT_HORIZON_COLOR = (1, 0.8, 0, 1)
DEFAULT_HORIZON_SCALE = 0.05

MAP_COLLIDE_BIT =       BitMask32.bit(1)
GROUND_COLLIDE_BIT =    BitMask32.bit(2)
HECTOR_COLLIDE_BIT =    BitMask32.bit(3)
FREESOLID_COLLIDE_BIT = BitMask32.bit(4)

class WorldObject (object):
    """
    Base class for anything attached to a World.
    """

    world = None
    last_unique_id = 0

    def __init__(self, name=None):
        self.name = name
        if not self.name:
            WorldObject.last_unique_id += 1
            self.name = '%s:%d' % (self.__class__.__name__, WorldObject.last_unique_id)

    def __repr__(self):
        return self.name

    def attached(self, world):
        """
        Called when this object is actually attached to a World. By this time, self.world will have been set.
        """
        pass

    def detached(self, world):
        """
        """
        pass

class PhysicalObject (WorldObject):
    """
    A WorldObject subclass that represents a physical object; i.e. one that is visible and may have an associated
    solid (OdeGeom) for physics collisions.
    """

    node = None
    solid = None
    collidable = False
    collide_bits = HECTOR_COLLIDE_BIT | FREESOLID_COLLIDE_BIT
    collide_category = MAP_COLLIDE_BIT

    def create_node(self, world):
        """
        Called by World.attach to create a NodePath that will be re-parented to the World's render.
        """
        pass

    def create_solid(self, physics, space):
        """
        Called by World.attach to create any necessary physics geometry.
        """
        pass

    def collision(self, other):
        """
        Called when this object is collidable, and collides with another collidable object.
        """
        pass

    def rotate(self, yaw, pitch, roll):
        """
        Programmatically rotate this object by the given yaw, pitch, and roll.
        """
        self.node.set_hpr(self.node, yaw, pitch, roll)
        self.sync_physics()

    def move(self, center):
        """
        Programmatically move this object to be centered at the given coordinates.
        """
        self.node.set_pos(*center)
        self.sync_physics()

    def sync_physics(self):
        """
        Updates the location and quaternion of the associated physics solid to match the visible node.
        """
        if self.solid and self.node:
            self.solid.set_position(self.node.get_pos(self.world.render))
            self.solid.set_quaternion(self.node.get_quat(self.world.render))

    def set_collidable(self, collidable):
        """
        Sets this object as being collidable or not (i.e. whether the collision will be called).
        """
        if self.collidable:
            self.world.collidables.remove(self)
        else:
            self.world.collidables.append(self)
        self.collidable = collidable

class Hector (PhysicalObject):

    collidable = True
    collide_bits = MAP_COLLIDE_BIT | GROUND_COLLIDE_BIT | FREESOLID_COLLIDE_BIT
    collide_category = HECTOR_COLLIDE_BIT

    def __init__(self):
        super(Hector, self).__init__()

    def create_node(self, world):
        from direct.actor.Actor import Actor
        actor = Actor('hector.egg')
        #aactor.setScale(3.0)
        return actor

    def create_solid(self, physics, space):
        return OdeTriMeshGeom(space, OdeTriMeshData(self.node, True))

    def collision(self, other):
        print 'HECTOR HIT BY', other

class Block (PhysicalObject):
    """
    A block. Blocks with non-zero mass will be treated as freesolids.
    """

    def __init__(self, size, color, mass, name=None):
        super(Block, self).__init__(name)
        self.size = size
        self.color = color
        self.mass = mass

    def create_node(self, world):
        return NodePath(make_box(self.color, (0, 0, 0), *self.size))

    def create_solid(self, physics, space):
        geom = OdeBoxGeom(space, self.size[0], self.size[1], self.size[2])
        if self.mass > 0.0:
            self.collidable = True
            self.collide_bits = MAP_COLLIDE_BIT | GROUND_COLLIDE_BIT | HECTOR_COLLIDE_BIT | FREESOLID_COLLIDE_BIT
            self.collide_category = FREESOLID_COLLIDE_BIT
            body = OdeBody(physics)
            mass = OdeMass()
            mass.set_box(self.mass, self.size[0], self.size[1], self.size[2])
            body.set_mass(mass)
            geom.set_body(body)
        return geom

class Dome (PhysicalObject):
    """
    A dome.
    """

    def __init__(self, radius, color, name=None):
        super(Dome, self).__init__(name)
        self.radius = radius
        self.color = color

    def create_node(self, world):
        return NodePath(make_dome(self.color, self.radius, 8, 5))

    def create_solid(self, physics, space):
        return OdeTriMeshGeom(space, OdeTriMeshData(self.node, True))

class Ground (PhysicalObject):
    """
    The ground. This is not a visible object, but does create a physical solid.
    """

    collide_bits = HECTOR_COLLIDE_BIT | FREESOLID_COLLIDE_BIT
    collide_category = GROUND_COLLIDE_BIT

    def __init__(self, radius, color, name=None):
        super(Ground, self).__init__(name)
        self.color = color

    def create_solid(self, physics, space):
        return OdePlaneGeom(space, Vec4(0, 1, 0, 0))

    def attached(self, world):
        # We need to tell the sky shader what color we are.
        self.world.sky.set_ground(self.color)

class Ramp (PhysicalObject):
    """
    A ramp. Basically a block that is rotated, and specified differently in XML. Should maybe be a Block subclass?
    """

    def __init__(self, base, top, width, thickness, color, name=None):
        super(Ramp, self).__init__(name)
        self.base = Point3(*base)
        self.top = Point3(*top)
        self.thickness = thickness
        self.color = color
        self.width = width
        self.length = (self.top - self.base).length()

    def create_node(self, world):
        return NodePath(make_box(self.color, (0, 0, 0), self.thickness, self.width, self.length))

    def create_solid(self, physics, space):
        return OdeBoxGeom(space, self.thickness or 0.001, self.width, self.length)

    def attached(self, world):
        # Do the block rotation after we've been attached (i.e. have a NodePath), so we can use node.look_at.
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
        self.sync_physics()

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

    def attached(self, world):
        geom = GeomNode('sky')
        bounds = self.world.camera.node().get_lens().make_bounds()
        dl = bounds.getMin()
        ur = bounds.getMax()
        z = dl.getZ() * 0.99
        geom.add_geom(make_square((1, 1, 1, 1), dl.getX(), dl.getY(), 0, ur.getX(), ur.getY(), 0))
        self.node = self.world.render.attach_new_node(geom)
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

class World (object):
    """
    The World models basically everything about a map, including gravity, ambient light, the sky, and all map objects.
    """

    def __init__(self, camera):
        self.objects = {}
        self.collidables = []
        self.render = NodePath('world')
        self.camera = camera
        self.ambient = self._make_ambient()
        self.sky = self.attach(Sky())
        # Set up the physics world. TODO: let maps set gravity.
        self.physics = OdeWorld()
        self.physics.set_gravity(0, -9.81, 0)
        self.physics.init_surface_table(1)
        self.physics.set_surface_entry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
        # Set up the physics collision space.
        self.space = OdeSimpleSpace()
        self.space.set_auto_collide_world(self.physics)
        self.space.set_collision_event('space_collision')
        # Set up the contact joints.
        self.contacts = OdeJointGroup()
        self.space.set_auto_collide_joint_group(self.contacts)
        # Register a collision event handler.
        base.accept('space_collision', self.handle_collision)

    def _make_ambient(self):
        alight = AmbientLight('ambient')
        alight.set_color(VBase4(*DEFAULT_AMBIENT_COLOR))
        node = self.render.attach_new_node(alight)
        self.render.set_light(node)
        return node

    def attach(self, obj):
        assert isinstance(obj, WorldObject)
        assert obj.name not in self.objects
        obj.world = self
        if isinstance(obj, PhysicalObject):
            # Let each object define it's own NodePath, then reparent them.
            obj.node = obj.create_node(self)
            if obj.node:
                obj.node.reparent_to(self.render)
            # Create the physical solid.
            obj.solid = obj.create_solid(self.physics, self.space)
            if obj.solid:
                if obj.collidable:
                    self.collidables.append(obj)
                if obj.collide_bits is not None:
                    obj.solid.set_collide_bits(obj.collide_bits)
                if obj.collide_category is not None:
                    obj.solid.set_category_bits(obj.collide_category)
                # Update the physics to match the visible node location.
                obj.sync_physics()
        self.objects[obj.name] = obj
        # Let the object know it has been attached.
        obj.attached(self)
        return obj

    def set_ambient(self, color):
        """
        Sets the ambient light to the given color.
        """
        self.ambient.node().set_color(VBase4(*color))

    def add_celestial(self, azimuth, elevation, color, intensity, radius, visible):
        """
        Adds a celestial light source to the scene. If it is a visible celestial, also add a sphere model.
        """
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

    def update(self, task):
        """
        Called every frame to update the physics, etc.
        """
        dt = globalClock.getDt()
        self.space.auto_collide()
        self.physics.quick_step(dt)
        for name, obj in self.objects.iteritems():
            # If the object is a freesolid (i.e. has a solid with an attached body), update the visible node to match
            # the location/rotation from the physics simulation.
            if isinstance(obj, PhysicalObject) and obj.solid and obj.solid.has_body():
                obj.node.set_pos_quat(self.render, obj.solid.get_position(), Quat(obj.solid.get_quaternion()))
        self.contacts.empty()
        return task.cont

    def handle_collision(self, entry):
        obj1 = None
        obj2 = None
        geom1 = entry.get_geom1()
        geom2 = entry.get_geom2()
        # For some reason, the OdeGeoms are not hashable (or are separate instances), and I can't find an appropriate
        # unique ID to use as a hash. So we do it the slow way, and search a list for the geoms (since == works).
        for obj in self.collidables:
            if obj.solid == geom1:
                obj1 = obj
            if obj.solid == geom2:
                obj2 = obj
            if obj1 and obj2:
                break
        if obj1 and obj2:
            obj1.collision(obj2)
            obj2.collision(obj1)
