from xml.dom.minidom import parse
from math import pi, sin, cos, radians, acos
from panda3d.core import Vec3, Geom, GeomNode, GeomVertexFormat, GeomVertexWriter, GeomVertexData
from panda3d.core import GeomTriangles, LRotationf, Point3, LOrientationf, AmbientLight, VBase4
from panda3d.core import DirectionalLight, Vec4, Plane, BitMask32, Shader
from panda3d.core import CompassEffect, TransparencyAttrib
from panda3d.ode import OdeBoxGeom, OdeSphereGeom
from wireGeom import wireGeom
import random

from Hector import Hector

DEBUG_MAP_COLLISION = False
MAP_COLLIDE_BIT = BitMask32(0x00000001)
MAP_COLLIDE_CATEGORY = BitMask32(0x00000002)

def addAlpha(color):
    if len(color) == 3:
        color = (color[0], color[1], color[2], 1)
    return color

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
    colorf = addAlpha(colorf)
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
    colorf = addAlpha(colorf)
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
        self.solid = None

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
        self.solid = CollisionPlane(Plane(Vec3(0, 1, 0), Point3(0, 0, 0)))

class Ramp(WorldObject):
    def __init__(self, base, top, width, thickness, color):
        WorldObject.__init__(self, 'Block')
        self.base = base
        self.top = top
        self.thickness = thickness
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

class Incarnator(WorldObject):
	def __init__(self, pos, angle):
		WorldObject.__init__(self, 'Incarnator')
		self.pos = pos
		self.angle = angle
		self.h = None
		
	def placeHector(self, render):
		self.h = Hector(render, self.pos[0], self.pos[1], self.pos[2], self.angle)

