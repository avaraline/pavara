from pandac.PandaModules import Point3
from panda3d.bullet import BulletGhostNode, BulletSphereShape, BulletRigidBodyNode
from direct.actor.Actor import Actor
from pavara.world import PhysicalObject, TriangleExplosion
from pavara.utils.integrator import Integrator
from pavara.assets import load_model
from pavara.constants import *
import math
import random

class Projectile(PhysicalObject):
    pass

class Plasma (Projectile):
    def __init__(self, pos, hpr, energy, name=None):
        super(Plasma, self).__init__(name)
        self.pos = Vec3(*pos)
        self.hpr = hpr
        self.energy = energy
        self.age = 0

    def create_node(self):
        m = load_model('plasma.egg')
        m.set_shader_auto()
        p = m.find('**/plasma')
        cf = self.energy
        p.setColor(1,(150/255.0)*cf,(150/255.0)*cf)
        m.set_scale(PLASMA_SCALE)
        return m

    def create_solid(self):
        node = BulletGhostNode(self.name)
        node_shape = BulletSphereShape(.05)
        node.add_shape(node_shape)
        node.set_kinematic(True)
        return node

    def attached(self):
        self.node.set_pos(self.pos)
        self.node.set_hpr(self.hpr)
        #light = PointLight(self.name+"_light")
        #cf  = self.energy
        #light.set_color(VBase4(.9*cf,0,0,1))
        #light.set_attenuation(Point3(0.1, 0.1, 0.8))
        #self.light_node = self.node.attach_new_node(light)

        #self.world.render.set_light(self.light_node)
        self.world.register_updater(self)
        self.world.register_collider(self)
        self.solid.setIntoCollideMask(NO_COLLISION_BITS)
        self.sound = self.world.audio3d.loadSfx('Sounds/plasma.wav')
        self.sound.set_balance(0)
        self.world.audio3d.attachSoundToObject(self.sound, self.node)
        self.world.audio3d.setSoundVelocity(self.sound, render.get_relative_vector(self.node, Vec3(0,0,400)))
        self.sound.set_loop(True)
        self.sound.play()

    def update(self, dt):
        self.move_by(0,0,(dt*60)/4)
        self.rotate_by(0,0,(dt*60)*3)
        result = self.world.physics.contact_test(self.solid)
        self.age += dt*60
        contacts = result.getContacts()
        if len(contacts) > 0:
            #self.world.render.clear_light(self.light_node)
            cf = self.energy
            expl_color = [1,(150/255.0)*cf,(150/255.0)*cf, 1]
            expl_pos = self.node.get_pos(self.world.render)
            expl = self.world.attach(TriangleExplosion(expl_pos, 5, size=.1, color=expl_color))
            contact = contacts[0]
            contact.getManifoldPoint().getLocalPointB()
            n1_name = contact.getNode1().get_name()
            self.world.do_plasma_push(self, n1_name, self.energy)
            self.sound.stop()
            self.world.audio3d.detachSound(self.sound)
            self.world.garbage.add(self)

        if self.age > PLASMA_LIFESPAN:
            self.sound.stop()
            self.world.audio3d.detachSound(self.sound)
            self.world.garbage.add(self)

    def decompose(self):
        pass

