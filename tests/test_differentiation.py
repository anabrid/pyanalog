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
# For Germany, additional rules exist. Please consult /LICENSE.DE
# for further agreements.
# ANABRID_END_LICENSE
#

"""
This test tests the differentiation capabilities by DDA.

Differentiation stands next to integration in this time
evolution code.

This text is rather lax and does NOT test the exact
validity of the integration, cf. test_exponential_solution.py.
"""

from dda import State, symbols, dda
import dda.cpp_exporter as cpp
# postprocessing:
import numpy as np

diff_in, diff_out, int_diff, int_out  = symbols("diff_in, diff_out, int_diff, int_out")
dt = 0.01
t_final = 5

alpha  = 0.9
ic     = 0


def run(s):
    data = s.export(to="CppSolver").run(max_iterations=t_final / dt, rk_order=4).as_recarray()
    xtime = np.arange(0, t_final, dt)
    assert len(data) == len(xtime)
    
    return xtime, data

def plot_simulation(time, data):
    # only for interactive testing:
    import matplotlib.pylab as plt
    plt.ion(); plt.clf()

    #cols = data.dtype.names
    cols = "diff_in diff_out int_diff".split()

    for n in cols: plt.plot(time, data[n], label=n)
    plt.legend()


def setup_constant():
    s = State()
    #s[diff_in]   = dda.const(1)  # TODO: Such an expression does no more work!!
    s[diff_out]  = dda.diff(1, dt, 0)
    s[int_diff]  = dda.int(diff_out, dt, 1) # integrates over 0, should do it.
    return s

def setup_polynomial():
    s = State()
    s[diff_in]        = dda.mult(2,dda.int(dda.int(1, dt, 0), dt, 0))   # diff_in = 2*int(1) = t^2
    s[diff_out]       = dda.neg(dda.diff(diff_in, dt, 0))  # 2*t
    s[int_diff]       = dda.neg(dda.int(diff_out, dt, 0)) # t^2 but with increasing deviations due to dt
    return s

def test_polynomial_diff():
    t,d = run(setup_polynomial())
    assert np.allclose(t**2, d["diff_in"],  atol=0.1)
    assert np.allclose(2*t,  d["diff_out"], atol=0.1)

def setup_sinusodial():
    # sinusodial test signal:
    s = State()
    y, my, mdy = symbols("y, my, mdy")
    s[my]  = dda.neg(y)
    s[y]   = dda.int(mdy, dt, 0)
    s[mdy] = dda.int(my, dt, 1)
    s[diff_in]     = y # diff_in = cos(t)
    s[diff_out]    = dda.neg(dda.diff(diff_in, dt, 0)) #  0 = sin(0)
    s[int_out]     = dda.neg(dda.int(diff_in, dt, +1)) # -1 = cos(0), but negated
    return s

def test_sinusodial_diff():
    t,d = run(setup_sinusodial())
    # note the bad tolerances...
    assert np.allclose(-np.sin(t), d["diff_in"], atol=1e-1)
    # Test except the first point, which can be wrong if the initial conditions for dt
    # were wrong.
    assert np.allclose( -np.cos(t[1:]), d["diff_out"][1:], atol=1e-1)
    pass


# interactive testing goes like:
"""
from pylab import *
s = setup_polynomial()
t,d = run(s)
plot_simulation(t,d)
"""
