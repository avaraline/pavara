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
        x += dx * dt
        v += dv * dt

        dx = v
        dv = self.acceleration(x, v, dt)
        return dx, dv

    def integrate(self, x, v, dt):
        dxa, dva = self.evaluate(x, v, 0.0, 0, 0)
        dxb, dvb = self.evaluate(x, v, dt*0.5, dxa, dva)
        dxc, dvc = self.evaluate(x, v, dt*0.5, dxb, dvb)
        dxd, dvd = self.evaluate(x, v, dt, dxc, dvc)

        dxdt = 1.0/6.0 * (dxa + 2.0*(dxb + dxc) + dxd)
        dvdt = 1.0/6.0 * (dva + 2.0*(dvb + dvc) + dvd)
        x += dxdt * dt
        v += dvdt * dt
        return x, v
