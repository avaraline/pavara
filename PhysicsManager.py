from panda3d.ode import *
from panda3d.core import BitMask32, Vec4, Quat
from wireGeom import wireGeom
from random import randint, random

DEBUG_MAP_COLLISION = False
MAP_COLLIDE_BIT = BitMask32(0x00000001)
MAP_COLLIDE_CATEGORY = BitMask32(0x00000002)

class PhysicsManager(object):
    def __init__(self, render):
        self.render = render
        self.physWorld = OdeWorld()
        self.physWorld.setGravity(0,-9.81,0)
        
        self.physWorld.initSurfaceTable(1)
        self.physWorld.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
        
        self.physSpace = OdeSimpleSpace()
        self.physSpace.setAutoCollideWorld(self.physWorld)
        
        self.contactgroup = OdeJointGroup()
        self.physSpace.setAutoCollideJointGroup(self.contactgroup)
        
        self.freesolids = []
        self.hectors = []
        
        groundGeom = OdePlaneGeom(self.physSpace, Vec4(0, 1, 0, 0))
        groundGeom.setCollideBits(BitMask32(0x00000001))
        groundGeom.setCategoryBits(BitMask32(0x00000002))
        
        self.dtAccumulator = 0.0
        self.physStepSize = 1.0/90.0
        
    def addHector(self, h):
        #make physics body
        mainBody = OdeBody(self.physWorld)
        M = OdeMass()
        M.setCapsuleTotal(120, 1, .5, 2)
        mainBody.setMass(M)
        mainBody.setPosition(h.model.getPos())
        mainBody.setQuaternion(h.model.getQuat(self.render))
        return
    
    def stepPhysics(self, task):
        dt = globalClock.getDt()
        self.physSpace.autoCollide()
        self.physWorld.quickStep(dt)
        for np, body, dbgnp in self.freesolids:
            np.setPosQuat(render, body.getPosition(), Quat(body.getQuaternion()))
            np.setPos(np, 0,-1,0)
            if dbgnp != None:
                dbgnp.setPosQuat(render, body.getPosition(), Quat(body.getQuaternion()))
        #for np, body, dbgnp in self.hectors:
        self.contactgroup.empty()
        return task.cont
    
    def addFreeObject(self, block = None, size = None, mass = None):
        if block != None:
            boxBody = OdeBody(self.physWorld)
            M = OdeMass()
            M.setBox(mass or 100, size[0] or .1, size[1] or .1, size[2] or .1)
            print "setting freesolid mass == %s" % M
            boxBody.setMass(M)
            boxBody.setPosition(block.node.getPos(self.render))
            boxBody.setQuaternion(block.node.getQuat(self.render))
            boxGeom = OdeBoxGeom(self.physSpace, 1,1,1)
            boxGeom.setCollideBits(MAP_COLLIDE_CATEGORY)
            boxGeom.setCategoryBits(MAP_COLLIDE_BIT)
            boxGeom.setBody(boxBody)
            boxDebugShape = None
            if DEBUG_MAP_COLLISION:
                boxDebugShape = wireGeom().generate('box',extents = (size[0],size[1],size[2]))
                boxDebugShape.reparentTo(self.render)
                boxDebugShape.setPos(block.node.getPos(self.render))
                boxDebugShape.setQuat(block.node.getQuat(self.render))
            self.freesolids.append((block.node, boxBody, boxDebugShape))

        
    def addStaticObject(self, block = None, size = None, ramp = None, top = None, 
        thickness = None, width = None, base = None, dome = None, radius = None):
        if block != None:
            blockGeom = OdeBoxGeom(self.physSpace, size[0], size[1], size[2])
            blockGeom.setCollideBits(MAP_COLLIDE_BIT)
            blockGeom.setCategoryBits(MAP_COLLIDE_CATEGORY)
            blockGeom.setPosition(block.node.getPos())
            blockGeom.setQuaternion(block.node.getQuat())
            if DEBUG_MAP_COLLISION:
                blockDebugShape = wireGeom().generate('box', 
                                                      extents = (size[0],size[1],size[2]))
                blockDebugShape.reparentTo(self.render)
                blockDebugShape.setPos(block.node.getPos())
                blockDebugShape.setQuat(block.node.getQuat())
        if dome != None:
            domeGeom = OdeSphereGeom(self.physSpace, radius)
            domeGeom.setCollideBits(MAP_COLLIDE_BIT)
            domeGeom.setCategoryBits(MAP_COLLIDE_CATEGORY)
            domeGeom.setPosition(dome.node.getPos())
            domeGeom.setQuaternion(dome.node.getQuat())
            
            if DEBUG_MAP_COLLISION:
                domeDebugShape = wireGeom().generate('sphere', radius=radius)
                domeDebugShape.reparentTo(self.render)
                domeDebugShape.setPos(dome.node.getPos(render))
                domeDebugShape.setQuat(dome.node.getQuat(render))
        if ramp != None:
            #physics doesn't work with 0 thickness boxes!
            if thickness == 0:
                thickness = .001
            rampGeom = OdeBoxGeom(self.physSpace, thickness, width, (top-base).length())
            rampGeom.setCollideBits(MAP_COLLIDE_BIT)
            rampGeom.setCategoryBits(MAP_COLLIDE_CATEGORY)
            rampGeom.setPosition(ramp.node.getPos())
            rampGeom.setQuaternion(ramp.node.getQuat())
            if DEBUG_MAP_COLLISION:
                rampDebugShape = wireGeom().generate('box', 
                                        extents = (thickness, width, (top-base).length()))
                rampDebugShape.reparentTo(self.render)
                rampDebugShape.setPos(ramp.node.getPos())
                rampDebugShape.setQuat(ramp.node.getQuat())