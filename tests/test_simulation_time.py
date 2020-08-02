#!/usr/bin/env python3

r"""
This test problem for DDA solves the simple differential
equation

   my(t) = - \int_0^{t_final} 1 \cdot dt
   
We then deduce t = -mt as an auxilliary step.

We then test the output of the C++ for consistency of times.
"""

from dda.computing_elements import symbols, state
from dda.cpp_exporter import compile, run
# postprocessing:
import numpy as np

# numbers of iterations and time step size
t_initial, t_final = 0.0, 2.0
dt = 0.05
N = t_final / dt
assert N == int(N)
N = int(N)  # np.linspace requires an integer

def setup_state():
    mt, t = symbols("mt, t")
    integrate, negate = symbols("int, neg")

    state["mt"] = integrate(1, dt, t_initial)
    state["t"]  = negate(mt)
    
    return state

def test_setup_state():
    state = setup_state()
    assert "mt" in state.variable_ordering().evolved
    assert  "t" in state.variable_ordering().aux.all

def run_simulation(write_initial_conditions=False):
    c_code = setup_state().export(to="C++")
    compile(c_code)
    return run(arguments={
        'max_iterations': N,
        'modulo_write': 1,
        "always_compute_aux_before_printing": 1,
        "write_initial_conditions": int(write_initial_conditions)
    })

def test_run_simulation():
    output_with_ic = run_simulation(True)
    output_without_ic = run_simulation(False)

    # Thanks to always_compute_aux_before_printing, this consistency holds:
    assert np.allclose(output_with_ic["t"], -output_with_ic["mt"])
    assert np.allclose(output_without_ic["t"], -output_without_ic["mt"])

    # The difference between write_initial_conditions is just:
    equalize = lambda without: np.concatenate(([t_initial], without))
    assert np.allclose(output_with_ic["t"], equalize(output_without_ic["t"]))
    assert np.allclose(output_with_ic["mt"], equalize(output_without_ic["mt"]))

    assert len(output_without_ic) == N
    time_without_ic = np.arange(t_initial, t_final, dt) + dt
    assert len(time_without_ic) == N
    assert np.allclose( time_without_ic, output_without_ic[ "t"])
    assert np.allclose(-time_without_ic, output_without_ic["mt"])

    assert len(output_with_ic) == N+1
    time_with_ic = np.linspace(t_initial, t_final, N+1, endpoint=True)
    assert len(time_with_ic) == N+1
    assert np.allclose( time_with_ic, output_with_ic[ "t"])
    assert np.allclose(-time_with_ic, output_with_ic["mt"])