from panda3d.core import *
from direct.actor.Actor import Actor
from world import *

class Hat (object):

    def __init__(self, actor):
        self.missile_loaded = False
        self.loaded_missile = load_model('missile.egg')
        self.loaded_missile.hide()
        self.loaded_missile.reparentTo(actor)
        self.loaded_missile.set_pos(self.loaded_missile, *MISSILE_OFFSET)
        self.loaded_missile.set_scale(MISSILE_SCALE)
        main_engines = self.loaded_missile.find('**/mainengines')
        main_engines.set_color(.2,.2,.2)
        wing_engines = self.loaded_missile.find('**/wingengines')
        wing_engines.set_color(.2,.2,.2)
        body = self.loaded_missile.find('**/bodywings')
        body.set_color(*MISSILE_BODY_COLOR)

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
        world.attach(Missile(origin, hpr))
        self.missile_loaded = False
        self.loaded_missile.hide()


class LegBones (object):

    motion = [ [Vec3(0, p, 0) for p in [ 50, -5, -60,  0]]
             , [Vec3(0, p, 0) for p in [ 20,  -40,  -10, -18]]
             ]
    TOP = 0
    BOTTOM = 1

    def __init__(self, top, bottom):
        self.bones = [(bone, bone.get_hpr(), bone.get_pos(), motions) for (bone, motions) in zip([top, bottom], self.motion)]

    def bottom_resting_pos(self):
        return self.bones[self.BOTTOM][2]

    def top_resting_pos(self):
        return self.bones[self.TOP][2]

    def get_walk_seq(self, stage, walk_cycle_speed, bob):
        lerps = [LerpHprInterval(bone, walk_cycle_speed, resting_hpr + motions[stage]) for (bone, resting_hpr, resting_pos, motions) in self.bones]
        bob = LerpPosInterval(self.bones[self.TOP][0], walk_cycle_speed, self.bones[self.TOP][2] + bob)
        lerps.append(bob)
        return lerps

    def get_return(self, return_speed):
        lerps = [LerpHprInterval(bone, return_speed, resting_hpr) for (bone, resting_hpr, resting_pos, motions) in self.bones]
        return_pos = LerpPosInterval(self.bones[self.TOP][0], return_speed, self.bones[self.TOP][2])
        lerps.append(return_pos)
        return lerps


class Skeleton (object):

    upbob = Vec3(0, 0.05, 0)
    downbob = upbob * -1
    walk_cycle_speed = 0.8
    return_speed = 0.1


    def __init__(self, left_leg, right_leg, shoulder):
        self.left_leg = left_leg
        self.right_leg = right_leg
        self.shoulder = shoulder
        self.resting = [self.shoulder.get_pos(), self.left_leg.top_resting_pos(), self.right_leg.top_resting_pos()] # :/
        self.walk_seq = self._make_walk_seq_()
        self.return_seq = self._make_return_seq_()
        self.walk_playing = False

    def _make_walk_seq_(self):
        # TODO: We definitely need more than four segments in the walk loop.
        # We also need to have separate loops for backwards and forwards walking.

        ws = self.walk_cycle_speed / 4.0
        up_interval = [LerpPosInterval(self.shoulder, ws, self.resting[0] + self.upbob)]
        down_interval = [LerpPosInterval(self.shoulder, ws, self.resting[0] + self.downbob)]
        steps = [ self.right_leg.get_walk_seq(0,ws, self.upbob) + self.left_leg.get_walk_seq(2,ws, self.upbob) + up_interval
                , self.right_leg.get_walk_seq(1,ws, self.downbob) + self.left_leg.get_walk_seq(3,ws, self.downbob) + down_interval
                , self.right_leg.get_walk_seq(2,ws, self.upbob) + self.left_leg.get_walk_seq(0,ws,self.upbob) + up_interval
                , self.right_leg.get_walk_seq(3,ws, self.downbob) + self.left_leg.get_walk_seq(1,ws,self.downbob) + down_interval
                ]
        steps = [Parallel(*step) for step in steps]
        return Sequence(*steps)

    def _make_return_seq_(self):
        lerps = self.right_leg.get_return(self.return_speed) + self.left_leg.get_return(self.return_speed)
        lerps.append(LerpPosInterval(self.shoulder, self.return_speed, self.resting[0]))
        print lerps
        return Parallel(*lerps)

    def walk(self):
        if not self.walk_playing:
            self.walk_playing = True
            self.walk_seq.loop()

    def stop(self):
        if self.walk_playing:
            self.walk_playing = False
            self.walk_seq.pause()
            self.return_seq.start()


