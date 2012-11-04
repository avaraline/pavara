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
        self.model = Actor("hector_b2.4-addedcrotch.egg")
        self.model.setScale(3.0)
        self.model.setHpr(self.model, 0, 0, 0)
        self.model.setH(self.model, angle)
        self.model.reparentTo(render)
        self.model.setPos(pos_x,pos_y,pos_z)
        
        
        
        #measure = loader.loadModel("models/yup-axis")
        #measure.reparentTo(render)
        #measure.setPos(pos_x, pos_y, pos_z)
        
        self.setupColor({"barrel_color": Vec3(.4,.7,.4), "barrel_trim_color": Vec3(.8,.9,.6), 
                         "visor_color": Vec3(.3,.6,1), "body_color":Vec3(.2,.5,.3), 
                         "top_leg_color": Vec3(.19,.49,.29), "middle_leg_color": Vec3(.10,.40,.20),
                         "bottom_leg_color": Vec3(.06,.30,.10)})
        
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
        
        self.left_foot_node = self.model.find("**/leftBottom")
        self.right_foot_node = self.model.find("**/rightBottom")
        
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
    
    def setupColor(self, colordict):
      
        if colordict.has_key("barrel_color"):
            barrels = self.model.find("**/barrels")
            barrels.setColor(*colordict.get("barrel_color"))
        if colordict.has_key("barrel_trim_color"):
            barrel_trim = self.model.find("**/barrelTrim")
            barrel_trim.setColor(*colordict.get("barrel_trim_color"))
        if colordict.has_key("visor_color"):
            visor = self.model.find("**/visor")
            visor.setColor(*colordict.get("visor_color"))
        if colordict.has_key("body_color"):
            color = colordict.get("body_color")
            hull = self.model.find("**/hull")
            hull.setColor(*color)
            crotch = self.model.find("**/crotch")
            crotch.setColor(*color)
            left_top = self.model.find("**/leftTop")
            right_top = self.model.find("**/rightTop")
            left_top.setColor(*color)
            right_top.setColor(*color)
            left_middle = self.model.find("**/leftMiddle")
            right_middle = self.model.find("**/rightMiddle")
            left_middle.setColor(*color)
            right_middle.setColor(*color)
            left_bottom = self.model.find("**/leftBottom")
            right_bottom = self.model.find("**/rightBottom")
            left_bottom.setColor(*color)
            right_bottom.setColor(*color)
        if colordict.has_key("hull_color"):
            hull = self.model.find("**/hull")
            hull.setColor(*colordict.get("hull_color"))
            crotch = self.model.find("**/crotch")
            crotch.setColor(*color)
        if colordict.has_key("top_leg_color"):
            color = colordict.get("top_leg_color")
            left_top = self.model.find("**/leftTop")
            right_top = self.model.find("**/rightTop")
            left_top.setColor(*color)
            right_top.setColor(*color)
        if colordict.has_key("middle_leg_color"):
            color = colordict.get("middle_leg_color")
            left_middle = self.model.find("**/leftMiddle")
            right_middle = self.model.find("**/rightMiddle")
            left_middle.setColor(*color)
            right_middle.setColor(*color)   
        if colordict.has_key("bottom_leg_color"):
            color = colordict.get("bottom_leg_color")
            left_bottom = self.model.find("**/leftBottom")
            right_bottom = self.model.find("**/rightBottom")
            left_bottom.setColor(*color)
            right_bottom.setColor(*color)
        
                
                
        
        return
        