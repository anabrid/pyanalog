#!/usr/bin/env python3

"""
Test different interfaces of the CPP exporter for resulting
in same data
"""

import dda.computing_elements as dda
import dda.cpp_exporter as cpp
import numpy as np

import pytest # pytest.raises

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

def test_similar_dtypes():
    s = dda.State()
    add_sinusodial(s, "foo")
    add_sinusodial(s, "bar")
    
    assert s.variable_ordering().evolved == ["bar_mdy", "bar_y", "foo_mdy", "foo_y" ]
    
    cpp.compile(s.export(to="C"))

    # note that we don't test return_ndarray=False, because this gives
    # us the plain output which is either a CSV file (in ASCII case)
    # or binary "garbarage" (in binary case, actually: packed floats)
    #
    # so these examples are all with return_ndarray=True
    
    ascii_data   = cpp.run(arguments={'max_iterations': N, "rk_order": 4})
    binary_data  = cpp.run(arguments={'max_iterations': N, "rk_order": 4}, binary=True)

    ascii_plain  = cpp.numpy_read(ascii_data, return_recarray=False )
    ascii_rec    = cpp.numpy_read(ascii_data, return_recarray=True )
    
    # with binary, it must ask for the fields:
    with pytest.raises(ValueError):
        binary_plain = cpp.numpy_read(binary_data, return_recarray=False, binary=True )
    with pytest.raises(ValueError):
        binary_rec   = cpp.numpy_read(binary_data, return_recarray=True, binary=True )
        
    all_fields = cpp.list_all_variables()
    assert all_fields == ['bar_mdy', 'bar_my', 'bar_y', 'foo_mdy', 'foo_my', 'foo_y']
    assert all_fields == list(ascii_rec.dtype.names)
    
    binary_plain = cpp.numpy_read(binary_data, return_recarray=False, binary=True, fields_to_export=all_fields)
    binary_rec   = cpp.numpy_read(binary_data, return_recarray=True, binary=True, fields_to_export=all_fields)

    assert ascii_plain.dtype  == binary_plain.dtype
    assert ascii_rec.dtype    == binary_rec.dtype
    assert ascii_plain.shape  == binary_plain.shape
    assert ascii_rec.shape    == binary_rec.shape

    assert np.allclose(ascii_plain, binary_plain)
    assert all(np.allclose(ascii_rec[name], binary_rec[name])  for name in ascii_rec.dtype.names)
