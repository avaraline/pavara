from icebox.environment import Arena, Block
from panda3d.core import VBase4, AmbientLight, NodePath
from panda3d.core import ColorAttrib, DirectionalLight, Vec4

class World (object):
    def __init__(self, showbase, physics_manager, is_client):
        self.is_client = is_client
        self.objects = {}
        self.updatables = set()
        self.physics_manager = physics_manager
        self.render = showbase.render
        if is_client:
            self.init_visual()


    def add_block(self, pos):
        block = Block()
        block.container_node.set_pos(*pos)
        if self.is_client:
            block.container_node.reparent_to(self.render)

    def add_tank(self, ):
        

    def init_visual(self):
        self.objects_node = NodePath('VisibleObjects')
        
        alight = AmbientLight('ambient')
        alight.set_color(VBase4(0.4, 0.4, 0.4, 1))
        node = self.objects_node.attach_new_node(alight)
        self.objects_node.set_light(node)

        directional_light = DirectionalLight('directionalLight')
        directional_light.set_color(Vec4(0.2, 0.2, 0.2, 1))
        directional_light_np = render.attach_new_node(directional_light)
        directional_light_np.set_hpr(0, 40, 0)
        render.set_light(directional_light_np)

        self.arena = Arena(self.objects_node)

        self.objects_node.setColorOff()
        self.objects_node.setShaderAuto()
        self.objects_node.node().setAttrib(ColorAttrib.makeVertex())
        self.objects_node.reparent_to(self.render)

    def update(self, dt):
        pass