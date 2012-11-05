from pandac.PandaModules import *
from panda3d.bullet import *
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

    def attached(self):
        """
        Called when this object is actually attached to a World. By this time, self.world will have been set.
        """
        pass

    def detached(self):
        """
        """
        pass

class PhysicalObject (WorldObject):
    """
    A WorldObject subclass that represents a physical object; i.e. one that is visible and may have an associated
    solid for physics collisions.
    """

    node = None
    solid = None
    collide_bits = BitMask32.all_on()

    def create_node(self):
        """
        Called by World.attach to create a NodePath that will be re-parented to the World's render.
        """
        pass

    def create_solid(self):
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

    def move(self, center):
        """
        Programmatically move this object to be centered at the given coordinates.
        """
        self.node.set_pos(*center)

class Hector (PhysicalObject):

    def __init__(self):
        super(Hector, self).__init__()
        
    def create_node(self):
        from direct.actor.Actor import Actor
        self.actor = Actor('hector.egg')
        self.barrels = self.actor.find("**/barrels")
        self.barrel_trim = self.actor.find("**/barrelTrim")
        self.visor = self.actor.find("**/visor")
        self.hull = self.actor.find("**/hull")
        self.crotch = self.actor.find("**/crotch")
        self.head = self.actor.attachNewNode("hector_head_node")
        self.barrels.reparentTo(self.head)
        self.barrel_trim.reparentTo(self.head)
        self.visor.reparentTo(self.head)
        self.hull.reparentTo(self.head)
        self.crotch.reparentTo(self.head)
        self.left_top = self.actor.find("**/leftTop")
        self.right_top = self.actor.find("**/rightTop")
    	self.left_middle = self.actor.find("**/leftMiddle")
    	self.left_middle.reparentTo(self.left_top)
        self.right_middle = self.actor.find("**/rightMiddle")
        self.right_middle.reparentTo(self.right_top)
    	self.left_bottom = self.actor.find("**/leftBottom")
    	self.left_bottom.reparentTo(self.left_middle)
        self.right_bottom = self.actor.find("**/rightBottom")
        self.right_bottom.reparentTo(self.right_middle)
        return self.actor

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        
        #node.add_shape(self.b_shape_from_node_path(self.visor))
        node.add_shape(self.b_shape_from_node_path(self.hull))
        #node.add_shape(BulletBoxShape(Vec3(.25,.25,.25)))
        #node.add_shape(self.b_shape_from_node_path(self.crotch))
        #node.add_shape(self.b_shape_from_node_path(self.barrels))
        #node.add_shape(self.b_shape_from_node_path(self.barrel_trim))
        #node.add_shape(self.b_shape_from_node_path(self.right_top))
        #node.add_shape(self.b_shape_from_node_path(self.right_middle))
        #node.add_shape(self.b_shape_from_node_path(self.right_bottom))
        #node.add_shape(self.b_shape_from_node_path(self.left_top))
        #node.add_shape(self.b_shape_from_node_path(self.left_middle))
        #node.add_shape(self.b_shape_from_node_path(self.left_bottom))
        node.set_mass(.3)
        return node
    
    def b_shape_from_node_path(self, nodepath):
    	node = nodepath.node()
    	geom = node.getGeom(0)
    	shape = BulletConvexHullShape()
    	shape.addGeom(geom)
    	return shape
    
    def setupColor(self, colordict):
        if colordict.has_key("barrel_color"):
            self.barrels.setColor(*colordict.get("barrel_color"))
        if colordict.has_key("barrel_trim_color"):
    		self.barrel_trim.setColor(*colordict.get("barrel_trim_color"))
        if colordict.has_key("visor_color"):
            self.visor.setColor(*colordict.get("visor_color"))
        if colordict.has_key("body_color"):
            color = colordict.get("body_color")
            self.hull.setColor(*color)
            self.crotch.setColor(*color)
            self.left_top.setColor(*color)
            self.right_top.setColor(*color)
            self.left_middle.setColor(*color)
            self.right_middle.setColor(*color)
            self.left_bottom.setColor(*color)
            self.right_bottom.setColor(*color)
        if colordict.has_key("hull_color"):
            self.hull.setColor(*colordict.get("hull_color"))
            self.crotch.setColor(*colordict.get("hull_color"))
        if colordict.has_key("top_leg_color"):
            color = colordict.get("top_leg_color")
            self.left_top.setColor(*color)
            self.right_top.setColor(*color)
        if colordict.has_key("middle_leg_color"):
            color = colordict.get("middle_leg_color")
            self.left_middle.setColor(*color)
            self.right_middle.setColor(*color)   
        if colordict.has_key("bottom_leg_color"):
            color = colordict.get("bottom_leg_color")
            self.left_bottom.setColor(*color)
            self.right_bottom.setColor(*color)
        return
    
    def attached(self):
        self.node.set_scale(3.0)

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

    def create_node(self):
        return NodePath(make_box(self.color, (0, 0, 0), *self.size))

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        node.add_shape(BulletBoxShape(Vec3(self.size[0] / 2.0, self.size[1] / 2.0, self.size[2] / 2.0)))
        node.set_mass(self.mass)
        return node

