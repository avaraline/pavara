from panda3d.core import *
from icebox.clock import Clock
from direct.showbase.ShowBase import ShowBase
from direct.filter.CommonFilters import CommonFilters

class Icebox(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.filters = CommonFilters(self.win, self.cam)
        self.render.setShaderAuto()
        self.setBackgroundColor(0, 0, 0)
        #self.enableParticles()
        
        render.setAntialias(AntialiasAttrib.MAuto)
        self.cam.set_pos(50,25,50)
        self.cam.look_at(0,0,0)
        c = Clock(self)
        taskMgr.add(c.update, 'ClockTask')

if __name__ == '__main__':
    loadPrcFile('panda_config.prc')
    i = Icebox()
    i.run()