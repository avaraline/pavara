import sys
#import direct.directbase.DirectStart
from panda3d.core import *
from pandac.PandaModules import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
#from pandac.PandaModules import NetDatagram
#from direct.gui.DirectGui import *
import random

from pavara.world import Hector

class Player (object):
    def __init__(self, pid, hector):
        self.pid = pid
        self.hector = hector

    def __repr__(self):
        return 'Player %s' % self.pid

    def handle_command(self, direction, pressed):
        print 'PLAYER %s GOT CMD %s %s' % (self.pid, direction, pressed)
        self.hector.handle_command(direction, pressed)

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
                self.players[netAddress.getIpString()] = self.last_pid
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
                pid = self.players[addr.getIpString()]
                self.broadcast(pid, dataIter.getString(), dataIter.getBool())
        return task.cont

    def broadcast(self, pid, cmd, onoff):
        datagram = PyDatagram()
        datagram.addInt8(pid)
        datagram.addString(cmd)
        datagram.addBool(onoff)
        for conn in self.connections:
            self.writer.send(datagram, conn)

class Client (object):
    def __init__(self, world, host, port, timeout=3000):
        self.world = world
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
        print 'CLIENT SEND', cmd, onoff
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
                cmd = dataIter.getString()
                onoff = dataIter.getBool()
                if pid not in self.players:
                    print 'NEW PLAYER', pid
                    hector = self.world.attach(Hector())
                    hector.move((0, 15, 0))
                    self.players[pid] = Player(pid, hector)
                self.players[pid].handle_command(cmd, onoff)
        return task.cont
