"""
PyDDA is a small library to write and generate DDA code in Python.
DDA stands for digital differential analyzer. In this context, it is
a code for solving ordinary differential equations given in a domain
specific language description (i.e. an electrical circuit).

The main advantage of this implementation in contrast to the older Perl
implementation is abstract syntax tree level of circuit representation.
The syntax tree representation allows for fine-grained manipulations of
terms where the older Perl code could only apply regular expressions.

This code can replace the dda2c.pl Perl implementation. It is a
standalone Python 3 code with no third party dependencies. It generates
standalone C++ code with no dependencies (not even on dda.h).

This module can either be used from a DDA file written in Python or 
directly from old-style traditional DDA plaintext files. While pythonic
dda files have the advantage to be able to use all the flexibility of
Python scripting (such as using numpy for linear algebra computations
and matplotlib for postprocessing of results), plaintext DDA files are
in general shorter and more precise to read.

The dda.py file can also be used as a command line utility. The
behaviour is similar to the simulate.pl and dda2c.pl utilities but also
covers a few more features.

Known Bugs and limitations
--------------------------

(Amongst others)

::

    (1) Aliasing

    > state.foo = f(...)
    > state.bar = state.foo

    doesn't resolve (state must point to terms, not variables)
    
(See also the relevant Gitlab project and issues therein)

Written in June 2020 by SvenK.
Will be Open Sourced within the Analog R&D project.
""" 

import sys

assert sys.version_info >= (3, 6), \
   "PyDDA uses f-strings all the ways, which require Python 3.6."

# Define some administrative code which should go somewhere else
# or be evventually deleted.

class exporter:
    "Base class for writing exporters. Should be removed."
    def __init__(self, state, **kw):
        self.__dict__.update(kw) # bit ugly parameter passing
        self.state = state
        self.run() # should be chainable (return self) and set self.output [str]
        
    def arg(self, name, default=None): # sugar
        return self.__dict__.get(name, default)
    
    def print(self, to=sys.stdout):
        if isinstance(to, str): to = open(to, "w") # a neat service
        if not hasattr(self, "output"): self.run()
        print(self.output, file=to)
        self.output_filename = to.name
        return self # chainable


def export(state, to, **kw):
    "Convenience function to export a state to something."
    from .cpp_exporter import cpp_code_generator
    from .dsl import traditional_dda_exporter
    from .sympy import to_sympy
    exporters = { "c": cpp_code_generator, "dda": traditional_dda_exporter, "sympy": to_sympy }
    if not to.lower() in exporters:
        raise ValueError(f"Export format {to} not known. Valid are {exporters.keys()}.")
    return exporters[to.lower()](state, **kw)


# populate namespace with some useful objects which should
# live in the package namespace.

from .ast import Symbol, State, BreveState, symbols, is_symbol
from .computing_elements import dda, dda_functions, dda_symbols
from .sympy import to_sympy
