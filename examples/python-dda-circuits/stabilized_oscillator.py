#!/usr/bin/env python3

#
# Oscillator limiter test:
#
# This circuit tests the limiting or "self-healing" of an oscillator
# ODE y'' = -y which is contamined with a linear term which should
# result in an exponential answer. Thanks to the limiter, this does
# not happen.
#
# The dead_lower/dead_upper combination models what is typically
# archived with two diodes on an electric level.
#
# This works like a charm!
#


import numpy as np
from dda import State, symbols, dda

ddy, y, mdy, my, lu, ld, y2, y2ohne = symbols("ddy, y, mdy, my, lu, ld, y2, y2ohne")
s = State()
dt = 0.1
t_final = 50

err = 0.5

ic_y   = 1.0
ic_mdy = 0.0

s[my]  = dda.neg(y)
s[y]   = dda.int(lu, mdy, ld, dda.mult(err,my), dt, ic_y)
s[mdy] = dda.int(my, dt, ic_mdy) # my = ddy

s[lu]  = dda.mult(1, dda.dead_upper(y, +1))
s[ld]  = dda.mult(1, dda.dead_lower(y, -1))

# count zero crossings:
ys, yd, yi = symbols("ys, yd, yi")
s[ys]  = dda.sign(y)
s[yd]  = dda.max(0, dda.min(1, dda.diff(ys, dt, 0)))
s[yi]  = dda.neg(dda.int(dda.mult(yd,1/dt), dt, 0))

# Frequenzverdopplung ohne linearem Offset
s[y2]  = dda.mult(y,y)
s[y2ohne] = dda.diff(y2, dt, 0)

data = s.export(to="CppSolver").run(max_iterations= t_final / dt, rk_order=1).as_recarray()
xtime = np.arange(0, t_final, dt)
assert len(data) == len(xtime)

from matplotlib.pylab import *
ion(); clf()

#cols = data.dtype.names
cols = "y y2 y2ohne".split()

for n in cols: plot(xtime, data[n], "o-", label=n)
legend()
