#!/usr/bin/env python3

#
# Differentiation by DDA:
#
# This circuit uses the novel DDA differentiator.
#


import numpy as np
from dda import State, symbols, dda

diff_in, diff_out, diff_loop  = symbols("diff_in, diff_out, diff_loop")
s = State()
dt = 0.01
t_final = 5

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

s[diff_out] = dda.diff(diff_in, dt, 0)



from dda.cpp_exporter import compile, run
compile(s.export(to="C"))
data = run(arguments={'max_iterations': t_final / dt, "rk_order": 4} )# return_recarray=True)
xtime = np.arange(0, t_final, dt)
assert len(data) == len(xtime)

from matplotlib.pylab import *
ion(); clf()

#cols = data.dtype.names
cols = "diff_in diff_out".split()

for n in cols: plot(xtime, data[n], label=n)
legend()
 