class Hector (PhysicalObject):

    collide_bits = SOLID_COLLIDE_BIT

    def __init__(self, incarnator):
        super(Hector, self).__init__()

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

    def get_model_part(self, obj_name):
        return self.actor.find("**/%s" % obj_name)

    def create_node(self):
        self.actor = Actor('walker.egg')
        self.actor.set_pos(*self.spawn_point.pos)
        self.actor.look_at(*self.spawn_point.heading)
        self.spawn_point.was_used()
        self.loaded_missile = Hat(self.actor)

        left_bones = LegBones(*[self.actor.controlJoint(None, 'modelRoot', name) for name in ['leftTopBone', 'leftBottomBone']])
        right_bones = LegBones(*[self.actor.controlJoint(None, 'modelRoot', name) for name in ['rightTopBone', 'rightBottomBone']])

        self.skeleton = Skeleton(left_bones, right_bones, self.actor.controlJoint(None, 'modelRoot', 'shoulderBone'))
        self.left_foot_joint = self.actor.exposeJoint(None, 'modelRoot', 'leftFootBone')
        self.right_foot_joint = self.actor.exposeJoint(None, 'modelRoot', 'rightFootBone')
        self.left_barrel_joint = self.actor.exposeJoint(None, 'modelRoot', 'leftBarrelBone')
        self.right_barrel_joint = self.actor.exposeJoint(None, 'modelRoot', 'rightBarrelBone')
        return self.actor

    def create_solid(self):
        hector_capsule = BulletGhostNode(self.name + "_hect_cap")
        self.hector_capsule_shape = BulletCylinderShape(.7, .2, YUp)
        hector_bullet_np = self.actor.attach_new_node(hector_capsule)
        hector_bullet_np.node().add_shape(self.hector_capsule_shape)
        hector_bullet_np.node().set_kinematic(True)
        hector_bullet_np.set_pos(0,1.5,0)
        hector_bullet_np.wrt_reparent_to(self.actor)
        self.world.physics.attach_ghost(hector_capsule)
        hector_bullet_np.node().setIntoCollideMask(GHOST_COLLIDE_BIT)
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
        if colordict.has_key('barrel_outer_color'):
            color = colordict['barrel_outer_color']
            self.get_model_part('L_barrel_outer').setColor(*color)
            self.get_model_part('R_barrel_outer').setColor(*color)
        if colordict.has_key('barrel_inner_color'):
            color = colordict['barrel_inner_color']
            self.get_model_part('R_barrel_inner').setColor(*color)
            self.get_model_part('L_barrel_inner').setColor(*color)
        if colordict.has_key('visor_color'):
            self.get_model_part('visor').setColor(*colordict['visor_color'])
        if colordict.has_key('body_primary_color'):
            color = colordict['body_primary_color']
            for part in ['head_primary', 'shoulders_primary', 'RT_leg_primary',
                         'LT_leg_primary', 'LB_leg_primary', 'RB_leg_primary']:
                self.get_model_part(part).setColor(*color)
        if colordict.has_key('body_secondary_color'):
            color = colordict['body_secondary_color']
            for part in ['head_secondary', 'shoulders_secondary', 'RB_leg_secondary',
                         'RT_leg_secondary', 'LB_leg_secondary', 'LB_leg_secondary']:
                self.get_model_part(part).setColor(*color)
        if colordict.has_key('engines'):
            color = colordict['engines']
            self.get_model_part('engines').setColor(*color)
        return

    def attached(self):
        self.integrator = Integrator(self.world.gravity)
        self.world.register_collider(self)
        self.world.register_updater(self)
        self.lf_sound = self.world.audio3d.loadSfx('Sounds/step_mono.wav')
        self.lf_sound.set_balance(0)
        self.world.audio3d.attachSoundToObject(self.lf_sound, self.left_foot_joint)
        self.lf_played_since = 0
        self.rf_sound = self.world.audio3d.loadSfx('Sounds/step_mono.wav')
        self.rf_sound.set_balance(0)
        self.world.audio3d.attachSoundToObject(self.rf_sound, self.right_foot_joint)
        self.rf_played_since = 0


    def collision(self, other, manifold, first):
        world_pt = manifold.get_position_world_on_a() if first else manifold.get_position_world_on_b()
        print self, 'HIT BY', other, 'AT', world_pt

    def handle_command(self, cmd, pressed):
        if cmd is 'crouch' and not pressed and self.on_ground:
            self.y_velocity = Vec3(0, 6.8, 0)
        if cmd is 'fire' and pressed:
            self.handle_fire()
            return
        if cmd is 'missile' and pressed:
            self.loaded_missile.toggle_visibility()
            return
        self.movement[cmd] = self.factors[cmd] if pressed else 0.0

    def handle_fire(self):
        if self.loaded_missile.can_fire():
            self.loaded_missile.fire(self.world)
        elif self.grenade_loaded:
            pass
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

        self.update_legs(walk,dt)
        if self.y_velocity.get_y() <= 0 and result.has_hit():
            self.on_ground = True
            floor_node = result.get_node()
            #print "standing on: ", floor_node
            self.y_velocity = Vec3(0, 0, 0)
            self.move(result.get_hit_pos())
        else:
            self.on_ground = False
            current_y = Point3(0, self.position().get_y(), 0)
            y, self.y_velocity = self.integrator.integrate(current_y, self.y_velocity, dt)

            self.move(self.position() + (y - current_y))
        goal = self.position()
        adj_dist = abs((start - goal).length())
        new_pos_ts = TransformState.make_pos(self.position() + self.head_height)

        sweep_result = self.world.physics.sweepTestClosest(self.hector_capsule_shape, cur_pos_ts, new_pos_ts, self.collides_with, 0)
        count = 0
        while sweep_result.has_hit() and count < 10:
            moveby = sweep_result.get_hit_normal()
            self.xz_velocity = -self.xz_velocity.cross(moveby).cross(moveby)
            moveby.normalize()
            moveby *= adj_dist * (1 - sweep_result.get_hit_fraction())
            self.move(self.position() + moveby)
            new_pos_ts = TransformState.make_pos(self.position() + self.head_height)
            sweep_result = self.world.physics.sweepTestClosest(self.hector_capsule_shape, cur_pos_ts, new_pos_ts, self.collides_with, 0)
            count += 1

        if self.energy > HECTOR_MIN_CHARGE_ENERGY:
            if self.left_gun_charge < 1:
                self.energy -= HECTOR_ENERGY_TO_GUN_CHARGE[0]
                self.left_gun_charge += HECTOR_ENERGY_TO_GUN_CHARGE[1]
            else:
                self.left_gun_charge = math.floor(self.left_gun_charge)

            if self.right_gun_charge < 1:
                self.energy -= HECTOR_ENERGY_TO_GUN_CHARGE[0]
                self.right_gun_charge += HECTOR_ENERGY_TO_GUN_CHARGE[1]
            else:
                self.right_gun_charge = math.floor(self.right_gun_charge)

        if self.energy < 1:
            self.energy += HECTOR_RECHARGE_FACTOR * (dt)


    def update_legs(self, walk, dt):
        if walk != 0:
            self.skeleton.walk()
            lf_from = self.left_foot_joint.get_pos(self.world.render)
            lf_to = self.left_foot_joint.get_pos(self.world.render)
            lf_to.y -= .3
            left_foot_result = self.world.physics.ray_test_closest(lf_from, lf_to, MAP_COLLIDE_BIT | SOLID_COLLIDE_BIT)
            self.lf_played_since += dt
            if left_foot_result.has_hit() and self.lf_played_since > .7:
                self.lf_sound.play()
                self.lf_played_since = 0

            rf_from = self.right_foot_joint.get_pos(self.world.render)
            rf_to = self.right_foot_joint.get_pos(self.world.render)
            rf_to.y -= .3
            right_foot_result = self.world.physics.ray_test_closest(rf_from, rf_to, MAP_COLLIDE_BIT | SOLID_COLLIDE_BIT)
            self.rf_played_since += dt
            if right_foot_result.has_hit() and self.rf_played_since > .7:
                self.rf_sound.play()
                self.rf_played_since = 0
        else:
            self.skeleton.stop()
            self.lf_sound.stop()
            self.rf_sound.stop()
