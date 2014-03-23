from panda3d.core import Vec3, TransformState, rad2Deg, AmbientLight, ColorBlendAttrib, LineSegs
from panda3d.bullet import BulletGhostNode, BulletCylinderShape, BulletConvexHullShape, BulletRigidBodyNode, YUp
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *
from pavara.world import *
from pavara.projectiles import *

TOP_LEG_LENGTH = 1
BOTTOM_LEG_LENGTH = 1.21
TOP_LEG_EXTENDED_P = 60
BOTTOM_LEG_EXTENDED_P = -70

MISSILE_OFFSET = [0, -.3, -.6]
GRENADE_OFFSET = [0, .3, -.8]

SIGHTS_FRIENDLY_COLOR = [14.0/255.0, 114.0/255.0, 26.0/255.0, 1]
SIGHTS_ENEMY_COLOR = [217.0/255.0, 24.0/255.0, 24.0/255.0, 1]

MIN_WALKFUNC_SIZE_FACTOR = .001
MAX_WALKFUNC_SIZE_FACTOR = 4
WALKFUNC_X_LIMIT = 2.00/3.00
WALKFUNC_STEPS = 20

class LoadedMissile (object):

    def __init__(self, actor, color):
        self.missile_loaded = False
        self.loaded_missile = load_model('missile.egg')
        self.loaded_missile.hide()
        self.loaded_missile.reparentTo(actor)
        self.loaded_missile.set_pos(self.loaded_missile, *MISSILE_OFFSET)
        self.loaded_missile.set_h(180)
        self.loaded_missile.set_scale(MISSILE_SCALE)
        main_engines = self.loaded_missile.find('**/mainengines')
        main_engines.set_color(.2,.2,.2)
        wing_engines = self.loaded_missile.find('**/wingengines')
        wing_engines.set_color(.2,.2,.2)
        self.body = self.loaded_missile.find('**/bodywings')
        self.color = color
        self.body.set_color(*color)

    def toggle_visibility(self):
        self.missile_loaded = not self.missile_loaded
        if self.missile_loaded:
            self.loaded_missile.show()
        else:
            self.loaded_missile.hide()

    def can_fire(self):
        return self.missile_loaded

    def fire(self, world):
        origin = self.loaded_missile.get_pos(world.render)
        hpr = self.loaded_missile.get_hpr(world.render)
        #hpr += head_angle
        world.attach(Missile(origin, hpr, self.color))
        self.missile_loaded = False
        self.loaded_missile.hide()

class LoadedGrenade (object):

    def __init__(self, actor, color):
        self.grenade_loaded = False
        self.loaded_grenade = load_model('grenade.egg')
        self.loaded_grenade.hide()
        self.loaded_grenade.reparentTo(actor)
        self.loaded_grenade.set_pos(self.loaded_grenade, *GRENADE_OFFSET)
        self.loaded_grenade.set_hpr(0,180,0)
        self.loaded_grenade.set_scale(GRENADE_SCALE)
        inner_top = self.loaded_grenade.find('**/inner_top')
        inner_top.set_color(.2,.2,.2)
        inner_bottom = self.loaded_grenade.find('**/inner_bottom')
        inner_bottom.set_color(.2,.2,.2)
        shell = self.loaded_grenade.find('**/shell')
        self.color = color
        shell.set_color(*color)

    def toggle_visibility(self):
        self.grenade_loaded = not self.grenade_loaded
        if self.grenade_loaded:
            self.loaded_grenade.show()
        else:
            self.loaded_grenade.hide()

    def can_fire(self):
        return self.grenade_loaded

    def fire(self, world, walker_v):
        origin = self.loaded_grenade.get_pos(world.render)
        hpr = self.loaded_grenade.get_hpr(world.render)
        world.attach(Grenade(origin, hpr, self.color, walker_v))
        self.grenade_loaded = False
        self.loaded_grenade.hide()

