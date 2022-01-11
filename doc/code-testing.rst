.. _code-testing:

Software testing in PyAnalog
============================

The PyAnalog code is still quite alpha, but we do a number of software tests
without much extra work:

`Doctests <https://docs.python.org/3/library/doctest.html>`_
    are super
    simple to add, they are just embedded in the documentation. It's a quite
    pythonic way to demonstrate (and test at the same time) the functionality
    of small pieces of code.
  
    We have doctests all over the place. The code snippets are of course
    also included in the documentation. You can copy & paste them into your
    python console to play with the API.
  
Acceptance/Integration tests
    We can provide some DDA files
    where we know the solution analytically. It should be a useful exercise
    both for readers and testers to run these examples. We use the
    `pytest <https://pytest.org>`_ third party library for (unit) testing.
  
    These tests are located in the ``tests/`` directory. They can be executed
    by running ``pytest tests`` or just ``make test`` from the parent directory.
    
.. note::

    Tests are special because they can be evaluated for success or failure
    automatically. This differs them from other code contributions, such
    as the example codes in the ``examples/`` directory, which cannot be
    evaluated for correctnes.
    
How to run the tests
--------------------

Just run ``make test`` in the root directory to run all of the tests. The output
should look somewhat like this one:

::

    $make test
    make doctest unittests
    make[1]: Verzeichnis ..../dda wird betreten
    python3 -m pytest --doctest-modules --pyargs dda --ignore=dda/__main__.py  -v
    ============================================= test session starts =============================================
    platform linux -- Python 3.9.7, pytest-6.2.5, py-1.10.0, pluggy-0.13.1 -- /usr/bin/python3
    cachedir: .pytest_cache
    rootdir: /home/sven/Analog/Software/dda
    collected 22 items                                                                                            

    dda/__init__.py::dda.clean PASSED                                                                       [  4%]
    dda/ast.py::dda.ast.BreveState PASSED                                                                   [  9%]
    dda/ast.py::dda.ast.State PASSED                                                                        [ 13%]
    dda/ast.py::dda.ast.State.dependency_graph PASSED                                                       [ 18%]
    dda/ast.py::dda.ast.State.equation_adder PASSED                                                         [ 22%]
    dda/ast.py::dda.ast.State.name_computing_elements PASSED                                                [ 27%]
    dda/ast.py::dda.ast.State.variable_ordering PASSED                                                      [ 31%]
    dda/ast.py::dda.ast.Symbol PASSED                                                                       [ 36%]
    dda/ast.py::dda.ast.Symbol.draw_graph PASSED                                                            [ 40%]
    dda/ast.py::dda.ast.Symbol.map_heads PASSED                                                             [ 45%]
    dda/ast.py::dda.ast.Symbol.map_tails PASSED                                                             [ 50%]
    dda/ast.py::dda.ast.Symbol.map_terms PASSED                                                             [ 54%]
    dda/ast.py::dda.ast.Symbol.map_variables PASSED                                                         [ 59%]
    dda/ast.py::dda.ast.symbols PASSED                                                                      [ 63%]
    dda/computing_elements.py::dda.computing_elements PASSED                                                [ 68%]
    dda/cpp_exporter.py::dda.cpp_exporter.run PASSED                                                        [ 72%]
    dda/dsl.py::dda.dsl PASSED                                                                              [ 77%]
    dda/dsl.py::dda.dsl.read_traditional_dda SKIPPED (all tests skipped by +SKIP option)                    [ 81%]
    dda/scipy.py::dda.scipy.to_scipy PASSED                                                                 [ 86%]
    dda/scipy.py::dda.scipy.to_scipy.rhs PASSED                                                             [ 90%]
    dda/sympy.py::dda.sympy.to_latex PASSED                                                                 [ 95%]
    dda/sympy.py::dda.sympy.to_sympy PASSED                                                                 [100%]

    ======================================== 21 passed, 1 skipped in 1.82s ========================================
    python3 -m pytest --doctest-modules --pyargs hycon  -v
    ============================================= test session starts =============================================
    platform linux -- Python 3.9.7, pytest-6.2.5, py-1.10.0, pluggy-0.13.1 -- /usr/bin/python3
    cachedir: .pytest_cache
    rootdir: /home/sven/Analog/Software/dda
    collected 12 items                                                                                            

    hycon/HyCon.py::hycon.HyCon PASSED                                                                      [  8%]
    hycon/HyCon.py::hycon.HyCon.ensure PASSED                                                               [ 16%]
    hycon/HyCon.py::hycon.HyCon.expect PASSED                                                               [ 25%]
    hycon/autosetup.py::hycon.autosetup.DotDict PASSED                                                      [ 33%]
    hycon/autosetup.py::hycon.autosetup.PotentiometerAddress PASSED                                         [ 41%]
    hycon/connections.py::hycon.connections PASSED                                                          [ 50%]
    hycon/replay.py::hycon.replay.HyConRequestReader PASSED                                                 [ 58%]
    hycon/replay.py::hycon.replay.consume PASSED                                                            [ 66%]
    hycon/replay.py::hycon.replay.consume.list PASSED                                                       [ 75%]
    hycon/replay.py::hycon.replay.consume.number PASSED                                                     [ 83%]
    hycon/replay.py::hycon.replay.delayed PASSED                                                            [ 91%]
    hycon/replay.py::hycon.replay.replay PASSED                                                             [100%]

    ============================================= 12 passed in 0.03s ==============================================
    # all other modules don't have useful tests anyway
    python3 -m pytest -v
    ============================================= test session starts =============================================
    platform linux -- Python 3.9.7, pytest-6.2.5, py-1.10.0, pluggy-0.13.1 -- /usr/bin/python3
    cachedir: .pytest_cache
    rootdir: /home/sven/Analog/Software/dda
    collected 15 items                                                                                            

    tests/test_cpp_interface.py::test_similar_dtypes PASSED                                                 [  6%]
    tests/test_differentiation.py::test_polynomial_diff PASSED                                              [ 13%]
    tests/test_differentiation.py::test_sinusodial_diff PASSED                                              [ 20%]
    tests/test_exponential_solution.py::test_run_simulation PASSED                                          [ 26%]
    tests/test_latex_symbols.py::test_state PASSED                                                          [ 33%]
    tests/test_latex_symbols.py::test_c_code PASSED                                                         [ 40%]
    tests/test_latex_symbols.py::test_dda_code PASSED                                                       [ 46%]
    tests/test_simulation_time.py::test_setup_state PASSED                                                  [ 53%]
    tests/test_simulation_time.py::test_run_simulation PASSED                                               [ 60%]
    tests/test_symbol_mappings.py::test_map_variable PASSED                                                 [ 66%]
    tests/test_traditional_ddas.py::test_if_double_pendulum_is_scaled PASSED                                [ 73%]
    tests/test_traditional_ddas.py::test_if_double_pendulum_is_working PASSED                               [ 80%]
    tests/test_traditional_ddas.py::test_if_chua_is_scaled PASSED                                           [ 86%]
    tests/test_traditional_ddas.py::test_notch_is_scaled PASSED                                             [ 93%]
    tests/test_traditional_ddas.py::test_nose PASSED                                                        [100%]

    ============================================= 15 passed in 11.23s =============================================
    make[1]: Verzeichnis ..../dda wird verlassen