class Dome (PhysicalObject):
    """
    A dome.
    """

    def __init__(self, radius, color, name=None):
        super(Dome, self).__init__(name)
        self.radius = radius
        self.color = color
        self.geom = make_dome(self.color, self.radius, 8, 5)

    def create_node(self):
        return NodePath(self.geom)

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        mesh = BulletTriangleMesh()
        mesh.add_geom(self.geom.get_geom(0))
        node.add_shape(BulletTriangleMeshShape(mesh, dynamic=False))
        return node

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

    def create_node(self):
        return NodePath(make_box(self.color, (0, 0, 0), self.thickness, self.width, self.length))

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        node.add_shape(BulletBoxShape(Vec3(self.thickness / 2.0, self.width / 2.0, self.length / 2.0)))
        return node

    def attached(self):
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

    def __init__(self, camera, debug=False):
        self.objects = {}
        self.collidables = {}
        self.render = NodePath('world')
        self.camera = camera
        self.ambient = self._make_ambient()
        self.sky = self.attach(Sky())
        # Set up the physics world. TODO: let maps set gravity.
        self.physics = BulletWorld()
        self.physics.set_gravity(Vec3(0, -9.81, 0))
        if debug:
            debug_node = BulletDebugNode('Debug')
            debug_node.show_wireframe(True)
            debug_node.show_constraints(True)
            debug_node.show_bounding_boxes(False)
            debug_node.show_normals(False)
            np = self.render.attach_new_node(debug_node)
            np.show()
            self.physics.set_debug_node(debug_node)

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
            obj.node = obj.create_node()
            obj.solid = obj.create_solid()
            if obj.solid:
                if isinstance(obj.solid, BulletRigidBodyNode):
                    self.physics.attach_rigid_body(obj.solid)
                elif isinstance(obj.solid, BulletGhostNode):
                    self.physics.attach_ghost(obj.solid)
            if obj.node:
                if obj.solid:
                    # If this is a solid visible object, create a new physics node and reparent the visual node to that.
                    phys_node = self.render.attach_new_node(obj.solid)
                    obj.node.reparent_to(phys_node)
                    obj.node = phys_node
                else:
                    # Otherwise just reparent the visual node to the root.
                    obj.node.reparent_to(self.render)
            elif obj.solid:
                obj.node = self.render.attach_new_node(obj.solid)
            if obj.solid and obj.collide_bits is not None:
                obj.solid.set_into_collide_mask(obj.collide_bits)
        self.objects[obj.name] = obj
        # Let the object know it has been attached.
        obj.attached()
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
        self.physics.do_physics(dt)
        for obj in self.objects.values():
            if isinstance(obj, Hector):
                obj.update(dt)
        return task.cont
