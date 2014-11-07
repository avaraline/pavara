from pavara.constants import *
from pavara.utils.integrator import Integrator, Friction
from pavara.base_objects import *
from pavara.map_objects import Sky, Dome
from pavara.utils.geom import to_cartesian
from panda3d.core import AmbientLight, DirectionalLight, VBase4, Vec3, TransparencyAttrib, CompassEffect, NodePath
from panda3d.bullet import BulletDebugNode, BulletWorld, BulletGhostNode, BulletSphereShape, BulletRigidBodyNode
import math
import random
import string

class World (object):
    """
    The World models basically everything about a map, including gravity, ambient light, the sky, and all map objects.
    """

    def __init__(self, camera, debug=False, audio3d=None, client=None, server=None):
        self.objects = {}

        self.incarnators = []

        self.collidables = set()

        self.updatables = set()
        self.updatables_to_add = set()
        self.garbage = set()
        self.scene = NodePath('world')


        # Set up the physics world. TODO: let maps set gravity.
        self.gravity = DEFAULT_GRAVITY
        self.physics = BulletWorld()
        self.physics.set_gravity(self.gravity)

        self.debug = debug

        if debug:
            debug_node = BulletDebugNode('Debug')
            debug_node.show_wireframe(True)
            debug_node.show_constraints(True)
            debug_node.show_bounding_boxes(False)
            debug_node.show_normals(False)
            np = self.scene.attach_new_node(debug_node)
            np.show()
            self.physics.set_debug_node(debug_node)


    def get_incarn(self):
        return random.choice(self.incarnators)


    def attach(self, obj):
        assert hasattr(obj, 'world') and hasattr(obj, 'name')
        assert obj.name not in self.objects
        obj.world = self
        if obj.name.startswith('Incarnator'):
            self.incarnators.append(obj)
        if hasattr(obj, 'create_node') and hasattr(obj, 'create_solid'):
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
                    phys_node = self.scene.attach_new_node(obj.solid)
                    obj.node.reparent_to(phys_node)
                    obj.node = phys_node
                else:
                    # Otherwise just reparent the visual node to the root.
                    obj.node.reparent_to(self.scene)
            elif obj.solid:
                obj.node = self.scene.attach_new_node(obj.solid)
            if obj.solid and obj.collide_bits is not None:
                obj.solid.set_into_collide_mask(obj.collide_bits)
        self.objects[obj.name] = obj
        # Let the object know it has been attached.
        obj.attached()
        return obj



    def create_hector(self, name=None):
        # TODO: get random incarn, start there
        h = self.attach(Hector(name))
        h.move((0, 15, 0))
        return h

    def register_updater(self, obj):
        assert isinstance(obj, WorldObject)
        self.updatables.add(obj)

    def register_updater_later(self, obj):
        assert isinstance(obj, WorldObject)
        self.updatables_to_add.add(obj)



    def update(self, task):
        """
        Called every frame to update the physics, etc.
        """
        dt = globalClock.getDt()
        for obj in self.updatables_to_add:
            self.updatables.add(obj)
        self.updatables_to_add = set()
        for obj in self.updatables:
            obj.update(dt)
        self.updatables -= self.garbage
        self.collidables -= self.garbage
        while True:
            if len(self.garbage) < 1:
                break;
            trash = self.garbage.pop()
            if(isinstance(trash.solid, BulletGhostNode)):
                self.physics.remove_ghost(trash.solid)
            if(isinstance(trash.solid, BulletRigidBodyNode)):
                self.physics.remove_rigid_body(trash.solid)
            if hasattr(trash, 'dead'):
                trash.dead()
            trash.node.remove_node()
            del(trash)
        self.physics.do_physics(dt)
        for obj in self.collidables:
            result = self.physics.contact_test(obj.node.node())
            for contact in result.get_contacts():
                obj1 = self.objects.get(contact.get_node0().get_name())
                obj2 = self.objects.get(contact.get_node1().get_name())
                if obj1 and obj2:
                    # Check the collision bits to see if the two objects should collide.
                    should_collide = obj1.collide_bits & obj2.collide_bits
                    if not should_collide.is_zero():
                        pt = contact.get_manifold_point()
                        if obj1 in self.collidables:
                            obj1.collision(obj2, pt, True)
                        if obj2 in self.collidables:
                            obj2.collision(obj1, pt, False)
        return task.cont

