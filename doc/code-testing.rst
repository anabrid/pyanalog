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
    `Pytest <https://pytest.org>`_ third party library for (unit) testing.
  
    These tests are located in the ``tests/`` directory. They can be executed
    by running ``pytest tests`` or just ``make test`` from the parent directory.
    
.. note::

    Tests are special because they can be evaluated for success or failure
    automatically. This differs them from other code contributions, such
    as the example codes in the ``examples/`` directory, which cannot be
    evaluated for correctnes.

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

What else about tests
---------------------

Continous integration
   Tests are run whenever the code is committed. See for instance https://lab.analogparadigm.com/koeppel/dda/-/pipelines

What about hardware tests?
   This would require having dedicated testing hardware somewhere. This is out of scope for the moment.