class World(object):
    def __init__(self, render, cam, camLens, physSpace):
        self.cam = cam
        self.render = render
        self.physSpace = physSpace
        self.name = None
        self.author = None
        
        self.setGround((0.75,0.5,0.25,1))
        self.setSky((0.7, 0.80, 1, 1))
        self.setHorizon((1, 0.8, 0, 1))
        self.setHorizonScale(0.05)

        self.makeSky(cam, camLens)

        self.makeAmbientLight()
        self.worldObjects = {}
        self.solids = []

    def makeAmbientLight(self):
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.4, 0.4, 0.4, 1))
        self.ambientLight = self.render.attachNewNode(alight)
        self.render.setLight(self.ambientLight)
        
    def makeSky(self, cam, camLens):
        node = GeomNode('sky')
        bounds = camLens.makeBounds()
        dl = bounds.getMin()
        ur = bounds.getMax()
        z = dl.getZ() * 0.99
        node.addGeom(makeSquare((1,1,1,1), dl.getX(), dl.getY(), 0, ur.getX(), ur.getY(), 0))
        self.sky = render.attachNewNode(node)
        self.sky.reparentTo(cam)
        self.sky.setPos(cam, 0,0, z)
        self.loadShader('Shaders/Sky.sha')

    def loadShader(self, path):
        shader = Shader.load(path)
        self.sky.setShader(shader)
        self.render.setShaderInput('camera', base.cam)
        self.render.setShaderInput('sky', self.sky)
        
    def addWorldObject(self, obj):
        self.worldObjects[obj.name] = obj
        obj.node = self.render.attachNewNode(obj.geom)
        if(obj.solid):
        	self.solids.append(obj.solid)

    def addBlock(self, center, size, color, yaw, pitch, roll):
        b = Block(size, color)
        self.addWorldObject(b)
        b.move(center)
        b.rotate(yaw, pitch, roll)
        blockGeom = OdeBoxGeom(self.physSpace, size[0], size[1], size[2])
        blockGeom.setCollideBits(MAP_COLLIDE_BIT)
        blockGeom.setCategoryBits(MAP_COLLIDE_CATEGORY)
        blockGeom.setPosition(b.node.getPos())
        blockGeom.setQuaternion(b.node.getQuat())
        if DEBUG_MAP_COLLISION:
			blockDebugShape = wireGeom().generate('box', extents = (size[0],size[1],size[2]))
			blockDebugShape.reparentTo(render)
			blockDebugShape.setPos(b.node.getPos())
			blockDebugShape.setQuat(b.node.getQuat())
        return b

    def addDome(self, center, radius, color):
        d = Dome(radius, color)
        self.addWorldObject(d)
        d.move(center)
        
        domeGeom = OdeSphereGeom(self.physSpace, radius)
        domeGeom.setCollideBits(MAP_COLLIDE_BIT)
        domeGeom.setCategoryBits(MAP_COLLIDE_CATEGORY)
        domeGeom.setPosition(d.node.getPos())
        domeGeom.setQuaternion(d.node.getQuat())
        
        if DEBUG_MAP_COLLISION:
        	domeDebugShape = wireGeom().generate('sphere', radius=radius)
        	domeDebugShape.reparentTo(render)
        	domeDebugShape.setPos(d.node.getPos(render))
        	domeDebugShape.setQuat(d.node.getQuat(render))
        
        return d

    def addRamp(self, base, top, width, thickness, color):
        r = Ramp(base, top, width, thickness, color)
        self.addWorldObject(r)
        r.orientate()
        
        #physics doesn't work with 0 thickness blocks!
        if thickness == 0:
        	thickness = .001
        
        rampGeom = OdeBoxGeom(self.physSpace, thickness, width, (top-base).length())
        rampGeom.setCollideBits(MAP_COLLIDE_BIT)
        rampGeom.setCategoryBits(MAP_COLLIDE_CATEGORY)
        rampGeom.setPosition(r.node.getPos())
        rampGeom.setQuaternion(r.node.getQuat())
        if DEBUG_MAP_COLLISION:
			rampDebugShape = wireGeom().generate('box', extents = (thickness, width, (top-base).length()))
			rampDebugShape.reparentTo(render)
			rampDebugShape.setPos(r.node.getPos())
			rampDebugShape.setQuat(r.node.getQuat())        
        return r
        
    def addIncarn(self, pos, angle):
    	i = Incarnator(pos, angle)
    	#i.placeHector(self.render)

    def setAmbientLight(self, color):
        color = addAlpha(color)
        self.ambientLight.node().setColor(color)

    def setHorizon(self, color):
        color = addAlpha(color)
        self.horizonColor = color
        render.setShaderInput('horizonColor', *self.horizonColor)

    def setHorizonScale(self, height):
        self.horizonScale = height
        render.setShaderInput('gradientHeight', self.horizonScale, 0, 0, 0)

    def setSky(self, color):
        color = addAlpha(color)
        self.skyColor = color
        render.setShaderInput('skyColor', *self.skyColor)

    def setGround(self, color):
        color = addAlpha(color)
        self.groundColor = color
        self.render.setShaderInput('groundColor', *self.groundColor)
   
    def addCelestial(self, azimuth, elevation, color, intensity, radius, visible):
        location = Vec3(toCartesian(azimuth, elevation, 1000.0 * 255.0 / 256.0))
        dlight = DirectionalLight('directionalLight')
        dlight.setColor((color[0]*intensity, color[1]*intensity, color[2]*intensity, 1.0))
        lightNode = self.render.attachNewNode(dlight)
        lightNode.lookAt(*(location * -1))
        self.render.setLight(lightNode)
        if visible:
            sphere = loader.loadModel('misc/sphere')
            sphere.setTransparency(TransparencyAttrib.MAlpha)
            sphere.reparentTo(self.render)
            sphere.setLightOff()
            sphere.setEffect(CompassEffect.make(self.cam, CompassEffect.PPos))
            sphere.setScale(45*radius)
            sphere.setColor(*color)
            sphere.setPos(location)

