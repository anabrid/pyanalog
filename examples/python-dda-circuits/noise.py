#!/usr/bin/env python3

#
# Random number by DDA:
#
# We can use the noise function to get randoms between [-1,1].
# Integration over such noise should give the average, i.e. 0.
#


import numpy as np
from dda import State, Symbol, dda

s = State()
dt = 0.01
t_final = 5

s["a"] = dda.noise(0)
s["i"] = dda.int(Symbol("a"), dt, 0)


data = s.export(to="CppSolver").run(max_iterations= t_final / dt, rk_order=4).as_recarray()
xtime = np.arange(0, t_final, dt)
#assert len(data) == len(xtime)

from matplotlib.pylab import *
#ion(); clf()

#cols = data.dtype.names
cols = "a i".split()

for n in cols: plot(xtime, data[n], label=n)
legend()
show()
