"""
This module provides interplay with the SymPy package. SymPy is a lightweight
pure-python computer algebra system which is bundled with SciPy.
An adapter to/from SymPy allows to use powerful Computer Algebra basic
functions such as expression simplification.

We use this currently to provide a lean latex representation for the
cumbersome DDA expressions.
"""

from . import exporter, Symbol
import builtins

class to_sympy(exporter):
    def run(self):
        """
        Export a state to a set of equations for SymPy.
        Returns a list of sympy.Eq objects.
        Of course it requires Sympy installed/available.
        
        With Sympy, you can do all funny things, such as:
        > ss = export(state).to_sympy()
        > import sympy
        > print(sympy.latex(ss)) # Will pretty-print simplified equations
        """
        import sympy
        
        state = self.state
        
        symbol_mapper = self.arg("symbol_mapper", lambda x:x)
        sympy_Symbol = lambda label: sympy.Symbol(symbol_mapper(label))
        
        # round large floats. Doesn't work yet.
        rhs_rounder = lambda rhs: sympy.N(rhs, n=self.arg("round_n", 15))
        
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
        
        self.equation_list = [ sympy.Eq(sympy_Symbol(lhs), rhs_rounder(symbol2sympy(state[lhs])))  for lhs in sorted(state) ]
    
        # Pretty-print set of equations. That's nicer then just
        # sympy.latex(self.equation_list)
        s = [ f"{sympy.latex(eq.lhs)} &= {sympy.latex(eq.rhs)}" for eq in self.equation_list ]
        equation_list_to_align = lambda t: r"\begin{align}"+"\n" + (r" \\"+"\n").join(t) + "\n\end{align}"
        
        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        
        chunk_n = self.arg("chunk_equations", None)
        self.latex = "\n".join(map(equation_list_to_align, chunks(s,chunk_n) if chunk_n else [s]))
        self.output = self.latex # just a pretty-print version
     
