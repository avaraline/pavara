import sys
from panda3d.core import PandaNode, NodePath, Vec3
from pavara.walker import Walker
from pavara.keymaps import KeyMaps
from pavara.map_objects import Block 
from pavara.effects import FreeSolid


class LocalPlayer (object):
    def __init__(self, mapobj, showbase):
        self.x = None
        self.y = None
        self.win = showbase.win
        self.map = mapobj
        self.mouseWatcherNode = showbase.mouseWatcherNode
        self.accept = showbase.accept
        self.camera = showbase.camera
        self.setup_input()

        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(showbase.render)
        self.up = Vec3(0, 1, 0)

        incarn = self.map.world.get_incarn()
        walker_color_dict = {
            "barrel_color": [219.0/255, 16.0/255, 50.0/255],
            "visor_color": [157.0/255, 14.0/255, 48.0/255],
            "body_primary_color": [44.0/255, 31.0/255, 54.0/255],
            "body_secondary_color": [80.0/255, 44.0/255, 62.0/255]
        }
        self.walker = self.map.world.attach(Walker(incarn, colordict=walker_color_dict, player=True))
        taskMgr.add(self.move, 'move')

    def setup_input(self):
        self.key_map = {'cam_forward': 0
                      , 'cam_left': 0
                      , 'cam_backward': 0
                      , 'cam_right': 0
                      , 'left': 0
                      , 'right': 0
                      , 'forward': 0
                      , 'backward': 0
                      , 'rotateLeft': 0
                      , 'rotateRight': 0
                      , 'walkForward': 0
                      , 'crouch': 0
                      , 'fire': 0
                      , 'missile': 0
                      , 'grenade_fire': 0
                      , 'grenade': 0
                      , 'print_cam': 0
                      }
        self.accept('escape', sys.exit)
        self.accept('p', self.drop_blocks)

        for key,cmd in KeyMaps.flycam_input_settings:
            self.accept(key, self.set_key, [cmd, 1])
            self.accept(key+"-up", self.set_key, [cmd, 0])

    def move(self, task):
        dt = globalClock.getDt()
        if self.mouseWatcherNode.hasMouse():
            oldx = self.x
            oldy = self.y
            md = self.win.getPointer(0)
            self.x = md.getX()
            self.y = md.getY()
            centerx = self.win.getProperties().getXSize()/2
            centery = self.win.getProperties().getYSize()/2
            self.win.movePointer(0, centerx, centery)

            if (oldx is not None):
                self.floater.setPos(self.camera, 0, 0, 0)
                self.floater.setHpr(self.camera, 0, 0, 0)
                self.floater.setH(self.floater, (centerx-self.x) * 10 * dt)
                p = self.floater.getP()
                self.floater.setP(self.floater, (centery-self.y) * 10 * dt)
                self.floater.setZ(self.floater, -1)
                angle = self.up.angleDeg(self.floater.getPos() - self.camera.getPos())
                if 10 > angle or angle > 170:
                    self.floater.setPos(self.camera, 0, 0, 0)
                    self.floater.setP(p)
                    self.floater.setZ(self.floater, -1)
                self.camera.lookAt(self.floater.getPos(), self.up)
        else:
            self.x = None
            self.y = None

        if (self.key_map['cam_forward']):
            self.camera.setZ(self.camera, -25 * dt)
        if (self.key_map['cam_backward']):
            self.camera.setZ(self.camera, 25 * dt)
        if (self.key_map['cam_left']):
            self.camera.setX(self.camera, -25 * dt)
        if (self.key_map['cam_right']):
            self.camera.setX(self.camera, 25 * dt)
        if (self.key_map['print_cam']):
            print "CAMERA: Pos - %s, Hpr - %s" % (self.camera.get_pos(), self.camera.get_hpr())
            self.key_map['print_cam'] = 0

        self.walker.handle_command('forward', self.key_map['forward'])
        self.walker.handle_command('left', self.key_map['left'])
        self.walker.handle_command('backward', self.key_map['backward'])
        self.walker.handle_command('right', self.key_map['right'])
        self.walker.handle_command('crouch', self.key_map['crouch'])

        self.walker.handle_command('fire', self.key_map['fire'])
        if self.key_map['fire']: self.key_map['fire'] = 0
        self.walker.handle_command('missile', self.key_map['missile'])
        if self.key_map['missile']: self.key_map['missile'] = 0
        self.walker.handle_command('grenade_fire', self.key_map['grenade_fire'])
        if self.key_map['grenade_fire']: self.key_map['grenade_fire'] = 0
        self.walker.handle_command('grenade', self.key_map['grenade'])
        if self.key_map['grenade']: self.key_map['grenade'] = 0

        return task.cont

    def set_key(self, key, value):
        self.key_map[key] = value

    def drop_blocks(self):
        block = self.map.world.attach(FreeSolid(Block((1, 1, 1), (1, 0, 0, 1), 0.01, (0, 40, 0), (0, 0, 0)), 0.01))
        for i in range(10):
            rand_pos = (random.randint(-25, 25), 40, random.randint(-25, 25))
            block = self.map.world.attach(FreeSolid(Block((1, 1, 1), (1, 0, 0, 1), 0.01, rand_pos, (0, 0, 0)), 0.01))
