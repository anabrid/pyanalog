#!/usr/bin/env python3

"""
Test different interfaces of the CPP exporter for resulting
in same data
"""

import dda.computing_elements as dda
import dda.cpp_exporter as cpp
import numpy as np

t_final = 10
dt = 0.01
N = t_final / dt
assert int(N) == N
 
def add_sinusodial(s, name):
    # some sinosidual test signal
    y, my, mdy = dda.symbols(f"{name}_y, {name}_my, {name}_mdy")
    s[my]  = dda.neg(y)
    s[y]   = dda.int(mdy, dt, 0)
    s[mdy] = dda.int(my, dt, 1)
    return s

def test_cpp_export_formats():
    s = dda.State()
    add_sinusodial(s, "foo")
    add_sinusodial(s, "bar")
    cpp.compile(s.export(to="C"))

    # note that we don't test return_ndarray=False, because this gives
    # us the plain output which is either a CSV file (in ASCII case)
    # or binary "garbarage" (in binary case, actually: packed floats)
    #
    # so these examples are all with return_ndarray=True

    ascii_plain  = cpp.run(arguments={'max_iterations': N, "rk_order": 4}, return_recarray=False )
    ascii_rec    = cpp.run(arguments={'max_iterations': N, "rk_order": 4}, return_recarray=True )
    binary_plain = cpp.run(arguments={'max_iterations': N, "rk_order": 4}, return_recarray=False, binary=True )
    binary_rec   = cpp.run(arguments={'max_iterations': N, "rk_order": 4}, return_recarray=True, binary=True )

    assert ascii_plain.dtype  == binary_plain.dtype
    assert ascii_rec.dtype    == binary_rec.dtype
    assert ascii_plain.shape  == binary_plain.shape
    assert ascii_rec.shape    == binary_rec.shape

    assert np.allclose(ascii_plain, binary_plain)
    assert all(np.allclose(ascii_rec[name], binary_rec[name])  for name in ascii_rec.dtype.names)
