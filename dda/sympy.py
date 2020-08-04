"""
This module provides interplay with the SymPy package. SymPy is a lightweight
pure-python computer algebra system which is bundled with SciPy.
An adapter to/from SymPy allows to use powerful Computer Algebra basic
functions such as expression simplification.

We use this currently to provide a lean latex representation for the
cumbersome DDA expressions.
"""

from . import Symbol
import builtins

identity = lambda x:x

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
 
