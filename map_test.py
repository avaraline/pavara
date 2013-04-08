import sys, os, random
from panda3d.core import *
from panda3d.rocket import *
from pandac.PandaModules import WindowProperties
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from direct.showbase import Audio3DManager
from direct.filter.CommonFilters import CommonFilters

from pavara.maps import load_maps
from pavara.world import Block, FreeSolid
from pavara.walker import Walker


class Map_Test (ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.x = None
        self.y = None
        self.filters = CommonFilters(self.win, self.cam)
        self.render.setShaderAuto()
        #self.task_mgr = taskMgr
        self.initP3D()
        self.audio3d = Audio3DManager.Audio3DManager(self.sfxManagerList[0], self.cam)

        self.doc = False
        self.map = False

        if len(sys.argv) > 1:
            self.switch_map(sys.argv[1])
            self.start_map()
        else:
            self.show_selection_screen()

        # axes = loader.loadModel('models/yup-axis')
        # axes.setScale(10)
        # axes.reparentTo(render)

    def initP3D(self):
        self.disableMouse()
        self.setBackgroundColor(0, 0, 0)
        render.setAntialias(AntialiasAttrib.MAuto)
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)
        self.up = Vec3(0, 1, 0)


    def show_selection_screen(self):
        LoadFontFace("Ui/assets/MunroSmall.otf")
        LoadFontFace("Ui/assets/Munro.otf")
        self.r_region = RocketRegion.make('pandaRocket', base.win)
        self.r_region.setActive(1)
        context = self.r_region.getContext()
        self.doc = context.LoadDocument('Ui/rml/map_test.rml')

        mlist = self.doc.GetElementById('map_select')

        for idx,item in enumerate(os.listdir('Maps')):
            if idx == 0:
                self.switch_map(item)
            item_div = self.doc.CreateElement("div")
            item_div.SetAttribute("map", item)
            item_div.AddEventListener('click', self.map_selected, True)
            item_div.AppendChild(self.doc.CreateTextNode(item))
            mlist.AppendChild(item_div)

        self.doc.GetElementById('go').AddEventListener('click', self.start_map, True)
        self.doc.GetElementById('quit').AddEventListener('click', self.quit_clicked, True)
        self.doc.Show()

        self.ih = RocketInputHandler()
        self.ih_node = base.mouseWatcher.attachNewNode(self.ih)
        self.r_region.setInputHandler(self.ih)

    def map_selected(self):
        in_map = event.current_element.GetAttribute("map")
        print "selected map: ", in_map
        self.switch_map(in_map)
        return

    def switch_map(self, mapname, show_info=False):
        if self.map:
            self.map.remove(self.render)
            del(self.map)
        maps = load_maps('Maps/%s' % mapname, self.cam, audio3d=self.audio3d)
        for map in maps:
            print map.name, '--', map.author
        self.map = maps[0]
        self.map.show(self.render)
        self.camera.setPos(0, 20, 40)
        self.camera.setHpr(0, 0, 0)
        if self.doc:
            title_e = self.doc.GetElementById('info_title')
            title_txt = title_e.first_child
            title_e.RemoveChild(title_txt)
            new_txt = self.map.name + " -- " + self.map.author
            new_txt = new_txt.encode('ascii', 'ignore')
            title_e.AppendChild(self.doc.CreateTextNode(new_txt))
            desc_e = self.doc.GetElementById('info_content')
            desc_txt = desc_e.first_child
            desc_e.RemoveChild(desc_txt)
            desc_e.AppendChild(self.doc.CreateTextNode(self.map.description.encode('ascii', 'ignore')))

    def start_map(self):
        try:
            self.r_region.setActive(0)
            self.ih_node.detach_node()
        except:
            pass
        incarn = self.map.world.get_incarn()
        walker_color_dict = {
            "barrel_color": [.7,.7,.7],
            "visor_color": [2.0/255, 94.0/255, 115.0/255],
            "body_primary_color": [3.0/255, 127.0/255, 140.0/255],
            "body_secondary_color": [217.0/255, 213.0/255, 154.0/255]
        }
        self.walker = self.map.world.attach(Walker(incarn, colordict=walker_color_dict))
        self.camera.setPos(0, 20, 40)
        self.camera.setHpr(0, 0, 0)
        taskMgr.add(self.move, 'move')
        taskMgr.add(self.map.world.update, 'worldUpdateTask')
        self.setup_input()
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)
        print self.render.analyze()

    def quit_clicked(self):
        exit()

    def set_key(self, key, value):
        self.key_map[key] = value

    def drop_blocks(self):
        block = self.map.world.attach(FreeSolid(Block((1, 1, 1), (1, 0, 0, 1), 0.01, (0, 40, 0), (0, 0, 0)), 0.01))
        for i in range(10):
            rand_pos = (random.randint(-25, 25), 40, random.randint(-25, 25))
            block = self.map.world.attach(FreeSolid(Block((1, 1, 1), (1, 0, 0, 1), 0.01, rand_pos, (0, 0, 0)), 0.01))

    def setup_input(self):
        self.key_map = { 'left': 0
                      , 'right': 0
                      , 'forward': 0
                      , 'backward': 0
                      , 'rotateLeft': 0
                      , 'rotateRight': 0
                      , 'walkForward': 0
                      , 'crouch': 0
                      , 'fire': 0
                      , 'missile': 0
                      , 'grenade_fire': 0
                      , 'grenade': 0
                      }
        self.accept('escape', sys.exit)
        self.accept('p', self.drop_blocks)
        self.accept('w', self.set_key, ['forward', 1])
        self.accept('w-up', self.set_key, ['forward', 0])
        self.accept('a', self.set_key, ['left', 1])
        self.accept('a-up', self.set_key, ['left', 0])
        self.accept('s', self.set_key, ['backward', 1])
        self.accept('s-up', self.set_key, ['backward', 0])
        self.accept('d', self.set_key, ['right', 1])
        self.accept('d-up', self.set_key, ['right', 0])
        # Test walker movement
        self.accept('i',        self.walker.handle_command, ['forward', True])
        self.accept('i-up',     self.walker.handle_command, ['forward', False])
        self.accept('j',        self.walker.handle_command, ['left', True])
        self.accept('j-up',     self.walker.handle_command, ['left', False])
        self.accept('k',        self.walker.handle_command, ['backward', True])
        self.accept('k-up',     self.walker.handle_command, ['backward', False])
        self.accept('l',        self.walker.handle_command, ['right', True])
        self.accept('l-up',     self.walker.handle_command, ['right', False])
        self.accept('shift',    self.walker.handle_command, ['crouch', True])
        self.accept('shift-up', self.walker.handle_command, ['crouch', False])
        self.accept('mouse1',   self.walker.handle_command, ['fire', True])
        self.accept('mouse1-up',self.walker.handle_command, ['fire', False])
        self.accept('u',        self.walker.handle_command, ['missile', True])
        self.accept('u-up',     self.walker.handle_command, ['missile', False])
        self.accept('o',        self.walker.handle_command, ['grenade_fire', True])
        self.accept('o-up',     self.walker.handle_command, ['grenade_fire', False])
        self.accept('m',        self.walker.handle_command, ['grenade', True])
        self.accept('m-up',     self.walker.handle_command, ['grenade', False])

    def move(self, task):
        dt = globalClock.getDt()
        if self.mouseWatcherNode.hasMouse():
            oldx = self.x
            oldy = self.y
            md = self.win.getPointer(0)
            self.x = md.getX()
            self.y = md.getY()
            centerx = self.win.getProperties().getXSize()/2
            centery = self.win.getProperties().getYSize()/2
            self.win.movePointer(0, centerx, centery)

            if (oldx is not None):
                self.floater.setPos(self.camera, 0, 0, 0)
                self.floater.setHpr(self.camera, 0, 0, 0)
                self.floater.setH(self.floater, (centerx-self.x) * 10 * dt)
                p = self.floater.getP()
                self.floater.setP(self.floater, (centery-self.y) * 10 * dt)
                self.floater.setZ(self.floater, -1)
                angle = self.up.angleDeg(self.floater.getPos() - self.camera.getPos())
                if 10 > angle or angle > 170:
                    self.floater.setPos(self.camera, 0, 0, 0)
                    self.floater.setP(p)
                    self.floater.setZ(self.floater, -1)
                self.camera.lookAt(self.floater.getPos(), self.up)
        else:
            self.x = None
            self.y = None

        if (self.key_map['forward']):
            self.camera.setZ(self.camera, -25 * dt)
        if (self.key_map['backward']):
            self.camera.setZ(self.camera, 25 * dt)
        if (self.key_map['left']):
            self.camera.setX(self.camera, -25 * dt)
        if (self.key_map['right']):
            self.camera.setX(self.camera, 25 * dt)

        return task.cont

if __name__ == '__main__':
    loadPrcFile('pavara.prc')
    m = Map_Test()
    m.run()