class Sights (object):

    def __init__(self, left_barrel, right_barrel, world):
        self.render = world.render
        self.physics = world.physics
        self.world = world
        self.left_plasma = load_model('plasma_sight.egg')
        self.right_plasma = load_model('plasma_sight.egg')
        self.left_plasma.reparent_to(left_barrel)
        self.right_plasma.reparent_to(right_barrel)
        self.left_plasma.set_r(180)
        self.left_plasma.find("**/sight").setColor(*SIGHTS_FRIENDLY_COLOR)
        self.right_plasma.find("**/sight").setColor(*SIGHTS_FRIENDLY_COLOR)

        # inverted colors based on colors behind sights
        self.left_plasma.setTransparency(TransparencyAttrib.MAlpha)
        self.left_plasma.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MInvSubtract,
              ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
        self.right_plasma.setTransparency(TransparencyAttrib.MAlpha)
        self.right_plasma.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MInvSubtract,
              ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))

        # ambient light source for lighting sight shapes
        sight_light = AmbientLight('sight_light')
        sight_light.set_color(VBase4(1,1,1,1))
        sight_lightnp = render.attach_new_node(sight_light)

        # the following excludes the sights from z-culling (always visible)
        self.left_plasma.set_bin("fixed", 40)
        self.left_plasma.set_depth_test(False)
        self.left_plasma.set_depth_write(False)
        self.left_plasma.set_light(sight_lightnp)
        self.right_plasma.set_bin("fixed", 40)
        self.right_plasma.set_depth_test(False)
        self.right_plasma.set_depth_write(False)
        self.right_plasma.set_light(sight_lightnp)

    def update(self, left_barrel, right_barrel):
        self.do_barrel_raytest(left_barrel, self.left_plasma)
        self.do_barrel_raytest(right_barrel, self.right_plasma)

    def do_barrel_raytest(self, barrel, sight):
        pfrom = barrel.get_pos(self.render)
        pto = pfrom + self.render.get_relative_vector(barrel, Vec3(0,0,-60))
        result = self.physics.ray_test_closest(pfrom, pto, MAP_COLLIDE_BIT | SOLID_COLLIDE_BIT)
        if result.has_hit():
            sight.set_pos(render, result.get_hit_pos())
            obj = False
            nodename = result.get_node().get_name()
            try:
                obj = self.world.objects[nodename]
            except:
                raise
            hostile = getattr(obj, 'hostile', False)
            if hostile is False:
                self.enemy(sight)
            else:
                self.friend(sight)
        else:
            sight.set_pos(render, pto)

    def friend(self, sight):
        sight.find("**/sight").setColor(*SIGHTS_ENEMY_COLOR)
    def enemy(self, sight):
        sight.find("**/sight").setColor(*SIGHTS_FRIENDLY_COLOR)


