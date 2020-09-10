#!/usr/bin/env python3
#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the test suite of the PyAnalog toolkit.
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
# ANABRID_END_LICENSE
#

"""
This test problem for DDA solves the simple differential
equation

   y'(t) = alpha * y(t)
   
with a real-valued alpha. The analytic solution is of course

   y(t) = exp(alpha*t) * y_0
   
with the initial value y(t=0) = y_0. We do not look into
complex alpha's at this point.
"""

from dda.computing_elements import symbols, state
from dda.cpp_exporter import compile, run
# postprocessing:
import numpy as np

# numbers of iterations and time step size
t_initial, t_final = 0.0, 3.0
dt = 0.05
N = t_final / dt
assert N == int(N)
N = int(N)  # np.linspace requires an integer

def setup_state(alpha=-1., y0=+1.):
    # parameters of problem: slope and initial value

    # define variables and local shorthands
    y = symbols("y")
    integrate, mult, neg = symbols("int, mult, neg")
    state["y"] = integrate(mult(alpha, neg(y)), dt, -y0)
    
    return state

def run_simulation():
    c_code = setup_state().export(to="C++")
    compile(c_code)
    return run(arguments={
        'max_iterations': N,
        'modulo_write': 1,
        "always_compute_aux_before_printing": 1,
        "write_initial_conditions": 0,
    })

def test_run_simulation():
    output = run_simulation()
    ysim = output["y"]

    time = np.arange(t_initial, t_final, dt) + dt
    yanalytic = -np.exp(-time)
    
    relative_tolerance = 1e-1 # which is pretty bad, actually
    
    assert np.allclose(ysim, yanalytic, rtol=relative_tolerance)
    return time, ysim

# You can also plot the results easily:

# from pylab import *
# ion()
# time, ysim = test_run_simulation()
#
# plot(time, ysim, "o")
# plot(time, -exp(-time))

