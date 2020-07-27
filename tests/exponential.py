#!/usr/bin/env python3

"""
This test problem for DDA solves the simple differential
equation

   y'(t) = alpha * y(t)
   
with a real-valued alpha. The analytic solution is of course

   y(t) = exp(alpha*t) * y_0
   
with the initial value y(t=0) = y_0. We do not look into
complex alpha's at this point.
"""

from pydda.computing_elements import *
from pydda.cpp_exporter import compile, run
from numpy import genfromtxt

# numbers of iterations and time step size
N = 5000
dt = const(0.05)

# parameters of problem:
alpha = -1.
y0 = +1.

# define variables and local shorthands
y = symbols("y")
state["y"] = int(mult(alpha, neg(y)), dt, neg(y0))

c_code = state.export(to="C++")
compile(c_code)
output = run()


# TODO FIXME generated code is again wrong here:
"""
      // 3. State variable changes (dqdt), finally
     _dqdt.y = Int(_aux.mult_1);
     // 4. Unneeded auxilliary variables (maybe postprocessing, etc.)
     _aux.mult_1 = mult(-1.0, neg(_state.y));
"""
