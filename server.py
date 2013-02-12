import sys, random
from panda3d.core import *
from pandac.PandaModules import WindowProperties
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase

from pavara.maps import load_maps
from pavara.world import Block, Hector
from pavara.network import Server, Client
from pavara.constants import TCP_PORT

class PavaraServer (ShowBase):
    def __init__(self, *args):
        ShowBase.__init__(self)
        maps = load_maps('Maps/bodhi.xml')
        self.map = maps[0]
        self.map.show(self.render)
        taskMgr.add(self.map.world.update, 'worldUpdateTask')
        self.server = Server(self.map.world, TCP_PORT)

if __name__ == '__main__':
    loadPrcFile('server.prc')
    p = PavaraServer(*sys.argv[1:])
    p.run()
