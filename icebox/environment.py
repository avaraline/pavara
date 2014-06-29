from pavara.utils.geom import GeomBuilder
from panda3d.core import NodePath

class MapObject(object):
    def __init__(self):
        pass

class Arena(MapObject):    
    def __init__(self, parent):
        super(Arena, self).__init__()
        b = GeomBuilder('block')
        b.add_block([155,0,155,255], (0,0,0), (100,100,1))
        floor_geom = b.get_geom_node()
        floor_node = parent.attach_new_node(floor_geom)
        #floor_node.set_color(155,0,155)
