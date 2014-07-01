from pavara.utils.geom import GeomBuilder
from panda3d.core import NodePath, ColorAttrib
from panda3d.physics import ActorNode
from icebox.constants import *

class WorldObject(object):
	world = None
    last_unique_id = 0

    def __init__(self, name=None):
    	self.name = name
        if not self.name:
            self.name = '%s:%d' % (self.__class__.__name__, self.__class__.last_unique_id)
        self.__class__.last_unique_id += 1
        pass

    def __repr__(self):
        return self.name

class Arena(WorldObject):    
    def __init__(self, parent):
        super(Arena, self).__init__()

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

        floor_np.reparent_to(parent)

class Block(WorldObject):
	def __init__(self):
		super(Block, self).__init__()

		b = GeomBuilder('block')
		b.add_block(BLOCK_COLOR, (0, 0, 0), (5, 3, 5))
		block_geom = b.get_geom_node()
		self.container_node = NodePath('BlockPhysicsNode')
		self.actor_node = ActorNode('block-actor')
		anp = self.container_node.attach_new_node(self.actor_node)
		self.block_node = anp.attach_new_node(block_geom)
