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
N-body with an inverse square law force (Coulumb/Newton like)
"""

from os import system
from numpy import *

# numbers of iterations and time step size
iterations = 10000
dt = 0.0005

nParticles  = 2
nDim        = 1
shape = (nParticles, nDim)

N = list(arange(nParticles))
D = list(arange(nDim))

G = 1 # coupling constant (say Newton's constant)
m = ones(nParticles) # masses of particles

# initial positions and velocities
x0 = array([[+1], [-1]]) #zeros(shape)
v0 = zeros(shape)


dda_content = []
say = dda_content.append

say(f"dt = const({dt})")

say("")

for i, d in ndindex(shape):
    say(f"xinitial_{i}_{d} = const({x0[i,d]})")
    say(f"vinitial_{i}_{d} = const({v0[i,d]})")

say("")

for i in N:
    # coupling constant times mass of {i}.th particle:
    say(f"Gm_{i} = const({G * m[i]})")

for i, j in ndindex((nParticles, nParticles)):
    if i == j: continue # avoid pitfalls
    say(f"dist_{i}_{j} = sqrt(sum(" +  ",".join([ f"x_{i}_{k}, mx_{j}_{k}" for k in D ]) + "))");
    say(f"distCubed_{i}_{j} = mult(dist_{i}_{j},dist_{i}_{j},dist_{i}_{j})")
    for d  in D:
        # This is \vec{x}_{ij} = \frac{\vec x_i - \vec x_j}_{|x_ij|^3}
        say(f"xhat_{i}_{j}_{d} = div(sum(x_{i}_{d}, mx_{j}_{d}), distCubed_{i}_{j})")
say("")

for i, d in ndindex(shape):
    say(f"mv_{i}_{d} = mult(Gm_{i}, int(" + ", ".join([f"xhat_{i}_{j}_{d}" for j in N if i != j])
                                 +f", dt, xinitial_{i}_{d}))")
    say(f"x_{i}_{d} = int(mv_{i}_{d}, dt, vinitial_{i}_{d})")
    say(f"mx_{i}_{d} = neg(x_{i}_{d})")
    
say("")

dda_content = "\n".join(dda_content)
dda_fname = "N-body.dda"
with open(dda_fname, "w") as dda_fhandle:
    print(dda_content, file=dda_fhandle)

dump_list = [ f"x_{i}_{d}" for i, d in ndindex(shape) ]

def run_with_old_dda2c_code(dda_fname):
    def simulate(circuit_file, iterations, modulus, dump_list):
        compiler, scratch_file, gnuplot_file = './dda2c.pl', 'scratch.dat', 'gnuplot.dat'
        variables = " ".join(dump_list)
        output_file = circuit_file.replace(".","_") + ".c"
        
        cflags = "-Wall -g"

        if system(f"{compiler} {circuit_file} {iterations} {modulus} {variables}"): raise ValueError("Could no generate C source!");
        if system(f"cc {cflags} {output_file} -lm"):   raise ValueError("Could not compile C source!")
        if system(f"./a.out > {scratch_file}"): raise ValueError("Could not execute simulation!");

        return genfromtxt(scratch_file, names=dump_list)

    dda_fhandle.close()
    result_data = simulate(dda_fname, iterations=iterations, modulus=1, dump_list=dump_list)
    return result_data

def run_with_new_pydda(dda_content):
    from dda import read_traditional_dda
    state = read_traditional_dda(dda_content)
    result_data = state.export(to="CppSolver").run().as_ndarray()
    return result_data

run_with_new_pydda(dda_content)
