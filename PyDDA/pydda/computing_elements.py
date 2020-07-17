from .ast import Symbol, State
import types


# Here come dragons: The following lines define a couple of handy variables
# which can be used to write brever scripts. However, one probably does not
# want to import them.
#
# Here is the big CAVEAT: The following will OVERWRITE python internals such
# as int, sum, min, max. This can lead to very strange errors.
# Note that you can always access the Python builtins by importing builtins
# and using builtins.int, builtins.sum, etc.
#

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

# In order to access the dda functions in your global namespace, run this code:
# > globals().update(dda_symbols)
# Globals are module-local, so we cannot provide this as a function

# -> thanks to this file, one can now just run
# > from computing_elements import *
 
 
 
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
