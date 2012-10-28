from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Vec3, CollisionNode, CollisionRay, BitMask32, Geom
from pandac.PandaModules import GeomVertexReader, GeomVertexWriter
from pandac.PandaModules import GeomVertexArrayFormat, InternalName, GeomVertexFormat
import math
class Hector():
    def __init__(self, render, pos_x, pos_y, pos_z, angle):
        #self.model = Actor("hector_b2.4_2segment.egg")
        self.model = Actor("hector_b2.4_anim.egg")
        self.model.setPlayRate(6.5, "walk")
        self.model.setScale(3.0)
        self.model.setHpr(self.model, 0, 0, 0)
        self.model.setH(self.model, angle)
        self.model.reparentTo(render)
        self.model.setPos(pos_x,pos_y,pos_z)
        self.walking = False
        
        self.velocity = Vec3(0,0,0)
        self.accel = Vec3(0,0,0)
        
        self.model.enableBlend()
        self.model.setControlEffect('stand', 1.0)
        self.model.setControlEffect('crouch', 0.0)
        #self.model.loop('crouch')
        
        self.crouchcontrol = self.model.getAnimControl('crouch')
        self.crouchfactor = 0
        
        self.setupColor(.2,.3,.8,1)
        
        
        #this prints the bones available in the model to the console
        #self.model.listJoints()
    
        return
        #using these prevents animations from being played
        #if these bones aren't in the list printed out by listJoints it doesn't work 
        self.head_bone = self.model.controlJoint(None, "modelRoot", "headBone")
        self.left_top_bone = self.model.controlJoint(None, "modelRoot", "leftTopBone")
        self.right_top_bone = self.model.controlJoint(None, "modelRoot", "rightTopBone")
        self.left_middle_bone = self.model.controlJoint(None, "modelRoot", "leftMiddleBone")
        self.right_middle_bone = self.model.controlJoint(None, "modelRoot", "rightMiddleBone")
        self.left_bottom_bone = self.model.controlJoint(None, "modelRoot", "leftBottomBone")
        self.right_bottom_bone = self.model.controlJoint(None, "modelRoot", "rightBottomBone")
        
        self.ltb_rest = self.left_top_bone.getP()
        self.rtb_rest = self.right_top_bone.getP()
        self.lbb_rest = self.left_bottom_bone.getP()
        self.rbb_rest = self.right_bottom_bone.getP()
        

        
    def walk(self):
        #self.right_top_bone.setP(self.right_top_bone, 1)
        #self.right_bottom_bone.setP(self.right_bottom_bone, -2)
        #self.left_top_bone.setP(self.left_top_bone, -1)
        #self.left_bottom_bone.setP(self.left_bottom_bone, -2)
        
        if not self.walking:
            if self.crouchfactor > 0:
                self.model.setControlEffect('walk', 1.0)
                self.model.setControlEffect('stand', 0)
            else:
                self.model.setControlEffect('walk', .5)
                self.model.setControlEffect('crouch', .5)
            self.model.loop("walk")
            self.walking = True
        
    def unwalk(self):
        #self.right_top_bone.setP(self.rtb_rest)
        #self.right_bottom_bone.setP(self.rbb_rest)
        #self.left_top_bone.setP(self.ltb_rest)
        #self.left_bottom_bone.setP(self.lbb_rest)
        
        if self.walking:
            self.model.setControlEffect('walk', 0.0)
            if self.crouchfactor > 0:
                self.model.setControlEffect('crouch', .50)
                self.model.setControlEffect('stand', .50)
            else:
                self.model.setControlEffect('stand', 1.0)
            

            self.model.stop("walk")
            self.model.play("stand")
            self.walking = False
    
    def crouch(self):
        if not self.walking:
            self.model.setControlEffect('walk', .5)
            self.model.setControlEffect('crouch', .5)
        else:
            self.model.setControlEffect('crouch', 1)
            self.model.setControlEffect('stand', 0)
        
        if(self.crouchfactor < 1):
            self.crouchfactor +=.2
        
        self.crouchcontrol.pose(math.floor(((self.crouchcontrol.getNumFrames()/2) * self.crouchfactor))) 
        
    def uncrouch(self):
        if not self.walking:
            self.model.setControlEffect('walk', 1.0)
            self.model.setControlEffect('crouch', 0)
        else:
            self.model.setControlEffect('stand', 1.0)
            self.model.setControlEffect('crouch', 0)
        
        if self.crouchfactor > 0:
            self.crouchfactor -= .2
            
        self.crouchcontrol.pose(math.floor(((self.crouchcontrol.getNumFrames()/2) * self.crouchfactor))) 
    

    
    def rotateLeft(self):
        self.model.setH(self.model, 1)
    
    def rotateRight(self):
        self.model.setH(self.model, -1)
    
    def setupColor(self, r, g, b, a):
    	gvarrayf = GeomVertexArrayFormat()
        gvarrayf.addColumn(InternalName.make('color'), 4, Geom.NTFloat32, Geom.CColor)
        gformat = GeomVertexFormat()
        gformat.addArray(gvarrayf)
        gformat = GeomVertexFormat.registerFormat(gformat)
        
        geomNodeCollection = self.model.findAllMatches('**/+GeomNode')
        for nodePath in geomNodeCollection:
            geomNode = nodePath.node()
            for i in range(geomNode.getNumGeoms()):
                geom = geomNode.modifyGeom(i)
                vdata = geom.modifyVertexData()
                pre_existing_color = False
                
                if(vdata.hasColumn('color')):
                    pre_existing_color = True

                new_format = vdata.getFormat().getUnionFormat(gformat)
                vdata.setFormat(new_format)
                color = GeomVertexWriter(vdata, 'color')
                vertex = GeomVertexReader(vdata, 'vertex')
                while not vertex.isAtEnd():
                    v = vertex.getData3f()
                    if pre_existing_color:
                        color.setData4f(r,g,b,a)
                    else:
                        color.addData4f(r,g,b,a)
        
