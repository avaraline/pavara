from xml.dom.minidom import parse
from panda3d.core import Vec3, Geom, GeomNode, GeomVertexFormat, GeomVertexWriter, GeomVertexData
from panda3d.core import GeomTriangles, LRotationf, Point3, LOrientationf, AmbientLight, VBase4
from panda3d.core import DirectionalLight, Vec4

def myNormalize(myVec):
    myVec.normalize()
    return myVec

def makeSquare(colorf, x1,y1,z1, x2,y2,z2):
    if len(colorf) == 3:
        colorf = (colorf[0], colorf[1], colorf[2], 1)
    format=GeomVertexFormat.getV3n3cpt2()
    vdata=GeomVertexData('square', format, Geom.UHDynamic)

    vertex=GeomVertexWriter(vdata, 'vertex')
    normal=GeomVertexWriter(vdata, 'normal')
    color=GeomVertexWriter(vdata, 'color')
    texcoord=GeomVertexWriter(vdata, 'texcoord')
    
    #make sure we draw the sqaure in the right plane
    if x1!=x2:
        vertex.addData3f(x1, y1, z1)
        vertex.addData3f(x2, y1, z1)
        vertex.addData3f(x2, y2, z2)
        vertex.addData3f(x1, y2, z2)
        v1 = Point3(x1, y1, z1) - Point3(x2, y1, z1)
        if y1 != y2:
            v2 = Point3(x2, y1, z1) - Point3(x2, y2, z1)
        else:
            v2 = Point3(x2, y1, z1) - Point3(x2, y1, z2)
        n = myNormalize(v1.cross(v2))
        normal.addData3f(n)
        normal.addData3f(n)
        normal.addData3f(n)
        normal.addData3f(n)
        
    else:
        vertex.addData3f(x1, y1, z1)
        vertex.addData3f(x2, y2, z1)
        vertex.addData3f(x2, y2, z2)
        vertex.addData3f(x1, y1, z2)
        v1 = Point3(x1, y1, z1) - Point3(x2, y2, z1)
        v2 = Point3(x2, y2, z1) - Point3(x1, y1, z2)
        n = myNormalize(v1.cross(v2))
        normal.addData3f(n)
        normal.addData3f(n)
        normal.addData3f(n)
        normal.addData3f(n)

    #adding different colors to the vertex for visibility
    color.addData4f(*colorf)
    color.addData4f(*colorf)
    color.addData4f(*colorf)
    color.addData4f(*colorf)

    texcoord.addData2f(0.0, 1.0)
    texcoord.addData2f(0.0, 0.0)
    texcoord.addData2f(1.0, 0.0)
    texcoord.addData2f(1.0, 1.0)

    #quads arent directly supported by the Geom interface
    #you might be interested in the CardMaker class if you are
    #interested in rectangle though
    tri1=GeomTriangles(Geom.UHDynamic)
    tri2=GeomTriangles(Geom.UHDynamic)

    tri1.addVertex(0)
    tri1.addVertex(1)
    tri1.addVertex(3)

    tri2.addConsecutiveVertices(1,3)

    tri1.closePrimitive()
    tri2.closePrimitive()


    square=Geom(vdata)
    square.addPrimitive(tri1)
    square.addPrimitive(tri2)
    
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

    def loadMaps(self, dom):
        for m in dom.getElementsByTagName('map'):
            current = World(render)
            current.name = m.attributes['name'].value
            current.author = m.attributes['author'].value
            for child in m.childNodes:
                if child.nodeName.lower() == 'block':
                    center = child.attributes.get('center')
                    center = parseVector(center.value) if center else (0,0,0)
                    size = child.attributes.get('size')
                    size = parseVector(size.value) if size else (4,4,4)
                    color = child.attributes.get('color')
                    color = parseVector(color.value) if color else (1,1,1,1)
                    yaw = float(child.attributes['yaw'].value) if child.attributes.get('yaw') else 0
                    pitch = float(child.attributes['pitch'].value) if child.attributes.get('pitch') else 0
                    roll = float(child.attributes['roll'].value) if child.attributes.get('roll') else 0
                    current.addBlock(center, size, color, yaw, pitch, roll)

                elif child.nodeName.lower() == 'incarnator':
                    pass
                elif child.nodeName.lower() == 'ramp':
                    base = parseVector(child.attributes['base'].value) if child.attributes.get('base') else (-2, 0, 0)
                    base = Point3(*base)
                    top = parseVector(child.attributes['top'].value) if child.attributes.get('top') else (2, 4, 0)
                    top = Point3(*top)
                    color = parseVector(child.attributes['color'].value) if child.attributes.get('color') else (1, 1, 1, 1)
                    width = float(child.attributes['width'].value) if child.attributes.get('width') else 8
                    thickness = float(child.attributes['thickness'].value) if child.attributes.get('thickness') else 0
                    current.addRamp(base, top, width, thickness, color)
                elif child.nodeName.lower() == 'ground':
                    color = parseVector(child.attributes['color'].value)
                    current.setGround(500, color)
            self.maps.append(current)


def load(path, render):
    dom = parse(path)
    parser = MapParser(render)
    parser.loadMaps(dom)
    
