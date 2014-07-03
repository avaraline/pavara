from pavara.utils.geom import GeomBuilder
from panda3d.core import NodePath, ColorAttrib, Vec3
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape, BulletPlaneShape, BulletGhostNode
from icebox.constants import *

class WorldObject(object):
    world = None
    last_unique_id = 0
    attached = False
    moved = False

    def __init__(self, name=None):
        self.name = name
        if not self.name:
            self.name = '%s:%d' % (self.__class__.__name__, self.__class__.last_unique_id)
        self.__class__.last_unique_id += 1

    def update(self, dt):
        pass

    def move(self, pos):
        assert(self.attached)
        self.moved = True
        self.np.set_pos(*pos)
        pass

    def rotate(self, hpr):
        assert(self.attached)
        self.moved = True
        self.np.set_hpr(*hpr)
        pass

    def add_update(self, datagram):
        pos = self.np.get_pos()
        hpr = self.np.get_hpr()
        if not self.moved:
            return
        datagram.addString(self.name)
        datagram.addFloat32(pos.x)
        datagram.addFloat32(pos.y)
        datagram.addFloat32(pos.z)
        datagram.addFloat32(hpr.x)
        datagram.addFloat32(hpr.y)
        datagram.addFloat32(hpr.z)
        self.moved = False

    def __repr__(self):
        return self.name

class Tank(WorldObject):
    def __init__(self, name = None):
        super(Tank, self).__init__(name)

        b = GeomBuilder('tank')
        b.add_dome(RED_COLOR, (0, 0, 0), 2, 6, 4)
        b.add_block([.3, .3, .3, 1], (0, 0.6, 2.2), (.7, .7, 2))
        self.geom = b.get_geom_node()

        self.node = BulletGhostNode(self.name)

    def update(self, dt):
        pass

class Block(WorldObject):
    def __init__(self, name=None):
        super(Block, self).__init__(name)

        b = GeomBuilder('block')
        b.add_block(BLOCK_COLOR, (0, 0, 0), BLOCK_SIZE)
        self.geom = b.get_geom_node()

        shape = BulletBoxShape(Vec3(BLOCK_SIZE))
        self.node = BulletRigidBodyNode(self.name)
        self.node.set_mass(1.0)
        self.node.addShape(shape)

    def update(self, dt):
        if self.attached:
            self.moved = True

class Arena(WorldObject):    
    def __init__(self, name=None):
        super(Arena, self).__init__(name)

        b = GeomBuilder('floor')
        b.add_block(FLOOR_COLOR, (0, 0, 0), (100, 1, 100))
        floor_geom = b.get_geom_node()
        floor_np = NodePath('floor_np')
        floor_np.attach_new_node(floor_geom)

        b = GeomBuilder('halfcourt')
        b.add_block(LINE_COLOR, (0, .6, 0), (100, .2, 1))
        line_geom = b.get_geom_node()
        floor_np.attach_new_node(line_geom)

        b = GeomBuilder('redgoal')
        b.add_block(RED_COLOR, (0, .6, -25), (GOAL_SIZE[0], .1, GOAL_SIZE[1]))
        redgoal_geom = b.get_geom_node()
        b = GeomBuilder('redgoal_overlay')
        b.add_block(FLOOR_COLOR, (0, .65, -25), (GOAL_SIZE[0] - .8, .1, GOAL_SIZE[1] - .8))
        redgoal_overlay_geom = b.get_geom_node()
        floor_np.attach_new_node(redgoal_geom)
        floor_np.attach_new_node(redgoal_overlay_geom)

        b = GeomBuilder('bluegoal')
        b.add_block(BLUE_COLOR, (0, .6, 25), (GOAL_SIZE[0], .1, GOAL_SIZE[1]))
        bluegoal_geom = b.get_geom_node()
        b = GeomBuilder('bluegoal_overlay')
        b.add_block(FLOOR_COLOR, (0, .65, 25), (GOAL_SIZE[0] - .8, .1, GOAL_SIZE[1] - .8,))
        bluegoal_overlay_geom = b.get_geom_node()
        floor_np.attach_new_node(bluegoal_geom)
        floor_np.attach_new_node(bluegoal_overlay_geom)

        self.geom = floor_np

        ground_shape = BulletPlaneShape(Vec3(0, 1, 0), 1)
        self.node = BulletRigidBodyNode('ground')
        self.node.add_shape(ground_shape)
        self.node.set_mass(0)






