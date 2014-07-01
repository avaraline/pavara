from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from icebox.clock import ServerClock

class Icebox_Server(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)
		self.enableParticles()
		c = ServerClock(self, self.physicsMgr)

if __name__ == '__main__':
    loadPrcFile('icebox_server.prc')
    i = Icebox_Server()
    i.run()