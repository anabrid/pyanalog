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
# For Germany, additional rules exist. Please consult /LICENSE.DE
# for further agreements.
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
import math, functools, itertools, operator, copy, argparse, inspect, sys # builtins
import numpy as np # externals
from builtins import sum # just to be explicit, sum is not overwritten
from collections import namedtuple, OrderedDict

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
    >>> py_state.rhs(py_state.y0)  # evaluation of f(y) on y0
    array([-1, -2])
    >>> y1 = py_state.rhs(py_state.y0) * py_state.dt  # a single Euler integration timestep, for instance
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
        self.vars = self.state.variable_ordering()
        
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
    
    def evaluate_state(self, evolution_vector, copy=False):
        """
        Recomputes the full state from the evolution state vector.
        Returns a dictionary with same keys as ``self.state`` and scalars (floats) as
        values.
        
        This will especially compute the aux variables, while for the evaluation
        variables the RHS of ``dy / dt = f(y)`` is computed.
        
        .. note:: As a user, you most likely want to call :meth:`reconstruct_state` or
           :meth:`rhs` instead of this function.
        
        For optimization purpose, numerical state evaluation is always carried
        out on the ``evaluation_default_values`` member (which also hold the initial
        values for the first ``rhs`` evaluation). If you set ``copy=True``,
        a shallow copy (which is equal to a deep copy for a dict holding floats)
        is returned. In external calls, you should probably always set ``copy=True``.
        
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
        # A shallow copy should be fine, since self.evaluation_default_values 
        # only holds immutable datat types (floats) and never mutable ones
        # (such as lists). We allow for *not* doing this copy only for performance
        # reasons, as calls to self.rhs() basically overwrite the values dict
        # completely and thus don't need to reallocate all the dict on every call.
        if copy or self.debug: values = values.copy() #copy.deepcopy(values)
        for i,var in enumerate(self.vars.evolved):
            values[var] = evolution_vector[i]  # scatter
        # TODO: md3.py doesnt work when vars.aux.unneeded is skipped, because
        #       Int(...) depends on such an unneeded guy. This is wrong.
        for var in itertools.chain(self.vars.aux.sorted, self.vars.aux.cyclic, self.vars.aux.unneeded):
            values[var] = evaluate_values(self.state[var], values)
        nanmask = np.isnan(list(values.values()))
        if any(nanmask):
            nankeys = np.array(list(values.keys()))[nanmask]
            print(f"to_scipy(state).evaluate_state({evolution_vector}): NaN detected in evaluation of {nankeys}")
            print("Here is a PDB shell for debugging:")
            from pdb import set_trace as bp
            bp()
        return values
    
    def reconstruct_state(self, evolution_vector, copy=True):
        """
        Given the evolution vector sizes, this computes the full state. That is, this function
        differs from :meth:`evaluate` at all evaluation quantities where the values of the
        evolution vector itself are put in place.
        """
        values = self.evaluate_state(evolution_vector, copy=copy)
        for i,var in self.vars.evolved:
            values[var] = evolution_vector[i]
        return values

    def rhs(self, evolution_vector):
        """
        The ODE *right hand side* in ``dy / dt = f(y)``. ``y`` is a numpy vector,
        and ``f(y)`` returns a similarly sized (numpy) vector which we call ``rhs`` here:
        
        >>> ode = to_scipy(State({ Symbol("x"): Symbol("int")(Symbol("x"),0.1,1) }))
        >>> y1 = ode.y0 + ode.rhs(ode.y0) * ode.dt   # perform some euler integration step
        >>> y1
        array([0.9])
        
        Usually, you want to pass this function to some scipy integrator. See
        also :meth:`ft`.
        """
        values = self.evaluate_state(evolution_vector)
        dqdt = [ evaluate_values(self.state[var], values) for var in self.vars.evolved ] # gather
        if np.any(np.isnan(np.array(dqdt))):
            from pdb import set_trace as bp
            bp()
        return np.array(dqdt)

    def rhst(self, t, evolution_vector):
        """Syntactic sugar for scipy integrators who want a signature ``rhst(t,y)``. Will
        just call ``rhs(y)`` instead."""
        return self.rhs(evolution_vector)

    def solve(self, tfinal, **kwargs):
        """
        Basically passes all arguments to ``scipy.integrate.solve_ivp``. See
        documentation for :class:`to_scipy` for usage example.
        
        Currently, it is hardcodedly ``tspan=[0,tfinal]``. All other (keyword) arguments
        are passed to ``solve_ivp``.
        """
        from scipy.integrate import solve_ivp
        return solve_ivp(self.rhst, [0, tfinal], self.y0, **kwargs)


def cli_scipy():
    """
    A Command Line Interface (CLI) for dda.scipy.

    This CLI API basically solves a DDA file (see :mod:dsl for the syntax).
    This is a different approach then using the :mod:cpp_exporter: Instead
    of code generation (and the need for a C++ compiler), this evaluates the
    DDA file within python. The disadvantage is that this is damned slow, the
    advantage is that the time integrator is much better then the selfmade one
    in the :mod:cpp_exporter module.
    
    Invocation is like  ``python -m dda.scipy --help`` anywhere from the system.
    Run this to explore the usage of this command line interface.
    """
    from .dsl import read_traditional_dda
    
    parser = argparse.ArgumentParser(description="PyDDA's scipy interface simulation runner", epilog=inspect.getdoc(cli_scipy))

    parser.add_argument("circuit_file", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="DDA setup (traditional file). Default is stdin.")
    parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="Where to write output CSV to. Default is stdout.")
    
    g = parser.add_argument_group(title="Arguments passed to scipy.integrate.solve_ivp")
    g.add_argument("-t", "--tfinal", required=True, type=float, help="Time (in simulation units) to run up to. Do not confuse this with some iteration counter.")
    g.add_argument("--method", nargs="?", help="Integration method to use")
    # add whatever you want to expose
    
    arg = parser.parse_args()
    
    dda_text = arg.circuit_file.read()
    dda_state = read_traditional_dda(dda_text)
    scipy_state = to_scipy(dda_state)
    
    scipy_args = {}
    if arg.method: scipy_args["method"] = arg.method
    
    sol = scipy_state.solve(arg.tfinal, **scipy_args)
    
    writeout = OrderedDict()
    writeout["t"] = sol.t
    for i,fieldname in enumerate(sorted(scipy_state.vars.evolved)):
        writeout[fieldname] = sol.y[i]

    sep = "\t"
    # don't using np.savetxt(header=...) because it prepends a comment sign "# "
    print(sep.join(writeout.keys()), file=arg.output)
    np.savetxt(arg.output, np.array(list(writeout.values())).T, delimiter=sep)

    
if __name__ == "__main__":
    cli_scipy()
