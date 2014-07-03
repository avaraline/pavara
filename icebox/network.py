import sys
#import direct.directbase.DirectStart
from panda3d.core import *
from pandac.PandaModules import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
#from pandac.PandaModules import NetDatagram
#from direct.gui.DirectGui import *
import random


class Player (object):
    def __init__(self, pid, tank):
        self.pid = pid
        self.tank = tank

    def __repr__(self):
        return 'Player %s' % self.pid

    def handle_command(self, direction, pressed):
        print 'PLAYER %s GOT CMD %s %s' % (self.pid, direction, pressed)
        self.tank.handle_command(direction, pressed)

class Server (object):
    def __init__(self, world, port):
        self.world = world
        self.manager = QueuedConnectionManager()
        self.listener = QueuedConnectionListener(self.manager, 0)
        self.reader = QueuedConnectionReader(self.manager, 0)
        self.writer = ConnectionWriter(self.manager, 0)
        self.connections = []
        self.players = {}
        self.last_pid = 0
        sock = self.manager.openTCPServerRendezvous(port, 1000)
        self.listener.addConnection(sock)
        taskMgr.doMethodLater(0.05, self.server_task, 'serverManagementTask')

    def server_task(self, task):
        if self.listener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()
            if self.listener.getNewConnection(rendezvous, netAddress, newConnection):
                print 'GOT CONNECTION FROM', netAddress
                newConnection = newConnection.p()
                newConnection.setNoDelay(True)
                self.connections.append(newConnection)
                self.reader.addConnection(newConnection)
                self.last_pid += 1
                self.players[netAddress.getIpString()] = Player(self.last_pid, self.world.add_tank([random.randint(0,50), 1, random.randint(0,50)]))
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
                    del self.connections[idx]
                    break
        while self.reader.dataAvailable():
            datagram = NetDatagram()
            if self.reader.getData(datagram):
                conn = datagram.getConnection()
                dataIter = PyDatagramIterator(datagram)
                addr = conn.getAddress()
                player = self.players[addr.getIpString()]
                player.handle_command(dataIter.getString(), dataIter.getBool())
        update = PyDatagram()
        update.addInt8(len([o for o in self.world.updatables if o.moved]))
        for obj in self.world.updatables:
            obj.add_update(update)
        for conn in self.connections:
            self.writer.send(update, conn)
        return task.again

class Client (object):
    def __init__(self, world, host, port, timeout=3000):
        self.world = world
        self.manager = QueuedConnectionManager()
        self.reader = QueuedConnectionReader(self.manager, 0)
        self.writer = ConnectionWriter(self.manager, 0)
        self.connection = self.manager.openTCPClientConnection(host, port, timeout)
        if self.connection:
            self.connection.setNoDelay(True)
            self.reader.addConnection(self.connection)
            self.connected = True
        self.players = {}
        taskMgr.add(self.update, 'clientUpdatesFromServer')

    def send(self, cmd, onoff):
        print 'CLIENT SEND', cmd, onoff
        datagram = PyDatagram()
        datagram.addString(cmd)
        datagram.addBool(onoff)
        self.writer.send(datagram, self.connection)

    def update(self, task):
        while self.reader.dataAvailable():
            datagram = NetDatagram()
            if self.reader.getData(datagram):
                update = PyDatagramIterator(datagram)
                num_objects = update.getInt8()
                for i in range(num_objects):
                    name = update.getString()
                    x = update.getFloat32()
                    y = update.getFloat32()
                    z = update.getFloat32()
                    h = update.getFloat32()
                    p = update.getFloat32()
                    r = update.getFloat32()
                    #print 'CLIENT RECV', name, x, y, z
                    if name.startswith('Tank') and name not in self.world.objects:
                        self.world.add_tank([0,0,0], name=name)
                    if name.startswith('Block') and name not in self.world.objects:
                        self.world.add_block([0,0,0], name=name)
                    obj = self.world.objects.get(name)
                    if obj:
                        obj.move((x, y, z))
                        obj.rotate((h, p, r))
        return task.cont
