from pavara.constants import *
from pavara.utils.geom import GeomBuilder
from pavara.base_objects import WorldObject, PhysicalObject
from direct.interval.LerpInterval import LerpFunc
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape
from panda3d.core import Point3, TransparencyAttrib
import math
import random

class Effect (object):
    """Effects wrap objects like boxes and ramps and other effects and change
       behavior of the wrapped object. Subclasses of this class automatically
       delegate anything not implemented in the effect to the object being
       wrapped."""
    def __init__(self, effected):
        object.__setattr__(self, 'effected', effected)

    def __setattr__(self, name, value):
        """Attributes should be assigned as deeply in the effect chain as
           possible, so go all the way down the effect chain, and start coming
           back until the first object to have the attribute is found. Set it
           and return. If nothing is found, set it in this object."""
        objs = []
        obj = self

        while hasattr(obj, 'effected'):
            obj = obj.effected
            objs.append(obj)

        while objs:
            obj = objs.pop()
            if hasattr(obj, name):
                object.__setattr__(obj, name, value)
                return
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        """Python only calls this function if the attribute is not defined on
           the object. This makes it so method calls are automatically passed
           down the effect chain if they are not defined in the effect object"""
        return getattr(self.effected, name)


class Hologram (Effect):
    collide_bits = NO_COLLISION_BITS

class FreeSolid (Effect):

    def __init__(self, effected, mass):
        if mass > 0:
            self.mass = mass
        Effect.__init__(self, effected)
        self.collide_bits = MAP_COLLIDE_BIT | SOLID_COLLIDE_BIT

    def create_solid(self):
        node = self.effected.create_solid()
        node.set_mass(self.mass if self.mass > 0 else 1)
        return node


class Transparent (Effect):

    def __init__(self, effected, alpha):
        Effect.__init__(self, effected)
        self.alpha = alpha

    def create_node(self):
        node = self.effected.create_node()
        node.setTwoSided(True)
        node.setDepthWrite(False)
        node.set_transparency(TransparencyAttrib.MAlpha)
        node.setTwoSided(True)
        node.setDepthWrite(False)
        node.setAlphaScale(self.alpha)
        return node

class Hostile (Effect):
    
    def __init__(self, effected):
        Effect.__init__(self, effected)
        self.hostile = True

class Mortal (Effect):

    def __init__(self, effected, hp):
        self.hp = hp
        Effect.__init__(self, effected)

    def damage(self, amt):
        self.hp -= amt
        if self.hp < 0:
            self.world.garbage.add(self)
            return
        def update_color(scaleval):
             if self.node: 
                self.node.set_color_scale(scaleval, scaleval, scaleval, 1.0)
        ramp_up = LerpFunc(update_color, fromData=3, toData=1, duration=.2, name=None)
        ramp_up.start()

    def dead(self):
        c = getattr(self, 'color', [1,1,1,1])
        expl_pos = self.node.get_pos(self.world.render)
        size = getattr(self, 'size', None)
        width = getattr(self, 'width', None)
        radius = getattr(self, 'radius', None)
        reduced = 0
        count = 0
        if size is not None:
            reduced = sum(size) / float(len(size)) * .3
            count = int(reduced)*4
        if width is not None:
            reduced = width * .6
            count = int(reduced)/3
        if radius is not None:
            reduced = radius * .6
            count = int(reduced)

        self.world.attach(TriangleExplosion(expl_pos, count, size=reduced, color=c, lifetime=60, debris_area=size))
        

class TriangleExplosion (WorldObject):
    def __init__(self, pos, count, hit_normal=None, lifetime=40, color=[1,1,1,1], size=.2, amount=5, name=None, debris_area=None):
        super(TriangleExplosion, self).__init__(name)
        self.pos = Vec3(*pos)
        self.hit_normal = Vec3(*hit_normal) if hit_normal else None
        self.lifetime = lifetime
        self.color = color
        self.size = size
        self.count = count
        self.shrapnels = []
        self.debris_area = debris_area


    def create_node(self):
        self.pos_node = self.world.render.attachNewNode(self.name+"_node")
        return self.pos_node

    def attached(self):
        for i in xrange(self.count):
            #if self.hit_normal:
                #vector = Vec3(*[random.uniform(x+.7, x-.7) for x in self.hit_normal])
            #else:
            vector = Vec3(*[random.uniform(-.5,.5) for _ in xrange(3)])
            if self.debris_area:
                position = Vec3(*[random.uniform(x + ((y/2)-self.size), x - ((y/2)+self.size)) for x,y in zip(self.pos,self.debris_area)])
            else:
                position = Vec3(*[random.uniform(x+self.size, x-self.size) for x in self.pos])

            if position.y < 0:
                position.y = self.size+.1
            self.shrapnels.append(self.world.attach(Shrapnel(position, self.size, self.color, vector, self.lifetime)))


class Shrapnel (PhysicalObject):
    def __init__(self, pos, size, color, vector, lifetime, name=None):
        super(Shrapnel, self).__init__(name)
        self.pos = pos
        self.vector = vector
        self.lifetime = lifetime
        self.size = size
        self.color = color
        self.mass = .01
        self.age = 0

    def create_node(self):
        extent = self.size/2.0
        geom_points = [Point3(0,-extent,-extent), Point3(0,extent,extent), Point3(0,-extent,extent)]
        self.geom = GeomBuilder('tri').add_tri(self.color, geom_points).get_geom_node()
        self.node = self.world.render.attach_new_node(self.geom)
        self.colorhandle = self.node.find('**/*')
        return self.node

    def create_solid(self):
        node = BulletRigidBodyNode(self.name)
        node_shape = BulletBoxShape(Vec3(.01, self.size, self.size))
        node.add_shape(node_shape)
        node.set_mass(3)
        node.set_angular_damping(.7)
        return node

    def attached(self):
        self.world.register_collider(self)
        self.world.register_updater_later(self)
        self.node.set_pos(self.pos)
        self.solid.apply_impulse(Vec3(*self.vector)*12, Point3(*self.pos))
        self.solid.setIntoCollideMask(NO_COLLISION_BITS)

    def update(self, dt):
        self.age += dt*60
        halflife = self.lifetime/2
        if self.age > self.lifetime-halflife:
            newcolor = [x*((self.lifetime-self.age)/halflife) for x in self.color]
            newcolor[3] = 1 #changing the alpha channel doesn't work
            if self.node:
                self.node.set_color(*newcolor)
        if self.age > self.lifetime:
            self.world.garbage.add(self)