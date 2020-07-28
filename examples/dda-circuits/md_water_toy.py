#!/usr/bin/env python3

# This file comes from commit f0eab6b08fc2d6e7837d56d33a9837cb009a5aab
# from the F&E repository /experimente/Water-Toy and serves as a standlone
# example for an advanced use of PyDDA.

"""
PyDDA file for defining the circuit for the molecular dynamics
water model.

This file compiles a "low level" DDA circuit from a linear
algebra/vector level Newtonian physics description. This is why
numpy is required.

You also need PyDDA installed. For a brief guide, see
http://ai.svenk.org/dirhtml/installation/
"""

from numpy import arange, ones, ndindex, array, pi, zeros, sin, cos, sqrt
from dda import Symbol, dda_symbols, export

# numbers of iterations and time step size
iterations = 90000
dt = 0.0005

nParticles  = 3
nDim        = 2

N, D = arange(nParticles), arange(nDim)

NN = (nParticles, nParticles)
DN = (nDim, nParticles)
DNN = (nDim, nParticles, nParticles)

G = 1 # coupling constant (say Newton's constant)
m = ones(nParticles) # masses of particles

# initial data constants
scaling = 1.  # coordinate scaling from °A
dOH = scaling * 0.9572 # °A: Distance O-H 
angleHH = 104.52 * 2*pi/360; # opening angle at O in radiant
angleOH = pi/2 - angleHH/2;  # opening angle at a H

# ODE system constants
mlB = dOH
qO = -0.834 # e
qH = +0.417 # e
mO = 16. # u
mH = 1.  # u
epsilon_0 = 4*pi # jup
kB = 1.

name = [ "O", "H1", "H2" ] # for bookkeeping
q = [ qO, qH, qH ]
m = [ mO, mH, mH ]

# Identifiers for symmetric and antisymmetric matrices
sym = lambda char,i,j: "%s_{%d%d}" % (char, i if i<j else j, j if i<j else i)
antisym = lambda char,i,j: ('-' if j>i else '') + sym(char,i,j)

# naming follows Latex/PDF
r   = array([ Symbol(antisym(f"r^{d}",i,j)) for d,i,j in ndindex(DNN) ]).reshape(DNN)
s   = array([ Symbol(sym(f"s^{d}",i,j))     for d,i,j in ndindex(DNN) ]).reshape(DNN)
t   = array([ Symbol(sym("t",i,j))          for   i,j in ndindex( NN) ]).reshape( NN)
rm1 = array([ Symbol(sym("r^{-1}",i,j))     for   i,j in ndindex( NN) ]).reshape( NN)
rm3 = array([ Symbol(sym("r^{-3}",i,j))     for   i,j in ndindex( NN) ]).reshape( NN) # for better debugging
F   = array([ Symbol(antisym(f"F^{d}",i,j)) for d,i,j in ndindex(DNN) ]).reshape(DNN)
C   = array([ Symbol(sym("C",i,j))          for   i,j in ndindex( NN) ]).reshape( NN)
B   = array([ Symbol(sym("B",i,j))          for   i,j in ndindex( NN) ]).reshape( NN)
mV  = array([ Symbol(f"-V^{d}_{i}")         for d,i   in ndindex(DN ) ]).reshape(DN )
R   = array([ Symbol( f"R^{d}_{i}")         for d,i   in ndindex(DN ) ]).reshape(DN )
mR  = array([ Symbol(f"-R^{d}_{i}")         for d,i   in ndindex(DN ) ]).reshape(DN )

# initial positions and velocities
R0, V0 = zeros(DN), zeros(DN)
R_offset = array([0, 0])
pert_dist, pert_angle = 0, 0
rest_distance = 0.92617 # minimum of potential, determined numerically
idist = rest_distance*(1+pert_dist)
ia = angleOH*(1+pert_angle)
R0[:, 0] = 0
R0[:, 1] = idist*array([ -sin(angleOH/2), -cos(angleOH/2) ])
R0[:, 2] = idist*array([ +sin(angleOH/2), -cos(angleOH/2) ])


# Overall length scaling for maximum distance from [-1,-1] to [+1,+1]
# which is just sqrt(2), so 1./sqrt(2) ~ 0.707 is fine:
length_scaling = 1./sqrt(2)  * 0.5
R0 *= length_scaling
mlB *= length_scaling
epsilon_0 /= length_scaling**2

## Print initial state for latex:
#for (d,i),r in ndenumerate(R0): print(f"r^{d}_{i} &= {r:.5f} \\\\")

#R0 *= scaling
#V0 = 0

# sum, sqrt, abs... are Symbols from here on.
from dda.computing_elements import *

dt = 0.001

# This scaling is for treating the 1/sqrt(r) terms and all derived ones.
# The aim is to reduce the forces by factor oneOverScale**3 = 125
# and to compensate this in the analog integrators by a smaller integration speed
alpha = 5.

optimize_integrals = False

