from math import pi, sin, cos
from panda3d.core import Vec3, Geom, GeomNode, GeomVertexFormat, GeomVertexWriter, GeomVertexData
from panda3d.core import GeomTriangles, LRotationf, LVector3f, Point3
import random

class InvalidPrimitive (Exception):
    pass

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
        points = [p for p in self.points if p not in seen and not seen.add(p)]
        if len(points) >= 3:
            v1 = points[0] - points[1]
            v2 = points[1] - points[2]
            normal = v1.cross(v2)
            normal.normalize()
        else:
            normal = Vec3.up()
        return normal

class GeomBuilder(object):

    def __init__(self, name='tris'):
        self.name = name
        self.vdata = GeomVertexData(name, GeomVertexFormat.get_v3n3cpt2(), Geom.UHDynamic)
        self.writer = VertexDataWriter(self.vdata)
        self.tris = GeomTriangles(Geom.UHDynamic)

    def _commit_polygon(self, poly, color):
        """
        Transmutes colors and vertices for tris and quads into visible geometry.
        """
        point_id = self.writer.count
        for p in poly.points:
            self.writer.add_vertex(p, poly.get_normal(), color, (0.0, 1.0))
        if len(poly.points) == 3:
            self.tris.add_consecutive_vertices(point_id, 3)
            self.tris.close_primitive()
        elif len(poly.points) == 4:
            self.tris.add_vertex(point_id)
            self.tris.add_vertex(point_id + 1)
            self.tris.add_vertex(point_id + 3)
            self.tris.close_primitive()
            self.tris.add_consecutive_vertices(point_id + 1, 3)
            self.tris.close_primitive()
        else:
            raise InvalidPrimitive
            
    def add_tri(self, color, points):
        self._commit_polygon(Polygon(points), color)
        self._commit_polygon(Polygon(points[::-1]), color)
        return self
        
    def add_rect(self, color, x1, y1, z1, x2, y2, z2):
        p1 = Point3(x1, y1, z1)
        p3 = Point3(x2, y2, z2)

        # Make sure we draw the rect in the right plane.
        if x1 != x2:
            p2 = Point3(x2, y1, z1)
            p4 = Point3(x1, y2, z2)
        else:
            p2 = Point3(x2, y2, z1)
            p4 = Point3(x1, y1, z2)

        self._commit_polygon(Polygon([p1, p2, p3, p4]), color)

        return self

    def add_block(self, color, center, size, rot=None):
        x_shift = size[0] / 2.0
        y_shift = size[1] / 2.0
        z_shift = size[2] / 2.0
        rot = LRotationf(0, 0, 0) if rot is None else rot

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
        vertices = [rot.xform(v) + LVector3f(*center) for v in vertices]

        faces = (
            # XY
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            # XZ
            [vertices[0], vertices[3], vertices[4], vertices[7]],
            [vertices[6], vertices[5], vertices[2], vertices[1]],
            # YZ
            [vertices[5], vertices[4], vertices[3], vertices[2]],
            [vertices[7], vertices[6], vertices[1], vertices[0]],
        )

        if size[0] and size[1]:
            self._commit_polygon(Polygon(faces[0]), color)
            self._commit_polygon(Polygon(faces[1]), color)
        if size[0] and size[2]:
            self._commit_polygon(Polygon(faces[2]), color)
            self._commit_polygon(Polygon(faces[3]), color)
        if size[1] and size[2]:
            self._commit_polygon(Polygon(faces[4]), color)
            self._commit_polygon(Polygon(faces[5]), color)

        return self

    def add_ramp(self, color, base, top, width, thickness, rot=None):
        midpoint = Point3((top + base) / 2.0)
        rot = LRotationf(0, 0, 0) if rot is None else rot

        # Temporarily move `base` and `top` to positions relative to a midpoint
        # at (0, 0, 0).
        if midpoint != Point3(0, 0, 0):
            base = Point3(base - (midpoint - Point3(0, 0, 0)))
            top = Point3(top - (midpoint - Point3(0, 0, 0)))
        p3 = Point3(top.get_x(), top.get_y() - thickness, top.get_z())
        p4 = Point3(base.get_x(), base.get_y() - thickness, base.get_z())

        # Use three points to calculate an offset vector we can apply to `base`
        # and `top` in order to find the required vertices.
        offset = (Point3(top + Vec3(0, -1000, 0)) - base).cross(top - base)
        offset.normalize()
        offset *= (width / 2.0)

        vertices = (
            Point3(top - offset),
            Point3(base - offset),
            Point3(base + offset),
            Point3(top + offset),
            Point3(p3 + offset),
            Point3(p3 - offset),
            Point3(p4 - offset),
            Point3(p4 + offset),
        )
        vertices = [rot.xform(v) + LVector3f(*midpoint) for v in vertices]

        faces = (
            # Top and bottom.
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[7], vertices[6], vertices[5], vertices[4]],
            # Back and front.
            [vertices[0], vertices[3], vertices[4], vertices[5]],
            [vertices[6], vertices[7], vertices[2], vertices[1]],
            # Left and right.
            [vertices[0], vertices[5], vertices[6], vertices[1]],
            [vertices[7], vertices[4], vertices[3], vertices[2]],
        )

        if width and (p3 - base).length():
            self._commit_polygon(Polygon(faces[0]), color)
            self._commit_polygon(Polygon(faces[1]), color)
        if width and thickness:
            self._commit_polygon(Polygon(faces[2]), color)
            self._commit_polygon(Polygon(faces[3]), color)
        if thickness and (p3 - base).length():
            self._commit_polygon(Polygon(faces[4]), color)
            self._commit_polygon(Polygon(faces[5]), color)

        return self

    def add_wedge(self, color, base, top, width, rot=None):
        delta_y = top.get_y() - base.get_y()
        midpoint = Point3((top + base) / 2.0)
        rot = LRotationf(0, 0, 0) if rot is None else rot

        # Temporarily move `base` and `top` to positions relative to a midpoint
        # at (0, 0, 0).
        if midpoint != Point3(0, 0, 0):
            base = Point3(base - (midpoint - Point3(0, 0, 0)))
            top = Point3(top - (midpoint - Point3(0, 0, 0)))
        p3 = Point3(top.get_x(), base.get_y(), top.get_z())

        # Use three points to calculate an offset vector we can apply to `base`
        # and `top` in order to find the required vertices. Ideally we'd use
        # `p3` as the third point, but `p3` can potentially be the same as `top`
        # if delta_y is 0, so we'll just calculate a new point relative to top
        # that differs in elevation by 1000, because that sure seems unlikely.
        # The "direction" of that point relative to `top` does depend on whether
        # `base` or `top` is higher. Honestly, I don't know why that's important
        # for wedges but not for ramps.
        if base.get_y() > top.get_y():
            direction = Vec3(0, 1000, 0)
        else:
            direction = Vec3(0, -1000, 0)
        offset = (Point3(top + direction) - base).cross(top - base)
        offset.normalize()
        offset *= (width / 2.0)

        vertices = (
            Point3(top - offset),
            Point3(base - offset),
            Point3(base + offset),
            Point3(top + offset),
            Point3(p3 + offset),
            Point3(p3 - offset),
        )
        vertices = [rot.xform(v) + LVector3f(*midpoint) for v in vertices]

        faces = (
            # The slope.
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            # The bottom.
            [vertices[5], vertices[4], vertices[2], vertices[1]],
            # The back.
            [vertices[0], vertices[3], vertices[4], vertices[5]],
            # The sides.
            [vertices[5], vertices[1], vertices[0]],
            [vertices[4], vertices[3], vertices[2]],
        )

        if width or delta_y:
            self._commit_polygon(Polygon(faces[0]), color)
        if width and (p3 - base).length():
            self._commit_polygon(Polygon(faces[1]), color)
        if width and delta_y:
            self._commit_polygon(Polygon(faces[2]), color)
        if delta_y and (p3 - base).length():
            self._commit_polygon(Polygon(faces[3]), color)
            self._commit_polygon(Polygon(faces[4]), color)

        return self

    def add_dome(self, color, center, radius, samples, planes, rot=None):
        two_pi = pi * 2
        half_pi = pi / 2
        azimuths = [(two_pi * i) / samples for i in range(samples + 1)]
        elevations = [(half_pi * i) / (planes - 1) for i in range(planes)]
        rot = LRotationf(0, 0, 0) if rot is None else rot

        # Generate polygons for all but the top tier. (Quads)
        for i in range(0, len(elevations) - 2):
            for j in range(0, len(azimuths) - 1):
                x1, y1, z1 = to_cartesian(azimuths[j], elevations[i], radius)
                x2, y2, z2 = to_cartesian(azimuths[j], elevations[i + 1], radius)
                x3, y3, z3 = to_cartesian(azimuths[j + 1], elevations[i + 1], radius)
                x4, y4, z4 = to_cartesian(azimuths[j + 1], elevations[i], radius)

                vertices = (
                    Point3(x1, y1, z1),
                    Point3(x2, y2, z2),
                    Point3(x3, y3, z3),
                    Point3(x4, y4, z4),
                )
                vertices = [rot.xform(v) + LVector3f(*center) for v in vertices]

                self._commit_polygon(Polygon(vertices), color)

        # Generate polygons for the top tier. (Tris)
        for k in range(0, len(azimuths) - 1):
            x1, y1, z1 = to_cartesian(azimuths[k], elevations[len(elevations) - 2], radius)
            x2, y2, z2 = Vec3(0, radius, 0)
            x3, y3, z3 = to_cartesian(azimuths[k + 1], elevations[len(elevations) - 2], radius)

            vertices = (
                Point3(x1, y1, z1),
                Point3(x2, y2, z2),
                Point3(x3, y3, z3),
            )
            vertices = [rot.xform(v) + LVector3f(*center) for v in vertices]

            self._commit_polygon(Polygon(vertices), color)

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

