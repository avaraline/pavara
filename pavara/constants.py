from panda3d.core import BitMask32, Vec3

#world defaults

DEFAULT_AMBIENT_COLOR = (0.4, 0.4, 0.4, 1)
DEFAULT_GROUND_COLOR =  (0, 0, 0.15, 1)
DEFAULT_SKY_COLOR =     (0, 0, 0.15, 1)
DEFAULT_HORIZON_COLOR = (0, 0, 0.8, 1)
DEFAULT_HORIZON_SCALE = 0.05

MISSILE_SCALE = .29
GRENADE_SCALE = .35

#collision bitmask constants

NO_COLLISION_BITS = BitMask32.all_off()
MAP_COLLIDE_BIT =   BitMask32.bit(0)
SOLID_COLLIDE_BIT = BitMask32.bit(1)
GHOST_COLLIDE_BIT = BitMask32.bit(2)

#physics contstants

EXPLOSIONS_DONT_PUSH = ["expl", "ground"]
DEFAULT_GRAVITY = Vec3(0, -9.81, 0)
DEFAULT_FRICTION = 1
AIR_FRICTION = 0.02

#weapons stuff

PLASMA_SCALE = .3
MIN_PLASMA_CHARGE = .4
WALKER_RECHARGE_FACTOR = .23
WALKER_ENERGY_TO_GUN_CHARGE = (.10,.36)
WALKER_MIN_CHARGE_ENERGY = .2
PLASMA_LIFESPAN = 900
PLASMA_SOUND_FALLOFF = 20
MISSILE_LIFESPAN = 600

#missile/grenade engine color lists in rgb decimal format

ENGINE_COLORS = [ [173.0/255.0, 0, 0, 1] #dark red
                , [237.0/255.0, 118.0/255.0, 21.0/255.0, 1] #bright orange
                , [194.0/255.0, 116.0/255.0, 14.0/255.0, 1] #darker orange
                , [247.0/255.0, 76.0/255.0, 42.0/255.0, 1] #brighter red
                ]

