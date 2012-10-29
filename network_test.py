import sys
import direct.directbase.DirectStart
from panda3d.core import *
from pandac.PandaModules import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
#from pandac.PandaModules import NetDatagram
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from MapLoader import makeBox
import random

TCP_PORT = 11248

class Player (object):
    def __init__(self, pid=0, client=None, draw=False):
        self.pid = pid
        self.client = client
        self.geom = makeBox((1, random.random(), 1, 1), (0, 0, 0), 5, 5, 5)
        if draw:
            self.node = render.attachNewNode(self.geom)
        else:
            self.node = NodePath('player_%s' % self.pid)
            self.node.attachNewNode(self.geom)
        self.movement = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False,
        }

    def __repr__(self):
        return 'Player %s' % self.pid

    def handle_move(self, direction, pressed):
        self.movement[direction] = pressed
        if self.client:
            self.client.send(direction, pressed)

    def do_move(self):
        moved = False
        if self.movement['forward']:
            self.node.setY(self.node, 25 * globalClock.getDt())
            moved = True
        if self.movement['backward']:
            self.node.setY(self.node, -25 * globalClock.getDt())
            moved = True
        if self.movement['left']:
            self.node.setX(self.node, -25 * globalClock.getDt())
            moved = True
        if self.movement['right']:
            self.node.setX(self.node, 25 * globalClock.getDt())
            moved = True
        return moved

    def move_to(self, x, y):
        self.node.setX(x)
        self.node.setY(y)

class Server (object):
    def __init__(self, port):
        self.manager = QueuedConnectionManager()
        self.listener = QueuedConnectionListener(self.manager, 0)
        self.reader = QueuedConnectionReader(self.manager, 0)
        self.writer = ConnectionWriter(self.manager, 0)
        self.connections = []
        self.players = {}
        self.last_pid = 0
        sock = self.manager.openTCPServerRendezvous(port, 1000)
        self.listener.addConnection(sock)
        taskMgr.add(self.server_task, 'serverManagementTask')
        taskMgr.add(self.update_players, 'serverPlayerTask')

    def server_task(self, task):
        if self.listener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()
            if self.listener.getNewConnection(rendezvous, netAddress, newConnection):
                print 'GOT CONNECTION FROM', netAddress
                newConnection = newConnection.p()
                self.connections.append(newConnection)
                self.reader.addConnection(newConnection)
                self.last_pid += 1
                self.players[netAddress.getIpString()] = Player(pid=self.last_pid, draw=False)
        while self.manager.resetConnectionAvailable():
            connPointer = PointerToConnection()
            self.manager.getResetConnection(connPointer)
            connection = connPointer.p()
            print 'LOST CONNECTION FROM', connection
            # Remove the connection we just found to be "reset" or "disconnected"
            self.reader.removeConnection(connection)
            # Loop through the activeConnections till we find the connection we just deleted
            # and remove it from our activeConnections list
            for idx in range(0, len(self.connections)):
                if self.connections[idx] == connection:
                    del self.connections[c]
                    break
        while self.reader.dataAvailable():
            datagram = NetDatagram()
            if self.reader.getData(datagram):
                conn = datagram.getConnection()
                dataIter = PyDatagramIterator(datagram)
                addr = conn.getAddress()
                player = self.players[addr.getIpString()]
                player.handle_move(dataIter.getString(), dataIter.getBool())
        return task.cont

    def update_players(self, task):
        for ip, player in self.players.items():
            if player.do_move():
                datagram = PyDatagram()
                datagram.addInt8(player.pid)
                datagram.addFloat32(player.node.getX())
                datagram.addFloat32(player.node.getY())
                for conn in self.connections:
                    self.writer.send(datagram, conn)
        return task.cont

class Client (object):
    def __init__(self, host, port, timeout=3000):
        self.manager = QueuedConnectionManager()
        self.reader = QueuedConnectionReader(self.manager, 0)
        self.writer = ConnectionWriter(self.manager, 0)
        self.connection = self.manager.openTCPClientConnection(host, port, timeout)
        if self.connection:
            self.reader.addConnection(self.connection)
            self.connected = True
        self.players = {}
        taskMgr.add(self.update, 'clientUpdatesFromServer')

    def send(self, cmd, onoff):
        datagram = PyDatagram()
        datagram.addString(cmd)
        datagram.addBool(onoff)
        self.writer.send(datagram, self.connection)

    def update(self, task):
        while self.reader.dataAvailable():
            datagram = NetDatagram()
            if self.reader.getData(datagram):
                dataIter = PyDatagramIterator(datagram)
                pid = dataIter.getInt8()
                x = dataIter.getFloat32()
                y = dataIter.getFloat32()
                if pid not in self.players:
                    print 'NEW PLAYER', pid
                    self.players[pid] = Player(pid=pid, draw=True)
                self.players[pid].move_to(x, y)
        return task.cont

class NetworkTest (DirectObject):
    def __init__(self, *args):
        if args:
            print 'CONNECTING TO', args
            self.client = Client(args[0], TCP_PORT)
        else:
            print 'CONNECTING TO localhost'
            self.server = Server(TCP_PORT)
            self.client = Client('localhost', TCP_PORT)
        self.player = Player(client=self.client)
        self.bind_keys()
        self.init_scene()
        render.attachNewNode(makeBox((1, 0, 0, 1), (0, 0, 0), 1000, 0.5, 0.5))
        render.attachNewNode(makeBox((0, 1, 0, 1), (0, 0, 0), 0.5, 1000, 0.5))
        #render.attachNewNode(makeBox((0, 0, 1, 1), (0, 0, 0), 0.5, 0.5, 1000))
        #render.attachNewNode(makeBox((1, 1, 0, 1), (10, 10, 0), 1, 1, 1))

    def bind_keys(self):
        self.accept('escape', sys.exit)
        self.accept('w',    self.player.handle_move, ['forward', True])
        self.accept('w-up', self.player.handle_move, ['forward', False])
        self.accept('s',    self.player.handle_move, ['backward', True])
        self.accept('s-up', self.player.handle_move, ['backward', False])
        self.accept('a',    self.player.handle_move, ['left', True])
        self.accept('a-up', self.player.handle_move, ['left', False])
        self.accept('d',    self.player.handle_move, ['right', True])
        self.accept('d-up', self.player.handle_move, ['right', False])

    def init_scene(self):
        base.setFrameRateMeter(True)
        base.setBackgroundColor(0, 0, 0)
        base.enableParticles()
        base.disableMouse()
        render.setAntialias(AntialiasAttrib.MMultisample)
        # Add some light so we can actually see the blocks.
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.4, 0.4, 0.4, 1))
        render.setLight(render.attachNewNode(alight))
        dlight = DirectionalLight('directionalLight')
        dlight.setColor(Vec4(1, 1, 1, 1))
        lightNode = render.attachNewNode(dlight)
        lightNode.setHpr(20, 120, 0)
        render.setLight(lightNode)
        # Position the camera with a birds-eye view of the ground.
        base.camera.setPos(0,0,300)
        base.camera.setHpr(0,-90,0)

if __name__ == '__main__':
    app = NetworkTest(*sys.argv[1:])
    run()
