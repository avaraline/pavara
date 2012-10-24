from xml.dom.minidom import parse
from math import pi, sin, cos
from panda3d.core import Vec3, Geom, GeomNode, GeomVertexFormat, GeomVertexWriter, GeomVertexData
from panda3d.core import GeomTriangles, LRotationf, Point3, LOrientationf, AmbientLight, VBase4
from panda3d.core import DirectionalLight, Vec4

class VertexDataWriter(object):
    def __init__(self, vdata):
        self.vertex = GeomVertexWriter(vdata, 'vertex')
        self.normal = GeomVertexWriter(vdata, 'normal')
        self.color = GeomVertexWriter(vdata, 'color')
        self.texcoord = GeomVertexWriter(vdata, 'texcoord')

    def addVertex(self, point, normal, color, texcoord):
        self.vertex.addData3f(point)
        self.normal.addData3f(normal)
        self.color.addData4f(*color)
        self.texcoord.addData2f(*texcoord)


class Polygon(object):
    def __init__(self, points=None):
        if points:
            self.points = points
        else:
            self.points = []

    def getNormal(self):
        seen = set()
        points = [point for point in self.points if point not in seen and not seen.add(point)]
        if len(points) >= 3:
            v1 = points[0] - points[1]
            v2 = points[1] - points[2]
            normal = v1.cross(v2)
            normal.normalize()
        else:
            normal = Vec3.up()
        return normal


def makeAxisAlignedSquare(x1,y1,z1, x2,y2,z2):
    p1 = Point3(x1, y1, z1)
    p3 = Point3(x2, y2, z2)

    #make sure we draw the square in the right plane
    if x1 != x2:
        p2 = Point3(x2, y1, z1)
        p4 = Point3(x1, y2, z2)
    else:
        p2 = Point3(x2, y2, z1)
        p4 = Point3(x1, y1, z2)

    return Polygon([p1, p2, p3, p4])


def makeSquare(colorf, x1,y1,z1, x2,y2,z2):
    if len(colorf) == 3:
        colorf = (colorf[0], colorf[1], colorf[2], 1)
    vdata = GeomVertexData('square', GeomVertexFormat.getV3n3cpt2(), Geom.UHDynamic)
    writer = VertexDataWriter(vdata)
    aasquare = makeAxisAlignedSquare(x1, y1, z1, x2, y2, z2)

    # add points to vertex data
    normal = aasquare.getNormal()
    for point in aasquare.points:
        writer.addVertex(point, normal, colorf, (0.0, 1.0))

    tri = GeomTriangles(Geom.UHDynamic)

    tri.addVertex(0)
    tri.addVertex(1)
    tri.addVertex(3)
    tri.closePrimitive()
    tri.addConsecutiveVertices(1, 3)
    tri.closePrimitive()

    square = Geom(vdata)
    square.addPrimitive(tri)
    
    return square

def makeBox(color, center, xsize, ysize, zsize):
    node = GeomNode('square')
    node.addGeom(makeSquare(color, center[0] - xsize/2., center[1] + ysize/2., center[2] - zsize/2.,
                                   center[0] - xsize/2., center[1] - ysize/2., center[2] + zsize/2.))
    node.addGeom(makeSquare(color, center[0] + xsize/2., center[1] - ysize/2., center[2] - zsize/2.,
                                   center[0] + xsize/2., center[1] + ysize/2., center[2] + zsize/2.))
    node.addGeom(makeSquare(color, center[0] - xsize/2., center[1] - ysize/2., center[2] - zsize/2.,
                                   center[0] + xsize/2., center[1] - ysize/2., center[2] + zsize/2.))
    node.addGeom(makeSquare(color, center[0] + xsize/2., center[1] + ysize/2., center[2] - zsize/2.,
                                   center[0] - xsize/2., center[1] + ysize/2., center[2] + zsize/2.))
    node.addGeom(makeSquare(color, center[0] - xsize/2., center[1] + ysize/2., center[2] - zsize/2.,
                                   center[0] + xsize/2., center[1] - ysize/2., center[2] - zsize/2.))
    node.addGeom(makeSquare(color, center[0] - xsize/2., center[1] - ysize/2., center[2] + zsize/2.,
                                   center[0] + xsize/2., center[1] + ysize/2., center[2] + zsize/2.))
    return node

