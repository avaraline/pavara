from pavara.constants import *
from panda3d.core import GeomNode, NodePath
from pavara.utils.geom import GeomBuilder
from panda3d.bullet import BulletRigidBodyNode, BulletManifoldPoint

class WorldObject (object):
    """
    Base class for anything attached to a World.
    """

    world = None
    last_unique_id = 0
    collide_bits = NO_COLLISION_BITS

    def __init__(self, name=None):
        self.name = name
        if not self.name:
            self.name = '%s:%d' % (self.__class__.__name__, self.__class__.last_unique_id)
        self.__class__.last_unique_id += 1

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

    def update(self, dt):
        """
        Called each frame if the WorldObject has registered itself as updatable.
        """
        pass

class PhysicalObject (WorldObject):
    """
    A WorldObject subclass that represents a physical object; i.e. one that is visible and may have an associated
    solid for physics collisions.
    """

    node = None
    solid = None
    collide_bits = MAP_COLLIDE_BIT
    moved = False

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

    def collision(self, other, manifold, first):
        """
        Called when this object is collidable, and collides with another collidable object.
        :param manifold: The "line" between the colliding objects. See
                         https://www.panda3d.org/reference/devel/python/classpanda3d.bullet.BulletManifoldPoint.php
        :param first: Whether this was the "first" (node0) object in the collision.
        """
        pass

    def rotate(self, yaw, pitch, roll):
        """
        Programmatically set the yaw, pitch, and roll of this object.
        """
        self.node.set_hpr(yaw, pitch, roll)

    def rotate_by(self, yaw, pitch, roll):
        """
        Programmatically rotate this object by the given yaw, pitch, and roll.
        """
        self.node.set_hpr(self.node, yaw, pitch, roll)

    def move(self, center):
        """
        Programmatically move this object to be centered at the given coordinates.
        """
        self.node.set_pos(*center)
        self.moved = True

    def move_by(self, x, y, z):
        """
        Programmatically move this object by the given distances in each direction.
        """
        self.node.set_fluid_pos(self.node, x, y, z)
        self.moved = True

    def position(self):
        return self.node.get_pos()
    def add_update(self, datagram):
        if not self.moved:
            return
        pos = self.position()
        hpr = self.node.get_hpr()
        datagram.addString(self.name)
        datagram.addFloat32(pos.x)
        datagram.addFloat32(pos.y)
        datagram.addFloat32(pos.z)
        datagram.addFloat32(hpr.x)
        datagram.addFloat32(hpr.y)
        datagram.addFloat32(hpr.z)
        self.moved = False


class CompositeObject (PhysicalObject):

    def __init__(self, name=None):
        super(CompositeObject, self).__init__(name)
        self.objects = []

    def create_node(self):
        composite_geom = GeomBuilder('composite')
        for obj in self.objects:
            obj.add_to(composite_geom)
        return NodePath(composite_geom.get_geom_node())

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        for obj in self.objects:
            obj.add_solid(node)
        return node

    def attach(self, obj):
        self.objects.append(obj)