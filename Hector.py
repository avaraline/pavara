from direct.actor.Actor import Actor
from direct.interval.LerpInterval import LerpPosHprInterval
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import *
from pandac.PandaModules import GeomVertexReader, GeomVertexWriter
from pandac.PandaModules import GeomVertexArrayFormat, InternalName, GeomVertexFormat
from panda3d.ode import *
from direct.interval.IntervalGlobal import Sequence, Parallel
import math
class Hector():
    def __init__(self, render, pos_x, pos_y, pos_z, angle):
        self.model = Actor("hector.egg")
        self.model.setScale(3.0)
        self.model.setHpr(self.model, 0, 0, 0)
        self.model.setH(self.model, angle)
        self.model.reparentTo(render)
        self.model.setPos(pos_x,pos_y,pos_z)
    
    	measure = loader.loadModel("models/yup-axis")
        measure.reparentTo(render)
        measure.setPos(pos_x, pos_y, pos_z)
        
        self.setupColor(.2,.3,.8,1)
        
        self.walking = False
        
        #this prints the bones available in the model to the console
        #self.model.listJoints()
        
        #using these prevents animations from being played
        #if these bones aren't in the list printed out by listJoints it doesn't work 
        self.head_bone = self.model.controlJoint(None, "modelRoot", "headBone")
        self.left_top_bone = self.model.controlJoint(None, "modelRoot", "leftTopBone")
        self.right_top_bone = self.model.controlJoint(None, "modelRoot", "rightTopBone")
        self.left_middle_bone = self.model.controlJoint(None, "modelRoot", "leftMidBone")
        self.right_middle_bone = self.model.controlJoint(None, "modelRoot", "rightMidBone")
        self.left_bottom_bone = self.model.controlJoint(None, "modelRoot", "leftBottomBone")
        self.right_bottom_bone = self.model.controlJoint(None, "modelRoot", "rightBottomBone")
        
        self.ltb_rest = self.left_top_bone.getP()
        self.rtb_rest = self.right_top_bone.getP()
        self.lmb_rest = self.left_middle_bone.getP()
        self.rmb_rest = self.right_middle_bone.getP()
        self.lbb_rest = self.left_bottom_bone.getP()
        self.rbb_rest = self.right_bottom_bone.getP()
        
        #this is just an example to get started
        
        walk_int_1 = LerpPosHprInterval(self.left_top_bone, 
                                        .2, 
                                        pos=self.get_leg_pos(self.left_top_bone),
                                        hpr=self.get_leg_hpr(self.left_top_bone),
                                        startPos = None,
                                        blendType = "easeOut",
                                        bakeInStart = 0
                                    )
        walk_int_2 = LerpPosHprInterval(self.left_bottom_bone, 
                                        .2, 
                                        pos=self.get_leg_pos(self.left_bottom_bone),
                                        hpr=self.get_leg_hpr(self.left_bottom_bone),
                                        startPos = None,
                                        blendType = "easeIn",
                                        bakeInStart = 0
                                    )
        self.walk_seq_1 = Sequence(Parallel(walk_int_1, walk_int_2))
        
        
    def walk(self):
        if not self.walking:
        	self.walk_seq_1.start()
        	self.walking = True

    def get_leg_pos(self, obj):
    	pos = obj.getPos()
    	if obj.__repr__().split('/')[-1] == "leftTopBone":
    		pos.addY(-.1)
    	print pos
        return pos
        
    def get_leg_hpr(self, obj):
    	hpr = obj.getHpr()
    	hpr.addY(20)
    	print hpr
        return hpr
    
    def unwalk(self):
        if self.walking:
        	self.walk_seq_1.pause()
        	self.walking = False
        return
    
    def crouch(self):
		return
        
    def uncrouch(self):
    	return
    	
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
                #print geom
                vdata = geom.modifyVertexData()
                pre_existing_color = False
                
                if(vdata.hasColumn('color')):
                    pre_existing_color = True

                new_format = vdata.getFormat().getUnionFormat(gformat)
                vdata.setFormat(new_format)
                color = GeomVertexWriter(vdata, 'color')
                vertex = GeomVertexReader(vdata, 'vertex')
                read_color = GeomVertexReader(vdata, 'color')
                while not vertex.isAtEnd():
                    v = vertex.getData3f()
                    #print v
                    if pre_existing_color:
                        color.setData4f(r,g,b,a)
                    else:
                        color.addData4f(r,g,b,a)
        
