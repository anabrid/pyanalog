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
    #"int":   lambda *x: - sympy.Integral(sympy.Add(*x), t), # special meaning
    "Int":   lambda *x: - sum(x), # mangled integral
    "sum":   lambda *x: - sum(x),
    "mult":  lambda x,y: x*y,
    "sqrt":  lambda x: math.sqrt(x),
    "abs":   lambda x: math.abs(x),
    "exp":   lambda x: math.exp(x),
    "floor": lambda x: math.floor(x),
}

def to_scipy(state):
    """
    Returns a function ``f(dqdt)`` where dqdt are the evolution
    quantities (obtainable with :meth:`evolution_vector`).
    """
    state = clean(state, target="C").name_computing_elements()
    vars = state.variable_ordering()
    # no need to compute vars.aux.unneeded.
    evaluation_ordered = vars.aux.sorted + vars.aux.cyclic
    # this was wrong:
    #evaluation_ordered = sum(map(list, state.variable_ordering().ordering.values()),[])
    
    if not vars.evolved:
        raise ValueError("Nothing to evolve. Lacking some dda.int(f,dt,ic) integrators")
    
    # Translate const(foo) by stripping foo or some bar by looking up if it is an explicit constant.
    # Dynamical variables are not allowed here. This is somewhat similar but different to
    # cpp_exporter:lookup_const(var).
    def evaluate_const(var, state):
        if isinstance(var,Symbol):
            if var.head == "const":
                var = var.tail[0] # continue
            elif var.is_variable():
                if not var.head in vars.explicit_constants:
                    raise ValueError(f"Only constants allowed in this context. {var} however refers to {var.head}.")
                return evaluate_const(state[var.head], state)
            else: # remaining case: var.is_term()
                raise ValueError(f"Was expecting const(foo) or so, but got term {var}.")
        if not is_number(var): raise ValueError(f"Got a weird {type(var)} in a constant context: {var}")
        return var
    
    # by intention, dt and initial condition are ignored

    # Extract int(..., timestep, initial_data) and mark integrator as visited (mangled)
    timesteps = {}
    initial_data = {}
    def map_and_treat_integrals(var):
        if not var in vars.evolved: return state[var]
        tail = state[var].tail
        if not len(tail) >= 3: raise ValueError("int(...) requires at least int(value, dt, ic)")
        timesteps[var] = evaluate_const(tail[-2], state)
        initial_data[var] = evaluate_const(tail[-1], state)
        return Symbol("Int", *tail[0:len(tail)-2])
    state = State({ var: map_and_treat_integrals(var) for var in state })
    
    # Scipy needs numpy arrays for further processing
    timesteps = np.array([timesteps[k] for k in vars.evolved])
    y0 = np.array([initial_data[k] for k in vars.evolved])

    # The Scipy integrate methods cannot treat different timestep sizes.
    dt = timesteps[0]
    if not np.all(timesteps == dt):
        raise ValueError(f"Scipy requires all timesteps to be the same, however dt_({vars.evolved}) = {timesteps}")
    
    def evaluate(smbl, values):
        "Evaluate a symbol within the context of an already evaluated values dictionary given."
        if isinstance(smbl, float) or isinstance(smbl, int):
            return smbl # usable node
        if not isinstance(smbl, Symbol): raise TypeError(f"Expecting symbol, got {smbl}")
        if smbl.is_variable():
            return values[smbl.head] # can raise KeyError if variable not found.
        else: # symbl.is_term()
            if smbl.head in dda2python:
                return dda2python[smbl.head](*(evaluate(t, values) for t in smbl.tail))
            else:
                raise ValueError(f"DDA Symbol {smbl.head} in expression {smbl} not (yet) implemented.")

    # set beginning values for each call of f(y). This dictionary can be
    # mutated over repeated calls, but if you want to go sure, make a 
    # deep copy at every call.
    evaluation_default_values = { k: np.nan for k in state.keys() }
    for var in vars.explicit_constants:
        evaluation_default_values[var] = state[var].tail[0]
    
    def f(y):
        values = copy.deepcopy(evaluation_default_values)
        for i,var in enumerate(vars.evolved):
            values[var] = y[i]  # scatter
        # TODO: md3.py doesnt work when vars.aux.unneeded is skipped, because
        #       Int(...) depends on such an unneeded guy. This is wrong.
        for var in vars.aux.sorted + vars.aux.cyclic + list(vars.aux.unneeded):
            values[var] = evaluate(state[var], values)
            if np.isnan(values[var]):
                from pdb import set_trace as bp
                bp()
        dqdt = [ evaluate(state[var], values) for var in vars.evolved ]
        if np.any(np.isnan(np.array(dqdt))):
            from pdb import set_trace as bp
            bp()
        return np.array(dqdt)

    dtype = namedtuple("OdeProblem", "f dt y0")
    return dtype(f, dt, y0)
    

