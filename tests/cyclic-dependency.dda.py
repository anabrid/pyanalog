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


#
# N-body with an inverse square law force (Coulumb/Newton like)
#
# -> TODO: PyDDA doesn't generate correct C++ code yet for this problem.
#
# for dt in 1 0.1 0.01 0.001 0.0001; do sed -i "s/^dt =.*$/dt = const($dt)/" 1d_exp.dda ; T=$(bc -l <<< "5* 1./$dt"); echo "dt=$dt T=$T"; ./simulate.pl 1d_exp.dda $T 1 minus_dy y; cp gnuplot.pdf 1d_exp-dt$dt.pdf; done;

from pydda.computing_elements import *

# numbers of iterations and time step size
N = 10000
dt = const(0.0005)

t = int(1, dt)

# exp(-t)
y0  = const(-1)
minus_dy0 = const(-1)

# define variables and local shorthands
y, minus_dy = state.symbols("y, minus_dy")

# This is a cyclic dependency:
state.minus_dy = int(y, dt, minus_dy0)
state.y        = int(minus_dy, dt, y0)

# Something else

state.foo = mult(y, minus_dy)
state.bar = mult(minus_dy, sum(y,y))

c_code = state.export(to="C")
print(c_code) # simulate etc.
