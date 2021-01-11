#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the DDA module of the PyAnalog toolkit.
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
The ``dda.scipy`` module allows in-python evaluation of DDA systems
as well as their solution with ODE Integrators in Python,
such as `scipy.integrate <https://docs.scipy.org/doc/scipy/reference/tutorial/integrate.html>`_.

For the usage and examples, see the class :class:`to_scipy`.

In order to run this code, you need, obviously, `SciPy <https://www.scipy.org/>`_ next 
to `NumPy <https://numpy.org/>`_.
"""

from . import State, Symbol, symbols, clean
import math, functools, itertools, operator, copy # builtins
import numpy as np # externals
from builtins import sum # just to be explicit, sum is not overwritten
from collections import namedtuple

is_number = lambda obj: isinstance(obj, float) or isinstance(obj, int)
first = lambda iterable: next(x for x in iterable if x)  # first element of iterator/list

dda2python = {  #: Mapping directory of Symbol heads to their pure-python implementation.
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
    The SciPy exporter. When initializing this class with your DDA system, it will setup
    a function ``f(y)`` which can be evaluated as any right hand side in the ordinary
    differential equation (ODE) system ``dy/dt = f(y)``. Here, ``y`` are the evolution
    quantities, i.e. a vector which is composed automatically from the linearized DDA system
    (see :meth:`ast.State.name_computing_elements` and :meth:`ast.State.variable_ordering`).
    Furthermore, this class prepares the initial values ``y0`` for the integration.
    
    You can evaluate these quantities in any python context, i.e. with any scientific python
    ODE solver library. For the time being, this class provides a convenience method
    :meth:`solve` which calls `scipy.integrate.solve_ivp <https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html>`_.
    There is no other scipy dependence in this code.
    
    Usage example:
    
    >>> from dda.computing_elements import neg,int,mult
    >>> from dda import State, symbols
    >>> x, y, z = symbols("x, y, z")
    >>> dda_state = State({x: int(y, 1, 1), y: mult(2,x), z: neg(int(z, 1, -1)) })
    >>> py_state = to_scipy(dda_state)
    >>> py_state.state # state has been linearized before processing
    State({'int_1': Int(z), 'x': Int(y), 'y': mult(2, x), 'z': neg(int_1)})
    >>> py_state.vars.evolved # evolved variables are therefore not [x,z] but [int_1,x]
    ['int_1', 'x']
    >>> py_state.y0  # initial values
    array([-1,  1])
    >>> py_state.dt # same timestep for all integrals (but see note below)
    1
    >>> py_state.f(py_state.y0)  # evaluation of f(y) on y0
    array([-1, -2])
    >>> y1 = py_state.f(py_state.y0) * py_state.dt  # a single Euler integration timestep, for instance
    >>> y1
    array([-1, -2])
    >>> sol = py_state.solve(10)  # ODE integration with SciPy
    >>> sol.t  # integration went from 0->10 with 17 timesteps     # doctest:+ELLIPSIS
    array([ 0.        , ..., 10.        ])
    >>> sol.y[:,-1] # the first solution is ~exp(+t)->inf, the second exp(-t)->0
    array([-2.20269685e+04,  1.94334984e-08])
    >>> from pylab import plot, legend, show  # plotting example   # doctest:+SKIP
    >>> for i,fieldname in enumerate(py_state.vars.evolved):       # doctest:+SKIP
            plot(sol.t, sol.y[i], label=fieldname)
    >>> legend(); show()                                           # doctest:+SKIP
    
    
    .. warning:: Due to the way how widespread ODE integrators work, the per-integral
       step size ``dt`` is required to be the same for every integration which is part
       of the DDA system. That is, the following generates an error:
       
       >>> from dda import dda, symbols
       >>> a,b=symbols("a,b")
       >>> state = State({ a: dda.int(a, 0.2, 0), b: dda.int(b, 0.5, 0) })
       >>> to_scipy(state)
       Traceback (most recent call last):
       ...
       ValueError: Scipy requires all timesteps to be the same, however dt_(['a', 'b']) = [0.2 0.5]
       
       Most high-level integrators available in scientific Python toolkits (such as scipy)
       assume the overall system to have a single timestep size ``Δt`` (which is also quite
       natural from a mathematical perspective). The signature ``dda.int(f,dt,ic)`` is thus
       quirky from a mathematical or numerical viewpoint. It is written in such a way because
       analog computing integrators have a tunable time scale ``k_0 ~= 1/dt`` which however
       can also be consumed in the integrand itself: ``dda.int(f,1/k_0,ic) == dda.int(f/k_0,1,ic)``.
       
       Furthermore, most high-level integrators do adaptive timestepping anyway. The fine-tuning
       of timestep sizes is something which is only paid respect to in the :mod:`cpp_exporter`
       module.
    """
    
    def __init__(self, state):
        "state needs to be an instance of :class:`ast.State`"
        self.state = clean(state, target="python").name_computing_elements()
        self.vars = state.variable_ordering()
        
        if not self.vars.evolved:
            raise ValueError("Nothing to evolve. Lacking some dda.int(f,dt,ic) integrators")
        
        # by intention, dt and initial condition are ignored

        # Extract int(..., timestep, initial_data) and mark integrator as visited (mangled)
        timesteps = {}
        initial_data = {}
        def map_and_treat_integrals(var):
            if not var in self.vars.evolved: return self.state[var]
            tail = self.state[var].tail
            if not len(tail) >= 3: raise ValueError("int(...) requires at least int(value, dt, ic)")
            timesteps[var] = self.evaluate_const(tail[-2])
            initial_data[var] = self.evaluate_const(tail[-1])
            return Symbol("Int", *tail[0:len(tail)-2])
        self.state = State({ var: map_and_treat_integrals(var) for var in self.state })
        
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
        self.evaluation_default_values = { k: np.nan for k in self.state.keys() }
        for var in self.vars.explicit_constants:
            self.evaluation_default_values[var] = self.state[var].tail[0]
            
        self.debug = False
    
    def evaluate_const(self, var):
        """
        Translate ``const(foo)`` by stripping foo or some bar by looking up if it is an explicit constant.
        Dynamical variables are not allowed here. This is somewhat similar but different to
        ``cpp_exporter.lookup_const(var)``.
        """
        if isinstance(var,Symbol):
            if var.head == "const":
                var = var.tail[0] # continue
            elif var.is_variable():
                if not var.head in self.vars.explicit_constants:
                    raise ValueError(f"Only constants allowed in this context. {var} however refers to {var.head}.")
                return self.evaluate_const(self.state[var.head])
            else: # remaining case: var.is_term()
                raise ValueError(f"Was expecting const(foo) or so, but got term {var}.")
        if not is_number(var): raise ValueError(f"Got a weird {type(var)} in a constant context: {var}")
        return var
    

    def f(self, y):
        """
        The ODE right hand side in ``dy / dt = f(y)``. ``y`` is a numpy vector,
        and ``f(y)`` returns a similarly sized vector:
        
        >>> ode = to_scipy(State({ Symbol("x"): Symbol("int")(Symbol("x"),0.1,1) }))
        >>> y1 = ode.y0 + ode.f(ode.y0) * ode.dt   # perform some euler integration step
        >>> y1
        array([0.9])
        
        Usually, you want to pass this function to some scipy integrator. See
        also :meth:`ft`.
        
        .. note:: The implementation of this function currently evaluates the (prepared) DDA 
            sytem by recursive calls with the help of a variable assignment directory. This is
            basically a *run-time compilation* (JIT/VM) in pure python. Needless to say, this
            won't give a great performance!
            
            There are plenty of low-hanging fruits to provide optimized versions of this code:
            One could call the efficient (but still scalar) C++ implementation which
            :mod:`cpp_exporter` provides by `methods provided by Cython
            <https://cython.readthedocs.io/en/latest/src/userguide/external_C_code.html>`_.
            One could also map the DDA abstract syntax tree (AST) to the python one and
            use some unparser code to evaluate the DDA code as pure python
            (see for instance
            `Python: Modify AST and write back python code 
            <https://stackoverflow.com/questions/768634/parse-a-py-file-read-the-ast-modify-it-then-write-back-the-modified-source-c>`_).
            
            For the time being, this code remains as a pure demonstration code.
            Thanks to using the linearized state, there should be no troubles with call stack
            overflows, however cyclic dependencies may not be properly resolved
            and can result in infinite recursions (stack overflow).
        """
        values = self.evaluation_default_values
        if self.debug: values = copy.deepcopy(values)
        for i,var in enumerate(self.vars.evolved):
            values[var] = y[i]  # scatter
        # TODO: md3.py doesnt work when vars.aux.unneeded is skipped, because
        #       Int(...) depends on such an unneeded guy. This is wrong.
        for var in itertools.chain(self.vars.aux.sorted, self.vars.aux.cyclic, self.vars.aux.unneeded):
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
        Basically passes all arguments to ``scipy.integrate.solve_ivp``. See
        documentation for :class:`to_scipy` for usage example.
        """
        from scipy.integrate import solve_ivp
        return solve_ivp(self.ft, [0, tfinal], self.y0, **kwargs)

