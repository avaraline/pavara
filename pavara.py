import sys
from panda3d.core import *
from panda3d.ode import *
from pandac.PandaModules import WindowProperties
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
import MapLoader
from Hector import Hector
from random import randint, random
from wireGeom import wireGeom

class Pavara(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.x = None
        self.y = None
        
        # init panda3d crap
        self.initP3D()
        
        # load level

        MapLoader.load('Maps/phosphorus.xml', render, self.physSpace)
        #render.attachNewNode(MapLoader.makeBox((1, 0, 0, 1), (0, 0, 0), 1000, 0.5, 0.5))
        #render.attachNewNode(MapLoader.makeBox((0, 1, 0, 1), (0, 0, 0), 0.5, 1000, 0.5))
        #render.attachNewNode(MapLoader.makeBox((0, 0, 1, 1), (0, 0, 0), 0.5, 0.5, 1000))

        self.h = Hector(render, 0, 12, 14, 90)

    def initP3D(self):
        self.setupInput()
        self.setupCollision(render)     
        
        #self.globalClock = globalClock
        
        base.setBackgroundColor(0,0,0)
        base.enableParticles()
        base.disableMouse()
        render.setAntialias(AntialiasAttrib.MAuto)
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)
        base.camera.setPos(0,20,40)
        base.camera.setHpr(0,0,0)
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)
        self.up = Vec3(0, 1, 0)
        taskMgr.add(self.move, 'move')
        taskMgr.doMethodLater(0.5, self.stepPhysics, "Physics Simulation")

    def setKey(self, key, value):
        self.keyMap[key] = value
    
    def setupCollision(self, render):
        self.physWorld = OdeWorld()
        self.physWorld.setGravity(0,-9.81,0)
        
        self.physWorld.initSurfaceTable(1)
        self.physWorld.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
        
        self.physSpace = OdeSimpleSpace()
        self.physSpace.setAutoCollideWorld(self.physWorld)
        
        self.contactgroup = OdeJointGroup()
        self.physSpace.setAutoCollideJointGroup(self.contactgroup)
        
        testmodel = loader.loadModel('hector_b2.4_anim.egg')
        testmodel.setScale(.5)
        
        self.objects = []
        for i in range(randint(15,20)):
            testnp = testmodel.copyTo(render)
            testnp.setPos(randint(-10, 10), 13, randint(-14, 15) + random())
            testnp.setHpr(randint(-45, 45), 13, randint(-45, 45))
            boxBody = OdeBody(self.physWorld)
            M = OdeMass()
            M.setBox(50,1,1,1)
            boxBody.setMass(M)
            boxBody.setPosition(testnp.getPos(render))
            boxBody.setQuaternion(testnp.getQuat(render))
            boxGeom = OdeBoxGeom(self.physSpace, 1,1,1)
            boxGeom.setCollideBits(BitMask32(0x00000002))
            boxGeom.setCategoryBits(BitMask32(0x00000001))
            boxGeom.setBody(boxBody)
            
            boxDebugShape = wireGeom().generate('box',extents = (1,1,1))
            boxDebugShape.reparentTo(render)
            boxDebugShape.setPos(testnp.getPos(render))
            boxDebugShape.setQuat(testnp.getQuat(render))
            
            
            self.objects.append((testnp, boxBody, boxDebugShape))
        
        groundGeom = OdePlaneGeom(self.physSpace, Vec4(0, 1, 0, 0))
        groundGeom.setCollideBits(BitMask32(0x00000001))
        groundGeom.setCategoryBits(BitMask32(0x00000002))
        
        self.dtAccumulator = 0.0
        self.physStepSize = 1.0/90.0
        
    
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
        self.accept('w', self.setKey, ['forward', 1])
        self.accept('w-up', self.setKey, ['forward', 0])
        self.accept('a', self.setKey, ['left', 1])
        self.accept('a-up', self.setKey, ['left', 0])
        self.accept('s', self.setKey, ['backward', 1])
        self.accept('s-up', self.setKey, ['backward', 0])
        self.accept('d', self.setKey, ['right', 1])
        self.accept('d-up', self.setKey, ['right', 0])
        self.accept('j', self.setKey, ['rotateLeft', 1])
        self.accept('j-up', self.setKey, ['rotateLeft', 0])
        self.accept('k', self.setKey, ['rotateRight', 1])
        self.accept('k-up', self.setKey, ['rotateRight', 0])
        self.accept('n', self.setKey, ['walkForward', 1])
        self.accept('n-up', self.setKey, ['walkForward', 0])
        self.accept('m', self.setKey, ['crouch', 1])
        self.accept('m-up', self.setKey, ['crouch', 0])
        
    def move(self, task):
        dt = globalClock.getDt()
        if base.mouseWatcherNode.hasMouse():
            oldx = self.x
            oldy = self.y
            self.x=base.mouseWatcherNode.getMouseX()
            self.y=base.mouseWatcherNode.getMouseY()
            centerx = base.win.getProperties().getXSize()/2
            centery = base.win.getProperties().getYSize()/2
            base.win.movePointer(0,centerx,centery)

            if (oldx is not None):
                self.floater.setPos(base.camera, 0, 0, 0)
                self.floater.setHpr(base.camera, 0, 0, 0)
                self.floater.setH(self.floater, -self.x * 3000 * dt)
                p = self.floater.getP()
                self.floater.setP(self.floater, self.y * 3000 * dt)
                self.floater.setZ(self.floater, -1)
                angle = self.up.angleDeg(self.floater.getPos() - base.camera.getPos())
                if 10 > angle or angle > 170:
                    self.floater.setPos(base.camera, 0, 0, 0)
                    self.floater.setP(p)
                    self.floater.setZ(self.floater, -1)
                base.camera.lookAt(self.floater.getPos(), self.up)
        else:
            self.x = None
            self.y = None
        if (self.keyMap['forward']):
            base.camera.setZ(base.camera, -25 * dt)
        if (self.keyMap['backward']):
            base.camera.setZ(base.camera, 25 * dt)
        if (self.keyMap['left']):
            base.camera.setX(base.camera, -25 * dt)
        if (self.keyMap['right']):
            base.camera.setX(base.camera, 25 * dt)
        if (self.keyMap['rotateLeft']):
            self.h.rotateLeft()
        if (self.keyMap['rotateRight']):
            self.h.rotateRight()  
            
        if (self.keyMap['crouch']):
            self.h.crouch()
        else: 
            self.h.uncrouch()
               
        if (self.keyMap['walkForward']):
            self.h.walk()
        else:
            self.h.unwalk()

        #render.setShaderInput('m_camToWorld.mat4', base.camLens.getProjectionMat())
        #self.sky.setShaderInput('m_cameraPosition.vec3', base.cam.getPos())        
        
        
        
        return task.cont
    
    
    def stepPhysics(self, task):
        dt = globalClock.getDt()
        self.physSpace.autoCollide()
        #self.physWorld.quickStep(dt)
        self.dtAccumulator += dt
        while self.dtAccumulator > self.physStepSize:
        	self.dtAccumulator -= self.physStepSize
        	self.physWorld.quickStep(self.physStepSize)
        for np, body, dbgnp in self.objects:
            np.setPosQuat(render, body.getPosition(), Quat(body.getQuaternion()))
            np.setPos(np, 0,-1,0)
            dbgnp.setPosQuat(render, body.getPosition(), Quat(body.getQuaternion()))
        self.contactgroup.empty()
        return task.cont

if __name__ == '__main__':
    loadPrcFile('pavara.prc')
    p = Pavara()
    p.run()