def toCartesian(azimuth, elevation, length):
    x = length * sin(azimuth) * cos(elevation)
    y = length * sin(elevation)
    z = -length * cos(azimuth) * cos(elevation)
    return (x,y,z)

def makeDome(colorf, radius, radialSamples, planes):
    if len(colorf) == 3:
        colorf = (colorf[0], colorf[1], colorf[2], 1)
    vdata=GeomVertexData('square', GeomVertexFormat.getV3n3cpt2(), Geom.UHDynamic)
    writer = VertexDataWriter(vdata)

    two_pi = pi * 2
    half_pi = pi / 2
    azimuths = [(two_pi * i)/radialSamples for i in range(radialSamples+1)]
    elevations = [(half_pi * i) / (planes - 1) for i in range(planes)]
    point_id = 0
    tri = GeomTriangles(Geom.UHDynamic)
    for i in range(0, len(elevations) - 1):
        for j in range(0, len(azimuths) - 1):
            poly = Polygon()
            x1, y1, z1 = toCartesian(azimuths[j], elevations[i], radius)
            x2, y2, z2 = toCartesian(azimuths[j], elevations[i+1], radius)
            x3, y3, z3 = toCartesian(azimuths[j+1], elevations[i+1], radius)
            x4, y4, z4 = toCartesian(azimuths[j+1], elevations[i], radius)
            poly.points.append(Point3(x1, y1, z1))
            poly.points.append(Point3(x2, y2, z2))
            poly.points.append(Point3(x3, y3, z3))
            poly.points.append(Point3(x4, y4, z4))
            normal = poly.getNormal()
            for point in poly.points:
                writer.addVertex(point, normal, colorf, (0.0, 1.0))
            tri.addVertex(point_id)
            tri.addVertex(point_id+1)
            tri.addVertex(point_id+3)
            tri.closePrimitive()
            tri.addConsecutiveVertices(point_id + 1, 3)
            tri.closePrimitive()
            point_id += 4
    dome = Geom(vdata)
    dome.addPrimitive(tri)
    node = GeomNode('dome')
    node.addGeom(dome)
    return node


def parseVector(s):
    return [float(v) for v in s.split(',')]

lastUniqueID = 0

class WorldObject(object):
    def __init__(self, objType):
        global lastUniqueID
        self.name = objType + ':' + str(lastUniqueID)
        lastUniqueID += 1
        self.node = None

class Block(WorldObject):
    def __init__(self, size, color):
        WorldObject.__init__(self, 'Block')
        self.geom = makeBox(color, (0,0,0), *size)
    def rotate(self, yaw, pitch, roll):
        self.node.setHpr(self.node, yaw, pitch, roll)
    def move(self, center):
        self.node.setPos(*center)

class Dome(WorldObject):
    def __init__(self, radius, color):
        WorldObject.__init__(self, 'Dome')
        self.geom = makeDome(color, radius, 8, 5)
    def move(self, center):
        self.node.setPos(*center)

class Ground(WorldObject):
    def __init__(self, radius, color):
        WorldObject.__init__(self, 'Ground')
        self.geom = makeBox(color, (0, 0, 0), radius, 0.5, radius)

class Ramp(WorldObject):
    def __init__(self, base, top, width, thickness, color):
        WorldObject.__init__(self, 'Block')
        self.base = base
        self.top = top
        distance = top - base
        length = distance.length()
        self.geom = makeBox(color, (0,0,0), thickness, width, length)
    def orientate(self):
        v1 = self.top - self.base
        if self.base.getX() != self.top.getX():
            p3 = Point3(self.top.getX()+100, self.top.getY(), self.top.getZ())
        else:
            p3 = Point3(self.top.getX(), self.top.getY(), self.top.getZ() + 100)
        v2 = self.top - p3
        up = v1.cross(v2)
        up.normalize()
        midpoint = Point3((self.base + self.top) / 2.0)
        self.node.setPos(midpoint)
        self.node.lookAt(self.top, up)

