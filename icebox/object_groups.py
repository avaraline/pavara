from icebox.environment import Arena
from panda3d.core import VBase4, AmbientLight, NodePath
from panda3d.core import ColorAttrib, DirectionalLight, Vec4

class ObjectGroup(object):
    def __init__(self):
        pass

class VisibleObjects(ObjectGroup):
    def __init__(self, render):
        super(VisibleObjects, self).__init__()
        self.render = render
        self.objects_node = NodePath('VisibleObjects')
        
        self.updatables = set()
        self.updatables_to_add = set()
        self.garbage = set()
        
        alight = AmbientLight('ambient')
        alight.set_color(VBase4(0.4, 0.4, 0.4, 1))
        node = self.objects_node.attach_new_node(alight)
        self.objects_node.set_light(node)

        directional_light = DirectionalLight('directionalLight')
        directional_light.set_color(Vec4(0.8, 0.2, 0.2, 1))
        directional_light_np = render.attach_new_node(directional_light)
        directional_light_np.set_hpr(180, -20, 0)
        render.set_light(directional_light_np)

        self.arena = Arena(self.objects_node)
        self.objects_node.setColorOff()
        self.objects_node.setShaderAuto()
        self.objects_node.node().setAttrib(ColorAttrib.makeVertex())
        self.objects_node.reparent_to(self.render)

    def update(self, dt):
        pass

class PhysicalObjects(ObjectGroup):
    def __init__(self):
        super(PhysicalObjects, self).__init__()

    def update(self, dt):
        pass