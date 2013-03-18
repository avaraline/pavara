from panda3d.core import Point3, Vec3


class Integrator(object):
    """Integrator is based on a game physics article. It's supposedly much less
       dependent on frame rate than simply adding a multiple of dt to the velocity
       of something in every frame.

       http://gafferongames.com/game-physics/integration-basics/"""

    def __init__(self, accel):
        self.accel = accel

    def acceleration(self, x, v, dt):
        return self.accel

    def evaluate(self, x, v, dt, dx, dv):
        x = x + dx * dt
        v = v + dv * dt

        dx = v
        dv = self.acceleration(x, v, dt)

        return dx, dv

    def integrate(self, x, v, dt):
        dxa, dva = self.evaluate(x, v, 0.0, Vec3(0, 0, 0), Vec3(0,0,0))
        dxb, dvb = self.evaluate(x, v, dt*0.5, dxa, dva)
        dxc, dvc = self.evaluate(x, v, dt*0.5, dxb, dvb)
        dxd, dvd = self.evaluate(x, v, dt, dxc, dvc)

        dxdt = (dxa + (dxb + dxc)*2.0 + dxd) * 1.0/6.0
        dvdt = (dva + (dvb + dvc)*2.0 + dvd) * 1.0/6.0
        x = x + dxdt * dt
        v = v + dvdt * dt
        return x, v

class Friction(Integrator):

    def __init__(self, accel, friction):
        super(Friction, self).__init__(accel)
        self.friction = friction


    def acceleration(self, x, v, dt):
        direction = self.accel - v
        if direction.length() > self.friction / 5.0:
            direction.normalize()
            return direction * self.friction * 70
        else:
            return direction * self.friction * 70