class MapParser(object):
    def __init__(self, render, physSpace):
        self.render = render
        self.physSpace = physSpace
        self.maps = []
        self.solids = []

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
        current.setGround(color)

    def parse_dome(self, node, current):
        center = node.attributes.get('center')
        radius = node.attributes.get('radius')
        color = node.attributes.get('color')
        center = parseVector(center.value if center else '0,0,0')
        radius = float(radius.value if radius else '2.5')
        color = parseVector(color.value if color else '0,0,0')
        current.addDome(center, radius, color)

    def parse_starfield(self, node, current):
        seed = node.attributes.get('seed')
        count = node.attributes.get('count')
        minColor = node.attributes.get('minColor')
        maxColor = node.attributes.get('maxColor')
        minSize = node.attributes.get('minSize')
        maxSize = node.attributes.get('maxSize')
        monochrome = node.attributes.get('monochrome')
        if seed:
            random.seed(int(seed.value))
        count = int(count.value) if count else 500
        minColor = parseVector(minColor.value) if minColor else (1,1,1,1)
        maxColor = parseVector(maxColor.value) if maxColor else (1,1,1,1)
        minSize = float(minSize.value) if minSize else 0.025
        maxSize = float(maxSize.value) if maxSize else 0.025
        monochrome = True if monochrome and monochrome.value.lower() in ('yes', 'y', 'true', 't') else False
        minR = minColor[0]
        deltaR = maxColor[0] - minR
        minG = minColor[1]
        deltaG = maxColor[1] - minG
        minB = minColor[2]
        deltaB = maxColor[2] - minB
        deltaSize = maxSize - minSize
        two_pi = pi * 2
        half_pi = pi / 2
        for s in range(count):
            theta = two_pi * random.random()
            phi = abs(half_pi - acos(random.random()))
            starType = random.randint(0,2)
            #if starType == 0: # white star
            #    r = g = b = 1
            #elif starType == 1: # orange/yellow
            #    r = 1
            #    g = 0.5 + random.random() * 0.5
            #    b = g/2
            #elif starType == 2: # blue
            #    b = 1
            #    g = b * (1 - random.random() * 0.30)
            #    r = g * (1 - random.random() * 0.30)
            if monochrome:
                dice = random.random()
                r = minR + dice * deltaR
                g = minG + dice * deltaG
                b = minB + dice * deltaB
            else:
                r = minR + random.random() * deltaR
                g = minG + random.random() * deltaG
                b = minB + random.random() * deltaB
            color = (r, g, b, 1 - (1 - phi/pi)**6)
            size = minSize + random.random() * deltaSize
            current.addCelestial(theta, phi, color, 0, size, True)

            
    def parse_sky(self, node, current):
        color = node.attributes.get('color')
        horizon = node.attributes.get('horizon')
        ambient = node.attributes.get('ambient')
        horizonScale = node.attributes.get('horizonScale')
        if color:
            current.setSky(parseVector(color.value))
        if horizon:
            current.setHorizon(parseVector(horizon.value))
        if ambient:
            current.setAmbientLight(parseVector(ambient.value))
        if horizonScale:
            current.setHorizonScale(float(horizonScale.value))
        celestialCount = 0
        for child in node.childNodes:
            if "celestial" == child.nodeName.lower():
                azimuth = child.attributes.get('azimuth')
                elevation = child.attributes.get('elevation')
                color = child.attributes.get('color')
                intensity = child.attributes.get('intensity')
                visible = child.attributes.get('visible')
                azimuth = radians(float(azimuth.value) if azimuth else 30)
                elevation = radians(float(elevation.value) if elevation else 20)
                color = parseVector(color.value) if color else (1.0, 1.0, 1.0, 1.0)
                intensity = float(intensity.value) if intensity else 0.6
                visible = True if visible and visible.value.lower() in ('yes', 'y', 'true', 't') else False
                current.addCelestial(azimuth, elevation, color, intensity, 1.0, visible)
                celestialCount += 1
        if celestialCount == 0:
            current.addCelestial(radians(20), radians(45), (1,1,1,1), 0.4, 1.0, False)
            current.addCelestial(radians(200), radians(20), (1,1,1,1), 0.3, 1.0, False)

    def loadMaps(self, dom):
        for m in dom.getElementsByTagName('map'):
            current = World(render, base.cam, base.camLens, self.physSpace)
            current.name = m.attributes['name'].value
            current.author = m.attributes['author'].value
            for child in m.childNodes:
                name = "parse_" + child.nodeName.lower()
                if hasattr(self, name):
                    getattr(self, name)(child, current)
            self.maps.append(current)
        
def load(path, render, physSpace):
    dom = parse(path)
    parser = MapParser(render, physSpace)
    parser.loadMaps(dom)
    return parser
    
