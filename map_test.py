import sys, random
from panda3d.core import *
from pandac.PandaModules import WindowProperties
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase

from pavara.maps import load_maps
from pavara.world import Block, Hector

class Pavara (ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.x = None
        self.y = None

        # init panda3d crap
        self.initP3D()

        maps = load_maps('Maps/bodhi.xml', self.cam)
        for map in maps:
            print map.name, '--', map.author
        self.map = maps[0]

        # Testing physical hector.


        self.hector = self.map.world.attach(Hector())
        self.hector.setupColor({"barrel_color": Vec3(.4,.7,.4), "barrel_trim_color": Vec3(.8,.9,.6),
                         "visor_color": Vec3(.3,.6,1), "body_color":Vec3(.2,.5,.3)})
        self.hector.move((0, 15, 0))

        self.setupInput()

        # Put the hector in the World's render so the lighting applies correctly.
        #self.h = HectorActor(self.map.world.render, 0, 13, 14, 90)

        self.map.show(self.render)
        taskMgr.add(self.map.world.update, 'worldUpdateTask')

        #axes = loader.loadModel('models/yup-axis')
        #axes.setScale(10)
        #axes.reparentTo(render)

    def initP3D(self):
        self.setBackgroundColor(0,0,0)
        self.enableParticles()
        self.disableMouse()
        render.setAntialias(AntialiasAttrib.MAuto)
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)
        self.camera.setPos(0,20,40)
        self.camera.setHpr(0,0,0)
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)
        self.up = Vec3(0, 1, 0)
        taskMgr.add(self.move, 'move')

    def setKey(self, key, value):
        self.keyMap[key] = value

    def drop_blocks(self):
        block = self.map.world.attach(Block((1, 1, 1), (1, 0, 0, 1), 0.01))
        block.move((0, 40, 0))
        for i in range(10):
            block = self.map.world.attach(Block((1, 1, 1), (1, 0, 0, 1), 0.01))
            block.move((random.randint(-25, 25), 40, random.randint(-25, 25)))

    def setupInput(self):
        self.keyMap = { 'left': 0
                      , 'right': 0
                      , 'forward': 0
                      , 'backward': 0
                      , 'rotateLeft': 0
                      , 'rotateRight': 0
                      , 'walkForward': 0
                      , 'crouch': 0
                      }
        self.accept('escape', sys.exit)
        self.accept('p', self.drop_blocks)
        self.accept('w', self.setKey, ['forward', 1])
        self.accept('w-up', self.setKey, ['forward', 0])
        self.accept('a', self.setKey, ['left', 1])
        self.accept('a-up', self.setKey, ['left', 0])
        self.accept('s', self.setKey, ['backward', 1])
        self.accept('s-up', self.setKey, ['backward', 0])
        self.accept('d', self.setKey, ['right', 1])
        self.accept('d-up', self.setKey, ['right', 0])
        # Hector movement.
        self.accept('i',        self.hector.handle_command, ['forward', True])
        self.accept('i-up',     self.hector.handle_command, ['forward', False])
        self.accept('j',        self.hector.handle_command, ['left', True])
        self.accept('j-up',     self.hector.handle_command, ['left', False])
        self.accept('k',        self.hector.handle_command, ['backward', True])
        self.accept('k-up',     self.hector.handle_command, ['backward', False])
        self.accept('l',        self.hector.handle_command, ['right', True])
        self.accept('l-up',     self.hector.handle_command, ['right', False])
        self.accept('shift',    self.hector.handle_command, ['crouch', True])
        self.accept('shift-up', self.hector.handle_command, ['crouch', False])

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
            self.win.movePointer(0,centerx,centery)

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
        if (self.keyMap['forward']):
            self.camera.setZ(self.camera, -25 * dt)
        if (self.keyMap['backward']):
            self.camera.setZ(self.camera, 25 * dt)
        if (self.keyMap['left']):
            self.camera.setX(self.camera, -25 * dt)
        if (self.keyMap['right']):
            self.camera.setX(base.camera, 25 * dt)

        return task.cont

if __name__ == '__main__':
    loadPrcFile('pavara.prc')
    p = Pavara()
    p.run()