for d,i in ndindex(DN):
    for j in N:
        if j >= i: continue
        state[ r[d,i,j] ] = sum(R[d,i], neg(R[d,j]))
        state[ s[d,i,j] ] = mult(r[d,i,j], r[d,i,j])
        state[ t[  i,j] ] = neg(sum(*[s[k,i,j] for k in D]))
        state[ rm1[i,j] ] = div(1./alpha, sqrt(t[i,j])) # TODO use function generation
        
        rm3 = mult(mult(rm1[i,j], rm1[i,j]), rm1[i,j]) # TODO use function generation
        C_prefactor = q[i]*q[j]/epsilon_0
        state[ C[i,j] ] = rm3 # skaliert mit 1./125 # eigentlich C_pre*rm3

        if i==0 or j==0:
            # single molecule, bond stretching is computed whenever the O (idx 0) is involved.
            #overRwhat = mult(rm1[i,j],rm1[i,j])
            B_summands = (neg(1/alpha**3), mult(mlB/alpha**2, rm1[i,j]))
            forces = mult(sum(*B_summands, mult(C_prefactor,C[i,j])), r[d,i,j])
        else:
            forces = mult(mult(C_prefactor,C[i,j]), neg(r[d,i,j]))
        
        state[ F[d,i,j] ] = forces # skaliert mit 1./125


        # Generate the antisymmetric elements
        if (not optimize_integrals) or (i != 0 and j != 0): # optimization, don't compute unneccessary elements!
            state[ F[d,j,i] ] = neg(F[d,i,j])

        #state[ r[d,j,i] ] = neg(r[d,i,j]) # terms not needed!

    state[ mV[d,i] ] = int(*[mult(alpha**3 / m[i], F[d,i,j]) for j in N if j != i], dt, V0[d,i])
    state[  R[d,i] ] = int(mV[d,i], dt, R0[d,i])

# Well, as another optimization, move the double negation away in mV:
if optimize_integrals:
    m0 = alpha**3 / m[0]
    state[mV[0,0]] = int(neg(sum(mult(m0, F[0,1,0]), mult(m0, F[0,2,0]))), dt, V0[0,0])
    state[mV[1,0]] = int(neg(sum(mult(m0, F[1,1,0]), mult(m0, F[1,2,0]))), dt, V0[1,0])


# This is our convention for DDA/C/Python-compatible symbol names
latex2c = lambda name: name.replace("-","m").replace("{","").replace("}","").replace("^","")
cstate = state.map_heads(latex2c)

# options for passing at C runtime
evolved_fields = [ latex2c(str(symb)) for symb in (list(R.flatten())+list(mV.flatten())) ]
c_runtime_args = { "max_iterations": iterations, "modulo_write": 300, "debug": 1 }

c_code = cstate.export(to="C")
latex_code = cstate.export(to="latex", chunk_n=4)

#with open("md_water.cc", "w") as fh: print(c_code, file=fh)

## Starting from here, plotting and postpcoressing of simulation takes over
## (from plot_md_water.py)


from os import system
from numpy import * 
from numpy import abs, sum # especially overwrites abs, sum, ... again
from matplotlib.pyplot import *
from dda.cpp_exporter import compile, run

# choose what to plot
fields = evolved_fields
#fields = [] # by default, all

compile(c_code, "md_water.cc")
data = run(fields_to_export=fields, return_ndarray=True, arguments=c_runtime_args)

all_columns = data.dtype.names

# shape: nDim x nParticles 
nParticles  = 3
nDim        = 2
DN = (nDim, nParticles)
name = [ "O", "H1", "H2" ] # for bookkeeping
R   = array([ (f"R{d}_{i}"   ) for d,i   in ndindex(DN ) ]).reshape(DN )
mR  = array([ (f"mR{d}_{i}"  ) for d,i   in ndindex(DN ) ]).reshape(DN )

subplot(121)

def rename(rec):
    rec.dtype.names = ("x","y")
    return rec

def line(a, b, *args, **kwargs):
    plot([a[0], b[0]], [a[1], b[1]], *args, **kwargs)

# one molecule:

O  = rename(data[[R[0, 0], R[1, 0]]])
H0 = rename(data[[R[0, 1], R[1, 1]]])
H1 = rename(data[[R[0, 2], R[1, 2]]])

plot(H0["x"], H0["y"], "-")
plot(H1["x"], H1["y"], "-")
plot(O["x"], O["y"], "-")

# plot triangle
line(H0[0], O[0], "--", color="gray")
line(H1[0], O[0], "--", color="gray")

line(H0[-1], O[-1], "--", color="black")
line(H1[-1], O[-1], "--", color="black")

# plot ... box

gca().add_patch(matplotlib.patches.Rectangle((-1,-1), 2, 2, color='lightgrey'))

xlabel("x")
ylabel("y")
#gca().set_aspect("equal")

O =np.array(O.tolist())
H0=np.array(H0.tolist())
H1=np.array(H1.tolist())

# center of mass computation
mO, mH = 16, 1
R_COM = (O*mO + H0*mH + H1*mH) / (mO + 2*mH)

plot(R_COM[:,0], R_COM[:,1], "-.", lw=3, color="purple", label="COM")

#xlim(-1,1)
#ylim(-1,1)

problematic_columns = {n for n in all_columns if any(abs(data[n]) > 1)}

for col in sorted(problematic_columns):
    print(f"Column out of range: %-8s  (min=%+.4f, max=%+.4f)" % (col, min(data[col]), max(data[col])))

subplot(122)
for col in all_columns: #R.flatten(): #all_columns:
    plot(data[col], "-", label=col, alpha=(0.5 if not col in problematic_columns else 1))
    
l = legend(ncol=8)
if hasattr(l, "set_draggable"): l.set_draggable(True)

xlabel("coordinate time")
ylabel("evolution quantity")

ylim(-1.5,1.5)
subplot(121)

savefig("md_water_toy.png")
savefig("md_water_toy.pdf")
 
print("Figures successfully written to md_water_toy.{png,pdf}")
