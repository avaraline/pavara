from math import pi, hypot, sin, cos, radians, acos
from panda3d.core import Vec3, Geom, GeomNode, GeomVertexFormat, GeomVertexWriter, GeomVertexData
from panda3d.core import GeomTriangles, LRotationf, LVector3f, Point3, LOrientationf, AmbientLight, VBase4
from panda3d.core import DirectionalLight, Vec4, Plane, Shader
from panda3d.core import CompassEffect, TransparencyAttrib
import random

class VertexDataWriter (object):

    def __init__(self, vdata):
        self.count = 0
        self.vertex = GeomVertexWriter(vdata, 'vertex')
        self.normal = GeomVertexWriter(vdata, 'normal')
        self.color = GeomVertexWriter(vdata, 'color')
        self.texcoord = GeomVertexWriter(vdata, 'texcoord')

    def add_vertex(self, point, normal, color, texcoord):
        self.vertex.add_data3f(point)
        self.normal.add_data3f(normal)
        self.color.add_data4f(*color)
        self.texcoord.add_data2f(*texcoord)
        self.count += 1

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

class GeomBuilder(object):

    def __init__(self, name='tris'):
        self.name = name
        self.vdata = GeomVertexData(name, GeomVertexFormat.get_v3n3cpt2(), Geom.UHDynamic)
        self.writer = VertexDataWriter(self.vdata)
        self.tris = GeomTriangles(Geom.UHDynamic)

    def add_rect(self, colorf, x1, y1, z1, x2, y2, z2):
        point_id = self.writer.count
        aasquare = make_axis_aligned_rect(x1, y1, z1, x2, y2, z2)
        # Add points to vertex data.
        normal = aasquare.get_normal()
        for point in aasquare.points:
            self.writer.add_vertex(point, normal, colorf, (0.0, 1.0))

        self.tris.add_vertex(point_id)
        self.tris.add_vertex(point_id + 1)
        self.tris.add_vertex(point_id + 3)
        self.tris.close_primitive()
        self.tris.add_consecutive_vertices(point_id + 1, point_id + 3)
        self.tris.close_primitive()

        return self

    def add_block(self, color, center, size, rot=None):
        rot2 = rot
        rot = LRotationf(0, 0, 0) if rot is None else rot
        x_shift = size[0] / 2.0
        y_shift = size[1] / 2.0
        z_shift = size[2] / 2.0

        vertices = (
            Point3(-x_shift, +y_shift, +z_shift),
            Point3(-x_shift, -y_shift, +z_shift),
            Point3(+x_shift, -y_shift, +z_shift),
            Point3(+x_shift, +y_shift, +z_shift),
            Point3(+x_shift, +y_shift, -z_shift),
            Point3(+x_shift, -y_shift, -z_shift),
            Point3(-x_shift, -y_shift, -z_shift),
            Point3(-x_shift, +y_shift, -z_shift),
        )
        #if rot2:
        #    rot = rot * LRotationf(0, 45, 0)
        vertices = [rot.xform(vertex) + LVector3f(*center) for vertex in vertices]

        faces = (
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            [vertices[7], vertices[0], vertices[3], vertices[4]],
            [vertices[4], vertices[3], vertices[2], vertices[5]],
            [vertices[5], vertices[2], vertices[1], vertices[6]],
            [vertices[6], vertices[1], vertices[0], vertices[7]],
        )

        point_id = self.writer.count
        for f in faces:
            poly = Polygon(f)
            normal = poly.get_normal()
            for p in poly.points:
                self.writer.add_vertex(p, normal, color, (0.0, 1.0))
            self.tris.add_vertex(point_id)
            self.tris.add_vertex(point_id + 1)
            self.tris.add_vertex(point_id + 3)
            self.tris.close_primitive()
            self.tris.add_consecutive_vertices(point_id + 1, 3)
            self.tris.close_primitive()
            point_id += 4

        return self


    def add_dome(self, colorf, center, radius, samples, planes, rot=None):
        if not rot:
            rot = LRotationf()
        center = Vec3(*center)
        two_pi = pi * 2
        half_pi = pi / 2
        azimuths = [(two_pi * i) / samples for i in range(samples + 1)]
        elevations = [(half_pi * i) / (planes - 1) for i in range(planes)]
        point_id = self.writer.count
        for i in range(0, len(elevations) - 1):
            for j in range(0, len(azimuths) - 1):
                poly = Polygon()
                x1, y1, z1 = to_cartesian(azimuths[j], elevations[i], radius)
                x2, y2, z2 = to_cartesian(azimuths[j], elevations[i + 1], radius)
                x3, y3, z3 = to_cartesian(azimuths[j + 1], elevations[i + 1], radius)
                x4, y4, z4 = to_cartesian(azimuths[j + 1], elevations[i], radius)
                p = Point3(x1, y1, z1)
                p = rot.xform(p) + center
                poly.points.append(p)
                p = Point3(x2, y2, z2)
                p = rot.xform(p) + center
                poly.points.append(p)
                p = Point3(x3, y3, z3)
                p = rot.xform(p) + center
                poly.points.append(p)
                p = Point3(x4, y4, z4)
                p = rot.xform(p) + center
                poly.points.append(p)
                normal = poly.get_normal()
                for point in poly.points:
                    self.writer.add_vertex(point, normal, colorf, (0.0, 1.0))
                self.tris.add_vertex(point_id)
                self.tris.add_vertex(point_id + 1)
                self.tris.add_vertex(point_id + 3)
                self.tris.close_primitive()
                self.tris.add_consecutive_vertices(point_id + 1, 3)
                self.tris.close_primitive()
                point_id += 4

        return self

    def get_geom(self):
        geom = Geom(self.vdata)
        geom.add_primitive(self.tris)
        return geom

    def get_geom_node(self):
        node = GeomNode(self.name)
        node.add_geom(self.get_geom())
        return node


def to_cartesian(azimuth, elevation, length):
    x = length * sin(azimuth) * cos(elevation)
    y = length * sin(elevation)
    z = -length * cos(azimuth) * cos(elevation)
    return (x, y, z)

