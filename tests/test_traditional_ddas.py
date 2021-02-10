#!/usr/bin/env python3

from pathlib import Path # Python > 3.5
import numpy as np
import dda

base = Path("../examples/traditional-dda-circuits")

def run_file(name, *args, **kwargs):
    return dda.read_traditional_dda_file(base/name).export(to="CppSolver").run(*args, **kwargs)

def test_if_double_pendulum_is_scaled():
    data = run_file("double-pendulum.dda", max_iterations=15000, modulo_write=15).as_recarray()
    assert np.max(np.abs(data["p1"])) < 5
    assert np.max(np.abs(data["p2"])) < 10
    # Well, this is not really scaled, isn't it? ;-)
    return data
    
def test_if_double_pendulum_is_working():
    # TODO: Would be nice to test that particular python script here.
    #mod = __import__(str(base/"run-double-pendulum.py"))
    pass

def test_if_chua_is_scaled():
    fields = ["x","y","z"]
    # we cannot run as many iterations as the run-chua.py test program since
    # that is dumping to a file while we are doing crazy python-internal pipe stuff.
    # which seems to be a bottleneck. So we reduced N=5e6 to N=5e4.
    N, mod = int(1e5), 30
    data = run_file("chua.dda", *fields, binary=True, max_iterations=N*mod, modulo_write=mod).as_ndarray()
    assert np.max(np.abs(data)) <= 1
    return data

def test_notch_is_scaled():
    data = run_file("notch_simplified.dda", max_iterations=1000, modulo_write=10).as_ndarray()
    assert np.max(np.abs(data)) <= 1

def test_nose():
    data = run_file("nose_9.dda", max_iterations=1000, modulo_write=10).as_recarray()
    assert np.max(np.abs(data["z"])) <= 2
    assert np.max(np.abs(data["y"])) <= 2
    assert np.max(np.abs(data["minus_x"])) <= 2
