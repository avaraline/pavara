from pavara.utils import drill
from pavara.world import *
import random
import math

def parse_int(s, default=0):
    if s is None or not s.strip():
        return default
    return int(s.strip())

def parse_float(s, default=0.0):
    if s is None or not s.strip():
        return default
    return float(s.strip())

def parse_bool(s, default=False):
    if s is None or not s.strip():
        return default
    return s.strip().lower() in ('yes', 'y', 'true', 't', '1')

def parse_vector(s, default=None):
    if s is None or not s.strip():
        return default or (0, 0, 0)
    return [float(v.strip()) for v in s.split(',')]

def parse_color(s, default=None):
    v = parse_vector(s, default)
    if len(v) == 3:
        return list(v) + [1]
    return v

class Map (object):
    """
    Includes meta-information about a map, along with a World object containing all the objects.
    """

    name = None
    author = None
    tagline = None
    description = None
    world = None
    has_celestials = False
    effects = []

    def __init__(self, root, camera):
        self.name = root['name'] or 'Untitled Map'
        self.author = root['author'] or 'Unknown Author'
        self.tagline = root['tagline']
        self.description = root['description'] or 'No description.'
        self.world = World(camera, debug=parse_bool(root['debug']))
        self.process_children(root)
        if not self.has_celestials:
            self.world.add_celestial(math.radians(20), math.radians(45), (1, 1, 1, 1), 0.4, 30.0, False)
            self.world.add_celestial(math.radians(200), math.radians(20), (1, 1, 1, 1), 0.3, 30.0, False)
        self.world.create_celestial_node()

    def show(self, render):
        """
        Reparents the root NodePath of this Map's World to the given NodePath.
        """
        self.world.render.setColorOff()
        self.world.render.node().setAttrib(ColorAttrib.makeVertex())
        self.world.render.reparent_to(render)

    def process_children(self, node):
        for child in node.children():
            func_name = 'parse_%s' % child.tagname.lower()
            if hasattr(self, func_name):
                getattr(self, func_name)(child)

    def parse_static(self, node):
        world = self.world
        self.world = self.wrap_object(CompositeObject())
        self.process_children(node)
        world.attach(self.world)
        self.world = world

    def parse_transparent(self, node):
        alpha = parse_float(node['alpha'])
        self.effects.append(lambda effected: Transparent(effected, alpha))
        self.process_children(node)
        self.effects.pop()

    def parse_freesolid(self, node):
        mass = parse_float(node['mass'])
        self.effects.append(lambda effected: FreeSolid(effected, mass))
        self.process_children(node)
        self.effects.pop()

    def parse_hologram(self, node):
        self.effects.append(Hologram)
        self.process_children(node)
        self.effects.pop()

    def wrap_object(self, obj):
        for effect in reversed(self.effects):
            obj = effect(obj)
        return obj

    def parse_incarnator(self, node):
        pos = parse_vector(node['location'])
        heading = parse_float(node['heading'])
        incarn = self.wrap_object(Incarnator(pos, heading, name=node['id']))
        self.world.attach(incarn)

    def parse_block(self, node):
        center = parse_vector(node['center'])
        size = parse_vector(node['size'], (4, 4, 4))
        color = parse_color(node['color'], (1, 1, 1, 1))
        mass = parse_float(node['mass'])
        yaw = parse_float(node['yaw'])
        pitch = parse_float(node['pitch'])
        roll = parse_float(node['roll'])
        block = self.world.attach(self.wrap_object(Block(size, color, mass, center, (yaw, pitch, roll), name=node['id'])))

    def parse_ramp(self, node):
        base = parse_vector(node['base'])
        top = parse_vector(node['top'], (0, 4, 4))
        thickness = parse_float(node['thickness'])
        width = parse_float(node['width'], 8)
        color = parse_color(node['color'], (1, 1, 1, 1))
        mass = parse_float(node['mass'])
        yaw = parse_float(node['yaw'])
        pitch = parse_float(node['pitch'])
        roll = parse_float(node['roll'])
        ramp = self.world.attach(self.wrap_object(Ramp(base, top, width, thickness, color, mass, (yaw, pitch, roll), name=node['id'])))

    def parse_wedge(self, node):
        base = parse_vector(node['base'])
        top = parse_vector(node['top'], (0, 4, 4))
        width = parse_float(node['width'], 8)
        color = parse_color(node['color'], (1, 1, 1, 1))
        mass = parse_float(node['mass'])
        yaw = parse_float(node['yaw'])
        pitch = parse_float(node['pitch'])
        roll = parse_float(node['roll'])
        wedge = self.world.attach(self.wrap_object(Wedge(base, top, width, color, mass, (yaw, pitch, roll), name=node['id'])))

    def parse_blockramp(self, node):
        base = parse_vector(node['base'])
        top = parse_vector(node['top'], (0, 4, 4))
        thickness = parse_float(node['thickness'])
        width = parse_float(node['width'], 8)
        color = parse_color(node['color'], (1, 1, 1, 1))
        mass = parse_float(node['mass'])
        yaw = parse_float(node['yaw'])
        pitch = parse_float(node['pitch'])
        roll = parse_float(node['roll'])
        ramp = self.world.attach(self.wrap_object(BlockRamp(base, top, width, thickness, color, mass, (yaw, pitch, roll), name=node['id'])))

    def parse_ground(self, node):
        color = parse_color(node['color'], (1, 1, 1, 1))
        radius = parse_float(node['radius'], 1000)
        self.world.attach(self.wrap_object(Ground(radius, color, name=(node['id'] or 'ground'))))

    def parse_goody(self, node):
        model = node["model"]
        pos = parse_vector(node["location"])
        grenades = parse_int(node["grenades"])
        missles = parse_int(node["missles"])
        boosters = parse_int(node["boosters"])
        respawn = parse_float(node["respawn"], 8.0) # Default spawn time.
        spin = parse_vector(node['spin'])
        goody = self.world.attach(self.wrap_object(Goody(pos, model, (grenades, missles, boosters), respawn, spin)))

    def parse_dome(self, node):
        center = parse_vector(node['center'])
        radius = parse_float(node['radius'], 2.5)
        samples = parse_int(node['samples'], 8)
        planes = parse_int(node['planes'], 5)
        color = parse_color(node['color'], (1, 1, 1, 1))
        mass = parse_float(node['mass'])
        yaw = parse_float(node['yaw'])
        pitch = parse_float(node['pitch'])
        roll = parse_float(node['roll'])
        dome = self.world.attach(self.wrap_object(Dome(radius, samples, planes, color, mass, center, (yaw, pitch, roll), name=node['id'])))

    def parse_sky(self, node):
        color = parse_color(node['color'], DEFAULT_SKY_COLOR)
        horizon = parse_color(node['horizon'], DEFAULT_HORIZON_COLOR)
        ambient = parse_color(node['ambient'], DEFAULT_AMBIENT_COLOR)
        scale = parse_float(node['horizonScale'], DEFAULT_HORIZON_SCALE)

        self.world.set_ambient(ambient)
        self.world.sky.set_color(color)
        self.world.sky.set_horizon(horizon)
        self.world.sky.set_scale(scale)

        for child in node.children('celestial'):
            azimuth = math.radians(parse_float(child['azimuth'], 30))
            elevation = math.radians(parse_float(child['elevation'], 20))
            color = parse_color(child['color'], (1, 1, 1, 1))
            intensity = parse_float(child['intensity'], 0.6)
            visible = parse_bool(child['visible'])
            size = parse_float(child['size'], 30.0)
            self.world.add_celestial(azimuth, elevation, color, intensity, size, visible)
            self.has_celestials = True

        for child in node.children('starfield'):
            seed = parse_int(child['seed'])
            count = parse_int(child['count'])
            min_color = parse_color(child['minColor'], (1, 1, 1, 1))
            max_color = parse_color(child['maxColor'], (1, 1, 1, 1))
            min_size = parse_float(child['minSize'], 0.4)
            max_size = parse_float(child['maxSize'], 1.0)
            mode = child['mode'] or 'default'
            mode = mode.strip().lower()
            min_r = min_color[0]
            delta_r = max_color[0] - min_r
            min_g = min_color[1]
            delta_g = max_color[1] - min_g
            min_b = min_color[2]
            delta_b = max_color[2] - min_b
            delta_size = max_size - min_size
            two_pi = math.pi * 2
            half_pi = math.pi / 2
            if seed:
                random.seed(seed)
            for s in range(count):
                theta = two_pi * random.random()
                phi = abs(half_pi - math.acos(random.random()))
                if mode == 'realistic':
                    star_type = random.randint(0,2)
                    if star_type == 0: # white star
                        r = g = b = 1
                    elif star_type == 1: # orange/yellow
                        r = 1
                        g = 0.5 + random.random() * 0.5
                        b = g / 2
                    elif star_type == 2: # blue
                        b = 1
                        g = b * (1 - random.random() * 0.30)
                        r = g * (1 - random.random() * 0.30)
                elif mode == 'monochrome':
                    dice = random.random()
                    r = min_r + dice * delta_r
                    g = min_g + dice * delta_g
                    b = min_b + dice * delta_b
                else:
                    r = min_r + random.random() * delta_r
                    g = min_g + random.random() * delta_g
                    b = min_b + random.random() * delta_b
                color = (r, g, b, 1 - (1 - phi/math.pi)**6)
                size = min_size + random.random() * delta_size
                self.world.add_celestial(theta, phi, color, 0, size, True)

def load_maps(path, camera):
    """
    Given a path to an XML file and the camera, returns a list of parsed/populated Map objects.
    """
    root = drill.parse(path)
    if root.tagname.lower() == 'map':
        return [Map(root, camera)]
    else:
        maps = []
        for map_root in root.find('map'):
            maps.append(Map(map_root, camera))
        return maps
