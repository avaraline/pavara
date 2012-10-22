from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText

class Hector():

    def __init__(self, render, pos_x, pos_y, pos_z):
        #self.model = Actor("hector_b2.4_2segment.egg")
        self.model = Actor("hector_b2.4_anim.egg")
        self.model.setPlayRate(6.5, "walk")
        self.model.setScale(3.0)
        self.model.setHpr(self.model, 0, 0, 0)
        self.model.reparentTo(render)
        self.model.setPos(pos_x,pos_y,pos_z)
        self.walking = False
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
            self.model.loop("walk")
            self.walking = True
        
    def unwalk(self):
        #self.right_top_bone.setP(self.rtb_rest)
        #self.right_bottom_bone.setP(self.rbb_rest)
        #self.left_top_bone.setP(self.ltb_rest)
        #self.left_bottom_bone.setP(self.lbb_rest)
        
        if self.walking:
            self.model.play("stand")
            self.walking = False
    
    def rotateLeft(self):
        self.model.setH(self.model, 1)
    
    def rotateRight(self):
        self.model.setH(self.model, -1)