class LegBones (object):

    motion = [ [ 50]
             , [ 0]
             ]

    TOP = 0
    BOTTOM = 1

    def __init__(self, render, physics, hip, foot, foot_ref, top, bottom):
        self.bones = [(bone, float(bone.get_p()), Point3(bone.get_pos()), motions) for (bone, motions) in zip([top, bottom], self.motion)]
        self.foot_bone = foot
        self.foot_ref = foot_ref
        self.foot_ref.set_hpr(self.foot_ref, 90, 0, 0)
        self.walkfunc_target_node = self.foot_ref.attach_new_node('walkfunc_target')
        self.top_bone = top
        self.bottom_bone = bottom
        self.hip_bone = hip
        self.hip_rest = self.hip_bone.get_pos()
        self.is_on_ground = False
        self.render = render
        self.physics = physics
        self.top_bone_target_angle = self.top_bone.get_p()
        print "top bone angle: %s" % self.top_bone_target_angle
        self.bottom_bone_target_angle = self.bottom_bone.get_p()
        print "bottom bone angle: %s" % self.bottom_bone_target_angle   
        self.crouch_factor = 0

        """walk sequence step varies from -WALKFUNC_STEPS/2 to WALKFUNC_STEPS/2
         with 0 being the top or bottom of the ellipse
         depending on down or up step. -WALKFUNC_STEPS/2 and WALKFUNC_STEPS/2
         are the points of the ellipse where the incrementor
         switches directions between up/down step. this way
         we deal with only one potential y at any x"""
        self.walk_seq_step = 0
        self.up_step = False

        """x input to the ellipse eq. to get y point"""
        self.walkfunc_x = 0
        """sizeparam varies from .001 (a tiny ellipse)
         to 4 (full clip walking cycle ellipse)"""
        self.walkfunc_sizeparam = MIN_WALKFUNC_SIZE_FACTOR


    def _recompute_walkfunc_x(self):
        """compute x and then proportion so that it matches 
        current size vs the maximum size of the ellipse"""
        self.walkfunc_x = abs(self.walk_seq_step) * WALKFUNC_X_LIMIT / (WALKFUNC_STEPS/2)
        self.walkfunc_x = self.walkfunc_x * self.walkfunc_sizeparam / MAX_WALKFUNC_SIZE_FACTOR
        if (self.walk_seq_step < 0):
            self.walkfunc_x = -1 * self.walkfunc_x

    def _increment_walk_seq_step(self):
        if not (-((WALKFUNC_STEPS/2) - 1) < self.walk_seq_step < ((WALKFUNC_STEPS/2) - 1)):
            self.up_step = not self.up_step
        if (self.up_step):
            self.walk_seq_step -= 1
        else:
            self.walk_seq_step += 1

    def _walkfunc_upper(self, x):
        """Defines the upper portion of the ellipse (up step)"""
        return (math.sqrt(3) * math.sqrt(self.walkfunc_sizeparam - (9 * math.pow(self.walkfunc_x, 2))) + (3 * self.walkfunc_x))/6

    def _walkfunc_lower(self, x):
        """Defines the lower portion of the ellipse (down step)"""
        return -1 * (math.sqrt(3)/6) * math.sqrt(self.walkfunc_sizeparam-(9 * math.pow(self.walkfunc_x, 2))) + (.5 * self.walkfunc_x)

    def _get_target_pos(self):
        walkfunc_y = None
        if self.up_step:
            walkfunc_y = self._walkfunc_upper(self.walkfunc_x)
        else:
            walkfunc_y = self._walkfunc_lower(self.walkfunc_x)
        self.walkfunc_target_node.set_pos(self.foot_ref, self.walkfunc_x, walkfunc_y, 0)
        return self.walkfunc_target_node.get_pos(self.foot_ref)

    def bottom_resting_pos(self):
        return self.bones[self.BOTTOM][2] + self.crouch_factor*-50

    def top_resting_pos(self):
        return self.bones[self.TOP][2] + self.crouch_factor*-50

    def get_return(self, return_speed):
        lerps = [LerpFunc(self.update_piece_hpr,
                          fromData=float(bone.get_p()),
                          toData=resting_p,
                          duration=return_speed,
                          extraArgs=[bone, idx])
        for idx, (bone, resting_p, resting_pos, motions) in enumerate(self.bones)]

        return_pos = LerpFunc(self.update_bob,
                              fromData=float(self.top_bone.get_pos().y),
                              toData=self.bones[self.TOP][2].y,
                              duration=return_speed,
                              extraArgs=[self.bones[self.TOP][0]])
        lerps.append(return_pos)
        return lerps

    def update_piece_hpr(self, angle, bone, idx):
        if self.crouch_factor > 0:
            if bone is self.top_bone:
                bone.set_p(angle + (self.crouch_factor*-50))
            if bone is self.bottom_bone:
                bone.set_p(angle + (self.crouch_factor*-50))
        else:
            bone.set_p(angle)

    def update_bob(self, deltay, bone):
        rest_pos = self.bones[self.TOP][2]
        bone.set_pos(rest_pos.x,deltay - (self.crouch_factor * .02), rest_pos.z)


    def get_floor_spot(self):
        l_from = self.foot_bone.get_pos(self.render)
        l_to = self.foot_bone.get_pos(self.render)
        l_from.y += 1
        l_to.y -= .7
        result = self.physics.ray_test_closest(l_from, l_to, MAP_COLLIDE_BIT | SOLID_COLLIDE_BIT)
        if result.has_hit():
            return self.foot_ref.get_relative_point(self.render, result.get_hit_pos())
        else:
            return None

    def ik_leg(self, data):
        floor_pos = self.get_floor_spot()
        target_pos = self._get_target_pos()
        hip_pos = self.hip_bone.get_pos(self.foot_ref)

        if floor_pos and target_pos.y < floor_pos.y:
            floor_pos.x = target_pos.x
            target_vector = hip_pos - floor_pos
            self.is_on_ground = True
        else:
            target_vector = hip_pos - target_pos
            self.is_on_ground = False

        pt_length = target_vector.length()
        if .01 < pt_length < (TOP_LEG_LENGTH + BOTTOM_LEG_LENGTH +.1):
            tt_angle_cos = (math.pow(TOP_LEG_LENGTH, 2) + math.pow(pt_length, 2) - math.pow(BOTTOM_LEG_LENGTH,2))/(2*TOP_LEG_LENGTH*pt_length)
            try:
                target_top_angle = rad2Deg(math.acos(tt_angle_cos))
            except ValueError:
                return

            if target_top_angle and target_top_angle == target_top_angle and -120 < target_top_angle < 100:
                target_vector.normalize()
                self.hip_bone.get_relative_vector(self.foot_ref, target_vector)
                delta = target_vector.get_xy().signed_angle_deg(Vec3.unitY().get_xy())
                self.top_bone.set_p(90 - target_top_angle + delta)

            tb_angle_cos = ((math.pow(TOP_LEG_LENGTH, 2) + math.pow(BOTTOM_LEG_LENGTH, 2) - math.pow(pt_length,2))/(2*TOP_LEG_LENGTH*BOTTOM_LEG_LENGTH))
            target_bottom_angle = rad2Deg(math.acos(tb_angle_cos))

            if target_bottom_angle and target_bottom_angle == target_bottom_angle and -140 < target_bottom_angle < 140:
                self.bottom_bone.set_p((180 - target_bottom_angle) * -1)
        else:
            #print "too long/short: ", pt_length
            return