Test scripts can also be run and inspected with python interactively, i.e.
  
::

    you@yourcomputer$ python -i test_exponential_solution.py
    >>> from pylab import *
    >>> ion()
    >>> time, ysim = test_run_simulation()
    generated.cc: In Elementfunktion »void csv_writer::write_header() const«:
    generated.cc:171:43: Warnung: Operation auf »i« könnte undefiniert sein [-Wsequence-point]
    171 |             std::cout << query_variables[i++] << sep(i);
        |                                          ~^~
    generated.cc: In Funktion »int main(int, char**)«:
    generated.cc:275:90: Warnung: Operation auf »i« könnte undefiniert sein [-Wsequence-point]
    275 |                 for(size_t j=0;j<5 && i<all_variables.size();j++) cerr << all_variables[i++] << (i!=all_variables.size() ? ", " : ""); }
        |                                                                                         ~^~
    Running: ./a.out --max_iterations=60 --modulo_write=1 --always_compute_aux_before_printing=1 --write_initial_conditions=0
    >>> print(time)
    [0.05 0.1  0.15 0.2  0.25 0.3  0.35 0.4  0.45 0.5  0.55 0.6  0.65 0.7
    0.75 0.8  0.85 0.9  0.95 1.   1.05 1.1  1.15 1.2  1.25 1.3  1.35 1.4
    1.45 1.5  1.55 1.6  1.65 1.7  1.75 1.8  1.85 1.9  1.95 2.   2.05 2.1
    2.15 2.2  2.25 2.3  2.35 2.4  2.45 2.5  2.55 2.6  2.65 2.7  2.75 2.8
    2.85 2.9  2.95 3.  ]
    >>> plot(time, ysim, "o")
    [<matplotlib.lines.Line2D object at 0x7fe9a99c7520>]
    >>> plot(time, -exp(-time))
    [<matplotlib.lines.Line2D object at 0x7fe9982f43a0>]
    >>> savefig("exponential_solution.png")


How to run doctests on the whole package
----------------------------------------

Use `pytest <https://docs.pytest.org/>`_ as a slim frontend for the python
doctest builtin, for instance:

::

    $ cd $(git rev-parse --show-toplevel)            # execute from PyAnalog root directory
    $ pytest-3 --doctest-modules --pyargs dda  -v

See also the ``Makefile`` provided in the root directory.

Where are the tests running?
----------------------------

Tests are run by our *Gitlab Continous Integration* whenever the code is committed. You can
view the file ``.gitlab-ci.yml`` in the root of the repository in order to see what is happening,
which is at the moment something like

  * Make the docs (run sphinx)
  * Deploy the docs (upload them somewhere)
  * Run all the tests (as above)

The finished/running pipelines can be seen at https://lab.analogparadigm.com/software/dda/-/pipelines
We also run these tests at our Gitlab CI when pushes happen to the Github repository
https://github.com/anabrid/pyanalog thanks to mirroring at
https://lab.analogparadigm.com/software/pyanalog-mirror-from-github

What about analog hardware tests
--------------------------------

This would require having dedicated testing hardware somewhere. This is out of scope for the moment.
