import sys
from panda3d.core import *
from pandac.PandaModules import WindowProperties
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
import MapLoader
from Hector import Hector

class Pavara(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.x = None
        self.y = None
        
        # init panda3d crap
        self.initP3D()
        
        # load level

        MapLoader.load('Maps/phosphorus.xml', render)
        #render.attachNewNode(MapLoader.makeBox((1, 0, 0, 1), (0, 0, 0), 1000, 0.5, 0.5))
        #render.attachNewNode(MapLoader.makeBox((0, 1, 0, 1), (0, 0, 0), 0.5, 1000, 0.5))
        #render.attachNewNode(MapLoader.makeBox((0, 0, 1, 1), (0, 0, 0), 0.5, 0.5, 1000))
        self.h = Hector(render, 0, 12, 14)
        node = GeomNode('sky')
        bounds = base.camLens.make_bounds()
        dl = bounds.getMin()
        ur = bounds.getMax()
        z = dl.getZ() * 0.99
        node.addGeom(MapLoader.makeSquare((1,1,1,1), dl.getX(), dl.getY(), 0, ur.getX(), ur.getY(), 0))
        node = render.attachNewNode(node)
        node.reparentTo(base.camera)
        node.setPos(base.camera, 0,0, z)
        self.shader = Shader.load('Shaders/Sky.sha')
        node.setShader(self.shader)
        render.setShaderInput('camera', base.cam)
        render.setShaderInput('sky', node)
        render.setShaderInput('m_skyColor', Vec4(0, 0, 0, 0))
        render.setShaderInput('m_horizonColor', Vec4(0.15, 0, 0.3, 0))
        render.setShaderInput('m_groundColor', Vec4(0.15, 0.15, 0.15, 0.15))
        render.setShaderInput('m_gradientHeight', 0.05, 0.05, 0.05, 0.05)
        self.sky = node


    def initP3D(self):
        self.setupInput()
        self.collisionTraverser = CollisionTraverser()
        self.collisionHandler = CollisionHandlerQueue()
        self.collisionTraverser.showCollisions(render)
        base.cTrav = self.collisionTraverser
        taskMgr.add(self.move,'moveTask')
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

    def setKey(self, key, value):
        self.keyMap[key] = value
        
    def setupCollision(self, m):
        self.worldColNode = CollisionNode('worldSolids')
        for s in m.solids:
            self.worldColNode.addSolid(s)
        self.worldColNode.setFromCollideMask(BitMask32.allOff())
        self.worldColNode.setIntoCollideMask(BitMask32.bit(1))
        
        self.worldColNp = self.render.attachNewNode(self.worldColNode)
        self.worldColNp.show()
    
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

if __name__ == '__main__':
    loadPrcFile('pavara.prc')
    p = Pavara()
    p.run()