class Missile (Projectile):
    def __init__(self, pos, hpr, color, name=None):
        super(Missile, self).__init__(name)
        self.pos = Vec3(*pos)
        self.hpr = hpr
        self.age = 0
        self.color = color
        self.velocity = Vec3(0,0,0)

    def create_node(self):
        self.model = load_model('missile.egg')
        self.body = self.model.find('**/bodywings')
        self.body.set_color(*self.color)
        self.main_engines = self.model.find('**/mainengines')
        self.wing_engines = self.model.find('**/wingengines')
        self.main_engines.set_color(*random.choice(ENGINE_COLORS))
        self.wing_engines.set_color(*random.choice(ENGINE_COLORS))
        self.model.set_scale(MISSILE_SCALE)
        self.model.set_hpr(0,0,0)
        return self.model

    def create_solid(self):
        node = BulletGhostNode(self.name)
        node_shape = BulletSphereShape(.08)
        node.add_shape(node_shape)
        node.set_kinematic(True)
        return node

    def attached(self):
        self.node.set_pos(self.pos)
        self.node.set_hpr(self.hpr)
        self.world.register_updater(self)
        self.world.register_collider(self)
        self.solid.setIntoCollideMask(NO_COLLISION_BITS)
        self.sound = self.world.audio3d.loadSfx('Sounds/plasma.wav')
        self.sound.set_balance(0)
        self.world. audio3d.attachSoundToObject(self.sound, self.node)
        self.sound.set_loop(True)
        self.sound.play()
        self.integrator = Integrator(self.world.render.get_relative_vector(self.node, Vec3(0,0,30)))

    def decompose(self):
        clist = list(self.color)
        clist.extend([1])
        expl_colors = [clist]
        expl_colors.extend(ENGINE_COLORS)
        expl_pos = self.node.get_pos(self.world.render)
        for c in expl_colors:
            self.world.attach(TriangleExplosion(expl_pos, 1, size=.1, color=c, lifetime=40))
        self._remove_all()

    def update(self, dt):
        current_pos = Point3(0, self.position().get_y(), 0)
        pos, self.velocity = self.integrator.integrate(self.node.get_pos(), self.velocity, dt)
        if self.velocity.length() > 30:
            self.integrator.accel = Vec3(0,0,0)
        else:
            self.integrator.accel = self.world.render.get_relative_vector(self.node, Vec3(0,0,30))
        self.move(self.position() + (pos - self.node.get_pos()))

        self.main_engines.set_color(*random.choice(ENGINE_COLORS))
        self.wing_engines.set_color(*random.choice(ENGINE_COLORS))
        result = self.world.physics.contact_test(self.solid)
        self.age += dt
        if len(result.getContacts()) > 0:
            clist = list(self.color)
            clist.extend([1])
            expl_colors = [clist]
            expl_colors.extend(ENGINE_COLORS)
            expl_pos = self.node.get_pos(self.world.render)
            for c in expl_colors:
                self.world.attach(TriangleExplosion(expl_pos, 3, size=.1, color=c, lifetime=80))
            self.world.do_explosion(self.node, 1.5, 30)
            self._remove_all()

        if self.age > MISSILE_LIFESPAN:
            self._remove_all()

    def _remove_all(self):
        self.sound.stop()
        self.world.audio3d.detachSound(self.sound)
        self.world.garbage.add(self)

class Grenade (Projectile):
    def __init__(self, pos, hpr, color, walker_v, name=None):
        super(Grenade, self).__init__(name)
        self.pos = Vec3(*pos)
        self.hpr = hpr
        self.move_divisor = 9
        self.color = color
        self.forward_m = .25
        self.walker_v = walker_v

    def create_node(self):
        self.model = Actor('grenade.egg')
        self.shell = self.model.find('**/shell')
        self.shell.set_color(*self.color)
        self.inner_top = self.model.find('**/inner_top')
        self.inner_bottom = self.model.find('**/inner_bottom')
        self.inner_top.set_color(*random.choice(ENGINE_COLORS))
        self.inner_bottom.set_color(*random.choice(ENGINE_COLORS))
        self.model.set_scale(GRENADE_SCALE)
        self.model.set_hpr(0,0,0)
        self.spin_bone = self.model.controlJoint(None, 'modelRoot', 'grenade_bone')
        return self.model

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        node.set_angular_damping(.9)
        node_shape = BulletSphereShape(.08)
        node.add_shape(node_shape)
        node.set_mass(.5)
        return node

    def attached(self):
        self.node.set_pos(self.pos)
        self.node.set_hpr(self.hpr)
        self.world.register_updater(self)
        self.world.register_collider(self)
        self.solid.setIntoCollideMask(NO_COLLISION_BITS)
        self.solid.set_gravity(DEFAULT_GRAVITY*4.5)
        grenade_iv = render.get_relative_vector(self.node, Vec3(0,8.5,13.5))
        grenade_iv += (self.walker_v * 1/2)
        self.solid.apply_impulse(grenade_iv, Point3(*self.pos))

    def decompose(self):
        clist = list(self.color)
        clist.extend([1])
        expl_colors = [clist]
        expl_colors.extend(ENGINE_COLORS)
        expl_pos = self.node.get_pos(self.world.render)
        for c in expl_colors:
            self.world.attach(TriangleExplosion(expl_pos, 1, size=.1, color=c, lifetime=40))
        self.world.garbage.add(self)

    def update(self, dt):
        self.inner_top.set_color(*random.choice(ENGINE_COLORS))
        self.inner_bottom.set_color(*random.choice(ENGINE_COLORS))
        result = self.world.physics.contact_test(self.solid)
        self.spin_bone.set_hpr(self.spin_bone, 0,0,10)
        contacts = result.getContacts()
        if len(contacts) > 0:
            hit_node = contacts[0].get_node1().get_name()
            if hit_node.endswith("_walker_cap"):
                return
            clist = list(self.color)
            clist.extend([1])
            expl_colors = [clist]
            expl_colors.extend(ENGINE_COLORS)
            expl_pos = self.node.get_pos(self.world.render)
            for c in expl_colors:
                self.world.attach(TriangleExplosion(expl_pos, 3, size=.1, color=c, lifetime=80,))
            self.world.do_explosion(self.node, 3, 100)
            self.world.garbage.add(self)

