from panda3d.core import *
from icebox.object_groups import VisibleObjects, PhysicalObjects
from icebox.world import World
from icebox.network import Server, Client
from icebox.local_player import LocalPlayer
from icebox.input_manager import InputManager

class Clock (object):
    def __init__(self, showbase):
        render = showbase.render
        self.time = 0
        self.world = World(showbase, True)
        self.local_player = LocalPlayer()
        self.client = Client(self.world, 'localhost', 23000)
        self.input_manager = InputManager(showbase, self.local_player, self.client)
        

    def update(self, task):
        dt = globalClock.getDt()
        self.time += dt
        self.world.update(dt)
        return task.cont


class ServerClock (object):
    def __init__(self, showbase):
        render = showbase.render
        self.time = 0
        self.world = World(showbase, False)
        self.server = Server(self.world, 23000)
        taskMgr.doMethodLater(5, self.drop_block, 'drop_block_task')

    def drop_block(self, task):
        self.world.add_block([0,25,0])
        return task.again

    def update(self, task):
        dt = globalClock.getDt()
        self.time += dt
        self.world.update(dt)
        return task.cont
