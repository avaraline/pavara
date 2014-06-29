from panda3d.core import *
from icebox.object_groups import VisibleObjects, PhysicalObjects
from icebox.input_manager import InputManager
from icebox.local_player import LocalPlayer

class Clock (object):
    def __init__(self, showbase):
        render = showbase.render

        self.visual_objects = VisibleObjects(render)
        self.physical_objects = PhysicalObjects()
        self.local_player = LocalPlayer()
        self.input_manager = InputManager(showbase, self.local_player)
        

    def update(self, task):
        dt = globalClock.getDt()
        self.visual_objects.update(dt)
        self.physical_objects.update(dt)
        self.local_player.update(dt)
        self.input_manager.update(dt)
        return task.cont
