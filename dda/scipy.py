#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the DDA module of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# ANABRID_END_LICENSE
#
 
"""
The scipy module allows in-python evaluation of DDA systems
as well as their solution with standard scipy methods
(basically LAPACK and friends).
"""

from . import State, Symbol, symbols, clean
import math, functools, operator, copy # builtins
import numpy as np # externals
from builtins import sum # just to be explicit, sum is not overwritten
from collections import namedtuple

is_number = lambda obj: isinstance(obj, float) or isinstance(obj, int)
first = lambda iterable: next(x for x in iterable if x)  # first element of iterator/list

dda2python = {
    "const": lambda x: x,
    "neg":   lambda x: -x,
    "div":   lambda x,y: x/y,
    "Int":   lambda *x: - sum(x), # mangled integral
    "sum":   lambda *x: - sum(x),
    "mult":  lambda x,y: x*y,
    "sqrt":  lambda x: math.sqrt(x),
    "abs":   lambda x: math.abs(x),
    "exp":   lambda x: math.exp(x),
    "floor": lambda x: math.floor(x),
}

def evaluate_values(smbl, values):
    "Evaluate a symbol within the context of an already evaluated values dictionary given."
    if isinstance(smbl, float) or isinstance(smbl, int):
        return smbl # usable node
    if not isinstance(smbl, Symbol): raise TypeError(f"Expecting symbol, got {smbl}")
    if smbl.is_variable():
        return values[smbl.head] # can raise KeyError if variable not found.
    else: # symbl.is_term()
        if smbl.head in dda2python:
            return dda2python[smbl.head](*(evaluate_values(t, values) for t in smbl.tail))
        else:
            raise ValueError(f"DDA Symbol {smbl.head} in expression {smbl} not (yet) implemented.")

class to_scipy:
    """
    Basically provides a function ``f(dqdt)`` where dqdt are the evolution
    quantities.
    
    # FIXME: 
    >>> from dda.computing_elements import neg,int,mult
    >>> dda_state = State({"x": neg(int(neg(int(neg(mult(1, Symbol("x")), 0.005, 1)), 0.005, 0))) })
    >>> clean(dda_state, target="python").name_computing_elements().variable_ordering()
    # Should contain evolved variables, but does not!
    #>>> py_state = to_scipy(dda_state)
    """
    
    def __init__(self, state):
        state = clean(state, target="python").name_computing_elements()
        self.vars = state.variable_ordering()
        
        if not self.vars.evolved:
            raise ValueError("Nothing to evolve. Lacking some dda.int(f,dt,ic) integrators")
        
        # by intention, dt and initial condition are ignored

        # Extract int(..., timestep, initial_data) and mark integrator as visited (mangled)
        timesteps = {}
        initial_data = {}
        def map_and_treat_integrals(var):
            if not var in self.vars.evolved: return state[var]
            tail = state[var].tail
            if not len(tail) >= 3: raise ValueError("int(...) requires at least int(value, dt, ic)")
            timesteps[var] = self.evaluate_const(tail[-2])
            initial_data[var] = self.evaluate_const(tail[-1])
            return Symbol("Int", *tail[0:len(tail)-2])
        self.state = State({ var: map_and_treat_integrals(var) for var in state })
        
        # Scipy needs numpy arrays for further processing
        timesteps = np.array([timesteps[k] for k in self.vars.evolved])
        self.y0 = np.array([initial_data[k] for k in self.vars.evolved])

        # The Scipy integrate methods cannot treat different timestep sizes.
        self.dt = timesteps[0]
        if not np.all(timesteps == self.dt):
            raise ValueError(f"Scipy requires all timesteps to be the same, however dt_({self.vars.evolved}) = {timesteps}")
        
        # set beginning values for each call of f(y). This dictionary can be
        # mutated over repeated calls, but if you want to go sure, make a 
        # deep copy at every call.
        self.evaluation_default_values = { k: np.nan for k in state.keys() }
        for var in self.vars.explicit_constants:
            self.evaluation_default_values[var] = state[var].tail[0]
            
        self.debug = False
    
    def evaluate_const(self, var):
        """
        Translate const(foo) by stripping foo or some bar by looking up if it is an explicit constant.
        Dynamical variables are not allowed here. This is somewhat similar but different to
        cpp_exporter:lookup_const(var).
        """
        if isinstance(var,Symbol):
            if var.head == "const":
                var = var.tail[0] # continue
            elif var.is_variable():
                if not var.head in self.vars.explicit_constants:
                    raise ValueError(f"Only constants allowed in this context. {var} however refers to {var.head}.")
                return self.evaluate_const(state[var.head])
            else: # remaining case: var.is_term()
                raise ValueError(f"Was expecting const(foo) or so, but got term {var}.")
        if not is_number(var): raise ValueError(f"Got a weird {type(var)} in a constant context: {var}")
        return var
    

    def f(self, y):
        """
        The ODE right hand side in ``dy / dt = f(y)``. ``y`` is a numpy vector,
        and ``f(y)`` returns a similarly sized vector:
        
        >>> ode = to_scipy(State({ x: int(x,0,0) }))
        >>> y1 = ode.y0 + ode.f(ode.y0) * ode.dt   # perform some euler integration step
        [ will give some vector ]
        
        Usually, you want to pass this function to some scipy integrator. See
        also :meth:`ft`.
        """
        values = self.evaluation_default_values
        if self.debug: values = copy.deepcopy(values)
        for i,var in enumerate(self.vars.evolved):
            values[var] = y[i]  # scatter
        # TODO: md3.py doesnt work when vars.aux.unneeded is skipped, because
        #       Int(...) depends on such an unneeded guy. This is wrong.
        for var in self.vars.aux.sorted + self.vars.aux.cyclic + list(self.vars.aux.unneeded):
            values[var] = evaluate_values(self.state[var], values)
            if np.isnan(values[var]):
                from pdb import set_trace as bp
                bp()
        dqdt = [ evaluate_values(self.state[var], values) for var in self.vars.evolved ]
        if np.any(np.isnan(np.array(dqdt))):
            from pdb import set_trace as bp
            bp()
        return np.array(dqdt)

    def ft(self, t, y):
        """Syntactic sugar for scipy integrators who want a signature ``f(t,y)``. Will
        just call ``f(y)`` instead."""
        return self.f(y)

    def solve(self, tfinal, **kwargs):
        """
        Usage is then like:
        
        >>> system = State({ "x": int(...), "y": ... })
        >>> ode = system.export(to="scipy")
        >>> sol = ode.solve(tfinal=100)
        >>> for i,fieldname in enumerate(ode.vars.evolved):
                plot(sol.t, sol.y[i], label=fieldname)
        >>> legend(); show()
        """
        from scipy.integrate import solve_ivp
        return solve_ivp(self.ft, [0, tfinal], self.y0, **kwargs)

