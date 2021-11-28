#!/usr/bin/env python3
#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the examples of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# Commercial License Usage
# Licensees holding valid commercial anabrid licenses may use this file in
# accordance with the commercial license agreement provided with the
# Software or, alternatively, in accordance with the terms contained in
# a written agreement between you and Anabrid GmbH. For licensing terms
# and conditions see https://www.anabrid.com/licensing. For further
# information use the contact form at https://www.anabrid.com/contact.
# 
# GNU General Public License Usage
# Alternatively, this file may be used under the terms of the GNU 
# General Public License version 3 as published by the Free Software
# Foundation and appearing in the file LICENSE.GPL3 included in the
# packaging of this file. Please review the following information to
# ensure the GNU General Public License version 3 requirements
# will be met: https://www.gnu.org/licenses/gpl-3.0.html.
# For Germany, additional rules exist. Please consult /LICENSE.DE
# for further agreements.
# ANABRID_END_LICENSE
#

"""
Roche-Attraktor
"""

from dda import symbols, State
from dda.computing_elements import int, mult, neg
from numpy import *

# numbers of iterations and time step size
iterations = 100_000_000
dt = 0.0005

x,y,z = symbols("x,y,z")
a = [ NaN, 5, 2, 0.5, 1, 4, 1 ]
x0, y0, z0 = -5, 0, 5

state = State()

state[x] = int(mult(a[1], x), neg(mult(mult(a[2],y),z)), dt, x0)
state[y] = int(neg(mult(a[3],y)), mult(mult(a[4],x),z),  dt, y0)
state[z] = int(mult(a[5],z), neg(mult(mult(a[6],x),y)),  dt, z0)

if 0:
    # solve with naive explicit RK
    results = state.export(to="CppSolver").run(
        max_iterations=iterations,
        modulo_write=300,
        binary=True
    ).as_recarray()
else:
    # solve with scipy instead
    py_state = state.export("scipy")
    sol = py_state.solve(1000, dense_output=True)
    results = { field: sol.y[i] for i, field in  enumerate(py_state.vars.evolved) }

from pylab import *
ion()
plot(results["x"])
plot(results["y"])
plot(results["z"])

figure()
plot(results["x"], results["y"])

# oder in 3D: 

import matplotlib.pyplot as plt
fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.plot(results["x"], results["y"], results["z"])

