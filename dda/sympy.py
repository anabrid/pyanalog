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
This module provides interplay with the SymPy package. SymPy is a lightweight
pure-python computer algebra system which is bundled with SciPy.
An adapter to/from SymPy allows to use powerful Computer Algebra basic
functions such as expression simplification.

We use this currently to provide a lean latex representation for the
cumbersome DDA expressions.
"""

from . import Symbol, dda
import builtins

identity = lambda x:x

def from_sympy(sympy_equation_list):
    """
    Import a state from a set of equations from SymPy.
    
    This function expects a python list of sympy equations where there
    is a single sympy symbol on one hand and an expression on the other
    hand (see examples below).
    
    The mapping basically follows the `SymPy key invariant
    <https://docs.sympy.org/latest/tutorial/manipulation.html#args>`_:
    "Every well-formed SymPy expression must either have empty ``args``
    or satisfy ``expr == expr.func(*expr.args)``".

    Therefore we basically map a sympy expression ``(expr.func,
    expr.args)`` to the DDA ``(head, tail)`` notation. While the heads
    are easy to map (for instance, ``sympy.Mul`` equals ``dda.mult``),
    special attention must be given to the tails, for instance SymPys
    ``Mul(a,b,c)`` translates to DDAs ``mult(mult(a,b),c)`` (in DDA
    we always assume commutative real-valued variables). Also in DDA
    there is ``neg(x)`` or ``div(x,y)`` which is represented in SymPy as
    ``Mul(Integer(-1), x)`` and ``Mul(Symbol('x'), Pow(Symbol('y'), Integer(-1)))``,
    respectively.
    """
    import sympy
    
    raise ValueError("Not yet implemented!")

    # This is terribly nontrivial.
    
    # final mappings without simplifications
    sympy2dda = {
        sympy.Mul:   dda.mult,
        sympy.sqrt:  dda.sqrt,
        sympy.Abs:   dda.abs,
        sympy.Add:   lambda *x: dda.neg(dda.sum(*x)),
        sympy.exp:   dda.exp,
        sympy.floor: dda.floor,
        sympy.integral: lambda function, *symbols: dda.int(function)
    }
    
    dda_Symbol = Symbol # just to be verbose
    atom = sympy.Wild("x", properties=[lambda k: k.is_Symbol])
    
    # Do a depth-first-traversal mapping sympy to dda expressions
    def expr2dda(expr):
        if len(expr.args) == 0: # reached leaf
            if expr.is_number:
                return float(expr)
            else:
                raise ValueError(f"Found {expr} but don't know how to handle.\n(srepr: {srepr(expr)})")
        else: # map compound expression
            # First, try shorthands:
            
            # expressions 1/x for atom x:
            #( sympy.Mul(sympy.Integer(-1), atom), lambda match: dda.inv(
                
            # border cases which are really mad to catch:
            # srepr(-3*b) -> Mul(Integer(-1), Integer(3), Symbol('b'))
            
            # Last, try anything else
            if type(expr) in sympy2dda:
                return sympy2dda[type(expr)](*expr.args)
            else:
                raise ValueError(f"Found compound expression of type {type(expr)}, don't know how to handle. It is: {expr}\n(srepr: {srepr(expr)})")
            
            
        for arg in expr.args:
            expr2dda(arg)
    
    for eq in sympy_equation_list:
        eq = eq.canonical # ensure symbol on the left
        lhs, rhs = eq.args
        if not isinstance(lhs, sympy.Symbol):
            raise ValueError(f"Missing single symbol on LHS of Sympy equation {eq}")
        
        dda_lhs = dda_Symbol(lhs.name)
        



def to_sympy(state, symbol_mapper=identity, round_n=15):
    """
    Export a state to a set of equations for SymPy.
    Returns a list of ``sympy.Eq`` objects.
    Of course it requires Sympy installed/available.
    
    .. note::

       The heart of this function is a mapping from :class:`ast.Symbol`
       terms (functions) to Sympy functions, for instance by mapping
       ``Symbol("int")(...)`` to ``-sympy.Integral(sympy.Add(...), t)``.

       Thanks to the ease of the computing elements, this mapping does
       not require pattern matching but can be performed on a basic
       level. However, not all terms are yet supported.


    The argument `symbol_mapper` allows to apply another mapping
    on the DDA Symbol heads. By default, it is the identity
    function.
    
    With Sympy, you can do all funny things, such as:
    
    >>> from dda import *
    >>> x,int,neg=symbols("x,int,neg")
    >>> state = State({'x': int(neg(x), 0.2, 1)})
    >>> to_sympy(state)
    [Eq(x, -Integral(1.2 - x, t))]
    """
    import sympy
    
    sympy_Symbol = lambda label: sympy.Symbol(symbol_mapper(label))
    
    # round large floats. Doesn't work yet.
    rhs_rounder = lambda rhs: sympy.N(rhs, n=round_n)
    
    int = builtins.int # just to go sure
    t = sympy_Symbol("t")
    
    def todo(*x):
        raise ValueError("Requried DDA 2 Sympy function yet implemented")
    
    dda2sympy = {
        "const": lambda x: x,
        "neg":   lambda x: -x,
        "div":   lambda x,y: x/y,
        "int":   lambda *x: - sympy.Integral(sympy.Add(*x), t),
        "sum":   lambda *x: - sympy.Add(*x),
        "mult":  sympy.Mul,
        "sqrt":  sympy.sqrt,
        "abs":   sympy.Abs,
        "exp":   sympy.exp,
        "floor": sympy.floor,
    }
    
    def symbol2sympy(smbl):
        if isinstance(smbl, float) or isinstance(smbl, int):
            return smbl # let Sympy handle the numbers
        if not isinstance(smbl, Symbol): raise TypeError(f"Expecting symbol, got {smbl}")
        if smbl.is_variable():
            return sympy_Symbol(smbl.head) # just a variable
        else: # symbl.is_term()
            if smbl.head in dda2sympy:
                return dda2sympy[smbl.head](*map(symbol2sympy, smbl.tail))
            else:
                raise ValueError(f"DDA Symbol {smbl.head} in expression {smbl} not (yet) implemented.")
    
    equation_list = [ sympy.Eq(sympy_Symbol(lhs), rhs_rounder(symbol2sympy(state[lhs])))  for lhs in sorted(state) ]
    return equation_list

def to_latex(state, chunk_n=None):
    """
    Export to latex, using sympy.
    
    This mostly differs from ``sympy.latex`` for large equation
    systems where we use the align latex environment instead of
    a single equation. For the above example:
    
    >>> import sympy, dda
    >>> x,int,neg=dda.symbols("x,int,neg")
    >>> state = dda.State({'x': int(neg(x), 0.2, 1)})
    >>> print(sympy.latex(to_sympy(state)))  
    \\left[ x = - \\int \\left(1.2 - x\\right)\\, dt\\right]
    >>> print(to_latex(state))               
    \\begin{align}
    x &= - \\int \\left(1.2 - x\\right)\\, dt
    \\end{align}
    """
    import sympy
    
    equation_list = to_sympy(state)

    # Pretty-print set of equations. That's nicer then just
    # sympy.latex(self.equation_list)
    s = [ f"{sympy.latex(eq.lhs)} &= {sympy.latex(eq.rhs)}" for eq in equation_list ]
    equation_list_to_align = lambda t: r"\begin{align}"+"\n" + (r" \\"+"\n").join(t) + "\n" + r"\end{align}"
    
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    latex = "\n".join(map(equation_list_to_align, chunks(s,chunk_n) if chunk_n else [s]))
    return latex
 