class ServerWorld(World):
    """
    The server's view of the world, sans any purely visual information.
    """
    def __init__(self, debug=False):
        super(ServerWorld, self).__init__(debug)



    def register_collider(self, obj):
        assert isinstance(obj, PhysicalObject)
        self.collidables.add(obj)

    def do_explosion(self, node, radius, force):
        center = node.get_pos(self.scene);
        expl_body = BulletGhostNode("expl")
        expl_shape = BulletSphereShape(radius)
        expl_body.add_shape(expl_shape)
        expl_bodyNP = self.scene.attach_new_node(expl_body)
        expl_bodyNP.set_pos(center)
        self.physics.attach_ghost(expl_body)
        result = self.physics.contact_test(expl_body)
        for contact in result.getContacts():
            n0_name = contact.getNode0().get_name()
            n1_name = contact.getNode1().get_name()
            obj = None
            try:
                obj = self.objects[n1_name]
            except:
                break
            if n0_name == "expl" and n1_name not in EXPLOSIONS_DONT_PUSH and not n1_name.startswith('Walker'):
                # repeat contact test with just this pair of objects
                # otherwise all manifold point values will be the same
                # for all objects in original result
                real_c = self.physics.contact_test_pair(expl_body, obj.solid)
                mpoint = real_c.getContacts()[0].getManifoldPoint()
                distance = mpoint.getDistance()
                if distance < 0:
                    if hasattr(obj, 'decompose'):
                        obj.decompose()
                    else:
                        expl_vec = Vec3(mpoint.getPositionWorldOnA() - mpoint.getPositionWorldOnB())
                        expl_vec.normalize()
                        magnitude = force * 1.0/math.sqrt(abs(radius - abs(distance)))
                        obj.solid.set_active(True)
                        obj.solid.apply_impulse(expl_vec*magnitude, mpoint.getLocalPointB())
                    if hasattr(obj, 'damage'):
                        obj.damage(magnitude/5)
        self.physics.remove_ghost(expl_body)
        expl_bodyNP.detach_node()
        del(expl_body, expl_bodyNP)


    def do_plasma_push(self, plasma, node, energy):
        obj = None
        try:
            obj = self.objects[node]
        except:
            raise

        if node not in EXPLOSIONS_DONT_PUSH and not node.startswith('Walker'):
            if hasattr(obj, 'decompose'):
                obj.decompose()
            else:
                solid = obj.solid
                dummy_node = NodePath('tmp')
                dummy_node.set_hpr(plasma.hpr)
                dummy_node.set_pos(plasma.pos)
                f_vec = scene.get_relative_vector(dummy_node, Vec3(0,0,1))
                local_point = (obj.node.get_pos() - dummy_node.get_pos()) *-1
                f_vec.normalize()
                solid.set_active(True)
                try:
                    solid.apply_impulse(f_vec*(energy*35), Point3(local_point))
                except:
                    pass
                del(dummy_node)
        if hasattr(obj, 'damage'):
            obj.damage(energy*5)


class ClientWorld(World):
    """
    A client's view of the world, including visual information.
    Leaves most physics and game logic to the server to dictate.
    """
    def __init__(self, camera, debug=False, audio3d=False):
        super(ClientWorld, self).__init__(debug)
        self.camera = camera
        self.audio3d = audio3d
        self.ambient = self._make_ambient()
        self.celestials = CompositeObject()
        self.sky = self.attach(Sky())

    def _make_ambient(self):
        alight = AmbientLight('ambient')
        alight.set_color(VBase4(*DEFAULT_AMBIENT_COLOR))
        node = self.scene.attach_new_node(alight)
        self.scene.set_light(node)
        return node

    def set_ambient(self, color):
        """
        Sets the ambient light to the given color.
        """
        self.ambient.node().set_color(VBase4(*color))

    def create_celestial_node(self):
        bounds = self.camera.node().get_lens().make_bounds()
        self.celestials = self.celestials.create_node()
        self.celestials.set_transparency(TransparencyAttrib.MAlpha)
        self.celestials.set_light_off()
        self.celestials.set_effect(CompassEffect.make(self.camera, CompassEffect.PPos))
        self.celestials.node().set_bounds(bounds)
        self.celestials.node().set_final(True)
        self.celestials.reparent_to(self.scene)

    def register_collider(self, obj):
        pass

    def add_celestial(self, azimuth, elevation, color, intensity, radius, visible):
        """
        Adds a celestial light source to the scene. If it is a visible celestial, also add a sphere model.
        """
        if not self.camera:
            return
        location = Vec3(to_cartesian(azimuth, elevation, 1000.0 * 255.0 / 256.0))
        if intensity:
            dlight = DirectionalLight('celestial')
            dlight.set_color((color[0] * intensity, color[1] * intensity,
                color[2] * intensity, 1.0))
            node = self.scene.attach_new_node(dlight)
            node.look_at(*(location * -1))
            self.scene.set_light(node)
        if visible:
            if radius <= 2.0:
                samples = 6
            elif radius >= 36.0:
                samples = 40
            else:
                samples = int(round(((1.5 * radius) * (2 / 3.0)) + 3.75))
            celestial = Dome(radius * 1.5, samples, 2, color, 0, location,
                ((-(math.degrees(azimuth))), 90 + math.degrees(elevation), 0))
            self.celestials.attach(celestial)