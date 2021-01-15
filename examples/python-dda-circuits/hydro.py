#!/usr/bin/env python3

"""
Classical newtonian Hydrodynamics in a flux-conservative
formulation with an ideal fluid equation. This is kind of
the most basic kind of fluid dynamics one can imagine.
Written out as DDA equations and discretized in time with
n'th order finite difference, while time integration is
subject to the analog computer time integrator. n can be
chosen freely.

Numerically, such a scheme is used with 4th or 6th order FD
also in practice.
"""

from numpy import arange, ones, ndindex, array
from dda import Symbol, State, dda_functions
from dda.computing_elements import div, sum, int, sqrt, mult, neg


nDim = 1
rDim = range(nDim)

nFD = 2 # order of finite difference / spatial convergence
dx = [ Symbol(f"deltax{j}") for j in rDim ]

# the conserved state vector Q
#  Q = ( D   ) =  ( rho                   )
#      ( S_j )    ( rho * v_i             )
#      ( E   )    ( rho/(2*v^2) + epsilon )
Q = [Symbol("D"), *(Symbol(f"S{j}") for j in rDim), Symbol("E") ]
D, *S, E = Q

# the primitive state vector V
V = [Symbol("rho"), *(Symbol(f"v{j}") for j in rDim), Symbol("eps") ]
rho, *v, eps = V

# Some helper symbols
symmetric = lambda char,i,j: "%s%d%d" % (char, i if i<j else j, j if i<j else i)
vv = [[Symbol(symmetric("v",i,j)) for i in rDim] for j in rDim] # vv[i][j] = v[i]*v[j]
v2 = Symbol("v2") # v2 = norm(v)**2 = v0**2 + ... + vN**2
p = Symbol("p") # pressure (equation of state)

# for neat indexing Q[foo], we define the index positions
iD, iS, iE = 0, 1 + array(list(rDim)), -1

# Symbolic spatial partial derivative, expected usage:
# partial(expression, i)  with i the spatial dimension
partial = Symbol("Partial")

state = State()

dt = 0.1 # meaningless timestep size
Q0 = [ 0., *(0 for j in rDim), 0 ] # initial conditions

# analytical recovery of primitives and other auxilliaries
state[rho] = state[D]  # actually never really needed
for i in rDim:
    state[v[i]] = div(state[S[i]], state[rho])
    for j in rDim:
        state[vv[i][j]] = mult(v[i], v[j])
state[v2] = neg(sum(*(vv[j][j] for j in rDim)))
state[eps] = neg(sum(E, neg(div(D, mult(2, v2)))))

# Equation of state
Gamma = 2 # polytropic constant in ideal fluid equation of state
state[p] = mult(rho, mult(eps, Gamma-1))

# actual conserved flux system

# D = -int_t partial_i D^i = - partial_i (rho * v^i)
state[ D ] = int(*( partial(S[i], i) for i in rDim), dt, Q0[iD])

for i in rDim:
    integrands = [ partial(mult(S[i],v[j]),i) for j in rDim ]
    if i == j: integrands.append( partial(neg(p),i) )
    state[ S[i] ] = int(*integrands, dt, Q0[iS[i]])

state[ E ] = int(*(partial(mult(v[i],neg(sum(E, p))),i) for i in rDim), dt, Q0[iE])

# Variant 1: Evaluate the partials to neighbouring elements in
# order to plot one macro cell. The idea is to translate alike
#
#  partial(sum(a,mult(b,c)), i) -> (sum(a_p1,mult(b_p1,c_p1)) - sum(a_m1,mult(b_m1,c_m1))) / dx
#
# i.e. to keep the neighbour cells symbolic instead of introducing
# a large number of symbolic evaluating points.
#  

# Naming of neighbour variables.
neighbour_name = lambda name, pos: f"{name}_{'p' if pos > 0 else 'm'}{abs(pos)}"
assert nDim == 1, "neighbour_name is currently only implemented for 1D to avoid naming clutter."

def partial_to_rim(smbl):
    if smbl.head != partial.head: return smbl.map_tails(partial_to_rim)
    body, direction = smbl.tail
    neighbour = lambda pos: body.map_variables(lambda name: neighbour_name(name, pos))
    
    assert nFD == 2, "only nFD=2 implemented so far"
    return div(sum(neighbour(-1), neg(neighbour(+1)), dx[direction]))
rimstate = state.map_tails(partial_to_rim)

"""
def partial(smbl, i):
    "Compute the partial derivative of smbl in direction i \in NN_0"
    assert nFD == 2, "only nFD=2 implemented so far"
    
    minus = smbl.map_variables()
    
    plus
"""
