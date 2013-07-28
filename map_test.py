import sys, os, random
from panda3d.core import *
from panda3d.rocket import *
from pandac.PandaModules import WindowProperties
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from direct.showbase import Audio3DManager
from direct.filter.CommonFilters import CommonFilters
from direct.interval.LerpInterval import *
from direct.interval.IntervalGlobal import *
from pavara.network import Server, Client
from pavara.constants import TCP_PORT
from pavara.maps import load_maps
from pavara.map_objects import Block 
from pavara.effects import FreeSolid
from pavara.utils.geom import GeomBuilder
from pavara.walker import Walker
from pavara.keymaps import KeyMaps


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
        self.audio3d.setDopplerFactor(.7)

        self.doc = False
        self.map = False

        if len(sys.argv) > 1:
            self.switch_map(sys.argv[1])
            self.start_map()
        else:
            self.switch_map("../Ui/scenes/splash.xml", audio=False)
            self.fade_in()
            incarn = self.map.world.get_incarn()
            self.map.world.attach(Walker(incarn))
            self.show_selection_screen()

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
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)
        self.up = Vec3(0, 1, 0)

    def fade_in(self):
        #blackout card
        bgeom = GeomBuilder().add_rect([0,0,0,1],-5,-5,0,5,5,0).get_geom_node()
        b = render.attach_new_node(bgeom)
        b.set_pos(self.cam.get_pos(render))
        b.set_hpr(self.cam.get_hpr(render))
        b_move_by = render.get_relative_vector(self.cam, Vec3(0,0,-2))
        b.set_pos(b, b_move_by)
        b.setColor(0,0,0)
        b.setTransparency(TransparencyAttrib.MAlpha)
        #fade from full opacity to no opacity
        cintv = LerpColorScaleInterval(b, 1.5, (1,1,1,0), (1,1,1,1))
        def _unhide_ui():
            self.doc.GetElementById('content').style.display = 'block'
            b.detach_node()
        #show ui after lerp is finished
        showui = Func(_unhide_ui)
        Sequence(cintv,showui).start()

    def show_selection_screen(self):
        LoadFontFace("Ui/assets/MunroSmall.otf")
        LoadFontFace("Ui/assets/Munro.otf")
        self.r_region = RocketRegion.make('pandaRocket', base.win)
        self.r_region.setActive(1)
        context = self.r_region.getContext()
        self.doc = context.LoadDocument('Ui/rml/map_test.rml')

        mlist = self.doc.GetElementById('map_select')
        for idx,item in enumerate(os.listdir('Maps')):
            fn_split = item.split('.')
            if len(fn_split) < 2 or fn_split[0] == "" or fn_split[1] != "xml":
                continue
            item_div = self.doc.CreateElement("div")
            item_div.SetAttribute("map", item)
            item_div.AddEventListener('click', self.map_selected, True)
            item_div.AppendChild(self.doc.CreateTextNode(item))
            mlist.AppendChild(item_div)

        self.doc.GetElementById('go').AddEventListener('click', self.start_map, True)
        self.doc.GetElementById('quit').AddEventListener('click', self.quit_clicked, True)
        self.doc.GetElementById('info_box').style.display = 'none'
        self.doc.GetElementById('content').style.display = 'none'
        self.doc.GetElementById('go').style.display = 'none'
        self.doc.Show()


        self.ih = RocketInputHandler()
        self.ih_node = base.mouseWatcher.attachNewNode(self.ih)
        self.r_region.setInputHandler(self.ih)

    def map_selected(self):
        in_map = event.current_element.GetAttribute("map")
        self.switch_map(in_map, show_info=True)
        return

    def switch_map(self, mapname, show_info=False, audio=True):
        if self.map:
            self.map.remove(self.render)
            del(self.map)
        if audio:
            maps = load_maps('Maps/%s' % mapname, self.cam, audio3d=self.audio3d)
        else:
            maps = load_maps('Maps/%s' % mapname, self.cam)
        self.map = maps[0]
        self.map.show(self.render)
        self.camera.setPos(*self.map.preview_cam[0])
        self.camera.setH(self.map.preview_cam[1][0])
        self.camera.setP(self.map.preview_cam[1][1])
        if self.doc and show_info:
            title_e = self.doc.GetElementById('info_title')
            title_txt = title_e.first_child
            title_e.RemoveChild(title_txt)
            new_txt = self.map.name + " -- " + self.map.author
            new_txt = new_txt.encode('latin2', 'ignore')
            title_e.AppendChild(self.doc.CreateTextNode(new_txt))
            desc_e = self.doc.GetElementById('info_content')
            desc_txt = desc_e.first_child
            desc_e.RemoveChild(desc_txt)
            desc_e.AppendChild(self.doc.CreateTextNode(self.map.description.encode('latin2', 'ignore')))
            self.doc.GetElementById('info_box').style.display = 'block'
            self.doc.GetElementById('go').style.display = 'inline'
            self.doc.GetElementById('gametitle').style.display = 'none'

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
        self.walker = self.map.world.attach(Walker(incarn, colordict=walker_color_dict, player=True))
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
        self.key_map = {'cam_forward': 0
                      , 'cam_left': 0
                      , 'cam_backward': 0
                      , 'cam_right': 0
                      , 'left': 0
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
                      , 'print_cam': 0
                      }
        self.accept('escape', sys.exit)
        self.accept('p', self.drop_blocks)

        for key,cmd in KeyMaps.flycam_input_settings:
            self.accept(key, self.set_key, [cmd, 1])
            self.accept(key+"-up", self.set_key, [cmd, 0])

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

        if (self.key_map['cam_forward']):
            self.camera.setZ(self.camera, -25 * dt)
        if (self.key_map['cam_backward']):
            self.camera.setZ(self.camera, 25 * dt)
        if (self.key_map['cam_left']):
            self.camera.setX(self.camera, -25 * dt)
        if (self.key_map['cam_right']):
            self.camera.setX(self.camera, 25 * dt)
        if (self.key_map['print_cam']):
            print "CAMERA: Pos - %s, Hpr - %s" % (self.camera.get_pos(), self.camera.get_hpr())
            self.key_map['print_cam'] = 0

        self.walker.handle_command('forward', self.key_map['forward'])
        self.walker.handle_command('left', self.key_map['left'])
        self.walker.handle_command('backward', self.key_map['backward'])
        self.walker.handle_command('right', self.key_map['right'])
        self.walker.handle_command('crouch', self.key_map['crouch'])

        self.walker.handle_command('fire', self.key_map['fire'])
        if self.key_map['fire']: self.key_map['fire'] = 0
        self.walker.handle_command('missile', self.key_map['missile'])
        if self.key_map['missile']: self.key_map['missile'] = 0
        self.walker.handle_command('grenade_fire', self.key_map['grenade_fire'])
        if self.key_map['grenade_fire']: self.key_map['grenade_fire'] = 0
        self.walker.handle_command('grenade', self.key_map['grenade'])
        if self.key_map['grenade']: self.key_map['grenade'] = 0

        return task.cont

if __name__ == '__main__':
    loadPrcFile('panda_config.prc')
    m = Map_Test()
    m.run()
