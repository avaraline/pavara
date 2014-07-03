from icebox.objects import Arena, Block, Tank
from panda3d.core import VBase4, AmbientLight, NodePath
from panda3d.core import ColorAttrib, DirectionalLight, Vec4, Vec3
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode, BulletGhostNode, BulletDebugNode

class World (object):
    def __init__(self, showbase, is_client):
        self.is_client = is_client
        self.objects = {}
        self.updatables = set()
        self.render = showbase.render

        self.bullet_world = BulletWorld()

        if is_client:
            self.init_visual()
        else:
            self.bullet_world.setGravity(Vec3(0, -9.81, 0))

        self.arena = Arena('arena')
        self.attach(self.arena)
        self.arena.np.set_pos(0,0,0)

    def attach(self, obj):
        assert(obj.name not in self.objects)
        self.objects[obj.name] = obj
        obj.np = self.render.attach_new_node(obj.node)
        if isinstance(obj.node, BulletRigidBodyNode):
            self.bullet_world.attach_rigid_body(obj.node)
        if isinstance(obj.node, BulletGhostNode):
            self.bullet_world.attach_ghost(obj.node)
        if self.is_client:
            NodePath(obj.geom).reparent_to(obj.np)
        obj.attached = True

    def add_block(self, pos, name=None):
        block = Block(name)
        self.attach(block)
        self.updatables.add(block)
        block.move(pos)

    def add_tank(self, pos, name=None):
        tank = Tank(name)
        self.attach(tank)
        self.updatables.add(tank)
        tank.move(pos)        

    def init_visual(self):
        self.objects_node = NodePath('VisibleObjects')
        
        alight = AmbientLight('ambient')
        alight.set_color(VBase4(0.6, 0.6, 0.6, 1))
        node = self.render.attach_new_node(alight)
        self.render.set_light(node)

        directional_light = DirectionalLight('directionalLight')
        directional_light.set_color(Vec4(0.7, 0.7, 0.7, 1))
        directional_light_np = self.render.attach_new_node(directional_light)
        directional_light_np.set_hpr(0, -80, 0)
        self.render.set_light(directional_light_np)

        self.arena = Arena(self.objects_node)

        self.render.setColorOff()
        self.render.setShaderAuto()
        self.render.node().setAttrib(ColorAttrib.makeVertex())

        debug_node = BulletDebugNode('Debug')
        debug_node.showWireframe(True)
        debug_node.showConstraints(True)
        debug_node.showBoundingBoxes(False)
        debug_node.showNormals(True)
        debug_np = self.render.attach_new_node(debug_node)
        debug_np.show()
        self.bullet_world.setDebugNode(debug_np.node())

        #self.objects_node.setColorOff()
        #self.objects_node.setShaderAuto()
        #self.objects_node.node().setAttrib(ColorAttrib.makeVertex())
       # self.objects_node.reparent_to(self.render)

    def update(self, dt):
        if not self.is_client:
            for obj in self.updatables:
                obj.update(dt)
        self.bullet_world.doPhysics(dt)