class Skeleton (object):

    upbob = Vec3(0, 0.05, 0)
    downbob = upbob * -1
    walk_cycle_speed = 1
    return_speed = 0.1


    def __init__(self, left_leg, right_leg, shoulder):
        self.left_leg = left_leg
        self.right_leg = right_leg
        self.shoulder = shoulder
        self.crouch_factor = 0
        self.resting = self.shoulder.get_pos()
        self.return_seq = self._make_return_seq_()
        self.walk_playing = False
        self.lf_sound_played = False
        self.rf_sound_played = False


    def _move_shoulder(self, data, shoulder):
        shoulder.set_pos(self.resting.x, data - (self.crouch_factor * .8), self.resting.z)

    def _make_return_seq_(self):
        lerps = self.right_leg.get_return(self.return_speed) + self.left_leg.get_return(self.return_speed)
        return Parallel(*lerps)

    def stop(self):
        if self.walk_playing:
            self.walk_playing = False
            self.walk_seq.pause()
            self.left_leg.is_on_ground = True
            self.right_leg.is_on_ground = True
            Sequence(self.return_seq).start()

    def setup_footsteps(self, audio3d):
        if audio3d is not None:
            self.lf_sound = audio3d.loadSfx('Sounds/step_mono.wav')
            self.lf_sound.set_balance(0)
            audio3d.attachSoundToObject(self.lf_sound, self.left_leg.foot_bone)
            self.lf_played_since = 0
            self.rf_sound = audio3d.loadSfx('Sounds/step_mono.wav')
            self.rf_sound.set_balance(0)
            audio3d.attachSoundToObject(self.rf_sound, self.right_leg.foot_bone)
            self.rf_played_since = 0

    def update_legs(self, walk, dt, render, physics):
        if self.crouch_factor > 0:
            self.left_leg.crouch_factor = self.crouch_factor
            self.right_leg.crouch_factor = self.crouch_factor
            self.shoulder.set_pos(self.resting.x, self.resting.y - self.crouch_factor * .8, self.resting.z)
        if walk != 0:
            #self.walk()
            self.left_leg.up_step = not self.right_leg.up_step
            for leg in [self.left_leg, self.right_leg]:
                leg.walkfunc_sizeparam = MAX_WALKFUNC_SIZE_FACTOR
                leg._increment_walk_seq_step()
                leg._recompute_walkfunc_x()
                leg.ik_leg(0)
            if self.left_leg.is_on_ground and not self.lf_sound_played:
                self.lf_sound.play()
                self.lf_sound_played = True
            if not self.left_leg.is_on_ground:
                self.lf_sound_played = False
            if self.right_leg.is_on_ground and not self.rf_sound_played:
                self.rf_sound.play()
                self.rf_sound_played = True
            if not self.right_leg.is_on_ground:
                self.rf_sound_played = False
        else:
            self.stop()
            for leg in [self.left_leg, self.right_leg]:
                leg.walkfunc_sizeparam = .001
                leg._recompute_walkfunc_x()
                leg.ik_leg(0)


