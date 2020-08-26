#!/usr/bin/env python3

r"""
This test mainly tests the `clean` function to work properly.
"""

from dda import State, Symbol
from dda.cpp_exporter import compile, run
import random, string

# primitive notation mapped to expected cleaninness
weirdos = [
    r"notWeird123",  
    r"\frac{x}{y}",  
    r"a^{-1}",       
    r"a^b_c^{ef}",   
    r"0123g",        
    r"µ²",           
    r"^^^",          
    r"foo[bar]baz",  
    r"Foo(bar)Baz",  
    r"77%",          
    r"4€",           
    r"what`the`heck",
]

def state():
    weirdsymbols = list(map(Symbol, weirdos))
    dt, t_initial = 0.1, 0.1
    integrate, negate = Symbol("int"), Symbol("neg")
    return State({ k: integrate(random.choice(weirdsymbols), dt, t_initial) for k in weirdsymbols })

def test_state():
    assert set(state().variable_ordering().evolved) == set(weirdos)

def c_code():
    return state().export(to="C++")

def dda_code():
    return state().export(to="dda")

def test_c_code():
    assert all(char in string.printable for char in c_code())
    compile(c_code()) # should now work without problems

def test_dda_code():
    assert all(char in string.printable for char in dda_code())