class World(object):
    def __init__(self, render):
        self.render = render
        self.name = None
        self.author = None
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.4, 0.4, 0.4, 1))
        render.setLight(render.attachNewNode(alight))
        dlight = DirectionalLight('directionalLight')
        dlight.setColor(Vec4(1, 1, 1, 1))
        lightNode = render.attachNewNode(dlight)
        lightNode.setHpr(20, -120, 0)
        render.setLight(lightNode)
        self.worldObjects = {}

    def addWorldObject(self, obj):
        self.worldObjects[obj.name] = obj
        obj.node = self.render.attachNewNode(obj.geom)

    def addBlock(self, center, size, color, yaw, pitch, roll):
        b = Block(size, color)
        self.addWorldObject(b)
        b.move(center)
        b.rotate(yaw, pitch, roll)
        return b

    def addDome(self, center, radius, color):
        d = Dome(radius, color)
        self.addWorldObject(d)
        d.move(center)
        return d

    def addRamp(self, base, top, width, thickness, color):
        r = Ramp(base, top, width, thickness, color)
        self.addWorldObject(r)
        r.orientate()

    def setGround(self, radius, color):
        g = Ground(radius, color)
        self.addWorldObject(g)
        return g

class MapParser(object):
    def __init__(self, render):
        self.render = render
        self.maps = []
    def parse_block(self, node, current):
        center = node.attributes.get('center')
        center = parseVector(center.value) if center else (0,0,0)
        size = node.attributes.get('size')
        size = parseVector(size.value) if size else (4,4,4)
        color = node.attributes.get('color')
        color = parseVector(color.value) if color else (1,1,1,1)
        yaw = node.attributes.get('yaw')
        yaw = float(yaw.value) if yaw else 0
        pitch = node.attributes.get('pitch')
        pitch = float(pitch.value) if pitch else 0
        roll = node.attributes.get('roll')
        roll = float(roll.value) if roll else 0
        current.addBlock(center, size, color, yaw, pitch, roll)
        
    def parse_ramp(self, node, current):
        base = node.attributes.get('base')
        base = parseVector(base.value) if base else (-2, 0, 0)
        base = Point3(*base)
        top = node.attributes.get('top')
        top = parseVector(top.value) if top else (2, 4, 0)
        top = Point3(*top)
        color = node.attributes.get('color')
        color = parseVector(color.value) if color else (1, 1, 1, 1)
        width = node.attributes.get('width') 
        width = float(width.value) if width else 8
        thickness = node.attributes.get('thickness')
        thickness = float(thickness.value) if thickness else 0
        current.addRamp(base, top, width, thickness, color)
    
    def parse_ground(self, node, current):
        color = parseVector(node.attributes['color'].value)
        current.setGround(500, color)

    def parse_dome(self, node, current):
        center = node.attributes.get('center')
        radius = node.attributes.get('radius')
        color = node.attributes.get('color')
        center = parseVector(center.value if center else '0,0,0')
        radius = float(radius.value if radius else '2.5')
        color = parseVector(color.value if color else '0,0,0')
        current.addDome(center, radius, color)

    def loadMaps(self, dom):
        for m in dom.getElementsByTagName('map'):
            current = World(render)
            current.name = m.attributes['name'].value
            current.author = m.attributes['author'].value
            for child in m.childNodes:
                name = "parse_" + child.nodeName.lower()
                if hasattr(self, name):
                    getattr(self, name)(child, current)
            self.maps.append(current)


def load(path, render):
    dom = parse(path)
    parser = MapParser(render)
    parser.loadMaps(dom)
    
