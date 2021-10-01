#!/usr/bin/env python3

from math import pi, log
from numpy import array
import numpy as np
from dda import State, Symbol, dda, symbols

s = State()
dt = 0.005
#t_final = 1000  # Note, the period length is = 2*pi = 6.28
t_final = 200
norm = 0.5 # amplitude of the oscillators
modulo_write = 10
xtime = np.arange(0, t_final, dt * modulo_write)
#reference_sinus = np.cos(xtime)
wavelength = 2*pi # natural wavelength of our oscillators

# stabilization = 1 turns on dead_upper/dead_lower
stabilization = 0

# initial conditions: Phase shifts
phase = 0 *2*pi
#phase = np.random.rand() *2*pi
#print("Gewürfelte Startphasen (rand*2*pi): ", phase)

ic_dy  = -np.sin(phase) * norm
ic_mdy = -np.cos(phase) * norm

# oscillator damping and amplification
D = 0
A = 0

# oscillator frqeuency variation
#FREQS = [ 0.95, 1.00, 1.05  ]
freqvarianz = 1.0

# oscillator gain variation
GAINS = [ 0.95, 1.00, 1.05 ]
N = len(GAINS)

ddavars = [ [Symbol(f"{x}{n}") for n in range(N)] for x in symbols("y, limu, limd, mdy, my") ]

for y, limu, limd, mdy, my, gain in zip(*ddavars, GAINS):
    s[y]     = dda.mult(gain, dda.int(dda.mult(freqvarianz, mdy), dda.mult(A, my), limu, limd, dt, ic_dy))
    s[limu]  = dda.mult(stabilization, dda.dead_upper(y,  norm))
    s[limd]  = dda.mult(stabilization, dda.dead_lower(y, -norm))
    s[mdy]   = dda.int(dda.mult(freqvarianz, my), dda.mult(D, mdy),  dt, ic_mdy)
    s[my]    = dda.sum(y)

runtime_args = {
    'max_iterations': t_final / dt,
    "rk_order": 3,
    "modulo_write": modulo_write,
    "modulo_progress": t_final / dt / 10,
}
fields_to_export = ["y0","y1","y2"]
solver = s.export(to="CppSolver",  constexpr_consts=False)

def single_run():
    global xtime
    data = solver.run(*fields_to_export, cleanup=False, binary=True, **runtime_args).as_recarray()
    if not len(data) == len(xtime):
        print(f"len(data) != len(time), thus fixing...")
        xtime = np.linspace(0, t_final, len(data))
    return xtime, data

from matplotlib.pylab import *
ion(); clf()

xtime, data = single_run()

plot(xtime / wavelength, data["y0"])
plot(xtime / wavelength, data["y1"])
plot(xtime / wavelength, data["y2"])
 