class Walker (PhysicalObject):

    collide_bits = SOLID_COLLIDE_BIT

    def __init__(self, incarnator, colordict=None, player=False):
        super(Walker, self).__init__()
        self.spawn_point = incarnator
        self.on_ground = False
        self.mass = 150.0 # 220.0 for heavy
        self.xz_velocity = Vec3(0, 0, 0)
        self.y_velocity = Vec3(0, 0, 0)
        self.factors = {
            'forward': 7.5,
            'backward': -7.5,
            'left': 2.0,
            'right': -2.0,
            'crouch': 0.0,
        }
        self.movement = {
            'forward': 0.0,
            'backward': 0.0,
            'left': 0.0,
            'right': 0.0,
            'crouch': 0.0,
        }
        self.head_height = Vec3(0, 1.5, 0)
        self.collides_with = MAP_COLLIDE_BIT | SOLID_COLLIDE_BIT
        self.grenade_loaded = False
        self.energy = 1.0
        self.left_gun_charge = 1.0
        self.right_gun_charge = 1.0
        self.primary_color = [1,1,1,1]
        self.colordict = colordict if colordict else None
        self.crouching = False
        self.player = player
        self.can_jump = False
        self.crouch_impulse = 0

    def get_model_part(self, obj_name):
        return self.actor.find("**/%s" % obj_name)

    def create_node(self):
        self.actor = Actor('walker.egg')
        if self.colordict:
            self.setup_color(self.colordict)
        self.actor.set_pos(*self.spawn_point.pos)
        self.actor.look_at(*self.spawn_point.heading)
        self.spawn_point.was_used()


        self.left_barrel_joint = self.actor.exposeJoint(None, 'modelRoot', 'left_barrel_bone')
        self.right_barrel_joint = self.actor.exposeJoint(None, 'modelRoot', 'right_barrel_bone')

        return self.actor

    def create_solid(self):
        walker_capsule = BulletGhostNode(self.name + "_walker_cap")
        self.walker_capsule_shape = BulletCylinderShape(.7, .2, YUp)
        walker_bullet_np = self.actor.attach_new_node(walker_capsule)
        walker_bullet_np.node().add_shape(self.walker_capsule_shape)
        walker_bullet_np.node().set_kinematic(True)
        walker_bullet_np.set_pos(0,1.5,0)
        walker_bullet_np.wrt_reparent_to(self.actor)
        self.world.physics.attach_ghost(walker_capsule)
        walker_bullet_np.node().setIntoCollideMask(GHOST_COLLIDE_BIT)
        return None

    def setup_shape(self, gnodepath, bone, pname):
        shape = BulletConvexHullShape()

        gnode = gnodepath.node()
        geom = gnode.get_geom(0)
        shape.add_geom(geom)

        node = BulletRigidBodyNode(self.name + pname)
        np = self.actor.attach_new_node(node)
        np.node().add_shape(shape)
        np.node().set_kinematic(True)
        np.wrt_reparent_to(bone)
        self.world.physics.attach_rigid_body(node)
        return np

    def setup_color(self, colordict):
        if colordict.has_key('barrel_color'):
            color = colordict['barrel_color']
            self.get_model_part('left_barrel').setColor(*color)
            self.get_model_part('right_barrel').setColor(*color)
        if colordict.has_key('visor_color'):
            self.get_model_part('visor').setColor(*colordict['visor_color'])
        if colordict.has_key('body_primary_color'):
            color = colordict['body_primary_color']
            self.primary_color = color
            for part in ['hull_primary', 'rt_leg_primary',
                         'lt_leg_primary', 'lb_leg_primary', 'rb_leg_primary',
                         'left_barrel_ring', 'right_barrel_ring', 'hull_bottom']:
                self.get_model_part(part).setColor(*color)
        if colordict.has_key('body_secondary_color'):
            color = colordict['body_secondary_color']
            for part in ['hull_secondary', 'visor_stripe', 'rb_leg_secondary',
                         'rt_leg_secondary', 'lb_leg_secondary', 'lt_leg_secondary']:
                self.get_model_part(part).setColor(*color)
        return

    def attached(self):
        self.integrator = Integrator(self.world.gravity)
        self.world.register_collider(self)
        self.world.register_updater(self)

        pelvis_bone = self.actor.controlJoint(None, 'modelRoot', 'pelvis_bone')

        left_foot_bone = self.actor.exposeJoint(None, 'modelRoot', 'left_foot_bone')
        left_foot_bone_origin_ref = self.actor.attach_new_node("left_foot_reference")
        left_foot_bone_origin_ref.set_pos(left_foot_bone.get_pos())
        #pelvis_bone.attach_new_node(left_foot_bone_origin_ref)

        right_foot_bone = self.actor.exposeJoint(None, 'modelRoot', 'right_foot_bone')
        right_foot_bone_origin_ref = self.actor.attach_new_node("right_foot_reference")
        right_foot_bone_origin_ref.set_pos(right_foot_bone.get_pos())
        #pelvis_bone.attach_new_node(right_foot_bone_origin_ref)

        left_bones = LegBones(
            self.world.render, self.world.physics,
            self.actor.exposeJoint(None, 'modelRoot', 'left_hip_bone'),
            left_foot_bone,
            left_foot_bone_origin_ref,
            *[self.actor.controlJoint(None, 'modelRoot', name) for name in ['left_top_bone', 'left_bottom_bone']]
        )
        right_bones = LegBones(
            self.world.render, self.world.physics,
            self.actor.exposeJoint(None, 'modelRoot', 'right_hip_bone'),
            right_foot_bone,
            right_foot_bone_origin_ref,
            *[self.actor.controlJoint(None, 'modelRoot', name) for name in  ['right_top_bone', 'right_bottom_bone']]
        )

        self.skeleton = Skeleton(left_bones, right_bones, pelvis_bone)
        self.skeleton.setup_footsteps(self.world.audio3d)
        self.head_bone = self.actor.controlJoint(None, 'modelRoot', 'head_bone')
        self.head_bone_joint = self.actor.exposeJoint(None, 'modelRoot', 'head_bone')
        self.loaded_missile = LoadedMissile(self.head_bone_joint, self.primary_color)
        self.loaded_grenade = LoadedGrenade(self.head_bone_joint, self.primary_color)
        if self.player:
            self.sights = Sights(self.left_barrel_joint, self.right_barrel_joint, self.world)



    def collision(self, other, manifold, first):
        world_pt = manifold.get_position_world_on_a() if first else manifold.get_position_world_on_b()
        print self, 'HIT BY', other, 'AT', world_pt

    def handle_command(self, cmd, pressed):
        if cmd is 'crouch' and pressed:
            self.crouching = True
            if self.on_ground:
                self.can_jump = True
        if cmd is 'crouch' and not pressed and self.on_ground and self.can_jump:
            self.crouching = False
            self.y_velocity = Vec3(0, 6.8, 0)
            self.can_jump = False
        if cmd is 'fire' and pressed:
            self.handle_fire()
            return
        if cmd is 'missile' and pressed:
            if self.loaded_grenade.can_fire():
                self.loaded_grenade.toggle_visibility()
            self.loaded_missile.toggle_visibility()
            return
        if cmd is 'grenade' and pressed:
            if self.loaded_missile.can_fire():
                self.loaded_missile.toggle_visibility()
            self.loaded_grenade.toggle_visibility()
            return
        if cmd is 'grenade_fire' and pressed:
            if self.loaded_missile.can_fire():
                self.loaded_missile.toggle_visibility()
            if not self.loaded_grenade.can_fire():
                self.loaded_grenade.toggle_visibility()
            walker_v = Vec3(self.xz_velocity)
            walker_v.y = self.y_velocity.y
            self.loaded_grenade.fire(self.world, walker_v)
            return
        self.movement[cmd] = self.factors[cmd] if pressed else 0.0

    def handle_fire(self):
        if self.loaded_missile.can_fire():
            self.loaded_missile.fire(self.world)
        elif self.loaded_grenade.can_fire():
            walker_v = self.xz_velocity
            walker_v.y = self.y_velocity.y
            self.loaded_grenade.fire(self.world, walker_v)
        else:
            p_energy = 0
            hpr = 0
            if self.left_gun_charge > self.right_gun_charge:
                origin = self.left_barrel_joint.get_pos(self.world.render)
                hpr = self.left_barrel_joint.get_hpr(self.world.render)
                p_energy = self.left_gun_charge
                if p_energy < MIN_PLASMA_CHARGE:
                    return
                self.left_gun_charge = 0
            else:
                origin = self.right_barrel_joint.get_pos(self.world.render)
                hpr = self.right_barrel_joint.get_hpr(self.world.render)
                p_energy = self.right_gun_charge
                if p_energy < MIN_PLASMA_CHARGE:
                    return
                self.right_gun_charge = 0
            hpr.y += 180
            plasma = self.world.attach(Plasma(origin, hpr, p_energy))

    def st_result(self, cur_pos, new_pos):
        return self.world.physics.sweepTestClosest(self.walker_capsule_shape, cur_pos, new_pos, self.collides_with, 0)

    def update(self, dt):
        dt = min(dt, 0.2) # let's just temporarily assume that if we're getting less than 5 fps, dt must be wrong.
        yaw = self.movement['left'] + self.movement['right']
        self.rotate_by(yaw * dt * 60, 0, 0)
        walk = self.movement['forward'] + self.movement['backward']
        start = self.position()
        cur_pos_ts = TransformState.make_pos(self.position() + self.head_height)

        if self.on_ground:
            friction = DEFAULT_FRICTION
        else:
            friction = AIR_FRICTION

        #to debug walk cycle (stay in place)
        #friction = 0

        speed = walk
        pos = self.position()
        self.move_by(0, 0, speed)
        direction = self.position() - pos
        newpos, self.xz_velocity = Friction(direction, friction).integrate(pos, self.xz_velocity, dt)
        self.move(newpos)

        # Cast a ray from just above our feet to just below them, see if anything hits.
        pt_from = self.position() + Vec3(0, 1, 0)
        pt_to = pt_from + Vec3(0, -1.1, 0)
        result = self.world.physics.ray_test_closest(pt_from, pt_to, MAP_COLLIDE_BIT | SOLID_COLLIDE_BIT)

        # this should return 'on ground' information
        self.skeleton.update_legs(walk, dt, self.world.render, self.world.physics)

        if self.y_velocity.get_y() <= 0 and result.has_hit():
            self.on_ground = True
            self.crouch_impulse = self.y_velocity.y
            self.y_velocity = Vec3(0, 0, 0)
            self.move(result.get_hit_pos())
            self.skeleton.left_leg_on_ground = True
            self.skeleton.right_leg_on_ground = True
        else:
            self.on_ground = False
            current_y = Point3(0, self.position().get_y(), 0)
            y, self.y_velocity = self.integrator.integrate(current_y, self.y_velocity, dt)
            self.move(self.position() + (y - current_y))

        if self.crouching and self.skeleton.crouch_factor < 1:
            self.skeleton.crouch_factor += (dt*60)/10
            self.skeleton.update_legs(0, dt, self.world.render, self.world.physics)
        elif not self.crouching and self.skeleton.crouch_factor > 0:
            self.skeleton.crouch_factor -= (dt*60)/10
            self.skeleton.update_legs(0, dt, self.world.render, self.world.physics)

        #if self.crouch_impulse < 0:

        goal = self.position()
        adj_dist = abs((start - goal).length())
        new_pos_ts = TransformState.make_pos(self.position() + self.head_height)

        sweep_result = self.st_result(cur_pos_ts, new_pos_ts)
        count = 0
        while sweep_result.has_hit() and count < 10:
            moveby = sweep_result.get_hit_normal()
            self.xz_velocity = -self.xz_velocity.cross(moveby).cross(moveby)
            moveby.normalize()
            moveby *= adj_dist * (1 - sweep_result.get_hit_fraction())
            self.move(self.position() + moveby)
            new_pos_ts = TransformState.make_pos(self.position() + self.head_height)
            sweep_result = self.st_result(cur_pos_ts, new_pos_ts)
            count += 1

        if self.energy > WALKER_MIN_CHARGE_ENERGY:
            if self.left_gun_charge < 1:
                self.energy -= WALKER_ENERGY_TO_GUN_CHARGE[0]
                self.left_gun_charge += WALKER_ENERGY_TO_GUN_CHARGE[1]
            else:
                self.left_gun_charge = math.floor(self.left_gun_charge)

            if self.right_gun_charge < 1:
                self.energy -= WALKER_ENERGY_TO_GUN_CHARGE[0]
                self.right_gun_charge += WALKER_ENERGY_TO_GUN_CHARGE[1]
            else:
                self.right_gun_charge = math.floor(self.right_gun_charge)

        if self.energy < 1:
            self.energy += WALKER_RECHARGE_FACTOR * (dt)

        if self.player:
            self.sights.update(self.left_barrel_joint, self.right_barrel_joint)





