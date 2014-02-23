import sys, os, random
from panda3d.core import *
from panda3d.rocket import *
from pandac.PandaModules import WindowProperties
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from direct.showbase import Audio3DManager
from direct.filter.CommonFilters import CommonFilters
from pavara.network import Server, Client
from pavara.constants import TCP_PORT
from splash import Splash


class MapTest (ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.filters = CommonFilters(self.win, self.cam)
        self.render.setShaderAuto()
        self.initP3D()
        self.audio3d = Audio3DManager.Audio3DManager(self.sfxManagerList[0], self.cam)
        self.audio3d.setDopplerFactor(.7)

        self.splash = Splash(base, self,
            sys.argv[1] if len(sys.argv) > 1 else False
        )

        #host = args[0] if args else 'localhost'
        #print 'CONNECTING TO', host
        #self.client = Client(self.map.world, host, TCP_PORT)


        # axes = loader.loadModel('models/yup-axis')
        # axes.setScale(10)
        # axes.reparentTo(render)

    def initP3D(self):
        self.disableMouse()
        self.setBackgroundColor(0, 0, 0)
        render.setAntialias(AntialiasAttrib.MAuto)

if __name__ == '__main__':
    loadPrcFile('panda_config.prc')
    m = MapTest()
    m.run()
