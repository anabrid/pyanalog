#!/usr/bin/env python3

#
# Differentiation by integration:
#
# This circuit uses the "trick" from page 95ff / section 5.14 from
# Bernds ap2.pdf Book "Analog Computing II"
#


import numpy as np
from dda import State, symbols, dda

diff_in, diff_out, diff_loop  = symbols("diff_in, diff_out, diff_loop")
s = State()
dt = 0.05
t_final = 10

alpha  = 0.9
ic     = 0

# test signal:
#s[diff_in]        = dda.int(dda.int(1, dt, 0), dt, 0)   # diff_in = t^2

# sinusodial test signal:
y, my, mdy = symbols("y, my, mdy")
s[my]  = dda.neg(y)
s[y]   = dda.int(mdy, dt, 0)
s[mdy] = dda.int(my, dt, 1)

s[diff_in]  = y # diff_in = cos(t)

s[diff_out]       = dda.neg(dda.sum(diff_in, diff_loop, dda.mult(alpha, diff_out)))
s[diff_loop]      = dda.int(diff_out, dt, ic)


data = s.export(to="CppSolver").run(max_iterations= t_final / dt, rk_order= 4).as_recarray()
xtime = np.arange(0, t_final, dt)
assert len(data) == len(xtime)

from matplotlib.pylab import *
ion(); clf()

#cols = data.dtype.names
cols = "diff_in diff_out".split()

for n in cols: plot(xtime, data[n], label=n)
legend()
 
