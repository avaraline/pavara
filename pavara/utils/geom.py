from math import pi, hypot, sin, cos, radians, acos
from panda3d.core import Vec3, Geom, GeomNode, GeomVertexFormat, GeomVertexWriter, GeomVertexData
from panda3d.core import GeomTriangles, LRotationf, Point3, LOrientationf, AmbientLight, VBase4
from panda3d.core import DirectionalLight, Vec4, Plane, Shader
from panda3d.core import CompassEffect, TransparencyAttrib
import random

class VertexDataWriter (object):

    def __init__(self, vdata):
        self.vertex = GeomVertexWriter(vdata, 'vertex')
        self.normal = GeomVertexWriter(vdata, 'normal')
        self.color = GeomVertexWriter(vdata, 'color')
        self.texcoord = GeomVertexWriter(vdata, 'texcoord')

    def add_vertex(self, point, normal, color, texcoord):
        self.vertex.add_data3f(point)
        self.normal.add_data3f(normal)
        self.color.add_data4f(*color)
        self.texcoord.add_data2f(*texcoord)

class Polygon (object):

    def __init__(self, points=None):
        self.points = points or []

    def get_normal(self):
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

def make_axis_aligned_rect(x1, y1, z1, x2, y2, z2):
    p1 = Point3(x1, y1, z1)
    p3 = Point3(x2, y2, z2)
    # Make sure we draw the rect in the right plane.
    if x1 != x2:
        p2 = Point3(x2, y1, z1)
        p4 = Point3(x1, y2, z2)
    else:
        p2 = Point3(x2, y2, z1)
        p4 = Point3(x1, y1, z2)
    return Polygon([p1, p2, p3, p4])

def make_rect(colorf, x1, y1, z1, x2, y2, z2):
    vdata = GeomVertexData('square', GeomVertexFormat.get_v3n3cpt2(), Geom.UHDynamic)
    writer = VertexDataWriter(vdata)
    aasquare = make_axis_aligned_rect(x1, y1, z1, x2, y2, z2)
    # Add points to vertex data.
    normal = aasquare.get_normal()
    for point in aasquare.points:
        writer.add_vertex(point, normal, colorf, (0.0, 1.0))

    tri = GeomTriangles(Geom.UHDynamic)
    tri.add_vertex(0)
    tri.add_vertex(1)
    tri.add_vertex(3)
    tri.close_primitive()
    tri.add_consecutive_vertices(1, 3)
    tri.close_primitive()

    square = Geom(vdata)
    square.add_primitive(tri)

    return square

def make_block(color, center, x_size, y_size, z_size):
    x_shift = x_size / 2.0
    y_shift = y_size / 2.0
    z_shift = z_size / 2.0

    vertices = (
        Point3(center[0] - x_shift, center[1] + y_shift, center[2] + z_shift),
        Point3(center[0] - x_shift, center[1] - y_shift, center[2] + z_shift),
        Point3(center[0] + x_shift, center[1] - y_shift, center[2] + z_shift),
        Point3(center[0] + x_shift, center[1] + y_shift, center[2] + z_shift),
        Point3(center[0] + x_shift, center[1] + y_shift, center[2] - z_shift),
        Point3(center[0] + x_shift, center[1] - y_shift, center[2] - z_shift),
        Point3(center[0] - x_shift, center[1] - y_shift, center[2] - z_shift),
        Point3(center[0] - x_shift, center[1] + y_shift, center[2] - z_shift),
    )

    faces = (
        [vertices[0], vertices[1], vertices[2], vertices[3]],
        [vertices[4], vertices[5], vertices[6], vertices[7]],
        [vertices[7], vertices[0], vertices[3], vertices[4]],
        [vertices[4], vertices[3], vertices[2], vertices[5]],
        [vertices[5], vertices[2], vertices[1], vertices[6]],
        [vertices[6], vertices[1], vertices[0], vertices[7]],
    )

    vdata = GeomVertexData('block', GeomVertexFormat.get_v3n3cpt2(), Geom.UHDynamic)
    writer = VertexDataWriter(vdata)
    tri = GeomTriangles(Geom.UHDynamic)

    point_id = 0
    for f in faces:
        poly = Polygon(f)
        for p in poly.points:
            writer.add_vertex(p, poly.get_normal(), color, (0.0, 1.0))
        tri.add_vertex(point_id)
        tri.add_vertex(point_id + 1)
        tri.add_vertex(point_id + 3)
        tri.close_primitive()
        tri.add_consecutive_vertices(point_id + 1, 3)
        tri.close_primitive()
        point_id += 4

    block = Geom(vdata)
    block.add_primitive(tri)

    node = GeomNode('block')
    node.add_geom(block)

    return node

def to_cartesian(azimuth, elevation, length):
    x = length * sin(azimuth) * cos(elevation)
    y = length * sin(elevation)
    z = -length * cos(azimuth) * cos(elevation)
    return (x, y, z)

def make_dome(colorf, radius, samples, planes):
    vdata = GeomVertexData('square', GeomVertexFormat.get_v3n3cpt2(), Geom.UHDynamic)
    writer = VertexDataWriter(vdata)
    two_pi = pi * 2
    half_pi = pi / 2
    azimuths = [(two_pi * i) / samples for i in range(samples + 1)]
    elevations = [(half_pi * i) / (planes - 1) for i in range(planes)]
    point_id = 0
    tri = GeomTriangles(Geom.UHDynamic)
    for i in range(0, len(elevations) - 1):
        for j in range(0, len(azimuths) - 1):
            poly = Polygon()
            x1, y1, z1 = to_cartesian(azimuths[j], elevations[i], radius)
            x2, y2, z2 = to_cartesian(azimuths[j], elevations[i + 1], radius)
            x3, y3, z3 = to_cartesian(azimuths[j + 1], elevations[i + 1], radius)
            x4, y4, z4 = to_cartesian(azimuths[j + 1], elevations[i], radius)
            poly.points.append(Point3(x1, y1, z1))
            poly.points.append(Point3(x2, y2, z2))
            poly.points.append(Point3(x3, y3, z3))
            poly.points.append(Point3(x4, y4, z4))
            normal = poly.get_normal()
            for point in poly.points:
                writer.add_vertex(point, normal, colorf, (0.0, 1.0))
            tri.add_vertex(point_id)
            tri.add_vertex(point_id + 1)
            tri.add_vertex(point_id + 3)
            tri.close_primitive()
            tri.add_consecutive_vertices(point_id + 1, 3)
            tri.close_primitive()
            point_id += 4
    dome = Geom(vdata)
    dome.add_primitive(tri)
    node = GeomNode('dome')
    node.add_geom(dome)
    return node
