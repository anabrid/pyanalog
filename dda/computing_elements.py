"""
The DDA language is built around the analog computing elements (or primitives).
These are basically electrical block circuits implementing basic arithmetics
such as summation and multiplication, but also integration. These are also
special elements for clipping, exponentials, square roots, and many more.

The DDA domain specific language is agnostic for function names. Host languages
such as Python or C are not. Many of the function names are reserved words in
these languages. Examples are:

- ``const``: Reserved word in C/C++ for constant variables
- ``int``: Type name in C, overwritable in python
- ``sum``: Builtin in python
- ``div``: Function in ``stdlib.h`` in C, which can cause clashes in slightly
  more complex C codes.

When it comes to exporting to languages such as C, we rewrite these keywords.
In Python, we don't have to, because none of the well known DDA function names 
is really *reserved*. The primitive builtins can always be recovered by
``from builtins import int, sum``, etc.

Different ways to access the well-known DDA computing elements in Python
------------------------------------------------------------------------

If you write

>>> from dda.computing_elements import *
>>> int(int,sum)  # Make use of the imported Symbols
int(int, sum)

you will load a bunch of names such as ``int`` and ``sum`` in your local
namespace.

You can also just call

>>> from dda.computing_elements import dda_functions, dda_symbols
>>> print(dda_symbols["floor"]) # will print a Symbol()
floor

You can use the symbols dictionary to populate your namespace at whish:

>>> globals().update(dda_symbols)

Note that Python globals are module-local, so we cannot provide this line
as a function.

Last but not least, you can also just use the namespaced version with
prefixes, which leaves you on a safe footing:

>>> dda.floor(dda.sum)
floor(sum)

Definition/Implementation of the primitives
-------------------------------------------

Once we have a pure-Python DDA evolution code (probably using scipy), we will
have a python implementation of the DDA functions. Otherwise I could avoid that.
This module also contains a C++ implementation of the primitives, which resides
as a string (``cpp_impl``).

"""

from .ast import Symbol, State, symbols
import types

# Here is the list of well-known DDA functions:
dda_functions = "const neg div int sum mult dead_upper dead_lower min max lt le gt ge sqrt abs exp floor".split()
dda_symbols = { k: Symbol(k) for k in dda_functions }

# This allows for easy namespace access, but cannot be easily imported
dda = types.SimpleNamespace(**dda_symbols)

# First, let's be nice and provide an instance:
state = State()

# Second, populate module this very namespace with well known DDA-registered functions:
globals().update(dda_symbols)

# The above line is equivalent to:
#const, neg, div, int, sum, mult, dead_upper, dead_lower, min, max, lt, le, gt, ge, sqrt, abs, exp, floor = symbols("\
#const, neg, div, int, sum, mult, dead_upper, dead_lower, min, max, lt, le, gt, ge, sqrt, abs, exp, floor")

 
# The implementation is given directly in the target language
cpp_impl = """
/* if you use an old C++ compiler, just remove the newer features */
#define A constexpr double            /* constexpr requires C++11 */
#define D template<typename... T> A   /* Variadic templates require C++17 */

// Known limitations for div(int, double): If certain arguments appear as integer
// in the code (i.e. 1 instead of 1.0), there is div(int,int) kicking in from
// cstdlib. TODO: Should rename div to Div; following int->Int.

A neg(double a) { return -a; }
A div(double a, double b) { return a/b; }
D Int(T... a) { return -(a + ...); } // int() is reserved in C
D sum(T... a) { return -(a + ...); }
D mult(T... a) { return (a * ...); }
A dead_upper(double a, double b) { return a > b ? (a-b) : 0; }
A dead_lower(double a, double b) { return a < b ? (a-b) : 0; }
A min(double a, double b) { return a < b ? a : b; }
A max(double a, double b) { return a > b ? a : b; }
A lt(double a, double b, double c, double d) { return a <  b ? c : d; }
A le(double a, double b, double c, double d) { return a <= b ? c : d; }
A gt(double a, double b, double c, double d) { return a >  b ? c : d; }
A ge(double a, double b, double c, double d) { return a >= b ? c : d; }
// A sqrt(double a) is part of <cmath>
A abs(double a) { return a < 0 ? -a : a; } // abs(int) part of cstdlib
// A exp(double a) is part of <cmath>
A floor(double a) { return (int)(a); } // also part of cmath since c++11
"""
